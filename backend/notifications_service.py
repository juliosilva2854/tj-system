"""Motor de notificacoes configuravel por usuario.

Cada usuario tem `notification_prefs` no seu documento:
{
  "stock_low":            {"in_app": true, "email": false},
  "requisition_created":  {"in_app": true, "email": false},
  "requisition_resolved": {"in_app": true, "email": false},
  "transfer_received":    {"in_app": true, "email": false},
  "invoice_pending":      {"in_app": true, "email": false}
}

Se um usuario nao tiver preferencia definida, usamos os defaults abaixo.
Cada evento respeita a preferencia individual (in_app e/ou email).
"""
import asyncio
import logging
from datetime import datetime, timezone

from database import db
from models import gen_id

logger = logging.getLogger(__name__)

# Metadados dos eventos: label (PT-BR), tipo visual e default por canal.
EVENT_TYPES = {
    "stock_low": {
        "label": "Estoque baixo",
        "description": "Quando um produto atinge ou fica abaixo do estoque minimo",
        "type": "warning",
        "default": {"in_app": True, "email": False},
    },
    "requisition_created": {
        "label": "Nova requisicao",
        "description": "Quando um deposito FILHO cria uma requisicao para aprovacao",
        "type": "info",
        "default": {"in_app": True, "email": False},
    },
    "requisition_resolved": {
        "label": "Requisicao aprovada/rejeitada",
        "description": "Quando a sua requisicao e aprovada ou rejeitada",
        "type": "success",
        "default": {"in_app": True, "email": False},
    },
    "transfer_received": {
        "label": "Transferencia recebida",
        "description": "Quando a sua loja recebe uma transferencia de outra loja",
        "type": "info",
        "default": {"in_app": True, "email": False},
    },
    "invoice_pending": {
        "label": "Nota fiscal pendente",
        "description": "Quando uma nova nota fiscal e registrada e fica pendente",
        "type": "info",
        "default": {"in_app": True, "email": False},
    },
}


def default_prefs() -> dict:
    return {k: dict(v["default"]) for k, v in EVENT_TYPES.items()}


def merge_prefs(user_prefs) -> dict:
    """Combina os defaults com as preferencias salvas do usuario."""
    merged = default_prefs()
    if isinstance(user_prefs, dict):
        for event, channels in user_prefs.items():
            if event in merged and isinstance(channels, dict):
                for ch in ("in_app", "email"):
                    if ch in channels:
                        merged[event][ch] = bool(channels[ch])
    return merged


def _simple_email_html(title: str, message: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #E4E4E7; border-radius: 12px; overflow: hidden;">
      <div style="background: #2563EB; color: white; padding: 20px 24px;">
        <h1 style="margin: 0; font-size: 18px;">Gestao TJ</h1>
      </div>
      <div style="padding: 24px;">
        <p style="font-weight: 600; font-size: 16px; color: #18181B; margin: 0 0 8px;">{title}</p>
        <p style="color: #52525B; font-size: 14px; margin: 0;">{message}</p>
      </div>
      <div style="background: #FAFAFA; padding: 16px 24px; border-top: 1px solid #E4E4E7; text-align: center;">
        <p style="color: #A1A1AA; font-size: 12px; margin: 0;">Sistema Gestao TJ - Notificacao Automatica</p>
      </div>
    </div>
    """


async def _create_one(user_doc: dict, event: str, title: str, message: str,
                      ntype: str, meta: dict | None):
    prefs = merge_prefs(user_doc.get("notification_prefs"))
    channels = prefs.get(event, EVENT_TYPES.get(event, {}).get("default", {"in_app": True, "email": False}))
    now = datetime.now(timezone.utc).isoformat()

    if channels.get("in_app", True):
        await db.notifications.insert_one({
            "id": gen_id(),
            "user_id": user_doc["id"],
            "tenant_id": user_doc.get("tenant_id", ""),
            "event": event,
            "type": ntype,
            "title": title,
            "message": message,
            "meta": meta or {},
            "read": False,
            "created_at": now,
        })

    if channels.get("email") and user_doc.get("email"):
        from email_service import send_email
        try:
            await asyncio.to_thread(send_email, user_doc["email"], f"[Gestao TJ] {title}", _simple_email_html(title, message))
        except Exception as e:  # nunca quebra o fluxo principal
            logger.error(f"Falha ao enviar email de notificacao para {user_doc.get('email')}: {e}")


async def notify_users(user_ids, event: str, title: str, message: str,
                       ntype: str = "info", meta: dict | None = None,
                       exclude_user_id: str | None = None):
    """Cria notificacoes para uma lista de user_ids, respeitando as preferencias de cada um."""
    try:
        ids = {uid for uid in user_ids if uid and uid != exclude_user_id}
        if not ids:
            return
        users = await db.users.find({"id": {"$in": list(ids)}, "active": True}, {"_id": 0}).to_list(1000)
        for u in users:
            await _create_one(u, event, title, message, ntype, meta)
    except Exception as e:  # notificacao nunca deve derrubar a operacao principal
        logger.error(f"Falha ao notificar (event={event}): {e}")


# === Helpers para descobrir destinatarios ===

async def tenant_user_ids(tenant_id: str, roles=None) -> list:
    q = {"tenant_id": tenant_id, "active": True}
    if roles:
        q["role"] = {"$in": list(roles)}
    return [u["id"] async for u in db.users.find(q, {"_id": 0, "id": 1})]


async def warehouse_watcher_ids(tenant_id: str, warehouse: dict) -> list:
    """Usuarios que 'observam' um deposito: admins do tenant + quem tem o deposito
    (ou a loja do deposito) no seu escopo."""
    ids = set(await tenant_user_ids(tenant_id, roles={"admin"}))
    wid = warehouse.get("id")
    store_id = warehouse.get("store_id")
    parent_id = warehouse.get("parent_id")
    or_clauses = [
        {"warehouse_id": wid},
        {"warehouse_ids": wid},
    ]
    if parent_id:
        or_clauses += [{"warehouse_id": parent_id}, {"warehouse_ids": parent_id}]
    if store_id:
        or_clauses.append({"store_ids": store_id})
    async for u in db.users.find({"tenant_id": tenant_id, "active": True, "$or": or_clauses}, {"_id": 0, "id": 1}):
        ids.add(u["id"])
    return list(ids)


async def check_low_stock(tenant_id: str, warehouse_id: str, product_id: str):
    """Verifica se o produto no deposito ficou abaixo do minimo e notifica os observadores."""
    try:
        prod = await db.products.find_one({"id": product_id, "tenant_id": tenant_id}, {"_id": 0})
        if not prod or (prod.get("min_stock") or 0) <= 0:
            return
        inv = await db.inventory.find_one(
            {"product_id": product_id, "warehouse_id": warehouse_id, "tenant_id": tenant_id}, {"_id": 0})
        qty = inv["quantity"] if inv else 0
        if qty > prod["min_stock"]:
            return
        wh = await db.warehouses.find_one({"id": warehouse_id}, {"_id": 0})
        if not wh:
            return
        recipients = await warehouse_watcher_ids(tenant_id, wh)
        await notify_users(
            recipients, "stock_low",
            f"Estoque baixo: {prod['name']}",
            f"{prod['name']} em {wh['name']} esta em {qty} (minimo {prod['min_stock']}).",
            ntype="warning",
            meta={"product_id": product_id, "warehouse_id": warehouse_id, "quantity": qty, "min_stock": prod["min_stock"]},
        )
    except Exception as e:
        logger.error(f"check_low_stock falhou: {e}")
