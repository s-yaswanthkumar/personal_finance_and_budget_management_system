from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.db.postgres import get_db_connection
from backend.db.mongo import log_alert

router = APIRouter(prefix="/api/transfers", tags=["Transfers"])

class TransferRequest(BaseModel):
    user_id: int = 1
    from_account_id: int = Field(..., description="Source account ID")
    to_account_id: int = Field(..., description="Destination account ID")
    amount: float = Field(..., gt=0, description="Transfer amount")
    memo: Optional[str] = Field("Internal Account Transfer", description="Memo/Note")

@router.post("")
def execute_transfer(payload: TransferRequest):
    """
    Executes an atomic multi-account transfer inside a strict ACID block.
    Uses row-level locking (SELECT ... FOR UPDATE).
    If source has insufficient funds, performs an explicit ROLLBACK with zero state updates.
    """
    if payload.from_account_id == payload.to_account_id:
        raise HTTPException(status_code=400, detail="Source and destination accounts must be distinct.")

    with get_db_connection() as conn:
        conn.autocommit = False  # Explicit transaction control
        cur = conn.cursor()
        try:
            # 1. Lock source account row
            cur.execute("""
                SELECT account_id, account_name, balance 
                FROM accounts 
                WHERE account_id = %s AND user_id = %s 
                FOR UPDATE;
            """, (payload.from_account_id, payload.user_id))
            src_row = cur.fetchone()

            if not src_row:
                conn.rollback()
                raise HTTPException(status_code=404, detail="Source account not found.")

            src_id, src_name, src_balance = src_row
            src_balance = float(src_balance)

            # 2. Verify sufficient funds
            if src_balance < payload.amount:
                # Explicit rollback guaranteeing 100% ledger consistency
                conn.rollback()
                # Log audit event in MongoDB
                try:
                    log_alert(
                        user_id=payload.user_id,
                        alert_type="transfer_rollback",
                        category="Transfer",
                        message=f"ACID Rollback: Attempted transfer of ${payload.amount:,.2f} from '{src_name}' aborted. Insufficient balance (${src_balance:,.2f}).",
                        severity="warning",
                        metadata={
                            "from_account_id": payload.from_account_id,
                            "to_account_id": payload.to_account_id,
                            "requested_amount": payload.amount,
                            "current_balance": src_balance
                        }
                    )
                except Exception:
                    pass

                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": "INSUFFICIENT_FUNDS",
                        "message": f"Transfer rejected: Account '{src_name}' has insufficient funds (${src_balance:,.2f}) for requested transfer of ${payload.amount:,.2f}.",
                        "rolled_back": True,
                        "available_balance": src_balance,
                        "requested_amount": payload.amount
                    }
                )

            # 3. Lock destination account row
            cur.execute("""
                SELECT account_id, account_name, balance 
                FROM accounts 
                WHERE account_id = %s AND user_id = %s 
                FOR UPDATE;
            """, (payload.to_account_id, payload.user_id))
            dest_row = cur.fetchone()

            if not dest_row:
                conn.rollback()
                raise HTTPException(status_code=404, detail="Destination account not found.")

            dest_id, dest_name, dest_balance = dest_row
            dest_balance = float(dest_balance)

            # 4. Atomic balance updates
            cur.execute("""
                UPDATE accounts 
                SET balance = balance - %s 
                WHERE account_id = %s;
            """, (payload.amount, payload.from_account_id))

            cur.execute("""
                UPDATE accounts 
                SET balance = balance + %s 
                WHERE account_id = %s;
            """, (payload.amount, payload.to_account_id))

            # Fetch or ensure category for Transfer
            cur.execute("SELECT category_id FROM categories WHERE name = 'Transfer';")
            cat_row = cur.fetchone()
            if not cat_row:
                cur.execute("INSERT INTO categories (name) VALUES ('Transfer') ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING category_id;")
                cat_id = cur.fetchone()[0]
            else:
                cat_id = cat_row[0]

            # 5. Insert double-entry ledger records
            cur.execute("""
                INSERT INTO transactions 
                    (user_id, account_id, category_id, amount, transaction_type, raw_memo)
                VALUES 
                    (%s, %s, %s, %s, 'expense', %s);
            """, (payload.user_id, payload.from_account_id, cat_id, payload.amount, f"Transfer to {dest_name}: {payload.memo}"))

            cur.execute("""
                INSERT INTO transactions 
                    (user_id, account_id, category_id, amount, transaction_type, raw_memo)
                VALUES 
                    (%s, %s, %s, %s, 'income', %s);
            """, (payload.user_id, payload.to_account_id, cat_id, payload.amount, f"Transfer from {src_name}: {payload.memo}"))

            # 6. Commit atomic transaction
            conn.commit()

            new_src_balance = round(src_balance - payload.amount, 2)
            new_dest_balance = round(dest_balance + payload.amount, 2)

            return {
                "success": True,
                "status": "COMMITTED",
                "message": f"Successfully transferred ${payload.amount:,.2f} from '{src_name}' to '{dest_name}'.",
                "amount": payload.amount,
                "from_account": {
                    "account_id": src_id,
                    "name": src_name,
                    "previous_balance": src_balance,
                    "new_balance": new_src_balance
                },
                "to_account": {
                    "account_id": dest_id,
                    "name": dest_name,
                    "previous_balance": dest_balance,
                    "new_balance": new_dest_balance
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Atomic transfer failed and was rolled back: {str(e)}"
            )
        finally:
            cur.close()