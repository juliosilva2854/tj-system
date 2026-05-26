# ⚙️ Configuração de Porta Fixa - Railway

## 🎯 Porta Configurada: 8001

Para evitar problemas com variável `$PORT` do Railway, configuramos **porta fixa 8001**.

---

## 📁 Arquivos Atualizados

### 1. `/app/Dockerfile.railway`

**Mudanças:**
```dockerfile
# Adicionado ENV
ENV PORT=8001

# Porta fixa no EXPOSE
EXPOSE 8001

# Health check na porta fixa
CMD curl -fsS http://localhost:8001/api/health

# CMD sem variável $PORT
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
```

### 2. `/app/railway.toml`

**Mudanças:**
```toml
[deploy]
startCommand = "python -m uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2"
```

---

## 🌐 Configuração Railway

### Domínio Interno
```
tj-system.railway.internal:8001
```

**Uso interno:** Outros serviços Railway no mesmo projeto podem acessar via domínio interno.

### Domínio Público (Gerar)

1. **Railway Dashboard** → Seu serviço
2. **Settings** → **Networking**
3. **Generate Domain**
4. Railway gera: `tj-system-production-xxxx.up.railway.app`

**Railway mapeia automaticamente:**
- Domínio público (80/443) → Porta interna (8001)
- HTTPS automático
- SSL gerenciado

---

## ✅ Benefícios da Porta Fixa

| Aspecto | Benefício |
|---------|-----------|
| **Previsibilidade** | ✅ Sempre 8001, sem variação |
| **Debug** | ✅ Logs claros, sem confusão de porta |
| **Health Check** | ✅ Sempre sabe onde verificar |
| **Local Dev** | ✅ Mesma porta local e produção |
| **Networking** | ✅ Outros serviços sabem porta fixa |

---

## 🔧 Como Funciona no Railway

### Fluxo de Requisição

```
Internet (HTTPS :443)
    ↓
Railway Load Balancer
    ↓
tj-system-production-xxxx.up.railway.app
    ↓
Container (interno :8001)
    ↓
FastAPI + Uvicorn
```

**Railway cuida do mapeamento de portas automaticamente!**

---

## 🚀 Próximos Passos

### 1. Salvar no Git

```bash
# Arquivos modificados:
- Dockerfile.railway (porta fixa 8001)
- railway.toml (startCommand com porta 8001)
```

### 2. Railway Redeploy

- Detecta push em ~30s
- Build com nova configuração
- Deploy com porta fixa 8001

### 3. Gerar Domínio Público

1. Settings → Networking
2. Generate Domain
3. Anotar URL: `tj-system-production-xxxx.up.railway.app`

### 4. Testar

```bash
# Substituir pela sua URL
curl https://tj-system-production-xxxx.up.railway.app/api/health

# Esperado:
{"status":"healthy","db":"ok"}
```

---

## 📊 Configuração Final

```yaml
Build:
  Dockerfile: Dockerfile.railway
  Porta: 8001 (fixa)
  
Deploy:
  Comando: python -m uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
  Health: /api/health (porta 8001)
  Restart: ON_FAILURE (max 10 retries)

Networking:
  Interno: tj-system.railway.internal:8001
  Público: tj-system-production-xxxx.up.railway.app (HTTPS)
  
DNS (futuro):
  api.sconnecta.com.br → CNAME → tj-system-production-xxxx.up.railway.app
```

---

## ⚠️ Importante

**Railway mapeia portas automaticamente:**
- Você expõe: `8001` internamente
- Railway serve: `80` (HTTP) e `443` (HTTPS) externamente
- Não precisa mudar nada no código!

**Domínio interno (.railway.internal):**
- Só funciona entre serviços Railway no mesmo projeto
- Para acesso externo: Use domínio público gerado

---

## ✅ Checklist

- [x] PORT=8001 no ENV do Dockerfile
- [x] EXPOSE 8001 no Dockerfile
- [x] CMD com porta 8001 (sem variável)
- [x] railway.toml com porta 8001
- [x] Health check na porta 8001
- [ ] Salvar no Git
- [ ] Railway redeploy
- [ ] Gerar domínio público
- [ ] Testar health check

---

**Sistema configurado com porta fixa 8001 para máxima confiabilidade!** 🚀
