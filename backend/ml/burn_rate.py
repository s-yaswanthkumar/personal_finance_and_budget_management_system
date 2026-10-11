from datetime import datetime, timedelta
import calendar
from backend.db.postgres import get_db_cursor

PRIOR_DAILY_MEAN = 42.50  # Global baseline daily spend in USD for cold start
BAYES_SHRINKAGE_K = 7     # Shrinkage factor

def estimate_burn_rate(user_id: int) -> dict:
    """
    Computes daily burn rate and 30-day spend projections.
    Uses Empirical Bayes prior weighting when historical data has <14 distinct days.
    """
    now = datetime.now()
    current_month_str = now.strftime('%Y-%m')
    _, num_days_in_month = calendar.monthrange(now.year, now.month)
    days_elapsed = now.day
    days_remaining = max(1, num_days_in_month - days_elapsed)

    with get_db_cursor() as (cur, conn):
        # 1. Total expense in the current calendar month
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = %s
              AND transaction_type = 'expense'
              AND TO_CHAR(transaction_date, 'YYYY-MM') = %s;
        """, (user_id, current_month_str))
        current_month_spent = float(cur.fetchone()[0])

        # 2. Historical distinct days and spending in past 60 days
        sixty_days_ago = now - timedelta(days=60)
        cur.execute("""
            SELECT 
                COUNT(DISTINCT DATE(transaction_date)) AS active_days,
                COALESCE(SUM(amount), 0) AS total_spent,
                MIN(transaction_date) AS first_tx_date
            FROM transactions
            WHERE user_id = %s
              AND transaction_type = 'expense'
              AND transaction_date >= %s;
        """, (user_id, sixty_days_ago))
        row = cur.fetchone()
        active_days = row[0] or 0
        total_history_spent = float(row[1] or 0.0)

        # 3. Category breakdown for current month
        cur.execute("""
            SELECT 
                c.name AS category_name,
                COALESCE(SUM(t.amount), 0) AS spent,
                COALESCE(b.monthly_limit, 0) AS monthly_limit
            FROM categories c
            LEFT JOIN transactions t ON c.category_id = t.category_id 
                AND t.user_id = %s 
                AND t.transaction_type = 'expense' 
                AND TO_CHAR(t.transaction_date, 'YYYY-MM') = %s
            LEFT JOIN budgets b ON c.category_id = b.category_id 
                AND b.user_id = %s 
                AND b.month_year = %s
            GROUP BY c.name, b.monthly_limit
            ORDER BY spent DESC;
        """, (user_id, current_month_str, user_id, current_month_str))
        cat_rows = cur.fetchall()

    category_breakdown = []
    total_budget_limit = 0.0
    for cat_name, spent, limit in cat_rows:
        spent_flt = float(spent)
        limit_flt = float(limit)
        total_budget_limit += limit_flt
        category_breakdown.append({
            "category": cat_name,
            "spent": round(spent_flt, 2),
            "limit": round(limit_flt, 2),
            "utilization_pct": round((spent_flt / limit_flt * 100), 1) if limit_flt > 0 else 0.0
        })

    # Empirical Bayes Shrinkage / Daily Burn Rate calculation
    is_cold_start = active_days < 14
    if active_days > 0:
        user_daily_avg = total_history_spent / active_days
    else:
        user_daily_avg = PRIOR_DAILY_MEAN

    if is_cold_start:
        weight = active_days / (active_days + BAYES_SHRINKAGE_K)
        daily_burn_rate = (weight * user_daily_avg) + ((1.0 - weight) * PRIOR_DAILY_MEAN)
        estimation_method = f"Empirical Bayes (Cold-Start: {active_days} days observed, prior weight {round(1 - weight, 2)})"
    else:
        daily_burn_rate = user_daily_avg
        estimation_method = f"Historical Moving Average ({active_days} active days observed)"

    daily_burn_rate = round(daily_burn_rate, 2)
    projected_30_day_spend = round(daily_burn_rate * 30, 2)
    projected_month_end_spend = round(current_month_spent + (daily_burn_rate * days_remaining), 2)

    # Risk level assessment
    projected_overshoot = False
    if total_budget_limit > 0 and projected_month_end_spend > total_budget_limit:
        projected_overshoot = True

    return {
        "user_id": user_id,
        "current_month": current_month_str,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "current_month_spent": round(current_month_spent, 2),
        "total_budget_limit": round(total_budget_limit, 2),
        "daily_burn_rate": daily_burn_rate,
        "projected_30_day_spend": projected_30_day_spend,
        "projected_month_end_spend": projected_month_end_spend,
        "is_cold_start": is_cold_start,
        "estimation_method": estimation_method,
        "projected_overshoot": projected_overshoot,
        "category_breakdown": category_breakdown
    }