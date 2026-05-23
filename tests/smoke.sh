#!/usr/bin/env bash
set -e
BASE="http://localhost:8001/api"
log() { echo -e "\n=== $1 ==="; }

login() {
  curl -s -X POST "$BASE/auth/login" -H "Content-Type: application/json" -d "{\"email\":\"$1\",\"password\":\"$2\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])"
}

# Login all
log "Login Master/Admin/Logistica/Operacional"
TM=$(login master@sconnecta.com.br Master@2026)
TA=$(login admin@tj.sconnecta.com.br Admin@2026)
TL=$(login logistica@tj.sconnecta.com.br Logistica@2026)
TO=$(login operacional@tj.sconnecta.com.br Operacional@2026)
echo "Master token ok=${#TM}, Admin=${#TA}, Logistica=${#TL}, Operacional=${#TO}"

# Auth me
log "Auth/me for Operacional"
curl -s "$BASE/auth/me" -H "Authorization: Bearer $TO" | python3 -m json.tool

# Warehouses
log "List warehouses (Admin)"
WH=$(curl -s "$BASE/warehouses" -H "Authorization: Bearer $TA")
echo "$WH" | python3 -m json.tool
PAI_ID=$(echo "$WH" | python3 -c "import sys,json;[print(w['id']) for w in json.load(sys.stdin) if w['type']=='pai']")
FILHO_ID=$(echo "$WH" | python3 -c "import sys,json;[print(w['id']) for w in json.load(sys.stdin) if w['type']=='filho']")
echo "PAI=$PAI_ID, FILHO=$FILHO_ID"

# Operacional should only see their FILHO
log "List warehouses (Operacional - should be 1 FILHO only)"
curl -s "$BASE/warehouses" -H "Authorization: Bearer $TO" | python3 -c "import sys,json;w=json.load(sys.stdin);print(f'count={len(w)}');[print(x['name'],x['type']) for x in w]"

# Suppliers
log "Create supplier (Admin)"
curl -s -X POST "$BASE/suppliers" -H "Authorization: Bearer $TA" -H "Content-Type: application/json" \
  -d '{"name":"ACME","cnpj":"00.000.000/0001-00","email":"acme@test.com","phone":"11999"}' | python3 -m json.tool

# Create a product directly (bypass invoice) for testing
log "Create product (Admin)"
PROD=$(curl -s -X POST "$BASE/products" -H "Authorization: Bearer $TA" -H "Content-Type: application/json" \
  -d '{"name":"Sabao em po","sku":"SAB001","unit":"UN","cost_price":12.5,"min_stock":5}')
echo "$PROD" | python3 -m json.tool
PID=$(echo "$PROD" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

# Manually inject available_qty (since no invoice). We'll use inventory.adjust to set PAI stock.
log "Adjust PAI stock +50 of product (Admin)"
curl -s -X POST "$BASE/inventory/adjust?product_id=$PID&warehouse_id=$PAI_ID&quantity=50" -H "Authorization: Bearer $TA" | python3 -m json.tool

# Inventory view
log "Inventory (Admin sees both)"
curl -s "$BASE/inventory" -H "Authorization: Bearer $TA" | python3 -m json.tool

log "Inventory (Operacional sees only FILHO)"
curl -s "$BASE/inventory" -H "Authorization: Bearer $TO" | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'count={len(d)}');[print(i['product_name'],'@',i['warehouse_name'],'=',i['quantity']) for i in d]"

# Operacional creates requisition for 10 units
log "Operacional creates requisition (10 unidades)"
REQ=$(curl -s -X POST "$BASE/requisitions" -H "Authorization: Bearer $TO" -H "Content-Type: application/json" \
  -d "{\"items\":[{\"product_id\":\"$PID\",\"product_name\":\"Sabao em po\",\"quantity\":10}],\"notes\":\"teste\"}")
echo "$REQ" | python3 -m json.tool
RID=$(echo "$REQ" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

# Logistica approves
log "Logistica approves requisition"
curl -s -X POST "$BASE/requisitions/$RID/approve" -H "Authorization: Bearer $TL" | python3 -m json.tool

# Check inventory: PAI=40, FILHO=10
log "Final inventory check"
curl -s "$BASE/inventory" -H "Authorization: Bearer $TA" | python3 -c "import sys,json;d=json.load(sys.stdin);[print(i['warehouse_name'],i['warehouse_type'],'=',i['quantity']) for i in d]"

# Dashboard stats
log "Dashboard stats (Admin)"
curl -s "$BASE/dashboard/stats" -H "Authorization: Bearer $TA" | python3 -m json.tool

# IDOR test: Operacional tries to approve (should be 403)
log "IDOR: Operacional tries to approve requisition (expect 403)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST "$BASE/requisitions/$RID/approve" -H "Authorization: Bearer $TO"

# Tenants list (Master only)
log "Tenants list (Master)"
curl -s "$BASE/tenants" -H "Authorization: Bearer $TM" | python3 -m json.tool

# Admin tries tenants list -> 403
log "Tenants list (Admin, expect 403)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$BASE/tenants" -H "Authorization: Bearer $TA"

# Audit
log "Audit list (Admin)"
curl -s "$BASE/audit" -H "Authorization: Bearer $TA" | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'count={len(d)}');[print(l['action'],l['entity_type'],l['user_email']) for l in d[:10]]"

echo -e "\n=== SMOKE TEST COMPLETED ==="
