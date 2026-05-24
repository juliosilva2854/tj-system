# ☁️ Guia Passo a Passo: Deploy no Cloudflare

Deploy completo do **Gestão TJ** usando Cloudflare Pages + Railway (backend).

---

## 📋 Visão Geral

```
┌──────────────────────────────────────┐
│  1. MongoDB Atlas (Banco)            │  ← Grátis (512MB)
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│  2. Railway (Backend FastAPI)        │  ← Grátis (500h/mês)
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│  3. Cloudflare Pages (Frontend)      │  ← Grátis (ilimitado)
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│  4. Cloudflare DNS                   │  ← Grátis
│  tj.seudominio.com                   │
│  administrator.seudominio.com        │
└──────────────────────────────────────┘
```

**Custo Total:** R$ 0,00/mês 🎉

---

## 🗄️ ETAPA 1: MongoDB Atlas (Banco de Dados)

### 1.1 Criar Conta
1. Acesse: https://www.mongodb.com/cloud/atlas/register
2. Cadastre-se com email (ou login via Google/GitHub)
3. Escolha "Free" (M0 Sandbox)

### 1.2 Criar Cluster
1. Clique em **"Build a Database"**
2. Escolha **"M0 Free"** (512MB grátis)
3. **Provider:** AWS
4. **Region:** São Paulo (sa-east-1) ou mais próximo de você
5. **Cluster Name:** `gestao-tj-cluster`
6. Clique em **"Create"**
7. Aguarde 3-5 minutos para criar

### 1.3 Criar Usuário do Banco
1. No pop-up "Security Quickstart":
   - **Authentication Method:** Username and Password
   - **Username:** `gestaotj_admin`
   - **Password:** Clique em "Autogenerate Secure Password"
   - **⚠️ COPIE A SENHA** e guarde (exemplo: `Abc123xyz456`)
   - Clique em **"Create User"**

### 1.4 Configurar Acesso de Rede
1. Ainda no pop-up:
   - **Where would you like to connect from?**
   - Selecione **"Cloud Environment"**
   - Clique em **"Add My Current IP Address"**
   - **⚠️ IMPORTANTE:** Clique em **"Add IP Address"**
   - Na caixa de texto, digite: `0.0.0.0/0` (permitir de qualquer lugar)
   - Descrição: `Allow from anywhere`
   - Clique em **"Add Entry"**
   - Clique em **"Finish and Close"**

### 1.5 Obter Connection String
1. Clique em **"Connect"** no seu cluster
2. Clique em **"Connect your application"**
3. Driver: **Python**, Version: **3.12 or later**
4. Copie a connection string:
   ```
   mongodb+srv://gestaotj_admin:<password>@gestao-tj-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. **Substitua `<password>`** pela senha que você copiou no passo 1.3
6. **Adicione o nome do banco:** Troque `/?retryWrites` por `/gestaotj?retryWrites`
7. String final deve ficar assim:
   ```
   mongodb+srv://gestaotj_admin:SuaSenhaAqui@gestao-tj-cluster.xxxxx.mongodb.net/gestaotj?retryWrites=true&w=majority
   ```
8. **GUARDE ESTA STRING!** Vamos usar no Railway.

---

## 🚂 ETAPA 2: Railway (Backend)

### 2.1 Criar Conta
1. Acesse: https://railway.app
2. Clique em **"Login"**
3. Login com **GitHub** (recomendado)
4. Autorize Railway a acessar seus repositórios

### 2.2 Criar Projeto
1. Dashboard do Railway
2. Clique em **"New Project"**
3. Escolha **"Deploy from GitHub repo"**
4. Selecione: **`juliosilva2854/tj-system`**
5. Railway detecta automaticamente e cria o serviço

### 2.3 Configurar Serviço do Backend
1. Clique no serviço criado (card azul)
2. Vá na aba **"Settings"**
3. Configure:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2`
4. Clique em **"Save Changes"**

### 2.4 Adicionar Variáveis de Ambiente
1. Ainda no serviço, vá na aba **"Variables"**
2. Clique em **"RAW Editor"**
3. Cole (substitua os valores com `...` pelos seus):

```env
MONGO_URL=mongodb+srv://gestaotj_admin:SuaSenha@gestao-tj-cluster.xxxxx.mongodb.net/gestaotj?retryWrites=true&w=majority
DB_NAME=gestaotj
JWT_SECRET=cole-um-texto-aleatorio-de-32-caracteres-aqui
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app-16-chars
FRONTEND_URL=https://tj.seudominio.com
CORS_ORIGINS=https://tj.seudominio.com,https://administrator.seudominio.com
```

**Como preencher cada variável:**

- **MONGO_URL:** Cole a connection string do MongoDB Atlas (passo 1.5)
- **JWT_SECRET:** Gere um aleatório:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- **SMTP_USER:** Seu email do Gmail
- **SMTP_PASSWORD:** Senha de app do Gmail (veja LOCAL_SETUP.md)
- **FRONTEND_URL:** Por enquanto deixe `http://localhost:3000` (vamos atualizar depois)
- **CORS_ORIGINS:** Por enquanto deixe `*` (vamos atualizar depois)

4. Clique em **"Save"**

### 2.5 Deploy do Backend
1. Volte para a aba **"Deployments"**
2. Railway fará deploy automático
3. Aguarde 2-3 minutos
4. Quando ver **"SUCCESS"**, anote a URL gerada

### 2.6 Obter URL do Backend
1. No serviço, vá na aba **"Settings"**
2. Role até **"Domains"**
3. Clique em **"Generate Domain"**
4. Railway gera uma URL como: `https://gestao-tj-backend-production-xxxx.up.railway.app`
5. **COPIE ESTA URL!** Vamos usar no frontend.

### 2.7 Testar Backend
```bash
curl https://sua-url.railway.app/api/health

# Deve retornar:
{"status":"healthy","db":"ok"}
```

### 2.8 Inicializar Banco
```bash
curl -X POST https://sua-url.railway.app/api/seed

# Deve retornar:
{"message":"Sistema inicializado", ...}
```

✅ **Backend no ar!**

---

## 🌐 ETAPA 3: Cloudflare Pages (Frontend)

### 3.1 Preparar Domínio no Cloudflare

**Se você JÁ tem um domínio:**

1. Acesse: https://dash.cloudflare.com
2. Clique em **"Add a site"**
3. Digite seu domínio: `seudominio.com`
4. Escolha plano **"Free"**
5. Cloudflare mostra os nameservers:
   ```
   nameserver1.cloudflare.com
   nameserver2.cloudflare.com
   ```
6. **Vá ao seu registrador** (Registro.br, GoDaddy, etc.)
7. **Troque os nameservers** pelos da Cloudflare
8. Aguarde 5-60 minutos para propagação
9. Cloudflare enviará email quando ativar

**Se você NÃO tem um domínio:**

Por enquanto, use o domínio gerado pelo Cloudflare Pages (ex: `gestao-tj.pages.dev`)

### 3.2 Criar Projeto no Cloudflare Pages
1. No Cloudflare Dashboard
2. Vá em **"Workers & Pages"**
3. Clique em **"Create application"**
4. Clique em **"Pages"**
5. Clique em **"Connect to Git"**

### 3.3 Conectar ao GitHub
1. Clique em **"Connect GitHub"**
2. Autorize Cloudflare Pages
3. Selecione repositório: **`juliosilva2854/tj-system`**

### 3.4 Configurar Build
1. **Project name:** `gestao-tj`
2. **Production branch:** `main`
3. **Framework preset:** `Create React App`
4. **Build command:** `cd frontend && yarn install && yarn build`
5. **Build output directory:** `frontend/build`
6. **Root directory:** `/` (deixe vazio)

### 3.5 Adicionar Variável de Ambiente
1. Clique em **"Environment variables"** (abra Advanced)
2. Clique em **"Add variable"**
3. **Variable name:** `REACT_APP_BACKEND_URL`
4. **Value:** `https://sua-url.railway.app` (a URL do Railway)
5. Clique em **"Save"**

### 3.6 Deploy do Frontend
1. Clique em **"Save and Deploy"**
2. Aguarde 3-5 minutos
3. Cloudflare faz build e deploy
4. Quando terminar, verá a URL: `https://gestao-tj.pages.dev`

### 3.7 Testar Frontend
1. Acesse: `https://gestao-tj.pages.dev`
2. Deve aparecer a tela de login
3. Login com: `admin.tj` / `Admin@2026`

✅ **Frontend no ar!**

---

## 🔗 ETAPA 4: Configurar Domínio Customizado

### 4.1 Adicionar DNS Records
1. No Cloudflare Dashboard
2. Selecione seu domínio
3. Vá em **"DNS"** > **"Records"**
4. Clique em **"Add record"**

**Record 1 - Subdomínio Principal:**
```
Type: CNAME
Name: tj
Target: gestao-tj.pages.dev
Proxy status: Proxied (nuvem laranja)
```

**Record 2 - Subdomínio Master:**
```
Type: CNAME
Name: administrator
Target: gestao-tj.pages.dev
Proxy status: Proxied (nuvem laranja)
```

**Record 3 - API (Opcional):**
```
Type: CNAME
Name: api
Target: sua-url.railway.app
Proxy status: Proxied (nuvem laranja)
```

### 4.2 Conectar Domínio ao Cloudflare Pages
1. Volte para **Workers & Pages**
2. Clique no projeto **gestao-tj**
3. Vá na aba **"Custom domains"**
4. Clique em **"Set up a custom domain"**
5. Digite: `tj.seudominio.com`
6. Clique em **"Continue"**
7. Cloudflare adiciona automaticamente
8. Repita para: `administrator.seudominio.com`

### 4.3 Aguardar Propagação DNS
1. Aguarde 5-10 minutos
2. Teste:
   ```bash
   curl https://tj.seudominio.com
   # Deve retornar HTML da página
   ```

---

## 🔒 ETAPA 5: Configurar SSL e Segurança

### 5.1 SSL/TLS
1. Cloudflare Dashboard > Seu domínio
2. **SSL/TLS** > **Overview**
3. Modo: Selecione **"Full (strict)"**
4. **Edge Certificates:**
   - ✅ Always Use HTTPS: **ON**
   - ✅ Automatic HTTPS Rewrites: **ON**
   - ✅ Minimum TLS Version: **TLS 1.2**

### 5.2 Atualizar Variáveis de Ambiente

**No Railway (Backend):**
1. Volte ao serviço do backend
2. Vá em **Variables** > **RAW Editor**
3. Atualize:
   ```env
   FRONTEND_URL=https://tj.seudominio.com
   CORS_ORIGINS=https://tj.seudominio.com,https://administrator.seudominio.com
   ```
4. Clique em **"Save"**
5. Railway fará redeploy automático (2-3 min)

**No Cloudflare Pages (Frontend):**
1. Volte ao projeto do frontend
2. **Settings** > **Environment variables**
3. Clique no ícone de edição em `REACT_APP_BACKEND_URL`
4. Atualize para: `https://api.seudominio.com` (ou a URL do Railway)
5. Clique em **"Save"**
6. Volte para **Deployments**
7. No último deployment, clique nos 3 pontinhos
8. Clique em **"Retry deployment"**

---

## 🎉 ETAPA 6: Testar Tudo Funcionando

### 6.1 Acesse o Sistema
- **Principal:** https://tj.seudominio.com
- **Master:** https://administrator.seudominio.com

### 6.2 Faça Login
- **Usuário:** `admin.tj`
- **Senha:** `Admin@2026`

### 6.3 Teste Funcionalidades
1. ✅ Dashboard carrega
2. ✅ Criar usuário com username, CPF, telefone
3. ✅ Upload de foto de perfil
4. ✅ Recuperação de senha (email)
5. ✅ Todos os módulos funcionando

---

## 🔄 Deploy Automático (CI/CD)

Agora, sempre que você fizer `git push`:

1. **Railway** detecta e faz deploy do backend automaticamente
2. **Cloudflare Pages** detecta e faz deploy do frontend automaticamente

```bash
# No seu computador local:
git add .
git commit -m "Nova funcionalidade"
git push origin main

# Aguarde 3-5 minutos
# Suas mudanças estarão live!
```

---

## 📊 Monitoramento

### Railway (Backend)
1. Dashboard > Seu projeto
2. **Metrics:** CPU, Memória, Requests
3. **Logs:** Clique no serviço > Aba "Logs"

### Cloudflare Pages (Frontend)
1. Dashboard > gestao-tj
2. **Analytics:** Pageviews, Bandwidth
3. **Deployments:** Histórico de deploys

### MongoDB Atlas
1. Dashboard > Seu cluster
2. **Metrics:** Connections, Operations
3. **Database:** Tamanho do banco

---

## 🐛 Troubleshooting

### Frontend não conecta no backend
1. Verifique `REACT_APP_BACKEND_URL` no Cloudflare Pages
2. Verifique `CORS_ORIGINS` no Railway
3. Teste backend: `curl https://api.seudominio.com/api/health`

### Erro 502 Bad Gateway
1. Railway: Verifique logs do backend
2. MongoDB: Verifique connection string
3. Railway: Verifique se serviço está rodando

### Email não envia
1. Verifique `SMTP_PASSWORD` está correto
2. Verifique senha de app do Gmail (16 chars)
3. Teste: "Esqueci minha senha" no frontend

---

## 💰 Custos

### Infraestrutura Gratuita (Recomendado para começar)
```
MongoDB Atlas M0:        R$ 0/mês (512MB)
Railway Hobby:           R$ 0/mês (500h, $5 crédito)
Cloudflare Pages:        R$ 0/mês (ilimitado)
Cloudflare DNS:          R$ 0/mês
Gmail SMTP:              R$ 0/mês (500 emails/dia)
────────────────────────────────────────
Total:                   R$ 0/mês ✅
```

### Quando Escalar (>1000 usuários)
```
MongoDB Atlas M10:       ~R$ 280/mês (10GB)
Railway Starter:         ~R$ 100/mês (8GB RAM)
Cloudflare Pages:        R$ 0/mês
Cloudflare Pro:          ~R$ 100/mês (opcional)
────────────────────────────────────────
Total:                   ~R$ 380-480/mês
```

---

## 📚 Próximos Passos

1. ✅ Configurar backup do MongoDB
2. ✅ Adicionar domínio de email customizado
3. ✅ Configurar Cloudflare Page Rules
4. ✅ Ativar Cloudflare Analytics
5. ✅ Configurar alertas de monitoramento

---

## 🆘 Precisa de Ajuda?

- **Issues:** https://github.com/juliosilva2854/tj-system/issues
- **Email:** suportegestaotj@gmail.com
- **Documentação:** Ver README.md, DEPLOY.md

**Sistema no ar?** ⭐ Deixe uma star no repositório!
