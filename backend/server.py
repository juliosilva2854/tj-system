"""Gestao TJ - SaaS Multi-Tenant. Entry point enxuto.
Todos os endpoints vivem em /app/backend/routers/*.
"""
import os, logging
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from database import client
from routers.auth import limiter
from routers import ALL_ROUTERS

app = FastAPI(title="Gestao TJ - SaaS Multi-Tenant", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

api = APIRouter(prefix="/api")
for r in ALL_ROUTERS:
    api.include_router(r)

@api.get("/")
async def root():
    return {"name": "Gestao TJ", "version": "2.0.0", "status": "ok"}

@api.get("/health")
async def health():
    try:
        await client.admin.command('ping')
        return {"status": "healthy", "db": "ok"}
    except Exception as e:
        return {"status": "degraded", "db": "error", "error": str(e)}

app.include_router(api)
_cors_origins = [o.strip() for o in os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.on_event("shutdown")
async def shutdown():
    client.close()
