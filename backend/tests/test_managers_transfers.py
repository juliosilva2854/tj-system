"""Tests novos para multi-loja, gerentes, transferencias entre lojas e modulos.

Roda contra o tenant Arcos Dourados criado pelo seed.
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN_ARCOS = ("admin@arcos.sconnecta.com.br", "Admin@2026")
GERENTE_GERAL = ("gerentegeral@arcos.sconnecta.com.br", "GerenteGeral@2026")
GERENTE_LOG_A = ("gerentelogA@arcos.sconnecta.com.br", "GerenteLog@2026")
GERENTE_OP_A = ("gerenteopA@arcos.sconnecta.com.br", "GerenteOp@2026")
MASTER = ("master@sconnecta.com.br", "Master@2026")


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password})
    if r.status_code == 429:
        time.sleep(62)
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": password})
    return r


def _hdr(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module", autouse=True)
def seed_once():
    requests.post(f"{API}/seed")
    yield


@pytest.fixture(scope="module")
def t():
    out = {}
    for k, (e, p) in {
        "master": MASTER, "admin": ADMIN_ARCOS, "ger": GERENTE_GERAL,
        "log": GERENTE_LOG_A, "op": GERENTE_OP_A,
    }.items():
        r = _login(e, p)
        assert r.status_code == 200, f"login {k} {r.text}"
        out[k] = r.json()["access_token"]
        out[f"{k}_u"] = r.json()["user"]
    return out


class TestStoresAndManagers:
    def test_manager_roles_loaded(self, t):
        assert t["ger_u"]["role"] == "gerente_geral"
        assert t["log_u"]["role"] == "gerente_logistica"
        assert t["op_u"]["role"] == "gerente_operacional"
        # Gerente geral tem 2 stores
        assert len(t["ger_u"].get("store_ids") or []) == 2
        # Gerente logistica tem 1 store + 1 warehouse
        assert len(t["log_u"].get("warehouse_ids") or []) >= 1
        # Gerente operacional tem 2 warehouses (FILHOs)
        assert len(t["op_u"].get("warehouse_ids") or []) == 2

    def test_list_stores_filtered_by_scope(self, t):
        # Admin Arcos ve as 2 lojas
        r = requests.get(f"{API}/stores", headers=_hdr(t["admin"]))
        assert r.status_code == 200
        assert len(r.json()) == 2
        # Gerente Geral tambem ve 2
        r = requests.get(f"{API}/stores", headers=_hdr(t["ger"]))
        assert len(r.json()) == 2
        # Gerente Logistica A ve apenas 1
        r = requests.get(f"{API}/stores", headers=_hdr(t["log"]))
        assert len(r.json()) == 1

    def test_create_and_delete_store(self, t):
        slug = f"loja-{uuid.uuid4().hex[:6]}"
        r = requests.post(f"{API}/stores", headers=_hdr(t["admin"]),
                          json={"name": f"Loja Teste {slug}", "code": slug.upper(), "address": "Rua X"})
        assert r.status_code == 200, r.text
        sid = r.json()["id"]
        r = requests.delete(f"{API}/stores/{sid}", headers=_hdr(t["admin"]))
        assert r.status_code == 200

    def test_op_cannot_create_store(self, t):
        r = requests.post(f"{API}/stores", headers=_hdr(t["op"]),
                          json={"name": "Loja Hack"})
        assert r.status_code == 403


@pytest.fixture(scope="module")
def warehouses(t):
    r = requests.get(f"{API}/warehouses", headers=_hdr(t["admin"]))
    assert r.status_code == 200
    whs = r.json()
    return {
        "pai_a": next(w for w in whs if w["name"] == "Almoxarifado Rest. A"),
        "pai_b": next(w for w in whs if w["name"] == "Almoxarifado Rest. B"),
        "cozinha_a": next(w for w in whs if w["name"] == "Cozinha A"),
    }


@pytest.fixture(scope="module")
def stocked_product_arcos(t, warehouses):
    sku = f"TEST{uuid.uuid4().hex[:8].upper()}"
    r = requests.post(f"{API}/products", headers=_hdr(t["admin"]),
                      json={"name": "Hamburguer Test", "sku": sku, "unit": "UN",
                            "cost_price": 2.0, "min_stock": 5})
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    # Injeta 100 unidades no PAI A via inventory/adjust
    r = requests.post(f"{API}/inventory/adjust", headers=_hdr(t["admin"]),
                      params={"product_id": pid, "warehouse_id": warehouses["pai_a"]["id"], "quantity": 100})
    assert r.status_code == 200, r.text
    return {"id": pid, "name": "Hamburguer Test"}


class TestTransfersBetweenStores:
    def test_gerente_geral_can_transfer(self, t, warehouses, stocked_product_arcos):
        body = {
            "from_warehouse_id": warehouses["pai_a"]["id"],
            "to_warehouse_id": warehouses["pai_b"]["id"],
            "items": [{"product_id": stocked_product_arcos["id"],
                       "product_name": stocked_product_arcos["name"], "quantity": 20}],
            "notes": "Reabastecer loja B"
        }
        r = requests.post(f"{API}/transfers", headers=_hdr(t["ger"]), json=body)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "completed"
        assert r.json()["from_store_id"]
        assert r.json()["to_store_id"]

    def test_operacional_cannot_transfer(self, t, warehouses, stocked_product_arcos):
        body = {
            "from_warehouse_id": warehouses["pai_a"]["id"],
            "to_warehouse_id": warehouses["pai_b"]["id"],
            "items": [{"product_id": stocked_product_arcos["id"],
                       "product_name": stocked_product_arcos["name"], "quantity": 1}]
        }
        r = requests.post(f"{API}/transfers", headers=_hdr(t["op"]), json=body)
        assert r.status_code == 403

    def test_transfer_blocks_filho(self, t, warehouses, stocked_product_arcos):
        # transferencia so entre PAIs
        body = {
            "from_warehouse_id": warehouses["pai_a"]["id"],
            "to_warehouse_id": warehouses["cozinha_a"]["id"],
            "items": [{"product_id": stocked_product_arcos["id"],
                       "product_name": "x", "quantity": 1}]
        }
        r = requests.post(f"{API}/transfers", headers=_hdr(t["admin"]), json=body)
        assert r.status_code == 400

    def test_transfer_insufficient_stock(self, t, warehouses, stocked_product_arcos):
        body = {
            "from_warehouse_id": warehouses["pai_a"]["id"],
            "to_warehouse_id": warehouses["pai_b"]["id"],
            "items": [{"product_id": stocked_product_arcos["id"],
                       "product_name": "x", "quantity": 999999}]
        }
        r = requests.post(f"{API}/transfers", headers=_hdr(t["ger"]), json=body)
        assert r.status_code == 400

    def test_list_transfers_scoped(self, t):
        # Gerente Operacional A nao tem acesso a PAI A => lista vazia (ou apenas seus FILHOs)
        r = requests.get(f"{API}/transfers", headers=_hdr(t["op"]))
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        # Gerente Geral ve as transferencias entre A e B
        r = requests.get(f"{API}/transfers", headers=_hdr(t["ger"]))
        assert r.status_code == 200
        assert any(tr["from_store_id"] and tr["to_store_id"] for tr in r.json())


class TestModulesConfig:
    def test_list_all_modules(self, t):
        r = requests.get(f"{API}/modules", headers=_hdr(t["admin"]))
        assert r.status_code == 200
        assert "products" in r.json()["modules"]
        assert "transfers" in r.json()["modules"]

    def test_my_modules_admin_has_all(self, t):
        r = requests.get(f"{API}/modules/me", headers=_hdr(t["admin"]))
        assert r.status_code == 200
        assert "transfers" in r.json()["enabled_modules"]

    def test_disable_module_on_pai(self, t, warehouses):
        wid = warehouses["pai_b"]["id"]
        # Disable 'sales' on PAI B
        r = requests.put(f"{API}/warehouses/{wid}/modules", headers=_hdr(t["admin"]),
                         json={"enabled_modules": ["dashboard", "products", "inventory",
                                                    "warehouses", "stores", "audit", "guide"]})
        assert r.status_code == 200
        # Gerente Logistica A nao e afetado (PAI A nao mudou)
        # Tem que reabilitar tudo no PAI B para nao deixar lixo
        r2 = requests.put(f"{API}/warehouses/{wid}/modules", headers=_hdr(t["admin"]),
                          json={"enabled_modules": [
                              "dashboard", "stores", "warehouses", "products", "inventory",
                              "requisitions", "transfers", "invoices", "suppliers",
                              "sales", "reports", "alerts", "audit", "users", "guide"
                          ]})
        assert r2.status_code == 200

    def test_cannot_set_modules_on_filho(self, t, warehouses):
        wid = warehouses["cozinha_a"]["id"]
        r = requests.put(f"{API}/warehouses/{wid}/modules", headers=_hdr(t["admin"]),
                         json={"enabled_modules": ["dashboard"]})
        assert r.status_code == 400

    def test_invalid_module_rejected(self, t, warehouses):
        wid = warehouses["pai_a"]["id"]
        r = requests.put(f"{API}/warehouses/{wid}/modules", headers=_hdr(t["admin"]),
                         json={"enabled_modules": ["dashboard", "modulo_inexistente"]})
        assert r.status_code == 422


class TestAuditScopedToManagers:
    def test_gerente_log_sees_audit_for_pai(self, t):
        r = requests.get(f"{API}/audit", headers=_hdr(t["log"]))
        assert r.status_code == 200
        logs = r.json()
        # Devem ser logs do tenant arcos apenas
        for log in logs:
            assert log["tenant_id"] == t["log_u"]["tenant_id"] or log["tenant_id"] == ""

    def test_operacional_can_view_audit(self, t):
        # operacional agora ve audit (escopado)
        r = requests.get(f"{API}/audit", headers=_hdr(t["op"]))
        assert r.status_code == 200
