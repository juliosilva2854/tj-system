"""
End-to-end backend tests for Gestao TJ SaaS Multi-Tenant.
Covers: auth, RBAC, multi-tenant isolation (IDOR), warehouses (PAI/FILHO),
requisitions flow, suppliers, invoices, dashboard, reports, audit, validation.
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tj-auditoria.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

MASTER = ("master@sconnecta.com.br", "Master@2026")
ADMIN_TJ = ("admin@tj.sconnecta.com.br", "Admin@2026")
LOG_TJ = ("logistica@tj.sconnecta.com.br", "Logistica@2026")
OP_TJ = ("operacional@tj.sconnecta.com.br", "Operacional@2026")


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password})
    if r.status_code == 429:
        time.sleep(62)
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": password})
    return r


def _hdr(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session", autouse=True)
def seed_once():
    requests.post(f"{API}/seed")
    yield


@pytest.fixture(scope="session")
def tokens():
    t = {}
    for k, (e, p) in {"master": MASTER, "admin": ADMIN_TJ, "log": LOG_TJ, "op": OP_TJ}.items():
        r = _login(e, p)
        assert r.status_code == 200, f"Login {k} failed: {r.status_code} {r.text}"
        t[k] = r.json()["access_token"]
        t[f"{k}_user"] = r.json()["user"]
    return t


# ============ AUTH / SEED ============
class TestAuth:
    def test_seed_idempotent(self):
        r = requests.post(f"{API}/seed")
        assert r.status_code == 200
        assert "message" in r.json()

    def test_login_invalid(self):
        r = _login("nobody@x.com", "wrong")
        assert r.status_code == 401

    def test_login_all_roles(self, tokens):
        for k in ["master", "admin", "log", "op"]:
            assert tokens[k]
        assert tokens["master_user"]["role"] == "master"
        assert tokens["admin_user"]["role"] == "admin"
        assert tokens["log_user"]["role"] == "logistica"
        assert tokens["op_user"]["role"] == "operacional"
        # warehouse_id present for op/log
        assert tokens["op_user"].get("warehouse_id")
        assert tokens["log_user"].get("warehouse_id")

    def test_auth_me(self, tokens):
        r = requests.get(f"{API}/auth/me", headers=_hdr(tokens["op"]))
        assert r.status_code == 200
        d = r.json()
        assert d["email"] == OP_TJ[0]
        assert "tenant_name" in d
        assert "warehouse_name" in d
        assert d["tenant_name"] == "Unidade TJ"
        assert "password_hash" not in d
        assert "_id" not in d

    def test_auth_refresh(self):
        r = _login(*ADMIN_TJ)
        refresh = r.json()["refresh_token"]
        r2 = requests.post(f"{API}/auth/refresh", json={"refresh_token": refresh})
        assert r2.status_code == 200
        assert "access_token" in r2.json()

    def test_auth_no_token(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_validation_email_invalid(self, tokens):
        # admin attempts to register invalid email
        r = requests.post(f"{API}/auth/register", headers=_hdr(tokens["admin"]),
                          json={"email": "not-an-email", "name": "X", "password": "abcdef", "role": "operacional",
                                "warehouse_id": tokens["op_user"]["warehouse_id"]})
        assert r.status_code == 422

    def test_validation_password_short(self, tokens):
        r = requests.post(f"{API}/auth/register", headers=_hdr(tokens["admin"]),
                          json={"email": f"x{uuid.uuid4().hex[:6]}@a.com", "name": "X", "password": "123",
                                "role": "operacional"})
        assert r.status_code == 422


# ============ RBAC ============
class TestRBAC:
    def test_tenants_master_only(self, tokens):
        assert requests.get(f"{API}/tenants", headers=_hdr(tokens["master"])).status_code == 200
        assert requests.get(f"{API}/tenants", headers=_hdr(tokens["admin"])).status_code == 403
        assert requests.get(f"{API}/tenants", headers=_hdr(tokens["log"])).status_code == 403
        assert requests.get(f"{API}/tenants", headers=_hdr(tokens["op"])).status_code == 403

    def test_users_admin_sees_own_tenant(self, tokens):
        r_master = requests.get(f"{API}/users", headers=_hdr(tokens["master"]))
        r_admin = requests.get(f"{API}/users", headers=_hdr(tokens["admin"]))
        assert r_master.status_code == 200 and r_admin.status_code == 200
        admin_tid = tokens["admin_user"]["tenant_id"]
        # All admin users should be of admin's tenant
        for u in r_admin.json():
            assert u["tenant_id"] == admin_tid
        # master sees >= admin count
        assert len(r_master.json()) >= len(r_admin.json())

    def test_users_op_forbidden(self, tokens):
        assert requests.get(f"{API}/users", headers=_hdr(tokens["op"])).status_code == 403


# ============ MULTI-TENANT IDOR ============
@pytest.fixture(scope="session")
def second_tenant(tokens):
    """Create a second tenant + admin via master, for isolation tests."""
    slug = f"acme{uuid.uuid4().hex[:6]}"
    r = requests.post(f"{API}/tenants", headers=_hdr(tokens["master"]),
                      json={"name": "ACME Test", "slug": slug})
    assert r.status_code == 200, r.text
    tid = r.json()["id"]
    email = f"admin_{slug}@acme.com"
    r2 = requests.post(f"{API}/auth/register", headers=_hdr(tokens["master"]),
                       json={"email": email, "name": "Admin ACME", "password": "Acme@2026",
                             "role": "admin", "tenant_id": tid})
    assert r2.status_code == 200, r2.text
    login = _login(email, "Acme@2026")
    assert login.status_code == 200
    return {"tenant_id": tid, "admin_token": login.json()["access_token"],
            "admin_user": login.json()["user"]}


class TestIsolation:
    def test_create_second_tenant(self, second_tenant):
        assert second_tenant["tenant_id"]

    def test_warehouses_isolated(self, tokens, second_tenant):
        admin_a_whs = requests.get(f"{API}/warehouses", headers=_hdr(tokens["admin"])).json()
        admin_b_whs = requests.get(f"{API}/warehouses",
                                   headers=_hdr(second_tenant["admin_token"])).json()
        for w in admin_a_whs:
            assert w["tenant_id"] == tokens["admin_user"]["tenant_id"]
        for w in admin_b_whs:
            assert w["tenant_id"] == second_tenant["tenant_id"]
        # Admin B should not see TJ warehouses
        tj_ids = {w["id"] for w in admin_a_whs}
        b_ids = {w["id"] for w in admin_b_whs}
        assert tj_ids.isdisjoint(b_ids)

    def test_products_isolated(self, tokens, second_tenant):
        # Create a TEST_ product in tenant A
        p = requests.post(f"{API}/products", headers=_hdr(tokens["admin"]),
                          json={"name": "TEST_ProdA", "sku": f"TESTA{uuid.uuid4().hex[:6]}"})
        assert p.status_code == 200, p.text
        a_list = requests.get(f"{API}/products", headers=_hdr(tokens["admin"])).json()
        b_list = requests.get(f"{API}/products", headers=_hdr(second_tenant["admin_token"])).json()
        a_ids = {x["id"] for x in a_list}
        b_ids = {x["id"] for x in b_list}
        assert p.json()["id"] in a_ids
        assert p.json()["id"] not in b_ids


# ============ WAREHOUSES ============
class TestWarehouses:
    def test_op_sees_only_own(self, tokens):
        r = requests.get(f"{API}/warehouses", headers=_hdr(tokens["op"]))
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == tokens["op_user"]["warehouse_id"]
        assert data[0]["type"] == "filho"

    def test_filho_requires_parent(self, tokens):
        # admin creates a filho without parent_id
        r = requests.post(f"{API}/warehouses", headers=_hdr(tokens["admin"]),
                          json={"name": "TEST_FilhoSemPai", "location": "X", "type": "filho", "sectors": []})
        assert r.status_code == 400

    def test_master_cannot_create_warehouse(self, tokens):
        r = requests.post(f"{API}/warehouses", headers=_hdr(tokens["master"]),
                          json={"name": "TEST_W", "location": "x", "type": "pai", "sectors": []})
        assert r.status_code == 403


# ============ REQUISITIONS FLOW ============
@pytest.fixture(scope="session")
def stocked_product(tokens):
    """Create a product, populate PAI inventory."""
    sku = f"REQ{uuid.uuid4().hex[:6]}"
    p = requests.post(f"{API}/products", headers=_hdr(tokens["admin"]),
                      json={"name": "TEST_ReqProd", "sku": sku, "cost_price": 10, "min_stock": 1})
    assert p.status_code == 200, p.text
    pid = p.json()["id"]
    pai_id = tokens["log_user"]["warehouse_id"]
    # Adjust PAI inventory directly to 50 (use logistica)
    r = requests.post(f"{API}/inventory/adjust",
                      params={"product_id": pid, "warehouse_id": pai_id, "quantity": 50},
                      headers=_hdr(tokens["log"]))
    assert r.status_code == 200, r.text
    return {"product_id": pid, "pai_id": pai_id}


class TestRequisitions:
    def test_op_create_requisition(self, tokens, stocked_product):
        r = requests.post(f"{API}/requisitions", headers=_hdr(tokens["op"]),
                          json={"items": [{"product_id": stocked_product["product_id"],
                                           "product_name": "TEST_ReqProd", "quantity": 5}],
                                "notes": "TEST_req"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "pending"
        assert r.json()["from_warehouse_id"] == tokens["op_user"]["warehouse_id"]
        assert r.json()["to_warehouse_id"] == stocked_product["pai_id"]

    def test_logistica_user_cant_create_requisition(self, tokens):
        # log is bound to PAI; should fail because not filho
        r = requests.post(f"{API}/requisitions", headers=_hdr(tokens["log"]),
                          json={"items": [{"product_id": "x", "product_name": "x", "quantity": 1}]})
        assert r.status_code == 400

    def test_op_cannot_approve(self, tokens, stocked_product):
        # create one
        r = requests.post(f"{API}/requisitions", headers=_hdr(tokens["op"]),
                          json={"items": [{"product_id": stocked_product["product_id"],
                                           "product_name": "TEST_ReqProd", "quantity": 2}]})
        rid = r.json()["id"]
        # op tries to approve
        r2 = requests.post(f"{API}/requisitions/{rid}/approve", headers=_hdr(tokens["op"]))
        assert r2.status_code == 403

    def test_logistica_approve_transfers_stock(self, tokens, stocked_product):
        # New requisition for 3 units
        r = requests.post(f"{API}/requisitions", headers=_hdr(tokens["op"]),
                          json={"items": [{"product_id": stocked_product["product_id"],
                                           "product_name": "TEST_ReqProd", "quantity": 3}]})
        rid = r.json()["id"]
        # PAI inv before
        inv_pai_before = next((i for i in requests.get(f"{API}/inventory",
                                                       headers=_hdr(tokens["log"])).json()
                               if i["product_id"] == stocked_product["product_id"]), None)
        assert inv_pai_before is not None
        before_qty = inv_pai_before["quantity"]
        # approve
        ap = requests.post(f"{API}/requisitions/{rid}/approve", headers=_hdr(tokens["log"]))
        assert ap.status_code == 200, ap.text
        # PAI inv after
        inv_after = requests.get(f"{API}/inventory", headers=_hdr(tokens["admin"])).json()
        pai_qty = next((i["quantity"] for i in inv_after
                        if i["product_id"] == stocked_product["product_id"]
                        and i["warehouse_id"] == stocked_product["pai_id"]), None)
        filho_qty = next((i["quantity"] for i in inv_after
                          if i["product_id"] == stocked_product["product_id"]
                          and i["warehouse_id"] == tokens["op_user"]["warehouse_id"]), 0)
        assert pai_qty == before_qty - 3
        assert filho_qty >= 3

    def test_approve_insufficient_stock(self, tokens, stocked_product):
        r = requests.post(f"{API}/requisitions", headers=_hdr(tokens["op"]),
                          json={"items": [{"product_id": stocked_product["product_id"],
                                           "product_name": "TEST_ReqProd", "quantity": 99999}]})
        rid = r.json()["id"]
        ap = requests.post(f"{API}/requisitions/{rid}/approve", headers=_hdr(tokens["log"]))
        assert ap.status_code == 400
        assert "insuficiente" in ap.json().get("detail", "").lower()

    def test_reject_requisition(self, tokens, stocked_product):
        r = requests.post(f"{API}/requisitions", headers=_hdr(tokens["op"]),
                          json={"items": [{"product_id": stocked_product["product_id"],
                                           "product_name": "TEST_ReqProd", "quantity": 1}]})
        rid = r.json()["id"]
        rj = requests.post(f"{API}/requisitions/{rid}/reject", headers=_hdr(tokens["admin"]))
        assert rj.status_code == 200

    def test_idor_requisition_cross_tenant(self, tokens, second_tenant, stocked_product):
        # Get a TJ requisition
        my_reqs = requests.get(f"{API}/requisitions", headers=_hdr(tokens["op"])).json()
        if my_reqs:
            rid = my_reqs[0]["id"]
            # Tenant B admin tries to approve TJ requisition
            r = requests.post(f"{API}/requisitions/{rid}/approve",
                              headers=_hdr(second_tenant["admin_token"]))
            assert r.status_code == 403


# ============ SUPPLIERS / INVOICES / DASHBOARD ============
class TestSuppliersInvoices:
    def test_supplier_crud_and_isolation(self, tokens, second_tenant):
        s = requests.post(f"{API}/suppliers", headers=_hdr(tokens["admin"]),
                          json={"name": "TEST_Sup", "cnpj": "00.000.000/0001-00"})
        assert s.status_code == 200, s.text
        sid = s.json()["id"]
        a_list = requests.get(f"{API}/suppliers", headers=_hdr(tokens["admin"])).json()
        b_list = requests.get(f"{API}/suppliers",
                              headers=_hdr(second_tenant["admin_token"])).json()
        assert any(x["id"] == sid for x in a_list)
        assert not any(x["id"] == sid for x in b_list)

    def test_invoice_create_and_process(self, tokens):
        sku = f"INV{uuid.uuid4().hex[:6]}"
        inv = requests.post(f"{API}/invoices", headers=_hdr(tokens["log"]),
                            json={"invoice_number": f"NF{uuid.uuid4().hex[:6]}",
                                  "supplier_name": "TEST_FORN", "issue_date": "2026-01-01",
                                  "total_value": 100, "tax_value": 0,
                                  "items": [{"product_name": "TEST_InvProd", "product_sku": sku,
                                             "quantity": 10, "unit_price": 10, "total": 100}]})
        assert inv.status_code == 200, inv.text
        iid = inv.json()["id"]
        proc = requests.post(f"{API}/invoices/{iid}/process-items", headers=_hdr(tokens["log"]))
        assert proc.status_code == 200, proc.text
        # Product was created with available_qty
        prods = requests.get(f"{API}/products", headers=_hdr(tokens["log"])).json()
        found = next((p for p in prods if p["sku"] == sku), None)
        assert found is not None
        assert found["available_qty"] >= 10


class TestDashboardReports:
    def test_dashboard_stats(self, tokens):
        r = requests.get(f"{API}/dashboard/stats", headers=_hdr(tokens["admin"]))
        assert r.status_code == 200
        d = r.json()
        for k in ["total_products", "total_warehouses", "pending_requisitions", "low_stock_alerts"]:
            assert k in d

    def test_reports_rbac(self, tokens):
        # admin allowed
        r = requests.get(f"{API}/reports/financial?period=month", headers=_hdr(tokens["admin"]))
        assert r.status_code == 200
        # logistica forbidden
        r2 = requests.get(f"{API}/reports/financial?period=month", headers=_hdr(tokens["log"]))
        assert r2.status_code == 403
        r3 = requests.get(f"{API}/reports/abc-curve", headers=_hdr(tokens["admin"]))
        assert r3.status_code == 200
        r4 = requests.get(f"{API}/reports/inventory-turnover", headers=_hdr(tokens["admin"]))
        assert r4.status_code == 200

    def test_audit_logs_pt(self, tokens):
        r = requests.get(f"{API}/audit", headers=_hdr(tokens["admin"]))
        assert r.status_code == 200
        logs = r.json()
        admin_tid = tokens["admin_user"]["tenant_id"]
        # Tenant-filtered
        for log in logs:
            assert log.get("tenant_id", "") == admin_tid or log.get("tenant_id", "") == ""
        # Pt actions appear if there are logs
        if logs:
            actions = {l.get("action") for l in logs}
            pt_actions = {"CRIAR", "EDITAR", "APROVAR", "AJUSTAR", "TRANSFERIR", "PROCESSAR"}
            assert actions & pt_actions, f"No PT actions found in {actions}"


# ============ VALIDATION / SANITIZE ============
class TestValidation:
    def test_sanitize_strips_special_chars(self, tokens):
        r = requests.post(f"{API}/products", headers=_hdr(tokens["admin"]),
                          json={"name": "TEST_<script>X</script>", "sku": f"SAN{uuid.uuid4().hex[:6]}"})
        assert r.status_code == 200, r.text
        assert "<" not in r.json()["name"]
        assert ">" not in r.json()["name"]

    def test_duplicate_email_register(self, tokens):
        r = requests.post(f"{API}/auth/register", headers=_hdr(tokens["admin"]),
                          json={"email": OP_TJ[0], "name": "dup", "password": "abcdef",
                                "role": "operacional",
                                "warehouse_id": tokens["op_user"]["warehouse_id"]})
        assert r.status_code == 400

    def test_operacional_requires_warehouse(self, tokens):
        r = requests.post(f"{API}/auth/register", headers=_hdr(tokens["admin"]),
                          json={"email": f"opx{uuid.uuid4().hex[:6]}@x.com", "name": "Operacional Test",
                                "password": "abcdef", "role": "operacional"})
        assert r.status_code == 400
