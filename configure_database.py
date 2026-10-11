#!/usr/bin/env python3
"""
=============================================================================
 Interactive Database Configuration Utility (PostgreSQL & MongoDB Atlas)
 Predictive Budget Management System
=============================================================================
 Prompts the user for:
   1. PostgreSQL / pgAdmin Master Password & Database Name
   2. MongoDB Atlas Cloud Cluster Connection String & Target Database

 Validates connections live and automatically updates .env and .env.docker.
=============================================================================
"""

import os
import sys
import getpass
from pathlib import Path

# Optional database driver imports with graceful warnings
try:
    import psycopg2
except ImportError:
    psycopg2 = None

try:
    import pymongo
    import certifi
except ImportError:
    pymongo = None
    certifi = None


def print_banner():
    print("=" * 72)
    print(" 🛠️  AI PREDICTIVE BUDGET MANAGEMENT SYSTEM - DATABASE CONFIGURATION")
    print("=" * 72)
    print(" This wizard configures both databases required by the polyglot stack:")
    print("   [1] PostgreSQL (Relational Core): ACID Ledger, Triggers & PGVector")
    print("   [2] MongoDB Atlas (Document Store): Audit Logs & Alert Event Streams")
    print("=" * 72)
    print()


def configure_postgresql():
    print("----------------------------------------------------------------------")
    print(" 🐘 1. PostgreSQL & pgAdmin Configuration")
    print("----------------------------------------------------------------------")
    print(" Requirements:")
    print("  - A running PostgreSQL instance (Local Port 5432 or custom)")
    print("  - A database created in pgAdmin (e.g. 'budget_management_system')")
    print("  - The 'vector' extension enabled: CREATE EXTENSION IF NOT EXISTS vector;")
    print()

    # 1. Host
    default_host = "localhost"
    try:
        host_input = input(f"Enter PostgreSQL Host [Press Enter for '{default_host}']:\n> ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nConfiguration cancelled.")
        sys.exit(1)
    pg_host = host_input if host_input else default_host

    # 2. Port
    default_port = 5432
    while True:
        try:
            port_input = input(f"Enter PostgreSQL Port [Press Enter for '{default_port}']:\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nConfiguration cancelled.")
            sys.exit(1)
        if not port_input:
            pg_port = default_port
            break
        try:
            pg_port = int(port_input)
            break
        except ValueError:
            print("[ERROR] Port must be a valid integer.")

    # 3. User
    default_user = "postgres"
    try:
        user_input = input(f"Enter PostgreSQL User [Press Enter for '{default_user}']:\n> ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nConfiguration cancelled.")
        sys.exit(1)
    pg_user = user_input if user_input else default_user

    # 4. Database Name
    default_db = "budget_management_system"
    try:
        db_input = input(f"Enter PostgreSQL Database Name [Press Enter for '{default_db}']:\n> ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nConfiguration cancelled.")
        sys.exit(1)
    pg_db = db_input if db_input else default_db

    # 5. Password (Prompt securely or plain input)
    while True:
        try:
            # Use input or getpass
            pg_pass = input("Enter your PostgreSQL / pgAdmin Password:\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nConfiguration cancelled.")
            sys.exit(1)

        if not pg_pass:
            print("[ERROR] Password cannot be empty. Please enter your pgAdmin master password.\n")
            continue
        break

    # Construct Connection URL
    # Format: postgresql://<user>:<password>@<host>:<port>/<db>
    from urllib.parse import quote_plus
    encoded_pass = quote_plus(pg_pass)
    pg_url = f"postgresql://{pg_user}:{encoded_pass}@{pg_host}:{pg_port}/{pg_db}"

    # Test PostgreSQL Connection
    print("\nVerifying connection to PostgreSQL database...")
    if psycopg2:
        try:
            conn = psycopg2.connect(
                dbname=pg_db,
                user=pg_user,
                password=pg_pass,
                host=pg_host,
                port=pg_port,
                connect_timeout=5
            )
            cur = conn.cursor()
            cur.execute("SELECT version();")
            pg_ver = cur.fetchone()[0]
            # Check PGVector extension
            cur.execute("SELECT installed_version FROM pg_available_extensions WHERE name = 'vector';")
            vec_row = cur.fetchone()
            vec_ver = vec_row[0] if vec_row and vec_row[0] else "Not installed (will auto-create if privileged)"
            conn.close()
            print("  ✅ [OK] Connected to PostgreSQL service successfully!")
            print(f"         PostgreSQL Version: {pg_ver.split(',')[0]}")
            print(f"         PGVector Extension: {vec_ver}")
        except Exception as e:
            print(f"  ⚠️  [NOTICE] Could not connect directly to PostgreSQL: {e}")
            print("     Make sure your PostgreSQL service is running and the database exists in pgAdmin.")
            try:
                confirm = input("     Do you still want to save these PostgreSQL credentials? [Y/n]: ").strip().lower()
                if confirm == "n":
                    return None, None
            except (KeyboardInterrupt, EOFError):
                return None, None
    else:
        print("  ℹ️  'psycopg2' not installed in current environment; skipping live ping test.")

    print()
    return pg_url, {
        "POSTGRES_USER": pg_user,
        "POSTGRES_PASSWORD": pg_pass,
        "POSTGRES_DB": pg_db,
        "POSTGRES_HOST": pg_host,
        "POSTGRES_PORT": str(pg_port)
    }


def configure_mongodb():
    print("----------------------------------------------------------------------")
    print(" 🍃 2. MongoDB Atlas Cloud Cluster Configuration")
    print("----------------------------------------------------------------------")
    print(" Requirements:")
    print("  - Connection string from https://cloud.mongodb.com")
    print("  - Cluster Network Access: Current IP or 0.0.0.0/0 (Allow from Anywhere)")
    print()

    while True:
        try:
            uri_input = input("Enter your MongoDB Atlas Connection String:\n(Format: mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?...)\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nConfiguration cancelled.")
            sys.exit(1)

        if not uri_input:
            print("[ERROR] Connection string cannot be empty.\n")
            continue

        if not (uri_input.startswith("mongodb://") or uri_input.startswith("mongodb+srv://")):
            print("[ERROR] URI must start with 'mongodb://' or 'mongodb+srv://'.\n")
            continue

        break

    default_db = "budget_management_system"
    try:
        db_input = input(f"\nEnter the target MongoDB database name [Press Enter for '{default_db}']:\n> ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nConfiguration cancelled.")
        sys.exit(1)
    db_name = db_input if db_input else default_db

    # Format full URI with database
    clean_uri = uri_input
    if "?" in clean_uri:
        base_part, query_part = clean_uri.split("?", 1)
        base_part = base_part.rstrip("/")
        last_slash_idx = base_part.rfind("/")
        host_segment = base_part[last_slash_idx + 1:] if last_slash_idx != -1 else ""
        if "@" in host_segment or ":" in host_segment or not host_segment:
            clean_uri = f"{base_part}/{db_name}?{query_part}"
        else:
            prefix = base_part[:last_slash_idx]
            clean_uri = f"{prefix}/{db_name}?{query_part}"
    else:
        clean_uri = clean_uri.rstrip("/")
        last_slash_idx = clean_uri.rfind("/")
        host_segment = clean_uri[last_slash_idx + 1:] if last_slash_idx != -1 else ""
        if "@" in host_segment or ":" in host_segment or not host_segment:
            clean_uri = f"{clean_uri}/{db_name}?retryWrites=true&w=majority"

    # Test MongoDB Connectivity
    print("\nVerifying connection to MongoDB Atlas Cloud Cluster...")
    if pymongo:
        try:
            ca = certifi.where() if certifi else None
            client = pymongo.MongoClient(
                clean_uri,
                tlsCAFile=ca,
                serverSelectionTimeoutMS=7000,
                connectTimeoutMS=7000
            )
            client.admin.command("ping")
            print("  ✅ [OK] Connected to MongoDB Atlas Cloud Cluster successfully!")
        except Exception as e:
            print(f"  ⚠️  [NOTICE] Could not ping MongoDB Atlas cluster: {e}")
            print("     Common causes: IP Whitelist (Network Access) or incorrect user/password.")
            try:
                confirm = input("     Do you still want to save this MongoDB URI? [Y/n]: ").strip().lower()
                if confirm == "n":
                    return None
            except (KeyboardInterrupt, EOFError):
                return None
    else:
        print("  ℹ️  'pymongo' not installed in current environment; skipping live ping test.")

    print()
    return clean_uri


def save_configuration(pg_url, pg_details, mongo_uri):
    root_dir = Path(__file__).resolve().parent
    env_file = root_dir / ".env"
    env_docker_file = root_dir / ".env.docker"

    # 1. Update .env (Native Execution)
    if pg_url or mongo_uri:
        env_lines = []
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                env_lines = f.readlines()

        updated_pg = False
        updated_mongo = False
        new_lines = []

        for line in env_lines:
            stripped = line.strip()
            if stripped.startswith("POSTGRES_URL=") and pg_url:
                new_lines.append(f"POSTGRES_URL={pg_url}\n")
                updated_pg = True
            elif stripped.startswith("MONGO_URI=") and mongo_uri:
                new_lines.append(f"MONGO_URI={mongo_uri}\n")
                updated_mongo = True
            else:
                new_lines.append(line)

        if pg_url and not updated_pg:
            new_lines.insert(0, f"POSTGRES_URL={pg_url}\n")
        if mongo_uri and not updated_mongo:
            new_lines.append(f"MONGO_URI={mongo_uri}\n")

        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    # 2. Update .env.docker (Docker Compose Execution)
    if env_docker_file.exists() and (pg_details or mongo_uri):
        docker_lines = []
        with open(env_docker_file, "r", encoding="utf-8") as f:
            docker_lines = f.readlines()

        new_doc_lines = []
        keys_set = set()

        for line in docker_lines:
            stripped = line.strip()
            if stripped.startswith("POSTGRES_PASSWORD=") and pg_details:
                new_doc_lines.append(f"POSTGRES_PASSWORD={pg_details['POSTGRES_PASSWORD']}\n")
                keys_set.add("POSTGRES_PASSWORD")
            elif stripped.startswith("POSTGRES_USER=") and pg_details:
                new_doc_lines.append(f"POSTGRES_USER={pg_details['POSTGRES_USER']}\n")
                keys_set.add("POSTGRES_USER")
            elif stripped.startswith("POSTGRES_DB=") and pg_details:
                new_doc_lines.append(f"POSTGRES_DB={pg_details['POSTGRES_DB']}\n")
                keys_set.add("POSTGRES_DB")
            elif stripped.startswith("MONGO_URI=") and mongo_uri:
                new_doc_lines.append(f"MONGO_URI={mongo_uri}\n")
                keys_set.add("MONGO_URI")
            else:
                new_doc_lines.append(line)

        with open(env_docker_file, "w", encoding="utf-8") as f:
            f.writelines(new_doc_lines)

    print("=" * 72)
    print(" 🎉 CONFIGURATION SAVED SUCCESSFULLY!")
    print("=" * 72)
    print(f" Updated Environment Files:")
    print(f"   - {env_file}")
    if env_docker_file.exists():
        print(f"   - {env_docker_file}")
    print()
    print(" You can now start the complete application using:")
    print("   • Native Windows Launcher:  start_system.bat")
    print("   • Docker Desktop Launcher:  start_docker.bat  (or: docker compose up -d)")
    print("=" * 72)


def main():
    print_banner()
    pg_url, pg_details = configure_postgresql()
    mongo_uri = configure_mongodb()

    if pg_url or mongo_uri:
        save_configuration(pg_url, pg_details, mongo_uri)
    else:
        print("[NOTICE] No changes were saved.")


if __name__ == "__main__":
    main()
