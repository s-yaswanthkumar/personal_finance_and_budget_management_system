from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Form, Request
from backend.db.postgres import get_db_cursor
from backend.auth_jwt import (
    create_access_token,
    get_current_user_jwt,
    JWT_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def ensure_auth_schema():
    """Ensure username and password columns exist in the users table."""
    try:
        with get_db_cursor(commit=True) as (cur, conn):
            cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(50) UNIQUE;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS password VARCHAR(100);
            """)
            # Update default user 1 if credentials not set
            cur.execute("""
                UPDATE users 
                SET username = 'yaswanth', password = 'password123' 
                WHERE user_id = 1 AND (username IS NULL OR password IS NULL);
            """)
    except Exception as e:
        print("[AUTH] Notice ensuring auth schema:", e)

@router.post("/login", summary="[POST] Login & Obtain JWT Token (Input Fields: Username & Password)")
async def login(
    request: Request,
    username: Optional[str] = Form(None, description="Enter your username or email address", examples=["yaswanth"]),
    password: Optional[str] = Form(None, description="Enter your account password", examples=["password123"])
):
    """
    **Authenticate user credentials and issue a signed JWT access token.**
    
    In Swagger UI:
    - Simply type into the **username** and **password** input fields below (no JSON typing needed!).
    - Click **Execute** to receive your `access_token`.
    - You can also type username and password directly into the green **Authorize** dialog at the top!
    """
    uname = None
    pwd = None

    # 1. Parse JSON body if client submitted application/json (e.g. React frontend or test scripts)
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                uname = body.get("username")
                pwd = body.get("password")
        except Exception:
            pass

    # 2. Fall back to form fields (Swagger UI input boxes / x-www-form-urlencoded)
    if not uname and username:
        uname = username
    if not pwd and password:
        pwd = password

    if not uname or not pwd:
        raise HTTPException(
            status_code=400,
            detail="Both 'username' and 'password' input fields are required."
        )

    uname = uname.strip()
    pwd = pwd.strip()

    with get_db_cursor() as (cur, conn):
        cur.execute("""
            SELECT user_id, name, email, username, password
            FROM users
            WHERE (LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s));
        """, (uname, uname))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="Invalid username or email.")

        user_id, name, email, db_username, db_password = row

        if db_password != pwd:
            raise HTTPException(status_code=401, detail="Incorrect password.")

        effective_username = db_username or uname
        access_token = create_access_token({
            "sub": str(user_id),
            "user_id": user_id,
            "username": effective_username,
            "email": email
        })

        return {
            "success": True,
            "message": "Login successful. Use this access_token with the 'Authorize' button.",
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user_id,
                "name": name,
                "email": email,
                "username": effective_username
            }
        }

@router.post("/register", summary="[POST] Register New User (Input Fields: Username, Password, Name, Email)")
async def register(
    request: Request,
    username: Optional[str] = Form(None, description="Unique username for the new account", examples=["newuser"]),
    password: Optional[str] = Form(None, description="Password for the new account", examples=["secret123"]),
    name: Optional[str] = Form(None, description="Full display name (optional)", examples=["New User"]),
    email: Optional[str] = Form(None, description="Email address (optional)", examples=["newuser@example.com"])
):
    """
    **Register a new user with dedicated form input fields in Swagger UI.**
    
    Auto-provisions isolated baseline accounts (Checking, Savings, Credit Card) & category budgets.
    """
    uname = None
    pwd = None
    display_name = None
    user_email = None

    # 1. Parse JSON body if client submitted application/json
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                uname = body.get("username")
                pwd = body.get("password")
                display_name = body.get("name")
                user_email = body.get("email")
        except Exception:
            pass

    # 2. Fall back to form fields (Swagger UI input boxes)
    if not uname and username:
        uname = username
    if not pwd and password:
        pwd = password
    if not display_name and name:
        display_name = name
    if not user_email and email:
        user_email = email

    if not uname or not pwd:
        raise HTTPException(
            status_code=400,
            detail="Both 'username' and 'password' input fields are required."
        )

    uname = uname.strip()
    pwd = pwd.strip()
    final_name = (display_name or uname).strip()
    final_email = (user_email or f"{uname.lower()}@example.com").strip()

    with get_db_cursor(commit=True) as (cur, conn):
        # Check if username or email already taken
        cur.execute("""
            SELECT user_id FROM users 
            WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s);
        """, (uname, final_email))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Username or email is already registered.")

        # 1. Insert user
        cur.execute("""
            INSERT INTO users (name, email, username, password)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id, name, email, username;
        """, (final_name, final_email, uname, pwd))
        new_user = cur.fetchone()
        user_id, ret_name, ret_email, ret_username = new_user

        # 2. Provision default isolated accounts for this new user
        cur.execute("SELECT name, type_id FROM account_types;")
        type_map = dict(cur.fetchall())

        checking_type = type_map.get('Checking', 2)
        savings_type = type_map.get('Savings', 1)
        credit_type = type_map.get('Credit Card', 3)

        cur.execute("""
            INSERT INTO accounts (user_id, type_id, account_name, balance)
            VALUES 
                (%s, %s, 'Everyday Checking', 2500.00),
                (%s, %s, 'Primary Savings', 5000.00),
                (%s, %s, 'Rewards Credit Card', 0.00);
        """, (user_id, checking_type, user_id, savings_type, user_id, credit_type))

        # 3. Provision default category budgets for current & previous month
        cur.execute("SELECT name, category_id FROM categories;")
        cat_map = dict(cur.fetchall())

        now = datetime.now()
        current_month = now.strftime('%Y-%m')
        prev_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')

        budget_limits = {
            'Groceries': 600.00,
            'Dining': 400.00,
            'Utilities': 250.00,
            'Entertainment': 200.00,
            'Transport': 150.00,
        }

        for m in [prev_month, current_month]:
            for cat_name, limit in budget_limits.items():
                cat_id = cat_map.get(cat_name)
                if cat_id:
                    cur.execute("""
                        INSERT INTO budgets (user_id, category_id, monthly_limit, month_year)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (user_id, category_id, month_year) DO NOTHING;
                    """, (user_id, cat_id, limit, m))

        # Generate signed JWT access token for newly registered user
        access_token = create_access_token({
            "sub": str(user_id),
            "user_id": user_id,
            "username": ret_username,
            "email": ret_email
        })

        return {
            "success": True,
            "message": "User registered successfully with isolated accounts & budgets.",
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user_id,
                "name": ret_name,
                "email": ret_email,
                "username": ret_username
            }
        }

@router.get("/me", summary="[GET] Verify JWT Token & Get Profile (Protected)")
def get_current_user_profile(
    current_user: dict = Depends(get_current_user_jwt)
):
    """
    **GET method to verify JWT Authentication in Swagger Docs.**
    
    Steps to verify:
    1. Click the green **Authorize** button at the top right of Swagger docs.
    2. Enter your username and password, then click Authorize (or enter your Bearer token).
    3. Execute this **GET** endpoint to verify your authenticated identity.
    """
    return {
        "status": "authenticated",
        "message": "JWT Token verified successfully via GET request!",
        "user_id": current_user["user_id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "username": current_user["username"],
        "jwt_claims": current_user["jwt_claims"]
    }

@router.post("/verify-token", summary="[POST] Verify JWT Token & Claims (Protected)")
def verify_jwt_token(
    current_user: dict = Depends(get_current_user_jwt)
):
    """
    **POST method to verify JWT Authentication in Swagger Docs.**
    
    Steps to verify:
    1. Authorize using the Swagger **Authorize** button with your username/password or token.
    2. Execute this **POST** endpoint to verify your token claims.
    """
    return {
        "valid": True,
        "status": "authenticated",
        "message": "JWT Token verified successfully via POST request!",
        "authenticated_user": {
            "user_id": current_user["user_id"],
            "username": current_user["username"],
            "email": current_user["email"],
            "name": current_user["name"]
        },
        "claims": current_user["jwt_claims"]
    }

@router.get("/users", summary="List Available Users")
def list_users():
    """List available users for convenience and testing."""
    with get_db_cursor() as (cur, conn):
        cur.execute("""
            SELECT user_id, name, email, username
            FROM users
            ORDER BY user_id ASC;
        """)
        rows = cur.fetchall()
        return [
            {
                "user_id": r[0],
                "name": r[1],
                "email": r[2],
                "username": r[3] or f"user_{r[0]}"
            }
            for r in rows
        ]

@router.get("/profile", summary="Lookup User Profile by Query Param (Backward Compatibility)")
def get_user_profile_by_id(user_id: int = Query(..., description="Target user ID")):
    """Fetch user profile details by user_id for backward compatibility."""
    with get_db_cursor() as (cur, conn):
        cur.execute("""
            SELECT user_id, name, email, username
            FROM users
            WHERE user_id = %s;
        """, (user_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="User not found.")
        return {
            "user_id": r[0],
            "name": r[1],
            "email": r[2],
            "username": r[3]
        }
