from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from backend.db.postgres import get_db_cursor

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])

class BudgetUpsert(BaseModel):
    user_id: int = 1
    category_id: int
    monthly_limit: float
    month_year: str = None

@router.get("")
def get_budgets(
    user_id: int = Query(1, description="Target User ID"),
    month_year: str = Query(None, description="Month in YYYY-MM format")
):
    """List monthly budget thresholds and current utilization percentages."""
    if not month_year:
        month_year = datetime.now().strftime("%Y-%m")

    try:
        with get_db_cursor() as (cur, conn):
            # Fetch all categories joined with budget limits and current expenses
            cur.execute("""
                SELECT 
                    c.category_id,
                    c.name AS category_name,
                    COALESCE(b.monthly_limit, 0.00) AS monthly_limit,
                    b.budget_id,
                    COALESCE(SUM(t.amount), 0.00) AS current_spent
                FROM categories c
                LEFT JOIN budgets b ON c.category_id = b.category_id 
                    AND b.user_id = %s 
                    AND b.month_year = %s
                LEFT JOIN transactions t ON c.category_id = t.category_id 
                    AND t.user_id = %s 
                    AND t.transaction_type = 'expense' 
                    AND TO_CHAR(t.transaction_date, 'YYYY-MM') = %s
                GROUP BY c.category_id, c.name, b.monthly_limit, b.budget_id
                ORDER BY c.category_id ASC;
            """, (user_id, month_year, user_id, month_year))
            rows = cur.fetchall()

            budgets = []
            total_budget = 0.0
            total_spent = 0.0
            for r in rows:
                cat_id, cat_name, limit_val, budget_id, spent_val = r
                limit = float(limit_val)
                spent = float(spent_val)
                total_budget += limit
                total_spent += spent
                remaining = max(0.0, limit - spent)
                utilization = round((spent / limit * 100), 1) if limit > 0 else 0.0

                # Determine status
                if limit == 0:
                    status = "unbudgeted"
                elif utilization >= 100:
                    status = "breached"
                elif utilization >= 80:
                    status = "warning"
                else:
                    status = "on_track"

                budgets.append({
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "monthly_limit": round(limit, 2),
                    "current_spent": round(spent, 2),
                    "remaining": round(remaining, 2),
                    "utilization_pct": utilization,
                    "status": status,
                    "month_year": month_year,
                    "budget_id": budget_id
                })

            total_utilization = round((total_spent / total_budget * 100), 1) if total_budget > 0 else 0.0

            return {
                "user_id": user_id,
                "month_year": month_year,
                "total_budget": round(total_budget, 2),
                "total_spent": round(total_spent, 2),
                "total_remaining": round(max(0.0, total_budget - total_spent), 2),
                "total_utilization_pct": total_utilization,
                "budgets": budgets
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch budgets: {str(e)}")

@router.post("")
def upsert_budget(payload: BudgetUpsert):
    """Set or update a budget limit for a category."""
    month_year = payload.month_year or datetime.now().strftime("%Y-%m")
    try:
        with get_db_cursor(commit=True) as (cur, conn):
            cur.execute("""
                INSERT INTO budgets (user_id, category_id, monthly_limit, month_year)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, category_id, month_year) 
                DO UPDATE SET monthly_limit = EXCLUDED.monthly_limit
                RETURNING budget_id;
            """, (payload.user_id, payload.category_id, payload.monthly_limit, month_year))
            budget_id = cur.fetchone()[0]

            return {
                "success": True,
                "budget_id": budget_id,
                "category_id": payload.category_id,
                "monthly_limit": payload.monthly_limit,
                "month_year": month_year
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upsert budget: {str(e)}")