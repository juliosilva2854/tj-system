# 🎯 Checklist Final - Deploy Produção Railway + Cloudflare

**Sistema:** Gestão TJ - SaaS Multi-tenant  
**Domínio:** sconnecta.com.br  
**Data:** ___/___/2025

---

## 📦 PRÉ-DEPLOY

### Código
- [ ] Push para GitHub: `git push origin main`
- [ ] Branch main está atualizada
- [ ] Todos os testes pytest passando (48/48)
- [ ] Documentação atualizada

### Credenciais Geradas
```bash
# Executar e guardar os valores:
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('SEED_SECRET=' + secrets.token_urlsafe(16))"
```

- [ ] JWT_SECRET gerado: `________________`
- [ ] SEED_SECRET gerado: `________________`

---

## 🗄️ MONGODB ATLAS

- [ ] Conta criada/logada
- [ ] Cluster existente: `sistematj.5xfzgal.mongodb.net`
- [ ] String ajustada com `/gestaotj`:
  ```
  mongodb+srv://suportegestaotj_db_user:AX4UFsnZ4r62a4or@sistematj.5xfzgal.mongodb.net/gestaotj?retryWrites=true&w=majority&appName=SistemaTJ
  ```
- [ ] Network Access: `0.0.0.0/0` permitido
- [ ] Connection testada (opcional):
  ```bash
  mongosh "mongodb+srv://..."
  ```

---

## 🚂 RAILWAY (Backend)

### Configuração Inicial
- [ ] Login com GitHub em https://railway.app
- [ ] New Project → Deploy from GitHub repo
- [ ] Repositório: `juliosilva2854/tj-system` selecionado
- [ ] Serviço backend criado automaticamente

### Settings
- [ ] Root Directory: `backend`
- [ ] Build Command:
  ```
  pip install -r requirements.txt && pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ || true
  ```
- [ ] Start Command:
  ```
  uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2
  ```

### Variables (RAW Editor)
Cole e substitua os valores:

```env
MONGO_URL=mongodb+srv://suportegestaotj_db_user:AX4UFsnZ4r62a4or@sistematj.5xfzgal.mongodb.net/gestaotj?retryWrites=true&w=majority&appName=SistemaTJ
DB_NAME=gestaotj
JWT_SECRET=<COLE_JWT_SECRET_GERADO>
SEED_SECRET=<COLE_SEED_SECRET_GERADO>
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=suportegestaotj@gmail.com
SMTP_PASSWORD=rgftbuknxzrchchk
FRONTEND_URL=https://tj.sconnecta.com.br
CORS_ORIGINS=https://tj.sconnecta.com.br,https://administrator.sconnecta.com.br
COOKIE_SAMESITE=none
COOKIE_SECURE=true
```

- [ ] Variáveis salvas
- [ ] **SEM ESPAÇOS** no `CORS_ORIGINS` confirmado

### Deploy
- [ ] Deploy iniciado automaticamente
- [ ] Aguardou 2-3 minutos
- [ ] Status: **SUCCESS** ✅
- [ ] Logs sem erros críticos

### Networking
- [ ] Settings → Networking → Generate Domain
- [ ] URL Railway anotada: `___________________________________.up.railway.app`

### Validação Backend
```bash
# Health check (substituir URL)
curl https://_________.up.railway.app/api/health
```
- [ ] Retornou: `{"status":"healthy","db":"ok"}`

### Seed (Executar 1x)
```bash
# Substituir URL e SEED_SECRET
curl -X POST https://_________.up.railway.app/api/seed \
  -H "X-Seed-Secret: SEU_SEED_SECRET"
```
- [ ] Retornou: `{"message":"Sistema inicializado com sucesso",...}`
- [ ] Seed idempotente (rodar 2x retorna "Ja inicializado")

---

## ☁️ CLOUDFLARE PAGES (Frontend)

### Setup Inicial
- [ ] Login em https://dash.cloudflare.com
- [ ] Workers & Pages → Create application → Pages
- [ ] Connect to Git → GitHub autorizado
- [ ] Repo: `juliosilva2854/tj-system` selecionado

### Build Configuration
- [ ] Project name: `gestao-tj`
- [ ] Production branch: `main`
- [ ] Framework preset: `Create React App`
- [ ] Build command: `cd frontend && yarn install && yarn build`
- [ ] Build output directory: `frontend/build`
- [ ] Root directory: `/`

### Environment Variables
- [ ] Environment variables (Advanced) → Add variable
- [ ] Variable name: `REACT_APP_BACKEND_URL`
- [ ] Value: `https://api.sconnecta.com.br`
- [ ] Salvo

### Deploy
- [ ] Save and Deploy clicado
- [ ] Aguardou 3-5 minutos
- [ ] Build SUCCESS ✅
- [ ] URL temporária anotada: `gestao-tj.pages.dev`

### Teste Temporário
```bash
curl https://gestao-tj.pages.dev
```
- [ ] Retornou HTML (200 OK)
- [ ] **NÃO testou login ainda** (CORS ainda não permite)

---

## 🌐 CLOUDFLARE DNS

### DNS Records
No dashboard do domínio `sconnecta.com.br` → DNS → Records:

**Record 1:**
- [ ] Type: `CNAME`
- [ ] Name: `tj`
- [ ] Target: `gestao-tj.pages.dev`
- [ ] Proxy: ✅ Proxied (nuvem laranja)

**Record 2:**
- [ ] Type: `CNAME`
- [ ] Name: `administrator`
- [ ] Target: `gestao-tj.pages.dev`
- [ ] Proxy: ✅ Proxied (nuvem laranja)

**Record 3:**
- [ ] Type: `CNAME`
- [ ] Name: `api`
- [ ] Target: `___________________________________.up.railway.app` (sem https://)
- [ ] Proxy: ✅ Proxied (nuvem laranja)

### Custom Domains
Workers & Pages → Projeto `gestao-tj` → Custom domains:

- [ ] Domínio `tj.sconnecta.com.br` adicionado
- [ ] Domínio `administrator.sconnecta.com.br` adicionado
- [ ] Certificados SSL ativos (pode levar 5-10 min)

### Propagação
- [ ] Aguardou 5-10 minutos
- [ ] Testou DNS:
  ```bash
  nslookup tj.sconnecta.com.br
  nslookup api.sconnecta.com.br
  ```

---

## 🔒 CLOUDFLARE SSL/TLS

### SSL/TLS Overview
- [ ] Dashboard → `sconnecta.com.br` → SSL/TLS
- [ ] Encryption mode: **Full (strict)** selecionado

### Edge Certificates
SSL/TLS → Edge Certificates:

- [ ] **Always Use HTTPS:** ON
- [ ] **Automatic HTTPS Rewrites:** ON
- [ ] **Minimum TLS Version:** TLS 1.2
- [ ] **Opportunistic Encryption:** ON

---

## ✅ VALIDAÇÃO FINAL

### Backend via DNS
```bash
# Health check
curl https://api.sconnecta.com.br/api/health

# Esperado: {"status":"healthy","db":"ok"}
```
- [ ] Health check OK

```bash
# CORS preflight
curl -I -X OPTIONS https://api.sconnecta.com.br/api/auth/login \
  -H "Origin: https://tj.sconnecta.com.br" \
  -H "Access-Control-Request-Method: POST"

# Esperado headers:
# access-control-allow-origin: https://tj.sconnecta.com.br
# access-control-allow-credentials: true
```
- [ ] CORS headers corretos

### Frontend Principal
**URL:** https://tj.sconnecta.com.br

- [ ] Página carrega (tela de login)
- [ ] SSL ativo (cadeado verde)
- [ ] Login testado:
  - Usuário: `admin.tj`
  - Senha: `Admin@2026`
- [ ] Dashboard carrega
- [ ] Estatísticas exibidas
- [ ] Menu de navegação funciona
- [ ] DevTools → Application → Cookies → `api.sconnecta.com.br`:
  - [ ] Cookie `access_token` existe
  - [ ] Flags: `HttpOnly ✅ Secure ✅ SameSite=None ✅`

### Frontend Master
**URL:** https://administrator.sconnecta.com.br

- [ ] Página carrega
- [ ] Badge "Acesso Master Global" visível
- [ ] Login testado:
  - Email: `master@sconnecta.com.br`
  - Senha: `Master@2026`
- [ ] Dashboard master carrega
- [ ] Funcionalidades específicas de master OK

### Funcionalidades Críticas
- [ ] **Produtos:** Criar, editar, deletar
- [ ] **Estoque:** Visualizar, ajustar níveis
- [ ] **Transferências:** Criar entre lojas (PAI → PAI)
- [ ] **Relatórios:** Gerar DRE, ABC, Giro
- [ ] **Usuários:** Criar, editar, deletar
- [ ] **Profile:** Upload foto, editar dados
- [ ] **Recuperação de senha:** Email chega
- [ ] **Logout:** Redireciona para login
- [ ] **Multi-tenant:** Usuários veem apenas seu tenant
- [ ] **Audit logs:** Ações sendo gravadas

### Testes Negativos
- [ ] Acesso sem auth redireciona para login
- [ ] Token inválido retorna 401
- [ ] CORS de origem não permitida bloqueado
- [ ] Seed com secret errado retorna 403

---

## 📊 MONITORAMENTO

### Railway
- [ ] Dashboard → Metrics configurado
- [ ] Logs acessíveis
- [ ] Alerts de erro configurados (opcional)

### Cloudflare
- [ ] Analytics → Traffic visualizado
- [ ] Deployments history OK
- [ ] Logs de build acessíveis

### MongoDB Atlas
- [ ] Metrics → Connections monitoradas
- [ ] Storage usage verificado (<512MB M0)
- [ ] Alerts configurados (opcional)

---

## 🔄 CI/CD

### Teste de Deploy Automático
```bash
# Fazer uma mudança trivial
echo "# Deploy test" >> README.md
git add README.md
git commit -m "Test: CI/CD automático"
git push origin main
```

- [ ] Railway detectou push e iniciou build
- [ ] Cloudflare detectou push e iniciou build
- [ ] Aguardou 5-8 minutos
- [ ] Ambos deployados com sucesso
- [ ] Mudanças refletidas em produção

---

## 📋 PÓS-DEPLOY

### Documentação
- [ ] Credenciais atualizadas em `/app/memory/test_credentials.md`
- [ ] README.md atualizado com URLs de produção
- [ ] CHANGELOG.md atualizado (opcional)

### Backups
- [ ] MongoDB Atlas: Backup manual criado (ou configurar automático no M10+)
- [ ] Código: Tag de versão criada:
  ```bash
  git tag v1.0.0-production
  git push --tags
  ```

### Comunicação
- [ ] Usuários notificados das URLs novas
- [ ] Treinamento/onboarding agendado
- [ ] Suporte configurado (email, chat, etc.)

### Segurança (Opcional mas Recomendado)
- [ ] Cloudflare WAF: Regra para bloquear paths suspeitos
- [ ] Rate Limiting: Limitar tentativas de login
- [ ] 2FA habilitado para contas críticas
- [ ] Backup das variáveis de ambiente em local seguro

---

## 🎉 DEPLOY CONCLUÍDO!

### URLs Finais
- ✅ **Portal Principal:** https://tj.sconnecta.com.br
- ✅ **Portal Master:** https://administrator.sconnecta.com.br
- ✅ **API Backend:** https://api.sconnecta.com.br
- ✅ **Database:** MongoDB Atlas (privado)

### Credenciais de Acesso (anotar em local seguro)
```
JWT_SECRET: ________________________________
SEED_SECRET: ________________________________
MongoDB User: suportegestaotj_db_user
MongoDB Password: AX4UFsnZ4r62a4or
SMTP Password: rgftbuknxzrchchk
```

### Próximos Passos
1. Monitorar logs nas primeiras 24h
2. Validar carga de usuários reais
3. Configurar alertas de downtime
4. Planejar backups regulares
5. Documentar runbook de incidentes

---

**Data de Deploy:** ___/___/2025  
**Deploy realizado por:** _______________________  
**Aprovado por:** _______________________

**Status:** 🟢 PRODUÇÃO ATIVA

---

## 📞 Contatos de Emergência

**Suporte Técnico:** suportegestaotj@gmail.com  
**Railway Support:** https://railway.app/help  
**Cloudflare Support:** https://support.cloudflare.com  
**MongoDB Atlas Support:** https://support.mongodb.com

---

**Documentação Completa:**
- `/app/DEPLOY_RAILWAY_COMPLETO.md` - Passo a passo detalhado
- `/app/DEPLOY_QUICK_REFERENCE.md` - Referência rápida
- `/app/TROUBLESHOOTING.md` - Solução de problemas

**Repositório GitHub:** https://github.com/juliosilva2854/tj-system
