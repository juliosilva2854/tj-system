# 🔧 Configuração Manual Railway - SOLUÇÃO DEFINITIVA

## ❌ Problema Resolvido
```
The executable 'uvicorn' could not be found.
```

## ✅ Arquivos Corrigidos

1. ✅ **Dockerfile atualizado** com PATH correto
2. ✅ **railway.json deletado** (causava conflitos)
3. ✅ **.dockerignore criado** (otimiza build)

---

## 🚀 PASSOS PARA CONFIGURAR NO RAILWAY (5 minutos)

### 1. Commit e Push as Correções

```bash
# No seu terminal local ou Git
git add .
git commit -m "fix: Corrigir Dockerfile Railway + deletar railway.json"
git push origin main
```

### 2. Configurar no Railway Dashboard

#### A. Vá em Settings → Build

**Configure exatamente assim:**

| Campo | Valor |
|-------|-------|
| **Builder** | `Dockerfile` |
| **Dockerfile Path** | `backend/Dockerfile` |
| **Root Directory** | `backend` |

**⚠️ IMPORTANTE:** 
- **Root Directory** deve ser `backend` (não vazio!)
- Isso faz o Railway procurar o Dockerfile em `/backend/Dockerfile`

#### B. Vá em Settings → Deploy

**Start Command:** (deixe vazio ou configure como abaixo)
```bash
uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2
```

⚠️ **Nota:** O Dockerfile já tem o CMD, então pode deixar vazio.

#### C. Verificar Environment Variables

Certifique-se que **TODAS** essas variáveis estão configuradas:

```env
MONGO_URL=mongodb+srv://suportegestaotj_db_user:AX4UFsnZ4r62a4or@sistematj.5xfzgal.mongodb.net/gestaotj?retryWrites=true&w=majority&appName=SistemaTJ
DB_NAME=gestaotj
JWT_SECRET=<seu_jwt_secret_32_bytes>
SEED_SECRET=<seu_seed_secret_16_bytes>
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=suportegestaotj@gmail.com
SMTP_PASSWORD=rgftbuknxzrchchk
FRONTEND_URL=https://tj.sconnecta.com.br
CORS_ORIGINS=https://tj.sconnecta.com.br,https://administrator.sconnecta.com.br
COOKIE_SAMESITE=none
COOKIE_SECURE=true
```

**Gere JWT_SECRET e SEED_SECRET se ainda não gerou:**
```bash
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('SEED_SECRET=' + secrets.token_urlsafe(16))"
```

### 3. Redeploy

1. Clique na aba **"Deployments"**
2. Clique no botão **"Deploy"** ou **"Redeploy"** no canto superior direito

### 4. Acompanhar Logs

1. Enquanto o deploy roda, clique em **"View Logs"**
2. Você deve ver:
   ```
   ✓ Building Dockerfile
   ✓ Installing dependencies
   ✓ Starting uvicorn
   ✓ Application startup complete
   ```

---

## 📋 Checklist de Verificação

- [ ] Commit e push feitos
- [ ] Railway Settings → Build → Builder = `Dockerfile`
- [ ] Railway Settings → Build → Dockerfile Path = `backend/Dockerfile`
- [ ] Railway Settings → Build → Root Directory = `backend`
- [ ] Todas as variáveis de ambiente configuradas
- [ ] JWT_SECRET e SEED_SECRET gerados e configurados
- [ ] Redeploy disparado
- [ ] Logs mostram "Application startup complete"
- [ ] Sem erro "uvicorn could not be found"

---

## ✅ Como Saber Se Funcionou

### 1. No Railway Logs

Deve aparecer algo como:
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

### 2. Testar Health Check

```bash
# Substituir pela sua URL do Railway
curl https://tj-system-production-xxxx.up.railway.app/api/health

# Deve retornar:
{"status":"healthy","db":"ok"}
```

---

## 🚨 Se Ainda Der Erro

### Erro: "Dockerfile not found"
**Solução:** Verifique se o Root Directory está como `backend`

### Erro: "Port 8001 is not available"
**Solução:** O Railway usa a variável `$PORT` (já configurado no Dockerfile)

### Erro: "MongoDB connection timeout"
**Solução:** Verifique se MongoDB Atlas tem `0.0.0.0/0` permitido no Network Access

### Erro: "Environment variable MONGO_URL not set"
**Solução:** Vá em Variables e adicione todas as variáveis listadas acima

---

## 📸 Me Envie Se Precisar

1. **Screenshot dos logs após redeploy** (se der erro)
2. **Screenshot da aba Settings → Build** (para eu verificar config)
3. **Screenshot da aba Variables** (pode censurar valores sensíveis)

---

## 🎯 Resumo do Que Foi Corrigido

| Antes | Depois |
|-------|--------|
| ❌ railway.json com Nixpacks | ✅ Deletado (causava conflito) |
| ❌ Dockerfile sem PATH correto | ✅ PATH="/root/.local/bin:$PATH" |
| ❌ CMD com lista (formato errado) | ✅ CMD com string e $PORT |
| ❌ Sem Root Directory | ✅ Root Directory = backend |
| ❌ Sem .dockerignore | ✅ .dockerignore criado |

---

**Agora deve funcionar! 🚀**

Qualquer erro que aparecer, me envie o screenshot e eu te ajudo imediatamente.
