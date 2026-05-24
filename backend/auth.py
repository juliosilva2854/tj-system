import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import os
import secrets

JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE = 60  # minutes
REFRESH_TOKEN_EXPIRE = 7  # days

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(
    user_id: str,
    email: str,
    role: str,
    tenant_id: str = None,
    warehouse_id: str = None,
    warehouse_ids: Optional[List[str]] = None,
    store_ids: Optional[List[str]] = None,
) -> str:
    payload = {
        'sub': user_id, 'email': email, 'role': role,
        'tenant_id': tenant_id or '',
        'warehouse_id': warehouse_id or '',
        'warehouse_ids': warehouse_ids or [],
        'store_ids': store_ids or [],
        'type': 'access',
        'exp': datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        'sub': user_id,
        'type': 'refresh',
        'exp': datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None

def token_from_user_doc(doc: dict) -> str:
    return create_access_token(
        doc['id'], doc['email'], doc['role'],
        doc.get('tenant_id', ''),
        doc.get('warehouse_id', ''),
        doc.get('warehouse_ids', []) or [],
        doc.get('store_ids', []) or [],
    )
