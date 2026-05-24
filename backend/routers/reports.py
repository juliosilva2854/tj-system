from fastapi import APIRouter, Depends
from fastapi.responses import Response
from datetime import datetime, timezone
from database import db
from deps import require_roles
from permissions import CAN_VIEW_REPORTS
from report_export import generate_financial_pdf, generate_financial_excel

router = APIRouter(tags=["reports"])

async def _financial_data(period: str, user: dict):
    q = {}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    if period == "month":
        start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0).isoformat()
    else:
        start = datetime.now(timezone.utc).replace(month=1, day=1, hour=0, minute=0, second=0).isoformat()
    sales = await db.sales.find({**q, "created_at": {"$gte": start}, "status": "completed"}, {"_id": 0}).to_list(10000)
    revenue = sum(s.get('total', 0) for s in sales)
    cost = 0
    pids = list({i.get('product_id', '') for s in sales for i in s.get('items', [])})
    pdocs = {p['id']: p for p in await db.products.find({"id": {"$in": pids}}, {"_id": 0}).to_list(10000)}
    for s in sales:
        for it in s.get('items', []):
            p = pdocs.get(it.get('product_id'))
            if p:
                cost += p.get('cost_price', 0) * it.get('quantity', 0)
    gp = revenue - cost
    margin = (gp / revenue * 100) if revenue > 0 else 0
    return {"period": period, "revenue": revenue, "cost": cost, "gross_profit": gp,
            "profit_margin": margin, "expenses": 0, "net_profit": gp}

@router.get("/reports/financial")
async def financial_report(period: str, user: dict = Depends(require_roles(*CAN_VIEW_REPORTS))):
    return await _financial_data(period, user)

@router.get("/reports/abc-curve")
async def abc_curve(user: dict = Depends(require_roles(*CAN_VIEW_REPORTS))):
    q = {"status": "completed"}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    sales = await db.sales.find(q, {"_id": 0}).to_list(10000)
    pm = {}
    for s in sales:
        for it in s.get('items', []):
            pid = it.get('product_id', '')
            pm.setdefault(pid, {"product_name": it.get('product_name', ''), "revenue": 0, "quantity": 0})
            pm[pid]['revenue'] += it.get('total', 0)
            pm[pid]['quantity'] += it.get('quantity', 0)
    items = sorted(pm.values(), key=lambda x: x['revenue'], reverse=True)
    total = sum(i['revenue'] for i in items)
    cum = 0
    for i in items:
        cum += i['revenue']
        pct = (cum / total * 100) if total > 0 else 0
        i['percentage'] = round(i['revenue'] / total * 100, 1) if total > 0 else 0
        i['cumulative'] = round(pct, 1)
        i['class'] = 'A' if pct <= 80 else ('B' if pct <= 95 else 'C')
    return {"items": items, "total_revenue": total}

@router.get("/reports/inventory-turnover")
async def inventory_turnover(user: dict = Depends(require_roles(*CAN_VIEW_REPORTS))):
    pq = {"active": True}; sq = {"status": "completed"}; iq = {}
    if user['role'] != 'master':
        pq['tenant_id'] = sq['tenant_id'] = iq['tenant_id'] = user.get('tenant_id', '')
    products = await db.products.find(pq, {"_id": 0}).to_list(5000)
    sales = await db.sales.find(sq, {"_id": 0}).to_list(10000)
    ps = {}
    for s in sales:
        for it in s.get('items', []):
            ps[it.get('product_id', '')] = ps.get(it.get('product_id', ''), 0) + it.get('quantity', 0)
    inv_items = await db.inventory.find(iq, {"_id": 0}).to_list(5000)
    pstock = {}
    for i in inv_items:
        pstock[i['product_id']] = pstock.get(i['product_id'], 0) + i['quantity']
    results = []
    for p in products:
        sold = ps.get(p['id'], 0); stock = pstock.get(p['id'], 0)
        avg = stock if stock > 0 else 1
        turn = round(sold / avg, 2)
        days = round(avg / (sold / 30), 0) if sold > 0 else 999
        results.append({"product_name": p['name'], "sku": p['sku'], "total_sold": sold,
                        "current_stock": stock, "turnover_rate": turn,
                        "days_of_coverage": min(days, 999),
                        "status": 'critico' if days < 7 else 'baixo' if days < 15 else 'normal' if days < 60 else 'excesso'})
    return {"items": sorted(results, key=lambda x: x['turnover_rate'], reverse=True)}

@router.get("/reports/export/pdf")
async def export_pdf(period: str, user: dict = Depends(require_roles(*CAN_VIEW_REPORTS))):
    report = await _financial_data(period, user)
    pdf = generate_financial_pdf(report, "Mes Atual" if period == "month" else "Ano Atual")
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=relatorio_{period}.pdf"})

@router.get("/reports/export/excel")
async def export_excel(period: str, user: dict = Depends(require_roles(*CAN_VIEW_REPORTS))):
    report = await _financial_data(period, user)
    excel = generate_financial_excel(report, "Mes Atual" if period == "month" else "Ano Atual")
    return Response(content=excel,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=relatorio_{period}.xlsx"})
