from fastapi import APIRouter, Depends
from database import db
from deps import get_current_user
from permissions import get_user_warehouse_scope, ADMIN_ROLES

router = APIRouter(tags=["dashboard"])

@router.get("/dashboard/stats")
async def dashboard_stats(user: dict = Depends(get_current_user)):
    q = {}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    scope = None
    if user['role'] not in ADMIN_ROLES:
        scope = await get_user_warehouse_scope(user)
    prods = await db.products.count_documents({**q, "active": True})
    suppliers = await db.suppliers.count_documents({**q, "active": True})
    if scope is not None:
        whs = await db.warehouses.count_documents({**q, "active": True, "id": {"$in": list(scope) or ["__none__"]}})
    else:
        whs = await db.warehouses.count_documents({**q, "active": True})
    pending = await db.invoices.count_documents({**q, "status": "pending"})
    if scope is not None:
        pending_reqs = await db.requisitions.count_documents({
            **q, "status": "pending",
            "$or": [
                {"from_warehouse_id": {"$in": list(scope) or ["__none__"]}},
                {"to_warehouse_id": {"$in": list(scope) or ["__none__"]}},
            ]
        })
    else:
        pending_reqs = await db.requisitions.count_documents({**q, "status": "pending"})
    stores = await db.stores.count_documents({**q, "active": True}) if user['role'] in ADMIN_ROLES else 0
    inv_q = dict(q)
    if scope is not None:
        inv_q['warehouse_id'] = {"$in": list(scope) or ["__none__"]}
    inv = await db.inventory.find(inv_q, {"_id": 0}).to_list(5000)
    pids = list({it['product_id'] for it in inv})
    pdocs = {p['id']: p for p in await db.products.find({"id": {"$in": pids}}, {"_id": 0}).to_list(5000)}
    low = 0
    for it in inv:
        p = pdocs.get(it['product_id'])
        if p and p.get('min_stock', 0) > 0 and it['quantity'] <= p['min_stock']:
            low += 1
    return {
        "total_products": prods, "total_suppliers": suppliers, "total_warehouses": whs,
        "total_stores": stores,
        "pending_invoices": pending, "pending_requisitions": pending_reqs,
        "low_stock_alerts": low
    }

@router.get("/dashboard/alerts")
async def dashboard_alerts(user: dict = Depends(get_current_user)):
    q = {}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    if user['role'] not in ADMIN_ROLES:
        scope = await get_user_warehouse_scope(user)
        if scope is not None:
            q['warehouse_id'] = {"$in": list(scope) or ["__none__"]}
    inv = await db.inventory.find(q, {"_id": 0}).to_list(5000)
    pids = list({it['product_id'] for it in inv})
    wids = list({it['warehouse_id'] for it in inv})
    pdocs = {p['id']: p for p in await db.products.find({"id": {"$in": pids}}, {"_id": 0}).to_list(5000)}
    wdocs = {w['id']: w for w in await db.warehouses.find({"id": {"$in": wids}}, {"_id": 0}).to_list(1000)}
    alerts = []
    for it in inv:
        p = pdocs.get(it['product_id']); w = wdocs.get(it['warehouse_id'])
        if p and w and p.get('min_stock', 0) > 0 and it['quantity'] <= p['min_stock']:
            alerts.append({"product_name": p['name'], "warehouse_name": w['name'],
                           "current_quantity": it['quantity'], "min_stock": p['min_stock']})
    return alerts
