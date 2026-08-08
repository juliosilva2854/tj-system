# Gestao TJ - PRD

## Stack
- Backend: FastAPI + MongoDB (motor) + JWT em cookies httpOnly
- Frontend: React + Tailwind + Shadcn/UI + Axios (withCredentials)
- Email: Gmail SMTP
- Hosting alvo: Cloudflare Pages (frontend) + Railway (backend) + MongoDB Atlas; dominio sconnecta.com.br

## Auth (apos Fase 1 - cookie HttpOnly)
- POST /api/auth/login retorna apenas {user} no body; tokens vao em cookies HttpOnly access_token (1h) e refresh_token (7d)
- backend/deps.py aceita JWT via cookie httpOnly OU Authorization Bearer header (fallback p/ integracoes)
- _cookie_kwargs() em routers/auth.py adapta SameSite/Secure via env (COOKIE_SAMESITE, COOKIE_SECURE)
- POST /api/auth/refresh aceita refresh_token via cookie ou body, re-emite cookie
- POST /api/auth/logout limpa cookies (Max-Age=0)
- CORS_ORIGINS lido do .env com strip() e fallback http://localhost:3000

## Implementado
- Login JWT dual: username (usuarios normais) ou email (master/admin via subdomain administrator.*)
- Roles hierarquicas: master, admin, gerente_geral, gerente_logistica, gerente_operacional, logistica, operacional
- Dashboard responsivo (Master vs Normal)
- Profile: foto (Pillow compression), CPF, telefone, mudanca de senha
- Recuperacao de senha por email (Gmail SMTP, token 1h)
- Produtos, Depositos, Estoque (com setor), Fornecedores, Transferencias, Requisicoes
- Notas Fiscais: Upload PDF/XML + OCR/IA, processar itens automaticamente
- Relatorios: DRE + Curva ABC + Giro de Estoque + Export PDF/Excel
- Auditoria: filtros + Export Excel
- Alertas: caixa de entrada + canais + estoque minimo
- Usuarios: CRUD com CPF/telefone/username
- Multi-tenant SaaS com Lojas/Depositos/Modulos por tenant
- Mobile responsivo
- I18N PT-BR
- Documentacao: /app/QUICKSTART.md /app/LOCAL_SETUP.md /app/CLOUDFLARE_SETUP.md /app/DEPLOY.md /app/DEPLOY_CHECKLIST.md /app/PRODUCTION.md /app/DEPLOY_PRODUCAO_SCONNECTA.md

## Testes
- /app/backend/tests/test_cookie_auth.py (10/10 pytest cookies, header fallback, refresh, logout)
- /app/backend/tests/test_multitenant_saas.py (regression suite, ainda passa apos migracao)
- Cobertura E2E (testing_agent_v3_fork iter_6): 100% backend + 100% frontend

## Proximos passos (P1)
- [Code Quality Report - restante]
  - Comparacoes `is` vs `==` em literais string: nfe_parser.py, dashboard.py, inventory.py, permissions.py
  - React Hooks deps faltando: use-toast.js, UsersPage.js, TransfersPage.js, RequisitionsPage.js, ProductsPage.js, WarehousesPage.js, SuppliersPage.js
  - Catch blocks vazios: AlertsPage.js:29, App.js:28 (DashboardLayout ja resolvido)

## Backlog (P2)
- Refactor de complexidade: auth.py:register, transfers.py:create_transfer, seed.py:seed, UsersPage.js, ProfilePage.js
- Type hints em Python (server.py, nfe_parser.py, models.py)
- Array index as key em React (ReportsPage, RequisitionsPage)
- Backup automatico MongoDB
- Cloudflare Page Rules + WAF

## Status atual
- Auth HttpOnly cookie: implementado e testado (100%)
- Sistema funcional em preview: https://modules-access-1.preview.emergentagent.com
- Pronto para deploy em sconnecta.com.br
