# 🚀 Deploy Completo - Railway + MongoDB Atlas + Cloudflare

**Stack Final:**
```
Frontend (React)   →  Cloudflare Pages    →  tj.sconnecta.com.br
                                              administrator.sconnecta.com.br
Backend (FastAPI)  →  Railway.app          →  api.sconnecta.com.br
Database (Mongo)   →  MongoDB Atlas        →  privado
DNS/SSL/CDN        →  Cloudflare Free     →  zero vendor lock-in
```

**Custo Total:** R$ 0,00/mês (tier gratuito)

---

## ✅ PRÉ-REQUISITOS

- [ ] Conta no GitHub (código deve estar em `juliosilva2854/tj-system`)
- [ ] Conta no Railway.app (login via GitHub)
- [ ] Conta no MongoDB Atlas (tier gratuito M0)
- [ ] Conta no Cloudflare (tier gratuito)
- [ ] Domínio sconnecta.com.br configurado no Cloudflare

---

## 📦 ETAPA 1: MongoDB Atlas (Banco de Dados)

### 1.1 Verificar String de Conexão Atual

Você já tem o MongoDB Atlas configurado:
```
mongodb+srv://suportegestaotj_db_user:AX4UFsnZ4r62a4or@sistematj.5xfzgal.mongodb.net/?appName=SistemaTJ
```

### 1.2 Ajustar para Produção

Adicione o nome do banco à string:
```
mongodb+srv://suportegestaotj_db_user:AX4UFsnZ4r62a4or@sistematj.5xfzgal.mongodb.net/gestaotj?retryWrites=true&w=majority&appName=SistemaTJ
```

### 1.3 Configurar Network Access

1. Acesse MongoDB Atlas Dashboard
2. Network Access → Add IP Address
3. **Permitir Railway:** `0.0.0.0/0` (Railway usa IPs dinâmicos)
4. Descrição: "Railway Production"

**✅ MongoDB pronto!**

---

## 🚂 ETAPA 2: Railway (Backend FastAPI)

### 2.1 Gerar Secrets

No seu terminal local, gere os tokens:

```bash
# JWT_SECRET (32 bytes)
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"

# SEED_SECRET (16 bytes)
python3 -c "import secrets; print('SEED_SECRET=' + secrets.token_urlsafe(16))"
```

**Guarde esses valores!** Vamos usar no Railway.

### 2.2 Login no Railway

1. Acesse: https://railway.app
2. Login com GitHub
3. Autorize acesso aos repositórios

### 2.3 Criar Novo Projeto

1. Dashboard → **New Project**
2. **Deploy from GitHub repo**
3. Selecione: `juliosilva2854/tj-system`
4. Railway detecta automaticamente o projeto

### 2.4 Configurar Serviço Backend

1. Clique no serviço criado (card azul)
2. **Settings** → Configure:

**Root Directory:**
```
backend
```

**Build Command:**
```
pip install -r requirements.txt && pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ || true
```

**Start Command:**
```
uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2
```

3. Clique em **Deploy** (aba superior)

### 2.5 Configurar Variáveis de Ambiente

1. Aba **Variables**
2. Clique em **RAW Editor**
3. Cole (substitua os valores entre `<...>`):

```env
MONGO_URL=mongodb+srv://suportegestaotj_db_user:AX4UFsnZ4r62a4or@sistematj.5xfzgal.mongodb.net/gestaotj?retryWrites=true&w=majority&appName=SistemaTJ
DB_NAME=gestaotj

JWT_SECRET=<COLE_O_JWT_SECRET_GERADO_NO_PASSO_2.1>
SEED_SECRET=<COLE_O_SEED_SECRET_GERADO_NO_PASSO_2.1>

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=suportegestaotj@gmail.com
SMTP_PASSWORD=rgftbuknxzrchchk

FRONTEND_URL=https://tj.sconnecta.com.br
CORS_ORIGINS=https://tj.sconnecta.com.br,https://administrator.sconnecta.com.br

COOKIE_SAMESITE=none
COOKIE_SECURE=true
```

4. **Importante:** Não adicione espaços nas variáveis!
5. Clique em **Save**

### 2.6 Obter URL do Railway

1. **Settings** → Role até **Networking**
2. **Generate Domain**
3. Railway gera algo como: `gestao-tj-backend-production-xxxx.up.railway.app`
4. **COPIE ESSA URL** (sem `https://`)

Exemplo:
```
gestao-tj-backend-production-a1b2.up.railway.app
```

### 2.7 Aguardar Deploy

1. Aba **Deployments**
2. Aguarde aparecer **"SUCCESS"** (2-3 minutos)
3. Se houver erro, veja os logs e corrija

### 2.8 Testar Backend

```bash
# Substituir pela sua URL do Railway
curl https://gestao-tj-backend-production-xxxx.up.railway.app/api/health

# Deve retornar:
{"status":"healthy","db":"ok"}
```

### 2.9 Inicializar Banco (seed)

```bash
# Substituir <SEU_SEED_SECRET> pelo valor gerado no passo 2.1
# Substituir pela sua URL do Railway
curl -X POST https://gestao-tj-backend-production-xxxx.up.railway.app/api/seed \
  -H "X-Seed-Secret: <SEU_SEED_SECRET>"

# Deve retornar:
{"message":"Sistema inicializado com sucesso", ...}
```

**✅ Backend deployado e funcionando!**

---

## ☁️ ETAPA 3: Cloudflare Pages (Frontend React)

### 3.1 Acessar Cloudflare Dashboard

1. Login: https://dash.cloudflare.com
2. Verifique se `sconnecta.com.br` já está adicionado
3. Se não estiver, adicione: **Add a Site** → `sconnecta.com.br` → Free Plan

### 3.2 Criar Projeto no Cloudflare Pages

1. Menu lateral: **Workers & Pages**
2. **Create application**
3. **Pages** tab
4. **Connect to Git**

### 3.3 Conectar ao GitHub

1. **Connect GitHub**
2. Autorize Cloudflare Pages
3. Selecione: `juliosilva2854/tj-system`
4. **Begin setup**

### 3.4 Configurar Build Settings

**Project name:**
```
gestao-tj
```

**Production branch:**
```
main
```

**Framework preset:**
```
Create React App
```

**Build command:**
```
cd frontend && yarn install && yarn build
```

**Build output directory:**
```
frontend/build
```

**Root directory:**
```
/
```

### 3.5 Configurar Variável de Ambiente

1. **Environment variables** (abra a seção "Advanced")
2. **Add variable**

**Variable name:**
```
REACT_APP_BACKEND_URL
```

**Value:**
```
https://api.sconnecta.com.br
```

**Importante:** Usar `api.sconnecta.com.br` (não a URL `.railway.app` direta!)

3. Clique em **Save and Deploy**

### 3.6 Aguardar Build

1. Cloudflare faz build automático (3-5 minutos)
2. Quando terminar, anota a URL temporária: `gestao-tj.pages.dev`

### 3.7 Testar Frontend (Temporário)

1. Acesse: `https://gestao-tj.pages.dev`
2. Deve carregar a tela de login
3. **NÃO faça login ainda** (CORS vai falhar porque backend só aceita `tj.sconnecta.com.br`)

**✅ Frontend buildado com sucesso!**

---

## 🌐 ETAPA 4: Cloudflare DNS

### 4.1 Adicionar Records DNS

1. Cloudflare Dashboard
2. Selecione `sconnecta.com.br`
3. Menu lateral: **DNS** → **Records**
4. Adicione 3 records:

**Record 1: Frontend Principal**
```
Type: CNAME
Name: tj
Target: gestao-tj.pages.dev
Proxy status: ✅ Proxied (nuvem laranja)
TTL: Auto
```

**Record 2: Frontend Master**
```
Type: CNAME
Name: administrator
Target: gestao-tj.pages.dev
Proxy status: ✅ Proxied (nuvem laranja)
TTL: Auto
```

**Record 3: Backend API**
```
Type: CNAME
Name: api
Target: gestao-tj-backend-production-xxxx.up.railway.app
Proxy status: ✅ Proxied (nuvem laranja)
TTL: Auto
```

⚠️ **Importante:** No Record 3, cole apenas o domínio Railway (sem `https://`)

Clique em **Save** para cada record.

### 4.2 Conectar Domínios Customizados ao Cloudflare Pages

1. **Workers & Pages** → Projeto `gestao-tj`
2. Aba **Custom domains**
3. **Set up a custom domain**

Adicione os 2 domínios:

**Domínio 1:**
```
tj.sconnecta.com.br
```

**Domínio 2:**
```
administrator.sconnecta.com.br
```

Cloudflare configura automaticamente os certificados SSL.

### 4.3 Aguardar Propagação

- Aguarde 5-10 minutos para propagação DNS
- Pode levar até 1 hora em casos raros

**✅ DNS configurado!**

---

## 🔒 ETAPA 5: SSL e Segurança

### 5.1 Configurar SSL/TLS

1. Cloudflare Dashboard → `sconnecta.com.br`
2. **SSL/TLS** → **Overview**
3. Encryption mode: **Full (strict)**

### 5.2 Edge Certificates

1. **SSL/TLS** → **Edge Certificates**
2. Habilite:

- ✅ **Always Use HTTPS:** ON
- ✅ **Automatic HTTPS Rewrites:** ON
- ✅ **Minimum TLS Version:** TLS 1.2
- ✅ **Opportunistic Encryption:** ON

**✅ SSL configurado!**

---

## 🎯 ETAPA 6: Validação Final

### 6.1 Testar Backend via DNS

```bash
curl https://api.sconnecta.com.br/api/health
# Esperado: {"status":"healthy","db":"ok"}
```

### 6.2 Testar CORS Preflight

```bash
curl -I -X OPTIONS https://api.sconnecta.com.br/api/auth/login \
  -H "Origin: https://tj.sconnecta.com.br" \
  -H "Access-Control-Request-Method: POST"

# Deve retornar headers:
# access-control-allow-origin: https://tj.sconnecta.com.br
# access-control-allow-credentials: true
```

### 6.3 Testar Login no Browser

**Portal Principal:**
1. Acesse: https://tj.sconnecta.com.br
2. Login:
   - **Usuário:** `admin.tj`
   - **Senha:** `Admin@2026`
3. Deve entrar no dashboard
4. Navegue por módulos (Produtos, Estoque, Relatórios)
5. DevTools → Application → Cookies → `api.sconnecta.com.br`:
   - Verifique se `access_token` existe
   - Flags: `HttpOnly ✅ Secure ✅ SameSite=None`

**Portal Master:**
1. Acesse: https://administrator.sconnecta.com.br
2. Deve mostrar badge **"Acesso Master Global"**
3. Login:
   - **Email:** `master@sconnecta.com.br`
   - **Senha:** `Master@2026`

### 6.4 Testar Funcionalidades Críticas

- [ ] Login/Logout funcionando
- [ ] Dashboard carrega com estatísticas
- [ ] Produtos: Criar/Editar/Deletar
- [ ] Estoque: Visualizar e ajustar
- [ ] Transferências: Criar entre lojas
- [ ] Relatórios: Gerar DRE e ABC
- [ ] Recuperação de senha (email)
- [ ] Upload de foto de perfil
- [ ] Multi-tenant (usuários veem apenas seu tenant)

---

## 🔄 ETAPA 7: CI/CD Automático

Agora o deploy é automático! Sempre que você fizer `git push`:

```bash
git add .
git commit -m "Nova funcionalidade"
git push origin main
```

**O que acontece:**
1. Railway detecta push → rebuild backend → redeploy (2-3 min)
2. Cloudflare detecta push → rebuild frontend → redeploy (3-5 min)

**Total:** 5-8 minutos para mudanças irem para produção!

---

## 📊 Monitoramento

### Railway (Backend)

1. Dashboard do projeto
2. **Metrics:** CPU, Memória, Network
3. **Logs:** Clique no serviço → View Logs

```bash
# Comandos úteis:
# Ver logs em tempo real
railway logs

# Ver últimos 100 logs
railway logs --limit 100
```

### Cloudflare Pages (Frontend)

1. Dashboard do projeto
2. **Analytics:** Pageviews, Bandwidth
3. **Deployments:** Histórico de builds
4. **Functions:** Logs de edge functions (se usar)

### MongoDB Atlas

1. Dashboard do cluster
2. **Metrics:** Connections, Operations/sec, Storage
3. **Real-time Performance Panel**
4. **Alerts:** Configure alertas de uso

---

## 🚨 Troubleshooting

### Problema: Backend retorna 500 Internal Server Error

**Solução:**
```bash
# Ver logs do Railway
railway logs --limit 50

# Verificar variáveis de ambiente
railway variables

# Testar conexão MongoDB
# No Railway logs, procure por "MongoDB connected" ou erros de conexão
```

### Problema: Frontend carrega mas login retorna 401

**Causa:** CORS configurado incorretamente

**Solução:**
1. Railway → Variables → Verifique `CORS_ORIGINS`
2. Deve ser: `https://tj.sconnecta.com.br,https://administrator.sconnecta.com.br`
3. **SEM ESPAÇOS** entre vírgulas
4. Salvar → aguardar redeploy (2 min)

### Problema: Login funciona mas chamadas subsequentes retornam 401

**Causa:** Cookie cross-domain não configurado

**Solução:**
1. Railway → Variables → Verifique:
   ```
   COOKIE_SAMESITE=none
   COOKIE_SECURE=true
   ```
2. Cloudflare Pages → Variables → Verifique:
   ```
   REACT_APP_BACKEND_URL=https://api.sconnecta.com.br
   ```
3. DevTools → Application → Cookies → Verifique se cookie tem flags `SameSite=None` e `Secure`

### Problema: Email de recuperação não chega

**Solução:**
1. Verifique `SMTP_PASSWORD` no Railway (deve ser senha de app, 16 chars)
2. Verifique spam/lixeira
3. Gmail App Passwords: https://myaccount.google.com/apppasswords
4. Gere nova senha de app se necessário

### Problema: MongoDB timeout ou connection refused

**Solução:**
1. MongoDB Atlas → Network Access
2. Adicione `0.0.0.0/0` (permitir de qualquer lugar)
3. Verifique se senha no `MONGO_URL` está correta
4. Teste connection string localmente:
   ```bash
   mongosh "mongodb+srv://suportegestaotj_db_user:AX4UFsnZ4r62a4or@sistematj.5xfzgal.mongodb.net/gestaotj"
   ```

### Problema: Build do frontend falha no Cloudflare

**Solução:**
1. Deployments → View build log
2. Erros comuns:
   - Faltou `REACT_APP_BACKEND_URL` → Adicione nas variables
   - Erro de dependências → `yarn.lock` desatualizado
   - Memória estourada → Build command está executando no diretório errado

---

## 💰 Custos e Limites

### Tier Gratuito (Atual)

```
MongoDB Atlas M0:        R$ 0/mês
├─ Storage: 512 MB
├─ RAM: Compartilhada
└─ Connections: 500 max

Railway Hobby:           R$ 0/mês (com cartão)
├─ $5 crédito/mês
├─ 500h execução
└─ 100 GB egress

Cloudflare Pages:        R$ 0/mês
├─ Requests: Ilimitado
├─ Bandwidth: Ilimitado
└─ Builds: 500/mês

Cloudflare DNS:          R$ 0/mês
├─ SSL: Grátis
└─ CDN: Grátis

Gmail SMTP:              R$ 0/mês
└─ 500 emails/dia
────────────────────────────────
Total:                   R$ 0/mês ✅
```

### Quando Escalar (>1000 usuários ativos)

```
MongoDB Atlas M10:       ~R$ 280/mês
├─ Storage: 10 GB
├─ RAM: 2 GB dedicada
└─ Backup automático

Railway Starter:         ~R$ 100/mês
├─ 8 GB RAM
└─ $10/mês por serviço

Cloudflare Pages:        R$ 0/mês
└─ Sem mudanças

Total:                   ~R$ 380/mês
```

---

## 📋 Checklist Pós-Deploy

- [ ] Backend responde em `https://api.sconnecta.com.br/api/health`
- [ ] Frontend carrega em `https://tj.sconnecta.com.br`
- [ ] Login funciona (cookies com HttpOnly + SameSite=None)
- [ ] Dashboard carrega dados do banco
- [ ] CORS configurado corretamente
- [ ] SSL ativo (cadeado verde no browser)
- [ ] Email de recuperação funciona
- [ ] Multi-tenant isolado (usuários veem só seu tenant)
- [ ] Audit logs gravando ações
- [ ] Todas as rotas protegidas (401 sem auth)
- [ ] Credenciais em `/app/memory/test_credentials.md` atualizadas
- [ ] Documentação atualizada
- [ ] Monitoramento configurado (Railway + Cloudflare)

---

## 🎯 Próximos Passos (Opcional)

### Melhorias de Segurança

1. **Cloudflare WAF (Web Application Firewall):**
   - Security → WAF → Create rule
   - Bloquear paths suspeitos (`/admin`, `/.env`, etc.)

2. **Rate Limiting:**
   - Security → Rate Limiting Rules
   - Limitar requests de login (ex: 5 tentativas/minuto)

3. **MongoDB IP Whitelist:**
   - Trocar `0.0.0.0/0` por IPs específicos (se Railway oferecer IPs estáticos)

### Melhorias de Performance

1. **Cloudflare Page Rules:**
   - Cache Level para `/static/*`: Standard
   - Browser Cache TTL: 4 hours

2. **Railway Workers:**
   - Aumentar workers do Uvicorn (se tráfego aumentar)
   - Settings → Start Command: `--workers 4`

3. **MongoDB Indexes:**
   - Criar índices para queries frequentes
   - Ver MongoDB Atlas → Performance Advisor

### Backup e Disaster Recovery

1. **MongoDB Atlas Backup:**
   - Cluster → Backup → Enable
   - Upgrade para M10+ para backups automáticos

2. **Railway Backup:**
   - Logs persistidos em 7 dias (default)
   - Considerar export de volumes se usar persistent storage

3. **Git Backup:**
   - Sempre manter código no GitHub
   - Tags de versão: `git tag v1.0.0 && git push --tags`

---

## 🆘 Suporte

### Documentação Adicional

- `/app/PRODUCTION.md` - Hardening de segurança
- `/app/TESTING.md` - Suite de testes
- `/app/LOCAL_SETUP.md` - Desenvolvimento local

### Contatos

- **Email:** suportegestaotj@gmail.com
- **GitHub Issues:** https://github.com/juliosilva2854/tj-system/issues
- **Railway Support:** https://railway.app/help

### Logs Úteis

```bash
# Railway logs (requer CLI instalado)
railway logs --limit 100

# Cloudflare Pages: Dashboard → Deployments → View build log

# MongoDB Atlas: Dashboard → Cluster → Metrics
```

---

## ✅ Deploy Completo!

Seu sistema está rodando em produção em:

- 🌐 **Frontend:** https://tj.sconnecta.com.br
- 👨‍💼 **Master:** https://administrator.sconnecta.com.br
- 🔌 **API:** https://api.sconnecta.com.br
- 💾 **Database:** MongoDB Atlas (privado)

**Próximo deploy:** Apenas `git push origin main` e aguardar 5-8 minutos! 🚀

---

**Problemas?** Veja seção [Troubleshooting](#-troubleshooting) ou abra uma issue no GitHub.

**Deploy bem-sucedido?** ⭐ Deixe uma star no repositório!
