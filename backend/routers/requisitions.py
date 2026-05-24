from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from database import db, audit
from deps import get_current_user, require_roles
from models import RequisitionCreate, gen_id
from permissions import (
    verify_tenant_access, get_user_warehouse_scope,
    CAN_APPROVE_REQUISITION, ADMIN_ROLES,
)

router = APIRouter(tags=["requisitions"])

@router.post("/requisitions")
async def create_requisition(data: RequisitionCreate, user: dict = Depends(get_current_user)):
    tid = user.get('tenant_id', '')
    # warehouse de origem = warehouse_id legado ou primeiro warehouse_ids do usuario
    wid = user.get('warehouse_id') or (user.get('warehouse_ids') or [None])[0]
    if not wid:
        raise HTTPException(status_code=400, detail="Voce precisa estar vinculado a um deposito")
    wh = await db.warehouses.find_one({"id": wid, "tenant_id": tid}, {"_id": 0})
    if not wh or wh.get('type') != 'filho':
        raise HTTPException(status_code=400, detail="Requisicoes sao criadas apenas por depositos filhos")
    parent_id = wh.get('parent_id', '')
    if not parent_id:
        raise HTTPException(status_code=400, detail="Deposito filho sem pai vinculado")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": gen_id(), "tenant_id": tid, "from_warehouse_id": wid, "to_warehouse_id": parent_id,
        "store_id": wh.get('store_id', ''),
        "items": [i.model_dump() for i in data.items], "notes": data.notes or "",
        "status": "pending", "created_at": now, "created_by": user['sub']
    }
    await db.requisitions.insert_one(doc); doc.pop("_id", None)
    await audit.log(user['sub'], user['email'], "CRIAR", "requisicao", doc['id'], tid,
                    warehouse_id=wid, store_id=wh.get('store_id', ''))
    return doc

@router.get("/requisitions")
async def list_requisitions(user: dict = Depends(get_current_user)):
    q = {}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    docs = await db.requisitions.find(q, {"_id": 0}).sort('created_at', -1).to_list(1000)
    # filtrar por escopo
    if user['role'] not in ADMIN_ROLES:
        scope = await get_user_warehouse_scope(user)
        if scope is not None:
            docs = [d for d in docs if d.get('from_warehouse_id') in scope or d.get('to_warehouse_id') in scope]
    return docs

@router.post("/requisitions/{rid}/approve")
async def approve_requisition(rid: str, user: dict = Depends(require_roles(*CAN_APPROVE_REQUISITION))):
    req = await db.requisitions.find_one({"id": rid}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Requisicao nao encontrada")
    if user['role'] != 'master':
        await verify_tenant_access(user, req['tenant_id'])
        # gerente_logistica/geral so podem aprovar requisicoes do PAI no seu escopo
        if user['role'] not in ADMIN_ROLES:
            scope = await get_user_warehouse_scope(user)
            if scope is not None and req['to_warehouse_id'] not in scope:
                raise HTTPException(status_code=403, detail="Sem acesso a este deposito PAI")
    if req['status'] != 'pending':
        raise HTTPException(status_code=400, detail="Requisicao ja processada")
    now = datetime.now(timezone.utc).isoformat()
    pai_id = req['to_warehouse_id']
    filho_id = req['from_warehouse_id']
    for item in req['items']:
        pid = item['product_id']
        qty = item['quantity']
        pai_inv = await db.inventory.find_one({"product_id": pid, "warehouse_id": pai_id, "tenant_id": req['tenant_id']}, {"_id": 0})
        if not pai_inv or pai_inv['quantity'] < qty:
            available = pai_inv['quantity'] if pai_inv else 0
            raise HTTPException(status_code=400, detail=f"Estoque insuficiente no almoxarifado para {item['product_name']}. Disponivel: {available}")
        new_pai_qty = max(0, pai_inv['quantity'] - qty)
        await db.inventory.update_one({"id": pai_inv['id']}, {"$set": {"quantity": new_pai_qty, "updated_at": now}})
        filho_inv = await db.inventory.find_one({"product_id": pid, "warehouse_id": filho_id, "tenant_id": req['tenant_id']}, {"_id": 0})
        if filho_inv:
            await db.inventory.update_one({"id": filho_inv['id']}, {"$set": {"quantity": filho_inv['quantity'] + qty, "updated_at": now}})
        else:
            await db.inventory.insert_one({
                "id": gen_id(), "tenant_id": req['tenant_id'], "product_id": pid,
                "warehouse_id": filho_id, "quantity": qty, "updated_at": now
            })
    await db.requisitions.update_one({"id": rid}, {"$set": {"status": "approved", "resolved_at": now, "resolved_by": user['sub']}})
    await audit.log(user['sub'], user['email'], "APROVAR", "requisicao", rid, req['tenant_id'],
                    warehouse_id=pai_id, store_id=req.get('store_id', ''))
    return {"message": "Requisicao aprovada. Itens transferidos."}

@router.post("/requisitions/{rid}/reject")
async def reject_requisition(rid: str, user: dict = Depends(require_roles(*CAN_APPROVE_REQUISITION))):
    req = await db.requisitions.find_one({"id": rid}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Nao encontrada")
    if user['role'] != 'master':
        await verify_tenant_access(user, req['tenant_id'])
    now = datetime.now(timezone.utc).isoformat()
    await db.requisitions.update_one({"id": rid}, {"$set": {"status": "rejected", "resolved_at": now, "resolved_by": user['sub']}})
    await audit.log(user['sub'], user['email'], "REJEITAR", "requisicao", rid, req['tenant_id'])
    return {"message": "Requisicao rejeitada"}
