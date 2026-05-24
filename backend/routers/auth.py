from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import db, audit
from auth import hash_password, verify_password, create_refresh_token, decode_token, token_from_user_doc
from deps import get_current_user, require_roles
from models import UserCreate, UserLogin, gen_id

router = APIRouter(tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, creds: UserLogin):
    doc = await db.users.find_one({"email": creds.email}, {"_id": 0})
    if not doc or not verify_password(creds.password, doc['password_hash']):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    if not doc.get('active', True):
        raise HTTPException(status_code=403, detail="Conta inativa")
    access = token_from_user_doc(doc)
    refresh = create_refresh_token(doc['id'])
    user_out = {k: doc.get(k) for k in [
        'id', 'email', 'name', 'role', 'tenant_id', 'warehouse_id',
        'warehouse_ids', 'store_ids', 'active', 'created_at'
    ] if k in doc}
    return {"access_token": access, "refresh_token": refresh, "user": user_out}

@router.post("/auth/refresh")
async def refresh_token(request: Request):
    body = await request.json()
    token = body.get('refresh_token')
    if not token:
        raise HTTPException(status_code=400, detail="Refresh token obrigatorio")
    payload = decode_token(token)
    if not payload or payload.get('type') != 'refresh':
        raise HTTPException(status_code=401, detail="Refresh token invalido")
    doc = await db.users.find_one({"id": payload['sub']}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado")
    access = token_from_user_doc(doc)
    return {"access_token": access}

@router.get("/auth/me")
async def auth_me(user: dict = Depends(get_current_user)):
    doc = await db.users.find_one({"id": user['sub']}, {"_id": 0, "password_hash": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    tenant_name = ""
    warehouse_name = ""
    store_names = []
    if doc.get('tenant_id'):
        t = await db.tenants.find_one({"id": doc['tenant_id']}, {"_id": 0})
        if t:
            tenant_name = t['name']
    if doc.get('warehouse_id'):
        w = await db.warehouses.find_one({"id": doc['warehouse_id']}, {"_id": 0})
        if w:
            warehouse_name = w['name']
    sids = doc.get('store_ids') or []
    if sids:
        stores = await db.stores.find({"id": {"$in": sids}}, {"_id": 0}).to_list(50)
        store_names = [s['name'] for s in stores]
    doc['tenant_name'] = tenant_name
    doc['warehouse_name'] = warehouse_name
    doc['store_names'] = store_names
    # Modulos efetivos
    from permissions import get_user_enabled_modules
    doc['enabled_modules'] = await get_user_enabled_modules(user)
    return doc

@router.post("/auth/register")
async def register(data: UserCreate, user: dict = Depends(require_roles("master", "admin"))):
    if user['role'] == 'admin' and data.role == 'master':
        raise HTTPException(status_code=403, detail="Admin nao pode criar master")
    if user['role'] == 'admin':
        data.tenant_id = user.get('tenant_id')
    if data.role == 'master':
        data.tenant_id = ''
        data.warehouse_id = ''
        data.warehouse_ids = []
        data.store_ids = []
    else:
        if not data.tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id obrigatorio para esta role")
        t = await db.tenants.find_one({"id": data.tenant_id}, {"_id": 0})
        if not t:
            raise HTTPException(status_code=404, detail="Estabelecimento nao encontrado")
        if data.role == 'operacional' and not data.warehouse_id and not data.warehouse_ids:
            raise HTTPException(status_code=400, detail="Operacional precisa de deposito vinculado")
        if data.warehouse_id:
            w = await db.warehouses.find_one({"id": data.warehouse_id, "tenant_id": data.tenant_id}, {"_id": 0})
            if not w:
                raise HTTPException(status_code=404, detail="Deposito nao encontrado neste estabelecimento")
        # validar warehouse_ids e store_ids
        if data.warehouse_ids:
            count = await db.warehouses.count_documents({"id": {"$in": data.warehouse_ids}, "tenant_id": data.tenant_id})
            if count != len(set(data.warehouse_ids)):
                raise HTTPException(status_code=400, detail="Algum warehouse_id nao pertence ao estabelecimento")
        if data.store_ids:
            count = await db.stores.count_documents({"id": {"$in": data.store_ids}, "tenant_id": data.tenant_id})
            if count != len(set(data.store_ids)):
                raise HTTPException(status_code=400, detail="Alguma loja nao pertence ao estabelecimento")
    existing = await db.users.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email ja cadastrado")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": gen_id(), "email": data.email, "name": data.name, "role": data.role,
        "tenant_id": data.tenant_id or "",
        "warehouse_id": data.warehouse_id or "",
        "warehouse_ids": data.warehouse_ids or [],
        "store_ids": data.store_ids or [],
        "password_hash": hash_password(data.password),
        "active": True, "created_at": now
    }
    await db.users.insert_one(doc); doc.pop("_id", None)
    await audit.log(user['sub'], user['email'], "CRIAR", "usuario", doc['id'], doc.get('tenant_id', ''))
    doc.pop('password_hash')
    return doc
