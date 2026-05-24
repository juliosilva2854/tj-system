#!/usr/bin/env python3
"""
Manual verification tests for Gestao TJ SaaS backend refactoring.
Tests against public URL with all 8 seeded users.
"""
import os
import json
import requests
from typing import Dict, Any

BASE_URL = "https://estoque-api.preview.emergentagent.com"
API = f"{BASE_URL}/api"

# Test credentials from /app/memory/test_credentials.md
CREDENTIALS = {
    "master": ("master@sconnecta.com.br", "Master@2026"),
    "admin_tj": ("admin@tj.sconnecta.com.br", "Admin@2026"),
    "log_tj": ("logistica@tj.sconnecta.com.br", "Logistica@2026"),
    "op_tj": ("operacional@tj.sconnecta.com.br", "Operacional@2026"),
    "admin_arcos": ("admin@arcos.sconnecta.com.br", "Admin@2026"),
    "gerente_geral": ("gerentegeral@arcos.sconnecta.com.br", "GerenteGeral@2026"),
    "gerente_log_a": ("gerentelogA@arcos.sconnecta.com.br", "GerenteLog@2026"),
    "gerente_op_a": ("gerenteopA@arcos.sconnecta.com.br", "GerenteOp@2026"),
}

def login(email: str, password: str) -> Dict[str, Any]:
    """Login and return full response with token and user data."""
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        print(f"❌ Login failed for {email}: {r.status_code} {r.text}")
        return None
    return r.json()

def hdr(token: str) -> Dict[str, str]:
    """Return authorization headers."""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_all_logins():
    """Test 1: Login all 8 users and verify JWT structure."""
    print_section("TEST 1: Login All 8 Users + JWT Structure")
    
    tokens = {}
    for key, (email, password) in CREDENTIALS.items():
        result = login(email, password)
        if result:
            tokens[key] = result["access_token"]
            user = result["user"]
            
            print(f"✅ {key:20s} | {email:40s}")
            print(f"   Role: {user.get('role', 'N/A')}")
            print(f"   Tenant: {user.get('tenant_name', 'N/A')}")
            
            # Check multi-warehouse fields
            if "warehouse_ids" in user:
                print(f"   warehouse_ids: {user['warehouse_ids']} (count: {len(user['warehouse_ids'])})")
            if "store_ids" in user:
                print(f"   store_ids: {user['store_ids']} (count: {len(user['store_ids'])})")
            if "warehouse_id" in user:
                print(f"   warehouse_id (legacy): {user['warehouse_id']}")
            print()
        else:
            print(f"❌ {key} login failed\n")
            
    return tokens

def test_stores_scope(tokens: Dict[str, str]):
    """Test 2: GET /api/stores filtered by scope."""
    print_section("TEST 2: Stores Filtered by Scope")
    
    test_users = [
        ("admin_arcos", "Admin Arcos (should see 2 stores)"),
        ("gerente_geral", "Gerente Geral (should see 2 stores)"),
        ("gerente_log_a", "Gerente Logistica A (should see 1 store)"),
    ]
    
    for key, desc in test_users:
        if key not in tokens:
            print(f"⚠️  {desc}: No token available")
            continue
            
        r = requests.get(f"{API}/stores", headers=hdr(tokens[key]))
        if r.status_code == 200:
            stores = r.json()
            print(f"✅ {desc}")
            print(f"   Stores count: {len(stores)}")
            for store in stores:
                print(f"   - {store.get('name', 'N/A')} (id: {store.get('id', 'N/A')})")
        else:
            print(f"❌ {desc}: {r.status_code} {r.text}")
        print()

def test_dashboard_stats(tokens: Dict[str, str]):
    """Test 3: GET /api/dashboard/stats - verify total_stores field."""
    print_section("TEST 3: Dashboard Stats (total_stores field)")
    
    test_users = ["admin_arcos", "gerente_geral", "admin_tj"]
    
    for key in test_users:
        if key not in tokens:
            print(f"⚠️  {key}: No token available")
            continue
            
        r = requests.get(f"{API}/dashboard/stats", headers=hdr(tokens[key]))
        if r.status_code == 200:
            stats = r.json()
            print(f"✅ {key}")
            print(f"   total_stores: {stats.get('total_stores', 'MISSING')}")
            print(f"   total_warehouses: {stats.get('total_warehouses', 'N/A')}")
            print(f"   total_products: {stats.get('total_products', 'N/A')}")
        else:
            print(f"❌ {key}: {r.status_code} {r.text}")
        print()

def test_transfers(tokens: Dict[str, str]):
    """Test 4: POST /api/transfers - PAI to PAI transfer."""
    print_section("TEST 4: Transfers Between Stores (PAI→PAI)")
    
    # First get warehouses for Arcos tenant
    if "admin_arcos" not in tokens:
        print("⚠️  No admin_arcos token, skipping transfer test")
        return
        
    r = requests.get(f"{API}/warehouses", headers=hdr(tokens["admin_arcos"]))
    if r.status_code != 200:
        print(f"❌ Failed to get warehouses: {r.status_code}")
        return
        
    warehouses = r.json()
    pai_warehouses = [w for w in warehouses if w.get("type", "").lower() == "pai"]
    
    if len(pai_warehouses) < 2:
        print(f"⚠️  Need at least 2 PAI warehouses, found {len(pai_warehouses)}")
        return
        
    pai_a = pai_warehouses[0]
    pai_b = pai_warehouses[1]
    
    print(f"PAI A: {pai_a['name']} (id: {pai_a['id']})")
    print(f"PAI B: {pai_b['name']} (id: {pai_b['id']})")
    print()
    
    # Get products to transfer
    r = requests.get(f"{API}/products", headers=hdr(tokens["admin_arcos"]))
    if r.status_code != 200 or not r.json():
        print("⚠️  No products available for transfer test")
        return
        
    product = r.json()[0]
    print(f"Product: {product['name']} (id: {product['id']})")
    print()
    
    # Test with gerente_geral (should succeed)
    if "gerente_geral" in tokens:
        transfer_data = {
            "from_warehouse_id": pai_a["id"],
            "to_warehouse_id": pai_b["id"],
            "product_id": product["id"],
            "quantity": 1,
            "notes": "Test transfer PAI→PAI"
        }
        
        r = requests.post(f"{API}/transfers", headers=hdr(tokens["gerente_geral"]), json=transfer_data)
        if r.status_code == 200:
            print(f"✅ Gerente Geral transfer succeeded")
            transfer = r.json()
            print(f"   Transfer ID: {transfer.get('id', 'N/A')}")
            print(f"   From: {transfer.get('from_warehouse_name', 'N/A')}")
            print(f"   To: {transfer.get('to_warehouse_name', 'N/A')}")
            print(f"   Quantity: {transfer.get('quantity', 'N/A')}")
        else:
            print(f"❌ Gerente Geral transfer failed: {r.status_code} {r.text}")
    print()
    
    # Test with gerente_operacional (should fail with 403)
    if "gerente_op_a" in tokens:
        transfer_data = {
            "from_warehouse_id": pai_a["id"],
            "to_warehouse_id": pai_b["id"],
            "product_id": product["id"],
            "quantity": 1,
            "notes": "Test transfer (should fail)"
        }
        
        r = requests.post(f"{API}/transfers", headers=hdr(tokens["gerente_op_a"]), json=transfer_data)
        if r.status_code == 403:
            print(f"✅ Gerente Operacional correctly blocked (403)")
        else:
            print(f"❌ Gerente Operacional should get 403, got: {r.status_code}")
    print()

def test_modules_config(tokens: Dict[str, str]):
    """Test 5: Module configuration endpoints."""
    print_section("TEST 5: Module Configuration")
    
    if "admin_arcos" not in tokens:
        print("⚠️  No admin_arcos token, skipping module test")
        return
        
    # Get PAI warehouse
    r = requests.get(f"{API}/warehouses", headers=hdr(tokens["admin_arcos"]))
    if r.status_code != 200:
        print(f"❌ Failed to get warehouses: {r.status_code}")
        return
        
    pai_warehouses = [w for w in r.json() if w.get("type", "").lower() == "pai"]
    if not pai_warehouses:
        print("⚠️  No PAI warehouse found")
        return
        
    pai = pai_warehouses[0]
    print(f"Testing with PAI: {pai['name']} (id: {pai['id']})")
    print()
    
    # Test GET /api/modules (list all available modules)
    r = requests.get(f"{API}/modules", headers=hdr(tokens["admin_arcos"]))
    if r.status_code == 200:
        modules = r.json()
        print(f"✅ GET /api/modules: {len(modules)} modules available")
        for mod in modules:
            print(f"   - {mod}")
    else:
        print(f"❌ GET /api/modules failed: {r.status_code}")
    print()
    
    # Test GET /api/modules/me (user's effective modules)
    r = requests.get(f"{API}/modules/me", headers=hdr(tokens["admin_arcos"]))
    if r.status_code == 200:
        my_modules = r.json()
        print(f"✅ GET /api/modules/me: {len(my_modules.get('enabled_modules', []))} enabled")
        print(f"   Modules: {my_modules.get('enabled_modules', [])}")
    else:
        print(f"❌ GET /api/modules/me failed: {r.status_code}")
    print()
    
    # Test GET /api/warehouses/{wid}/modules
    r = requests.get(f"{API}/warehouses/{pai['id']}/modules", headers=hdr(tokens["admin_arcos"]))
    if r.status_code == 200:
        wh_modules = r.json()
        print(f"✅ GET /api/warehouses/{pai['id']}/modules")
        print(f"   Enabled: {wh_modules.get('enabled_modules', [])}")
    else:
        print(f"❌ GET /api/warehouses/{pai['id']}/modules failed: {r.status_code}")
    print()
    
    # Test PUT /api/warehouses/{wid}/modules (disable one module)
    current_modules = wh_modules.get('enabled_modules', [])
    if current_modules:
        test_modules = current_modules[:-1]  # Remove last module
        r = requests.put(
            f"{API}/warehouses/{pai['id']}/modules",
            headers=hdr(tokens["admin_arcos"]),
            json={"enabled_modules": test_modules}
        )
        if r.status_code == 200:
            print(f"✅ PUT /api/warehouses/{pai['id']}/modules succeeded")
            print(f"   Updated modules: {r.json().get('enabled_modules', [])}")
            
            # Restore original modules
            requests.put(
                f"{API}/warehouses/{pai['id']}/modules",
                headers=hdr(tokens["admin_arcos"]),
                json={"enabled_modules": current_modules}
            )
        else:
            print(f"❌ PUT /api/warehouses/{pai['id']}/modules failed: {r.status_code} {r.text}")
    print()
    
    # Test invalid module name (should get 422)
    r = requests.put(
        f"{API}/warehouses/{pai['id']}/modules",
        headers=hdr(tokens["admin_arcos"]),
        json={"enabled_modules": ["invalid_module_xyz"]}
    )
    if r.status_code == 422:
        print(f"✅ Invalid module correctly rejected (422)")
    else:
        print(f"❌ Invalid module should get 422, got: {r.status_code}")
    print()

def test_audit_scoped(tokens: Dict[str, str]):
    """Test 6: GET /api/audit scoped per role."""
    print_section("TEST 6: Audit Logs Scoped by Role")
    
    test_users = [
        ("gerente_geral", "Gerente Geral (should see Arcos tenant)"),
        ("gerente_log_a", "Gerente Logistica A (should see their PAI)"),
        ("admin_tj", "Admin TJ (should see TJ tenant)"),
    ]
    
    for key, desc in test_users:
        if key not in tokens:
            print(f"⚠️  {desc}: No token available")
            continue
            
        r = requests.get(f"{API}/audit?limit=5", headers=hdr(tokens[key]))
        if r.status_code == 200:
            logs = r.json()
            print(f"✅ {desc}")
            print(f"   Audit logs count: {len(logs)}")
            if logs:
                print(f"   Latest action: {logs[0].get('action', 'N/A')}")
                print(f"   User: {logs[0].get('user_email', 'N/A')}")
        else:
            print(f"❌ {desc}: {r.status_code} {r.text}")
        print()

def test_seed_idempotent():
    """Test 7: POST /api/seed idempotency."""
    print_section("TEST 7: Seed Idempotency")
    
    r = requests.post(f"{API}/seed")
    if r.status_code == 200:
        result = r.json()
        print(f"✅ Seed endpoint responded: {r.status_code}")
        print(f"   Message: {result.get('message', 'N/A')}")
        
        # Call again to verify idempotency
        r2 = requests.post(f"{API}/seed")
        if r2.status_code == 200:
            result2 = r2.json()
            print(f"✅ Second seed call: {r2.status_code}")
            print(f"   Message: {result2.get('message', 'N/A')}")
            
            if "inicializado" in result2.get('message', '').lower():
                print(f"✅ Seed is idempotent (already initialized message)")
        else:
            print(f"❌ Second seed call failed: {r2.status_code}")
    else:
        print(f"❌ Seed failed: {r.status_code} {r.text}")
    print()

def main():
    """Run all manual verification tests."""
    print("\n" + "="*80)
    print("  GESTAO TJ SAAS - BACKEND REFACTORING VERIFICATION")
    print("  Testing against: " + BASE_URL)
    print("="*80)
    
    # Test 1: Login all users
    tokens = test_all_logins()
    
    if not tokens:
        print("\n❌ No tokens obtained, cannot continue with other tests")
        return
    
    # Test 2: Stores scope
    test_stores_scope(tokens)
    
    # Test 3: Dashboard stats
    test_dashboard_stats(tokens)
    
    # Test 4: Transfers
    test_transfers(tokens)
    
    # Test 5: Modules
    test_modules_config(tokens)
    
    # Test 6: Audit
    test_audit_scoped(tokens)
    
    # Test 7: Seed idempotency
    test_seed_idempotent()
    
    print("\n" + "="*80)
    print("  VERIFICATION COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
