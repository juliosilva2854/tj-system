"""Transferencias entre LOJAS - PAI -> PAI dentro do mesmo tenant.
Apenas master, admin e gerente_geral podem criar/aprovar.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from database import db, audit
from deps import get_current_user, require_roles
from models import TransferCreate, gen_id
from permissions import (
    verify_tenant_access, verify_warehouse_access, get_user_warehouse_scope,
    CAN_TRANSFER_BETWEEN_STORES, ADMIN_ROLES,
)
from notifications_service import notify_users, check_low_stock, warehouse_watcher_ids

router = APIRouter(tags=["transfers"])

@router.post("/transfers")
async def create_transfer(data: TransferCreate, user: dict = Depends(require_roles(*CAN_TRANSFER_BETWEEN_STORES))):
    tid = user.get('tenant_id', '')
    if not tid and user['role'] != 'master':
        raise HTTPException(status_code=400, detail="Sem estabelecimento")
    if data.from_warehouse_id == data.to_warehouse_id:
        raise HTTPException(status_code=400, detail="Origem e destino devem ser diferentes")
    src = await db.warehouses.find_one({"id": data.from_warehouse_id}, {"_id": 0})
    dst = await db.warehouses.find_one({"id": data.to_warehouse_id}, {"_id": 0})
    if not src or not dst:
        raise HTTPException(status_code=404, detail="Deposito origem ou destino nao encontrado")
    target_tid = src['tenant_id']
    if user['role'] != 'master':
        await verify_tenant_access(user, target_tid)
    if src.get('tenant_id') != dst.get('tenant_id'):
        raise HTTPException(status_code=400, detail="Transferencia somente dentro do mesmo estabelecimento")
    if src.get('type') != 'pai' or dst.get('type') != 'pai':
        raise HTTPException(status_code=400, detail="Transferencias entre lojas sao apenas entre depositos PAI")
    # gerente_geral precisa ter acesso a ambos
    if user['role'] not in ADMIN_ROLES:
        await verify_warehouse_access(user, data.from_warehouse_id)
        await verify_warehouse_access(user, data.to_warehouse_id)
    # validar estoque na origem para todos os itens
    for item in data.items:
        inv = await db.inventory.find_one({
            "product_id": item.product_id,
            "warehouse_id": data.from_warehouse_id,
            "tenant_id": target_tid,
        }, {"_id": 0})
        avail = inv['quantity'] if inv else 0
        if avail < item.quantity:
            raise HTTPException(status_code=400, detail=f"Estoque insuficiente para {item.product_name} (disponivel: {avail})")
    # criar o registro e executar imediatamente
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": gen_id(), "tenant_id": target_tid,
        "from_store_id": src.get('store_id', ''),
        "to_store_id": dst.get('store_id', ''),
        "from_warehouse_id": data.from_warehouse_id,
        "to_warehouse_id": data.to_warehouse_id,
        "items": [i.model_dump() for i in data.items],
        "notes": data.notes or "",
        "status": "completed",
        "created_at": now, "created_by": user['sub'],
        "resolved_at": now, "resolved_by": user['sub'],
    }
    await db.transfers.insert_one(doc); doc.pop("_id", None)
    # debitar origem e creditar destino
    for item in data.items:
        src_inv = await db.inventory.find_one({
            "product_id": item.product_id,
            "warehouse_id": data.from_warehouse_id,
            "tenant_id": target_tid,
        }, {"_id": 0})
        await db.inventory.update_one({"id": src_inv['id']},
            {"$set": {"quantity": max(0, src_inv['quantity'] - item.quantity), "updated_at": now}})
        dst_inv = await db.inventory.find_one({
            "product_id": item.product_id,
            "warehouse_id": data.to_warehouse_id,
            "tenant_id": target_tid,
        }, {"_id": 0})
        if dst_inv:
            await db.inventory.update_one({"id": dst_inv['id']},
                {"$set": {"quantity": dst_inv['quantity'] + item.quantity, "updated_at": now,
                          "product_name": item.product_name, "product_sku": getattr(item, 'product_sku', '') or ''}})
        else:
            await db.inventory.insert_one({
                "id": gen_id(), "tenant_id": target_tid, "product_id": item.product_id,
                "warehouse_id": data.to_warehouse_id, "quantity": item.quantity, "updated_at": now,
                "product_name": item.product_name, "product_sku": getattr(item, 'product_sku', '') or '',
            })
    await audit.log(user['sub'], user['email'], "TRANSFERIR_ENTRE_LOJAS", "transferencia",
                    doc['id'], target_tid,
                    {"de": src['name'], "para": dst['name'], "itens": len(data.items)},
                    warehouse_id=data.from_warehouse_id, store_id=src.get('store_id', ''))
    # Notifica observadores do deposito de destino + verifica estoque baixo na origem
    receivers = await warehouse_watcher_ids(target_tid, dst)
    await notify_users(
        receivers, "transfer_received",
        "Transferencia recebida",
        f"{dst['name']} recebeu {len(data.items)} item(ns) de {src['name']}.",
        ntype="info", meta={"transfer_id": doc['id']}, exclude_user_id=user['sub'],
    )
    for item in data.items:
        await check_low_stock(target_tid, data.from_warehouse_id, item.product_id)
    return doc

@router.get("/transfers")
async def list_transfers(user: dict = Depends(get_current_user)):
    q = {}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    docs = await db.transfers.find(q, {"_id": 0}).sort('created_at', -1).to_list(1000)
    if user['role'] not in ADMIN_ROLES:
        scope = await get_user_warehouse_scope(user)
        if scope is not None:
            docs = [d for d in docs if d.get('from_warehouse_id') in scope or d.get('to_warehouse_id') in scope]
    return docs

@router.get("/transfers/{tid}")
async def get_transfer(tid: str, user: dict = Depends(get_current_user)):
    doc = await db.transfers.find_one({"id": tid}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Nao encontrada")
    if user['role'] != 'master':
        await verify_tenant_access(user, doc['tenant_id'])
    return doc
