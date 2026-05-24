from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from database import db, audit
from deps import require_roles
from models import TenantCreate, gen_id

router = APIRouter(tags=["tenants"])

@router.post("/tenants")
async def create_tenant(data: TenantCreate, user: dict = Depends(require_roles("master"))):
    existing = await db.tenants.find_one({"slug": data.slug}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Slug ja em uso")
    now = datetime.now(timezone.utc).isoformat()
    doc = {"id": gen_id(), "name": data.name, "slug": data.slug, "active": True, "created_at": now}
    await db.tenants.insert_one(doc); doc.pop("_id", None)
    await audit.log(user['sub'], user['email'], "CRIAR", "tenant", doc['id'])
    return doc

@router.get("/tenants")
async def list_tenants(user: dict = Depends(require_roles("master"))):
    return await db.tenants.find({}, {"_id": 0}).to_list(1000)

@router.patch("/tenants/{tid}")
async def update_tenant(tid: str, data: TenantCreate, user: dict = Depends(require_roles("master"))):
    await db.tenants.update_one({"id": tid}, {"$set": {"name": data.name}})
    await audit.log(user['sub'], user['email'], "EDITAR", "tenant", tid)
    return {"message": "Atualizado"}

@router.delete("/tenants/{tid}")
async def delete_tenant(tid: str, user: dict = Depends(require_roles("master"))):
    r = await db.tenants.delete_one({"id": tid})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    await audit.log(user['sub'], user['email'], "EXCLUIR", "tenant", tid)
    return {"message": "Excluido"}
