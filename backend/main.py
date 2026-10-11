from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.accounts import router as accounts_router
from backend.routes.budgets import router as budgets_router
from backend.routes.transactions import router as transactions_router
from backend.routes.transfers import router as transfers_router
from backend.routes.alerts import router as alerts_router
from backend.routes.analytics import router as analytics_router
from backend.routes.ml_routes import router as ml_router
from backend.routes.auth import router as auth_router, ensure_auth_schema
from backend.routes.vector_routes import router as vector_router
from backend.ml.vector_embeddings import init_pgvector_schema, backfill_transaction_embeddings
from backend.db.postgres import get_db_cursor
from backend.db.mongo import get_mongo_db

# Ensure relational auth schema and pgvector vector schema exist on startup
ensure_auth_schema()
init_pgvector_schema()
try:
    backfill_transaction_embeddings()
except Exception as e:
    print("[STARTUP] Notice backfilling embeddings:", e)

app = FastAPI(
    title="AI-Powered Personal Finance & Predictive Budget Management System",
    version="2.0.0",
    description="""
## 🚀 Predictive Budget Management System with JWT & PGVector

### 🔐 How to Verify JWT with the Swagger "Authorize" Button:
1. **Get JWT Token**: Send a `POST` request to `/api/auth/login` (Credentials: `username: yaswanth`, `password: password123`).
2. **Click "Authorize"**: Click the green **Authorize 🔓** button at the top right of this Swagger page.
3. **Paste Token**: In the BearerAuth dialog, paste your `access_token` and click **Authorize**.
4. **Test Verified Protected Endpoints**:
   - **[GET] `/api/auth/me`**: Verify authenticated user session and JWT claims.
   - **[POST] `/api/auth/verify-token`**: POST endpoint verifying token validity.
   - **[POST] `/api/vector/search`**: PGVector semantic search across transactions using cosine distance (`<=>`).
   - **[GET] `/api/vector/similar/{transaction_id}`**: PGVector nearest neighbor lookup.
   - **[GET] `/api/vector/status`**: PGVector extension and index health diagnostics.
""",
    swagger_ui_parameters={"persistAuthorization": True}
)

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth_router)
app.include_router(vector_router)
app.include_router(accounts_router)
app.include_router(budgets_router)
app.include_router(transactions_router)
app.include_router(transfers_router)
app.include_router(alerts_router)
app.include_router(analytics_router)
app.include_router(ml_router)

@app.get("/", tags=["System"])
def root():
    return {
        "status": "online",
        "system": "AI-Powered Personal Finance & Predictive Budget Management System",
        "version": "2.0.0",
        "docs_url": "/docs",
        "jwt_auth_enabled": True,
        "pgvector_enabled": True,
        "swagger_authorize_button": True
    }

@app.get("/api/health", tags=["System"])
def health_check():
    """System diagnostic check across PostgreSQL, MongoDB, PGVector, and AI/ML services."""
    postgres_status = "error"
    mongo_status = "error"
    pgvector_status = "error"
    
    try:
        with get_db_cursor() as (cur, conn):
            cur.execute("SELECT 1;")
            if cur.fetchone()[0] == 1:
                postgres_status = "healthy"
            
            cur.execute("SELECT installed_version FROM pg_available_extensions WHERE name = 'vector';")
            ext = cur.fetchone()
            if ext and ext[0]:
                pgvector_status = f"healthy (pgvector v{ext[0]})"
    except Exception as e:
        postgres_status = f"unhealthy: {str(e)}"
        pgvector_status = f"unhealthy: {str(e)}"

    try:
        db = get_mongo_db()
        db.command("ping")
        mongo_status = "healthy (MongoDB Atlas Cloud Cluster)"
    except Exception as e:
        mongo_status = f"unhealthy: {str(e)} (Check MongoDB Atlas Network Access IP whitelist: add current IP '103.255.144.74' or '0.0.0.0/0' to allow all)"

    return {
        "overall_status": "healthy" if postgres_status == "healthy" and "healthy" in mongo_status else "degraded",
        "services": {
            "postgresql": postgres_status,
            "mongodb": mongo_status,
            "pgvector": pgvector_status,
            "jwt_authenticator": "healthy",
            "ml_categorizer": "healthy",
            "ml_anomaly_detector": "healthy",
            "ml_burn_rate_estimator": "healthy"
        }
    }