from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from datetime import datetime, timezone
from database import db, audit
from deps import get_current_user, require_roles
from models import StoreCreate, gen_id
from permissions import verify_tenant_access, get_user_store_scope, ADMIN_ROLES, GENERAL_MANAGER_ROLES

router = APIRouter(tags=["stores"])


def _can_manage_stores(user: dict) -> bool:
    """Master (role ou is_master_access) ou admin podem gerir lojas."""
    role = str(user.get('role', '')).lower().strip()
    return role in ('master', 'admin') or bool(user.get('is_master_access', False))


def _is_master(user: dict) -> bool:
    return str(user.get('role', '')).lower().strip() == 'master' or bool(user.get('is_master_access', False))


@router.post("/stores")
async def create_store(data: StoreCreate, tenant_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    if not _can_manage_stores(user):
        raise HTTPException(status_code=403, detail="Permissao insuficiente")
    is_master = _is_master(user)
    tid = user.get('tenant_id') or ''
    # Master global (sem tenant proprio) precisa indicar o tenant alvo da loja
    if not tid and is_master:
        tid = tenant_id or ''
    if not tid:
        if is_master:
            raise HTTPException(status_code=400, detail="Informe o tenant_id para criar a loja como master")
        raise HTTPException(status_code=400, detail="Sem estabelecimento vinculado")
    # Se o tenant foi informado explicitamente (master), valida que existe
    if tenant_id and is_master:
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
    if not _is_master(user):
        q['tenant_id'] = user.get('tenant_id', '')
    docs = await db.stores.find(q, {"_id": 0}).to_list(1000)
    # filtrar por escopo se nao for admin/master
    if not _is_master(user) and user['role'] not in ADMIN_ROLES:
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
async def update_store(sid: str, request: Request, user: dict = Depends(get_current_user)):
    if not _can_manage_stores(user):
        raise HTTPException(status_code=403, detail="Permissao insuficiente")
    body = await request.json()
    target = await db.stores.find_one({"id": sid}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Nao encontrada")
    if not _is_master(user):
        await verify_tenant_access(user, target['tenant_id'])
    body.pop('id', None); body.pop('tenant_id', None); body.pop('created_at', None)
    await db.stores.update_one({"id": sid}, {"$set": body})
    await audit.log(user['sub'], user['email'], "EDITAR", "store", sid, target['tenant_id'])
    return {"message": "Atualizada"}

@router.delete("/stores/{sid}")
async def delete_store(sid: str, user: dict = Depends(get_current_user)):
    if not _can_manage_stores(user):
        raise HTTPException(status_code=403, detail="Permissao insuficiente")
    target = await db.stores.find_one({"id": sid}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Nao encontrada")
    if not _is_master(user):
        await verify_tenant_access(user, target['tenant_id'])
    # bloquear se houver warehouses ativos
    count = await db.warehouses.count_documents({"store_id": sid, "active": True})
    if count > 0:
        raise HTTPException(status_code=400, detail=f"Existem {count} deposito(s) ativo(s) nesta loja")
    await db.stores.delete_one({"id": sid})
    await audit.log(user['sub'], user['email'], "EXCLUIR", "store", sid, target['tenant_id'])
    return {"message": "Excluida"}
