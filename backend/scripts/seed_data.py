import random
from datetime import datetime, timedelta
from backend.db.postgres import get_db_cursor
from backend.db.mongo import log_alert
from backend.ml.vector_embeddings import backfill_transaction_embeddings

def seed_all():
    print("Starting database seeding tailored for an urban Indian lifestyle across 60 days (INR)...")
    with get_db_cursor(commit=True) as (cur, conn):
        # 1. Seed test users
        cur.execute("""
            INSERT INTO users (user_id, name, email, username, password)
            VALUES 
                (1, 'Sukhavasi Yaswanth', 'yaswanth@example.com', 'yaswanth', 'password123'),
                (2, 'Demo User', 'demouser@example.com', 'demouser', 'demo123')
            ON CONFLICT (user_id) DO UPDATE 
                SET name = EXCLUDED.name, email = EXCLUDED.email, 
                    username = EXCLUDED.username, password = EXCLUDED.password;
        """)
        cur.execute("SELECT setval('users_user_id_seq', (SELECT MAX(user_id) FROM users));")

        # 2. Seed accounts with realistic Indian Rupee (INR ₹) balances
        cur.execute("SELECT name, type_id FROM account_types;")
        type_map = dict(cur.fetchall())

        cur.execute("""
            INSERT INTO accounts (account_id, user_id, type_id, account_name, balance)
            VALUES 
                (1, 1, %s, 'Primary Savings (SBI/HDFC)', 250000.00),
                (2, 1, %s, 'Everyday Checking (HDFC Salary)', 45000.00),
                (3, 1, %s, 'Rewards Credit Card (HDFC Regalia)', 0.00),
                (4, 2, %s, 'Everyday Checking', 32000.00),
                (5, 2, %s, 'Primary Savings', 180000.00),
                (6, 2, %s, 'Rewards Credit Card', 0.00)
            ON CONFLICT (account_id) DO UPDATE 
                SET balance = EXCLUDED.balance, account_name = EXCLUDED.account_name;
        """, (
            type_map['Savings'], type_map['Checking'], type_map['Credit Card'],
            type_map['Checking'], type_map['Savings'], type_map['Credit Card']
        ))
        cur.execute("SELECT setval('accounts_account_id_seq', (SELECT MAX(account_id) FROM accounts));")

        # 3. Seed monthly budgets realistic for an Indian urban household
        cur.execute("SELECT name, category_id FROM categories;")
        cat_map = dict(cur.fetchall())

        now = datetime.now()
        current_month = now.strftime('%Y-%m')
        prev_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')

        # Realistic monthly limits in INR
        budget_limits = {
            'Groceries': 25000.00,    # Blinkit, Zepto, DMart, BigBasket
            'Dining': 18000.00,       # Swiggy, Zomato, Chai Point, Biryani, Weekend dining
            'Utilities': 8500.00,     # Bescom Electricity, BWSSB Water, Airtel Fiber, Jio 5G, LPG Gas
            'Entertainment': 6000.00, # BookMyShow PVR, Hotstar, Netflix India, Spotify
            'Transport': 10000.00,    # Ola Cabs, Namma Metro, Indian Oil Fuel, FASTag, Uber
        }

        two_months_ago = (now.replace(day=1) - timedelta(days=32)).strftime('%Y-%m')

        for uid in [1, 2]:
            for m in [two_months_ago, prev_month, current_month]:
                for cat_name, limit in budget_limits.items():
                    cat_id = cat_map.get(cat_name)
                    if cat_id:
                        cur.execute("""
                            INSERT INTO budgets (user_id, category_id, monthly_limit, month_year)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (user_id, category_id, month_year) 
                            DO UPDATE SET monthly_limit = EXCLUDED.monthly_limit;
                        """, (uid, cat_id, limit, m))

        # 4. Generate 60 days of historical transactions spanning every day of the month
        cur.execute("ALTER TABLE transactions DISABLE TRIGGER trg_check_budget_limits;")
        cur.execute("DELETE FROM transactions WHERE user_id IN (1, 2);")
        cur.execute("DELETE FROM budget_alerts WHERE user_id IN (1, 2);")

        # Seed salary income bi-weekly for user 1 & 2 (INR ₹47,500 bi-weekly = ~₹95,000 monthly take-home)
        for days_ago in [58, 44, 30, 16, 2]:
            tx_date = now - timedelta(days=days_ago, hours=9)
            cur.execute("""
                INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                VALUES 
                    (1, 2, %s, 47500.00, 'income', 'TCS Tata Consultancy Services Payroll Direct Deposit', %s),
                    (2, 4, %s, 52000.00, 'income', 'Infosys Technologies Monthly Salary Credit', %s);
            """, (cat_map['Salary'], tx_date, cat_map['Salary'], tx_date))

        random.seed(42)  # Deterministic seed for reproducible testing

        for day in range(59, -1, -1):
            target_date = now - timedelta(days=day)
            dow = target_date.weekday()  # 0=Monday, 6=Sunday
            dom = target_date.day        # Day of month (1-31)

            # A. Recurring Monthly Indian Utility & Subscription Bills on fixed dates
            if dom == 5:
                # Airtel Xstream Fiber Broadband (₹1,179)
                tx_time = target_date.replace(hour=8, minute=15)
                cur.execute("""
                    INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                    VALUES (1, 2, %s, 1179.00, 'expense', 'Airtel Xstream Fiber Broadband Bill', %s);
                """, (cat_map['Utilities'], tx_time))
            elif dom == 10:
                # Jio 5G Monthly Mobile Recharge (₹449)
                tx_time = target_date.replace(hour=9, minute=30)
                cur.execute("""
                    INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                    VALUES (1, 2, %s, 449.00, 'expense', 'Jio 5G Monthly Mobile Recharge', %s);
                """, (cat_map['Utilities'], tx_time))
            elif dom == 12:
                # Netflix India Premium Plan (₹649)
                tx_time = target_date.replace(hour=10, minute=45)
                cur.execute("""
                    INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                    VALUES (1, 3, %s, 649.00, 'expense', 'Netflix Monthly Subscription', %s);
                """, (cat_map['Entertainment'], tx_time))
            elif dom == 15:
                # Bescom Electricity Bill Bangalore (₹2,450)
                tx_time = target_date.replace(hour=14, minute=0)
                cur.execute("""
                    INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                    VALUES (1, 2, %s, 2450.00, 'expense', 'Bescom Electricity Bill Bangalore', %s);
                """, (cat_map['Utilities'], tx_time))
            elif dom == 20:
                # BWSSB Water Supply & Sewerage Board (₹620)
                tx_time = target_date.replace(hour=11, minute=30)
                cur.execute("""
                    INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                    VALUES (1, 2, %s, 620.00, 'expense', 'BWSSB Water Supply Board', %s);
                """, (cat_map['Utilities'], tx_time))
            elif dom == 22:
                # Indane LPG Domestic Gas Cylinder Refill (₹950)
                tx_time = target_date.replace(hour=15, minute=10)
                cur.execute("""
                    INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                    VALUES (1, 2, %s, 950.00, 'expense', 'Indane LPG Gas Cylinder Booking', %s);
                """, (cat_map['Utilities'], tx_time))
            elif dom == 25:
                # Spotify India Premium (₹119)
                tx_time = target_date.replace(hour=16, minute=20)
                cur.execute("""
                    INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                    VALUES (1, 3, %s, 119.00, 'expense', 'Spotify India Music Premium', %s);
                """, (cat_map['Entertainment'], tx_time))

            # B. Daily Indian Living Cadence based on Day of Week
            # Occasional light spending or zero discretionary spend days
            is_zero_spend_day = (day in [7, 19, 33, 47]) and (dow in [1, 2])

            if not is_zero_spend_day:
                if dow in [0, 1, 3]:  # Monday, Tuesday, Thursday (Standard workdays)
                    # 1. Morning Commute: Namma Metro, Ola, or Rapido
                    metro_or_cab = random.choice([
                        ('Namma Metro Smart Card Recharge', 200.0, 300.0),
                        ('Ola Cabs City Ride Fare', 160.0, 280.0),
                        ('Rapido Bike Taxi Fare', 65.0, 110.0),
                        ('Uber India Auto Go Trip', 110.0, 190.0)
                    ])
                    commute_memo, c_min, c_max = metro_or_cab
                    cur.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                        VALUES (1, 2, %s, %s, 'expense', %s, %s);
                    """, (cat_map['Transport'], round(random.uniform(c_min, c_max), 2), commute_memo, target_date.replace(hour=8, minute=random.randint(15, 45))))

                    # 2. Chai / Coffee: Chai Point or Blue Tokai
                    chai_or_coffee = random.choice([
                        ('Chai Point Tea Snacks Cafe', 90.0, 160.0),
                        ('Blue Tokai Coffee Roasters', 210.0, 320.0)
                    ])
                    cur.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                        VALUES (1, 2, %s, %s, 'expense', %s, %s);
                    """, (cat_map['Dining'], round(random.uniform(chai_or_coffee[1], chai_or_coffee[2]), 2), chai_or_coffee[0], target_date.replace(hour=10, minute=random.randint(15, 50))))

                    # 3. Lunch: Swiggy or Saravana Bhavan
                    lunch_choice = random.choice([
                        ('Swiggy Food Delivery Order', 220.0, 420.0),
                        ('Saravana Bhavan Dosa Lunch', 180.0, 310.0)
                    ])
                    cur.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                        VALUES (1, 2, %s, %s, 'expense', %s, %s);
                    """, (cat_map['Dining'], round(random.uniform(lunch_choice[1], lunch_choice[2]), 2), lunch_choice[0], target_date.replace(hour=13, minute=random.randint(10, 40))))

                    # 4. Quick evening grocery or snack: Zepto or Blinkit (35% probability)
                    if random.random() < 0.35:
                        quick_grocer = random.choice([
                            ('Zepto 10-Min Supermarket', 280.0, 580.0),
                            ('Blinkit Quick Grocery Delivery', 340.0, 690.0)
                        ])
                        cur.execute("""
                            INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                            VALUES (1, 2, %s, %s, 'expense', %s, %s);
                        """, (cat_map['Groceries'], round(random.uniform(quick_grocer[1], quick_grocer[2]), 2), quick_grocer[0], target_date.replace(hour=19, minute=random.randint(15, 55))))

                elif dow == 2:  # Wednesday (Mid-week grocery refresh via BigBasket / Instamart)
                    cur.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                        VALUES (1, 2, %s, %s, 'expense', 'BigBasket Daily Mart Superstore', %s);
                    """, (cat_map['Groceries'], round(random.uniform(950.0, 1650.0), 2), target_date.replace(hour=18, minute=20)))
                    cur.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                        VALUES (1, 2, %s, %s, 'expense', 'Chai Point Tea Snacks Cafe', %s);
                    """, (cat_map['Dining'], round(random.uniform(95.0, 160.0), 2), target_date.replace(hour=16, minute=30)))

                elif dow == 4:  # Friday (Commute + Friday Biryani / Dinner Celebration)
                    cur.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                        VALUES (1, 2, %s, %s, 'expense', 'Ola Cabs City Ride Fare', %s);
                    """, (cat_map['Transport'], round(random.uniform(220.0, 380.0), 2), target_date.replace(hour=9, minute=15)))
                    
                    friday_treat = random.choice([
                        ('Behrouz Biryani Royal Feast', 580.0, 1150.0),
                        ("Domino's Pizza Delivery", 490.0, 890.0),
                        ('Zomato Restaurant Delivery', 520.0, 950.0)
                    ])
                    cur.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                        VALUES (1, 3, %s, %s, 'expense', %s, %s);
                    """, (cat_map['Dining'], round(random.uniform(friday_treat[1], friday_treat[2]), 2), friday_treat[0], target_date.replace(hour=20, minute=15)))

                elif dow == 5:  # Saturday (DMart Supermarket + Evening Buffet Outing + Movie)
                    # Major supermarket restock
                    grocery_trip = random.choice([
                        ('DMart Ready Hypermarket Retail', 2400.0, 4800.0),
                        ("Nature's Basket Organic Market", 1600.0, 2900.0)
                    ])
                    cur.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                        VALUES (1, 2, %s, %s, 'expense', %s, %s);
                    """, (cat_map['Groceries'], round(random.uniform(grocery_trip[1], grocery_trip[2]), 2), grocery_trip[0], target_date.replace(hour=11, minute=30)))

                    # Evening dinner outing
                    dining_out = random.choice([
                        ('Barbeque Nation Buffet Dinner', 1600.0, 2600.0),
                        ("Haldiram's Sweets and Restaurant", 650.0, 1250.0)
                    ])
                    cur.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                        VALUES (1, 3, %s, %s, 'expense', %s, %s);
                    """, (cat_map['Dining'], round(random.uniform(dining_out[1], dining_out[2]), 2), dining_out[0], target_date.replace(hour=20, minute=30)))

                    # Movie / Cinema (65% chance)
                    if random.random() < 0.65:
                        cur.execute("""
                            INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                            VALUES (1, 3, %s, %s, 'expense', 'BookMyShow PVR Cinemas Ticket', %s);
                        """, (cat_map['Entertainment'], round(random.uniform(550.0, 1150.0), 2), target_date.replace(hour=16, minute=45)))

                elif dow == 6:  # Sunday (Family brunch + Fuel / FASTag recharge)
                    sunday_dining = random.choice([
                        ('Saravana Bhavan Dosa Lunch', 420.0, 780.0),
                        ('Swiggy Food Delivery Order', 550.0, 1050.0)
                    ])
                    cur.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                        VALUES (1, 3, %s, %s, 'expense', %s, %s);
                    """, (cat_map['Dining'], round(random.uniform(sunday_dining[1], sunday_dining[2]), 2), sunday_dining[0], target_date.replace(hour=13, minute=15)))

                    fuel_or_fastag = random.choice([
                        ('Indian Oil Petrol Pump Fuel IOCL', 1800.0, 2700.0),
                        ('FASTag Highway Toll Recharge', 500.0, 1000.0)
                    ])
                    cur.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                        VALUES (1, 2, %s, %s, 'expense', %s, %s);
                    """, (cat_map['Transport'], round(random.uniform(fuel_or_fastag[1], fuel_or_fastag[2]), 2), fuel_or_fastag[0], target_date.replace(hour=16, minute=45)))

            # Seed a parallel subset for User 2 (Demo User)
            if day % 2 == 0 and not is_zero_spend_day:
                u2_cat = 'Groceries' if dow in [5, 6] else 'Dining'
                u2_memo = 'Blinkit Quick Grocery Delivery' if u2_cat == 'Groceries' else 'Zomato Restaurant Delivery'
                cur.execute("""
                    INSERT INTO transactions (user_id, account_id, category_id, amount, transaction_type, raw_memo, transaction_date)
                    VALUES (2, 4, %s, %s, 'expense', %s, %s);
                """, (cat_map[u2_cat], round(random.uniform(350.0, 1250.0), 2), u2_memo, target_date.replace(hour=14, minute=0)))

        # Re-enable trigger
        cur.execute("ALTER TABLE transactions ENABLE TRIGGER trg_check_budget_limits;")
        print("60 days of Indian monthly lifestyle transactions generated successfully!")

        # 5. Update account balances accurately from ledger (in INR ₹)
        cur.execute("""
            UPDATE accounts a
            SET balance = (
                SELECT COALESCE(
                    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE -amount END),
                    0
                )
                FROM transactions t
                WHERE t.account_id = a.account_id
            ) + 150000.00;
        """)

    # 6. Backfill PGVector 64-D embeddings for all Indian transactions
    print("Generating PGVector semantic embeddings for Indian transactions...")
    updated_embeddings = backfill_transaction_embeddings()
    print(f"Generated {updated_embeddings} PGVector semantic embeddings!")

    # 7. Seed initial MongoDB alert logs in Atlas cloud cluster with Indian context
    print("Seeding initial MongoDB alert logs in Atlas cloud cluster (INR)...")
    try:
        log_alert(
            user_id=1,
            alert_type="budget_warning",
            category="Dining",
            message="Warning: Spending in category 'Dining' has reached 82.5% of monthly budget (Rs. 8,250.00 / Rs. 10,000.00)",
            severity="warning",
            metadata={"threshold_pct": 82.5, "current_spent": 8250.0, "monthly_limit": 10000.0}
        )
        log_alert(
            user_id=1,
            alert_type="anomaly",
            category="Transport",
            message="Anomaly detected: Flight booking charges Rs. 14,850.00 deviates 6.8x from standard Transport transaction average.",
            severity="anomaly",
            metadata={"amount": 14850.0, "category": "Transport"}
        )
        print("Initial Indian MongoDB alert logs seeded successfully in Atlas!")
    except Exception as e:
        print("Notice: MongoDB alert seeding error:", e)

    print("Database seeding for Indian monthly spending complete!")

if __name__ == '__main__':
    seed_all()