from fastapi import APIRouter, Depends, HTTPException, Request
from database import db, audit
from auth import hash_password
from deps import require_roles
from permissions import CAN_MANAGE_USERS

router = APIRouter(tags=["users"])

@router.get("/users")
async def list_users(user: dict = Depends(require_roles(*CAN_MANAGE_USERS))):
    q = {}
    if user['role'] == 'admin':
        q['tenant_id'] = user.get('tenant_id')
    return await db.users.find(q, {"_id": 0, "password_hash": 0}).to_list(1000)

@router.patch("/users/{uid}")
async def update_user(uid: str, request: Request, user: dict = Depends(require_roles(*CAN_MANAGE_USERS))):
    body = await request.json()
    body.pop('id', None)
    body.pop('email', None)
    if 'password' in body:
        body['password_hash'] = hash_password(body.pop('password'))
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    if user['role'] == 'admin' and target.get('tenant_id') != user.get('tenant_id'):
        raise HTTPException(status_code=403, detail="Sem permissao")
    if user['role'] == 'admin' and body.get('role') == 'master':
        raise HTTPException(status_code=403, detail="Admin nao pode promover a master")
    await db.users.update_one({"id": uid}, {"$set": body})
    await audit.log(user['sub'], user['email'], "EDITAR", "usuario", uid, user.get('tenant_id', ''))
    return {"message": "Atualizado"}

@router.delete("/users/{uid}")
async def delete_user(uid: str, user: dict = Depends(require_roles("master"))):
    if uid == user['sub']:
        raise HTTPException(status_code=400, detail="Nao pode excluir a si mesmo")
    r = await db.users.delete_one({"id": uid})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    await audit.log(user['sub'], user['email'], "EXCLUIR", "usuario", uid)
    return {"message": "Excluido"}
