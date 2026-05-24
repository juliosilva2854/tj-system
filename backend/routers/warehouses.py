from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone
from database import db, audit
from deps import get_current_user, require_roles
from models import WarehouseCreate, ALL_MODULES, gen_id
from permissions import (
    verify_tenant_access, verify_warehouse_access, get_user_warehouse_scope,
    CAN_MANAGE_WAREHOUSES, ADMIN_ROLES, OPERATIONS_ROLES,
)

router = APIRouter(tags=["warehouses"])

@router.post("/warehouses")
async def create_warehouse(data: WarehouseCreate, user: dict = Depends(require_roles(*CAN_MANAGE_WAREHOUSES))):
    if user['role'] == 'master':
        raise HTTPException(status_code=403, detail="Master nao cria deposito diretamente")
    tid = user.get('tenant_id', '')
    if not tid:
        raise HTTPException(status_code=400, detail="Usuario sem estabelecimento vinculado")
    if data.type == "filho" and not data.parent_id:
        raise HTTPException(status_code=400, detail="Deposito FILHO precisa de um Deposito PAI vinculado")
    if data.parent_id:
        parent = await db.warehouses.find_one({"id": data.parent_id, "tenant_id": tid}, {"_id": 0})
        if not parent:
            raise HTTPException(status_code=404, detail="Deposito PAI nao encontrado")
        if parent.get('type') != 'pai':
            raise HTTPException(status_code=400, detail="O deposito vinculado precisa ser do tipo PAI")
    # store_id (loja)
    store_id = data.store_id or ""
    if store_id:
        s = await db.stores.find_one({"id": store_id, "tenant_id": tid}, {"_id": 0})
        if not s:
            raise HTTPException(status_code=404, detail="Loja nao encontrada")
    elif data.parent_id:
        # FILHO herda store_id do PAI
        store_id = parent.get('store_id') or ""
    # modulos default = todos
    enabled_modules = data.enabled_modules if data.enabled_modules is not None else list(ALL_MODULES)
    if data.type == 'filho':
        enabled_modules = []  # FILHO herda do PAI; nao armazena
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": gen_id(), "tenant_id": tid, "store_id": store_id,
        "name": data.name, "location": data.location,
        "description": data.description or "", "type": data.type,
        "parent_id": data.parent_id or "", "sectors": data.sectors,
        "enabled_modules": enabled_modules,
        "active": True, "created_at": now, "created_by": user['sub']
    }
    await db.warehouses.insert_one(doc); doc.pop("_id", None)
    await audit.log(user['sub'], user['email'], "CRIAR", "deposito", doc['id'], tid, warehouse_id=doc['id'], store_id=store_id)
    return doc

@router.get("/warehouses")
async def list_warehouses(user: dict = Depends(get_current_user)):
    q = {}
    tid = user.get('tenant_id')
    if user['role'] != 'master' and tid:
        q['tenant_id'] = tid
    docs = await db.warehouses.find(q, {"_id": 0}).to_list(1000)
    # restringir por escopo (exceto admin/master)
    if user['role'] not in ADMIN_ROLES:
        scope = await get_user_warehouse_scope(user)
        if scope is not None:
            docs = [d for d in docs if d['id'] in scope]
    return docs

@router.patch("/warehouses/{wid}")
async def update_warehouse(wid: str, request: Request, user: dict = Depends(require_roles(*CAN_MANAGE_WAREHOUSES))):
    body = await request.json()
    target = await db.warehouses.find_one({"id": wid}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    await verify_tenant_access(user, target['tenant_id'])
    if user['role'] not in ADMIN_ROLES:
        await verify_warehouse_access(user, wid)
    body.pop('id', None); body.pop('tenant_id', None); body.pop('created_at', None)
    # nao deixar editar enabled_modules por aqui (so master via /modules)
    body.pop('enabled_modules', None)
    await db.warehouses.update_one({"id": wid}, {"$set": body})
    await audit.log(user['sub'], user['email'], "EDITAR", "deposito", wid, target['tenant_id'], warehouse_id=wid)
    return {"message": "Atualizado"}

@router.delete("/warehouses/{wid}")
async def delete_warehouse(wid: str, user: dict = Depends(require_roles("master", "admin"))):
    target = await db.warehouses.find_one({"id": wid}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    await verify_tenant_access(user, target['tenant_id'])
    await db.warehouses.delete_one({"id": wid})
    await audit.log(user['sub'], user['email'], "EXCLUIR", "deposito", wid, target['tenant_id'], warehouse_id=wid)
    return {"message": "Excluido"}
