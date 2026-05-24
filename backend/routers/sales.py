from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from database import db, audit
from deps import get_current_user
from models import SaleCreate, gen_id

router = APIRouter(tags=["sales"])

@router.post("/sales")
async def create_sale(data: SaleCreate, user: dict = Depends(get_current_user)):
    tid = user.get('tenant_id', '')
    now = datetime.now(timezone.utc).isoformat()
    last = await db.sales.find_one({"tenant_id": tid}, {"_id": 0}, sort=[('created_at', -1)])
    num = 1
    if last and 'sale_number' in last:
        try:
            num = int(last['sale_number'][3:]) + 1
        except ValueError:
            pass
    doc = {
        "id": gen_id(), "tenant_id": tid, "sale_number": f"VND{str(num).zfill(6)}",
        "warehouse_id": data.warehouse_id, "customer_name": data.customer_name or "",
        "items": [i.model_dump() for i in data.items],
        "subtotal": data.subtotal, "discount": data.discount, "total": data.total,
        "payment_method": data.payment_method or "", "status": "completed",
        "created_at": now, "created_by": user['sub']
    }
    await db.sales.insert_one(doc); doc.pop("_id", None)
    for item in data.items:
        inv = await db.inventory.find_one({"product_id": item.product_id, "warehouse_id": data.warehouse_id, "tenant_id": tid}, {"_id": 0})
        if inv:
            new_qty = max(0, inv['quantity'] - item.quantity)
            await db.inventory.update_one({"id": inv['id']}, {"$set": {"quantity": new_qty, "updated_at": now}})
    await audit.log(user['sub'], user['email'], "CRIAR", "venda", doc['id'], tid, warehouse_id=data.warehouse_id)
    return doc

@router.get("/sales")
async def list_sales(user: dict = Depends(get_current_user)):
    q = {}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    return await db.sales.find(q, {"_id": 0}).sort('created_at', -1).to_list(5000)
