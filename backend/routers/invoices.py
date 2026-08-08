import os, json, base64 as b64mod
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from datetime import datetime, timezone
from database import db, audit
from deps import get_current_user, require_roles
from models import InvoiceCreate, OCRRequest, gen_id
from permissions import verify_tenant_access, verify_warehouse_access, CAN_MANAGE_INVOICES
from nfe_parser import parse_nfe_xml
from notifications_service import notify_users, tenant_user_ids

router = APIRouter(tags=["invoices"])

_OCR_PROMPT = (
    "Analise esta nota fiscal brasileira. Extraia com PRECISAO:\n"
    "- QUANTIDADE = numero de unidades (NAO confunda com codigo)\n"
    "- VALOR UNITARIO = preco de 1 unidade\n"
    "Retorne SOMENTE JSON:\n"
    '{"invoice_number":"","supplier_name":"","issue_date":"YYYY-MM-DD","total_value":0,"tax_value":0,'
    '"items":[{"product_name":"","product_sku":"","quantity":0,"unit_price":0,"total":0}]}'
)

def _clean_json(txt: str) -> dict:
    txt = txt.strip()
    if txt.startswith('```json'):
        txt = txt[7:]
    if txt.startswith('```'):
        txt = txt[3:]
    if txt.endswith('```'):
        txt = txt[:-3]
    return json.loads(txt.strip())

def _gemini_extract(content: bytes, mime: str) -> dict:
    import google.generativeai as genai
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY nao configurada")
    genai.configure(api_key=api_key)
    
    # CORREÇÃO AQUI: Mudando para o modelo 2.5-flash que tem cota gratuita liberada e estável
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    response = model.generate_content([_OCR_PROMPT, {"mime_type": mime, "data": content}])
    return _clean_json(response.text)

@router.post("/invoices")
async def create_invoice(data: InvoiceCreate, user: dict = Depends(require_roles(*CAN_MANAGE_INVOICES))):
    tid = user.get('tenant_id', '')
    if data.warehouse_id and user['role'] != 'master':
        await verify_warehouse_access(user, data.warehouse_id)
    now = datetime.now(timezone.utc).isoformat()
    body = data.model_dump()
    body['items'] = [dict(i) for i in body.get('items', [])]
    doc = {
        "id": gen_id(), "tenant_id": tid, **body,
        "status": "pending", "type": "entrada", "created_at": now, "created_by": user['sub']
    }
    await db.invoices.insert_one(doc); doc.pop("_id", None)
    await audit.log(user['sub'], user['email'], "CRIAR", "nota_fiscal", doc['id'], tid,
                    warehouse_id=data.warehouse_id or '')
    # Notifica gestores do tenant sobre nota pendente
    managers = await tenant_user_ids(tid, roles={"admin", "gerente_geral", "gerente_logistica", "logistica"})
    await notify_users(
        managers, "invoice_pending",
        "Nota fiscal pendente",
        f"Nota {data.invoice_number} de {data.supplier_name} (R$ {data.total_value:.2f}) esta pendente.",
        ntype="info", meta={"invoice_id": doc['id']}, exclude_user_id=user['sub'],
    )
    return doc

@router.get("/invoices")
async def list_invoices(user: dict = Depends(get_current_user)):
    q = {}
    if user['role'] != 'master':
        q['tenant_id'] = user.get('tenant_id', '')
    return await db.invoices.find(q, {"_id": 0}).to_list(5000)

@router.post("/invoices/{iid}/process-items")
async def process_invoice_items(iid: str, user: dict = Depends(require_roles(*CAN_MANAGE_INVOICES))):
    inv = await db.invoices.find_one({"id": iid}, {"_id": 0})
    if not inv:
        raise HTTPException(status_code=404, detail="Nota nao encontrada")
    if user['role'] != 'master':
        await verify_tenant_access(user, inv['tenant_id'])
    tid = inv['tenant_id']
    created = 0
    for item in inv.get('items', []):
        pname = item.get('product_name', '')
        if not pname:
            continue
        sku = item.get('product_sku', '') or pname[:10].upper().replace(' ', '')
        qty = item.get('quantity', 0)
        existing = await db.products.find_one({"sku": sku, "tenant_id": tid}, {"_id": 0})
        now = datetime.now(timezone.utc).isoformat()
        if existing:
            new_avail = existing.get('available_qty', 0) + qty
            await db.products.update_one({"id": existing['id']}, {"$set": {"available_qty": new_avail}})
        else:
            await db.products.insert_one({
                "id": gen_id(), "tenant_id": tid, "name": pname, "sku": sku,
                "description": "", "category": "", "unit": "UN",
                "cost_price": item.get('unit_price', 0), "min_stock": 0,
                "available_qty": qty, "active": True, "created_at": now,
                "created_by": user['sub']
            })
            created += 1
    await db.invoices.update_one({"id": iid}, {"$set": {"status": "processed"}})
    await audit.log(user['sub'], user['email'], "PROCESSAR", "nota_fiscal", iid, tid,
                    {"produtos_criados": created})
    return {"message": f"Itens enviados para Produtos. {created} novos criados.", "products_created": created}

@router.post("/invoices/ocr")
async def ocr_invoice(data: OCRRequest, user: dict = Depends(require_roles(*CAN_MANAGE_INVOICES))):
    img_bytes = b64mod.b64decode(data.image_base64)
    return _gemini_extract(img_bytes, "image/jpeg")

@router.post("/invoices/upload")
async def upload_invoice(file: UploadFile = File(...), user: dict = Depends(require_roles(*CAN_MANAGE_INVOICES))):
    content = await file.read()
    fname = (file.filename or '').lower()
    if fname.endswith('.xml'):
        return {"source": "xml", "data": parse_nfe_xml(content)}
    if fname.endswith('.pdf') or fname.endswith('.jpg') or fname.endswith('.jpeg') or fname.endswith('.png'):
        mime = "application/pdf" if fname.endswith('.pdf') else "image/jpeg"
        return {"source": "ocr", "data": _gemini_extract(content, mime)}
    raise HTTPException(status_code=400, detail="Use PDF, XML, JPG ou PNG")
