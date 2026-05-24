# 🖥️ Guia Completo: Executar Localmente

Este guia ensina como rodar o **Gestão TJ** completamente no seu computador local.

---

## 📋 Pré-requisitos

Antes de começar, instale:

### Windows
1. **Git:** https://git-scm.com/download/win
2. **MongoDB:** https://www.mongodb.com/try/download/community
   - Durante instalação, marque "Install MongoDB as a Service"
3. **Python 3.11:** https://www.python.org/downloads/
   - Marque "Add Python to PATH"
4. **Node.js 20:** https://nodejs.org/
5. **Abra PowerShell como Administrador:**
   ```powershell
   npm install -g yarn
   ```

### macOS
```bash
# Instale Homebrew (se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instale as dependências
brew install git
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
brew install python@3.11 node@20
npm install -g yarn
```

### Ubuntu/Debian
```bash
# Git
sudo apt-get update
sudo apt-get install -y git

# MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# Python e Node
sudo apt-get install -y python3.11 python3.11-venv python3-pip
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g yarn
```

---

## 🚀 Instalação Passo a Passo

### Passo 1: Clone o Repositório

```bash
# Clone o projeto
git clone https://github.com/juliosilva2854/tj-system.git

# Entre na pasta
cd tj-system
```

---

### Passo 2: Configure o Backend

```bash
# Entre na pasta do backend
cd backend

# Crie ambiente virtual Python
python3 -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale dependências (pode demorar 2-3 minutos)
pip install -r requirements.txt
```

**Configure variáveis de ambiente:**

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env
# Windows: notepad .env
# Mac: open .env
# Linux: nano .env
```

**Cole esta configuração no `.env`:**

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=gestaotj

# JWT Secret (gere um aleatório)
JWT_SECRET=cole-um-texto-aleatorio-de-32-caracteres-aqui

# Email - Gmail SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app-16-chars

# Frontend URL
FRONTEND_URL=http://localhost:3000

# CORS
CORS_ORIGINS=http://localhost:3000
```

**📧 Como obter senha de app do Gmail:**

1. Vá para: https://myaccount.google.com/security
2. Ative "Verificação em duas etapas" (se não estiver ativa)
3. Vá para: https://myaccount.google.com/apppasswords
4. Clique em "Gerar" → "Outro" → Digite "Gestao TJ"
5. Copie a senha de 16 caracteres (ex: `abcd efgh ijkl mnop`)
6. Cole em `SMTP_PASSWORD` **SEM ESPAÇOS**: `abcdefghijklmnop`

**🔐 Gerar JWT_SECRET:**

```bash
# Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Ou use qualquer string aleatória de 32+ caracteres
```

**Inicie o backend:**

```bash
# Certifique-se de estar na pasta backend com venv ativo
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Você deve ver:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

✅ **Backend rodando!** Deixe este terminal aberto.

---

### Passo 3: Configure o Frontend

**Abra um NOVO terminal** e execute:

```bash
# Entre na pasta do frontend
cd tj-system/frontend

# Instale dependências (pode demorar 2-3 minutos)
yarn install
```

**Configure variáveis de ambiente:**

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env
# Windows: notepad .env
# Mac: open .env
# Linux: nano .env
```

**Cole esta configuração no `.env`:**

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

**Inicie o frontend:**

```bash
yarn start
```

**Aguarde 30-60 segundos. O navegador abrirá automaticamente em:**
```
http://localhost:3000
```

✅ **Frontend rodando!** Deixe este terminal aberto.

---

### Passo 4: Inicialize o Banco de Dados

**Abra um TERCEIRO terminal** e execute:

```bash
# Aguarde backend e frontend estarem rodando
curl -X POST http://localhost:8001/api/seed
```

**Você deve ver:**
```json
{
  "message": "Sistema inicializado",
  "tenants": { ... }
}
```

✅ **Banco inicializado com dados de teste!**

---

## 🎉 Acessar o Sistema

### 1. Abra o navegador em: http://localhost:3000

### 2. Faça login com uma das credenciais:

**Admin TJ:**
- **Usuário:** `admin.tj`
- **Senha:** `Admin@2026`

**Admin Arcos:**
- **Usuário:** `admin.arcos`
- **Senha:** `Admin@2026`

**Gerente Geral:**
- **Usuário:** `geral.arcos`
- **Senha:** `GerenteGeral@2026`

**Master (necessita subdomínio administrator.*):**
- **Email:** `master@sconnecta.com.br`
- **Senha:** `Master@2026`
- ⚠️ No localhost, use um dos usuários acima

---

## 🔍 Verificar se está Funcionando

### Backend:
```bash
# Health check
curl http://localhost:8001/api/health

# Deve retornar:
{"status":"healthy","db":"ok"}
```

### Frontend:
- Acesse: http://localhost:3000
- Deve aparecer tela de login

### MongoDB:
```bash
# Conecte ao MongoDB
mongosh

# Use o banco
use gestaotj

# Liste usuários
db.users.find().pretty()
```

---

## 🛠️ Comandos Úteis

### Backend

```bash
# Parar: Ctrl+C no terminal

# Reiniciar:
cd backend
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Ver logs:
# Os logs aparecem direto no terminal

# Rodar testes:
pytest
```

### Frontend

```bash
# Parar: Ctrl+C no terminal

# Reiniciar:
cd frontend
yarn start

# Build para produção:
yarn build

# Limpar cache:
rm -rf node_modules yarn.lock
yarn install
```

### MongoDB

```bash
# Ver status:
# Linux/Mac:
sudo systemctl status mongod

# Windows: verificar "Serviços" (services.msc)

# Reiniciar:
# Linux/Mac:
sudo systemctl restart mongod

# Windows: reiniciar serviço no "Serviços"

# Limpar banco (CUIDADO - apaga tudo):
mongosh
use gestaotj
db.dropDatabase()
exit
# Depois, rode seed novamente:
curl -X POST http://localhost:8001/api/seed
```

---

## 🐛 Solução de Problemas

### Problema: Backend não inicia

**Erro: "No module named 'fastapi'"**
```bash
# Certifique-se de estar no venv
cd backend
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

**Erro: "KeyError: 'DB_NAME'"**
```bash
# Verifique se o .env existe e está correto
cat backend/.env  # Linux/Mac
type backend\.env # Windows

# Deve conter MONGO_URL e DB_NAME
```

**Erro: "Connection refused MongoDB"**
```bash
# Verifique se MongoDB está rodando:
# Linux/Mac:
sudo systemctl status mongod
sudo systemctl start mongod

# Windows: abra services.msc e inicie "MongoDB Server"
```

### Problema: Frontend não inicia

**Erro: "PORT 3000 is already in use"**
```bash
# Mate o processo na porta 3000:
# Linux/Mac:
sudo lsof -ti:3000 | xargs kill -9

# Windows (PowerShell como Admin):
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process
```

**Erro: "Module not found"**
```bash
# Reinstale dependências:
cd frontend
rm -rf node_modules yarn.lock
yarn install
```

### Problema: Login não funciona

**Erro: "Credenciais incorretas"**
1. Verifique se o seed foi executado:
   ```bash
   curl -X POST http://localhost:8001/api/seed
   ```
2. Tente com: `admin.tj` / `Admin@2026`

**Erro: "Network Error"**
1. Verifique se backend está rodando:
   ```bash
   curl http://localhost:8001/api/health
   ```
2. Verifique `frontend/.env`:
   ```
   REACT_APP_BACKEND_URL=http://localhost:8001
   ```

---

## 📊 Acessar Outras Funcionalidades

Após fazer login:

1. **Dashboard** - Visão geral do sistema
2. **Usuários** - Criar/editar usuários (veja os novos campos!)
3. **Perfil** - Clique no seu nome → Edite perfil, upload de foto
4. **Produtos** - Cadastrar produtos
5. **Estoque** - Gerenciar inventário
6. **Transferências** - Entre depósitos
7. **Relatórios** - DRE, Curva ABC, Giro de Estoque

---

## 🎯 Próximo Passo: Deploy Cloudflare

Agora que está rodando localmente, veja o guia completo de deploy:

📘 **[CLOUDFLARE_SETUP.md](CLOUDFLARE_SETUP.md)** - Deploy passo a passo

---

## 📚 Documentação Adicional

- **README.md** - Documentação completa
- **INSTALL.md** - Métodos de instalação
- **DEPLOY.md** - Deploy em produção
- **QUICKSTART.md** - Início rápido

---

**Precisa de ajuda?**
- Issues: https://github.com/juliosilva2854/tj-system/issues
- Email: suportegestaotj@gmail.com

**Sistema funcionando localmente?** ⭐ Deixe uma star no repositório!
