# 💰 AI-Powered Personal Finance & Predictive Budget Management System

A high-performance, polyglot personal finance and predictive budget management platform combining **PostgreSQL** relational integrity (ACID ledger, active triggers, aggregated views), **PGVector** dense semantic embeddings (64-dimensional nearest-neighbor search), **MongoDB Atlas Cloud** event streaming, and **Scikit-Learn** predictive machine learning models, delivered with a responsive **Spendee-style React 19** interface.

---

## 🏛️ System Architecture

```
                          Client Tier (React 19 + Tailwind CSS)
                     [ Spendee-grade Dashboard | Port 5173 / 8080 ]
                                         │
                                         ▼ (HTTP / JWT Bearer)
                        FastAPI Gateway (Uvicorn | Port 8000)
                     [ Auth | REST Endpoints | ML Pipelines ]
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
       Relational Core & Vector Store               Document Event Store
    PostgreSQL 16/18 + PGVector (Port 5432/5433)      MongoDB Atlas Cloud Cluster
  - ACID Ledgers & Multi-Account Balances           - Real-Time Alert Logs
  - Active PL/pgSQL Hard-Cap Triggers               - Audit Trail & Breach Snapshots
  - Aggregated View: vw_monthly_summary             - Flexible Schema Event Streams
  - 64-dim HNSW Cosine Vector Index (<=>)
```

---

## 🛠️ Technology Stack

| Layer | Technologies & Frameworks | Description |
| :--- | :--- | :--- |
| **Frontend Web App** | React 19, Vite, Tailwind CSS, Lucide Icons, Recharts | Modern Single-Page Application styled like Spendee with responsive charts and financial analytics. |
| **Backend API Gateway** | FastAPI, Uvicorn, Python 3.11, Pydantic v2 | High-throughput asynchronous ASGI REST API with interactive Swagger UI and JWT authentication. |
| **Relational Database** | PostgreSQL (v16 / v18), Psycopg2 Connection Pool | ACID transaction ledger, PL/pgSQL triggers (`BEFORE INSERT`), composite B-tree indexes, views. |
| **Vector Database** | PGVector Extension (v0.8.x) | 64-dimensional semantic transaction embeddings using HNSW indexing and Cosine Distance (`<=>`). |
| **Document Database** | MongoDB Atlas Cloud Cluster, PyMongo | Cloud-hosted document database for unstructured budget alerts, forensic logs, and event streams. |
| **Machine Learning** | Scikit-Learn, NumPy | • **NLP Categorizer**: TF-IDF + Multinomial Naive Bayes (98% accuracy)<br>• **Anomaly Detection**: Unsupervised Isolation Forest ($>3\sigma$ flag)<br>• **Spending Forecaster**: Two-Stage Hurdle / Historical Cadence Model |
| **Containerization** | Docker, Docker Compose, Multi-stage Dockerfiles, Nginx Alpine | Complete microservice containerization with health checks, persistent volumes, and bridge network. |

---

## ⚙️ Prerequisites & Database Configuration

Before running the application, make sure you configure your databases as outlined below.

### 1. PostgreSQL & PGAdmin Setup
1. **Create the Database in PGAdmin**:
   - Open **pgAdmin** (or `psql` command line).
   - Create a new database named:
     ```sql
     CREATE DATABASE budget_management_system;
     ```
     *(or `predictive_budget_management_system` depending on your environment settings)*.
2. **Install the PGVector Extension**:
   - In pgAdmin Query Tool, execute:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```
   - Verify installation:
     ```sql
     SELECT installed_version FROM pg_available_extensions WHERE name = 'vector';
     ```
3. **Automatic Schema & Data Initialization**:
   - You **do not** need to manually create tables!
   - On the first run, the system automatically builds the tables, indexes, views, and PL/pgSQL triggers (`check_budget_limits()`), and seeds baseline accounts and 60 days of realistic INR spending transactions.
   - Alternatively, you can prime the database manually anytime by running:
     ```bash
     python -m backend.scripts.setup_db
     python -m backend.scripts.seed_data
     ```

---

### 2. Database Credentials Configuration (PostgreSQL & MongoDB Atlas)

#### Option A: Interactive Setup via Python (Recommended)
Run the built-in configuration utility to set up both PostgreSQL and MongoDB Atlas in one step:
```bash
python configure_database.py
```
This utility will:
1. Prompt you to enter your **PostgreSQL / pgAdmin Master Password** (and database name, default: `budget_management_system`).
2. Prompt you to enter your **MongoDB Atlas Connection String**:
   ```
   mongodb+srv://<username>:<password>@<your-cluster>.mongodb.net/?retryWrites=true&w=majority
   ```
3. Prompt you for the MongoDB database name (defaults to `budget_management_system`).
4. Automatically verify live connectivity to both databases.
5. Save your credentials to `.env` (native execution) and `.env.docker` (containerized execution).

> [!TIP]
> If you run `start_system.bat` or `start_docker.bat` for the first time, the script automatically detects unconfigured passwords and launches `configure_database.py` for you!

#### Option B: Manual Setup via `.env`
Edit the `.env` file in the project root:
```env
POSTGRES_URL=postgresql://postgres:YOUR_PGADMIN_PASSWORD@localhost:5432/budget_management_system
MONGO_URI=mongodb+srv://<username>:<password>@<your-cluster>.mongodb.net/budget_management_system?retryWrites=true&w=majority
```

> [!IMPORTANT]
> **MongoDB Atlas Network Access (IP Whitelist)**:
> In your MongoDB Atlas Dashboard, navigate to **Network Access** $\rightarrow$ **IP Access List** and ensure your current IP address (or `0.0.0.0/0` for development access) is whitelisted, otherwise connection attempts will time out.

---

## 🐳 How to Run via Docker (Recommended)

The entire application stack (Frontend, Backend, PostgreSQL with PGVector, and Nginx reverse proxy) is containerized with Docker Compose.

### Option 1: One-Click Windows Batch Launcher
- **Start**: Double-click [`start_docker.bat`](file:///c:/Users/sukha/OneDrive/Desktop/predictive%20budget%20management%20system/start_docker.bat)
- **Stop**: Double-click [`stop_docker.bat`](file:///c:/Users/sukha/OneDrive/Desktop/predictive%20budget%20management%20system/stop_docker.bat)

### Option 2: Command Line
```bash
# 1. Build and start all containers in background mode
docker compose up --build -d

# 2. Check container status and health
docker compose ps

# 3. View live backend logs
docker compose logs -f backend

# 4. Stop containers (preserves database volume)
docker compose down

# 5. Stop and wipe database volume (clean reset)
docker compose down -v
```

### Docker Service Endpoints:
- **React Frontend (Spendee UI)**: `http://localhost:5173` & `http://localhost:8080`
- **FastAPI Backend Root**: `http://localhost:8000`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **Diagnostics API**: `http://localhost:8000/api/health`
- **PostgreSQL (Host Access)**: `localhost:5433` *(mapped to avoid port 5432 collisions on Windows)*

---

## 💻 How to Run Locally (Native Mode without Docker)

If you prefer to run services natively on Windows:

### Option 1: One-Click Windows Batch Launcher
```cmd
start_system.bat
```
To stop the services:
```cmd
stop_system.bat
```

### Option 2: Manual Terminal Commands
1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Install & Build Frontend**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```
3. **Start FastAPI Backend**:
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```
4. **Start React Frontend**:
   ```bash
   cd frontend
   npm run dev -- --host 127.0.0.1 --port 5173
   ```

---

## 🔑 Demo Login Credentials

The database comes pre-seeded with two demo accounts:

| User | Username | Password | Role / Details |
| :--- | :--- | :--- | :--- |
| **Primary User** | `yaswanth` | `password123` | Sukhavasi Yaswanth (User ID: 1, 3 accounts, 60 days of INR transactions) |
| **Demo User** | `demouser` | `demo123` | Demo User (User ID: 2, 3 accounts, isolated test data) |

---

## 🔐 Swagger UI & JWT Verification

1. Open Swagger UI at `http://localhost:8000/docs`.
2. Expand `POST /api/auth/login`, enter username `yaswanth` and password `password123`, and click **Execute**.
3. Copy the returned `access_token`.
4. Click the green **Authorize 🔓** button at the top-right of the Swagger page.
5. Paste the token into the value box and click **Authorize**.
6. You can now execute protected endpoints:
   - `GET /api/auth/me`: Inspect user profile and JWT claims.
   - `POST /api/vector/search`: Run semantic vector queries using PGVector cosine distance (`<=>`).
   - `GET /api/vector/similar/{id}`: Find nearest neighbor transactions.
   - `GET /api/vector/status`: Inspect PGVector extension health and HNSW index metrics.

---

## 🧪 Verification & Integration Tests

The project includes an automated end-to-end test suite (`verify_system.py`) covering all 17 system verification benchmarks:
- Database diagnostics & PGVector status
- NLP Merchant Categorization accuracy
- ACID atomic transfers and explicit rollbacks
- Active PL/pgSQL budget hard cap triggers and breach aborts
- Isolation Forest anomaly detection
- CSV batch upload with transactional rollback
- Multi-user data isolation guarantees
- PGVector semantic search similarity

To run the verification test suite:
```bash
python verify_system.py
```
*(Or inside Docker)*:
```bash
docker exec budget-backend python verify_system.py
```

---

## 📄 License & Attribution
Developed as part of the **AI-Powered Personal Finance & Predictive Budget Management System** project review for KL University.
