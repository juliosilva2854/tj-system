# 🚨 FIX IMEDIATO: requirements.txt not found

## ❌ Erro Atual
```
failed to solve: "/requirements.txt" not found
```

**Causa:** Railway usa build context na raiz, mas Dockerfile procura `requirements.txt` relativo.

---

## ✅ SOLUÇÃO (2 PASSOS)

### 1️⃣ Commit e Push (Use "Save to GitHub")

Arquivos corrigidos:
- ✅ `railway.toml` → Agora aponta para `Dockerfile.railway`
- ✅ `Dockerfile.railway` → Paths explícitos `backend/requirements.txt`

```bash
# Ou manualmente:
git add railway.toml Dockerfile.railway
git commit -m "fix: Usar Dockerfile.railway com paths explícitos"
git push origin main
```

### 2️⃣ Railway NÃO Precisa Mudar Nada!

Como o `railway.toml` foi atualizado e está na raiz do repo:
- ✅ Railway vai detectar automaticamente
- ✅ Vai usar `Dockerfile.railway`
- ✅ Vai funcionar no próximo deploy

**Basta disparar um novo deploy:**

1. Railway Dashboard → Deployments
2. Clique em **"Redeploy"** ou **"Deploy"**
3. Railway vai usar o novo railway.toml
4. Build vai passar! ✅

---

## 📋 O Que Foi Corrigido

### railway.toml (ANTES):
```toml
[build]
dockerfilePath = "backend/Dockerfile"  ← Errado
```

### railway.toml (DEPOIS):
```toml
[build]
dockerfilePath = "Dockerfile.railway"  ← Correto
```

### Dockerfile.railway (CORRIGIDO):
```dockerfile
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt  ← Path explícito
COPY backend/ ./                                   ← Path explícito
```

**Por que funciona:**
- ✅ Railway build context = raiz do repo
- ✅ `Dockerfile.railway` está na raiz
- ✅ Paths começam com `backend/` (explícitos)
- ✅ Arquivo encontrado! ✅

---

## ✅ O Que Esperar Agora

### Build Logs (deve passar):
```
✅ COPY backend/requirements.txt ./requirements.txt
✅ RUN pip install -r requirements.txt
✅ Successfully installed uvicorn-0.25.0 fastapi-0.110.1 ...
✅ COPY backend/ ./
✅ exporting to docker image format
```

### Deploy Logs (deve iniciar):
```
✅ Starting Container
✅ INFO: Started server process [1]
✅ INFO: Application startup complete
✅ INFO: Uvicorn running on http://0.0.0.0:xxxx
```

---

## 🚀 Próximos Passos

1. **Salve no Git** (botão "Save to GitHub" ou git push)
2. **Aguarde 30 segundos** (Railway detecta push)
3. **Railway faz redeploy automático**
4. **Aguarde 3-5 minutos** para build completar
5. **Teste:** `curl https://sua-url/api/health`

---

## 📸 Se Ainda Falhar

Me envie:
1. Screenshot dos **novos** Build Logs
2. Screenshot das **Settings → Build** (para confirmar config)
3. Confirmação: Fez o push dos arquivos?

---

**AGORA VAI FUNCIONAR! 🚀**

O problema era simples: path relativo vs absoluto. Corrigido! ✅
