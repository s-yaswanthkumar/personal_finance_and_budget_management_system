import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import pymongo
import certifi
from bson import ObjectId
from backend.config import MONGO_URI

# Cloud MongoDB Atlas Cluster URI
ATLAS_CLUSTER_URI = "mongodb+srv://<username>:<password>@<your-cluster>.mongodb.net/budget_management_system?retryWrites=true&w=majority"

_client: Optional[pymongo.MongoClient] = None
_last_check_time: float = 0
_is_cluster_available: bool = False

def get_mongo_client() -> pymongo.MongoClient:
    """
    Connect exclusively to the Cloud MongoDB Atlas Cluster.
    Localhost fallback is strictly disabled per project requirements.
    """
    global _client
    if _client is None:
        target_uri = MONGO_URI or ATLAS_CLUSTER_URI
        if "127.0.0.1" in target_uri or "localhost" in target_uri:
            target_uri = ATLAS_CLUSTER_URI

        _client = pymongo.MongoClient(
            target_uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
    return _client

def is_atlas_cluster_reachable() -> bool:
    """Check connectivity to MongoDB Atlas cluster with cached backoff to avoid latency spikes."""
    global _last_check_time, _is_cluster_available
    now = time.time()
    if (now - _last_check_time) < 10.0:
        return _is_cluster_available
    
    try:
        client = get_mongo_client()
        client.admin.command('ping')
        _is_cluster_available = True
    except Exception as e:
        _is_cluster_available = False
    
    _last_check_time = now
    return _is_cluster_available

def get_mongo_db(db_name: str = 'budget_management_system'):
    client = get_mongo_client()
    return client[db_name]

def get_alert_logs_collection():
    db = get_mongo_db()
    return db['alert_logs']

def get_raw_payloads_collection():
    db = get_mongo_db()
    return db['raw_inbound_payloads']

def log_alert(user_id: int, alert_type: str, category: str, message: str, severity: str, metadata: dict = None) -> dict:
    """Log an alert document directly to the MongoDB Atlas cluster."""
    doc = {
        'user_id': user_id,
        'type': alert_type,
        'category': category,
        'message': message,
        'severity': severity,  # warning, breach, anomaly
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'is_read': False,
        'metadata': metadata or {}
    }
    if is_atlas_cluster_reachable():
        try:
            coll = get_alert_logs_collection()
            result = coll.insert_one(doc)
            doc['_id'] = str(result.inserted_id)
        except Exception as e:
            print(f"[MONGODB CLUSTER] Notice writing alert to Atlas: {e}")
            doc['_id'] = "temp_cluster_pending_ip"
    else:
        doc['_id'] = "temp_cluster_pending_ip"
    return doc

def log_raw_payload(user_id: int, raw_payload: dict, source: str = 'web_dashboard', parsed_status: str = 'success', error: str = None) -> dict:
    """Log raw inbound HTTP payload to MongoDB Atlas cluster."""
    doc = {
        'user_id': user_id,
        'raw_payload': raw_payload,
        'received_at': datetime.utcnow().isoformat() + 'Z',
        'source': source,
        'parsed_status': parsed_status,
        'error': error
    }
    if is_atlas_cluster_reachable():
        try:
            coll = get_raw_payloads_collection()
            result = coll.insert_one(doc)
            doc['_id'] = str(result.inserted_id)
        except Exception as e:
            print(f"[MONGODB CLUSTER] Notice writing payload to Atlas: {e}")
            doc['_id'] = "temp_cluster_pending_ip"
    else:
        doc['_id'] = "temp_cluster_pending_ip"
    return doc

def get_alerts(user_id: int, limit: int = 50, unread_only: bool = False) -> List[Dict[str, Any]]:
    """Fetch user alert documents from MongoDB Atlas cluster."""
    alerts = []
    if is_atlas_cluster_reachable():
        try:
            coll = get_alert_logs_collection()
            query = {'user_id': user_id}
            if unread_only:
                query['is_read'] = False
            cursor = coll.find(query).sort('timestamp', -1).limit(limit)
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                alerts.append(doc)
        except Exception as e:
            print(f"[MONGODB CLUSTER] Notice reading alerts from Atlas: {e}")
    return alerts

def mark_alert_read(alert_id: str) -> bool:
    """Mark an alert read in MongoDB Atlas cluster."""
    if is_atlas_cluster_reachable():
        try:
            coll = get_alert_logs_collection()
            coll.update_one({'_id': ObjectId(alert_id)}, {'$set': {'is_read': True}})
            return True
        except Exception:
            return False
    return False

def mark_all_alerts_read(user_id: int) -> bool:
    """Mark all alerts read for a user in MongoDB Atlas cluster."""
    if is_atlas_cluster_reachable():
        try:
            coll = get_alert_logs_collection()
            coll.update_many({'user_id': user_id, 'is_read': False}, {'$set': {'is_read': True}})
            return True
        except Exception:
            return False
    return False

def get_raw_payloads(user_id: Optional[int] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch raw inbound HTTP payload documents from MongoDB Atlas cluster."""
    payloads = []
    if is_atlas_cluster_reachable():
        try:
            coll = get_raw_payloads_collection()
            query = {'user_id': user_id} if user_id else {}
            cursor = coll.find(query).sort('received_at', -1).limit(limit)
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                payloads.append(doc)
        except Exception as e:
            print(f"[MONGODB CLUSTER] Notice reading payloads from Atlas: {e}")
    return payloads

def get_mongo_stats() -> Dict[str, Any]:
    """Retrieve operational statistics and health of the MongoDB Atlas cluster."""
    is_connected = is_atlas_cluster_reachable()
    alert_logs_count = 0
    raw_payloads_count = 0
    if is_connected:
        try:
            db = get_mongo_db()
            alert_logs_count = db['alert_logs'].count_documents({})
            raw_payloads_count = db['raw_inbound_payloads'].count_documents({})
        except Exception:
            pass
    return {
        "cluster_host": "cluster0.mst0hj0.mongodb.net",
        "database": "budget_management_system",
        "connected": is_connected,
        "collections": {
            "alert_logs": alert_logs_count,
            "raw_inbound_payloads": raw_payloads_count
        }
    }
