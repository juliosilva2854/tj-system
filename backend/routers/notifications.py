from fastapi import APIRouter, Depends
from database import db
from deps import get_current_user

router = APIRouter(tags=["notifications"])

@router.get("/notifications")
async def list_notifications(user: dict = Depends(get_current_user)):
    q = {"user_id": user['sub']}
    return await db.notifications.find(q, {"_id": 0}).sort('created_at', -1).to_list(100)

@router.get("/notifications/unread-count")
async def unread_count(user: dict = Depends(get_current_user)):
    c = await db.notifications.count_documents({"user_id": user['sub'], "read": False})
    return {"count": c}

@router.patch("/notifications/{nid}/read")
async def mark_read(nid: str, user: dict = Depends(get_current_user)):
    await db.notifications.update_one({"id": nid, "user_id": user['sub']}, {"$set": {"read": True}})
    return {"message": "Lida"}

@router.post("/notifications/read-all")
async def read_all(user: dict = Depends(get_current_user)):
    await db.notifications.update_many({"user_id": user['sub'], "read": False}, {"$set": {"read": True}})
    return {"message": "Todas lidas"}
