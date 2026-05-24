from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone
from database import db, audit
from deps import get_current_user, require_roles
from models import SupplierCreate, gen_id
from permissions import verify_tenant_access, CAN_MANAGE_PRODUCTS

router = APIRouter(tags=["suppliers"])

@router.post("/suppliers")
async def create_supplier(data: SupplierCreate, user: dict = Depends(require_roles(*CAN_MANAGE_PRODUCTS))):
    tid = user.get('tenant_id', '')
    now = datetime.now(timezone.utc).isoformat()
    doc = {"id": gen_id(), "tenant_id": tid, **data.model_dump(), "active": True, "created_at": now, "created_by": user['sub']}
    await db.suppliers.insert_one(doc); doc.pop("_id", None)
    await audit.log(user['sub'], user['email'], "CRIAR", "fornecedor", doc['id'], tid)
    return doc

@router.get("/suppliers")
async def list_suppliers(user: dict = Depends(get_current_user)):
    q = {}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    return await db.suppliers.find(q, {"_id": 0}).to_list(1000)

@router.patch("/suppliers/{sid}")
async def update_supplier(sid: str, request: Request, user: dict = Depends(require_roles(*CAN_MANAGE_PRODUCTS))):
    body = await request.json()
    target = await db.suppliers.find_one({"id": sid}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    if user['role'] != 'master':
        await verify_tenant_access(user, target['tenant_id'])
    body.pop('id', None); body.pop('tenant_id', None)
    await db.suppliers.update_one({"id": sid}, {"$set": body})
    await audit.log(user['sub'], user['email'], "EDITAR", "fornecedor", sid, target['tenant_id'])
    return {"message": "Atualizado"}

@router.delete("/suppliers/{sid}")
async def delete_supplier(sid: str, user: dict = Depends(require_roles(*CAN_MANAGE_PRODUCTS))):
    target = await db.suppliers.find_one({"id": sid}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    if user['role'] != 'master':
        await verify_tenant_access(user, target['tenant_id'])
    await db.suppliers.delete_one({"id": sid})
    await audit.log(user['sub'], user['email'], "EXCLUIR", "fornecedor", sid, target['tenant_id'])
    return {"message": "Excluido"}
