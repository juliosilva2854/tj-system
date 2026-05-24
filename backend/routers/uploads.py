from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from PIL import Image
import os
import secrets
from pathlib import Path

from database import db
from deps import get_current_user

router = APIRouter(tags=["uploads"])

# Diretório para uploads
UPLOAD_DIR = Path("/app/backend/uploads/profiles")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

@router.post("/auth/profile/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload de foto de perfil com validação e compressão"""
    
    # Valida extensão
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato nao permitido. Use: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Lê arquivo
    contents = await file.read()
    
    # Valida tamanho
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Arquivo muito grande. Tamanho maximo: 2MB"
        )
    
    try:
        # Abre imagem com PIL
        img = Image.open(file.file)
        
        # Converte RGBA para RGB se necessário
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        
        # Redimensiona se muito grande (mantém aspect ratio)
        max_size = (800, 800)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Gera nome único
        filename = f"{user['sub']}_{secrets.token_urlsafe(8)}.jpg"
        filepath = UPLOAD_DIR / filename
        
        # Salva com compressão
        img.save(filepath, "JPEG", quality=85, optimize=True)
        
        # Remove foto antiga se existir
        user_doc = await db.users.find_one({"id": user['sub']}, {"_id": 0})
        old_picture = user_doc.get('profile_picture')
        if old_picture:
            old_path = UPLOAD_DIR / old_picture
            if old_path.exists():
                old_path.unlink()
        
        # Atualiza banco
        await db.users.update_one(
            {"id": user['sub']},
            {"$set": {"profile_picture": filename}}
        )
        
        return {
            "message": "Foto enviada com sucesso",
            "filename": filename,
            "url": f"/uploads/profiles/{filename}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar imagem: {str(e)}")

@router.get("/uploads/profiles/{filename}")
async def get_profile_picture(filename: str):
    """Serve foto de perfil"""
    filepath = UPLOAD_DIR / filename
    
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Imagem nao encontrada")
    
    return FileResponse(filepath, media_type="image/jpeg")

@router.delete("/auth/profile/picture")
async def delete_profile_picture(user: dict = Depends(get_current_user)):
    """Remove foto de perfil"""
    user_doc = await db.users.find_one({"id": user['sub']}, {"_id": 0})
    
    if not user_doc.get('profile_picture'):
        raise HTTPException(status_code=404, detail="Sem foto de perfil")
    
    # Remove arquivo
    filepath = UPLOAD_DIR / user_doc['profile_picture']
    if filepath.exists():
        filepath.unlink()
    
    # Atualiza banco
    await db.users.update_one(
        {"id": user['sub']},
        {"$set": {"profile_picture": None}}
    )
    
    return {"message": "Foto removida com sucesso"}
