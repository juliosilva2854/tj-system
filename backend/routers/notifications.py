from fastapi import APIRouter, Depends
from database import db
from deps import get_current_user
from notifications_service import EVENT_TYPES, merge_prefs, default_prefs

router = APIRouter(tags=["notifications"])

@router.get("/notifications")
async def list_notifications(user: dict = Depends(get_current_user)):
    q = {"user_id": user['sub']}
    return await db.notifications.find(q, {"_id": 0}).sort('created_at', -1).to_list(100)

@router.get("/notifications/unread-count")
async def unread_count(user: dict = Depends(get_current_user)):
    c = await db.notifications.count_documents({"user_id": user['sub'], "read": False})
    return {"count": c}

@router.get("/notifications/preferences")
async def get_preferences(user: dict = Depends(get_current_user)):
    """Retorna os metadados dos eventos + as preferencias atuais do usuario (com defaults aplicados)."""
    doc = await db.users.find_one({"id": user['sub']}, {"_id": 0, "notification_prefs": 1})
    prefs = merge_prefs((doc or {}).get('notification_prefs'))
    events = [
        {"key": k, "label": v["label"], "description": v["description"]}
        for k, v in EVENT_TYPES.items()
    ]
    return {"events": events, "preferences": prefs}

@router.put("/notifications/preferences")
async def update_preferences(data: dict, user: dict = Depends(get_current_user)):
    """Salva as preferencias do usuario. Aceita {preferences: {event: {in_app, email}}}."""
    incoming = data.get('preferences', data) or {}
    # Valida e normaliza contra os eventos conhecidos
    clean = default_prefs()
    for event, channels in incoming.items():
        if event in clean and isinstance(channels, dict):
            for ch in ("in_app", "email"):
                if ch in channels:
                    clean[event][ch] = bool(channels[ch])
    await db.users.update_one({"id": user['sub']}, {"$set": {"notification_prefs": clean}})
    return {"message": "Preferencias atualizadas", "preferences": clean}

@router.patch("/notifications/{nid}/read")
async def mark_read(nid: str, user: dict = Depends(get_current_user)):
    await db.notifications.update_one({"id": nid, "user_id": user['sub']}, {"$set": {"read": True}})
    return {"message": "Lida"}

@router.post("/notifications/read-all")
async def read_all(user: dict = Depends(get_current_user)):
    await db.notifications.update_many({"user_id": user['sub'], "read": False}, {"$set": {"read": True}})
    return {"message": "Todas lidas"}
