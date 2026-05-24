"""Helpers de RBAC, escopo multi-warehouse e modulos.

Roles:
  master           - acesso global, todos os tenants
  admin            - admin do tenant, todas as lojas/warehouses
  gerente_geral    - acesso a multiplas lojas (via store_ids) ou multiplos warehouses
  gerente_logistica- gerente de PAIs (almoxarifados)
  gerente_operacional- gerente de FILHOs (setores)
  logistica        - legado, equivalente a gerente_logistica
  operacional      - legado, single FILHO
"""
from typing import List, Set, Optional
from fastapi import HTTPException
from database import db
from models import ALL_MODULES

# === GROUPS ===
ADMIN_ROLES = {"master", "admin"}
GENERAL_MANAGER_ROLES = {"gerente_geral"}
LOGISTICS_ROLES = {"logistica", "gerente_logistica"}
OPERATIONS_ROLES = {"operacional", "gerente_operacional"}
MANAGER_ROLES = GENERAL_MANAGER_ROLES | LOGISTICS_ROLES | OPERATIONS_ROLES

# Quem pode aprovar requisicoes (FILHO -> PAI)
CAN_APPROVE_REQUISITION = ADMIN_ROLES | LOGISTICS_ROLES | GENERAL_MANAGER_ROLES
# Quem pode criar transferencias entre lojas (PAI -> PAI)
CAN_TRANSFER_BETWEEN_STORES = ADMIN_ROLES | GENERAL_MANAGER_ROLES
# Quem pode criar warehouses
CAN_MANAGE_WAREHOUSES = ADMIN_ROLES | LOGISTICS_ROLES | GENERAL_MANAGER_ROLES
# Quem pode CRUD produtos / fornecedores / notas
CAN_MANAGE_PRODUCTS = ADMIN_ROLES | LOGISTICS_ROLES | GENERAL_MANAGER_ROLES
CAN_MANAGE_INVOICES = ADMIN_ROLES | LOGISTICS_ROLES | GENERAL_MANAGER_ROLES
# Quem pode ver auditoria
CAN_VIEW_AUDIT = ADMIN_ROLES | MANAGER_ROLES
# Quem pode ver relatorios
CAN_VIEW_REPORTS = ADMIN_ROLES | GENERAL_MANAGER_ROLES
# Quem pode gerenciar usuarios
CAN_MANAGE_USERS = ADMIN_ROLES

# === SCOPE ===

async def get_user_warehouse_scope(user: dict) -> Optional[Set[str]]:
    """Retorna o conjunto de warehouse_ids ao qual o usuario tem acesso.
    None = acesso total (master / admin). Set vazio = nenhum acesso.
    """
    role = user.get('role')
    if role in ADMIN_ROLES:
        return None
    ids: Set[str] = set()
    # warehouse_id legado
    legacy = user.get('warehouse_id')
    if legacy:
        ids.add(legacy)
    # multi warehouses
    for w in (user.get('warehouse_ids') or []):
        ids.add(w)
    # warehouses por loja
    store_ids = user.get('store_ids') or []
    if store_ids:
        cursor = db.warehouses.find({"store_id": {"$in": store_ids}, "active": True}, {"_id": 0, "id": 1})
        async for w in cursor:
            ids.add(w['id'])
    return ids

async def get_user_store_scope(user: dict) -> Optional[Set[str]]:
    """Retorna o conjunto de store_ids ao qual o usuario tem acesso.
    None = total. Set vazio = nenhum (mas pode ter warehouses avulsos).
    """
    if user.get('role') in ADMIN_ROLES:
        return None
    return set(user.get('store_ids') or [])

async def verify_tenant_access(user: dict, tenant_id: str):
    if user.get('role') == 'master':
        return
    if user.get('tenant_id') != tenant_id:
        raise HTTPException(status_code=403, detail="Acesso negado a este estabelecimento")

async def verify_warehouse_access(user: dict, warehouse_id: str):
    """Garante que o warehouse esta no escopo do usuario.
    Para master/admin, apenas exige mesmo tenant (admin) ou nada (master)."""
    role = user.get('role')
    if role == 'master':
        return
    wh = await db.warehouses.find_one({"id": warehouse_id}, {"_id": 0})
    if not wh:
        raise HTTPException(status_code=404, detail="Deposito nao encontrado")
    if wh.get('tenant_id') != user.get('tenant_id'):
        raise HTTPException(status_code=403, detail="Deposito de outro estabelecimento")
    if role == 'admin':
        return
    scope = await get_user_warehouse_scope(user)
    if scope is None:
        return
    if warehouse_id not in scope:
        raise HTTPException(status_code=403, detail="Sem acesso a este deposito")

# === MODULES ===

async def get_user_enabled_modules(user: dict) -> List[str]:
    """Retorna lista de modulos efetivos para o usuario.
    master/admin: todos. Outros: uniao dos enabled_modules dos PAIs no seu escopo.
    """
    role = user.get('role')
    if role in ADMIN_ROLES:
        return list(ALL_MODULES)
    scope = await get_user_warehouse_scope(user)
    if scope is None:
        return list(ALL_MODULES)
    if not scope:
        return []
    # Pega PAIs do escopo + PAIs dos FILHOs no escopo
    whs = await db.warehouses.find({"id": {"$in": list(scope)}}, {"_id": 0}).to_list(1000)
    pai_ids: Set[str] = set()
    for w in whs:
        if w.get('type') == 'pai':
            pai_ids.add(w['id'])
        elif w.get('parent_id'):
            pai_ids.add(w['parent_id'])
    if not pai_ids:
        return list(ALL_MODULES)
    pais = await db.warehouses.find({"id": {"$in": list(pai_ids)}}, {"_id": 0}).to_list(1000)
    modules: Set[str] = set()
    for p in pais:
        em = p.get('enabled_modules')
        if not em:
            # Sem config = todos habilitados
            return list(ALL_MODULES)
        for m in em:
            modules.add(m)
    return sorted(modules)

async def is_module_enabled_for_warehouse(warehouse_id: str, module: str) -> bool:
    wh = await db.warehouses.find_one({"id": warehouse_id}, {"_id": 0})
    if not wh:
        return False
    pai_id = warehouse_id if wh.get('type') == 'pai' else wh.get('parent_id')
    if not pai_id:
        return True
    pai = await db.warehouses.find_one({"id": pai_id}, {"_id": 0})
    if not pai:
        return True
    em = pai.get('enabled_modules') or []
    if not em:
        return True  # sem config = tudo habilitado
    return module in em
