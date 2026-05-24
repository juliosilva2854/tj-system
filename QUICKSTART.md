# ⚡ Início Rápido - Gestão TJ

Comece em **5 minutos** com Docker!

---

## 🐳 Opção 1: Docker (Mais Rápido)

### Passo 1: Clone
```bash
git clone https://github.com/juliosilva2854/tj-system.git
cd tj-system
```

### Passo 2: Configure Email (Obrigatório)
```bash
# Copie o exemplo
cp .env.example .env

# Edite e adicione suas credenciais de Gmail
nano .env
```

**Obtenha senha de app do Gmail:**
1. Vá para: https://myaccount.google.com/apppasswords
2. Clique em "Gerar" > "Outro" > Digite "Gestao TJ"
3. Copie a senha de 16 caracteres
4. Cole em `.env` na linha `SMTP_PASSWORD=`

### Passo 3: Inicie
```bash
docker-compose up -d
```

### Passo 4: Inicialize o Banco (após 30 segundos)
```bash
curl -X POST http://localhost:8001/api/seed
```

### Passo 5: Acesse
- **Frontend:** http://localhost:3000
- **Usuário:** `admin.tj`
- **Senha:** `Admin@2026`

---

## 💻 Opção 2: Local (Desenvolvimento)

### Requisitos
- Node.js 18+, Python 3.11+, MongoDB 7+

### Comandos
```bash
# Clone
git clone https://github.com/juliosilva2854/tj-system.git
cd tj-system

# Backend (Terminal 1)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edite .env com suas credenciais
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend (Terminal 2)
cd frontend
yarn install
cp .env.example .env
yarn start

# Seed (Terminal 3)
curl -X POST http://localhost:8001/api/seed
```

---

## 📚 Próximos Passos

1. ✅ [Documentação Completa](README.md)
2. ✅ [Guia de Instalação Detalhado](INSTALL.md)
3. ✅ [Guia de Deploy](DEPLOY.md)

---

## 🔑 Credenciais de Teste

| Usuário | Senha | Tipo |
|---------|-------|------|
| `admin.tj` | `Admin@2026` | Admin TJ |
| `admin.arcos` | `Admin@2026` | Admin Arcos |
| `geral.arcos` | `GerenteGeral@2026` | Gerente Geral |
| `master@sconnecta.com.br` | `Master@2026` | Master (via administrator.*) |

---

## 🆘 Problemas?

```bash
# Ver logs
docker-compose logs -f

# Reiniciar
docker-compose restart

# Limpar tudo
docker-compose down -v

# Testar backend
curl http://localhost:8001/api/health
```

---

**Pronto!** 🎉 Sistema rodando em http://localhost:3000
