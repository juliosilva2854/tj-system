# 🚨 FIX: No module named uvicorn

## ❌ Erro Atual
```
/usr/local/bin/python: No module named uvicorn
```

**Causa:** O Railway não está instalando as dependências do `requirements.txt` porque o Root Directory está configurado errado.

---

## ✅ SOLUÇÃO DEFINITIVA (Escolha UMA)

### Opção 1: Usar Dockerfile.railway (RECOMENDADO)

Este Dockerfile foi criado especificamente para Railway e funciona **SEM** Root Directory.

#### Passo 1: Commit e Push

```bash
git add .
git commit -m "fix: Adicionar Dockerfile.railway para Railway"
git push origin main
```

#### Passo 2: Configurar no Railway

**Settings → Build:**

| Campo | Valor |
|-------|-------|
| Builder | **Dockerfile** |
| Dockerfile Path | **Dockerfile.railway** |
| Root Directory | **(VAZIO - deixe em branco!)** |

**Settings → Deploy:**
- Start Command: (deixe vazio)

#### Passo 3: Redeploy

1. Salve as configurações
2. Clique em **"Redeploy"**
3. Aguarde 3-5 minutos

---

### Opção 2: Corrigir Root Directory Manualmente

Se preferir usar o Dockerfile original do backend:

**Settings → Build:**

| Campo | Valor |
|-------|-------|
| Builder | **Dockerfile** |
| Dockerfile Path | **backend/Dockerfile** |
| Root Directory | **backend** ⚠️ |

**MAS também precisa:**
1. Verificar se o `backend/requirements.txt` existe
2. Verificar se o `backend/entrypoint.sh` existe

**Problema dessa opção:** Railway às vezes não respeita o Root Directory corretamente com Dockerfiles.

---

## 🎯 Diferença Entre as Opções

### Dockerfile.railway (Opção 1)
```dockerfile
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt  ← Caminho explícito
COPY backend/ ./                                   ← Copia tudo do backend
```
- ✅ Funciona SEM Root Directory
- ✅ Caminhos explícitos
- ✅ Mais confiável no Railway

### backend/Dockerfile (Opção 2)
```dockerfile
WORKDIR /app
COPY requirements.txt .          ← Assume que já está em /backend
COPY . .                          ← Copia tudo
```
- ⚠️ Requer Root Directory = `backend`
- ⚠️ Railway às vezes ignora essa configuração
- ❌ Causando o problema atual

---

## 📋 Checklist de Verificação

### Se usar Opção 1 (Dockerfile.railway):
- [ ] Commit e push feito
- [ ] Railway Settings → Dockerfile Path = `Dockerfile.railway`
- [ ] Railway Settings → Root Directory = **(vazio)**
- [ ] Redeploy disparado
- [ ] Logs mostram instalação de dependências:
  ```
  RUN pip install --no-cache-dir -r requirements.txt
  Successfully installed uvicorn-0.25.0 ...
  ```
- [ ] Container inicia sem erro "No module named uvicorn"

### Se usar Opção 2 (backend/Dockerfile):
- [ ] Railway Settings → Dockerfile Path = `backend/Dockerfile`
- [ ] Railway Settings → Root Directory = `backend`
- [ ] Redeploy disparado
- [ ] Build Logs mostram `COPY requirements.txt` com sucesso
- [ ] Container inicia sem erro

---

## ✅ Como Saber Se Funcionou

### Build Logs (aba "Build Logs")

Deve aparecer:
```
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
Collecting fastapi
Collecting uvicorn==0.25.0
...
Successfully installed fastapi-0.110.1 uvicorn-0.25.0 motor-3.3.1 ...
```

### Deploy Logs (aba "Deploy Logs")

Deve aparecer:
```
✅ Starting Container
✅ INFO: Started server process [1]
✅ INFO: Waiting for application startup.
✅ INFO: Application startup complete.
✅ INFO: Uvicorn running on http://0.0.0.0:xxxx
```

**SEM:**
```
❌ No module named uvicorn
```

---

## 🎯 Recomendação

Use a **Opção 1 (Dockerfile.railway)** porque:
- ✅ Mais confiável no Railway
- ✅ Caminhos explícitos
- ✅ Sem dependência de Root Directory
- ✅ Menos propenso a erros

---

## 📸 Se Ainda Der Erro

Me envie:
1. **Screenshot do Build Logs** (aba "Build Logs")
2. **Screenshot do Deploy Logs** (aba "Deploy Logs")
3. **Screenshot das Settings → Build** (para ver configuração)

---

## 🚀 Após Funcionar

Teste:
```bash
curl https://sua-url.railway.app/api/health
# Esperado: {"status":"healthy","db":"ok"}
```

---

**Qual opção você quer usar? Opção 1 (recomendado) ou Opção 2?** 🤔
