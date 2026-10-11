from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from backend.db.postgres import get_db_cursor
from backend.ml.burn_rate import estimate_burn_rate
from backend.ml.forecast import get_user_daily_forecast

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/summary")
def get_analytics_summary(
    user_id: int = Query(1, description="User ID"),
    month_year: str = Query(None, description="Month in YYYY-MM format")
):
    """
    Returns high-level financial health analytics:
    1. Aggregated category breakdown from PostgreSQL view `vw_monthly_summary`.
    2. Total Net Worth across accounts.
    3. 30-day predictive spend forecast and daily burn-rate via Empirical Bayes.
    4. Month-over-month trend analysis.
    5. Machine Learning Day-by-Day Spending Forecast (next 30 days).
    """
    if not month_year:
        month_year = datetime.now().strftime("%Y-%m")

    try:
        with get_db_cursor() as (cur, conn):
            # 1. Total Net Worth
            cur.execute("SELECT COALESCE(SUM(balance), 0) FROM accounts WHERE user_id = %s;", (user_id,))
            net_worth = float(cur.fetchone()[0])

            # 2. Aggregated totals from SQL view `vw_monthly_summary` for target month
            cur.execute("""
                SELECT 
                    category_id,
                    category_name,
                    month_year,
                    total_expense,
                    total_income,
                    transaction_count
                FROM vw_monthly_summary
                WHERE user_id = %s AND month_year = %s
                ORDER BY total_expense DESC;
            """, (user_id, month_year))
            cat_summary_rows = cur.fetchall()

            category_spend = []
            month_total_expense = 0.0
            month_total_income = 0.0
            for r in cat_summary_rows:
                cid, cname, my, exp, inc, cnt = r
                exp_f = float(exp)
                inc_f = float(inc)
                month_total_expense += exp_f
                month_total_income += inc_f
                if exp_f > 0:
                    category_spend.append({
                        "category_id": cid,
                        "category_name": cname,
                        "amount": round(exp_f, 2),
                        "transaction_count": cnt
                    })

            # 3. Fetch past 6 months trend from `vw_monthly_summary`
            cur.execute("""
                SELECT 
                    month_year,
                    SUM(total_expense) AS monthly_expense,
                    SUM(total_income) AS monthly_income
                FROM vw_monthly_summary
                WHERE user_id = %s
                GROUP BY month_year
                ORDER BY month_year ASC
                LIMIT 6;
            """, (user_id,))
            trend_rows = cur.fetchall()

            monthly_trends = []
            for r in trend_rows:
                monthly_trends.append({
                    "month": r[0],
                    "expense": round(float(r[1]), 2),
                    "income": round(float(r[2]), 2),
                    "net_savings": round(float(r[2]) - float(r[1]), 2)
                })

        # 4. Invoke Predictive Burn-Rate & Cold-Start Estimator
        burn_rate_data = estimate_burn_rate(user_id)

        # 5. Invoke Two-Stage Hurdle ML Day-by-Day Spending Forecaster (30 days)
        daily_forecast_data = get_user_daily_forecast(user_id=user_id, days=30)

        return {
            "user_id": user_id,
            "month_year": month_year,
            "net_worth": round(net_worth, 2),
            "current_month_income": round(month_total_income, 2),
            "current_month_expense": round(month_total_expense, 2),
            "current_month_savings": round(month_total_income - month_total_expense, 2),
            "savings_rate_pct": round(((month_total_income - month_total_expense) / month_total_income * 100), 1) if month_total_income > 0 else 0.0,
            "category_spend_breakdown": category_spend,
            "monthly_trends": monthly_trends,
            "predictive_burn_rate": burn_rate_data,
            "daily_forecast": daily_forecast_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics summary: {str(e)}")

@router.get("/daily-forecast")
def get_daily_forecast_endpoint(
    user_id: int = Query(1, description="Target User ID"),
    days: int = Query(30, ge=7, le=90, description="Forecast horizon in days (7 to 90)")
):
    """
    Predictive Machine Learning model forecasting:
    - On which specific upcoming calendar days the user is projected to spend money.
    - How much money the user will spend on each day (amount and confidence range).
    - Top likely expenditure categories for each day.
    - Peak projected spending day and alert flags.
    """
    try:
        forecast = get_user_daily_forecast(user_id=user_id, days=days)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate daily spending forecast: {str(e)}")