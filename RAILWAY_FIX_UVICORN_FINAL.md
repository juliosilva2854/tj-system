# 🎯 FIX DEFINITIVO: uvicorn not found

## ❌ Problema
```
/bin/sh: 1: uvicorn: not found
```

**Causa:** O Railway estava tentando executar `uvicorn` via `/bin/sh` mas o executável não estava no PATH.

## ✅ Solução Aplicada

1. **Criado `entrypoint.sh`** que usa `python -m uvicorn`
2. **Dockerfile atualizado** para usar ENTRYPOINT ao invés de CMD
3. **Suporte à variável $PORT** do Railway

---

## 🚀 O QUE FAZER AGORA (2 minutos)

### Passo 1: Commit e Push

```bash
git add .
git commit -m "fix: Usar python -m uvicorn com entrypoint.sh para Railway"
git push origin main
```

### Passo 2: Aguardar Redeploy

O Railway detectará o push e fará redeploy automático (~3-5 minutos).

### Passo 3: Verificar Logs

1. **Railway Dashboard → Seu serviço → View Logs**
2. **Agora deve aparecer:**
   ```
   ✅ Starting Container
   ✅ INFO: Started server process [1]
   ✅ INFO: Waiting for application startup.
   ✅ INFO: Application startup complete.
   ✅ INFO: Uvicorn running on http://0.0.0.0:xxxx
   ```

3. **SEM mais erros de:**
   ```
   ❌ /bin/sh: 1: uvicorn: not found
   ```

---

## 📋 Arquivos Modificados

### `/app/backend/Dockerfile`
- ✅ Usa `ENTRYPOINT ["/entrypoint.sh"]`
- ✅ Copia e torna executável o `entrypoint.sh`
- ✅ Remove CMD antigo que estava causando problema

### `/app/backend/entrypoint.sh` (NOVO)
```bash
#!/bin/sh
PORT=${PORT:-8001}
exec python -m uvicorn server:app --host 0.0.0.0 --port "$PORT" --workers 2
```

**Por que funciona:**
- `python -m uvicorn` → Executa uvicorn como módulo Python
- `exec` → Substitui o processo do shell pelo uvicorn (melhor handling de signals)
- `$PORT` → Usa a variável do Railway automaticamente

---

## ✅ Como Saber Se Funcionou

### 1. Logs do Railway

**ANTES (erro):**
```
/bin/sh: 1: uvicorn: not found
/bin/sh: 1: uvicorn: not found
/bin/sh: 1: uvicorn: not found
```

**DEPOIS (sucesso):**
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

### 2. Health Check

```bash
curl https://tj-system-production-xxxx.up.railway.app/api/health

# Esperado:
{"status":"healthy","db":"ok"}
```

### 3. Status no Railway

- Deploy status: **SUCCESS** ✅ (não apenas "Completed")
- Container: **Running** (não crashando)

---

## 🔍 Por Que o Problema Acontecia?

### Problema Original

```dockerfile
CMD uvicorn server:app ...
```

**Quando Railway executava:**
```bash
/bin/sh -c "uvicorn server:app ..."
```

**Resultado:** `/bin/sh` não encontrava `uvicorn` no PATH

### Solução Implementada

```dockerfile
ENTRYPOINT ["/entrypoint.sh"]
```

**Quando Railway executa:**
```bash
/entrypoint.sh
  └─> python -m uvicorn server:app ...
```

**Resultado:** Python executa uvicorn como módulo ✅

---

## 🎯 Checklist Final

- [ ] Arquivos commitados e pushed
- [ ] Railway iniciou redeploy automático
- [ ] Build Logs mostram sucesso
- [ ] Deploy Logs mostram "Application startup complete"
- [ ] Health check retorna 200 OK
- [ ] Container não crashando (status: Running)
- [ ] Sem mais erros "uvicorn: not found"

---

## 📸 Se Ainda Der Erro

Me envie:
1. **Screenshot dos NOVOS logs de deploy** (após o push)
2. **Screenshot do Build Logs** (para verificar se entrypoint.sh foi copiado)
3. **Confirmação:** Você fez o commit e push?

---

## 🎉 Após Funcionar

Teste os endpoints:

```bash
# Health check
curl https://sua-url.railway.app/api/health

# Seed (rodar 1x)
curl -X POST https://sua-url.railway.app/api/seed \
  -H "X-Seed-Secret: SEU_SEED_SECRET"

# Login
curl -X POST https://sua-url.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"admin.tj","password":"Admin@2026","is_master":false}'
```

---

**Agora deve funcionar! 🚀**

Faça o commit e push, e me avise o resultado!
