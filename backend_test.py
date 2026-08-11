#!/usr/bin/env python3
"""
Backend test for Master Store Management Permission Bug Fix
Tests the isolated permission bug fix for STORE management in multi-tenant FastAPI SaaS
"""
import requests
import json
from typing import Optional, Dict, Any

# Base URL from frontend/.env
BASE_URL = "https://a4f9812a-7632-49c5-a118-8c7d537f85e9.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
CREDENTIALS = {
    "master": {"identifier": "master@sconnecta.com.br", "password": "Master@2026"},
    "admin": {"identifier": "admin.tj", "password": "Admin@2026"},
    "operacional": {"identifier": "operacional.tj", "password": "Operacional@2026"}
}

class TestSession:
    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.user_info = None
    
    def login(self, identifier: str, password: str) -> bool:
        """Login and store cookies"""
        url = f"{BASE_URL}/auth/login"
        payload = {"identifier": identifier, "password": password}
        try:
            resp = self.session.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.user_info = data.get('user', {})
                print(f"✓ {self.name} login successful: {self.user_info.get('name')} ({self.user_info.get('role')})")
                return True
            else:
                print(f"✗ {self.name} login failed: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            print(f"✗ {self.name} login error: {e}")
            return False
    
    def get(self, endpoint: str) -> requests.Response:
        """GET request with session cookies"""
        return self.session.get(f"{BASE_URL}{endpoint}", timeout=10)
    
    def post(self, endpoint: str, json_data: Dict[Any, Any]) -> requests.Response:
        """POST request with session cookies"""
        return self.session.post(f"{BASE_URL}{endpoint}", json=json_data, timeout=10)
    
    def patch(self, endpoint: str, json_data: Dict[Any, Any]) -> requests.Response:
        """PATCH request with session cookies"""
        return self.session.patch(f"{BASE_URL}{endpoint}", json=json_data, timeout=10)
    
    def delete(self, endpoint: str) -> requests.Response:
        """DELETE request with session cookies"""
        return self.session.delete(f"{BASE_URL}{endpoint}", timeout=10)


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


def print_test(test_num: int, description: str):
    """Print test header"""
    print(f"\n--- TEST {test_num}: {description} ---")


def print_result(status_code: int, expected: int, response_text: str = ""):
    """Print test result with status code"""
    match = "✓ PASS" if status_code == expected else "✗ FAIL"
    print(f"{match} | Status: {status_code} (expected {expected})")
    if response_text:
        try:
            data = json.loads(response_text)
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            print(f"Response: {response_text[:200]}")


def main():
    print_section("MASTER STORE MANAGEMENT PERMISSION BUG FIX - BACKEND TESTS")
    
    # Initialize test sessions
    master_session = TestSession("MASTER")
    admin_session = TestSession("ADMIN")
    operacional_session = TestSession("OPERACIONAL")
    
    # Login all users
    print_section("AUTHENTICATION")
    if not master_session.login(**CREDENTIALS["master"]):
        print("CRITICAL: Master login failed. Cannot proceed.")
        return
    if not admin_session.login(**CREDENTIALS["admin"]):
        print("CRITICAL: Admin login failed. Cannot proceed.")
        return
    if not operacional_session.login(**CREDENTIALS["operacional"]):
        print("CRITICAL: Operacional login failed. Cannot proceed.")
        return
    
    # Get valid tenant_id for master tests
    print_section("SETUP: Get Valid Tenant ID")
    resp = master_session.get("/tenants")
    if resp.status_code != 200:
        print(f"✗ Failed to get tenants: {resp.status_code}")
        return
    
    tenants = resp.json()
    if not tenants:
        print("✗ No tenants found in database")
        return
    
    tenant_id = tenants[0]['id']
    tenant_name = tenants[0]['name']
    print(f"✓ Using tenant: {tenant_name} (id: {tenant_id})")
    
    # Store IDs for cleanup and later tests
    created_store_ids = []
    
    # =========================================================================
    # TEST 1: MASTER CREATE WITH tenant_id (MAIN BUG FIX)
    # =========================================================================
    print_section("TEST SCENARIO 1: MASTER CREATE WITH tenant_id (MAIN BUG)")
    print_test(1, "Master creates store WITH tenant_id query param")
    print(f"Expected: HTTP 200 (previously returned 400 'Master deve criar...')")
    
    store_data = {
        "name": "Loja QA Master",
        "code": "QA-M",
        "address": "Rua X"
    }
    
    resp = master_session.post(f"/stores?tenant_id={tenant_id}", store_data)
    print_result(resp.status_code, 200, resp.text)
    
    if resp.status_code == 200:
        store = resp.json()
        created_store_ids.append(store['id'])
        
        # Verify tenant_id matches
        if store.get('tenant_id') == tenant_id:
            print(f"✓ Store tenant_id matches: {store['tenant_id']}")
        else:
            print(f"✗ Store tenant_id mismatch: got {store.get('tenant_id')}, expected {tenant_id}")
        
        print(f"✓ Store created with id: {store['id']}")
    else:
        print("✗ TEST 1 FAILED: Master could not create store with tenant_id")
    
    # =========================================================================
    # TEST 2: MASTER CREATE WITHOUT tenant_id
    # =========================================================================
    print_section("TEST SCENARIO 2: MASTER CREATE WITHOUT tenant_id")
    print_test(2, "Master creates store WITHOUT tenant_id query param")
    print(f"Expected: HTTP 400 with message asking for tenant_id")
    
    store_data_no_tenant = {
        "name": "Loja Sem Tenant"
    }
    
    resp = master_session.post("/stores", store_data_no_tenant)
    print_result(resp.status_code, 400, resp.text)
    
    if resp.status_code == 400:
        response_data = resp.json()
        if "tenant_id" in response_data.get('detail', '').lower():
            print("✓ Error message correctly asks for tenant_id")
        else:
            print(f"⚠ Error message doesn't mention tenant_id: {response_data.get('detail')}")
    
    # =========================================================================
    # TEST 3: MASTER EDIT
    # =========================================================================
    print_section("TEST SCENARIO 3: MASTER EDIT")
    print_test(3, "Master edits existing store")
    print(f"Expected: HTTP 200")
    
    if not created_store_ids:
        print("✗ No store available to edit (TEST 1 failed)")
    else:
        store_id = created_store_ids[0]
        edit_data = {"name": "Loja QA Editada"}
        
        resp = master_session.patch(f"/stores/{store_id}", edit_data)
        print_result(resp.status_code, 200, resp.text)
        
        if resp.status_code == 200:
            # Verify the name changed
            resp_get = master_session.get("/stores")
            if resp_get.status_code == 200:
                stores = resp_get.json()
                edited_store = next((s for s in stores if s['id'] == store_id), None)
                if edited_store and edited_store['name'] == "Loja QA Editada":
                    print(f"✓ Store name successfully changed to: {edited_store['name']}")
                else:
                    print(f"⚠ Store name not verified in GET /stores")
    
    # =========================================================================
    # TEST 4: MASTER DELETE
    # =========================================================================
    print_section("TEST SCENARIO 4: MASTER DELETE")
    print_test(4, "Master deletes store (no active warehouses)")
    print(f"Expected: HTTP 200")
    
    # Create a new store specifically for deletion
    store_data_delete = {
        "name": "Loja Para Excluir",
        "code": "QA-DEL"
    }
    
    resp = master_session.post(f"/stores?tenant_id={tenant_id}", store_data_delete)
    if resp.status_code == 200:
        delete_store_id = resp.json()['id']
        print(f"✓ Created store for deletion: {delete_store_id}")
        
        # Ensure no active warehouses (check first)
        resp_wh = master_session.get("/warehouses")
        if resp_wh.status_code == 200:
            warehouses = resp_wh.json()
            active_wh = [w for w in warehouses if w.get('store_id') == delete_store_id and w.get('active')]
            if active_wh:
                print(f"⚠ Store has {len(active_wh)} active warehouse(s), cannot delete")
            else:
                print(f"✓ Store has no active warehouses, proceeding with delete")
                
                resp = master_session.delete(f"/stores/{delete_store_id}")
                print_result(resp.status_code, 200, resp.text)
    else:
        print(f"✗ Could not create store for deletion: {resp.status_code}")
    
    # =========================================================================
    # TEST 5: ADMIN REGRESSION
    # =========================================================================
    print_section("TEST SCENARIO 5: ADMIN REGRESSION")
    print_test(5, "Admin creates/edits/deletes store (no tenant_id query)")
    print(f"Expected: HTTP 200 for all operations")
    
    # Admin POST (no tenant_id query - should use admin's own tenant)
    admin_store_data = {
        "name": "Loja Admin",
        "code": "ADMIN-1"
    }
    
    print("\n5a. Admin POST /stores (no tenant_id query):")
    resp = admin_session.post("/stores", admin_store_data)
    print_result(resp.status_code, 200, resp.text)
    
    admin_store_id = None
    if resp.status_code == 200:
        admin_store = resp.json()
        admin_store_id = admin_store['id']
        admin_tenant = admin_store.get('tenant_id')
        print(f"✓ Store created in admin's tenant: {admin_tenant}")
        
        # Admin PATCH
        print("\n5b. Admin PATCH /stores/{id}:")
        resp = admin_session.patch(f"/stores/{admin_store_id}", {"name": "Loja Admin Editada"})
        print_result(resp.status_code, 200, resp.text)
        
        # Admin DELETE
        print("\n5c. Admin DELETE /stores/{id}:")
        resp = admin_session.delete(f"/stores/{admin_store_id}")
        print_result(resp.status_code, 200, resp.text)
    else:
        print("✗ Admin POST failed, skipping PATCH/DELETE tests")
    
    # =========================================================================
    # TEST 6: RBAC NEGATIVE (Operacional should be blocked)
    # =========================================================================
    print_section("TEST SCENARIO 6: RBAC NEGATIVE (Operacional)")
    print_test(6, "Operacional attempts POST/PATCH/DELETE")
    print(f"Expected: HTTP 403 for all three operations")
    
    # Operacional POST
    print("\n6a. Operacional POST /stores:")
    resp = operacional_session.post("/stores", {"name": "X"})
    print_result(resp.status_code, 403, resp.text)
    
    # Operacional PATCH (use any existing store)
    print("\n6b. Operacional PATCH /stores/{any}:")
    if created_store_ids:
        resp = operacional_session.patch(f"/stores/{created_store_ids[0]}", {"name": "Y"})
        print_result(resp.status_code, 403, resp.text)
    else:
        print("⚠ No store available for PATCH test")
    
    # Operacional DELETE
    print("\n6c. Operacional DELETE /stores/{any}:")
    if created_store_ids:
        resp = operacional_session.delete(f"/stores/{created_store_ids[0]}")
        print_result(resp.status_code, 403, resp.text)
    else:
        print("⚠ No store available for DELETE test")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_section("TEST SUMMARY")
    print("""
Test Scenarios:
1. MASTER CREATE with tenant_id     - Main bug fix (previously 400, now 200)
2. MASTER CREATE without tenant_id  - Expected 400 (validation)
3. MASTER EDIT                       - Expected 200
4. MASTER EDIT                       - Expected 200
5. ADMIN REGRESSION (POST/PATCH/DEL) - Expected 200 for all
6. RBAC NEGATIVE (Operacional)       - Expected 403 for all

Review the detailed results above for exact HTTP status codes.
    """)
    
    print("\nTest execution completed.")


if __name__ == "__main__":
    main()
