# ✅ Checklist de Deploy - Gestão TJ

Use este checklist para garantir que seguiu todos os passos corretamente.

---

## 📋 PRÉ-REQUISITOS

- [ ] Conta no GitHub (https://github.com)
- [ ] Repositório tj-system clonado/fork
- [ ] Email do Gmail configurado
- [ ] Senha de app do Gmail gerada (16 caracteres)

---

## 🗄️ MONGODB ATLAS

- [ ] Conta criada (https://mongodb.com/cloud/atlas)
- [ ] Cluster M0 Free criado
- [ ] Região escolhida (ex: São Paulo)
- [ ] Usuário do banco criado (`gestaotj_admin`)
- [ ] Senha do banco copiada e guardada
- [ ] IP `0.0.0.0/0` adicionado (Network Access)
- [ ] Connection string copiada
- [ ] `/gestaotj` adicionado na connection string
- [ ] Senha substituída em `<password>`

**Connection String Final:**
```
mongodb+srv://gestaotj_admin:SuaSenha@cluster.mongodb.net/gestaotj?retryWrites=true&w=majority
```

---

## 🚂 RAILWAY (BACKEND)

- [ ] Conta criada (https://railway.app)
- [ ] Login feito via GitHub
- [ ] Projeto criado "Deploy from GitHub repo"
- [ ] Repositório `tj-system` selecionado
- [ ] Root Directory: `backend`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2`

### Variáveis de Ambiente (Variables):
- [ ] `MONGO_URL` = connection string do MongoDB
- [ ] `DB_NAME` = `gestaotj`
- [ ] `JWT_SECRET` = string aleatória de 32 chars
- [ ] `SMTP_HOST` = `smtp.gmail.com`
- [ ] `SMTP_PORT` = `587`
- [ ] `SMTP_USER` = seu email do Gmail
- [ ] `SMTP_PASSWORD` = senha de app de 16 chars
- [ ] `FRONTEND_URL` = (atualizar depois)
- [ ] `CORS_ORIGINS` = `*` (atualizar depois)

### Deploy e Testes:
- [ ] Deploy concluído com sucesso (verde)
- [ ] Domain gerado no Railway
- [ ] URL do backend copiada (ex: `https://....railway.app`)
- [ ] Teste: `curl https://sua-url.railway.app/api/health`
  - [ ] Retornou: `{"status":"healthy","db":"ok"}`
- [ ] Seed executado: `curl -X POST https://sua-url.railway.app/api/seed`
  - [ ] Retornou: `{"message":"Sistema inicializado",...}`

---

## ☁️ CLOUDFLARE PAGES (FRONTEND)

### Configuração Inicial:
- [ ] Conta criada (https://dash.cloudflare.com)
- [ ] Workers & Pages > Create application > Pages
- [ ] Conectado ao GitHub
- [ ] Repositório `tj-system` selecionado

### Build Settings:
- [ ] Project name: `gestao-tj`
- [ ] Production branch: `main`
- [ ] Framework preset: `Create React App`
- [ ] Build command: `cd frontend && yarn install && yarn build`
- [ ] Build output: `frontend/build`
- [ ] Root directory: `/`

### Environment Variables:
- [ ] `REACT_APP_BACKEND_URL` = URL do Railway

### Deploy e Testes:
- [ ] Deploy concluído com sucesso
- [ ] URL gerada (ex: `https://gestao-tj.pages.dev`)
- [ ] Acesso ao site funcionando
- [ ] Tela de login aparece
- [ ] Login teste: `admin.tj` / `Admin@2026` funciona

---

## 🌐 DOMÍNIO CUSTOMIZADO (OPCIONAL)

### Cloudflare DNS:
- [ ] Domínio adicionado ao Cloudflare
- [ ] Nameservers trocados no registrador
- [ ] Propagação confirmada (email da Cloudflare)

### DNS Records:
- [ ] CNAME `tj` → `gestao-tj.pages.dev` (Proxied)
- [ ] CNAME `administrator` → `gestao-tj.pages.dev` (Proxied)
- [ ] CNAME `api` → sua-url.railway.app (Proxied) - opcional

### Custom Domains no Pages:
- [ ] `tj.seudominio.com` adicionado
- [ ] `administrator.seudominio.com` adicionado
- [ ] SSL ativo (cadeado verde)

---

## 🔒 SEGURANÇA E SSL

### Cloudflare SSL/TLS:
- [ ] Modo: **Full (strict)**
- [ ] Always Use HTTPS: **ON**
- [ ] Automatic HTTPS Rewrites: **ON**
- [ ] Minimum TLS Version: **TLS 1.2**

### Atualizar Variáveis (após domínio configurado):

**Railway:**
- [ ] `FRONTEND_URL` atualizado para `https://tj.seudominio.com`
- [ ] `CORS_ORIGINS` atualizado para `https://tj.seudominio.com,https://administrator.seudominio.com`
- [ ] Redeploy automático concluído

**Cloudflare Pages:**
- [ ] `REACT_APP_BACKEND_URL` atualizado (se usar `api.seudominio.com`)
- [ ] Retry deployment executado

---

## 🧪 TESTES FINAIS

### Acesso:
- [ ] `https://tj.seudominio.com` abre
- [ ] `https://administrator.seudominio.com` abre
- [ ] Ambos mostram tela de login
- [ ] SSL ativo (cadeado verde no navegador)

### Funcionalidades:
- [ ] Login funciona: `admin.tj` / `Admin@2026`
- [ ] Dashboard carrega corretamente
- [ ] Criar usuário com username, CPF, telefone
- [ ] Upload de foto de perfil funciona
- [ ] Editar perfil funciona
- [ ] Teste "Esqueci minha senha"
  - [ ] Email recebido
  - [ ] Link funciona
  - [ ] Senha resetada com sucesso
- [ ] Navegação entre páginas funciona
- [ ] Dados salvam corretamente

### Performance:
- [ ] Páginas carregam em < 3 segundos
- [ ] Sem erros no console do navegador (F12)
- [ ] Sem erros 500 nas requisições

---

## 📊 MONITORAMENTO

### Railway:
- [ ] Logs acessíveis e sem erros
- [ ] Métricas de CPU/Memória normais
- [ ] Serviço com status "Running"

### Cloudflare:
- [ ] Analytics configurado
- [ ] Deployments com histórico visível
- [ ] Sem erros nos builds

### MongoDB:
- [ ] Conexões ativas visíveis
- [ ] Dados persistindo corretamente
- [ ] Backup automático ativado (se em produção)

---

## 🎉 DEPLOY CONCLUÍDO!

Se todos os itens acima estão ✅, seu sistema está 100% no ar!

### URLs Finais:
```
Frontend: https://tj.seudominio.com
Master:   https://administrator.seudominio.com
Backend:  https://sua-url.railway.app
MongoDB:  mongodb+srv://...
```

### Credenciais de Teste:
```
Usuário: admin.tj
Senha:   Admin@2026

Email Master: master@sconnecta.com.br
Senha Master: Master@2026
```

---

## 🔄 CI/CD Ativo

Agora, sempre que fizer `git push`:
- ✅ Railway faz deploy do backend automaticamente
- ✅ Cloudflare Pages faz deploy do frontend automaticamente
- ✅ Mudanças live em 3-5 minutos!

---

## 📚 Próximos Passos

- [ ] Trocar senhas padrão dos usuários de teste
- [ ] Criar usuários reais do sistema
- [ ] Configurar backup do MongoDB
- [ ] Adicionar domínio de email customizado
- [ ] Configurar monitoramento/alertas
- [ ] Documentar processos internos

---

## 🆘 Algo não funcionou?

Consulte os guias detalhados:
- **LOCAL_SETUP.md** - Rodar localmente
- **CLOUDFLARE_SETUP.md** - Deploy passo a passo
- **DEPLOY.md** - Outras opções de deploy
- **README.md** - Documentação completa

**Issues:** https://github.com/juliosilva2854/tj-system/issues

---

**Parabéns pelo deploy! 🎉**

⭐ Deixe uma star no repositório se o sistema está funcionando!
