from fastapi import APIRouter
from pydantic import BaseModel, Field
from backend.ml.categorizer import predict_category
from backend.db.postgres import get_db_cursor

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])

class PredictCategoryRequest(BaseModel):
    memo: str = Field(..., description="Raw transaction memo string")

@router.post("/predict-category")
def predict_category_endpoint(payload: PredictCategoryRequest):
    """
    Real-time inference endpoint for memo input.
    Predicts category and retrieves category_id from PostgreSQL.
    """
    result = predict_category(payload.memo)
    category_name = result["category"]

    category_id = None
    try:
        with get_db_cursor() as (cur, conn):
            cur.execute("SELECT category_id FROM categories WHERE LOWER(name) = LOWER(%s);", (category_name,))
            row = cur.fetchone()
            if row:
                category_id = row[0]
    except Exception:
        pass

    return {
        "memo": payload.memo,
        "predicted_category": category_name,
        "category_id": category_id,
        "confidence": result.get("confidence", 0.9),
        "model": result.get("model", "nlp_pipeline")
    }