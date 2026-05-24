from fastapi import APIRouter, Depends, HTTPException, Body
from datetime import datetime, timezone
from database import db, audit
from deps import get_current_user
from permissions import (
    verify_tenant_access, verify_warehouse_access, get_user_warehouse_scope, ADMIN_ROLES,
)
from models import gen_id, InventoryAdjust

router = APIRouter(tags=["inventory"])

@router.get("/inventory")
async def list_inventory(user: dict = Depends(get_current_user)):
    q = {}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    items = await db.inventory.find(q, {"_id": 0}).to_list(5000)
    # filtrar por escopo de warehouse para nao-admin
    if user['role'] not in ADMIN_ROLES:
        scope = await get_user_warehouse_scope(user)
        if scope is not None:
            items = [it for it in items if it.get('warehouse_id') in scope]
    # batch fetch para evitar N+1
    pids = list({it['product_id'] for it in items})
    wids = list({it['warehouse_id'] for it in items})
    pdocs = {p['id']: p for p in await db.products.find({"id": {"$in": pids}}, {"_id": 0}).to_list(5000)}
    wdocs = {w['id']: w for w in await db.warehouses.find({"id": {"$in": wids}}, {"_id": 0}).to_list(1000)}
    result = []
    for it in items:
        p = pdocs.get(it['product_id'])
        w = wdocs.get(it['warehouse_id'])
        result.append({
            "id": it['id'], "tenant_id": it.get('tenant_id', ''),
            "product_id": it['product_id'],
            "product_name": p['name'] if p else 'Desconhecido',
            "product_sku": p['sku'] if p else '',
            "warehouse_id": it['warehouse_id'],
            "warehouse_name": w['name'] if w else 'Desconhecido',
            "warehouse_type": w.get('type', 'pai') if w else 'pai',
            "store_id": w.get('store_id', '') if w else '',
            "quantity": it['quantity'],
            "min_stock": p.get('min_stock', 0) if p else 0,
            "updated_at": it.get('updated_at', '')
        })
    return result

@router.post("/inventory/adjust")
async def adjust_inventory(
    product_id: str | None = None,
    warehouse_id: str | None = None,
    quantity: float | None = None,
    sector: str | None = None,
    reason: str | None = None,
    data: InventoryAdjust | None = Body(None),
    user: dict = Depends(get_current_user),
):
    # Aceita query params (legado) ou JSON body (novo)
    if data is None:
        if not product_id or not warehouse_id or quantity is None:
            raise HTTPException(status_code=422, detail="product_id, warehouse_id, quantity obrigatorios")
        data = InventoryAdjust(product_id=product_id, warehouse_id=warehouse_id,
                               quantity=quantity, sector=sector, reason=reason)
    tid = user.get('tenant_id', '')
    # Garantir warehouse no mesmo tenant + escopo do usuario
    if user['role'] != 'master':
        await verify_warehouse_access(user, data.warehouse_id)
    wh = await db.warehouses.find_one({"id": data.warehouse_id}, {"_id": 0})
    if not wh:
        raise HTTPException(status_code=404, detail="Deposito nao encontrado")
    if user['role'] != 'master' and wh.get('tenant_id') != tid:
        raise HTTPException(status_code=403, detail="Deposito de outro estabelecimento")
    # Inventory check com tenant
    target_tid = wh.get('tenant_id') if user['role'] == 'master' else tid
    inv = await db.inventory.find_one({
        "product_id": data.product_id,
        "warehouse_id": data.warehouse_id,
        "tenant_id": target_tid,
    }, {"_id": 0})
    now = datetime.now(timezone.utc).isoformat()
    if inv:
        new_qty = max(0, inv['quantity'] + data.quantity)
        await db.inventory.update_one({"id": inv['id']}, {"$set": {"quantity": new_qty, "updated_at": now}})
    else:
        if data.quantity < 0:
            raise HTTPException(status_code=400, detail="Nao ha estoque para dar baixa")
        await db.inventory.insert_one({
            "id": gen_id(), "tenant_id": target_tid, "product_id": data.product_id,
            "warehouse_id": data.warehouse_id, "quantity": max(0, data.quantity), "updated_at": now
        })
    changes = {"quantidade": data.quantity}
    if data.sector:
        changes['setor'] = data.sector
    if data.reason:
        changes['motivo'] = data.reason
    await audit.log(user['sub'], user['email'], "AJUSTAR", "estoque",
                    f"{data.product_id}:{data.warehouse_id}", target_tid, changes,
                    warehouse_id=data.warehouse_id)
    return {"message": "Estoque ajustado"}
