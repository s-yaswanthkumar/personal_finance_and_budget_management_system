"""
Flask API Implementation with JWT Authentication, Swagger UI with 'Authorize' Button, and PGVector.
Run standalone with: python -m backend.flask_api
Access Swagger UI at: http://127.0.0.1:5000/apidocs
"""
import os
from functools import wraps
from flask import Flask, request, jsonify
from flasgger import Swagger
from backend.db.postgres import get_db_cursor
from backend.auth_jwt import (
    create_access_token,
    decode_access_token,
    JWT_EXPIRE_MINUTES
)
from backend.ml.vector_embeddings import (
    semantic_search_transactions,
    find_similar_transactions,
    generate_embedding,
    init_pgvector_schema,
    VECTOR_DIM
)
from backend.ml.forecast import get_user_daily_forecast

app = Flask(__name__)

# Configure Flasgger Swagger with Bearer Token Authorization Button
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Predictive Budget Management - Flask API with JWT & PGVector",
        "description": "Flask REST API implementation featuring JWT authentication, Swagger UI with 'Authorize' button, and PostgreSQL PGVector semantic similarity search.",
        "version": "2.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Enter: Bearer <your_token>"
        }
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

def jwt_required_flask(f):
    """Decorator to require JWT Bearer token on Flask routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({
                "error": "Unauthorized",
                "detail": "Missing Authorization header. Click 'Authorize' in Swagger UI and provide your JWT Bearer token."
            }), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({
                "error": "Unauthorized",
                "detail": "Invalid Authorization header format. Expected 'Bearer <token>'."
            }), 401
        
        token = parts[1]
        try:
            payload = decode_access_token(token)
        except Exception as e:
            return jsonify({"error": "Unauthorized", "detail": str(e)}), 401

        user_id = payload.get("user_id") or payload.get("sub")
        with get_db_cursor() as (cur, conn):
            cur.execute("SELECT user_id, name, email, username FROM users WHERE user_id = %s;", (int(user_id),))
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "Unauthorized", "detail": "User not found."}), 401
            
            request.current_user = {
                "user_id": row[0],
                "name": row[1],
                "email": row[2],
                "username": row[3],
                "jwt_claims": payload
            }
        
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET"])
def flask_root():
    return jsonify({
        "status": "online",
        "framework": "Flask API",
        "swagger_docs": "/apidocs",
        "features": ["JWT Authentication", "Swagger Authorize Button", "PGVector Cosine Distance"]
    })

@app.route("/api/auth/login", methods=["POST"])
def flask_login():
    """
    Login and obtain JWT Bearer Token
    ---
    tags:
      - Authentication
    consumes:
      - application/x-www-form-urlencoded
      - application/json
    parameters:
      - name: username
        in: formData
        type: string
        required: true
        description: Enter your username or email address
        default: yaswanth
      - name: password
        in: formData
        type: string
        required: true
        description: Enter your account password
        default: password123
    responses:
      200:
        description: Returns JWT access token
      401:
        description: Incorrect credentials
    """
    uname = request.form.get("username")
    pwd = request.form.get("password")
    if not uname or not pwd:
        data = request.get_json(silent=True) or {}
        uname = uname or data.get("username")
        pwd = pwd or data.get("password")
    uname = (uname or "").strip()
    pwd = (pwd or "").strip()

    with get_db_cursor() as (cur, conn):
        cur.execute("""
            SELECT user_id, name, email, username, password
            FROM users
            WHERE (LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s));
        """, (uname, uname))
        row = cur.fetchone()
        if not row or row[4] != pwd:
            return jsonify({"error": "Unauthorized", "detail": "Invalid credentials."}), 401
        
        user_id, name, email, db_uname, _ = row
        token = create_access_token({
            "sub": str(user_id),
            "user_id": user_id,
            "username": db_uname or uname,
            "email": email
        })

        return jsonify({
            "success": True,
            "message": "Login successful. Use this token with the Swagger 'Authorize' button.",
            "access_token": token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user_id,
                "name": name,
                "email": email,
                "username": db_uname or uname
            }
        })

@app.route("/api/auth/me", methods=["GET"])
@jwt_required_flask
def flask_get_me():
    """
    [GET] Verify JWT Token & Get Authenticated User Profile (Protected)
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Token verified successfully
      401:
        description: Missing or invalid token
    """
    user = request.current_user
    return jsonify({
        "status": "authenticated",
        "message": "JWT Token successfully verified in Flask API via GET method!",
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user["email"],
        "name": user["name"],
        "claims": user["jwt_claims"]
    })

@app.route("/api/auth/verify-token", methods=["POST"])
@jwt_required_flask
def flask_verify_token():
    """
    [POST] Verify JWT Token & Claims (Protected)
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Token verified successfully via POST
      401:
        description: Missing or invalid token
    """
    user = request.current_user
    return jsonify({
        "valid": True,
        "status": "authenticated",
        "message": "JWT Token successfully verified in Flask API via POST method!",
        "user_id": user["user_id"],
        "username": user["username"],
        "claims": user["jwt_claims"]
    })

@app.route("/api/vector/search", methods=["POST"])
@jwt_required_flask
def flask_vector_search():
    """
    [POST] PGVector Semantic Search (Protected)
    ---
    tags:
      - PGVector Semantic Search
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - query
          properties:
            query:
              type: string
              example: Pizza delivery dining
            top_k:
              type: integer
              default: 5
    responses:
      200:
        description: Semantically ranked transactions using PostgreSQL pgvector (<=>)
      401:
        description: Unauthorized
    """
    user = request.current_user
    data = request.get_json() or {}
    query_text = data.get("query", "").strip()
    top_k = int(data.get("top_k", 5))

    results = semantic_search_transactions(user_id=user["user_id"], query_text=query_text, top_k=top_k)
    return jsonify({
        "status": "success",
        "user_id": user["user_id"],
        "query": query_text,
        "vector_dimension": VECTOR_DIM,
        "engine": "PostgreSQL pgvector cosine distance (<=>)",
        "results_count": len(results),
        "results": results
    })

@app.route("/api/vector/similar/<int:transaction_id>", methods=["GET"])
@jwt_required_flask
def flask_vector_similar(transaction_id):
    """
    [GET] Find Similar Transactions using PGVector (Protected)
    ---
    tags:
      - PGVector Semantic Search
    security:
      - Bearer: []
    parameters:
      - name: transaction_id
        in: path
        type: integer
        required: true
        example: 1
      - name: top_k
        in: query
        type: integer
        default: 5
    responses:
      200:
        description: Nearest neighbor transactions
      401:
        description: Unauthorized
    """
    user = request.current_user
    top_k = int(request.args.get("top_k", 5))
    results = find_similar_transactions(transaction_id=transaction_id, user_id=user["user_id"], top_k=top_k)
    return jsonify({
        "status": "success",
        "user_id": user["user_id"],
        "target_transaction_id": transaction_id,
        "similar_count": len(results),
        "similar_transactions": results
    })

@app.route("/api/vector/status", methods=["GET"])
@jwt_required_flask
def flask_vector_status():
    """
    [GET] PGVector Extension Diagnostic (Protected)
    ---
    tags:
      - PGVector Semantic Search
    security:
      - Bearer: []
    responses:
      200:
        description: PGVector diagnostic details
      401:
        description: Unauthorized
    """
    user = request.current_user
    with get_db_cursor() as (cur, conn):
        cur.execute("SELECT installed_version FROM pg_available_extensions WHERE name = 'vector';")
        ext = cur.fetchone()
        cur.execute("SELECT count(*) FROM transactions WHERE user_id = %s AND embedding IS NOT NULL;", (user["user_id"],))
        embedded_count = cur.fetchone()[0]
        return jsonify({
            "pgvector_version": ext[0] if ext else None,
            "vector_dimension": VECTOR_DIM,
            "embedded_transactions_count": embedded_count,
            "status": "healthy"
        })

@app.route("/api/analytics/daily-forecast", methods=["GET"])
@jwt_required_flask
def flask_daily_forecast():
    """
    [GET] AI Daily Spending Prediction (Next 30 Days)
    ---
    tags:
      - ML Predictive Analytics
    security:
      - Bearer: []
    parameters:
      - name: days
        in: query
        type: integer
        default: 30
        description: Forecast horizon in days (7 to 90)
    responses:
      200:
        description: Day-by-day expenditure forecast with probabilities and amounts
      401:
        description: Unauthorized
    """
    user = request.current_user
    days = int(request.args.get("days", 30))
    forecast = get_user_daily_forecast(user_id=user["user_id"], days=days)
    return jsonify(forecast)

if __name__ == "__main__":
    init_pgvector_schema()
    port = int(os.getenv("FLASK_PORT", 5000))
    print(f"Starting Flask API on http://127.0.0.1:{port}")
    print(f"Swagger Docs available at: http://127.0.0.1:{port}/apidocs")
    app.run(host="127.0.0.1", port=port, debug=True)
