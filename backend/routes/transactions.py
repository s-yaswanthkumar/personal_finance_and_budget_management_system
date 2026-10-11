import csv
import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, UploadFile, File, Form, Response
from pydantic import BaseModel, Field
import psycopg2.errors
from backend.db.postgres import get_db_cursor, get_db_connection
from backend.db.mongo import log_alert, log_raw_payload
from backend.ml.categorizer import predict_category
from backend.ml.anomaly_detector import detect_anomaly
from backend.ml.vector_embeddings import generate_embedding
from pgvector.psycopg2 import register_vector

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

class TransactionCreate(BaseModel):
    user_id: int = 1
    account_id: int
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    transaction_type: str = Field("expense", description="'expense' or 'income'")
    raw_memo: str = Field(..., min_length=1, description="Raw transaction memo/string")
    category_id: Optional[int] = None
    transaction_date: Optional[str] = None

@router.get("")
def get_transactions(
    user_id: int = Query(1, description="User ID"),
    limit: int = Query(50, ge=1, le=200),
    category_id: Optional[int] = Query(None),
    account_id: Optional[int] = Query(None)
):
    """Fetch paginated recent transactions."""
    try:
        with get_db_cursor() as (cur, conn):
            query = """
                SELECT 
                    t.transaction_id,
                    t.user_id,
                    t.account_id,
                    a.account_name,
                    t.category_id,
                    c.name AS category_name,
                    t.amount,
                    t.transaction_type,
                    t.raw_memo,
                    t.transaction_date
                FROM transactions t
                JOIN accounts a ON t.account_id = a.account_id
                JOIN categories c ON t.category_id = c.category_id
                WHERE t.user_id = %s
            """
            params = [user_id]

            if category_id:
                query += " AND t.category_id = %s"
                params.append(category_id)
            if account_id:
                query += " AND t.account_id = %s"
                params.append(account_id)

            query += " ORDER BY t.transaction_date DESC, t.transaction_id DESC LIMIT %s;"
            params.append(limit)

            cur.execute(query, tuple(params))
            rows = cur.fetchall()

            txs = []
            for r in rows:
                txs.append({
                    "transaction_id": r[0],
                    "user_id": r[1],
                    "account_id": r[2],
                    "account_name": r[3],
                    "category_id": r[4],
                    "category_name": r[5],
                    "amount": float(r[6]),
                    "transaction_type": r[7],
                    "raw_memo": r[8],
                    "transaction_date": r[9].isoformat() if hasattr(r[9], 'isoformat') else str(r[9])
                })

            return {"user_id": user_id, "count": len(txs), "transactions": txs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")

@router.post("")
def create_transaction(payload: TransactionCreate):
    """
    Ingest a new transaction:
    1. Log raw inbound payload to MongoDB.
    2. Invoke NLP auto-categorization if category_id is omitted.
    3. Run Isolation Forest anomaly detection.
    4. Insert into PostgreSQL (BEFORE INSERT trigger verifies budget caps).
    5. On trigger breach exception, write MongoDB breach alert & return 400.
    6. Update account balance and log warning/anomaly alerts to MongoDB.
    """
    raw_dict = payload.model_dump()
    user_id = payload.user_id
    tx_type = payload.transaction_type.lower()
    tx_time = datetime.fromisoformat(payload.transaction_date) if payload.transaction_date else datetime.now()

    # Step 1: Log raw unparsed inbound payload to MongoDB
    try:
        log_raw_payload(
            user_id=user_id,
            raw_payload=raw_dict,
            source="web_dashboard",
            parsed_status="processing"
        )
    except Exception as e:
        print("Warning: Failed to log raw payload to MongoDB:", e)

    # Step 2: NLP Auto-Categorization if category_id not provided
    category_id = payload.category_id
    predicted_category_name = None
    nlp_confidence = 1.0

    with get_db_cursor() as (cur, conn):
        cur.execute("SELECT category_id, name FROM categories;")
        cat_map_by_id = dict(cur.fetchall())
        cat_map_by_name = {name.lower(): cid for cid, name in cat_map_by_id.items()}

    if not category_id or category_id <= 0:
        nlp_result = predict_category(payload.raw_memo)
        predicted_category_name = nlp_result.get("category", "Dining")
        nlp_confidence = nlp_result.get("confidence", 0.9)
        category_id = cat_map_by_name.get(predicted_category_name.lower(), 1)
    else:
        predicted_category_name = cat_map_by_id.get(category_id, "Other")

    # Step 3: Run Isolation Forest anomaly detection
    anomaly_result = detect_anomaly(
        amount=payload.amount,
        tx_hour=tx_time.hour,
        category=predicted_category_name
    )

    # Step 4: Execute insertion into PostgreSQL inside an atomic transaction
    created_tx_id = None
    try:
        with get_db_cursor(commit=True) as (cur, conn):
            register_vector(conn)
            # Generate 64-dim semantic vector embedding for pgvector
            vec = generate_embedding(payload.raw_memo)
            # Insert transaction (PostgreSQL trigger runs BEFORE INSERT)
            cur.execute("""
                INSERT INTO transactions 
                    (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING transaction_id;
            """, (user_id, payload.account_id, category_id, payload.amount, tx_type, payload.raw_memo, tx_time, vec))
            created_tx_id = cur.fetchone()[0]

            # Update account balance
            if tx_type == "expense":
                cur.execute("UPDATE accounts SET balance = balance - %s WHERE account_id = %s;", (payload.amount, payload.account_id))
            else:
                cur.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s;", (payload.amount, payload.account_id))

            # Check if an 80% threshold warning was generated by trigger in budget_alerts
            cur.execute("""
                SELECT message, threshold_pct, current_spent, monthly_limit 
                FROM budget_alerts 
                WHERE user_id = %s AND category_id = %s 
                ORDER BY alert_id DESC LIMIT 1;
            """, (user_id, category_id))
            warning_row = cur.fetchone()

    except Exception as exc:
        # Check if this was a budget hard cap breach raised by trigger (code 23514)
        err_msg = str(exc)
        if "Budget hard cap breach" in err_msg or (hasattr(exc, 'pgcode') and exc.pgcode == '23514'):
            # Step 4a: Write hard cap breach alert to MongoDB
            breach_alert = log_alert(
                user_id=user_id,
                alert_type="budget_breach",
                category=predicted_category_name,
                message=f"Hard cap exceeded! Transaction of ${payload.amount:.2f} for '{payload.raw_memo}' was rejected by database trigger.",
                severity="breach",
                metadata={
                    "amount": payload.amount,
                    "raw_memo": payload.raw_memo,
                    "account_id": payload.account_id,
                    "category": predicted_category_name
                }
            )
            raise HTTPException(
                status_code=400,
                detail=f"Transaction Aborted by Database Trigger: Hard cap exceeded in category '{predicted_category_name}'. Breach logged to MongoDB alert audit."
            )
        else:
            raise HTTPException(status_code=500, detail=f"Database error: {str(exc)}")

    # Step 5: Post-insert Alert logging
    alerts_triggered = []

    # If anomaly detected by Isolation Forest -> write to MongoDB
    if anomaly_result.get("is_anomaly"):
        anom_doc = log_alert(
            user_id=user_id,
            alert_type="anomaly",
            category=predicted_category_name,
            message=anomaly_result.get("reason"),
            severity="anomaly",
            metadata={
                "transaction_id": created_tx_id,
                "amount": payload.amount,
                "score": anomaly_result.get("score"),
                "category": predicted_category_name
            }
        )
        alerts_triggered.append(anom_doc)

    # If spending reached >= 80% warning -> sync to MongoDB alert_logs
    if warning_row:
        warn_msg, thresh, spent, lim = warning_row
        warn_doc = log_alert(
            user_id=user_id,
            alert_type="budget_warning",
            category=predicted_category_name,
            message=warn_msg,
            severity="warning",
            metadata={
                "transaction_id": created_tx_id,
                "threshold_pct": float(thresh),
                "current_spent": float(spent),
                "monthly_limit": float(lim)
            }
        )
        alerts_triggered.append(warn_doc)

    return {
        "success": True,
        "transaction_id": created_tx_id,
        "amount": payload.amount,
        "transaction_type": tx_type,
        "category": {
            "category_id": category_id,
            "category_name": predicted_category_name,
            "confidence": nlp_confidence
        },
        "anomaly": anomaly_result,
        "alerts_triggered": alerts_triggered
    }

@router.get("/csv-template")
def get_csv_template():
    """Returns a downloadable sample CSV containing 50 transactions covering approximately 2 months of payments."""
    sample_csv = (
        "date,amount,type,raw_memo\n"
        "2026-08-01,65000.00,income,Monthly Payroll Direct Deposit\n"
        "2026-08-01,18000.00,expense,Apartment Monthly Rental Payment\n"
        "2026-08-02,145.50,expense,Trader Joes Market\n"
        "2026-08-03,240.00,expense,Uber Trip 281 City Ride\n"
        "2026-08-04,380.00,expense,Swiggy Gourmet Dinner Delivery\n"
        "2026-08-05,2150.00,expense,Electricity Utility Bill Payment\n"
        "2026-08-06,620.00,expense,Blinkit Instant Grocery Store\n"
        "2026-08-08,180.00,expense,Starbucks Hazelnut Latte\n"
        "2026-08-09,1200.00,expense,Airtel Fiber Broadband Internet\n"
        "2026-08-11,450.00,expense,Apollo Pharmacy Medicines\n"
        "2026-08-12,850.00,expense,Shell Fuel Station Petrol\n"
        "2026-08-14,699.00,expense,Netflix Monthly Subscription\n"
        "2026-08-15,1450.00,expense,Independence Day Family Dining Out\n"
        "2026-08-16,320.00,expense,Zepto Daily Essentials Supermarket\n"
        "2026-08-18,290.00,expense,Zomato Food Delivery Lunch\n"
        "2026-08-19,150.00,expense,Namma Metro Smart Card Recharge\n"
        "2026-08-21,1850.00,expense,DMart Supermarket Monthly Groceries\n"
        "2026-08-22,650.00,expense,BookMyShow Weekend Movie Tickets\n"
        "2026-08-24,310.00,expense,Ola Cabs Airport Taxi Ride\n"
        "2026-08-25,499.00,expense,Amazon Prime Annual Renewal\n"
        "2026-08-26,1100.00,expense,Indane Gas Cylinder Refill\n"
        "2026-08-28,420.00,expense,Dominos Pizza Weekend Order\n"
        "2026-08-29,199.00,expense,Spotify Premium Music Subscription\n"
        "2026-08-30,550.00,expense,Nature Basket Fresh Vegetables\n"
        "2026-08-31,2500.00,income,Freelance Consulting Honorarium\n"
        "2026-09-01,65000.00,income,Monthly Payroll Direct Deposit\n"
        "2026-09-01,18000.00,expense,Apartment Monthly Rental Payment\n"
        "2026-09-02,520.00,expense,BigBasket Organic Produce Order\n"
        "2026-09-03,280.00,expense,Uber Premier Office Commute\n"
        "2026-09-04,460.00,expense,Swiggy Lunch Bowl Express\n"
        "2026-09-05,1980.00,expense,Electric Utility Power Bill\n"
        "2026-09-06,750.00,expense,Instamart Household Groceries\n"
        "2026-09-08,210.00,expense,Blue Tokai Specialty Coffee Roasters\n"
        "2026-09-09,1200.00,expense,High-Speed Fiber Broadband Bill\n"
        "2026-09-11,390.00,expense,MedPlus Pharmacy Wellness\n"
        "2026-09-12,920.00,expense,HP Auto Fuel Station Refill\n"
        "2026-09-13,699.00,expense,Netflix Standard Subscription Renewal\n"
        "2026-09-14,1850.00,expense,Nature Basket Gourmet Pantry\n"
        "2026-09-16,340.00,expense,Zepto Quick Essentials Delivery\n"
        "2026-09-17,580.00,expense,Zomato Weekend Dinner Delivery\n"
        "2026-09-19,200.00,expense,Metro Card Station Transit Topup\n"
        "2026-09-20,2100.00,expense,Reliance Smart Superstore Provisions\n"
        "2026-09-22,850.00,expense,PVR Cinemas Movie Experience\n"
        "2026-09-23,340.00,expense,Ola Cabs City Travel Fare\n"
        "2026-09-25,950.00,expense,Water Utility Supply Tanker Bill\n"
        "2026-09-26,480.00,expense,McDonalds Fast Casual Meal\n"
        "2026-09-27,299.00,expense,YouTube Premium Family Plan\n"
        "2026-09-28,640.00,expense,Blinkit Fresh Dairy & Groceries\n"
        "2026-09-29,1500.00,expense,Dinner at Barbeque Nation\n"
        "2026-09-30,3500.00,income,Quarterly Investment Dividend Payout\n"
    )
    return Response(
        content=sample_csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions_template.csv"}
    )

@router.post("/import-csv")
async def import_transactions_csv(
    file: UploadFile = File(...),
    user_id: Optional[int] = Form(None),
    account_id: Optional[int] = Form(None),
    user_id_query: Optional[int] = Query(None, alias="user_id"),
    account_id_query: Optional[int] = Query(None, alias="account_id")
):
    """
    Atomic Batch CSV Ingestion Pipeline:
    1. Reads and normalizes uploaded CSV file with bank statement columns.
    2. Runs atomic database transaction (conn.autocommit = False).
    3. Invokes NLP auto-categorization and Isolation Forest on each row.
    4. Evaluates PostgreSQL BEFORE INSERT trigger (budget cap verification).
    5. If any row triggers a budget hard cap abort or database constraint failure,
       performs an explicit ROLLBACK of the entire batch (0 partial state updates).
    6. On success, commits all rows and updates account balances.
    """
    actual_user_id = user_id if user_id is not None else (user_id_query if user_id_query is not None else 1)
    actual_account_id = account_id if account_id is not None else account_id_query

    if actual_account_id is None:
        raise HTTPException(status_code=400, detail="account_id is required (via form data or query parameter).")
    user_id = actual_user_id
    account_id = actual_account_id

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are supported.")

    try:
        file_bytes = await file.read()
        text_content = file_bytes.decode("utf-8-sig")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV file encoding: {str(e)}")

    reader = list(csv.DictReader(io.StringIO(text_content)))
    if not reader:
        raise HTTPException(status_code=400, detail="CSV file is empty or contains only headers.")

    # Ingest raw payload into MongoDB for audit provenance
    try:
        log_raw_payload(
            user_id=user_id,
            raw_payload={"filename": file.filename, "row_count": len(reader)},
            source="csv_import_pipeline",
            parsed_status="processing"
        )
    except Exception:
        pass

    current_row_idx = 0
    with get_db_connection() as conn:
        conn.autocommit = False  # Explicit ACID transaction block
        register_vector(conn)
        cur = conn.cursor()
        try:
            # Pre-load category mappings
            cur.execute("SELECT category_id, name FROM categories;")
            cat_map_by_id = dict(cur.fetchall())
            cat_map_by_name = {name.lower(): cid for cid, name in cat_map_by_id.items()}

            # Verify account exists
            cur.execute("SELECT account_id, balance FROM accounts WHERE account_id = %s AND user_id = %s;", (account_id, user_id))
            acc_row = cur.fetchone()
            if not acc_row:
                conn.rollback()
                raise HTTPException(status_code=404, detail="Selected account does not exist.")

            imported_count = 0
            auto_categorized_count = 0
            anomalies_flagged_count = 0
            created_transactions = []
            alerts_to_log = []

            for idx, raw_row in enumerate(reader, start=1):
                current_row_idx = idx
                # Normalize keys to lower-case stripped
                row = {k.strip().lower(): (v.strip() if v else '') for k, v in raw_row.items() if k}

                # 1. Extract raw memo
                memo = (
                    row.get("raw_memo") or 
                    row.get("memo") or 
                    row.get("description") or 
                    row.get("merchant") or 
                    row.get("details") or 
                    row.get("name") or 
                    "Transaction"
                )

                # 2. Extract amount
                raw_amt_str = row.get("amount") or row.get("amt") or row.get("value") or row.get("total") or "0"
                cleaned_amt_str = raw_amt_str.replace("$", "").replace(",", "").strip()
                try:
                    raw_numeric_amt = float(cleaned_amt_str)
                except ValueError:
                    raise ValueError(f"Invalid numeric amount '{raw_amt_str}' on row {idx}")

                # 3. Determine transaction type
                raw_type = (row.get("type") or row.get("transaction_type") or row.get("tx_type") or "").lower()
                if raw_type in ["expense", "debit", "dr", "withdrawal", "outflow"]:
                    tx_type = "expense"
                    amount = abs(raw_numeric_amt)
                elif raw_type in ["income", "credit", "cr", "deposit", "inflow"]:
                    tx_type = "income"
                    amount = abs(raw_numeric_amt)
                else:
                    # Infer from sign of amount
                    if raw_numeric_amt < 0:
                        tx_type = "expense"
                        amount = abs(raw_numeric_amt)
                    else:
                        tx_type = "expense"  # Default assumption for typical charges
                        amount = raw_numeric_amt

                # 4. Extract date
                raw_date_str = row.get("date") or row.get("transaction_date") or row.get("tx_date") or row.get("timestamp")
                tx_date = datetime.now()
                if raw_date_str:
                    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
                        try:
                            tx_date = datetime.strptime(raw_date_str, fmt)
                            break
                        except ValueError:
                            pass

                # 5. NLP Auto-Categorization
                category_name = row.get("category") or row.get("category_name")
                category_id = None
                if category_name and category_name.lower() in cat_map_by_name:
                    category_id = cat_map_by_name[category_name.lower()]
                    pred_cat_name = cat_map_by_id[category_id]
                else:
                    # Invoke NLP Auto-Categorizer
                    nlp_res = predict_category(memo)
                    pred_cat_name = nlp_res.get("category", "Dining")
                    category_id = cat_map_by_name.get(pred_cat_name.lower(), 1)
                    auto_categorized_count += 1

                # 6. Isolation Forest Anomaly Detection
                anom = detect_anomaly(amount=amount, tx_hour=tx_date.hour, category=pred_cat_name)
                is_anom = anom.get("is_anomaly", False)
                if is_anom:
                    anomalies_flagged_count += 1
                    alerts_to_log.append({
                        "user_id": user_id,
                        "type": "anomaly",
                        "category": pred_cat_name,
                        "message": f"CSV Import (Row {idx}): {anom.get('reason')}",
                        "severity": "anomaly",
                        "metadata": {"amount": amount, "row": idx, "raw_memo": memo}
                    })

                # 7. Insert into PostgreSQL (native BEFORE INSERT trigger trg_check_budget_limits will fire)
                row_vec = generate_embedding(memo)
                cur.execute("""
                    INSERT INTO transactions 
                        (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING transaction_id;
                """, (user_id, account_id, category_id, amount, tx_type, memo, tx_date, row_vec))
                created_tx_id = cur.fetchone()[0]

                # 8. Update account balance
                if tx_type == "expense":
                    cur.execute("UPDATE accounts SET balance = balance - %s WHERE account_id = %s;", (amount, account_id))
                else:
                    cur.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s;", (amount, account_id))

                imported_count += 1
                created_transactions.append({
                    "transaction_id": created_tx_id,
                    "amount": amount,
                    "category": pred_cat_name,
                    "raw_memo": memo,
                    "is_anomaly": is_anom
                })

            # All rows processed successfully -> Atomic COMMIT
            conn.commit()

            # Post-commit: Asynchronously sync accumulated anomaly/warning alerts to MongoDB
            for a in alerts_to_log:
                try:
                    log_alert(a["user_id"], a["type"], a["category"], a["message"], a["severity"], a.get("metadata"))
                except Exception:
                    pass

            return {
                "status": "COMMITTED",
                "imported_count": imported_count,
                "auto_categorized": auto_categorized_count,
                "anomalies_flagged": anomalies_flagged_count,
                "message": f"Successfully ingested {imported_count} transactions with full ACID consistency.",
                "processed_transactions": created_transactions,
                "sample_transactions": created_transactions[:5],
                "rolled_back": False
            }

        except Exception as exc:
            # FORCE EXPLICIT ROLLBACK ON ANY ERROR TO GUARANTEE 100% LEDGER INTEGRITY
            conn.rollback()
            err_msg = str(exc)

            if "Budget hard cap breach" in err_msg or (hasattr(exc, 'pgcode') and exc.pgcode == '23514'):
                # Log breach event into MongoDB
                try:
                    log_alert(
                        user_id=user_id,
                        alert_type="budget_breach",
                        category="CSV Batch Ingestion",
                        message=f"CSV Batch Aborted at row {current_row_idx}: {err_msg.strip()}",
                        severity="breach",
                        metadata={"row": current_row_idx, "file": file.filename}
                    )
                except Exception:
                    pass

                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "rolled_back": True,
                        "error_row": current_row_idx,
                        "error": "BUDGET_HARD_CAP_BREACH",
                        "message": f"CSV Batch Aborted: Row {current_row_idx} triggered budget hard cap abort. Entire batch rolled back with 0 state changes committed.",
                        "raw_error": err_msg
                    }
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "rolled_back": True,
                        "error_row": current_row_idx,
                        "error": "CSV_PARSING_OR_DB_ERROR",
                        "message": f"CSV Batch Import failed at row {current_row_idx}: {err_msg}. Entire batch rolled back.",
                        "raw_error": err_msg
                    }
                )
        finally:
            cur.close()