# Manual de Producao - Gestao TJ

Sistema SaaS multi-tenant de controle de estoque. FastAPI + React + MongoDB.

## 1. Pre-requisitos

- Docker 24+ e Docker Compose v2
- Dominio com DNS apontando para o servidor (para SSL)
- (Opcional) `certbot` para emissao de SSL Let's Encrypt

## 2. Subindo em desenvolvimento local

```bash
cp .env.example .env
# edite .env (basta JWT_SECRET por enquanto)
docker compose up -d --build
# Aguarde alguns segundos e crie os dados iniciais:
curl -X POST http://localhost:8001/api/seed
```

Acesse `http://localhost:3000`. Use as credenciais em `/app/memory/test_credentials.md`.

## 3. Subindo em producao (com SSL + reverse proxy)

### 3.1 Configurar `.env`

```bash
cp .env.example .env
vim .env
```

Defina:
- `JWT_SECRET`: 32+ caracteres aleatorios (`openssl rand -hex 32`)
- `CORS_ORIGINS`: `https://seu-dominio.com.br` (sem barra no final)
- `SEED_SECRET`: outro 32+ caracteres aleatorios (proteje o endpoint de seed)
- `GEMINI_API_KEY`: chave do Gemini se for usar OCR de NF
- `REACT_APP_BACKEND_URL`: `https://seu-dominio.com.br`

### 3.2 SSL com Let's Encrypt

```bash
# Pare o proxy do compose se estiver rodando
docker compose down proxy 2>/dev/null

# Emita o certificado (porta 80 deve estar livre)
sudo certbot certonly --standalone -d seu-dominio.com.br -d www.seu-dominio.com.br

# Copie os certificados para o volume
mkdir -p nginx/certs nginx/logs
sudo cp /etc/letsencrypt/live/seu-dominio.com.br/fullchain.pem nginx/certs/
sudo cp /etc/letsencrypt/live/seu-dominio.com.br/privkey.pem  nginx/certs/
sudo chown -R $USER:$USER nginx/certs
```

### 3.3 Ajustar nginx.prod.conf

Edite `/app/nginx/nginx.prod.conf` e substitua `DOMINIO.com.br` pelo seu dominio real.

### 3.4 Subir todos os servicos

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose ps
```

Verifique:
- `https://seu-dominio.com.br` carrega a tela de login
- `https://seu-dominio.com.br/api/health` retorna `{"status":"healthy","db":"ok"}`

### 3.5 Inicializar dados (seed protegido)

```bash
curl -X POST https://seu-dominio.com.br/api/seed \
  -H "X-Seed-Secret: $SEED_SECRET"
```

Logue inicialmente como `master@sconnecta.com.br / Master@2026` e altere TODAS as senhas (Usuarios > Editar).

## 4. Backup

```bash
# Backup do MongoDB
docker compose exec -T mongo mongodump --archive --db=gestao_tj_db > backup-$(date +%F).archive

# Restore
docker compose exec -T mongo mongorestore --archive --drop < backup-2026-07-15.archive
```

Agendar via cron (recomendado: diario 03:00, reter 14 dias).

## 5. Logs e monitoramento

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f proxy
docker compose logs -f mongo
```

Healthchecks: cada container reporta status em `docker compose ps`.

## 6. Atualizar versao

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

O MongoDB persiste via volume `mongo-data`; nao e afetado por rebuild.

## 7. Variaveis de ambiente importantes

| Var | Onde | Obrigatorio | Descricao |
|---|---|---|---|
| `JWT_SECRET` | backend | sim | Segredo para assinar JWT. Trocar = invalidar todos os tokens. |
| `MONGO_URL` | backend | sim | `mongodb://mongo:27017` no docker compose |
| `DB_NAME` | backend | sim | `gestao_tj_db` (default) |
| `CORS_ORIGINS` | backend | sim em prod | Lista separada por virgula |
| `SEED_SECRET` | backend | recomendado em prod | Header `X-Seed-Secret` exigido em /api/seed |
| `GEMINI_API_KEY` | backend | so para OCR | Habilita /api/invoices/ocr e /upload |
| `REACT_APP_BACKEND_URL` | frontend (build-time) | sim | URL publica do backend |

## 8. Roles e RBAC (resumo)

| Role | Escopo | Pode |
|---|---|---|
| master | Global | Tudo (todos os tenants, modulos, etc.) |
| admin | Tenant | Tudo dentro do tenant + gestao de usuarios |
| gerente_geral | Multi-store | CRUD produtos/fornecedores/notas, aprovar requisicoes, **transferir entre lojas** |
| gerente_logistica | PAI(s) | Aprovar requisicoes, gerenciar NF/inventario PAI |
| gerente_operacional | FILHO(s) | Criar requisicoes, baixa estoque FILHO |
| logistica | Legado | = gerente_logistica |
| operacional | Legado | = gerente_operacional |

## 9. Modulos por Deposito PAI

Master/admin podem habilitar/desabilitar menus em **Modulos > Deposito PAI**.
Lista de modulos: dashboard, stores, warehouses, products, inventory, requisitions,
transfers, invoices, suppliers, sales, reports, alerts, audit, users, guide.

## 10. Troubleshooting rapido

- **/api/health degraded**: MongoDB caiu. `docker compose logs mongo`.
- **CORS error**: confira `CORS_ORIGINS` no `.env` do backend.
- **Token invalido apos restart**: voce trocou `JWT_SECRET`. Faca login novamente.
- **Seed retorna 403**: defina `X-Seed-Secret` no header igual ao `.env`.
