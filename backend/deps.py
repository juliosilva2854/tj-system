"""Dependencias compartilhadas do FastAPI."""
import os
from typing import Optional
from fastapi import Depends, Header, HTTPException, Cookie
from auth import decode_token

async def get_current_user(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
) -> dict:
    """Aceita JWT via Authorization header (Bearer) OU cookie httpOnly access_token.

    Cookie httpOnly e o canal preferido (protege contra XSS); o header fica como
    fallback para clientes que nao usam cookies (curl, mobile, integracoes).
    """
    token: Optional[str] = None
    if authorization and authorization.startswith('Bearer '):
        token = authorization[7:]
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(status_code=401, detail="Nao autenticado")

    payload = decode_token(token)
    if not payload or payload.get('type') != 'access':
        raise HTTPException(status_code=401, detail="Token invalido ou expirado")
    return payload

def require_roles(*roles):
    async def checker(user: dict = Depends(get_current_user)):
        if user['role'] not in roles:
            raise HTTPException(status_code=403, detail="Permissao insuficiente")
        return user
    return checker

def require_any_role(*roles_groups):
    """Aceita varios sets/iteraveis de roles e combina (uniao)."""
    allowed = set()
    for g in roles_groups:
        allowed.update(g)
    async def checker(user: dict = Depends(get_current_user)):
        if user['role'] not in allowed:
            raise HTTPException(status_code=403, detail="Permissao insuficiente")
        return user
    return checker

SEED_SECRET = os.environ.get('SEED_SECRET', '')

def require_seed_secret(x_seed_secret: Optional[str] = Header(None)):
    """Se SEED_SECRET estiver configurada, exige header X-Seed-Secret. Senao, libera (dev)."""
    if not SEED_SECRET:
        return True
    if x_seed_secret != SEED_SECRET:
        raise HTTPException(status_code=403, detail="Seed protegido")
    return True
