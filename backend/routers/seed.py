"""Seed idempotente. Protegido por SEED_SECRET em producao (header X-Seed-Secret).
Cria:
 - Tenant: Arcos Dourados (slug: arcos-dourados)
 - 2 Stores: Restaurante A, Restaurante B
 - Para cada Store: 1 PAI + 2 FILHOs com setores
 - Tenant legado: TJ (compat com testes existentes)
 - Usuarios: master, admin, gerente_geral, gerente_logistica, gerente_operacional, logistica, operacional
"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from database import db
from auth import hash_password
from deps import require_seed_secret
from models import gen_id, ALL_MODULES

router = APIRouter(tags=["seed"])

@router.post("/seed")
async def seed(_: bool = Depends(require_seed_secret)):
    # Detect old single-tenant schema (role="dev"/"usuario") and clear if present
    old = await db.users.find_one({"role": {"$in": ["dev", "usuario"]}}, {"_id": 0})
    if old:
        for coll in ["users", "tenants", "stores", "warehouses", "products", "inventory",
                     "suppliers", "invoices", "requisitions", "transfers", "sales",
                     "audit_logs", "notifications"]:
            await db.get_collection(coll).delete_many({})

    existing = await db.users.find_one({"email": "master@sconnecta.com.br"}, {"_id": 0})
    if existing:
        # Backfill warehouse_ids/store_ids para usuarios antigos que nao tem
        await db.users.update_many({"warehouse_ids": {"$exists": False}}, {"$set": {"warehouse_ids": []}})
        await db.users.update_many({"store_ids": {"$exists": False}}, {"$set": {"store_ids": []}})
        
        # Backfill novos campos de autenticação
        await db.users.update_many({"username": {"$exists": False}}, {"$set": {"username": None}})
        await db.users.update_many({"cpf": {"$exists": False}}, {"$set": {"cpf": None}})
        await db.users.update_many({"phone": {"$exists": False}}, {"$set": {"phone": None}})
        await db.users.update_many({"is_master_access": {"$exists": False}}, {"$set": {"is_master_access": False}})
        await db.users.update_many({"permissions": {"$exists": False}}, {"$set": {"permissions": {}}})
        await db.users.update_many({"managed_by": {"$exists": False}}, {"$set": {"managed_by": None}})
        await db.users.update_many({"profile_picture": {"$exists": False}}, {"$set": {"profile_picture": None}})
        
        # Atualizar master para ter is_master_access=True
        await db.users.update_one({"role": "master"}, {"$set": {"is_master_access": True}})
        
        return {"message": "Ja inicializado"}

    now = datetime.now(timezone.utc).isoformat()
    all_mods = list(ALL_MODULES)

    # Tenant LEGADO Unidade TJ (compat com testes anteriores)
    legacy_tid = gen_id()
    legacy_pai_id = gen_id()
    legacy_filho_id = gen_id()
    legacy_store_id = gen_id()
    await db.tenants.insert_one({"id": legacy_tid, "name": "Unidade TJ", "slug": "tj",
                                  "active": True, "created_at": now})
    await db.stores.insert_one({"id": legacy_store_id, "tenant_id": legacy_tid,
                                  "name": "Sede TJ", "code": "TJ", "address": "Sede",
                                  "active": True, "created_at": now, "created_by": "seed"})
    await db.warehouses.insert_many([
        {"id": legacy_pai_id, "tenant_id": legacy_tid, "store_id": legacy_store_id,
         "name": "Almoxarifado Central", "location": "Sede",
         "description": "Estoque PAI - recebe Notas Fiscais",
         "type": "pai", "parent_id": "", "sectors": ["Geral"],
         "enabled_modules": all_mods,
         "active": True, "created_at": now, "created_by": "seed"},
        {"id": legacy_filho_id, "tenant_id": legacy_tid, "store_id": legacy_store_id,
         "name": "Setor Operacional A", "location": "Unidade Operacional",
         "description": "Estoque FILHO - consome via requisicoes",
         "type": "filho", "parent_id": legacy_pai_id,
         "sectors": ["Atendimento", "Producao"],
         "enabled_modules": [],
         "active": True, "created_at": now, "created_by": "seed"},
    ])

    # Tenant ARCOS DOURADOS com 2 lojas e gerentes
    arcos_tid = gen_id()
    await db.tenants.insert_one({"id": arcos_tid, "name": "Arcos Dourados",
                                  "slug": "arcos-dourados", "active": True, "created_at": now})
    rest_a_id = gen_id(); rest_b_id = gen_id()
    await db.stores.insert_many([
        {"id": rest_a_id, "tenant_id": arcos_tid, "name": "Restaurante A",
         "code": "REST-A", "address": "Av. Paulista, 1000", "active": True,
         "created_at": now, "created_by": "seed"},
        {"id": rest_b_id, "tenant_id": arcos_tid, "name": "Restaurante B",
         "code": "REST-B", "address": "Av. Faria Lima, 2500", "active": True,
         "created_at": now, "created_by": "seed"},
    ])
    pai_a = gen_id(); filho_a1 = gen_id(); filho_a2 = gen_id()
    pai_b = gen_id(); filho_b1 = gen_id()
    await db.warehouses.insert_many([
        # Restaurante A
        {"id": pai_a, "tenant_id": arcos_tid, "store_id": rest_a_id,
         "name": "Almoxarifado Rest. A", "location": "Restaurante A",
         "description": "Deposito central da loja A",
         "type": "pai", "parent_id": "", "sectors": ["Geral"],
         "enabled_modules": all_mods,
         "active": True, "created_at": now, "created_by": "seed"},
        {"id": filho_a1, "tenant_id": arcos_tid, "store_id": rest_a_id,
         "name": "Cozinha A", "location": "Restaurante A - Cozinha",
         "description": "Setor cozinha", "type": "filho", "parent_id": pai_a,
         "sectors": ["Forno", "Geladeira"], "enabled_modules": [],
         "active": True, "created_at": now, "created_by": "seed"},
        {"id": filho_a2, "tenant_id": arcos_tid, "store_id": rest_a_id,
         "name": "Salao A", "location": "Restaurante A - Salao",
         "description": "Setor salao", "type": "filho", "parent_id": pai_a,
         "sectors": ["Bar", "Atendimento"], "enabled_modules": [],
         "active": True, "created_at": now, "created_by": "seed"},
        # Restaurante B
        {"id": pai_b, "tenant_id": arcos_tid, "store_id": rest_b_id,
         "name": "Almoxarifado Rest. B", "location": "Restaurante B",
         "description": "Deposito central da loja B",
         "type": "pai", "parent_id": "", "sectors": ["Geral"],
         "enabled_modules": all_mods,
         "active": True, "created_at": now, "created_by": "seed"},
        {"id": filho_b1, "tenant_id": arcos_tid, "store_id": rest_b_id,
         "name": "Cozinha B", "location": "Restaurante B - Cozinha",
         "description": "Setor cozinha", "type": "filho", "parent_id": pai_b,
         "sectors": ["Forno", "Geladeira"], "enabled_modules": [],
         "active": True, "created_at": now, "created_by": "seed"},
    ])

    users = [
        # MASTER GLOBAL (acesso via email em administrator.sconnecta.com.br)
        {"id": gen_id(), "email": "master@sconnecta.com.br", "name": "Master Global",
         "username": None, "cpf": None, "phone": None,
         "role": "master", "tenant_id": "", "warehouse_id": "",
         "warehouse_ids": [], "store_ids": [],
         "is_master_access": True, "permissions": {}, "managed_by": None,
         "profile_picture": None,
         "password_hash": hash_password("Master@2026"), "active": True, "created_at": now},
        
        # Tenant LEGADO TJ
        {"id": gen_id(), "email": "admin@tj.sconnecta.com.br", "name": "Admin TJ",
         "username": "admin.tj", "cpf": "12345678901", "phone": "(11) 98888-1111",
         "role": "admin", "tenant_id": legacy_tid, "warehouse_id": "",
         "warehouse_ids": [], "store_ids": [],
         "is_master_access": False, "permissions": {}, "managed_by": None,
         "profile_picture": None,
         "password_hash": hash_password("Admin@2026"), "active": True, "created_at": now},
        
        {"id": gen_id(), "email": "logistica@tj.sconnecta.com.br", "name": "Logistica PAI",
         "username": "logistica.tj", "cpf": "98765432109", "phone": "(11) 98888-2222",
         "role": "logistica", "tenant_id": legacy_tid, "warehouse_id": legacy_pai_id,
         "warehouse_ids": [legacy_pai_id], "store_ids": [legacy_store_id],
         "is_master_access": False, "permissions": {}, "managed_by": None,
         "profile_picture": None,
         "password_hash": hash_password("Logistica@2026"), "active": True, "created_at": now},
        
        {"id": gen_id(), "email": "operacional@tj.sconnecta.com.br", "name": "Operacional FILHO",
         "username": "operacional.tj", "cpf": "11122233344", "phone": "(11) 98888-3333",
         "role": "operacional", "tenant_id": legacy_tid, "warehouse_id": legacy_filho_id,
         "warehouse_ids": [legacy_filho_id], "store_ids": [],
         "is_master_access": False, "permissions": {}, "managed_by": None,
         "profile_picture": None,
         "password_hash": hash_password("Operacional@2026"), "active": True, "created_at": now},
        
        # Tenant ARCOS DOURADOS
        {"id": gen_id(), "email": "admin@arcos.sconnecta.com.br", "name": "Admin Arcos",
         "username": "admin.arcos", "cpf": "55566677788", "phone": "(11) 98888-4444",
         "role": "admin", "tenant_id": arcos_tid, "warehouse_id": "",
         "warehouse_ids": [], "store_ids": [],
         "is_master_access": False, "permissions": {}, "managed_by": None,
         "profile_picture": None,
         "password_hash": hash_password("Admin@2026"), "active": True, "created_at": now},
        
        {"id": gen_id(), "email": "gerentegeral@arcos.sconnecta.com.br", "name": "Gerente Geral Arcos",
         "username": "geral.arcos", "cpf": "99988877766", "phone": "(11) 98888-5555",
         "role": "gerente_geral", "tenant_id": arcos_tid, "warehouse_id": "",
         "warehouse_ids": [], "store_ids": [rest_a_id, rest_b_id],
         "is_master_access": False, "permissions": {}, "managed_by": None,
         "profile_picture": None,
         "password_hash": hash_password("GerenteGeral@2026"), "active": True, "created_at": now},
        
        {"id": gen_id(), "email": "gerentelogA@arcos.sconnecta.com.br", "name": "Gerente Logistica Rest. A",
         "username": "logistica.restA", "cpf": "22233344455", "phone": "(11) 98888-6666",
         "role": "gerente_logistica", "tenant_id": arcos_tid, "warehouse_id": pai_a,
         "warehouse_ids": [pai_a], "store_ids": [rest_a_id],
         "is_master_access": False, "permissions": {}, "managed_by": None,
         "profile_picture": None,
         "password_hash": hash_password("GerenteLog@2026"), "active": True, "created_at": now},
        
        {"id": gen_id(), "email": "gerenteopA@arcos.sconnecta.com.br", "name": "Gerente Operacional Rest. A",
         "username": "operacional.restA", "cpf": "66677788899", "phone": "(11) 98888-7777",
         "role": "gerente_operacional", "tenant_id": arcos_tid, "warehouse_id": filho_a1,
         "warehouse_ids": [filho_a1, filho_a2], "store_ids": [],
         "is_master_access": False, "permissions": {}, "managed_by": None,
         "profile_picture": None,
         "password_hash": hash_password("GerenteOp@2026"), "active": True, "created_at": now},
    ]
    await db.users.insert_many(users)
    
    # Criar índices únicos
    try:
        await db.users.create_index("email", unique=True)
    except Exception:
        pass
    try:
        await db.users.create_index("username", unique=True, sparse=True)
    except Exception:
        pass
    try:
        await db.users.create_index("cpf", unique=True, sparse=True)
    except Exception:
        pass
    try:
        await db.tenants.create_index("slug", unique=True)
    except Exception:
        pass
    return {
        "message": "Sistema inicializado",
        "tenants": {"legacy_tj": legacy_tid, "arcos_dourados": arcos_tid},
        "stores": {"sede_tj": legacy_store_id, "restaurante_a": rest_a_id, "restaurante_b": rest_b_id},
        "warehouses": {
            "legacy_pai": legacy_pai_id, "legacy_filho": legacy_filho_id,
            "pai_a": pai_a, "filho_a1": filho_a1, "filho_a2": filho_a2,
            "pai_b": pai_b, "filho_b1": filho_b1,
        },
        # Compat com testes antigos
        "tenant_id": legacy_tid,
        "pai_warehouse_id": legacy_pai_id,
        "filho_warehouse_id": legacy_filho_id,
    }
