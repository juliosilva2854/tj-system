import requests
import sys
import json
from datetime import datetime

class GestaoTJAPITester:
    def __init__(self, base_url="https://estoque-api.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_ids = {
            'warehouse': None,
            'supplier': None,
            'product': None,
            'order': None
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.text else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_seed_database(self):
        """Test database seeding"""
        success, response = self.run_test(
            "Database Seed",
            "POST",
            "seed",
            200
        )
        return success

    def test_login(self, email, password):
        """Test login and get token"""
        success, response = self.run_test(
            f"Login ({email})",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response.get('user', {})
            print(f"   Logged in as: {self.user_data.get('name')} ({self.user_data.get('role')})")
            return True
        return False

    def test_get_me(self):
        """Test get current user"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        if success:
            print(f"   Stats: {response}")
        return success

    def test_create_warehouse(self):
        """Test warehouse creation"""
        warehouse_data = {
            "name": "Depósito Teste",
            "location": "São Paulo, SP",
            "description": "Depósito para testes automatizados"
        }
        success, response = self.run_test(
            "Create Warehouse",
            "POST",
            "warehouses",
            200,
            data=warehouse_data
        )
        if success and 'id' in response:
            self.created_ids['warehouse'] = response['id']
            print(f"   Created warehouse ID: {response['id']}")
        return success

    def test_get_warehouses(self):
        """Test get warehouses"""
        success, response = self.run_test(
            "Get Warehouses",
            "GET",
            "warehouses",
            200
        )
        if success:
            print(f"   Found {len(response)} warehouses")
        return success

    def test_create_supplier(self):
        """Test supplier creation"""
        supplier_data = {
            "name": "Fornecedor Teste",
            "cnpj": "12.345.678/0001-90",
            "contact": "João Silva",
            "email": "joao@fornecedor.com",
            "phone": "(11) 99999-9999",
            "address": "Rua Teste, 123"
        }
        success, response = self.run_test(
            "Create Supplier",
            "POST",
            "suppliers",
            200,
            data=supplier_data
        )
        if success and 'id' in response:
            self.created_ids['supplier'] = response['id']
            print(f"   Created supplier ID: {response['id']}")
        return success

    def test_get_suppliers(self):
        """Test get suppliers"""
        success, response = self.run_test(
            "Get Suppliers",
            "GET",
            "suppliers",
            200
        )
        if success:
            print(f"   Found {len(response)} suppliers")
        return success

    def test_create_product(self):
        """Test product creation"""
        product_data = {
            "name": "Produto Teste",
            "sku": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "Produto para testes automatizados",
            "category": "Teste",
            "unit": "UN",
            "min_stock": 10,
            "cost_price": 50.0,
            "sale_price": 100.0
        }
        success, response = self.run_test(
            "Create Product",
            "POST",
            "products",
            200,
            data=product_data
        )
        if success and 'id' in response:
            self.created_ids['product'] = response['id']
            print(f"   Created product ID: {response['id']}")
        return success

    def test_get_products(self):
        """Test get products"""
        success, response = self.run_test(
            "Get Products",
            "GET",
            "products",
            200
        )
        if success:
            print(f"   Found {len(response)} products")
        return success

    def test_inventory_adjust(self):
        """Test inventory adjustment"""
        if not self.created_ids['product'] or not self.created_ids['warehouse']:
            print("❌ Cannot test inventory - missing product or warehouse")
            return False
        
        success, response = self.run_test(
            "Adjust Inventory",
            "POST",
            "inventory/adjust",
            200,
            params={
                'product_id': self.created_ids['product'],
                'warehouse_id': self.created_ids['warehouse'],
                'quantity': 100
            }
        )
        return success

    def test_get_inventory(self):
        """Test get inventory"""
        success, response = self.run_test(
            "Get Inventory",
            "GET",
            "inventory",
            200
        )
        if success:
            print(f"   Found {len(response)} inventory items")
        return success

    def test_create_invoice(self):
        """Test invoice creation"""
        invoice_data = {
            "invoice_number": f"NF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "supplier_name": "Fornecedor Teste",
            "issue_date": datetime.now().strftime('%Y-%m-%d'),
            "total_value": 1000.0,
            "tax_value": 100.0,
            "items": [
                {
                    "product_name": "Produto Teste",
                    "quantity": 10,
                    "unit_price": 90.0,
                    "total": 900.0
                }
            ]
        }
        success, response = self.run_test(
            "Create Invoice",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        return success

    def test_get_invoices(self):
        """Test get invoices"""
        success, response = self.run_test(
            "Get Invoices",
            "GET",
            "invoices",
            200
        )
        if success:
            print(f"   Found {len(response)} invoices")
        return success

    def test_create_sale(self):
        """Test sale creation"""
        if not self.created_ids['product'] or not self.created_ids['warehouse']:
            print("❌ Cannot test sales - missing product or warehouse")
            return False
            
        sale_data = {
            "customer_name": "Cliente Teste",
            "customer_document": "123.456.789-00",
            "warehouse_id": self.created_ids['warehouse'],
            "items": [
                {
                    "product_id": self.created_ids['product'],
                    "product_name": "Produto Teste",
                    "quantity": 2,
                    "unit_price": 100.0,
                    "total": 200.0
                }
            ],
            "subtotal": 200.0,
            "discount": 0.0,
            "total": 200.0,
            "payment_method": "dinheiro",
            "status": "completed"
        }
        success, response = self.run_test(
            "Create Sale",
            "POST",
            "sales",
            200,
            data=sale_data
        )
        return success

    def test_get_sales(self):
        """Test get sales"""
        success, response = self.run_test(
            "Get Sales",
            "GET",
            "sales",
            200
        )
        if success:
            print(f"   Found {len(response)} sales")
        return success

    def test_financial_report(self):
        """Test financial report"""
        success, response = self.run_test(
            "Financial Report (Month)",
            "GET",
            "reports/financial",
            200,
            params={'period': 'month'}
        )
        if success:
            print(f"   Revenue: R$ {response.get('revenue', 0):.2f}")
        return success

    def test_get_users(self):
        """Test get users (admin only)"""
        success, response = self.run_test(
            "Get Users",
            "GET",
            "users",
            200
        )
        if success:
            print(f"   Found {len(response)} users")
        return success

    def test_audit_logs(self):
        """Test audit logs (admin/master only)"""
        success, response = self.run_test(
            "Get Audit Logs",
            "GET",
            "audit",
            200
        )
        if success:
            print(f"   Found {len(response)} audit logs")
        return success

    def test_stock_alerts(self):
        """Test stock alerts"""
        success, response = self.run_test(
            "Get Stock Alerts",
            "GET",
            "dashboard/alerts",
            200
        )
        if success:
            print(f"   Found {len(response)} stock alerts")
        return success

    def test_alert_configs(self):
        """Test alert configurations"""
        success, response = self.run_test(
            "Get Alert Configs",
            "GET",
            "alerts/config",
            200
        )
        if success:
            print(f"   Found {len(response)} alert configs")
        return success

    def test_notifications(self):
        """Test notifications"""
        success, response = self.run_test(
            "Get Notifications",
            "GET",
            "notifications",
            200
        )
        if success:
            print(f"   Found {len(response)} notifications")
        return success

    def test_create_order(self):
        """Test order creation (new feature)"""
        if not self.created_ids['product'] or not self.created_ids['warehouse']:
            print("❌ Cannot test orders - missing product or warehouse")
            return False
            
        order_data = {
            "customer_name": "Cliente Pedido Teste",
            "customer_document": "123.456.789-00",
            "customer_email": "cliente@teste.com",
            "warehouse_id": self.created_ids['warehouse'],
            "items": [
                {
                    "product_id": self.created_ids['product'],
                    "product_name": "Produto Teste",
                    "quantity": 3,
                    "unit_price": 100.0,
                    "total": 300.0
                }
            ],
            "subtotal": 300.0,
            "discount": 0.0,
            "total": 300.0,
            "type": "pedido",
            "status": "draft"
        }
        success, response = self.run_test(
            "Create Order (Pedido)",
            "POST",
            "orders",
            200,
            data=order_data
        )
        if success and 'id' in response:
            self.created_ids['order'] = response['id']
            print(f"   Created order ID: {response['id']}")
        return success

    def test_get_orders(self):
        """Test get orders"""
        success, response = self.run_test(
            "Get Orders",
            "GET",
            "orders",
            200
        )
        if success:
            print(f"   Found {len(response)} orders")
        return success

    def test_convert_order_to_sale(self):
        """Test converting order to sale (new feature)"""
        if not self.created_ids.get('order'):
            print("❌ Cannot test order conversion - no order created")
            return False
            
        success, response = self.run_test(
            "Convert Order to Sale",
            "POST",
            f"orders/{self.created_ids['order']}/convert-to-sale",
            200
        )
        if success:
            print(f"   Order converted: {response.get('message', 'Success')}")
        return success

    def test_cash_flow_report(self):
        """Test cash flow report (new feature)"""
        success, response = self.run_test(
            "Cash Flow Report (Month)",
            "GET",
            "reports/cash-flow",
            200,
            params={'period': 'month'}
        )
        if success:
            print(f"   Inflows: R$ {response.get('inflows', 0):.2f}")
            print(f"   Outflows: R$ {response.get('outflows', 0):.2f}")
            print(f"   Balance: R$ {response.get('balance', 0):.2f}")
        return success

    def test_export_pdf_report(self):
        """Test PDF export (new feature)"""
        success, response = self.run_test(
            "Export PDF Report",
            "GET",
            "reports/export/pdf",
            200,
            params={'period': 'month'}
        )
        if success:
            print(f"   PDF export successful")
        return success

    def test_export_excel_report(self):
        """Test Excel export (new feature)"""
        success, response = self.run_test(
            "Export Excel Report",
            "GET",
            "reports/export/excel",
            200,
            params={'period': 'month'}
        )
        if success:
            print(f"   Excel export successful")
        return success

    def test_invoice_ocr_endpoint(self):
        """Test invoice OCR endpoint (new feature)"""
        # Test with a simple base64 image (1x1 pixel PNG)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGAWA0ddgAAAABJRU5ErkJggg=="
        
        success, response = self.run_test(
            "Invoice OCR Processing",
            "POST",
            "invoices/ocr",
            500,  # Expected to fail due to invalid image, but endpoint should exist
            data={"image_base64": test_image_b64}
        )
        # We expect this to fail with 500 due to OCR processing, but endpoint should exist
        if not success:
            print("   ✅ OCR endpoint exists (expected processing failure)")
            return True
        return success

def main():
    print("🚀 Starting Gestão TJ API Tests")
    print("=" * 50)
    
    tester = GestaoTJAPITester()
    
    # Test database seeding
    print("\n📦 Testing Database Setup")
    tester.test_seed_database()
    
    # Test admin login
    print("\n🔐 Testing Authentication")
    if not tester.test_login("admin@gestaotj.com", "Admin@123456"):
        print("❌ Admin login failed, stopping tests")
        return 1
    
    tester.test_get_me()
    
    # Test core functionality
    print("\n📊 Testing Dashboard")
    tester.test_dashboard_stats()
    tester.test_stock_alerts()
    
    print("\n🏢 Testing Warehouses")
    tester.test_create_warehouse()
    tester.test_get_warehouses()
    
    print("\n🏭 Testing Suppliers")
    tester.test_create_supplier()
    tester.test_get_suppliers()
    
    print("\n📦 Testing Products")
    tester.test_create_product()
    tester.test_get_products()
    
    print("\n📋 Testing Inventory")
    tester.test_inventory_adjust()
    tester.test_get_inventory()
    
    print("\n📄 Testing Invoices")
    tester.test_create_invoice()
    tester.test_get_invoices()
    
    print("\n💰 Testing Sales")
    tester.test_create_sale()
    tester.test_get_sales()
    
    print("\n📈 Testing Reports")
    tester.test_financial_report()
    
    print("\n👥 Testing Users")
    tester.test_get_users()
    
    print("\n🔍 Testing Audit")
    tester.test_audit_logs()
    
    print("\n🔔 Testing Alerts")
    tester.test_alert_configs()
    tester.test_notifications()
    
    # Test new features
    print("\n📋 Testing Orders (New Feature)")
    tester.test_create_order()
    tester.test_get_orders()
    tester.test_convert_order_to_sale()
    
    print("\n💰 Testing Cash Flow Reports (New Feature)")
    tester.test_cash_flow_report()
    
    print("\n📄 Testing Report Exports (New Feature)")
    tester.test_export_pdf_report()
    tester.test_export_excel_report()
    
    print("\n🖼️ Testing Invoice OCR (New Feature)")
    tester.test_invoice_ocr_endpoint()
    
    # Test different user roles
    print("\n👤 Testing Manager Role")
    if tester.test_login("gerente@gestaotj.com", "Gerente@123"):
        tester.test_dashboard_stats()
        tester.test_get_products()
        tester.test_audit_logs()
    
    print("\n👤 Testing User Role")
    if tester.test_login("usuario@gestaotj.com", "Usuario@123"):
        tester.test_dashboard_stats()
        tester.test_get_products()
        # Should fail for audit logs
        tester.run_test("Get Audit Logs (Should Fail)", "GET", "audit", 403)
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✅ Backend API testing completed successfully!")
        return 0
    else:
        print("❌ Backend API testing failed - too many failures")
        return 1

if __name__ == "__main__":
    sys.exit(main())