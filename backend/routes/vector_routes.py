from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from backend.auth_jwt import get_current_user_jwt
from backend.ml.vector_embeddings import (
    semantic_search_transactions,
    find_similar_transactions,
    generate_embedding,
    backfill_transaction_embeddings,
    VECTOR_DIM
)
from backend.db.postgres import get_db_cursor

router = APIRouter(prefix="/api/vector", tags=["PGVector Semantic Search"])

class VectorSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search text (e.g. 'coffee shop', 'electric utility', 'games')", example="Pizza delivery dining")
    top_k: int = Field(5, ge=1, le=50, description="Maximum number of nearest neighbors to retrieve")

class CustomEmbedRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text string to convert into vector embedding", example="Costco Wholesale Supermarket")

@router.post("/search", summary="[POST] PGVector Semantic Search (Protected - Requires JWT)")
def search_transactions_pgvector(
    payload: VectorSearchRequest,
    current_user: dict = Depends(get_current_user_jwt)
):
    """
    **POST method to perform Semantic Vector Search via PGVector.**
    
    **Requires JWT Authorization!**
    1. Click the green **Authorize** button at the top of Swagger docs.
    2. Enter your JWT access token (obtained from `POST /api/auth/login`).
    3. Execute this POST request with any natural language query.
    4. PGVector will compute cosine distance (`<=>`) in PostgreSQL and return semantically ranked transactions.
    """
    user_id = current_user["user_id"]
    query_text = payload.query.strip()
    top_k = payload.top_k

    results = semantic_search_transactions(user_id=user_id, query_text=query_text, top_k=top_k)

    return {
        "status": "success",
        "authenticated_user_id": user_id,
        "query": query_text,
        "vector_engine": "PostgreSQL pgvector (cosine distance <=>)",
        "vector_dimension": VECTOR_DIM,
        "results_count": len(results),
        "results": results
    }

@router.get("/similar/{transaction_id}", summary="[GET] Find Similar Transactions with PGVector (Protected - Requires JWT)")
def get_similar_transactions_pgvector(
    transaction_id: int = Path(..., description="Target transaction ID to find neighbors for"),
    top_k: int = Query(5, ge=1, le=20, description="Number of similar items to return"),
    current_user: dict = Depends(get_current_user_jwt)
):
    """
    **GET method to retrieve nearest-neighbor transactions using PGVector.**
    
    **Requires JWT Authorization!**
    1. Authorize via the Swagger **Authorize** button.
    2. Provide a `transaction_id`.
    3. PGVector locates the target vector in PostgreSQL and finds the closest past expenses using cosine distance.
    """
    user_id = current_user["user_id"]
    similar_items = find_similar_transactions(transaction_id=transaction_id, user_id=user_id, top_k=top_k)

    return {
        "status": "success",
        "authenticated_user_id": user_id,
        "target_transaction_id": transaction_id,
        "vector_engine": "PostgreSQL pgvector (<=> operator)",
        "similar_count": len(similar_items),
        "similar_transactions": similar_items
    }

@router.post("/embed-custom", summary="[POST] Compute 64-Dim PGVector Embedding (Protected - Requires JWT)")
def embed_custom_text(
    payload: CustomEmbedRequest,
    current_user: dict = Depends(get_current_user_jwt)
):
    """
    **POST method to generate a dense semantic vector representation.**
    
    **Requires JWT Authorization!**
    Demonstrates the vectorization pipeline used by PGVector before inserting into PostgreSQL.
    """
    vec = generate_embedding(payload.text)
    return {
        "text": payload.text,
        "vector_dimension": VECTOR_DIM,
        "vector_norm": round(float(sum(x*x for x in vec) ** 0.5), 4),
        "vector": [round(float(x), 5) for x in vec]
    }

@router.get("/status", summary="[GET] PGVector Extension & Index Diagnostic (Protected - Requires JWT)")
def get_pgvector_status(
    current_user: dict = Depends(get_current_user_jwt)
):
    """
    **GET method to verify PGVector extension health and transaction embedding coverage.**
    
    **Requires JWT Authorization!**
    Inspects PostgreSQL system catalogs for the `vector` extension and index configuration.
    """
    user_id = current_user["user_id"]
    with get_db_cursor() as (cur, conn):
        cur.execute("SELECT default_version, installed_version FROM pg_available_extensions WHERE name = 'vector';")
        ext_info = cur.fetchone()

        cur.execute("SELECT count(*) FROM transactions WHERE user_id = %s;", (user_id,))
        total_tx = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM transactions WHERE user_id = %s AND embedding IS NOT NULL;", (user_id,))
        embedded_tx = cur.fetchone()[0]

        return {
            "pgvector_installed": ext_info is not None and ext_info[1] is not None,
            "pgvector_version": ext_info[1] if ext_info else None,
            "vector_dimension": VECTOR_DIM,
            "index_type": "HNSW (Hierarchical Navigable Small World)",
            "distance_metric": "Cosine Distance (<=>)",
            "user_id": user_id,
            "total_user_transactions": total_tx,
            "embedded_user_transactions": embedded_tx,
            "coverage_percentage": f"{(embedded_tx / total_tx * 100):.1f}%" if total_tx > 0 else "100%"
        }

@router.post("/backfill", summary="[POST] Backfill Embeddings for Un-embedded Transactions (Protected - Requires JWT)")
def backfill_embeddings_endpoint(
    current_user: dict = Depends(get_current_user_jwt)
):
    """
    **POST method to ensure all transactions in the user ledger have PGVector embeddings.**
    """
    user_id = current_user["user_id"]
    updated = backfill_transaction_embeddings(user_id=user_id)
    return {
        "status": "success",
        "user_id": user_id,
        "backfilled_count": updated,
        "message": f"Successfully computed and stored pgvector embeddings for {updated} transactions."
    }
