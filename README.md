# 🏢 Gestão TJ - Sistema SaaS Multi-Tenant de Gestão Empresarial

Sistema completo de gestão empresarial com controle de estoque, transferências entre lojas, gestão de usuários hierárquica, relatórios avançados e muito mais.

## 📋 Índice

- [Características](#características)
- [Tecnologias](#tecnologias)
- [Pré-requisitos](#pré-requisitos)
- [Instalação Local](#instalação-local)
- [Executar com Docker](#executar-com-docker)
- [Deploy em Produção](#-deploy-em-produção)
- [Configuração](#configuração)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [API Documentation](#api-documentation)
- [Credenciais de Teste](#credenciais-de-teste)

---

## ✨ Características

### 🔐 Autenticação e Segurança
- ✅ **Login Dual**: Username para usuários normais, Email para Master
- ✅ **Recuperação de Senha**: Sistema completo com envio de email
- ✅ **JWT Authentication**: Access + Refresh tokens
- ✅ **Permissões Hierárquicas**: Master > Admin > Gerente Geral > Gerente > Funcionário
- ✅ **Upload de Foto de Perfil**: Validação, compressão e redimensionamento automático

### 🏪 Multi-Tenant SaaS
- ✅ **Múltiplos Estabelecimentos**: Gestão completa de tenants
- ✅ **Lojas/Unidades**: Cada estabelecimento pode ter várias lojas
- ✅ **Depósitos PAI/FILHO**: Hierarquia de estoques
- ✅ **Transferências entre Lojas**: Movimentação PAI → PAI
- ✅ **Módulos Configuráveis**: Ative/desative funcionalidades por depósito

### 📊 Gestão Completa
- ✅ **Controle de Estoque**: Por depósito e setor
- ✅ **Requisições**: FILHO solicita para PAI
- ✅ **Notas Fiscais**: Upload PDF/XML + OCR/IA para processamento
- ✅ **Fornecedores**: CRUD completo
- ✅ **Relatórios**: DRE, Curva ABC, Giro de Estoque (PDF/Excel)
- ✅ **Auditoria**: Log completo de todas as ações
- ✅ **Alertas**: Sistema de notificações configurável

### 💼 Gestão de Usuários
- ✅ **Perfil Completo**: Nome, email, username, CPF, telefone, foto
- ✅ **Hierarquia**: Gerentes gerenciam subordinados
- ✅ **Permissões Customizadas**: Controle granular por módulo

---

## 🛠 Tecnologias

### Backend
- **Python 3.11+**
- **FastAPI** - Framework web moderno e rápido
- **MongoDB** - Banco de dados NoSQL
- **Motor** - Driver assíncrono do MongoDB
- **Pydantic** - Validação de dados
- **JWT** - Autenticação
- **Pillow** - Processamento de imagens
- **ReportLab** - Geração de PDFs
- **Gmail SMTP** - Envio de emails

### Frontend
- **React 18**
- **React Router** - Navegação
- **Axios** - Requisições HTTP
- **Tailwind CSS** - Estilização
- **Shadcn/ui** - Componentes UI
- **Lucide React** - Ícones
- **Sonner** - Notificações toast

---

## 📦 Pré-requisitos

### Para Desenvolvimento Local (sem Docker):
- Node.js 18+ e Yarn
- Python 3.11+
- MongoDB 7+
- Git

### Para Docker:
- Docker 20.10+
- Docker Compose 2.0+

---

## 🚀 Instalação Local

### 1. Clone o Repositório
```bash
git clone https://github.com/juliosilva2854/tj-system.git
cd tj-system
```

### 2. Configure MongoDB
```bash
# Instale MongoDB (Ubuntu/Debian)
sudo apt-get install mongodb-org

# Inicie o serviço
sudo systemctl start mongod
sudo systemctl enable mongod
```

### 3. Configure o Backend

```bash
cd backend

# Crie ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
nano .env
```

**Arquivo `.env` do Backend:**
```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=gestaotj

# JWT
JWT_SECRET=seu-secret-super-seguro-aqui-mude-em-producao

# Email - Gmail SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app-aqui

# Frontend URL (para links de recuperação de senha)
FRONTEND_URL=http://localhost:3000

# Seed protection (opcional)
SEED_SECRET=seu-seed-secret-opcional
```

**Como obter senha de app do Gmail:**
1. Vá para https://myaccount.google.com/apppasswords
2. Crie uma senha de app com nome "Gestao TJ"
3. Copie a senha de 16 caracteres
4. Cole em `SMTP_PASSWORD`

```bash
# Execute o backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Configure o Frontend

```bash
cd ../frontend

# Instale dependências
yarn install

# Configure variáveis de ambiente
cp .env.example .env
nano .env
```

**Arquivo `.env` do Frontend:**
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

```bash
# Execute o frontend
yarn start
```

### 5. Inicialize o Banco de Dados

```bash
# O seed será executado automaticamente ao abrir o frontend
# Ou execute manualmente:
curl -X POST http://localhost:8001/api/seed
```

### 6. Acesse o Sistema

**Frontend:** http://localhost:3000

**Credenciais de teste:**
- **Usuário:** `admin.tj`
- **Senha:** `Admin@2026`

---

## 🐳 Executar com Docker

### 1. Clone e Configure

```bash
git clone https://github.com/juliosilva2854/tj-system.git
cd tj-system
```

### 2. Configure Variáveis de Ambiente

Crie um arquivo `.env` na raiz:

```env
# JWT
JWT_SECRET=seu-secret-super-seguro-mude-em-producao

# CORS (para produção, especifique domínios)
CORS_ORIGINS=*

# Backend URL (ajuste para produção)
REACT_APP_BACKEND_URL=http://localhost:8001

# Email (opcional, mas recomendado)
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app

# Seed Secret (opcional)
SEED_SECRET=seu-seed-secret
```

### 3. Build e Execute

```bash
# Development (com hot-reload)
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up --build -d
```

### 4. Inicialize o Banco

```bash
# Aguarde ~30 segundos para os serviços iniciarem
curl -X POST http://localhost:8001/api/seed
```

### 5. Acesse

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

---

## 🚀 Deploy em Produção

### Stack Recomendado: Railway + MongoDB Atlas + Cloudflare

**Arquitetura:**
```
Frontend (React)  →  Cloudflare Pages  →  tj.sconnecta.com.br
Backend (FastAPI) →  Railway.app        →  api.sconnecta.com.br
Database (Mongo)  →  MongoDB Atlas      →  privado
```

**Custo:** R$ 0,00/mês (tier gratuito) até ~1000 usuários

### 📖 Documentação de Deploy

Este repositório inclui documentação completa para deploy em produção:

#### 🎯 Guias de Deploy

1. **[DEPLOY_RAILWAY_COMPLETO.md](DEPLOY_RAILWAY_COMPLETO.md)** ⭐
   - Guia passo a passo completo
   - Railway + MongoDB Atlas + Cloudflare Pages
   - Inclui troubleshooting e monitoramento
   - **RECOMENDADO: Comece por aqui!**

2. **[DEPLOY_QUICK_REFERENCE.md](DEPLOY_QUICK_REFERENCE.md)**
   - Referência rápida de comandos
   - Variáveis de ambiente prontas
   - Troubleshooting rápido

3. **[DEPLOY_CHECKLIST_FINAL.md](DEPLOY_CHECKLIST_FINAL.md)**
   - Checklist completo para print/preenchimento
   - Validação passo a passo
   - Pós-deploy e monitoramento

4. **[CLOUDFLARE_SETUP.md](CLOUDFLARE_SETUP.md)**
   - Guia detalhado do Cloudflare Pages
   - Configuração de DNS e SSL
   - Custom domains

5. **[DEPLOY_PRODUCAO_SCONNECTA.md](DEPLOY_PRODUCAO_SCONNECTA.md)**
   - Configurações específicas para sconnecta.com.br
   - Cookies cross-domain
   - CORS e segurança

### ⚡ Quick Start - Deploy em 30 minutos

#### 1. Gere os Secrets
```bash
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('SEED_SECRET=' + secrets.token_urlsafe(16))"
```

#### 2. MongoDB Atlas (5 min)
- Crie conta gratuita: https://www.mongodb.com/cloud/atlas/register
- Crie cluster M0 (grátis)
- Network Access: `0.0.0.0/0`
- Connection string pronta

#### 3. Railway - Backend (10 min)
- Login: https://railway.app (via GitHub)
- New Project → Deploy from GitHub repo
- Configure variáveis de ambiente (ver `.env.production.example`)
- Deploy automático

#### 4. Cloudflare Pages - Frontend (10 min)
- Login: https://dash.cloudflare.com
- Workers & Pages → Create → Connect to Git
- Build: `cd frontend && yarn install && yarn build`
- Output: `frontend/build`
- Env var: `REACT_APP_BACKEND_URL=https://api.sconnecta.com.br`

#### 5. Cloudflare DNS (5 min)
```
tj              CNAME  →  gestao-tj.pages.dev           (Proxied)
administrator   CNAME  →  gestao-tj.pages.dev           (Proxied)
api             CNAME  →  sua-url.up.railway.app        (Proxied)
```

### 📁 Arquivos de Configuração de Produção

Este repositório inclui arquivos prontos para deploy:

```bash
/app/
├── railway.json                          # Configuração Railway (auto-detect)
├── .railwayignore                        # Arquivos ignorados no build
├── backend/
│   ├── Dockerfile                        # Container do backend
│   ├── .env.production.example           # Template de variáveis (Railway)
│   └── requirements.txt                  # Dependências Python
├── frontend/
│   ├── Dockerfile                        # Container do frontend
│   ├── .env.production.example           # Template de variáveis (Cloudflare)
│   ├── nginx.frontend.conf               # Nginx config para SPA
│   └── package.json                      # Dependências Node
└── docker-compose.prod.yml               # Docker Compose produção
```

**Importante:** Nunca commite arquivos `.env` com credenciais reais! Use os `.example` como template.

### 🔒 Segurança em Produção

- ✅ JWT_SECRET aleatório de 32+ bytes
- ✅ CORS configurado com domínios específicos (não use `*`)
- ✅ Cookies HttpOnly + SameSite=None + Secure para cross-domain
- ✅ MongoDB com autenticação e Network Access restrito
- ✅ SEED_SECRET para proteger endpoint `/api/seed`
- ✅ SSL/TLS Full (strict) no Cloudflare
- ✅ Senhas de app do Gmail (não senha principal)

### 📊 URLs Finais em Produção

Após deploy completo, seu sistema estará acessível em:

- 🌐 **Portal Principal:** https://tj.sconnecta.com.br
- 👨‍💼 **Portal Master:** https://administrator.sconnecta.com.br
- 🔌 **API Backend:** https://api.sconnecta.com.br
- 📄 **API Docs:** https://api.sconnecta.com.br/docs

2. **Configure SSL/TLS:**
   - SSL/TLS > Overview > Full (strict)
   - Edge Certificates > Always Use HTTPS: ON

3. **Page Rules (Opcional):**
   - `administrator.sconnecta.com.br/*` → Cache Level: Bypass
   - `tj.sconnecta.com.br/*` → Cache Level: Bypass

---

## ⚙️ Configuração

### Variáveis de Ambiente Completas

#### Backend (`backend/.env`)
```env
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=gestaotj

# Security
JWT_SECRET=change-this-to-a-random-secret-in-production
SEED_SECRET=optional-seed-protection-secret

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# App
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Optional: AI Integration
GEMINI_API_KEY=your-gemini-key-for-ocr
```

#### Frontend (`frontend/.env`)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## 📁 Estrutura do Projeto

```
tj-system/
├── backend/                    # FastAPI Backend
│   ├── routers/               # Endpoints organizados por módulo
│   │   ├── auth.py           # Autenticação e perfil
│   │   ├── users.py          # Gestão de usuários
│   │   ├── tenants.py        # Estabelecimentos
│   │   ├── stores.py         # Lojas/Unidades
│   │   ├── warehouses.py     # Depósitos
│   │   ├── products.py       # Produtos
│   │   ├── inventory.py      # Estoque
│   │   ├── requisitions.py   # Requisições
│   │   ├── transfers.py      # Transferências
│   │   ├── suppliers.py      # Fornecedores
│   │   ├── invoices.py       # Notas Fiscais
│   │   ├── reports.py        # Relatórios
│   │   ├── audit.py          # Auditoria
│   │   ├── notifications.py  # Alertas
│   │   ├── modules.py        # Módulos
│   │   ├── uploads.py        # Upload de arquivos
│   │   └── seed.py           # Inicialização do BD
│   ├── models.py             # Modelos Pydantic
│   ├── database.py           # Conexão MongoDB
│   ├── auth.py               # Funções de autenticação
│   ├── permissions.py        # Sistema de permissões
│   ├── email_service.py      # Envio de emails
│   ├── nfe_parser.py         # Parser de NFe
│   ├── report_export.py      # Geração de relatórios
│   ├── audit.py              # Logger de auditoria
│   ├── server.py             # Entry point
│   ├── requirements.txt      # Dependências Python
│   ├── Dockerfile            # Docker para produção
│   └── .env.example          # Exemplo de configuração
│
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── components/       # Componentes React
│   │   │   ├── LoginPage.js
│   │   │   ├── ForgotPasswordPage.js
│   │   │   ├── ResetPasswordPage.js
│   │   │   ├── ProfilePage.js
│   │   │   ├── DashboardLayout.js
│   │   │   ├── DashboardHome.js
│   │   │   ├── ProductsPage.js
│   │   │   ├── InventoryPage.js
│   │   │   ├── UsersPage.js
│   │   │   └── ... (outros componentes)
│   │   ├── components/ui/    # Componentes UI base
│   │   ├── api.js            # Cliente Axios
│   │   └── App.js            # App principal
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml         # Docker Compose dev
├── docker-compose.prod.yml    # Docker Compose prod
├── README.md                  # Este arquivo
├── INSTALL.md                 # Guia de instalação detalhado
├── DEPLOY.md                  # Guia de deploy
└── .gitignore

```

---

## 📚 API Documentation

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/auth/login` | Login (username ou email) |
| POST | `/api/auth/register` | Criar usuário |
| POST | `/api/auth/refresh` | Renovar token |
| GET | `/api/auth/me` | Dados do usuário atual |
| POST | `/api/auth/forgot-password` | Solicitar recuperação de senha |
| POST | `/api/auth/reset-password` | Resetar senha com token |
| GET | `/api/auth/profile` | Perfil completo |
| PUT | `/api/auth/profile` | Atualizar perfil |
| PUT | `/api/auth/change-password` | Mudar senha |
| POST | `/api/auth/profile/picture` | Upload foto |
| DELETE | `/api/auth/profile/picture` | Remover foto |

### Gestão

| Módulo | Endpoints |
|--------|-----------|
| **Tenants** | GET, POST, PATCH, DELETE `/api/tenants` |
| **Stores** | GET, POST, PATCH, DELETE `/api/stores` |
| **Warehouses** | GET, POST, PATCH, DELETE `/api/warehouses` |
| **Products** | GET, POST, PATCH, DELETE `/api/products` |
| **Inventory** | GET `/api/inventory`, POST `/api/inventory/adjust` |
| **Requisitions** | GET, POST, PATCH `/api/requisitions` |
| **Transfers** | GET, POST `/api/transfers` |
| **Suppliers** | GET, POST, PATCH, DELETE `/api/suppliers` |
| **Invoices** | GET, POST, PATCH, DELETE `/api/invoices` |
| **Reports** | GET `/api/reports/{type}` |
| **Audit** | GET `/api/audit` |
| **Users** | GET, POST, PATCH `/api/users` |

**Documentação Interativa:** http://localhost:8001/docs

---

## 🔑 Credenciais de Teste

### Master (Login via EMAIL)
- **Email:** `master@sconnecta.com.br`
- **Senha:** `Master@2026`
- **Acesso:** Via `administrator.sconnecta.com.br`

### Tenant: Unidade TJ
- **Admin:** `admin.tj` / `Admin@2026`
- **Logística:** `logistica.tj` / `Logistica@2026`
- **Operacional:** `operacional.tj` / `Operacional@2026`

### Tenant: Arcos Dourados
- **Admin:** `admin.arcos` / `Admin@2026`
- **Gerente Geral:** `geral.arcos` / `GerenteGeral@2026`
- **Gerente Log A:** `logistica.restA` / `GerenteLog@2026`
- **Gerente Op A:** `operacional.restA` / `GerenteOp@2026`

---

## 🧪 Testes

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
yarn test
```

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto é propriedade privada.

---

## 👥 Suporte

- **Email:** suportegestaotj@gmail.com
- **Issues:** https://github.com/juliosilva2854/tj-system/issues

---

## 🎯 Roadmap

- [ ] Dashboard Master com visualização global
- [ ] Sistema de permissões hierárquicas completo
- [ ] Relatórios adicionais (Margem, Rentabilidade)
- [ ] Integração com ERPs externos
- [ ] App Mobile (React Native)
- [ ] Modo offline (PWA)
- [ ] Backup automático
- [ ] Multi-idioma

---

**Desenvolvido com ❤️ para gestão empresarial eficiente**
