from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Literal
from datetime import datetime
import uuid
import re

def gen_id() -> str:
    return str(uuid.uuid4())

def sanitize_str(v: str, max_len: int = 500) -> str:
    if not isinstance(v, str):
        return v
    v = v.strip()
    v = re.sub(r'[<>{}]', '', v)
    return v[:max_len]

# Roles canonicas (mantemos legados para compat)
ROLES = Literal[
    "master",
    "admin",
    "gerente_geral",
    "gerente_logistica",
    "gerente_operacional",
    "logistica",
    "operacional",
]

# Modulos do sistema (= menus do frontend)
ALL_MODULES = [
    "dashboard",
    "stores",
    "warehouses",
    "products",
    "inventory",
    "requisitions",
    "transfers",
    "invoices",
    "suppliers",
    "sales",
    "reports",
    "alerts",
    "audit",
    "users",
    "guide",
]

# === TENANT (estabelecimento / empresa, ex: Arcos Dourados) ===
class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=50, pattern=r'^[a-z0-9\-]+$')
    @field_validator('name', 'slug')
    @classmethod
    def sanitize(cls, v):
        return sanitize_str(v, 100)

class Tenant(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=gen_id)
    name: str
    slug: str
    active: bool = True
    created_at: str

# === STORE / UNIDADE / LOJA (ex: Restaurante A, Restaurante B) ===
class StoreCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    code: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=300)
    @field_validator('name', 'code', 'address')
    @classmethod
    def sanitize(cls, v):
        if v:
            return sanitize_str(v, 300)
        return v

class Store(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=gen_id)
    tenant_id: str
    name: str
    code: Optional[str] = None
    address: Optional[str] = None
    active: bool = True
    created_at: str
    created_by: Optional[str] = None

# === USER ===
class UserCreate(BaseModel):
    email: str = Field(..., max_length=200)
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    role: ROLES
    tenant_id: Optional[str] = None
    warehouse_id: Optional[str] = None  # legado / unico
    warehouse_ids: List[str] = []  # multi-warehouse
    store_ids: List[str] = []  # acesso por loja inteira
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Email invalido')
        return v.lower().strip()
    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v):
        return sanitize_str(v, 100)

class UserLogin(BaseModel):
    email: str = Field(..., max_length=200)
    password: str = Field(..., max_length=128)

class UserOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    role: str
    tenant_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    warehouse_ids: List[str] = []
    store_ids: List[str] = []
    active: bool = True
    created_at: str

# === WAREHOUSE ===
class WarehouseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    location: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    type: Literal["pai", "filho"]
    parent_id: Optional[str] = None
    store_id: Optional[str] = None  # vinculo a loja
    sectors: List[str] = []
    enabled_modules: Optional[List[str]] = None  # so para PAI; default = todos
    @field_validator('name', 'location')
    @classmethod
    def sanitize(cls, v):
        return sanitize_str(v, 200)

class Warehouse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=gen_id)
    tenant_id: str
    store_id: Optional[str] = None
    name: str
    location: str
    description: Optional[str] = None
    type: Literal["pai", "filho"]
    parent_id: Optional[str] = None
    sectors: List[str] = []
    enabled_modules: List[str] = []
    active: bool = True
    created_at: str
    created_by: str

class ModuleConfigUpdate(BaseModel):
    enabled_modules: List[str]
    @field_validator('enabled_modules')
    @classmethod
    def validate_modules(cls, v):
        invalid = [m for m in v if m not in ALL_MODULES]
        if invalid:
            raise ValueError(f"Modulos invalidos: {invalid}")
        return v

# === PRODUCT ===
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    sku: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    unit: str = Field(default="UN", max_length=10)
    cost_price: float = Field(default=0, ge=0)
    min_stock: float = Field(default=0, ge=0)
    @field_validator('name', 'sku', 'category')
    @classmethod
    def sanitize(cls, v):
        if v:
            return sanitize_str(v, 200)
        return v

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=gen_id)
    tenant_id: str
    name: str
    sku: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit: str = "UN"
    cost_price: float = 0
    min_stock: float = 0
    available_qty: float = 0
    active: bool = True
    created_at: str
    created_by: str

# === INVENTORY adjust ===
class InventoryAdjust(BaseModel):
    product_id: str
    warehouse_id: str
    quantity: float  # delta (pode ser negativo)
    sector: Optional[str] = Field(None, max_length=100)
    reason: Optional[str] = Field(None, max_length=200)

# === INVOICE ===
class InvoiceItemInput(BaseModel):
    product_name: str = Field(..., max_length=200)
    product_sku: Optional[str] = Field(None, max_length=50)
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    total: float = Field(..., ge=0)
    tax: float = Field(default=0, ge=0)

class InvoiceCreate(BaseModel):
    invoice_number: str = Field(..., max_length=50)
    supplier_name: str = Field(..., max_length=200)
    issue_date: str = Field(..., max_length=10)
    total_value: float = Field(..., ge=0)
    tax_value: float = Field(default=0, ge=0)
    warehouse_id: Optional[str] = None  # PAI destino dos itens
    items: List[InvoiceItemInput] = []
    @field_validator('invoice_number', 'supplier_name')
    @classmethod
    def sanitize(cls, v):
        return sanitize_str(v, 200)

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=gen_id)
    tenant_id: str
    warehouse_id: Optional[str] = None
    invoice_number: str
    supplier_name: str
    issue_date: str
    total_value: float
    tax_value: float = 0
    items: list = []
    status: str = "pending"
    type: str = "entrada"
    created_at: str
    created_by: str

# === REQUISITION (FILHO -> PAI, mesma loja) ===
class RequisitionItemInput(BaseModel):
    product_id: str
    product_name: str = Field(..., max_length=200)
    quantity: float = Field(..., gt=0)

class RequisitionCreate(BaseModel):
    items: List[RequisitionItemInput]
    notes: Optional[str] = Field(None, max_length=500)

class Requisition(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=gen_id)
    tenant_id: str
    from_warehouse_id: str
    to_warehouse_id: str
    items: list
    notes: Optional[str] = None
    status: Literal["pending", "approved", "rejected"] = "pending"
    created_at: str
    created_by: str
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None

# === TRANSFER entre LOJAS (PAI -> PAI, dentro do mesmo tenant) ===
class TransferItemInput(BaseModel):
    product_id: str
    product_name: str = Field(..., max_length=200)
    quantity: float = Field(..., gt=0)

class TransferCreate(BaseModel):
    from_warehouse_id: str  # PAI origem
    to_warehouse_id: str    # PAI destino
    items: List[TransferItemInput]
    notes: Optional[str] = Field(None, max_length=500)

class Transfer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=gen_id)
    tenant_id: str
    from_store_id: Optional[str] = None
    to_store_id: Optional[str] = None
    from_warehouse_id: str
    to_warehouse_id: str
    items: list
    notes: Optional[str] = None
    status: Literal["pending", "completed", "rejected"] = "pending"
    created_at: str
    created_by: str
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None

# === SALE ===
class SaleItemInput(BaseModel):
    product_id: str
    product_name: str = Field(..., max_length=200)
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    total: float = Field(..., ge=0)

class SaleCreate(BaseModel):
    warehouse_id: str
    customer_name: Optional[str] = Field(None, max_length=200)
    items: List[SaleItemInput]
    subtotal: float = Field(..., ge=0)
    discount: float = Field(default=0, ge=0)
    total: float = Field(..., ge=0)
    payment_method: Optional[str] = Field(None, max_length=50)

# === SUPPLIER ===
class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    cnpj: str = Field(..., max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)

# === OCR ===
class OCRRequest(BaseModel):
    image_base64: str
