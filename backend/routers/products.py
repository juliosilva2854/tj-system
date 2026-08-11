from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone
from database import db, audit
from deps import get_current_user, require_roles
from models import ProductCreate, gen_id
from permissions import (
    verify_tenant_access, verify_warehouse_access,
    CAN_MANAGE_PRODUCTS, ADMIN_ROLES,
)

router = APIRouter(tags=["products"])

@router.post("/products")
async def create_product(data: ProductCreate, user: dict = Depends(require_roles(*CAN_MANAGE_PRODUCTS))):
    tid = user.get('tenant_id', '')
    if not tid and user['role'] != 'master':
        raise HTTPException(status_code=400, detail="Sem estabelecimento vinculado")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": gen_id(), "tenant_id": tid, **data.model_dump(),
        "available_qty": 0, "active": True, "created_at": now, "created_by": user['sub']
    }
    await db.products.insert_one(doc); doc.pop("_id", None)
    await audit.log(user['sub'], user['email'], "CRIAR", "produto", doc['id'], tid)
    return doc

@router.get("/products")
async def list_products(user: dict = Depends(get_current_user)):
    q = {}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    return await db.products.find(q, {"_id": 0}).to_list(5000)

@router.patch("/products/{pid}")
async def update_product(pid: str, request: Request, user: dict = Depends(require_roles(*CAN_MANAGE_PRODUCTS))):
    body = await request.json()
    target = await db.products.find_one({"id": pid}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    if user['role'] != 'master':
        await verify_tenant_access(user, target['tenant_id'])
    body.pop('id', None); body.pop('tenant_id', None)
    await db.products.update_one({"id": pid}, {"$set": body})
    await audit.log(user['sub'], user['email'], "EDITAR", "produto", pid, target['tenant_id'])
    return {"message": "Atualizado"}

@router.post("/products/{pid}/transfer")
async def transfer_product(pid: str, warehouse_id: str, quantity: float, sector: str = "",
                            user: dict = Depends(require_roles(*CAN_MANAGE_PRODUCTS))):
    product = await db.products.find_one({"id": pid}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    if user['role'] != 'master':
        await verify_tenant_access(user, product['tenant_id'])
        await verify_warehouse_access(user, warehouse_id)
    wh = await db.warehouses.find_one({"id": warehouse_id, "tenant_id": product['tenant_id']}, {"_id": 0})
    if not wh:
        raise HTTPException(status_code=404, detail="Deposito nao encontrado neste estabelecimento")
    avail = product.get('available_qty', 0)
    if quantity > avail:
        quantity = avail
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantidade invalida")
    inv = await db.inventory.find_one({"product_id": pid, "warehouse_id": warehouse_id, "tenant_id": product['tenant_id']}, {"_id": 0})
    now = datetime.now(timezone.utc).isoformat()
    if inv:
        await db.inventory.update_one({"id": inv['id']}, {"$set": {
            "quantity": inv['quantity'] + quantity, "updated_at": now,
            # mantem nome/sku denormalizados atualizados
            "product_name": product.get('name', ''), "product_sku": product.get('sku', ''),
        }})
    else:
        await db.inventory.insert_one({
            "id": gen_id(), "tenant_id": product['tenant_id'], "product_id": pid, "warehouse_id": warehouse_id,
            "quantity": quantity, "updated_at": now,
            # desnormaliza nome/sku para preservar integridade referencial no estoque
            "product_name": product.get('name', ''), "product_sku": product.get('sku', ''),
        })
    new_avail = avail - quantity
    # NAO deletamos mais o produto ao zerar (isso quebrava o join do estoque -> "Desconhecido").
    # Apenas zeramos available_qty; ele some da aba Produtos pendentes mas continua consultavel.
    await db.products.update_one({"id": pid}, {"$set": {"available_qty": max(0, new_avail)}})
    if new_avail <= 0:
        msg = f"Transferido {quantity} para {wh['name']}. Produto enviado ao estoque."
    else:
        msg = f"Transferido {quantity} para {wh['name']}. Restam {new_avail}."
    await audit.log(user['sub'], user['email'], "TRANSFERIR", "produto", pid, product['tenant_id'],
                    {"deposito": wh['name'], "quantidade": quantity, "setor": sector},
                    warehouse_id=warehouse_id)
    return {"message": msg, "removed": new_avail <= 0}
