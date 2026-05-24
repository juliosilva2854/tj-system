from fastapi import APIRouter, Depends, HTTPException, Request, Response
from datetime import datetime, timezone, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import db, audit
from auth import hash_password, verify_password, create_refresh_token, decode_token, token_from_user_doc
from deps import get_current_user, require_roles
from models import UserCreate, UserLogin, gen_id, sanitize_str

router = APIRouter(tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, response: Response, creds: UserLogin):
    """Login dual: username (usuários normais) ou email (master/admin-sistema)
    
    Security: Tokens são armazenados em httpOnly cookies para proteção contra XSS
    """
    identifier = creds.identifier.lower().strip()
    
    # Se is_master=True, busca por email; senão, tenta username primeiro
    if creds.is_master:
        doc = await db.users.find_one({"email": identifier, "is_master_access": True}, {"_id": 0})
    else:
        # Tenta username primeiro, depois email
        doc = await db.users.find_one({"username": identifier}, {"_id": 0})
        if not doc:
            doc = await db.users.find_one({"email": identifier}, {"_id": 0})
    
    if not doc or not verify_password(creds.password, doc['password_hash']):
        raise HTTPException(status_code=401, detail="Credenciais incorretas")
    if not doc.get('active', True):
        raise HTTPException(status_code=403, detail="Conta inativa")
    
    access = token_from_user_doc(doc)
    refresh = create_refresh_token(doc['id'])
    
    # Set httpOnly cookies para segurança contra XSS
    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        secure=True,  # HTTPS only em produção
        samesite="lax",
        max_age=3600  # 1 hora
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800  # 7 dias
    )
    
    user_out = {k: doc.get(k) for k in [
        'id', 'email', 'name', 'username', 'cpf', 'phone', 'role', 'tenant_id', 
        'warehouse_id', 'warehouse_ids', 'store_ids', 'is_master_access',
        'profile_picture', 'permissions', 'managed_by', 'active', 'created_at'
    ] if k in doc}
    
    # Retorna tokens também no body para compatibilidade (pode ser removido depois)
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
    
    # Verifica username único (se fornecido)
    if data.username:
        existing = await db.users.find_one({"username": data.username}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Username ja cadastrado")
    
    # Verifica CPF único (se fornecido)
    if data.cpf:
        existing = await db.users.find_one({"cpf": data.cpf}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="CPF ja cadastrado")
    
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": gen_id(),
        "email": data.email,
        "name": data.name,
        "username": data.username,
        "cpf": data.cpf,
        "phone": data.phone,
        "role": data.role,
        "tenant_id": data.tenant_id or "",
        "warehouse_id": data.warehouse_id or "",
        "warehouse_ids": data.warehouse_ids or [],
        "store_ids": data.store_ids or [],
        "is_master_access": data.is_master_access,
        "permissions": data.permissions or {},
        "managed_by": data.managed_by,
        "profile_picture": None,
        "password_hash": hash_password(data.password),
        "active": True,
        "created_at": now
    }
    await db.users.insert_one(doc)
    doc.pop("_id", None)
    await audit.log(user['sub'], user['email'], "CRIAR", "usuario", doc['id'], doc.get('tenant_id', ''))
    doc.pop('password_hash')
    return doc


# === FORGOT PASSWORD ===
@router.post("/auth/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: dict):
    """Envia email com link de recuperação de senha"""
    from email_service import send_email, build_password_reset_email
    import secrets
    
    identifier = data.get('identifier', '').lower().strip()
    if not identifier:
        raise HTTPException(status_code=400, detail="Email ou username obrigatorio")
    
    # Busca usuário por email ou username
    user = await db.users.find_one({"$or": [{"email": identifier}, {"username": identifier}]}, {"_id": 0})
    
    # Sempre retorna sucesso (segurança: não revelar se user existe)
    if not user:
        return {"message": "Se o usuario existir, um email foi enviado"}
    
    # Gera token aleatório de 32 caracteres
    token = secrets.token_urlsafe(24)[:32]
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    
    # Salva token no banco
    token_doc = {
        "id": gen_id(),
        "token": token,
        "user_id": user['id'],
        "email": user['email'],
        "expires_at": expires_at,
        "used": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.password_reset_tokens.insert_one(token_doc)
    
    # Monta URL de reset (usar FRONTEND_URL do .env)
    import os
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    reset_url = f"{frontend_url}/reset-password?token={token}"
    
    # Envia email
    subject, html = build_password_reset_email(reset_url, user['name'])
    send_email(user['email'], subject, html)
    
    return {"message": "Se o usuario existir, um email foi enviado"}

# === RESET PASSWORD ===
@router.post("/auth/reset-password")
async def reset_password(data: dict):
    """Reseta senha usando token do email"""
    token = data.get('token', '').strip()
    new_password = data.get('new_password', '')
    
    if not token or len(token) != 32:
        raise HTTPException(status_code=400, detail="Token invalido")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter no minimo 6 caracteres")
    
    # Busca token
    token_doc = await db.password_reset_tokens.find_one({"token": token}, {"_id": 0})
    if not token_doc:
        raise HTTPException(status_code=400, detail="Token invalido ou expirado")
    
    # Valida token
    if token_doc['used']:
        raise HTTPException(status_code=400, detail="Token ja foi usado")
    
    expires_at = datetime.fromisoformat(token_doc['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Token expirado")
    
    # Atualiza senha do usuário
    new_hash = hash_password(new_password)
    await db.users.update_one(
        {"id": token_doc['user_id']},
        {"$set": {"password_hash": new_hash}}
    )
    
    # Marca token como usado
    await db.password_reset_tokens.update_one(
        {"token": token},
        {"$set": {"used": True}}
    )
    
    return {"message": "Senha alterada com sucesso"}

# === PROFILE ===
@router.get("/auth/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    """Retorna dados completos do perfil do usuário"""
    doc = await db.users.find_one({"id": user['sub']}, {"_id": 0, "password_hash": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    
    # Dados adicionais (tenant, warehouse, stores)
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
    
    # Módulos efetivos
    from permissions import get_user_enabled_modules
    doc['enabled_modules'] = await get_user_enabled_modules(user)
    
    return doc

@router.put("/auth/profile")
async def update_profile(data: dict, user: dict = Depends(get_current_user)):
    """Atualiza dados do perfil (nome, telefone)"""
    updates = {}
    
    if 'name' in data and data['name']:
        name = sanitize_str(data['name'], 100)
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Nome deve ter no minimo 2 caracteres")
        updates['name'] = name
    
    if 'phone' in data:
        updates['phone'] = data['phone'][:20] if data['phone'] else None
    
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    
    await db.users.update_one({"id": user['sub']}, {"$set": updates})
    
    return {"message": "Perfil atualizado com sucesso"}



@router.post("/auth/logout")
async def logout(response: Response):
    """Logout: limpa cookies httpOnly"""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Logout realizado com sucesso"}

@router.put("/auth/change-password")
async def change_password(data: dict, user: dict = Depends(get_current_user)):
    """Muda senha do usuário (requer senha atual)"""
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Senha atual e nova senha obrigatorias")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Nova senha deve ter no minimo 6 caracteres")
    
    # Verifica senha atual
    doc = await db.users.find_one({"id": user['sub']}, {"_id": 0})
    if not doc or not verify_password(current_password, doc['password_hash']):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")
    
    # Atualiza senha
    new_hash = hash_password(new_password)
    await db.users.update_one({"id": user['sub']}, {"$set": {"password_hash": new_hash}})
    
    return {"message": "Senha alterada com sucesso"}

