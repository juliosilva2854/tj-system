#!/usr/bin/env python3
"""
Backend test for Fase 1: Referential integrity fix (Desconhecido bug) + Product CRUD RBAC
Test scenarios from review_request
"""
import requests
import json
import time
from typing import Optional

# Base URL from frontend/.env
BASE_URL = "https://a4f9812a-7632-49c5-a118-8c7d537f85e9.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_TJ = {"identifier": "admin.tj", "password": "Admin@2026"}
OPERACIONAL_TJ = {"identifier": "operacional.tj", "password": "Operacional@2026"}
GERAL_ARCOS = {"identifier": "geral.arcos", "password": "GerenteGeral@2026"}

class TestSession:
    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.user_data = None
        
    def login(self, credentials: dict) -> bool:
        """Login and store cookies"""
        print(f"\n[{self.name}] Logging in as {credentials['identifier']}...")
        resp = self.session.post(f"{BASE_URL}/auth/login", json=credentials)
        if resp.status_code == 200:
            data = resp.json()
            self.user_data = data.get('user', {})
            print(f"[{self.name}] ✓ Login successful: {self.user_data.get('name')} | Role: {self.user_data.get('role')}")
            return True
        else:
            print(f"[{self.name}] ✗ Login failed: {resp.status_code} - {resp.text}")
            return False
    
    def get(self, endpoint: str) -> requests.Response:
        return self.session.get(f"{BASE_URL}{endpoint}")
    
    def post(self, endpoint: str, json_data: dict = None, **kwargs) -> requests.Response:
        if json_data is not None:
            return self.session.post(f"{BASE_URL}{endpoint}", json=json_data, **kwargs)
        return self.session.post(f"{BASE_URL}{endpoint}", **kwargs)
    
    def patch(self, endpoint: str, json_data: dict) -> requests.Response:
        return self.session.patch(f"{BASE_URL}{endpoint}", json=json_data)

def print_test_header(test_num: int, description: str):
    print(f"\n{'='*80}")
    print(f"TEST {test_num}: {description}")
    print(f"{'='*80}")

def print_result(success: bool, message: str):
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {message}")

def main():
    print("="*80)
    print("FASE 1 BACKEND TESTING - Referential Integrity + Product CRUD RBAC")
    print("="*80)
    
    # Initialize sessions
    admin_session = TestSession("ADMIN_TJ")
    operacional_session = TestSession("OPERACIONAL_TJ")
    arcos_session = TestSession("GERAL_ARCOS")
    
    # Login all users
    if not admin_session.login(ADMIN_TJ):
        print("CRITICAL: Admin login failed. Aborting tests.")
        return
    
    if not operacional_session.login(OPERACIONAL_TJ):
        print("WARNING: Operacional login failed. RBAC tests will be skipped.")
    
    if not arcos_session.login(GERAL_ARCOS):
        print("WARNING: Arcos login failed. PAI->PAI transfer tests will be skipped.")
    
    # Get warehouses for tenant TJ
    print("\n[SETUP] Fetching warehouses for tenant TJ...")
    wh_resp = admin_session.get("/warehouses")
    if wh_resp.status_code != 200:
        print(f"CRITICAL: Failed to fetch warehouses: {wh_resp.status_code}")
        return
    
    warehouses = wh_resp.json()
    pai_warehouses = [w for w in warehouses if w.get('type') == 'pai']
    if not pai_warehouses:
        print("CRITICAL: No PAI warehouse found for tenant TJ")
        return
    
    pai_warehouse = pai_warehouses[0]
    print(f"[SETUP] ✓ Found PAI warehouse: {pai_warehouse['name']} (id: {pai_warehouse['id']})")
    
    # =========================================================================
    # TEST 1: PRODUCT CREATE + RBAC
    # =========================================================================
    print_test_header(1, "PRODUCT CREATE + RBAC")
    
    # 1a) Admin creates product
    product_data = {
        "name": "Produto Teste QA",
        "sku": "QA-SKU-001",
        "cost_price": 10.5,
        "min_stock": 2,
        "description": "Produto para teste de integridade referencial",
        "category": "Teste",
        "unit": "UN"
    }
    
    print(f"\n[TEST 1a] Admin creating product: {product_data['name']}")
    create_resp = admin_session.post("/products", product_data)
    
    if create_resp.status_code == 200:
        product = create_resp.json()
        product_id = product['id']
        print_result(True, f"Product created with id={product_id}, available_qty={product.get('available_qty')}")
        
        if product.get('available_qty') == 0:
            print_result(True, "available_qty correctly initialized to 0")
        else:
            print_result(False, f"available_qty should be 0, got {product.get('available_qty')}")
    else:
        print_result(False, f"Product creation failed: {create_resp.status_code} - {create_resp.text}")
        return
    
    # 1b) RBAC: Operacional tries to create product (should get 403)
    print(f"\n[TEST 1b] RBAC: Operacional attempting to create product (expect 403)")
    rbac_product_data = {
        "name": "Produto Nao Autorizado",
        "sku": "RBAC-FAIL-001",
        "cost_price": 5.0,
        "min_stock": 1,
        "description": "Este produto nao deve ser criado",
        "category": "Teste",
        "unit": "UN"
    }
    
    rbac_create_resp = operacional_session.post("/products", rbac_product_data)
    
    if rbac_create_resp.status_code == 403:
        print_result(True, "Operacional correctly blocked from creating product (403)")
    else:
        print_result(False, f"Expected 403, got {rbac_create_resp.status_code}")
    
    # =========================================================================
    # TEST 2: PRODUCT UPDATE SKU + RBAC
    # =========================================================================
    print_test_header(2, "PRODUCT UPDATE SKU + RBAC")
    
    # 2a) Admin updates SKU
    new_sku = "QA-SKU-EDITED"
    print(f"\n[TEST 2a] Admin updating product SKU to: {new_sku}")
    update_resp = admin_session.patch(f"/products/{product_id}", {"sku": new_sku})
    
    if update_resp.status_code == 200:
        print_result(True, "Product SKU update successful")
        
        # Verify SKU changed
        products_resp = admin_session.get("/products")
        if products_resp.status_code == 200:
            products = products_resp.json()
            updated_product = next((p for p in products if p['id'] == product_id), None)
            if updated_product and updated_product.get('sku') == new_sku:
                print_result(True, f"SKU correctly updated to {new_sku}")
            else:
                print_result(False, f"SKU not updated correctly. Got: {updated_product.get('sku') if updated_product else 'product not found'}")
        else:
            print_result(False, f"Failed to verify SKU update: {products_resp.status_code}")
    else:
        print_result(False, f"Product update failed: {update_resp.status_code} - {update_resp.text}")
    
    # 2b) RBAC: Operacional tries to update product (should get 403)
    print(f"\n[TEST 2b] RBAC: Operacional attempting to update product (expect 403)")
    rbac_update_resp = operacional_session.patch(f"/products/{product_id}", {"sku": "HACKED-SKU"})
    
    if rbac_update_resp.status_code == 403:
        print_result(True, "Operacional correctly blocked from updating product (403)")
    else:
        print_result(False, f"Expected 403, got {rbac_update_resp.status_code}")
    
    # =========================================================================
    # TEST 3: CRITICAL "Desconhecido" FLOW
    # =========================================================================
    print_test_header(3, "CRITICAL 'Desconhecido' FLOW - Full Transfer")
    
    # 3a) Give product some available_qty via invoice processing
    print(f"\n[TEST 3a] Creating invoice to give product available_qty...")
    invoice_data = {
        "invoice_number": f"NF-TEST-DESCONHECIDO-{int(time.time())}",
        "supplier_name": "Fornecedor Teste QA",
        "issue_date": "2026-01-15",
        "total_value": 105.0,
        "tax_value": 5.0,
        "items": [
            {
                "product_name": product_data['name'],
                "product_sku": new_sku,
                "quantity": 10,
                "unit_price": 10.5,
                "total": 105.0
            }
        ]
    }
    
    invoice_resp = admin_session.post("/invoices", invoice_data)
    if invoice_resp.status_code != 200:
        print_result(False, f"Invoice creation failed: {invoice_resp.status_code} - {invoice_resp.text}")
        return
    
    invoice = invoice_resp.json()
    invoice_id = invoice['id']
    print_result(True, f"Invoice created: {invoice_id}")
    
    # Process invoice items to update product available_qty
    print(f"\n[TEST 3b] Processing invoice items to update available_qty...")
    process_resp = admin_session.post(f"/invoices/{invoice_id}/process-items", {})
    
    if process_resp.status_code == 200:
        process_result = process_resp.json()
        print_result(True, f"Invoice processed: {process_result.get('message')}")
        print(f"   Products created: {process_result.get('products_created', 0)}")
        
        # Verify available_qty increased
        products_resp = admin_session.get("/products")
        if products_resp.status_code == 200:
            products = products_resp.json()
            updated_product = next((p for p in products if p['id'] == product_id), None)
            if updated_product:
                avail_qty = updated_product.get('available_qty', 0)
                print_result(True, f"Product available_qty now: {avail_qty}")
                print(f"   Product details: name='{updated_product.get('name')}', sku='{updated_product.get('sku')}'")
                
                # Check if a duplicate product was created instead
                matching_products = [p for p in products if p.get('sku') == new_sku]
                if len(matching_products) > 1:
                    print(f"   WARNING: Found {len(matching_products)} products with SKU '{new_sku}'")
                    for idx, p in enumerate(matching_products):
                        print(f"      Product {idx+1}: id={p['id']}, name='{p['name']}', available_qty={p.get('available_qty', 0)}")
                    # Use the one with available_qty > 0
                    product_with_qty = next((p for p in matching_products if p.get('available_qty', 0) > 0), None)
                    if product_with_qty:
                        product_id = product_with_qty['id']
                        avail_qty = product_with_qty.get('available_qty', 0)
                        print(f"   Using product with available_qty > 0: {product_id}")
                
                if avail_qty <= 0:
                    print_result(False, "available_qty should be > 0 after processing invoice")
                    return
            else:
                print_result(False, "Product not found after invoice processing")
                return
        else:
            print_result(False, f"Failed to fetch products: {products_resp.status_code}")
            return
    else:
        print_result(False, f"Invoice processing failed: {process_resp.status_code} - {process_resp.text}")
        return
    
    # 3c) Transfer FULL available_qty to warehouse
    print(f"\n[TEST 3c] Transferring FULL available_qty to warehouse {pai_warehouse['name']}...")
    transfer_qty = avail_qty
    transfer_url = f"/products/{product_id}/transfer?warehouse_id={pai_warehouse['id']}&quantity={transfer_qty}"
    transfer_resp = admin_session.session.post(f"{BASE_URL}{transfer_url}", json={})
    
    if transfer_resp.status_code == 200:
        transfer_result = transfer_resp.json()
        print_result(True, f"Transfer successful: {transfer_result.get('message')}")
        
        # 3d) Verify product still exists with available_qty=0
        print(f"\n[TEST 3d] Verifying product NOT deleted (should still exist with available_qty=0)...")
        products_resp = admin_session.get("/products")
        if products_resp.status_code == 200:
            products = products_resp.json()
            product_after_transfer = next((p for p in products if p['id'] == product_id), None)
            
            if product_after_transfer:
                print_result(True, f"✓ CRITICAL: Product still exists after full transfer (NOT deleted)")
                if product_after_transfer.get('available_qty') == 0:
                    print_result(True, "available_qty correctly set to 0")
                else:
                    print_result(False, f"available_qty should be 0, got {product_after_transfer.get('available_qty')}")
            else:
                print_result(False, "✗ CRITICAL BUG: Product was DELETED after full transfer (Desconhecido bug NOT fixed)")
                return
        else:
            print_result(False, f"Failed to fetch products: {products_resp.status_code}")
            return
        
        # 3e) Verify inventory shows CORRECT product_name (not "Desconhecido")
        print(f"\n[TEST 3e] Verifying inventory shows CORRECT product_name (not 'Desconhecido')...")
        inventory_resp = admin_session.get("/inventory")
        if inventory_resp.status_code == 200:
            inventory = inventory_resp.json()
            inventory_item = next((i for i in inventory if i['product_id'] == product_id and i['warehouse_id'] == pai_warehouse['id']), None)
            
            if inventory_item:
                product_name = inventory_item.get('product_name', '')
                product_sku = inventory_item.get('product_sku', '')
                
                print(f"   Inventory item: product_name='{product_name}', product_sku='{product_sku}'")
                
                if product_name == "Desconhecido":
                    print_result(False, "✗ CRITICAL BUG: product_name is 'Desconhecido' (referential integrity NOT fixed)")
                elif product_name == product_data['name']:
                    print_result(True, f"✓ CRITICAL: product_name is CORRECT ('{product_name}')")
                else:
                    print_result(False, f"product_name unexpected: '{product_name}'")
                
                if not product_sku:
                    print_result(False, "product_sku is empty")
                elif product_sku == new_sku:
                    print_result(True, f"✓ product_sku is CORRECT ('{product_sku}')")
                else:
                    print_result(False, f"product_sku unexpected: '{product_sku}'")
            else:
                print_result(False, f"Inventory item not found for product {product_id} in warehouse {pai_warehouse['id']}")
        else:
            print_result(False, f"Failed to fetch inventory: {inventory_resp.status_code}")
    else:
        print_result(False, f"Transfer failed: {transfer_resp.status_code} - {transfer_resp.text}")
        return
    
    # =========================================================================
    # TEST 4: INVENTORY ADJUST DENORMALIZATION
    # =========================================================================
    print_test_header(4, "INVENTORY ADJUST DENORMALIZATION")
    
    # Create a new product for this test
    print(f"\n[TEST 4a] Creating new product for inventory adjust test...")
    adjust_product_data = {
        "name": "Produto Ajuste Estoque",
        "sku": "ADJUST-SKU-001",
        "cost_price": 15.0,
        "min_stock": 5,
        "description": "Produto para teste de ajuste de estoque",
        "category": "Teste",
        "unit": "UN"
    }
    
    adjust_create_resp = admin_session.post("/products", adjust_product_data)
    if adjust_create_resp.status_code != 200:
        print_result(False, f"Product creation failed: {adjust_create_resp.status_code}")
        return
    
    adjust_product = adjust_create_resp.json()
    adjust_product_id = adjust_product['id']
    print_result(True, f"Product created: {adjust_product_id}")
    
    # Adjust inventory (positive quantity, creating new record)
    print(f"\n[TEST 4b] Adjusting inventory (creating new record with quantity=5)...")
    adjust_data = {
        "product_id": adjust_product_id,
        "warehouse_id": pai_warehouse['id'],
        "quantity": 5,
        "reason": "Teste de desnormalizacao"
    }
    
    adjust_resp = admin_session.post("/inventory/adjust", json=adjust_data)
    
    if adjust_resp.status_code == 200:
        print_result(True, "Inventory adjust successful")
        
        # Verify inventory has correct product_name and product_sku
        print(f"\n[TEST 4c] Verifying denormalized product_name and product_sku in inventory...")
        inventory_resp = admin_session.get("/inventory")
        if inventory_resp.status_code == 200:
            inventory = inventory_resp.json()
            inventory_item = next((i for i in inventory if i['product_id'] == adjust_product_id and i['warehouse_id'] == pai_warehouse['id']), None)
            
            if inventory_item:
                product_name = inventory_item.get('product_name', '')
                product_sku = inventory_item.get('product_sku', '')
                
                print(f"   Inventory item: product_name='{product_name}', product_sku='{product_sku}'")
                
                if product_name == "Desconhecido":
                    print_result(False, "✗ BUG: product_name is 'Desconhecido' after adjust")
                elif product_name == adjust_product_data['name']:
                    print_result(True, f"✓ product_name correctly denormalized ('{product_name}')")
                else:
                    print_result(False, f"product_name unexpected: '{product_name}'")
                
                if not product_sku:
                    print_result(False, "product_sku is empty after adjust")
                elif product_sku == adjust_product_data['sku']:
                    print_result(True, f"✓ product_sku correctly denormalized ('{product_sku}')")
                else:
                    print_result(False, f"product_sku unexpected: '{product_sku}'")
            else:
                print_result(False, f"Inventory item not found after adjust")
        else:
            print_result(False, f"Failed to fetch inventory: {inventory_resp.status_code}")
    else:
        print_result(False, f"Inventory adjust failed: {adjust_resp.status_code} - {adjust_resp.text}")
    
    # =========================================================================
    # TEST 5: REGRESSION - Endpoints Return 200
    # =========================================================================
    print_test_header(5, "REGRESSION - Endpoints Return 200")
    
    # 5a) GET /api/inventory
    print(f"\n[TEST 5a] GET /api/inventory")
    inv_resp = admin_session.get("/inventory")
    if inv_resp.status_code == 200:
        print_result(True, f"GET /api/inventory returned 200 ({len(inv_resp.json())} items)")
    else:
        print_result(False, f"GET /api/inventory returned {inv_resp.status_code}")
    
    # 5b) GET /api/transfers
    print(f"\n[TEST 5b] GET /api/transfers")
    transfers_resp = admin_session.get("/transfers")
    if transfers_resp.status_code == 200:
        print_result(True, f"GET /api/transfers returned 200 ({len(transfers_resp.json())} transfers)")
    else:
        print_result(False, f"GET /api/transfers returned {transfers_resp.status_code}")
    
    # 5c) GET /api/requisitions
    print(f"\n[TEST 5c] GET /api/requisitions")
    req_resp = admin_session.get("/requisitions")
    if req_resp.status_code == 200:
        print_result(True, f"GET /api/requisitions returned 200 ({len(req_resp.json())} requisitions)")
    else:
        print_result(False, f"GET /api/requisitions returned {req_resp.status_code}")
    
    # 5d) PAI->PAI transfer (Arcos tenant)
    if arcos_session.user_data:
        print(f"\n[TEST 5d] Creating PAI->PAI transfer as geral.arcos...")
        
        # Get Arcos warehouses
        arcos_wh_resp = arcos_session.get("/warehouses")
        if arcos_wh_resp.status_code == 200:
            arcos_warehouses = arcos_wh_resp.json()
            arcos_pai_warehouses = [w for w in arcos_warehouses if w.get('type') == 'pai']
            
            if len(arcos_pai_warehouses) >= 2:
                from_wh = arcos_pai_warehouses[0]
                to_wh = arcos_pai_warehouses[1]
                
                # First, ensure there's inventory in the source warehouse
                # Create a product for Arcos tenant
                arcos_product_data = {
                    "name": "Produto Transfer Arcos",
                    "sku": "ARCOS-TRANSFER-001",
                    "cost_price": 20.0,
                    "min_stock": 1,
                    "description": "Produto para teste de transferencia PAI->PAI",
                    "category": "Teste",
                    "unit": "UN"
                }
                
                arcos_product_resp = arcos_session.post("/products", arcos_product_data)
                if arcos_product_resp.status_code == 200:
                    arcos_product = arcos_product_resp.json()
                    arcos_product_id = arcos_product['id']
                    
                    # Add inventory to source warehouse
                    arcos_adjust_data = {
                        "product_id": arcos_product_id,
                        "warehouse_id": from_wh['id'],
                        "quantity": 10,
                        "reason": "Setup para teste de transferencia"
                    }
                    
                    arcos_adjust_resp = arcos_session.post("/inventory/adjust", json=arcos_adjust_data)
                    if arcos_adjust_resp.status_code == 200:
                        # Now create the transfer
                        transfer_data = {
                            "from_warehouse_id": from_wh['id'],
                            "to_warehouse_id": to_wh['id'],
                            "items": [
                                {
                                    "product_id": arcos_product_id,
                                    "product_name": arcos_product_data['name'],
                                    "product_sku": arcos_product_data['sku'],
                                    "quantity": 5
                                }
                            ],
                            "notes": "Teste de transferencia PAI->PAI"
                        }
                        
                        transfer_resp = arcos_session.post("/transfers", transfer_data)
                        if transfer_resp.status_code == 200:
                            transfer = transfer_resp.json()
                            print_result(True, f"PAI->PAI transfer created: {transfer['id']}")
                            
                            # Verify destination inventory has correct product_name
                            arcos_inv_resp = arcos_session.get("/inventory")
                            if arcos_inv_resp.status_code == 200:
                                arcos_inventory = arcos_inv_resp.json()
                                dest_inv = next((i for i in arcos_inventory if i['product_id'] == arcos_product_id and i['warehouse_id'] == to_wh['id']), None)
                                
                                if dest_inv:
                                    dest_product_name = dest_inv.get('product_name', '')
                                    if dest_product_name == "Desconhecido":
                                        print_result(False, "✗ BUG: Destination inventory shows 'Desconhecido' after PAI->PAI transfer")
                                    elif dest_product_name == arcos_product_data['name']:
                                        print_result(True, f"✓ Destination inventory shows correct product_name ('{dest_product_name}')")
                                    else:
                                        print_result(False, f"Destination product_name unexpected: '{dest_product_name}'")
                                else:
                                    print_result(False, "Destination inventory item not found")
                            else:
                                print_result(False, f"Failed to fetch Arcos inventory: {arcos_inv_resp.status_code}")
                        else:
                            print_result(False, f"PAI->PAI transfer failed: {transfer_resp.status_code} - {transfer_resp.text}")
                    else:
                        print_result(False, f"Failed to add inventory to source: {arcos_adjust_resp.status_code}")
                else:
                    print_result(False, f"Failed to create Arcos product: {arcos_product_resp.status_code}")
            else:
                print_result(False, f"Arcos tenant needs at least 2 PAI warehouses, found {len(arcos_pai_warehouses)}")
        else:
            print_result(False, f"Failed to fetch Arcos warehouses: {arcos_wh_resp.status_code}")
    else:
        print("SKIPPED: Arcos session not available")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("All critical tests completed. Review results above for any failures.")
    print("="*80)

if __name__ == "__main__":
    main()
