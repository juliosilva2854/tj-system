# 📦 Guia de Instalação Completo - Gestão TJ

Este guia cobre **3 métodos de instalação**:
1. ✅ **Docker** (Recomendado - mais rápido)
2. ✅ **Instalação Local** (Para desenvolvimento)
3. ✅ **Deploy em Produção** (Cloudflare, Railway, etc.)

---

## 🐳 Método 1: Instalação com Docker (RECOMENDADO)

### Pré-requisitos
- Docker 20.10+ instalado
- Docker Compose 2.0+ instalado
- Git instalado

### Passo 1: Clone o Repositório
```bash
git clone https://github.com/juliosilva2854/tj-system.git
cd tj-system
```

### Passo 2: Configure Variáveis de Ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env
nano .env  # ou use seu editor preferido
```

**Configurações mínimas necessárias:**
```env
JWT_SECRET=cole-um-secret-aleatorio-aqui
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app-aqui
```

**Como obter senha de app do Gmail:**
1. Vá para: https://myaccount.google.com/apppasswords
2. Clique em "Gerar" e escolha "Outro"
3. Digite "Gestao TJ" como nome
4. Copie a senha de 16 caracteres
5. Cole em `SMTP_PASSWORD` no arquivo `.env`

### Passo 3: Inicie os Containers
```bash
# Build e inicie todos os serviços
docker-compose up --build

# Ou execute em background
docker-compose up --build -d
```

### Passo 4: Inicialize o Banco de Dados
```bash
# Aguarde ~30 segundos para os serviços iniciarem completamente
# Em outro terminal, execute:
curl -X POST http://localhost:8001/api/seed
```

### Passo 5: Acesse o Sistema
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

**Credenciais de teste:**
- **Usuário:** `admin.tj`
- **Senha:** `Admin@2026`

### Comandos Úteis do Docker

```bash
# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs apenas do backend
docker-compose logs -f backend

# Parar todos os serviços
docker-compose down

# Parar e remover volumes (APAGA O BANCO!)
docker-compose down -v

# Rebuild apenas um serviço
docker-compose up --build backend

# Ver status dos containers
docker-compose ps

# Entrar no container do backend
docker-compose exec backend bash

# Entrar no MongoDB
docker-compose exec mongo mongosh gestaotj
```

---

## 💻 Método 2: Instalação Local (Desenvolvimento)

### Pré-requisitos
- Node.js 18+ e Yarn
- Python 3.11+
- MongoDB 7+
- Git

### 📥 Passo 1: Instale as Dependências do Sistema

#### Ubuntu/Debian
```bash
# MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Python e Node.js
sudo apt-get install -y python3.11 python3.11-venv python3-pip
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g yarn

# Inicie MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### macOS
```bash
# Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# MongoDB
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0

# Python e Node
brew install python@3.11 node@20
npm install -g yarn
```

#### Windows
1. **MongoDB:**
   - Baixe: https://www.mongodb.com/try/download/community
   - Instale e inicie como serviço

2. **Python 3.11:**
   - Baixe: https://www.python.org/downloads/
   - Marque "Add to PATH" durante instalação

3. **Node.js 20:**
   - Baixe: https://nodejs.org/
   - Instale npm e depois: `npm install -g yarn`

### 📥 Passo 2: Clone e Configure

```bash
# Clone o repositório
git clone https://github.com/juliosilva2854/tj-system.git
cd tj-system
```

### 🔧 Passo 3: Configure o Backend

```bash
cd backend

# Crie ambiente virtual Python
python3 -m venv venv

# Ative o ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt

# Configure .env
cp .env.example .env
nano .env  # Edite com suas configurações
```

**Configurações obrigatórias no `backend/.env`:**
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=gestaotj
JWT_SECRET=seu-secret-aqui
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app
FRONTEND_URL=http://localhost:3000
```

```bash
# Inicie o backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 🎨 Passo 4: Configure o Frontend

**Em outro terminal:**
```bash
cd frontend

# Instale dependências
yarn install

# Configure .env
cp .env.example .env
nano .env  # Edite com suas configurações
```

**Configuração obrigatória no `frontend/.env`:**
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

```bash
# Inicie o frontend
yarn start
```

### 🗄️ Passo 5: Inicialize o Banco

**Em outro terminal:**
```bash
curl -X POST http://localhost:8001/api/seed
```

### ✅ Passo 6: Acesse o Sistema

- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8001
- **Docs:** http://localhost:8001/docs

---

## 🚀 Método 3: Deploy em Produção

### Opção A: Railway (Mais Simples)

#### Backend no Railway

1. **Crie conta:** https://railway.app
2. **New Project > Deploy from GitHub**
3. **Selecione:** `juliosilva2854/tj-system`
4. **Configure serviço do Backend:**
   - Root Directory: `/backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`

5. **Adicione MongoDB:**
   - Add Service > Database > MongoDB
   - Copie a URL de conexão

6. **Variáveis de Ambiente:**
```
MONGO_URL=mongodb://... (copie do MongoDB adicionado)
DB_NAME=gestaotj
JWT_SECRET=gere-um-secret-seguro
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app
FRONTEND_URL=https://seu-frontend.pages.dev
CORS_ORIGINS=https://seu-frontend.pages.dev
```

7. **Deploy!** Railway gera URL automaticamente

#### Frontend no Cloudflare Pages

1. **Acesse:** https://dash.cloudflare.com
2. **Workers & Pages > Create application > Pages**
3. **Connect to Git:** Conecte ao GitHub
4. **Configurações:**
   - Build command: `cd frontend && yarn install && yarn build`
   - Build output: `frontend/build`
   - Root directory: `/`

5. **Environment Variable:**
```
REACT_APP_BACKEND_URL=https://seu-backend.railway.app
```

6. **Custom Domain:**
   - Adicione: `tj.seudominio.com`
   - Adicione: `administrator.seudominio.com`

### Opção B: Google Cloud Run + Cloudflare Pages

#### Backend no Cloud Run

```bash
# Instale gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Login
gcloud auth login

# Configure projeto
gcloud config set project SEU-PROJECT-ID

# Build e push
cd backend
gcloud builds submit --tag gcr.io/SEU-PROJECT-ID/gestao-tj-backend

# Deploy
gcloud run deploy gestao-tj-backend \
  --image gcr.io/SEU-PROJECT-ID/gestao-tj-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "MONGO_URL=mongodb+srv://...,JWT_SECRET=...,SMTP_USER=...,SMTP_PASSWORD=..."

# Obtenha URL
gcloud run services describe gestao-tj-backend --region us-central1
```

#### MongoDB Atlas (Recomendado para Produção)

1. **Crie conta:** https://www.mongodb.com/cloud/atlas
2. **Create Cluster:** Escolha região próxima
3. **Database Access:** Crie um usuário
4. **Network Access:** Adicione `0.0.0.0/0` (ou IPs específicos)
5. **Connect:** Copie a connection string
   ```
   mongodb+srv://username:password@cluster.mongodb.net/gestaotj
   ```

### Opção C: Vercel + Railway

#### Backend no Railway (igual Opção A)

#### Frontend no Vercel

```bash
# Instale Vercel CLI
npm i -g vercel

# Na pasta frontend
cd frontend
vercel login

# Deploy
vercel --prod

# Configure variável de ambiente no dashboard
# REACT_APP_BACKEND_URL=https://backend-url.railway.app
```

---

## 🔧 Troubleshooting

### Problema: MongoDB não conecta

**Solução:**
```bash
# Verifique se MongoDB está rodando
sudo systemctl status mongod

# Reinicie
sudo systemctl restart mongod

# Veja logs
sudo tail -50 /var/log/mongodb/mongod.log
```

### Problema: Backend retorna erro 500

**Solução:**
```bash
# Verifique logs
docker-compose logs backend  # Docker
# ou
tail -50 logs.txt  # Local

# Verifique .env
cat backend/.env

# Reinstale dependências
pip install -r requirements.txt
```

### Problema: Frontend não conecta no backend

**Solução:**
```bash
# Verifique .env do frontend
cat frontend/.env

# Deve ter:
REACT_APP_BACKEND_URL=http://localhost:8001

# Reinicie frontend
yarn start
```

### Problema: Email não envia

**Solução:**
1. Verifique senha de app do Gmail (16 caracteres)
2. Ative verificação em 2 etapas no Google
3. Gere nova senha de app
4. Verifique logs do backend

---

## 📊 Verificação Pós-Instalação

Execute estes comandos para verificar se tudo está funcionando:

```bash
# 1. Verifique MongoDB
curl -s http://localhost:8001/api/health | python3 -m json.tool

# 2. Verifique seed
curl -s http://localhost:8001/api/ | python3 -m json.tool

# 3. Teste login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"admin.tj","password":"Admin@2026","is_master":false}'

# 4. Acesse frontend
open http://localhost:3000  # Mac
xdg-open http://localhost:3000  # Linux
start http://localhost:3000  # Windows
```

---

## 🎯 Próximos Passos

Após instalação bem-sucedida:

1. ✅ **Faça login** com credenciais de teste
2. ✅ **Explore o sistema**
3. ✅ **Crie seu primeiro estabelecimento**
4. ✅ **Configure usuários**
5. ✅ **Teste recuperação de senha**
6. ✅ **Faça upload de foto de perfil**

---

## 📚 Recursos Adicionais

- **Documentação da API:** http://localhost:8001/docs
- **README Principal:** [README.md](README.md)
- **Guia de Deploy:** [DEPLOY.md](DEPLOY.md)
- **Issues:** https://github.com/juliosilva2854/tj-system/issues

---

**Precisa de ajuda?** Abra uma issue no GitHub ou envie email para suportegestaotj@gmail.com
