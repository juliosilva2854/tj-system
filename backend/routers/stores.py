from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone
from database import db, audit
from deps import get_current_user, require_roles
from models import StoreCreate, gen_id
from permissions import verify_tenant_access, get_user_store_scope, ADMIN_ROLES, GENERAL_MANAGER_ROLES

router = APIRouter(tags=["stores"])

@router.post("/stores")
async def create_store(data: StoreCreate, user: dict = Depends(require_roles("master", "admin"))):
    tid = user.get('tenant_id') or ''
    if user['role'] == 'master':
        body_tid = None  # master precisa passar tenant_id no body futuramente; por ora exigir vinculo
        raise HTTPException(status_code=400, detail="Master deve criar loja autenticado como admin do tenant ou usar /tenants/{id}/stores")
    if not tid:
        raise HTTPException(status_code=400, detail="Sem estabelecimento vinculado")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": gen_id(), "tenant_id": tid, "name": data.name,
        "code": data.code or "", "address": data.address or "",
        "active": True, "created_at": now, "created_by": user['sub']
    }
    await db.stores.insert_one(doc); doc.pop("_id", None)
    await audit.log(user['sub'], user['email'], "CRIAR", "store", doc['id'], tid)
    return doc

@router.post("/tenants/{tid}/stores")
async def create_store_for_tenant(tid: str, data: StoreCreate, user: dict = Depends(require_roles("master"))):
    t = await db.tenants.find_one({"id": tid}, {"_id": 0})
    if not t:
        raise HTTPException(status_code=404, detail="Tenant nao encontrado")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": gen_id(), "tenant_id": tid, "name": data.name,
        "code": data.code or "", "address": data.address or "",
        "active": True, "created_at": now, "created_by": user['sub']
    }
    await db.stores.insert_one(doc); doc.pop("_id", None)
    await audit.log(user['sub'], user['email'], "CRIAR", "store", doc['id'], tid)
    return doc

@router.get("/stores")
async def list_stores(user: dict = Depends(get_current_user)):
    q = {}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    docs = await db.stores.find(q, {"_id": 0}).to_list(1000)
    # filtrar por escopo se nao for admin/master
    if user['role'] not in ADMIN_ROLES:
        scope = await get_user_store_scope(user)
        # gerente_geral: filtra para as lojas que ele tem acesso (se tiver alguma definida)
        # se tiver store_ids definidas, filtra; caso contrario, mostra com base em warehouse_ids
        if scope:
            docs = [d for d in docs if d['id'] in scope]
        else:
            # derivar lojas a partir dos warehouse_ids do usuario
            wids = set(user.get('warehouse_ids') or [])
            if user.get('warehouse_id'):
                wids.add(user['warehouse_id'])
            if wids:
                whs = await db.warehouses.find({"id": {"$in": list(wids)}}, {"_id": 0}).to_list(1000)
                allowed = {w.get('store_id') for w in whs if w.get('store_id')}
                docs = [d for d in docs if d['id'] in allowed]
            else:
                docs = []
    return docs

@router.patch("/stores/{sid}")
async def update_store(sid: str, request: Request, user: dict = Depends(require_roles("master", "admin"))):
    body = await request.json()
    target = await db.stores.find_one({"id": sid}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Nao encontrada")
    await verify_tenant_access(user, target['tenant_id'])
    body.pop('id', None); body.pop('tenant_id', None); body.pop('created_at', None)
    await db.stores.update_one({"id": sid}, {"$set": body})
    await audit.log(user['sub'], user['email'], "EDITAR", "store", sid, target['tenant_id'])
    return {"message": "Atualizada"}

@router.delete("/stores/{sid}")
async def delete_store(sid: str, user: dict = Depends(require_roles("master", "admin"))):
    target = await db.stores.find_one({"id": sid}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Nao encontrada")
    await verify_tenant_access(user, target['tenant_id'])
    # bloquear se houver warehouses ativos
    count = await db.warehouses.count_documents({"store_id": sid, "active": True})
    if count > 0:
        raise HTTPException(status_code=400, detail=f"Existem {count} deposito(s) ativo(s) nesta loja")
    await db.stores.delete_one({"id": sid})
    await audit.log(user['sub'], user['email'], "EXCLUIR", "store", sid, target['tenant_id'])
    return {"message": "Excluida"}
