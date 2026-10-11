-- ====================================================================
-- Predictive Budget Management System - PostgreSQL & PGVector Schema
-- ====================================================================

-- 1. Enable PGVector Extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Drop existing views and tables if rebuilding
DROP VIEW IF EXISTS vw_monthly_summary CASCADE;
DROP TABLE IF EXISTS budget_alerts CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS budgets CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS account_types CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 3. Users Table (Authentication & User Profile)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Account Types Table (Savings, Checking, Credit Card)
CREATE TABLE account_types (
    type_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- 5. Accounts Table (Financial ledgers)
CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    type_id INT NOT NULL REFERENCES account_types(type_id),
    account_name VARCHAR(100) NOT NULL,
    balance NUMERIC(12,2) NOT NULL DEFAULT 0.00
);

-- 6. Categories Table (Budget & Transaction taxonomy)
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- 7. Budgets Table (Monthly spending limits per category)
CREATE TABLE budgets (
    budget_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    category_id INT NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
    monthly_limit NUMERIC(12,2) NOT NULL,
    month_year VARCHAR(7) NOT NULL,
    CONSTRAINT uq_user_category_month UNIQUE (user_id, category_id, month_year)
);

-- 8. Transactions Table (with PGVector 64-dim dense embedding)
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    account_id INT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    category_id INT NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
    amount NUMERIC(12,2) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('income', 'expense')),
    raw_memo TEXT,
    transaction_date TIMESTAMP NOT NULL DEFAULT NOW(),
    embedding vector(64)
);

-- 9. Budget Alerts Audit Log Table
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

-- 10. Performance Indexes
CREATE INDEX idx_transactions_user_date ON transactions(user_id, transaction_date);
CREATE INDEX idx_transactions_account_date ON transactions(account_id, transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_embedding_hnsw ON transactions USING hnsw (embedding vector_cosine_ops);

-- 11. Materialized / Aggregated Summary View
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

-- 12. Active PL/pgSQL Trigger: Hard Cap & 80% Warning Enforcement
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

-- 13. Baseline Master Data Seeding
INSERT INTO account_types (type_id, name) VALUES 
    (1, 'Savings'), 
    (2, 'Checking'), 
    (3, 'Credit Card')
ON CONFLICT (name) DO NOTHING;

INSERT INTO categories (category_id, name) VALUES 
    (1, 'Groceries'), 
    (2, 'Dining'), 
    (3, 'Utilities'), 
    (4, 'Entertainment'), 
    (5, 'Salary'), 
    (6, 'Transport'),
    (7, 'Transfer')
ON CONFLICT (name) DO NOTHING;

-- Default Users
INSERT INTO users (user_id, name, username, email, password) VALUES
    (1, 'Sukhavasi Yaswanth', 'yaswanth', 'yaswanth@example.com', 'password123'),
    (2, 'Demo User', 'demouser', 'demouser@example.com', 'demo123')
ON CONFLICT (user_id) DO UPDATE 
    SET username = EXCLUDED.username, password = EXCLUDED.password;

SELECT setval('users_user_id_seq', (SELECT COALESCE(MAX(user_id), 1) FROM users));
SELECT setval('account_types_type_id_seq', (SELECT COALESCE(MAX(type_id), 1) FROM account_types));
SELECT setval('categories_category_id_seq', (SELECT COALESCE(MAX(category_id), 1) FROM categories));
