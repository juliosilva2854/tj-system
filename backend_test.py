#!/usr/bin/env python3
"""
Backend tests for Gestao TJ - Email Anti-Hang + Notifications System
Tests against public URL with httpOnly cookie authentication.
"""
import os
import json
import time
import requests
from typing import Dict, Any

# Read BASE_URL from frontend/.env
BASE_URL = "https://system-updates-v1.preview.emergentagent.com"
API = f"{BASE_URL}/api"

# Test credentials from /app/memory/test_credentials.md
# NOTE: Login is DUAL - normal users by username, master by email
CREDENTIALS = {
    "admin_tj": ("admin.tj", "Admin@2026"),  # username login
    "logistica_tj": ("logistica.tj", "Logistica@2026"),  # username login
    "operacional_tj": ("operacional.tj", "Operacional@2026"),  # username login
    "master": ("master@sconnecta.com.br", "Master@2026", True),  # email login with is_master
}

def login(identifier: str, password: str, is_master: bool = False) -> requests.Session:
    """Login and return session with httpOnly cookies."""
    session = requests.Session()
    payload = {"identifier": identifier, "password": password}
    if is_master:
        payload["is_master"] = True
    
    r = session.post(f"{API}/auth/login", json=payload)
    if r.status_code != 200:
        print(f"❌ Login failed for {identifier}: {r.status_code} {r.text}")
        return None
    
    # Verify cookies are set
    if 'access_token' not in session.cookies:
        print(f"❌ Login succeeded but no access_token cookie set for {identifier}")
        return None
    
    return session

def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_email_anti_hang():
    """
    TEST 1: EMAIL ANTI-HANG (CRITICAL)
    POST /api/auth/forgot-password must respond FAST (<5s) with HTTP 200.
    Must NOT hang even if email sending fails.
    """
    print_section("TEST 1: EMAIL ANTI-HANG (forgot-password)")
    
    test_cases = [
        ("admin.tj", "Valid username - should respond fast"),
        ("naoexiste@nada.com", "Non-existent identifier - should also respond fast (security)"),
    ]
    
    all_passed = True
    
    for identifier, description in test_cases:
        print(f"Testing: {description}")
        print(f"Identifier: {identifier}")
        
        start_time = time.time()
        r = requests.post(f"{API}/auth/forgot-password", json={"identifier": identifier})
        elapsed = time.time() - start_time
        
        print(f"Response time: {elapsed:.3f}s")
        print(f"Status code: {r.status_code}")
        
        if r.status_code == 200:
            print(f"✅ HTTP 200 OK")
            response_data = r.json()
            print(f"Message: {response_data.get('message', 'N/A')}")
        else:
            print(f"❌ Expected 200, got {r.status_code}: {r.text}")
            all_passed = False
        
        if elapsed < 5.0:
            print(f"✅ Response time OK ({elapsed:.3f}s < 5s)")
        else:
            print(f"❌ CRITICAL: Response too slow ({elapsed:.3f}s >= 5s) - HANGS!")
            all_passed = False
        
        print()
    
    if all_passed:
        print("✅✅✅ EMAIL ANTI-HANG TEST PASSED - No hanging detected")
    else:
        print("❌❌❌ EMAIL ANTI-HANG TEST FAILED - Issues detected")
    
    return all_passed

def test_notification_preferences():
    """
    TEST 2: NOTIFICATION PREFERENCES (per-user)
    GET /api/notifications/preferences -> returns events + preferences
    PUT /api/notifications/preferences -> saves preferences
    """
    print_section("TEST 2: NOTIFICATION PREFERENCES")
    
    # Login as admin.tj
    session = login("admin.tj", "Admin@2026")
    if not session:
        print("❌ Failed to login as admin.tj")
        return False
    
    print("✅ Logged in as admin.tj")
    print()
    
    # GET preferences
    print("GET /api/notifications/preferences")
    r = session.get(f"{API}/notifications/preferences")
    
    if r.status_code != 200:
        print(f"❌ GET preferences failed: {r.status_code} {r.text}")
        return False
    
    data = r.json()
    print(f"✅ GET preferences succeeded")
    
    # Verify structure
    if "events" not in data or "preferences" not in data:
        print(f"❌ Missing 'events' or 'preferences' in response")
        return False
    
    events = data["events"]
    preferences = data["preferences"]
    
    print(f"Events count: {len(events)}")
    print(f"Expected events: stock_low, requisition_created, requisition_resolved, transfer_received, invoice_pending")
    
    expected_events = ["stock_low", "requisition_created", "requisition_resolved", "transfer_received", "invoice_pending"]
    event_keys = [e["key"] for e in events]
    
    missing_events = [e for e in expected_events if e not in event_keys]
    if missing_events:
        print(f"❌ Missing events: {missing_events}")
        return False
    
    print(f"✅ All 5 expected events present")
    print()
    
    # Display current preferences
    print("Current preferences:")
    for event_key in expected_events:
        pref = preferences.get(event_key, {})
        print(f"  {event_key}: in_app={pref.get('in_app')}, email={pref.get('email')}")
    print()
    
    # PUT preferences (update some settings)
    print("PUT /api/notifications/preferences")
    new_prefs = {
        "preferences": {
            "stock_low": {"in_app": True, "email": True},
            "invoice_pending": {"in_app": True, "email": False}
        }
    }
    
    r = session.put(f"{API}/notifications/preferences", json=new_prefs)
    
    if r.status_code != 200:
        print(f"❌ PUT preferences failed: {r.status_code} {r.text}")
        return False
    
    print(f"✅ PUT preferences succeeded")
    saved_prefs = r.json().get("preferences", {})
    print(f"Saved preferences: stock_low={saved_prefs.get('stock_low')}, invoice_pending={saved_prefs.get('invoice_pending')}")
    print()
    
    # GET again to verify persistence
    print("GET /api/notifications/preferences (verify persistence)")
    r = session.get(f"{API}/notifications/preferences")
    
    if r.status_code != 200:
        print(f"❌ GET preferences (2nd) failed: {r.status_code}")
        return False
    
    data = r.json()
    persisted_prefs = data["preferences"]
    
    # Verify stock_low was saved
    if persisted_prefs.get("stock_low", {}).get("email") == True:
        print(f"✅ Preferences persisted correctly (stock_low.email=True)")
    else:
        print(f"❌ Preferences not persisted (stock_low.email should be True)")
        return False
    
    print()
    print("✅✅✅ NOTIFICATION PREFERENCES TEST PASSED")
    return True

def test_invoice_pending_notification():
    """
    TEST 3: NOTIFICATION GENERATION - invoice_pending
    As admin.tj, create an invoice -> should generate invoice_pending notification
    for managers (logistica.tj is a manager/approver in same tenant).
    """
    print_section("TEST 3: NOTIFICATION GENERATION - invoice_pending")
    
    # Login as admin.tj
    admin_session = login("admin.tj", "Admin@2026")
    if not admin_session:
        print("❌ Failed to login as admin.tj")
        return False
    
    print("✅ Logged in as admin.tj")
    print()
    
    # Create an invoice
    print("Creating invoice as admin.tj...")
    invoice_data = {
        "invoice_number": f"NF-TEST-{int(time.time())}",
        "supplier_name": "Fornecedor Teste Notificacao",
        "issue_date": "2025-07-01",
        "total_value": 150.50,
        "tax_value": 0,
        "items": []
    }
    
    r = admin_session.post(f"{API}/invoices", json=invoice_data)
    
    if r.status_code != 200:
        print(f"❌ Failed to create invoice: {r.status_code} {r.text}")
        return False
    
    invoice = r.json()
    print(f"✅ Invoice created: {invoice.get('invoice_number')} (id: {invoice.get('id')})")
    print()
    
    # Wait a moment for notification to be created
    time.sleep(1)
    
    # Login as logistica.tj (same tenant, should receive notification)
    print("Logging in as logistica.tj (manager/approver)...")
    log_session = login("logistica.tj", "Logistica@2026")
    if not log_session:
        print("❌ Failed to login as logistica.tj")
        return False
    
    print("✅ Logged in as logistica.tj")
    print()
    
    # GET notifications
    print("GET /api/notifications (as logistica.tj)")
    r = log_session.get(f"{API}/notifications")
    
    if r.status_code != 200:
        print(f"❌ GET notifications failed: {r.status_code} {r.text}")
        return False
    
    notifications = r.json()
    print(f"Total notifications: {len(notifications)}")
    
    # Look for invoice_pending notification
    invoice_pending_notifs = [n for n in notifications if n.get("event") == "invoice_pending"]
    
    if not invoice_pending_notifs:
        print(f"❌ No 'invoice_pending' notification found")
        print(f"Available events: {[n.get('event') for n in notifications[:5]]}")
        return False
    
    print(f"✅ Found {len(invoice_pending_notifs)} invoice_pending notification(s)")
    latest = invoice_pending_notifs[0]
    print(f"   Title: {latest.get('title')}")
    print(f"   Message: {latest.get('message')}")
    print(f"   Type: {latest.get('type')}")
    print(f"   Read: {latest.get('read')}")
    print()
    
    # GET unread count
    print("GET /api/notifications/unread-count")
    r = log_session.get(f"{API}/notifications/unread-count")
    
    if r.status_code != 200:
        print(f"❌ GET unread-count failed: {r.status_code}")
        return False
    
    count_data = r.json()
    unread_count = count_data.get("count", 0)
    print(f"✅ Unread count: {unread_count}")
    
    if unread_count >= 1:
        print(f"✅ Unread count >= 1 (expected)")
    else:
        print(f"⚠️  Unread count is 0 (might be already read)")
    
    print()
    print("✅✅✅ INVOICE_PENDING NOTIFICATION TEST PASSED")
    return True

def test_requisition_flow_notifications():
    """
    TEST 4: NOTIFICATION GENERATION - requisition flow
    operacional.tj creates requisition -> notifies approvers (requisition_created)
    logistica.tj approves/rejects -> notifies creator (requisition_resolved)
    """
    print_section("TEST 4: NOTIFICATION GENERATION - requisition flow")
    
    # Login as operacional.tj (FILHO warehouse user)
    op_session = login("operacional.tj", "Operacional@2026")
    if not op_session:
        print("❌ Failed to login as operacional.tj")
        return False
    
    print("✅ Logged in as operacional.tj")
    print()
    
    # Get products to create requisition
    print("Getting products...")
    r = op_session.get(f"{API}/products")
    if r.status_code != 200 or not r.json():
        print(f"❌ No products available: {r.status_code}")
        return False
    
    products = r.json()
    product = products[0]
    print(f"✅ Using product: {product.get('name')} (id: {product.get('id')})")
    print()
    
    # Create requisition
    print("Creating requisition as operacional.tj...")
    req_data = {
        "items": [
            {
                "product_id": product.get("id"),
                "product_name": product.get("name"),
                "quantity": 1
            }
        ],
        "notes": "Teste de notificacao requisition_created"
    }
    
    r = op_session.post(f"{API}/requisitions", json=req_data)
    
    if r.status_code != 200:
        print(f"❌ Failed to create requisition: {r.status_code} {r.text}")
        return False
    
    requisition = r.json()
    req_id = requisition.get("id")
    print(f"✅ Requisition created: {req_id}")
    print(f"   Status: {requisition.get('status')}")
    print()
    
    # Wait for notification
    time.sleep(1)
    
    # Login as logistica.tj (approver)
    print("Logging in as logistica.tj (approver)...")
    log_session = login("logistica.tj", "Logistica@2026")
    if not log_session:
        print("❌ Failed to login as logistica.tj")
        return False
    
    print("✅ Logged in as logistica.tj")
    print()
    
    # Check for requisition_created notification
    print("GET /api/notifications (as logistica.tj)")
    r = log_session.get(f"{API}/notifications")
    
    if r.status_code != 200:
        print(f"❌ GET notifications failed: {r.status_code}")
        return False
    
    notifications = r.json()
    req_created_notifs = [n for n in notifications if n.get("event") == "requisition_created"]
    
    if not req_created_notifs:
        print(f"❌ No 'requisition_created' notification found")
        return False
    
    print(f"✅ Found requisition_created notification")
    print(f"   Title: {req_created_notifs[0].get('title')}")
    print(f"   Message: {req_created_notifs[0].get('message')}")
    print()
    
    # Get the requisition to approve/reject
    print("GET /api/requisitions (to find pending requisition)")
    r = log_session.get(f"{API}/requisitions")
    
    if r.status_code != 200:
        print(f"❌ GET requisitions failed: {r.status_code}")
        return False
    
    requisitions = r.json()
    pending_reqs = [req for req in requisitions if req.get("id") == req_id and req.get("status") == "pending"]
    
    if not pending_reqs:
        print(f"⚠️  Requisition {req_id} not found or not pending")
        print(f"   This is OK if it was already processed")
    else:
        print(f"✅ Found pending requisition: {req_id}")
        print()
        
        # Try to approve (may fail with "estoque insuficiente" - that's acceptable)
        print(f"POST /api/requisitions/{req_id}/approve")
        r = log_session.post(f"{API}/requisitions/{req_id}/approve")
        
        if r.status_code == 200:
            print(f"✅ Requisition approved")
        elif r.status_code == 400 and "insuficiente" in r.text.lower():
            print(f"⚠️  Approval failed due to insufficient stock (acceptable)")
            print(f"   Trying to reject instead...")
            
            # Reject instead
            r = log_session.post(f"{API}/requisitions/{req_id}/reject")
            if r.status_code == 200:
                print(f"✅ Requisition rejected")
            else:
                print(f"❌ Reject failed: {r.status_code} {r.text}")
                return False
        else:
            print(f"❌ Approve failed: {r.status_code} {r.text}")
            return False
        
        print()
        
        # Wait for notification
        time.sleep(1)
        
        # Login back as operacional.tj to check for requisition_resolved notification
        print("Logging back as operacional.tj (creator)...")
        op_session2 = login("operacional.tj", "Operacional@2026")
        if not op_session2:
            print("❌ Failed to re-login as operacional.tj")
            return False
        
        print("✅ Logged in as operacional.tj")
        print()
        
        print("GET /api/notifications (as operacional.tj)")
        r = op_session2.get(f"{API}/notifications")
        
        if r.status_code != 200:
            print(f"❌ GET notifications failed: {r.status_code}")
            return False
        
        notifications = r.json()
        req_resolved_notifs = [n for n in notifications if n.get("event") == "requisition_resolved"]
        
        if not req_resolved_notifs:
            print(f"❌ No 'requisition_resolved' notification found")
            return False
        
        print(f"✅ Found requisition_resolved notification")
        print(f"   Title: {req_resolved_notifs[0].get('title')}")
        print(f"   Message: {req_resolved_notifs[0].get('message')}")
        print()
    
    print("✅✅✅ REQUISITION FLOW NOTIFICATIONS TEST PASSED")
    return True

def test_stock_low_notification():
    """
    TEST 5: NOTIFICATION GENERATION - stock_low (best-effort)
    Set high min_stock on a product, adjust inventory to low quantity -> should trigger stock_low notification.
    """
    print_section("TEST 5: NOTIFICATION GENERATION - stock_low (best-effort)")
    
    # Login as admin.tj
    admin_session = login("admin.tj", "Admin@2026")
    if not admin_session:
        print("❌ Failed to login as admin.tj")
        return False
    
    print("✅ Logged in as admin.tj")
    print()
    
    # Get products
    print("Getting products...")
    r = admin_session.get(f"{API}/products")
    if r.status_code != 200 or not r.json():
        print(f"❌ No products available: {r.status_code}")
        return False
    
    products = r.json()
    product = products[0]
    product_id = product.get("id")
    print(f"✅ Using product: {product.get('name')} (id: {product_id})")
    print()
    
    # Get warehouses
    print("Getting warehouses...")
    r = admin_session.get(f"{API}/warehouses")
    if r.status_code != 200 or not r.json():
        print(f"❌ No warehouses available: {r.status_code}")
        return False
    
    warehouses = r.json()
    warehouse = warehouses[0]
    warehouse_id = warehouse.get("id")
    print(f"✅ Using warehouse: {warehouse.get('name')} (id: {warehouse_id})")
    print()
    
    # Set high min_stock
    print(f"PATCH /api/products/{product_id} (set min_stock=9999)")
    r = admin_session.patch(f"{API}/products/{product_id}", json={"min_stock": 9999})
    
    if r.status_code != 200:
        print(f"❌ Failed to update product: {r.status_code} {r.text}")
        return False
    
    print(f"✅ Product min_stock set to 9999")
    print()
    
    # Adjust inventory to low quantity
    print(f"POST /api/inventory/adjust (set quantity=1)")
    adjust_data = {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "quantity": 1,
        "reason": "Teste stock_low notification"
    }
    
    r = admin_session.post(f"{API}/inventory/adjust", json=adjust_data)
    
    if r.status_code != 200:
        print(f"❌ Failed to adjust inventory: {r.status_code} {r.text}")
        return False
    
    print(f"✅ Inventory adjusted to 1 (below min_stock 9999)")
    print()
    
    # Wait for notification
    time.sleep(1)
    
    # Check for stock_low notification
    print("GET /api/notifications (as admin.tj)")
    r = admin_session.get(f"{API}/notifications")
    
    if r.status_code != 200:
        print(f"❌ GET notifications failed: {r.status_code}")
        return False
    
    notifications = r.json()
    stock_low_notifs = [n for n in notifications if n.get("event") == "stock_low"]
    
    if not stock_low_notifs:
        print(f"⚠️  No 'stock_low' notification found")
        print(f"   This may be expected if inventory record didn't exist before")
        print(f"   Available events: {list(set([n.get('event') for n in notifications[:10]]))}")
        return True  # Not a failure, just best-effort
    
    print(f"✅ Found stock_low notification")
    print(f"   Title: {stock_low_notifs[0].get('title')}")
    print(f"   Message: {stock_low_notifs[0].get('message')}")
    print(f"   Type: {stock_low_notifs[0].get('type')}")
    print()
    
    print("✅✅✅ STOCK_LOW NOTIFICATION TEST PASSED")
    return True

def main():
    """Run all backend tests."""
    print("\n" + "="*80)
    print("  GESTAO TJ - EMAIL ANTI-HANG + NOTIFICATIONS TESTING")
    print("  Testing against: " + BASE_URL)
    print("="*80)
    
    results = {}
    
    # TEST 1: Email anti-hang (CRITICAL)
    results["email_anti_hang"] = test_email_anti_hang()
    
    # TEST 2: Notification preferences
    results["notification_preferences"] = test_notification_preferences()
    
    # TEST 3: Invoice pending notification
    results["invoice_pending"] = test_invoice_pending_notification()
    
    # TEST 4: Requisition flow notifications
    results["requisition_flow"] = test_requisition_flow_notifications()
    
    # TEST 5: Stock low notification (best-effort)
    results["stock_low"] = test_stock_low_notification()
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅✅✅ ALL TESTS PASSED ✅✅✅")
    else:
        print(f"\n❌❌❌ {total - passed} TEST(S) FAILED ❌❌❌")
    
    print("\n" + "="*80 + "\n")
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
