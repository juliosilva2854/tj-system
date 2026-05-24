# Manual de Testes - Gestao TJ

## 1. Testes Automatizados (Backend)

### Estrutura
```
/app/backend/tests/
  test_multitenant_saas.py        # 32 testes - core (login, RBAC, IDOR, etc.)
  test_managers_transfers.py      # 16 testes - stores, gerentes, transferencias, modulos
```

### Rodar localmente
```bash
# Backend deve estar de pe (supervisor ou docker)
cd /app/backend
python -m pytest tests/ -v
```

### Rodar contra outra URL (staging/prod)
```bash
REACT_APP_BACKEND_URL=https://seu-dominio.com.br python -m pytest tests/ -v
```

O seed e disparado automaticamente como fixture. Em ambiente com `SEED_SECRET` configurado, exporte:
```bash
export SEED_SECRET=xxx
```
E adicione header `X-Seed-Secret` no codigo do fixture se necessario.

### Cobertura
- **Autenticacao**: login, refresh, /me, validacao de credenciais, rate limiting
- **RBAC**: 7 roles, permissoes corretas/negadas (403)
- **Multi-tenant (IDOR)**: usuario do tenant A nao acessa dados do tenant B
- **Stores CRUD**: criar/listar/atualizar/deletar, filtro por escopo
- **Warehouses PAI/FILHO**: criar, hierarquia, validacao de tipo
- **Requisicoes FILHO -> PAI**: criar, aprovar, rejeitar, transferencia atomica
- **Transferencias PAI -> PAI entre lojas**: gerente_geral, valida estoque, debita/credita
- **Modulos**: configurar por PAI, FILHO herda, validacao de modulo invalido
- **Audit**: log em PT-BR, escopado por role
- **Dashboard / Reports**: stats, alertas, financeiro, ABC, giro
- **Sanitizacao**: rejeicao de tags <script>, validacao de email

## 2. Smoke Manual

### Login pelos 8 usuarios seed
```
master@sconnecta.com.br             / Master@2026
admin@tj.sconnecta.com.br           / Admin@2026
logistica@tj.sconnecta.com.br       / Logistica@2026
operacional@tj.sconnecta.com.br     / Operacional@2026
admin@arcos.sconnecta.com.br        / Admin@2026
gerentegeral@arcos.sconnecta.com.br / GerenteGeral@2026
gerentelogA@arcos.sconnecta.com.br  / GerenteLog@2026
gerenteopA@arcos.sconnecta.com.br   / GerenteOp@2026
```

### Fluxo end-to-end (Arcos Dourados)
1. Login como `admin@arcos` -> ver Lojas (Rest. A, Rest. B), criar produto
2. Em Notas Fiscais > Nova: emitir entrada de 100 unidades no PAI A
3. Em Estoque: ver 100 disponiveis em PAI A
4. Logout, login como `gerentegeral@arcos`
5. Sidebar deve mostrar: Lojas, Depositos, Produtos, Estoque, Requisicoes, **Transferencias**, etc.
6. Em Transferencias > Nova: PAI Rest. A -> PAI Rest. B, 50 unidades
7. Voltar em Estoque: PAI A = 50, PAI B = 50
8. Logout, login como `gerenteopA@arcos`
9. Sidebar **nao** deve mostrar Transferencias (so admin/geral) nem Modulos
10. Em Requisicoes > Nova: pedir 10 unidades do PAI para a Cozinha A
11. Logout, login como `gerentelogA@arcos`
12. Aprovar a requisicao. Estoque: PAI A = 40, Cozinha A = 10

## 3. Health Checks Operacionais

```bash
# Backend
curl https://seu-dominio.com.br/api/health

# Login basico
curl -X POST https://seu-dominio.com.br/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"master@sconnecta.com.br","password":"Master@2026"}'
```

## 4. Testes de Frontend (Playwright)

O frontend e testado via agente de teste integrado. Para rodar manualmente, instale dependencias e use os data-testid de cada pagina:

Paginas e testids principais:
- `dashboard-layout`, `nav-lojas`, `nav-transferencias`, `nav-modulos`
- `stores-page`, `new-store-btn`, `store-name`, `save-store-btn`
- `transfers-page`, `new-transfer-btn`, `transfer-from`, `transfer-to`, `submit-transfer-btn`
- `modules-page`, `pai-<id>`, `module-<key>`, `save-modules-btn`

## 5. CI/CD sugerido

```yaml
# .github/workflows/test.yml (exemplo)
name: tests
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      mongo:
        image: mongo:7
        ports: [27017:27017]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && uvicorn server:app --port 8001 & sleep 5
        env:
          MONGO_URL: mongodb://localhost:27017
          DB_NAME: gestao_tj_test
          JWT_SECRET: ci-test-secret
      - run: cd backend && pytest tests/ -v
```
