# 🔧 Code Quality Fixes Applied

Este documento lista todas as correções aplicadas baseadas no code review.

---

## ✅ CORREÇÕES APLICADAS

### 1. Security - Token Storage (PARCIAL)

**Status:** Backend atualizado, frontend requer mudança manual

**O que foi feito:**
- ✅ Backend: Adicionado suporte a httpOnly cookies em `/api/auth/login`
- ✅ Backend: Adicionado endpoint `/api/auth/logout` para limpar cookies
- ✅ Cookies configurados com `httponly=True`, `secure=True`, `samesite="lax"`

**O que falta fazer no frontend:**
```javascript
// Remover de todos os componentes:
localStorage.setItem('token', ...)
localStorage.setItem('refresh_token', ...)
localStorage.setItem('user', ...)

// Substituir por:
// Os tokens já vêm nos cookies automaticamente
// Apenas salvar dados não-sensíveis:
sessionStorage.setItem('user', JSON.stringify(user))
```

**Arquivos que precisam ser atualizados:**
- `src/components/LoginPage.js:40-41` - Remover localStorage para tokens
- `src/components/DashboardLayout.js:35,39` - Usar sessionStorage
- `src/components/AlertsPage.js:40,44,49` - Usar sessionStorage
- `src/api.js:6` - Atualizar interceptor para ler de cookies

---

### 2. Error Handling - Empty Catch Blocks

**Status:** Parcialmente corrigido

**Correções aplicadas:**
- ✅ `DashboardLayout.js` - fetchUnread: adicionado log de erro

**Ainda precisam ser corrigidos:**
- `DashboardLayout.js:40` - catch do authAPI.me()
- `AlertsPage.js:29` - catch vazio
- `App.js:28` - catch do seedDB

**Padrão a seguir:**
```javascript
catch (error) {
  console.error('Context about what failed:', error);
  // Se é erro crítico:
  toast.error('User-facing message');
  // Se precisa rastrear:
  // trackError(error);
}
```

---

## ⚠️ CORREÇÕES RECOMENDADAS (Não Aplicadas)

### 3. React Hooks - Missing Dependencies (30 instances)

**Prioridade:** Alta
**Esforço:** Médio

**Principais arquivos:**
```javascript
// src/hooks/use-toast.js:138
useEffect(() => {
  // ...
}, []); // Missing: index, listeners, setState

// src/components/UsersPage.js:72
useEffect(() => {
  if (!isMaster) return;
  // ...
}, [formData.tenant_id, isMaster]); // Missing: warehousesAPI, r, setTenantWarehouses

// Solução:
useEffect(() => {
  if (!isMaster) return;
  // ...
}, [formData.tenant_id, isMaster, warehousesAPI, setTenantWarehouses]);
// ou use useCallback para funções estáveis
```

**Lista completa:** Ver relatório original para todos os 30 casos

---

### 4. Python - Identity Comparison (23 instances)

**Prioridade:** Alta
**Esforço:** Baixo (buscar e substituir)

**Padrão incorreto:**
```python
# Errado
if status is "active":
if value is 0:
if type is "PAI":

# Correto
if status == "active":
if value == 0:
if type == "PAI":
```

**Arquivos principais:**
- `nfe_parser.py` - 6 instâncias
- `routers/dashboard.py` - 4 instâncias
- `routers/inventory.py` - 3 instâncias
- Todos os routers têm 1-2 instâncias

**Comando para encontrar:**
```bash
grep -rn "is '" backend/
grep -rn 'is "' backend/
```

---

### 5. React - Array Index as Key (11 instances)

**Prioridade:** Média
**Esforço:** Baixo

**Arquivos afetados:**
```javascript
// src/components/ReportsPage.js:84,112,146
{items.map((item, i) => <div key={i}>...  // Errado

// Correto:
{items.map((item) => <div key={item.id}>...  // Use ID único

// Se não tem ID, adicione um:
const itemsWithIds = items.map((item, i) => ({ ...item, _key: `item-${i}-${item.name}` }));
{itemsWithIds.map((item) => <div key={item._key}>...
```

**Lista completa:**
- `ReportsPage.js` - 3 instâncias (linhas 84, 112, 146)
- `RequisitionsPage.js` - 2 instâncias (117, 171)
- `InvoicesPage.js` - 2 instâncias (126, 154)
- `TransfersPage.js` - 1 instância (106)
- `NormalDashboardHome.js` - 1 instância (87)
- `GuidePage.js` - 2 instâncias (122, 131)

---

### 6. Python - High Complexity Functions

**Prioridade:** Média
**Esforço:** Alto (refatoração)

**Top offenders:**

#### `routers/auth.py:87` - `register()` (Complexity: 26, 72 lines)
**Recomendação:** Extrair validações

```python
# Antes (tudo em register())
async def register(data: UserCreate, user: dict = Depends(...)):
    # 72 linhas de validações e lógica
    ...

# Depois (separado)
def validate_user_creation(data: UserCreate, user: dict):
    """Valida dados de criação de usuário"""
    if user['role'] == 'admin' and data.role == 'master':
        raise HTTPException(...)
    # mais validações
    return validated_data

async def create_user_document(data: UserCreate):
    """Cria documento do usuário"""
    return {
        "id": gen_id(),
        "email": data.email,
        # ...
    }

async def register(data: UserCreate, user: dict = Depends(...)):
    validated = validate_user_creation(data, user)
    doc = await create_user_document(validated)
    await db.users.insert_one(doc)
    return doc
```

#### `routers/transfers.py:17` - `create_transfer()` (Complexity: 18, 72 lines)
**Recomendação:** Extrair validações de warehouse e inventory

```python
async def validate_warehouses(origem_id, destino_id, tenant_id):
    """Valida warehouses de origem e destino"""
    # Validações de warehouse
    ...

async def validate_inventory(items, origem_id):
    """Valida se há estoque suficiente"""
    # Validações de estoque
    ...

async def create_transfer(data: TransferCreate, user: dict = Depends(...)):
    await validate_warehouses(data.origem_id, data.destino_id, user['tenant_id'])
    await validate_inventory(data.items, data.origem_id)
    # Criar transferência
    ...
```

#### `routers/seed.py:19` - `seed()` (205 lines, 17 locals)
**Recomendação:** Separar por entidade

```python
async def seed_tenants(now: str):
    """Cria tenants de teste"""
    tenants = [...]
    await db.tenants.insert_many(tenants)
    return tenant_ids

async def seed_users(now: str, tenant_ids: dict):
    """Cria usuários de teste"""
    users = [...]
    await db.users.insert_many(users)

async def seed():
    now = datetime.now(timezone.utc).isoformat()
    tenant_ids = await seed_tenants(now)
    await seed_users(now, tenant_ids)
    await seed_products(now, tenant_ids)
    # ...
```

#### `nfe_parser.py:7` - `parse_nfe_xml()` (Complexity: 15, 79 lines)
**Recomendação:** Criar classes para cada seção

```python
class NFEParser:
    def __init__(self, xml_content: str):
        self.root = ET.fromstring(xml_content)
        
    def parse_header(self):
        """Extrai dados do cabeçalho"""
        ...
        
    def parse_items(self):
        """Extrai itens da NFE"""
        ...
        
    def parse_totals(self):
        """Extrai totais"""
        ...
        
    def parse(self):
        return {
            **self.parse_header(),
            "items": self.parse_items(),
            **self.parse_totals()
        }

def parse_nfe_xml(xml_content: str):
    parser = NFEParser(xml_content)
    return parser.parse()
```

---

### 7. React - Oversized Components

**Prioridade:** Baixa
**Esforço:** Alto (refatoração)

**Arquivos:**
- `UsersPage.js` (405 lines) → Extrair UserForm, UserModal
- `ProfilePage.js` (400 lines) → Extrair PhotoSection, InfoSection, SecuritySection
- `SalesPage.js` (347 lines) → Extrair SaleForm, SalesList

**Exemplo de refatoração:**

```javascript
// Antes (tudo em UsersPage.js)
export const UsersPage = () => {
  // 405 linhas...
  return (
    <div>
      {/* Formulário de 150 linhas */}
      {/* Tabela de 100 linhas */}
    </div>
  );
};

// Depois (separado)
// UserForm.js
export const UserForm = ({ onSubmit, editingId }) => {
  // Apenas lógica do formulário
};

// UsersTable.js
export const UsersTable = ({ users, onEdit, onDelete }) => {
  // Apenas lógica da tabela
};

// UsersPage.js
export const UsersPage = () => {
  return (
    <div>
      <UserForm onSubmit={handleSubmit} />
      <UsersTable users={users} onEdit={handleEdit} />
    </div>
  );
};
```

---

### 8. Python - Type Hints

**Prioridade:** Baixa
**Esforço:** Médio

**Arquivos prioritários:**

```python
# server.py - 0% coverage
# Adicionar:
from fastapi import FastAPI
from typing import Dict, Any

app: FastAPI = FastAPI()

@app.get("/")
async def root() -> Dict[str, str]:
    return {"status": "ok"}

# models.py - 21.4% coverage
# Adicionar hints em funções auxiliares:
def sanitize_str(value: str, max_len: int) -> str:
    """Remove caracteres perigosos e limita tamanho"""
    ...

def validate_cpf(cpf: str) -> bool:
    """Valida CPF brasileiro"""
    ...

# nfe_parser.py - 16.7% coverage
from typing import Dict, List, Any
from xml.etree import ElementTree as ET

def parse_nfe_xml(xml_content: str) -> Dict[str, Any]:
    """Parse NFe XML e retorna dicionário estruturado"""
    ...

def extract_items(root: ET.Element) -> List[Dict[str, Any]]:
    """Extrai itens da NFe"""
    ...
```

---

## 📊 RESUMO DE PRIORIDADES

| Categoria | Prioridade | Esforço | Status |
|-----------|-----------|---------|--------|
| Security (Tokens) | 🔴 Crítico | Médio | ✅ Backend / ⚠️ Frontend |
| Error Handling | 🔴 Crítico | Baixo | ⚠️ Parcial |
| Missing Dependencies | 🟡 Alto | Médio | ⚠️ Pendente |
| Identity Comparison | 🟡 Alto | Baixo | ⚠️ Pendente |
| Array Index Keys | 🟢 Médio | Baixo | ⚠️ Pendente |
| Complex Functions | 🟢 Médio | Alto | ⚠️ Pendente |
| Oversized Components | 🔵 Baixo | Alto | ⚠️ Pendente |
| Type Hints | 🔵 Baixo | Médio | ⚠️ Pendente |

---

## 🎯 ROADMAP DE CORREÇÕES

### Sprint 1 (Crítico - 1-2 dias)
- [ ] Completar migração de tokens para cookies (frontend)
- [ ] Corrigir todos empty catch blocks
- [ ] Corrigir identity comparisons (buscar/substituir)

### Sprint 2 (Importante - 3-5 dias)
- [ ] Corrigir missing dependencies nos hooks
- [ ] Substituir array index como key
- [ ] Adicionar type hints em models.py e nfe_parser.py

### Sprint 3 (Melhoria - 1-2 semanas)
- [ ] Refatorar funções complexas (auth.register, transfers.create)
- [ ] Separar componentes grandes (UsersPage, ProfilePage)
- [ ] Refatorar seed.py

---

## 🔍 FERRAMENTAS RECOMENDADAS

```bash
# ESLint para React
npm install --save-dev eslint-plugin-react-hooks

# Pylint para Python
pip install pylint

# MyPy para type checking
pip install mypy

# Ruff para linting rápido
pip install ruff
```

---

**Última atualização:** 2026-01-XX
**Responsável:** Dev Team
