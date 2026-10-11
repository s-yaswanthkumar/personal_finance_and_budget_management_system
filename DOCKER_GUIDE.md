# 🐳 Docker Containerization Guide

## AI-Powered Personal Finance & Predictive Budget Management System

This project is fully containerized with **Docker** and **Docker Compose**, providing an isolated, portable, and production-grade environment for the complete polyglot application stack.

---

## 🏛️ System Architecture in Docker

```
                                      Host Machine
  ====================================================================================
           | :5173 / :8080                               | :8000           | :5433
           v                                             v                 v
  +------------------+                          +-----------------+ +----------------+
  |  React Frontend  |                          | FastAPI Backend | |   PostgreSQL   |
  |  (Nginx Alpine)  | ---- /api/ reverse proxy | (Python 3.11)   | | (PGVector v16) |
  +------------------+                          +-----------------+ +----------------+
           |                                             |                 |
           +---------------------------------------------+-----------------+
                                         |
                          Internal Docker Bridge Network
                              (`budget-network`)
                                         |
                                         v
                         +-------------------------------+
                         | MongoDB Atlas Cloud Cluster   |
                         | (or optional local container) |
                         +-------------------------------+
```

### Services Breakdown:
1. **`frontend` (React + Nginx)**:
   - Multi-stage Docker build (`node:20-alpine` -> `nginx:alpine`).
   - Serves the Spendee-styled responsive Single Page Application.
   - Built-in Nginx reverse proxy routing `/api/` directly to the `backend` container without CORS restrictions.
   - Accessible on `http://localhost:5173` and `http://localhost:8080`.
2. **`backend` (FastAPI + PGVector + Scikit-Learn)**:
   - Lightweight `python:3.11-slim` container with PostgreSQL client headers and C-extensions.
   - Runs `uvicorn` on port `8000`.
   - Entrypoint script automatically verifies database readiness and seeds schema/data on first run.
   - Exposes Swagger UI at `http://localhost:8000/docs` and diagnostics at `http://localhost:8000/api/health`.
3. **`postgres` (PostgreSQL 16 with PGVector)**:
   - Powered by official image `pgvector/pgvector:pg16`.
   - Pre-loaded with `01-init.sql` for table schemas, indexes, triggers, and baseline seeds.
   - Accessible from the host machine on port `5433` (preventing collision if you have Windows PostgreSQL running on port `5432`).
   - Persistent volume `budget_postgres_data` guarantees data preservation across restarts.
4. **`mongo` (MongoDB Cloud / Local)**:
   - Primary: Connects directly to the MongoDB Atlas Cloud cluster specified in `.env.docker`.
   - Optional local offline mode supported via `docker compose --profile offline up -d`.

---

## 🚀 Quick Start (One-Click)

### Windows (Batch Launcher)
Simply double-click:
```cmd
start_docker.bat
```
This script will:
1. Check that Docker Desktop is running (and launch it if idle).
2. Build container images and boot services in the background.
3. Wait for all container health checks to report healthy.
4. Open the web app (`http://localhost:5173`), Swagger UI (`http://localhost:8000/docs`), and health status in your browser.

To stop the containers:
```cmd
stop_docker.bat
```

---

## 💻 Command-Line Usage

### 1. Build and Start Services
```bash
# Start all containers in the background
docker compose up --build -d

# Start with live logs in the foreground
docker compose up --build
```

### 2. View Service Logs
```bash
# Follow logs from all containers
docker compose logs -f

# Follow logs from the backend only
docker compose logs -f backend

# Follow logs from the database
docker compose logs -f postgres
```

### 3. Check Container Status and Health
```bash
docker compose ps
```

### 4. Stop Services
```bash
# Stop and remove containers (keeps database volume intact)
docker compose down

# Stop and wipe database volume (clean slate reset)
docker compose down -v
```

---

## 🌐 Container Endpoints & Credentials

| Service | Host URL / Port | Container Port | Purpose |
| :--- | :--- | :--- | :--- |
| **React Web App** | `http://localhost:5173` | `80` | Spendee-grade Dashboard & Budgeting |
| **Web App (Alt)** | `http://localhost:8080` | `80` | Alternative HTTP port |
| **FastAPI Backend** | `http://localhost:8000` | `8000` | REST API Root |
| **Swagger UI** | `http://localhost:8000/docs` | `8000` | Interactive OpenAPI with JWT Auth |
| **Health API** | `http://localhost:8000/api/health`| `8000` | Database & ML service diagnostics |
| **PostgreSQL** | `localhost:5433` | `5432` | Relational & PGVector database |
| **MongoDB** | MongoDB Atlas Cloud | `27017` | Unstructured audit logs & event store |

### Demo Login Credentials:
- **Primary User**: Username: `yaswanth` | Password: `password123` (Sukhavasi Yaswanth)
- **Demo User**: Username: `demouser` | Password: `demo123`

---

## ⚙️ Environment Configuration (`.env.docker`)

You can customize port bindings and database credentials in `.env.docker`:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_PGADMIN_PASSWORD
POSTGRES_DB=budget_management_system
POSTGRES_PORT=5433

BACKEND_PORT=8000
FRONTEND_PORT=5173
FRONTEND_HTTP_PORT=8080

MONGO_URI=mongodb+srv://<username>:<password>@<your-cluster>.mongodb.net/budget_management_system?retryWrites=true&w=majority
```

---

## 🧪 Testing the Dockerized Services

### 1. Diagnostic Health Check
```bash
curl http://localhost:8000/api/health
```
Expected output:
```json
{
  "overall_status": "healthy",
  "services": {
    "postgresql": "healthy",
    "mongodb": "healthy (MongoDB Atlas Cloud Cluster)",
    "pgvector": "healthy (pgvector v0.8.0)",
    "jwt_authenticator": "healthy",
    "ml_categorizer": "healthy",
    "ml_anomaly_detector": "healthy",
    "ml_burn_rate_estimator": "healthy"
  }
}
```

### 2. Semantic PGVector Search inside Docker
```bash
curl -X POST "http://localhost:8000/api/vector/search" \
     -H "Content-Type: application/json" \
     -d '{"user_id": 1, "query": "grocery shopping supermarket", "top_k": 3}'
```

### 3. Accessing the PostgreSQL Container CLI
```bash
docker exec -it budget-postgres psql -U postgres -d budget_management_system
```
```sql
\dx
SELECT count(*) FROM transactions;
```
