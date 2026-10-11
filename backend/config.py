import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / '.env'
if not env_path.exists():
    env_path = Path('.env')
load_dotenv(dotenv_path=env_path)

POSTGRES_URL = os.getenv('POSTGRES_URL')
MONGO_URI = os.getenv('MONGO_URI')

if not POSTGRES_URL or 'YOUR_PGADMIN_PASSWORD' in POSTGRES_URL:
    print("\n" + "=" * 70)
    print(" [DATABASE CONFIGURATION REQUIRED]")
    print(" PostgreSQL pgAdmin password is not configured.")
    print(" Please run: python configure_database.py")
    print("=" * 70 + "\n")
    POSTGRES_URL = 'postgresql://postgres:YOUR_PGADMIN_PASSWORD@localhost:5432/budget_management_system'

if not MONGO_URI or '<username>' in MONGO_URI:
    print("\n" + "=" * 70)
    print(" [MONGODB ATLAS CONFIGURATION REQUIRED]")
    print(" MongoDB Atlas connection string is not configured.")
    print(" Please run: python configure_database.py")
    print("=" * 70 + "\n")
    MONGO_URI = 'mongodb+srv://<username>:<password>@<cluster>.mongodb.net/budget_management_system?retryWrites=true&w=majority'
