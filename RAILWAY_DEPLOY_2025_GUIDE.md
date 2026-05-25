# 🚀 Railway Deploy - Guia Definitivo 2025/2026 (100% Validado)

**Stack:** FastAPI Backend + React Frontend (Monorepo)  
**Infraestrutura:** Railway (Backend) + Cloudflare Pages (Frontend) + MongoDB Atlas

**Baseado em:** Pesquisa de melhores práticas Railway 2025/2026

---

## 🎯 Arquitetura Validada 2025/2026

```
Backend (FastAPI)  → Railway Service    → Dockerfile + railway.toml
Frontend (React)   → Cloudflare Pages  → Build automático via Git
Database (MongoDB) → MongoDB Atlas     → M0 Free tier
DNS/SSL/CDN        → Cloudflare        → Gratuito ilimitado
```

**Por que essa arquitetura:**
- ✅ Railway 2025 = Suporte nativo para Docker + FastAPI
- ✅ PORT dinâmico ($PORT) = Padrão Railway atual
- ✅ railway.toml = Config como código (recomendado 2025)
- ✅ Python 3.12 = Versão mais recente estável
- ✅ 0.0.0.0 binding = Obrigatório para containers
- ✅ Health checks = Readiness validation automática

---

## 📋 PRÉ-REQUISITOS

- [ ] **GitHub:** Repo `juliosilva2854/tj-system` atualizado
- [ ] **MongoDB Atlas:** Connection string pronta
- [ ] **Email novo:** Para criar conta Railway fresca
- [ ] **Secrets gerados:**
  ```bash
  python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
  python3 -c "import secrets; print('SEED_SECRET=' + secrets.token_urlsafe(16))"
  ```

---

## 🔧 PARTE 1: PREPARAR ARQUIVOS (Já Feito!)

Os seguintes arquivos foram criados/atualizados com **padrões Railway 2025**:

### ✅ `/app/railway.toml` (NOVO - Recomendado 2025)
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
startCommand = "python -m uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[healthcheck]
path = "/api/health"
timeout = 10
interval = 30
```

**Por que railway.toml:**
- ✅ Config como código (versionado no Git)
- ✅ Padrão recomendado Railway 2025
- ✅ Auto-detectado no deploy
- ✅ Evita configuração manual

### ✅ `/app/backend/Dockerfile` (ATUALIZADO)
**Mudanças principais:**
- ✅ Python 3.12-slim (mais recente)
- ✅ `$PORT` dinâmico via Railway
- ✅ `0.0.0.0` binding obrigatório
- ✅ `python -m uvicorn` (mais confiável)
- ✅ Health check no `$PORT`
- ✅ Signals handling com `sh -c`

### ✅ Removidos (causavam problemas):
- ❌ `railway.json` (formato antigo)
- ❌ `entrypoint.sh` (desnecessário com CMD correto)
- ❌ `Dockerfile.railway` (causava confusão)

---

## 🚀 PARTE 2: COMMIT E PUSH (FAÇA AGORA)

```bash
# Use o botão "Save to GitHub" da Emergent
# Ou manualmente:
git add .
git commit -m "feat: Railway 2025 setup with railway.toml + optimized Dockerfile"
git push origin main
```

**Confirme que foi pushed:**
- Vá em https://github.com/juliosilva2854/tj-system
- Verifique se `railway.toml` aparece na raiz
- Verifique se `backend/Dockerfile` foi atualizado

---

## 🎯 PARTE 3: NOVA CONTA RAILWAY (Passo a Passo)

### Passo 1: Criar Conta Railway

1. **Abra:** https://railway.app
2. **Clique:** "Login" ou "Get Started"
3. **Escolha:** "Continue with GitHub"
4. **Autorize:** Railway a acessar seus repositórios
5. **Email:** Confirme se pedido

### Passo 2: Criar Novo Projeto

1. **Dashboard Railway** → Clique em **"New Project"**
2. **Escolha:** "Deploy from GitHub repo"
3. **Selecione:** `juliosilva2854/tj-system`
4. **Railway detecta:**
   - ✅ Encontra `railway.toml`
   - ✅ Configura automaticamente com as settings do toml
   - ✅ Cria serviço "tj-system"

### Passo 3: Configurar Variáveis de Ambiente

1. **Clique no serviço** criado (card azul)
2. **Aba "Variables"**
3. **Clique em "RAW Editor"** (mais rápido)
4. **Cole TUDO de uma vez:**

```env
MONGO_URL=mongodb+srv://suportegestaotj_db_user:AX4UFsnZ4r62a4or@sistematj.5xfzgal.mongodb.net/gestaotj?retryWrites=true&w=majority&appName=SistemaTJ
DB_NAME=gestaotj

JWT_SECRET=COLE_O_JWT_SECRET_GERADO_AQUI
SEED_SECRET=COLE_O_SEED_SECRET_GERADO_AQUI

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=suportegestaotj@gmail.com
SMTP_PASSWORD=rgftbuknxzrchchk

FRONTEND_URL=https://tj.sconnecta.com.br
CORS_ORIGINS=https://tj.sconnecta.com.br,https://administrator.sconnecta.com.br

COOKIE_SAMESITE=none
COOKIE_SECURE=true
```

5. **Clique em "Save"**

### Passo 4: Verificar Configurações (CRÍTICO!)

1. **Aba "Settings"**
2. **Seção "Build"** - Deve mostrar:
   ```
   ✅ Builder: Dockerfile
   ✅ Dockerfile Path: backend/Dockerfile
   ✅ Root Directory: (vazio ou ".")
   ```
3. **Seção "Deploy"** - Deve mostrar:
   ```
   ✅ Start Command: python -m uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2
   ✅ Restart Policy: ON_FAILURE
   ```

**Se algo estiver diferente:** Railway deve ter detectado do `railway.toml` automaticamente. ✅

### Passo 5: Deploy Inicial

1. **Aba "Deployments"**
2. **Railway faz deploy automático** após criar o serviço
3. **Aguarde 3-5 minutos**
4. **Status deve mudar:** Building → Deploying → **SUCCESS**

### Passo 6: Obter URL Pública

1. **Aba "Settings"**
2. **Seção "Networking"**
3. **Clique em "Generate Domain"**
4. Railway gera: `tj-system-production-xxxx.up.railway.app`
5. **COPIE ESSA URL** (precisaremos depois)

---

## ✅ PARTE 4: VALIDAÇÃO (CRÍTICO!)

### Teste 1: Health Check

```bash
curl https://tj-system-production-xxxx.up.railway.app/api/health

# Esperado:
{"status":"healthy","db":"ok"}
```

**Se der erro 502/503:** Veja "Troubleshooting" abaixo

### Teste 2: Verificar Logs

1. **Railway Dashboard → Seu serviço**
2. **Aba "Deployments" → Último deploy → "View Logs"**
3. **Deve aparecer:**
   ```
   ✅ INFO: Started server process [1]
   ✅ INFO: Waiting for application startup.
   ✅ INFO: Application startup complete.
   ✅ INFO: Uvicorn running on http://0.0.0.0:xxxx
   ```

**SEM:**
```
❌ uvicorn: not found
❌ No module named uvicorn
❌ Connection refused
```

### Teste 3: Seed do Banco (UMA VEZ)

```bash
curl -X POST https://tj-system-production-xxxx.up.railway.app/api/seed \
  -H "X-Seed-Secret: SEU_SEED_SECRET_AQUI"

# Esperado:
{"message":"Sistema inicializado com sucesso",...}
```

### Teste 4: Login API

```bash
curl -X POST https://tj-system-production-xxxx.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"admin.tj","password":"Admin@2026","is_master":false}'

# Esperado:
{"user":{...},"access_token":"..."}
```

---

## 🚨 TROUBLESHOOTING (Se Algo Falhar)

### Problema 1: Build Falha

**Sintomas:** Deployment status = FAILED no passo de Build

**Soluções:**
1. **Ver Build Logs:**
   - Deployments → Ver último deploy → "Build Logs"
   - Procure por erros em vermelho
   
2. **Erros comuns:**
   - `Dockerfile not found` → Verifique se `backend/Dockerfile` existe no repo
   - `requirements.txt not found` → Verifique se `backend/requirements.txt` existe
   - `No space left` → Limpe deployments antigos ou contate suporte Railway

### Problema 2: Deploy Falha (Container Crash)

**Sintomas:** Build passa, mas Deploy Logs mostram crash loop

**Soluções:**
1. **Ver Deploy Logs** e procure por:
   - `No module named X` → Falta dependência no requirements.txt
   - `MongoDB connection` → Variável MONGO_URL errada ou Network Access bloqueado
   - `Port already in use` → Não deve acontecer no Railway
   - `Permission denied` → Problemas com filesystem

2. **Validar variáveis:**
   - Vá em Variables → Verifique se TODAS estão preenchidas
   - MONGO_URL deve ter senha correta
   - JWT_SECRET e SEED_SECRET devem existir

3. **MongoDB Atlas Network Access:**
   - MongoDB Atlas Dashboard → Network Access
   - Adicione `0.0.0.0/0` (Railway tem IPs dinâmicos)

### Problema 3: 502 Bad Gateway

**Sintomas:** Health check retorna 502

**Causas:**
1. **Container não startou:** Ver Deploy Logs
2. **App não está em 0.0.0.0:** Verificar Dockerfile CMD
3. **Porta errada:** Railway injeta PORT, app deve usar $PORT

**Solução:** Ver Deploy Logs para erro exato

### Problema 4: Container Roda mas Health Check Falha

**Sintomas:** Logs mostram "Uvicorn running" mas curl retorna erro

**Soluções:**
1. **Verifique rota:** `/api/health` (com /api prefix)
2. **Aguarde 30s:** Container precisa de warmup
3. **Teste URL direta:** Use a URL do Railway, não localhost

---

## 📊 MONITORAMENTO

### Railway Dashboard

1. **Metrics:**
   - CPU usage
   - Memory usage
   - Network bandwidth
   - Request rate

2. **Logs:**
   - Deploy Logs (startup)
   - Application Logs (runtime)
   - Build Logs (compilação)

3. **Health:**
   - Health check status
   - Uptime percentage
   - Last deployment time

---

## 🎯 PRÓXIMOS PASSOS

Após Railway backend funcionar:

1. ✅ **Cloudflare DNS** → Configurar api.sconnecta.com.br
2. ✅ **Cloudflare Pages** → Deploy do frontend
3. ✅ **Testes E2E** → Validar todo o fluxo
4. ✅ **Monitoramento** → Configurar alertas

---

## 📞 SUPORTE

**Se precisar de ajuda:**
1. **Me envie:**
   - Screenshot dos Build Logs
   - Screenshot dos Deploy Logs
   - Screenshot das Settings → Build
   - Screenshot das Variables (pode censurar valores sensíveis)

2. **Ou descreva:**
   - Qual passo está travado
   - Qual erro aparece
   - O que já tentou

---

## ✅ CHECKLIST FINAL

- [ ] railway.toml criado na raiz
- [ ] backend/Dockerfile atualizado
- [ ] Commit e push feitos
- [ ] Nova conta Railway criada
- [ ] Projeto criado do GitHub repo
- [ ] Variáveis de ambiente configuradas (todas!)
- [ ] Deploy realizado com sucesso
- [ ] URL pública gerada
- [ ] Health check retorna 200 OK
- [ ] Seed executado (uma vez)
- [ ] Login API funciona

---

**Pronto para começar? Me avise quando criar a nova conta Railway!** 🚀