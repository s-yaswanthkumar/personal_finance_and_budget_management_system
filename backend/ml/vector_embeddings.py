import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from pgvector.psycopg2 import register_vector
from backend.db.postgres import get_db_cursor
from backend.ml.categorizer import TRAINING_DATA

VECTOR_DIM = 64

class FinancialVectorEmbedder:
    """
    Generates 64-dimensional dense semantic embeddings for financial memos,
    merchants, categories, and natural language search queries.
    Normalized to unit L2 length for fast cosine distance (<=>) with PGVector.
    """
    def __init__(self, dim: int = VECTOR_DIM):
        self.dim = dim
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            analyzer="char_wb",
            min_df=1,
            lowercase=True
        )
        self.svd = TruncatedSVD(n_components=self.dim, random_state=42)
        self._fit()

    def _fit(self):
        # Extract training texts from financial corpus
        corpus = [item[0] for item in TRAINING_DATA]
        # Augment with common financial keywords and categories
        keywords = [
            "groceries supermarket food produce vegetables fruits store market blinkit zepto instamart bigbasket dmart reliance fresh kirana",
            "dining restaurant cafe coffee burger pizza breakfast lunch dinner bar bistro eatery swiggy zomato chai point biryani dosa thali",
            "utilities electric power water gas internet wifi broadband cellular phone bill bescom bwssb jio airtel fiber indane lpg cylinder",
            "entertainment movies games netflix spotify music gaming cinema theatre steam subscription bookmyshow pvr inox hotstar sonyliv",
            "salary payroll direct deposit paycheck earnings wage income bonus tcs infosys wipro tech mahindra",
            "transport uber taxi flight transit gas fuel shell chevron parking highway toll metro subway ola rapido namma metro irctc fastag iocl petrol",
            "medical pharmacy health clinic hospital insurance doctor prescription apollo pharmacy",
            "shopping clothes electronics amazon flipkart myntra retail shoes luxury",
            "transfer savings checking credit deposit withdrawal payment wire upi neft rtgs imps"
        ]
        all_texts = corpus + keywords
        X_tfidf = self.vectorizer.fit_transform(all_texts)
        self.svd.fit(X_tfidf)

    def embed(self, text: str) -> np.ndarray:
        """Embed any text into a 64-dimensional float32 vector on the unit sphere."""
        if not text or not text.strip():
            # Zero vector fallback
            return np.zeros(self.dim, dtype=np.float32)
        tfidf_vec = self.vectorizer.transform([text.strip()])
        dense = self.svd.transform(tfidf_vec)
        norm = np.linalg.norm(dense)
        if norm > 1e-9:
            dense = dense / norm
        return dense[0].astype(np.float32)

# Singleton embedder instance
vector_embedder = FinancialVectorEmbedder()

def generate_embedding(text: str) -> np.ndarray:
    return vector_embedder.embed(text)

def init_pgvector_schema():
    """
    Ensure the PostgreSQL vector extension is enabled and the transactions table
    has a vector(64) column indexed with HNSW for ultra-fast similarity search.
    """
    try:
        with get_db_cursor(commit=True) as (cur, conn):
            register_vector(conn)
            # 1. Enable extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            # 2. Add embedding column to transactions if missing
            cur.execute(f"""
                ALTER TABLE transactions 
                ADD COLUMN IF NOT EXISTS embedding vector({VECTOR_DIM});
            """)
            # 3. Create HNSW index for cosine distance if not exists
            try:
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_transactions_embedding_hnsw 
                    ON transactions USING hnsw (embedding vector_cosine_ops);
                """)
            except Exception as idx_err:
                print("[PGVECTOR] HNSW index notice (non-fatal):", idx_err)
        print("[PGVECTOR] Schema verified: extension 'vector' and 'transactions.embedding' initialized.")
    except Exception as e:
        print("[PGVECTOR] Error initializing schema:", e)

def backfill_transaction_embeddings(user_id: Optional[int] = None) -> int:
    """
    Generate and populate vector embeddings for transactions that currently lack one.
    """
    updated_count = 0
    with get_db_cursor(commit=True) as (cur, conn):
        register_vector(conn)
        query = "SELECT transaction_id, raw_memo FROM transactions WHERE embedding IS NULL"
        params = []
        if user_id is not None:
            query += " AND user_id = %s"
            params.append(user_id)
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        for tx_id, memo in rows:
            vec = generate_embedding(memo or "")
            cur.execute(
                "UPDATE transactions SET embedding = %s WHERE transaction_id = %s;",
                (vec, tx_id)
            )
            updated_count += 1

    return updated_count

def semantic_search_transactions(
    user_id: int,
    query_text: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Perform semantic vector similarity search over a user's transactions using PGVector (<=>).
    """
    query_vec = generate_embedding(query_text)

    with get_db_cursor() as (cur, conn):
        register_vector(conn)
        sql = """
            SELECT 
                t.transaction_id,
                t.user_id,
                t.account_id,
                a.account_name,
                t.category_id,
                c.name AS category_name,
                t.amount,
                t.transaction_type,
                t.raw_memo,
                t.transaction_date,
                (t.embedding <=> %s) AS cosine_distance,
                (1.0 - (t.embedding <=> %s)) AS cosine_similarity
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            JOIN categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s AND t.embedding IS NOT NULL
            ORDER BY t.embedding <=> %s ASC
            LIMIT %s;
        """
        cur.execute(sql, (query_vec, query_vec, user_id, query_vec, top_k))
        rows = cur.fetchall()

        results = []
        for r in rows:
            results.append({
                "transaction_id": r[0],
                "user_id": r[1],
                "account_id": r[2],
                "account_name": r[3],
                "category_id": r[4],
                "category_name": r[5],
                "amount": float(r[6]),
                "transaction_type": r[7],
                "raw_memo": r[8],
                "transaction_date": r[9].isoformat() if hasattr(r[9], 'isoformat') else str(r[9]),
                "cosine_distance": round(float(r[10]), 4),
                "cosine_similarity": round(float(r[11]), 4)
            })
        return results

def find_similar_transactions(
    transaction_id: int,
    user_id: int,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Find past transactions most semantically similar to a given transaction using PGVector.
    """
    with get_db_cursor() as (cur, conn):
        register_vector(conn)
        cur.execute("""
            SELECT embedding, raw_memo 
            FROM transactions 
            WHERE transaction_id = %s AND user_id = %s;
        """, (transaction_id, user_id))
        row = cur.fetchone()
        if not row or row[0] is None:
            return []

        target_vec = row[0]

        sql = """
            SELECT 
                t.transaction_id,
                t.user_id,
                t.account_id,
                a.account_name,
                t.category_id,
                c.name AS category_name,
                t.amount,
                t.transaction_type,
                t.raw_memo,
                t.transaction_date,
                (t.embedding <=> %s) AS cosine_distance,
                (1.0 - (t.embedding <=> %s)) AS cosine_similarity
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            JOIN categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s AND t.transaction_id != %s AND t.embedding IS NOT NULL
            ORDER BY t.embedding <=> %s ASC
            LIMIT %s;
        """
        cur.execute(sql, (target_vec, target_vec, user_id, transaction_id, target_vec, top_k))
        rows = cur.fetchall()

        results = []
        for r in rows:
            results.append({
                "transaction_id": r[0],
                "user_id": r[1],
                "account_id": r[2],
                "account_name": r[3],
                "category_id": r[4],
                "category_name": r[5],
                "amount": float(r[6]),
                "transaction_type": r[7],
                "raw_memo": r[8],
                "transaction_date": r[9].isoformat() if hasattr(r[9], 'isoformat') else str(r[9]),
                "cosine_distance": round(float(r[10]), 4),
                "cosine_similarity": round(float(r[11]), 4)
            })
        return results
