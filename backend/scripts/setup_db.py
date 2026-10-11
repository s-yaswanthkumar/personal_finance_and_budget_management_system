import psycopg2
from backend.config import POSTGRES_URL

def setup_database():
    print("Connecting to PostgreSQL to create schema...")
    conn = psycopg2.connect(POSTGRES_URL)
    conn.autocommit = True
    cur = conn.cursor()

    ddl = """
    DROP VIEW IF EXISTS vw_monthly_summary CASCADE;
    DROP TABLE IF EXISTS budget_alerts CASCADE;
    DROP TABLE IF EXISTS transactions CASCADE;
    DROP TABLE IF EXISTS budgets CASCADE;
    DROP TABLE IF EXISTS accounts CASCADE;
    DROP TABLE IF EXISTS categories CASCADE;
    DROP TABLE IF EXISTS account_types CASCADE;
    DROP TABLE IF EXISTS users CASCADE;

    -- 1. users table
    CREATE TABLE users (
        user_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );

    -- 2. account_types table
    CREATE TABLE account_types (
        type_id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE
    );

    -- 3. accounts table
    CREATE TABLE accounts (
        account_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        type_id INT NOT NULL REFERENCES account_types(type_id),
        account_name VARCHAR(100) NOT NULL,
        balance NUMERIC(12,2) NOT NULL DEFAULT 0.00
    );

    -- 4. categories table
    CREATE TABLE categories (
        category_id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE
    );

    -- 5. budgets table
    CREATE TABLE budgets (
        budget_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        category_id INT NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
        monthly_limit NUMERIC(12,2) NOT NULL,
        month_year VARCHAR(7) NOT NULL,
        CONSTRAINT uq_user_category_month UNIQUE (user_id, category_id, month_year)
    );

    -- 6. transactions table
    CREATE TABLE transactions (
        transaction_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        account_id INT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
        category_id INT NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
        amount NUMERIC(12,2) NOT NULL,
        transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('income', 'expense')),
        raw_memo TEXT,
        transaction_date TIMESTAMP NOT NULL DEFAULT NOW()
    );

    -- 7. budget_alerts audit table
    CREATE TABLE budget_alerts (
        alert_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        category_id INT NOT NULL REFERENCES categories(category_id),
        threshold_pct NUMERIC(5,2) NOT NULL,
        current_spent NUMERIC(12,2) NOT NULL,
        monthly_limit NUMERIC(12,2) NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );

    -- Indexes: Composite B-Tree indexes on transactions
    CREATE INDEX idx_transactions_user_date ON transactions(user_id, transaction_date);
    CREATE INDEX idx_transactions_account_date ON transactions(account_id, transaction_date);

    -- Aggregated View: vw_monthly_summary
    CREATE VIEW vw_monthly_summary AS
    SELECT
        t.user_id,
        t.category_id,
        c.name AS category_name,
        TO_CHAR(t.transaction_date, 'YYYY-MM') AS month_year,
        SUM(CASE WHEN t.transaction_type = 'expense' THEN t.amount ELSE 0 END) AS total_expense,
        SUM(CASE WHEN t.transaction_type = 'income' THEN t.amount ELSE 0 END) AS total_income,
        COUNT(t.transaction_id) AS transaction_count
    FROM transactions t
    JOIN categories c ON t.category_id = c.category_id
    GROUP BY t.user_id, t.category_id, c.name, TO_CHAR(t.transaction_date, 'YYYY-MM');

    -- Active Trigger Function
    CREATE OR REPLACE FUNCTION check_budget_limits()
    RETURNS TRIGGER AS $trg$
    DECLARE
        v_limit NUMERIC(12,2);
        v_current_spent NUMERIC(12,2);
        v_month_year VARCHAR(7);
        v_cat_name VARCHAR(50);
        v_projected_spent NUMERIC(12,2);
    BEGIN
        IF NEW.transaction_type = 'expense' THEN
            v_month_year := TO_CHAR(NEW.transaction_date, 'YYYY-MM');
            
            -- Retrieve monthly budget limit
            SELECT monthly_limit INTO v_limit
            FROM budgets
            WHERE user_id = NEW.user_id 
              AND category_id = NEW.category_id 
              AND month_year = v_month_year;
              
            IF FOUND AND v_limit > 0 THEN
                -- Calculate existing monthly expenses in this category
                SELECT COALESCE(SUM(amount), 0) INTO v_current_spent
                FROM transactions
                WHERE user_id = NEW.user_id
                  AND category_id = NEW.category_id
                  AND transaction_type = 'expense'
                  AND TO_CHAR(transaction_date, 'YYYY-MM') = v_month_year;
                  
                v_projected_spent := v_current_spent + NEW.amount;
                
                -- Rule 1: Exceeds 100% hard cap -> Raise EXCEPTION to abort
                IF v_projected_spent > v_limit THEN
                    SELECT name INTO v_cat_name FROM categories WHERE category_id = NEW.category_id;
                    RAISE EXCEPTION 'Budget hard cap breach: Category "%" limit is $%, attempted total is $%. Transaction aborted.', 
                        v_cat_name, v_limit, v_projected_spent 
                        USING ERRCODE = '23514';
                END IF;
                
                -- Rule 2: Spending reaches >= 80% -> Insert into audit log
                IF v_projected_spent >= (v_limit * 0.80) THEN
                    SELECT name INTO v_cat_name FROM categories WHERE category_id = NEW.category_id;
                    INSERT INTO budget_alerts (user_id, category_id, threshold_pct, current_spent, monthly_limit, message)
                    VALUES (
                        NEW.user_id, 
                        NEW.category_id, 
                        ROUND((v_projected_spent / v_limit) * 100, 2), 
                        v_projected_spent, 
                        v_limit,
                        FORMAT('Warning: Spending in category "%s" has reached %s%% of monthly budget ($%s / $%s)', 
                            v_cat_name, ROUND((v_projected_spent / v_limit) * 100, 1), v_projected_spent, v_limit)
                    );
                END IF;
            END IF;
        END IF;
        RETURN NEW;
    END;
    $trg$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_check_budget_limits
    BEFORE INSERT ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION check_budget_limits();
    """

    cur.execute(ddl)
    print("Schema, Indexes, View, and Active Trigger created successfully!")

    # Insert static seeds for account_types and categories
    print("Seeding baseline types & categories...")
    cur.execute("""
    INSERT INTO account_types (name) VALUES 
        ('Savings'), 
        ('Checking'), 
        ('Credit Card')
    ON CONFLICT (name) DO NOTHING;

    INSERT INTO categories (name) VALUES 
        ('Groceries'), 
        ('Dining'), 
        ('Utilities'), 
        ('Entertainment'), 
        ('Salary'), 
        ('Transport'),
        ('Transfer')
    ON CONFLICT (name) DO NOTHING;
    """)
    print("Seed baseline complete!")
    cur.close()
    conn.close()

if __name__ == '__main__':
    setup_database()
