# ☁️ Guia Completo de Deploy com Cloudflare

Este guia ensina como fazer deploy do **Gestão TJ** usando **Cloudflare** para o frontend e diferentes opções para o backend.

---

## 📋 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────┐
│  Cloudflare DNS & CDN                   │
│  ├─ tj.seudominio.com (Frontend)       │
│  └─ administrator.seudominio.com        │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Cloudflare Pages (Frontend)            │
│  - React Build estático                 │
│  - Deploy automático via Git            │
└─────────────────────────────────────────┘
                ↓ API Requests
┌─────────────────────────────────────────┐
│  Backend (Escolha uma opção):           │
│  A) Railway.app (Mais simples)          │
│  B) Google Cloud Run                    │
│  C) Render.com                          │
│  D) Fly.io                              │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  MongoDB Atlas (Banco de Dados)         │
└─────────────────────────────────────────┘
```

---

## 🎯 Opção 1: Railway + Cloudflare Pages (RECOMENDADO)

### Passo 1: Configure MongoDB Atlas

1. **Crie conta gratuita:** https://www.mongodb.com/cloud/atlas/register

2. **Crie um cluster:**
   - Clique em "Build a Database"
   - Escolha "M0 Free" (512MB gratuitos)
   - Região: escolha a mais próxima dos seus usuários
   - Nome do cluster: `gestao-tj-cluster`

3. **Configure acesso:**
   - **Database Access:** 
     - Add New Database User
     - Username: `gestaotj_admin`
     - Password: Gere uma senha forte
     - Role: Atlas admin
   
   - **Network Access:**
     - Add IP Address
     - Allow access from anywhere: `0.0.0.0/0`
     - (Em produção, use IPs específicos)

4. **Obtenha connection string:**
   - Clique em "Connect"
   - "Connect your application"
   - Copie a string:
   ```
   mongodb+srv://gestaotj_admin:<password>@gestao-tj-cluster.xxxxx.mongodb.net/gestaotj?retryWrites=true&w=majority
   ```
   - Substitua `<password>` pela senha criada

### Passo 2: Deploy do Backend no Railway

1. **Crie conta:** https://railway.app (login com GitHub)

2. **Novo projeto:**
   - Dashboard > New Project
   - Deploy from GitHub repo
   - Selecione: `juliosilva2854/tj-system`
   - Railway detecta automaticamente

3. **Configure o serviço:**
   - Clique no serviço criado
   - Settings:
     - **Root Directory:** `backend`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2`

4. **Adicione variáveis de ambiente:**
   - Variables tab > RAW Editor
   
   ```env
   MONGO_URL=mongodb+srv://gestaotj_admin:SUA_SENHA@gestao-tj-cluster.xxxxx.mongodb.net/gestaotj?retryWrites=true&w=majority
   DB_NAME=gestaotj
   JWT_SECRET=cole-secret-aleatorio-de-32-chars-aqui
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=seu-email@gmail.com
   SMTP_PASSWORD=sua-senha-de-app-16-chars
   FRONTEND_URL=https://tj.seudominio.com
   CORS_ORIGINS=https://tj.seudominio.com,https://administrator.seudominio.com
   ```

   **Gere JWT_SECRET:**
   ```bash
   openssl rand -hex 32
   ```

5. **Deploy:**
   - Railway faz deploy automático
   - Aguarde 2-3 minutos
   - Anote a URL gerada (ex: `https://gestao-tj-backend.up.railway.app`)

6. **Teste o backend:**
   ```bash
   curl https://sua-url.railway.app/api/health
   # Deve retornar: {"status":"healthy","db":"ok"}
   ```

7. **Inicialize o banco:**
   ```bash
   curl -X POST https://sua-url.railway.app/api/seed
   ```

### Passo 3: Deploy do Frontend no Cloudflare Pages

1. **Acesse Cloudflare:**
   - https://dash.cloudflare.com
   - Workers & Pages > Create application > Pages

2. **Conecte ao GitHub:**
   - Connect to Git
   - Autorize Cloudflare Pages
   - Selecione: `juliosilva2854/tj-system`

3. **Configure build:**
   ```
   Project name: gestao-tj
   Production branch: main
   
   Build settings:
   - Framework preset: Create React App
   - Build command: cd frontend && yarn install && yarn build
   - Build output directory: frontend/build
   - Root directory: /
   ```

4. **Variáveis de ambiente:**
   - Environment variables > Add variable
   ```
   REACT_APP_BACKEND_URL=https://sua-url.railway.app
   ```

5. **Deploy:**
   - Save and Deploy
   - Aguarde 3-5 minutos
   - Cloudflare gera URL: `gestao-tj.pages.dev`

6. **Teste:**
   - Acesse: `https://gestao-tj.pages.dev`
   - Faça login com: `admin.tj` / `Admin@2026`

### Passo 4: Configure Domínio Customizado

#### A) Adicione domínio no Cloudflare

1. **Adicione seu domínio:**
   - Dashboard > Add a site
   - Digite: `seudominio.com`
   - Escolha plano Free
   - Cloudflare fornece nameservers

2. **Configure nameservers no seu registrador:**
   - Vá ao painel do seu registrador (Registro.br, GoDaddy, etc.)
   - Troque os nameservers pelos da Cloudflare
   - Aguarde 5-60 minutos para propagação

#### B) Configure DNS

No Cloudflare Dashboard > DNS > Records:

```
Type    Name              Content                         Proxy
CNAME   tj                gestao-tj.pages.dev            ✅ Proxied
CNAME   administrator     gestao-tj.pages.dev            ✅ Proxied  
CNAME   api               sua-url.railway.app            ✅ Proxied
```

#### C) Conecte domínio ao Cloudflare Pages

1. **Pages > gestao-tj > Custom domains**
2. **Add a custom domain:**
   - `tj.seudominio.com`
   - Confirm
3. **Repita para:**
   - `administrator.seudominio.com`

#### D) Configure SSL/TLS

1. **SSL/TLS > Overview:**
   - Modo: **Full (strict)**

2. **SSL/TLS > Edge Certificates:**
   - ✅ Always Use HTTPS: ON
   - ✅ Automatic HTTPS Rewrites: ON
   - ✅ TLS 1.3: ON

### Passo 5: Otimizações do Cloudflare

#### Page Rules

1. **SSL/TLS > Page Rules > Create Page Rule:**

**Rule 1: API Bypass Cache**
```
URL: api.seudominio.com/*
Settings:
- Cache Level: Bypass
- Disable Performance
```

**Rule 2: Admin Bypass Cache**
```
URL: administrator.seudominio.com/*
Settings:
- Cache Level: Bypass
```

**Rule 3: Frontend Cache**
```
URL: tj.seudominio.com/*
Settings:
- Browser Cache TTL: 4 hours
- Cache Level: Standard
```

#### Firewall Rules (Opcional - Segurança Extra)

1. **Security > WAF > Create rule:**

```yaml
Rule name: Block suspicious paths
Expression: 
  (http.request.uri.path contains "/admin" or
   http.request.uri.path contains "/phpmyadmin" or
   http.request.uri.path contains "/.env")
Action: Block
```

---

## 🎯 Opção 2: Google Cloud Run + Cloudflare Pages

### Passo 1: MongoDB Atlas (mesmo da Opção 1)

### Passo 2: Deploy do Backend no Cloud Run

```bash
# 1. Instale gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 2. Autentique
gcloud auth login

# 3. Crie projeto
gcloud projects create gestao-tj-prod --name="Gestao TJ"
gcloud config set project gestao-tj-prod

# 4. Ative APIs necessárias
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 5. Build e deploy
cd backend
gcloud builds submit --tag gcr.io/gestao-tj-prod/backend

gcloud run deploy gestao-tj-backend \
  --image gcr.io/gestao-tj-prod/backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "MONGO_URL=mongodb+srv://...,JWT_SECRET=...,SMTP_USER=...,SMTP_PASSWORD=...,FRONTEND_URL=https://tj.seudominio.com,CORS_ORIGINS=https://tj.seudominio.com"

# 6. Obtenha URL
gcloud run services describe gestao-tj-backend --region us-central1 --format 'value(status.url)'
```

### Passo 3: Frontend e DNS (mesmo da Opção 1)

---

## 🎯 Opção 3: Render.com + Cloudflare Pages

### Backend no Render.com

1. **Crie conta:** https://render.com (login com GitHub)

2. **Novo Web Service:**
   - New > Web Service
   - Connect repository: `juliosilva2854/tj-system`
   
3. **Configure:**
   ```
   Name: gestao-tj-backend
   Region: Oregon (US West)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2
   ```

4. **Plano:** Free (ou Starter $7/mês para produção)

5. **Environment Variables:** (mesmo da Railway)

6. **Deploy:** Automático

7. **URL:** `https://gestao-tj-backend.onrender.com`

---

## 🔒 Checklist de Segurança Pós-Deploy

- [ ] JWT_SECRET é aleatório e seguro (32+ chars)
- [ ] MongoDB tem usuário e senha fortes
- [ ] MongoDB Network Access está restrito (não 0.0.0.0/0)
- [ ] CORS_ORIGINS lista apenas domínios permitidos
- [ ] SSL/TLS está em modo "Full (strict)"
- [ ] Always Use HTTPS está ON
- [ ] Senha de app do Gmail é usada (não senha principal)
- [ ] SEED_SECRET está configurado (protege /seed)
- [ ] Variáveis de ambiente estão em arquivos .env (não no código)

---

## 📊 Monitoramento

### Railway
- Dashboard > View Logs
- Metrics tab para uso de CPU/Memória

### Cloud Run
```bash
gcloud run services logs read gestao-tj-backend --region us-central1
```

### Cloudflare Analytics
- Analytics > Web Analytics
- Performance, Traffic, Requests

---

## 🔄 CI/CD Automático

Com Railway e Cloudflare Pages, o deploy é automático:

```
Git Push → GitHub
    ↓
Railway detecta → Build Backend → Deploy
    ↓
Cloudflare detecta → Build Frontend → Deploy
```

**Para fazer deploy:**
```bash
git add .
git commit -m "Nova funcionalidade"
git push origin main
```

Aguarde 2-5 minutos e as mudanças estarão live!

---

## 🚨 Troubleshooting

### Backend retorna 500 em produção

```bash
# Railway: veja logs
railway logs

# Cloud Run:
gcloud run services logs read gestao-tj-backend --limit 50

# Verifique variáveis de ambiente
# Verifique conexão com MongoDB
```

### Frontend não conecta no backend

1. Verifique `REACT_APP_BACKEND_URL` no Cloudflare Pages
2. Rebuild do frontend após mudar variável
3. Verifique CORS_ORIGINS no backend
4. Teste backend direto: `curl https://backend-url/api/health`

### MongoDB timeout

1. MongoDB Atlas > Network Access > adicione IPs do Railway/Cloud Run
2. Teste connection string localmente
3. Verifique se senha está correta

---

## 💰 Custos Estimados

### Infraestrutura Gratuita (Até ~1000 usuários)
```
MongoDB Atlas (M0):      $0/mês (512MB)
Railway (Hobby):         $0/mês (500h, $5 crédito)
Cloudflare Pages:        $0/mês (ilimitado)
Cloudflare DNS:          $0/mês
Gmail SMTP:              $0/mês (500 emails/dia)
───────────────────────────────────────
Total:                   $0/mês
```

### Infraestrutura Escalonável (1000-10000 usuários)
```
MongoDB Atlas (M10):     $57/mês (10GB, backup)
Railway (Starter):       $20/mês (8GB RAM)
Cloudflare Pages:        $0/mês
Cloudflare Pro:          $20/mês (opcional)
───────────────────────────────────────
Total:                   $77-97/mês
```

---

## 📚 Recursos Adicionais

- **Railway Docs:** https://docs.railway.app
- **Cloudflare Pages Docs:** https://developers.cloudflare.com/pages
- **MongoDB Atlas Docs:** https://docs.atlas.mongodb.com
- **Google Cloud Run Docs:** https://cloud.google.com/run/docs

---

**Deploy bem-sucedido?** ⭐ Deixe uma star no repositório!

**Problemas?** Abra uma issue: https://github.com/juliosilva2854/tj-system/issues
