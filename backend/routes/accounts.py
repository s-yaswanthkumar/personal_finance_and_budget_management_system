from fastapi import APIRouter, Query, HTTPException
from backend.db.postgres import get_db_cursor

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])

@router.get("")
def get_accounts(user_id: int = Query(1, description="Target User ID")):
    """List all accounts and current balances for the user."""
    try:
        with get_db_cursor() as (cur, conn):
            cur.execute("""
                SELECT 
                    a.account_id,
                    a.user_id,
                    a.account_name,
                    a.balance,
                    at.name AS account_type,
                    a.type_id
                FROM accounts a
                JOIN account_types at ON a.type_id = at.type_id
                WHERE a.user_id = %s
                ORDER BY a.account_id ASC;
            """, (user_id,))
            rows = cur.fetchall()

            accounts = []
            total_balance = 0.0
            for r in rows:
                bal = float(r[3])
                total_balance += bal
                accounts.append({
                    "account_id": r[0],
                    "user_id": r[1],
                    "account_name": r[2],
                    "balance": round(bal, 2),
                    "account_type": r[4],
                    "type_id": r[5]
                })

            return {
                "user_id": user_id,
                "total_net_worth": round(total_balance, 2),
                "accounts": accounts
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch accounts: {str(e)}")