# Manual do Master - Gestao TJ

O **Master** e o super-usuario do SaaS. Visao global, controla tenants e modulos.

## 1. Identidade do Master

- Email: `master@sconnecta.com.br`
- Login com a opcao "Acesso Master" marcada na tela de login
- Nao pertence a nenhum tenant (`tenant_id = ""`)
- Nao tem warehouse vinculado
- Sidebar exibe **"Global (Master)"** ao inves de um estabelecimento

## 2. Como adicionar um novo cliente (Tenant)

1. Menu **Estabelecimentos** -> botao "Novo Estabelecimento"
2. Informe Nome (ex: "Burger Queen") e Slug (ex: "burger-queen", sem espacos)
3. Apos criar, vai pra Usuarios e cadastre o `admin@` do novo tenant (papel: Administrador)
4. O admin recem-criado loga e configura suas Lojas, Depositos, Modulos, etc.

## 3. Como configurar Modulos por Deposito PAI

1. Logue como master ou admin do tenant
2. Menu **Modulos**
3. A esquerda: lista de **Depositos PAI** do(s) tenant(s)
4. A direita: checkbox de cada modulo (Lojas, Produtos, Estoque, Transferencias, etc.)
5. Clique em **Salvar**
6. Usuarios vinculados aquele PAI (ou aos FILHOs dele) terao seus menus filtrados

**Importante**: lista de modulos vazia = todos habilitados (default).
FILHO **herda** os modulos do seu PAI.

## 4. Hierarquia conceitual

```
Tenant (Arcos Dourados)
  |__ Loja/Unidade (Restaurante A)
  |     |__ Deposito PAI (Almoxarifado Rest. A)        <- modulos configurados aqui
  |     |     |__ Deposito FILHO (Cozinha A)
  |     |     |__ Deposito FILHO (Salao A)
  |__ Loja/Unidade (Restaurante B)
        |__ Deposito PAI (Almoxarifado Rest. B)
              |__ Deposito FILHO (Cozinha B)
```

## 5. Como criar Gerente Geral (acesso multi-loja)

1. Menu **Usuarios** > Novo Usuario
2. Selecione papel: **Gerente Geral**
3. Selecione o Estabelecimento
4. Em **"Lojas atribuidas"** (campo store_ids), selecione 1 ou mais lojas
5. Salve. O usuario agora pode transferir produtos entre essas lojas e ver auditoria escopada.

Obs: a UI de edicao de `store_ids` esta acessivel via API; pode ser que a tela ainda use apenas warehouse_id simples — nesse caso, atualize via PATCH /api/users/{id} com payload `{"store_ids": ["id_loja1", "id_loja2"]}`.

## 6. Auditoria global

O master ve **todos** os logs de auditoria de todos os tenants em PT-BR (CRIAR, EDITAR, EXCLUIR, APROVAR, REJEITAR, TRANSFERIR_ENTRE_LOJAS, CONFIGURAR_MODULOS, etc.).
Exporte para Excel via botao "Exportar" na pagina de Auditoria.

## 7. Reset / Reseed em ambiente novo

Apos deploy em um servidor novo, o seed cria os dados iniciais (master + tenants exemplo).
Se `SEED_SECRET` estiver configurado em producao, a requisicao precisa incluir:

```bash
curl -X POST https://seu-dominio.com.br/api/seed -H "X-Seed-Secret: $SEED_SECRET"
```

## 8. Boas praticas

- Troque a senha do master logo no primeiro login
- Configure `JWT_SECRET`, `SEED_SECRET` e `CORS_ORIGINS` em producao
- Faca backup diario do MongoDB (volume `mongo-data`)
- Crie 1 admin por tenant (delegue gestao operacional ao admin)
- Use Modulos para vender planos diferenciados (basico = sem reports/transfers; pro = todos)
