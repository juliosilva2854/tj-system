"""Gestao de modulos habilitados por Warehouse PAI.
Master/Admin do tenant podem ler e alterar com seguranca validada no backend.
"""
from fastapi import APIRouter, Depends, HTTPException
from database import db, audit
from deps import get_current_user
from models import ModuleConfigUpdate, ALL_MODULES
from permissions import verify_tenant_access, get_user_enabled_modules

router = APIRouter(tags=["modules"])

@router.get("/modules")
async def list_modules():
    return {"modules": list(ALL_MODULES)}

@router.get("/modules/me")
async def my_modules(user: dict = Depends(get_current_user)):
    mods = await get_user_enabled_modules(user)
    return {"enabled_modules": mods}

@router.get("/warehouses/{wid}/modules")
async def get_warehouse_modules(wid: str, user: dict = Depends(get_current_user)):
    # Seguranca rigorosa: apenas master, is_master_access ou admin do tenant
    is_master = user.get('role') == 'master' or user.get('is_master_access', False)
    is_admin = user.get('role', '').lower() in ['admin', 'administrador']
    
    wh = await db.warehouses.find_one({"id": wid}, {"_id": 0})
    if not wh:
        raise HTTPException(status_code=404, detail="Deposito nao encontrado")
        
    if not is_master:
        if not is_admin:
            raise HTTPException(status_code=403, detail="Acesso negado")
        await verify_tenant_access(user, wh['tenant_id'])
        
    return {"warehouse_id": wid, "type": wh.get('type'), "enabled_modules": wh.get('enabled_modules', [])}

@router.put("/warehouses/{wid}/modules")
async def update_warehouse_modules(
    wid: str, data: ModuleConfigUpdate,
    user: dict = Depends(get_current_user)
):
    is_master = user.get('role') == 'master' or user.get('is_master_access', False)
    is_admin = user.get('role', '').lower() in ['admin', 'administrador']
    
    if not is_master and not is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar modulos")

    wh = await db.warehouses.find_one({"id": wid}, {"_id": 0})
    if not wh:
        raise HTTPException(status_code=404, detail="Deposito nao encontrado")
        
    if not is_master:
        await verify_tenant_access(user, wh['tenant_id'])
        
    if wh.get('type') != 'pai':
        raise HTTPException(status_code=400, detail="Modulos sao configurados apenas em depositos PAI")
        
    await db.warehouses.update_one({"id": wid}, {"$set": {"enabled_modules": data.enabled_modules}})
    await audit.log(user['sub'], user['email'], "CONFIGURAR_MODULOS", "deposito", wid, wh['tenant_id'],
                    {"modulos": data.enabled_modules}, warehouse_id=wid, store_id=wh.get('store_id', ''))
    return {"message": "Modulos atualizados", "enabled_modules": data.enabled_modules}