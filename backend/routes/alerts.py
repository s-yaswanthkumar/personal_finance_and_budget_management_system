from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from backend.db.mongo import get_alerts, mark_alert_read, mark_all_alerts_read, log_alert

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

class MarkReadRequest(BaseModel):
    alert_id: Optional[str] = None
    user_id: Optional[int] = 1
    mark_all: bool = False

@router.get("")
def fetch_alerts(
    user_id: int = Query(1, description="User ID"),
    unread_only: bool = Query(False, description="Filter unread alerts"),
    limit: int = Query(50, ge=1, le=100)
):
    """Retrieve alert events from MongoDB alert_logs collection."""
    try:
        alerts = get_alerts(user_id=user_id, limit=limit, unread_only=unread_only)
        unread_count = sum(1 for a in alerts if not a.get("is_read", False))
        return {
            "user_id": user_id,
            "total_count": len(alerts),
            "unread_count": unread_count,
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts from MongoDB: {str(e)}")

@router.post("/mark-read")
def mark_read_endpoint(payload: MarkReadRequest):
    """Mark a specific alert or all alerts as read in MongoDB."""
    try:
        if payload.mark_all and payload.user_id:
            mark_all_alerts_read(payload.user_id)
            return {"success": True, "message": f"All alerts marked as read for user {payload.user_id}"}
        elif payload.alert_id:
            mark_alert_read(payload.alert_id)
            return {"success": True, "message": f"Alert {payload.alert_id} marked as read"}
        else:
            raise HTTPException(status_code=400, detail="Must provide either alert_id or mark_all=True with user_id.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update alert: {str(e)}")