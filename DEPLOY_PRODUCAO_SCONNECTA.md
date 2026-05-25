# 🚀 Deploy Produção - sconnecta.com.br

Guia específico para o seu domínio. Use junto com `/app/CLOUDFLARE_SETUP.md` (que tem os passos detalhados de UI).

---

## 📋 Arquitetura final

```
Frontend (React)   →  Cloudflare Pages   →  tj.sconnecta.com.br
                                            administrator.sconnecta.com.br
Backend (FastAPI)  →  Railway             →  api.sconnecta.com.br
Banco (Mongo)      →  MongoDB Atlas M0    →  privado
DNS/SSL/CDN        →  Cloudflare (gratuito)
Email              →  Gmail SMTP (já configurado)
```

---

## ✅ ANTES de começar

1. **Push para GitHub** — clique no botão **"Save to GitHub"** aqui no Emergent. O Railway e Cloudflare puxam o código do repo `juliosilva2854/tj-system`. Sem push, deploy não atualiza.
2. **Verificar Fase 1 commitada** — os 5 arquivos abaixo precisam estar no repo:
   - `backend/deps.py` (lê cookie + header)
   - `backend/routers/auth.py` (cookies com SameSite/Secure configurável)
   - `backend/server.py` (CORS_ORIGINS com strip)
   - `backend/.env.example` (com COOKIE_SAMESITE / COOKIE_SECURE)
   - `frontend/src/components/DashboardLayout.js` (sem código órfão)

---

## 🔐 Geração do JWT_SECRET

Rode 1 vez no terminal:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Guarde o valor (vai em `JWT_SECRET` no Railway).

---

## 🚂 Railway — Variáveis de ambiente (RAW Editor)

Cole isto no **Variables → RAW Editor** do serviço backend, trocando os valores `<...>`:

```env
MONGO_URL=mongodb+srv://gestaotj_admin:<SUA_SENHA_MONGO>@gestao-tj-cluster.<SEU_ID>.mongodb.net/gestaotj?retryWrites=true&w=majority
DB_NAME=gestaotj
JWT_SECRET=<COLE_SEU_TOKEN_URLSAFE_32_BYTES_AQUI>

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=suportegestaotj@gmail.com
SMTP_PASSWORD=rgftbuknxzrchchk

FRONTEND_URL=https://tj.sconnecta.com.br

# CRÍTICO: lista exata dos domínios do frontend (sem '*'). Sem espaços.
CORS_ORIGINS=https://tj.sconnecta.com.br,https://administrator.sconnecta.com.br

# CRÍTICO: cross-domain (Cloudflare ↔ Railway) exige SameSite=None + Secure
COOKIE_SAMESITE=none
COOKIE_SECURE=true

# Protege o /seed em produção (recomendado). Gere outro token aleatório:
SEED_SECRET=<TOKEN_ALEATORIO_PARA_PROTEGER_SEED>
```

### Settings do serviço Railway
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2`

### Após primeiro deploy
1. Em **Settings → Domains**, clique **"Generate Domain"** → anote a URL `https://gestao-tj-backend-production-xxxx.up.railway.app`
2. Teste: `curl https://<URL_RAILWAY>/api/health` → deve retornar `{"status":"healthy","db":"ok"}`
3. Roda o seed UMA vez (com o secret que você definiu):
   ```bash
   curl -X POST https://<URL_RAILWAY>/api/seed -H "X-Seed-Secret: <SEU_SEED_SECRET>"
   ```

---

## ☁️ Cloudflare Pages — Variável de ambiente

No projeto `gestao-tj` em **Settings → Environment variables → Production**:

| Variável | Valor |
|---|---|
| `REACT_APP_BACKEND_URL` | `https://api.sconnecta.com.br` |

### Build settings
- **Framework preset:** Create React App
- **Build command:** `cd frontend && yarn install && yarn build`
- **Build output directory:** `frontend/build`
- **Root directory:** `/`

---

## 🌐 Cloudflare DNS — Records para sconnecta.com.br

No painel do Cloudflare, vá em **DNS → Records → Add record**:

| Type | Name | Target | Proxy |
|---|---|---|---|
| CNAME | `tj` | `gestao-tj.pages.dev` | ✅ Proxied |
| CNAME | `administrator` | `gestao-tj.pages.dev` | ✅ Proxied |
| CNAME | `api` | `<URL_RAILWAY_sem_https>` ex: `gestao-tj-backend-production-xxxx.up.railway.app` | ✅ Proxied |

### Em Cloudflare Pages → Custom domains
Adicione 2 domínios:
- `tj.sconnecta.com.br`
- `administrator.sconnecta.com.br`

---

## 🔒 Cloudflare SSL/TLS

- **SSL/TLS → Overview → Encryption mode:** Full (strict)
- **SSL/TLS → Edge Certificates:**
  - ✅ Always Use HTTPS: ON
  - ✅ Automatic HTTPS Rewrites: ON
  - ✅ Minimum TLS Version: TLS 1.2

---

## ⚠️ Detalhe que NINGUÉM avisa (cookies cross-domain)

Como frontend (`tj.sconnecta.com.br`) e backend (`api.sconnecta.com.br`) são **subdomínios diferentes**, o cookie httpOnly só atravessa entre eles porque:

1. **Backend seta `SameSite=None; Secure`** ← já configurado via `COOKIE_SAMESITE=none` acima
2. **CORS do backend tem `allow_credentials=True` + origens explícitas** (não `*`) ← já corrigido em `server.py`
3. **Frontend usa `withCredentials: true` no axios** ← já em `frontend/src/api.js`
4. **HTTPS em ambos** ← garantido pelo Cloudflare automaticamente
5. **Os subdomínios estão sob o mesmo eTLD+1** (`.sconnecta.com.br`) ← OK por design

Se um destes itens falhar, o login parece funcionar mas as chamadas subsequentes voltam 401.

---

## 🧪 Validação pós-deploy (checklist rápido)

```bash
# 1. Backend respondendo
curl https://api.sconnecta.com.br/api/health
# esperado: {"status":"healthy","db":"ok"}

# 2. CORS preflight OK
curl -I -X OPTIONS https://api.sconnecta.com.br/api/auth/login \
  -H "Origin: https://tj.sconnecta.com.br" \
  -H "Access-Control-Request-Method: POST"
# esperado: access-control-allow-origin: https://tj.sconnecta.com.br
#           access-control-allow-credentials: true

# 3. Login + cookie cross-domain
curl -c cookies.txt -X POST https://api.sconnecta.com.br/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: https://tj.sconnecta.com.br" \
  -d '{"identifier":"admin.tj","password":"Admin@2026","is_master":false}'
# esperado no header: set-cookie: access_token=...; SameSite=None; Secure; HttpOnly

# 4. Endpoint autenticado via cookie
curl -b cookies.txt https://api.sconnecta.com.br/api/auth/me
# esperado: JSON com dados do user
```

### Teste manual no browser
1. Abra https://tj.sconnecta.com.br
2. Login: `admin.tj` / `Admin@2026`
3. DevTools → Application → Cookies → `api.sconnecta.com.br`:
   - `access_token` deve estar listado com flags HttpOnly ✅ Secure ✅ SameSite=None
4. Navegue por Produtos, Estoque, Relatórios — todas as APIs devem retornar 200
5. Sair → deve voltar para /login e tentar /dashboard direto deve redirecionar

### Master access
- Abra https://administrator.sconnecta.com.br
- Deve aparecer **"Acesso Master Global"** (badge roxo) no topo do formulário
- Login: `master@sconnecta.com.br` / `Master@2026`

---

## 🔧 Troubleshooting comum

### "Login OK mas tudo retorna 401 nas chamadas seguintes"
- Verifique no DevTools se o `Set-Cookie` veio com `SameSite=None; Secure`
- Confira `COOKIE_SAMESITE=none` no Railway (case-insensitive)
- Confira que `REACT_APP_BACKEND_URL` aponta para `https://api.sconnecta.com.br` (não para a URL `.railway.app` direta — quebra CORS porque CORS_ORIGINS só lista `tj` e `administrator`)

### "CORS error: access-control-allow-origin"
- `CORS_ORIGINS` no Railway precisa conter a URL **exata** do frontend (com `https://` e sem barra final)
- Múltiplos: separar com vírgula sem espaço: `https://a.com,https://b.com`

### "Backend não conecta no MongoDB"
- MongoDB Atlas → Network Access → adicionar `0.0.0.0/0` (Railway tem IPs dinâmicos)
- Verifique a senha na connection string (caracteres especiais devem ser URL-encoded)

### "Email não envia em produção"
- Senha de app Gmail (`SMTP_PASSWORD`) precisa ter 16 chars, sem espaços
- Se Gmail bloquear: gere uma nova senha de app em https://myaccount.google.com/apppasswords

---

## 📞 Suporte rápido

- Logs Railway: Dashboard → serviço → aba "Logs"
- Logs Cloudflare Pages: Dashboard → projeto → "Deployments" → último → "View build log"
- Logs MongoDB Atlas: Dashboard → cluster → "Metrics" + "Profiler"

---

✅ **Após esses passos, sistema em produção em https://tj.sconnecta.com.br**
