from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class AuditLogger:
    def __init__(self, db):
        self.db = db

    async def log(self, user_id: str, user_email: str, action: str, entity_type: str, entity_id: str, tenant_id: str = "", changes: dict = None):
        try:
            await self.db.audit_logs.insert_one({
                "user_id": user_id, "user_email": user_email,
                "action": action, "entity_type": entity_type, "entity_id": entity_id,
                "tenant_id": tenant_id, "changes": changes,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Audit log failed: {e}")
