from datetime import datetime, timezone
import uuid

class AuditLogger:
    def __init__(self, db):
        self.db = db

    async def log(self, user_id: str, user_email: str, action: str,
                  entity_type: str, entity_id: str, tenant_id: str = "",
                  changes: dict = None, warehouse_id: str = "", store_id: str = ""):
        # Skip se tenant vazio E acao de tenant master (manter compat)
        if not tenant_id and entity_type not in ("tenant", "usuario", "store", "deposito"):
            return
        doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id, "user_email": user_email,
            "action": action, "entity_type": entity_type, "entity_id": entity_id,
            "tenant_id": tenant_id or "",
            "warehouse_id": warehouse_id or "",
            "store_id": store_id or "",
            "changes": changes or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.db.audit_logs.insert_one(doc)
