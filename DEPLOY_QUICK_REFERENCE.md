# ⚡ Guia Rápido - Deploy Railway + Cloudflare

**Para: sconnecta.com.br**  
**Stack: Railway (Backend) + MongoDB Atlas + Cloudflare Pages (Frontend)**

---

## 🎯 Comandos Essenciais

### Gerar Secrets (rode 1x antes do deploy)

```bash
# JWT_SECRET
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"

# SEED_SECRET
python3 -c "import secrets; print('SEED_SECRET=' + secrets.token_urlsafe(16))"
```

### Testar Backend

```bash
# Health check
curl https://api.sconnecta.com.br/api/health

# CORS preflight
curl -I -X OPTIONS https://api.sconnecta.com.br/api/auth/login \
  -H "Origin: https://tj.sconnecta.com.br" \
  -H "Access-Control-Request-Method: POST"

# Seed (só rodar 1x)
curl -X POST https://api.sconnecta.com.br/api/seed \
  -H "X-Seed-Secret: SEU_SEED_SECRET_AQUI"
```

### Fazer Deploy (CI/CD automático)

```bash
git add .
git commit -m "Nova funcionalidade"
git push origin main
# Aguarde 5-8 min → mudanças live!
```

---

## 📋 Checklist de Deploy

### ✅ Fase 1: MongoDB Atlas

- [ ] String de conexão ajustada:
  ```
  mongodb+srv://suportegestaotj_db_user:AX4UFsnZ4r62a4or@sistematj.5xfzgal.mongodb.net/gestaotj?retryWrites=true&w=majority&appName=SistemaTJ
  ```
- [ ] Network Access: `0.0.0.0/0` adicionado
- [ ] Database Name: `gestaotj`

### ✅ Fase 2: Railway (Backend)

- [ ] Projeto criado com GitHub repo
- [ ] Root Directory: `backend`
- [ ] Build Command: `pip install -r requirements.txt && pip install emergentintegrations...`
- [ ] Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2`
- [ ] **Variáveis de ambiente configuradas:**
  - [ ] `MONGO_URL`
  - [ ] `DB_NAME=gestaotj`
  - [ ] `JWT_SECRET` (32 bytes aleatórios)
  - [ ] `SEED_SECRET` (16 bytes aleatórios)
  - [ ] `SMTP_HOST=smtp.gmail.com`
  - [ ] `SMTP_PORT=587`
  - [ ] `SMTP_USER=suportegestaotj@gmail.com`
  - [ ] `SMTP_PASSWORD=rgftbuknxzrchchk`
  - [ ] `FRONTEND_URL=https://tj.sconnecta.com.br`
  - [ ] `CORS_ORIGINS=https://tj.sconnecta.com.br,https://administrator.sconnecta.com.br` **(sem espaços!)**
  - [ ] `COOKIE_SAMESITE=none`
  - [ ] `COOKIE_SECURE=true`
- [ ] Domain gerado: `gestao-tj-backend-production-xxxx.up.railway.app`
- [ ] Deploy com SUCCESS
- [ ] Health check responde: `{"status":"healthy","db":"ok"}`
- [ ] Seed executado com sucesso

### ✅ Fase 3: Cloudflare Pages (Frontend)

- [ ] Projeto `gestao-tj` criado
- [ ] Connected to Git: `juliosilva2854/tj-system`
- [ ] Production branch: `main`
- [ ] Framework preset: `Create React App`
- [ ] Build command: `cd frontend && yarn install && yarn build`
- [ ] Build output: `frontend/build`
- [ ] **Variável de ambiente:**
  - [ ] `REACT_APP_BACKEND_URL=https://api.sconnecta.com.br`
- [ ] Build completo com SUCCESS
- [ ] URL temporária funciona: `gestao-tj.pages.dev`

### ✅ Fase 4: Cloudflare DNS

**Records criados:**

- [ ] **tj** → CNAME → `gestao-tj.pages.dev` (Proxied ✅)
- [ ] **administrator** → CNAME → `gestao-tj.pages.dev` (Proxied ✅)
- [ ] **api** → CNAME → `gestao-tj-backend-production-xxxx.up.railway.app` (Proxied ✅)

**Custom domains no Cloudflare Pages:**

- [ ] `tj.sconnecta.com.br` adicionado
- [ ] `administrator.sconnecta.com.br` adicionado
- [ ] Certificados SSL ativos

### ✅ Fase 5: SSL/TLS Cloudflare

- [ ] Encryption mode: **Full (strict)**
- [ ] Edge Certificates:
  - [ ] Always Use HTTPS: **ON**
  - [ ] Automatic HTTPS Rewrites: **ON**
  - [ ] Minimum TLS Version: **TLS 1.2**

### ✅ Fase 6: Validação

**Backend:**
- [ ] `https://api.sconnecta.com.br/api/health` retorna `{"status":"healthy","db":"ok"}`
- [ ] CORS headers corretos (testar preflight)

**Frontend:**
- [ ] `https://tj.sconnecta.com.br` carrega tela de login
- [ ] Login `admin.tj` / `Admin@2026` funciona
- [ ] Dashboard carrega dados
- [ ] Navegação entre páginas OK
- [ ] DevTools → Cookies → `access_token` com flags `HttpOnly`, `Secure`, `SameSite=None`

**Master:**
- [ ] `https://administrator.sconnecta.com.br` mostra badge "Acesso Master Global"
- [ ] Login `master@sconnecta.com.br` / `Master@2026` funciona

**Funcionalidades:**
- [ ] Criar produto
- [ ] Ajustar estoque
- [ ] Criar transferência entre lojas
- [ ] Gerar relatório DRE
- [ ] Recuperação de senha (email chega)
- [ ] Upload de foto de perfil
- [ ] Logout e redirect para login

---

## 🚨 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| Backend 500 | Ver logs Railway: `railway logs` |
| Frontend carrega mas 401 no login | CORS errado: Verificar `CORS_ORIGINS` no Railway (sem espaços!) |
| Login OK mas outras chamadas 401 | Cookie config: `COOKIE_SAMESITE=none` e `COOKIE_SECURE=true` |
| Email não chega | `SMTP_PASSWORD` incorreto (deve ser 16 chars) |
| MongoDB timeout | Network Access: adicionar `0.0.0.0/0` |
| Build frontend falha | `REACT_APP_BACKEND_URL` faltando nas env vars |

---

## 🔧 Variáveis Críticas (Copiar/Colar)

### Railway RAW Editor

```env
MONGO_URL=mongodb+srv://suportegestaotj_db_user:AX4UFsnZ4r62a4or@sistematj.5xfzgal.mongodb.net/gestaotj?retryWrites=true&w=majority&appName=SistemaTJ
DB_NAME=gestaotj
JWT_SECRET=SUBSTITUA_AQUI_32_BYTES
SEED_SECRET=SUBSTITUA_AQUI_16_BYTES
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=suportegestaotj@gmail.com
SMTP_PASSWORD=rgftbuknxzrchchk
FRONTEND_URL=https://tj.sconnecta.com.br
CORS_ORIGINS=https://tj.sconnecta.com.br,https://administrator.sconnecta.com.br
COOKIE_SAMESITE=none
COOKIE_SECURE=true
```

### Cloudflare Pages Environment Variables

```
REACT_APP_BACKEND_URL=https://api.sconnecta.com.br
```

---

## 📊 Custos

**Tier Gratuito (atual):** R$ 0,00/mês

| Serviço | Limite Gratuito |
|---------|----------------|
| MongoDB Atlas M0 | 512 MB storage |
| Railway Hobby | $5 crédito/mês (500h) |
| Cloudflare Pages | Ilimitado |
| Cloudflare DNS | Ilimitado |
| Gmail SMTP | 500 emails/dia |

**Quando escalar (>1000 usuários):** ~R$ 380/mês (MongoDB M10 + Railway Starter)

---

## 📚 Documentação Completa

- **Passo a passo detalhado:** `/app/DEPLOY_RAILWAY_COMPLETO.md`
- **Cloudflare específico:** `/app/CLOUDFLARE_SETUP.md`
- **Produção geral:** `/app/DEPLOY_PRODUCAO_SCONNECTA.md`
- **Setup local:** `/app/LOCAL_SETUP.md`
- **Testes:** `/app/TESTING.md`

---

## 🎉 URLs Finais

- **Portal Principal:** https://tj.sconnecta.com.br
- **Portal Master:** https://administrator.sconnecta.com.br
- **API Backend:** https://api.sconnecta.com.br
- **Database:** MongoDB Atlas (privado)

**CI/CD ativo:** `git push` = deploy automático em 5-8 min! 🚀

---

**Problemas?** Ver troubleshooting ou abrir issue no GitHub.
