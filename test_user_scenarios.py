#!/usr/bin/env python3
"""
Test scenarios requested by user for Gestao TJ backend.
Tests authentication, profile, password recovery, users list, and health check.
"""
import requests
import json
from typing import Dict, Any, Optional

# Use the public backend URL from frontend/.env
BASE_URL = "https://admin-edit-perms.preview.emergentagent.com"
API = f"{BASE_URL}/api"

def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_result(success: bool, message: str, details: Optional[str] = None):
    """Print test result."""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")
    if details:
        print(f"   {details}")
    print()

def test_login_username():
    """Test 1: Login with username admin.tj"""
    print_section("TEST 1: Login com Username (admin.tj)")
    
    try:
        response = requests.post(
            f"{API}/auth/login",
            json={
                "identifier": "admin.tj",
                "password": "Admin@2026",
                "is_master": False
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                user = data["user"]
                print_result(
                    True,
                    "Login com username bem-sucedido",
                    f"User: {user.get('name', 'N/A')} | Email: {user.get('email', 'N/A')} | Role: {user.get('role', 'N/A')}"
                )
                return data["access_token"]
            else:
                print_result(False, "Login retornou 200 mas sem access_token ou user", f"Response: {data}")
                return None
        else:
            print_result(False, f"Login falhou com status {response.status_code}", f"Response: {response.text}")
            return None
    except Exception as e:
        print_result(False, "Erro ao fazer login", f"Exception: {str(e)}")
        return None

def test_login_email_master():
    """Test 2: Login with email master@sconnecta.com.br (is_master: true)"""
    print_section("TEST 2: Login com Email Master (is_master: true)")
    
    try:
        response = requests.post(
            f"{API}/auth/login",
            json={
                "identifier": "master@sconnecta.com.br",
                "password": "Master@2026",
                "is_master": True
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                user = data["user"]
                is_master = user.get("is_master_access", False)
                print_result(
                    True,
                    "Login master bem-sucedido",
                    f"User: {user.get('name', 'N/A')} | is_master_access: {is_master} | Role: {user.get('role', 'N/A')}"
                )
                return data["access_token"]
            else:
                print_result(False, "Login retornou 200 mas sem access_token ou user", f"Response: {data}")
                return None
        else:
            print_result(False, f"Login master falhou com status {response.status_code}", f"Response: {response.text}")
            return None
    except Exception as e:
        print_result(False, "Erro ao fazer login master", f"Exception: {str(e)}")
        return None

def test_login_invalid():
    """Test 3: Login with invalid credentials (should return 401)"""
    print_section("TEST 3: Login com Credenciais Inválidas (deve retornar 401)")
    
    try:
        response = requests.post(
            f"{API}/auth/login",
            json={
                "identifier": "invalid.user",
                "password": "WrongPassword123",
                "is_master": False
            },
            timeout=10
        )
        
        if response.status_code == 401:
            print_result(True, "Login com credenciais inválidas corretamente rejeitado (401)", f"Response: {response.json()}")
        else:
            print_result(False, f"Esperado 401, recebido {response.status_code}", f"Response: {response.text}")
    except Exception as e:
        print_result(False, "Erro ao testar login inválido", f"Exception: {str(e)}")

def test_profile_get(token: str):
    """Test 4: GET /api/auth/profile (authenticated)"""
    print_section("TEST 4: GET /api/auth/profile (autenticado)")
    
    if not token:
        print_result(False, "Token não disponível para teste de profile")
        return None
    
    try:
        response = requests.get(
            f"{API}/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            profile = response.json()
            print_result(
                True,
                "Profile recuperado com sucesso",
                f"Nome: {profile.get('name', 'N/A')} | Email: {profile.get('email', 'N/A')} | Telefone: {profile.get('phone', 'N/A')}"
            )
            return profile
        else:
            print_result(False, f"GET profile falhou com status {response.status_code}", f"Response: {response.text}")
            return None
    except Exception as e:
        print_result(False, "Erro ao buscar profile", f"Exception: {str(e)}")
        return None

def test_profile_update(token: str, current_profile: Optional[Dict]):
    """Test 5: PUT /api/auth/profile with new data (name, phone)"""
    print_section("TEST 5: PUT /api/auth/profile (atualizar dados)")
    
    if not token:
        print_result(False, "Token não disponível para teste de atualização de profile")
        return
    
    if not current_profile:
        print_result(False, "Profile atual não disponível para teste de atualização")
        return
    
    try:
        # Update name and phone
        new_name = "Admin TJ Atualizado"
        new_phone = "(11) 99999-8888"
        
        response = requests.put(
            f"{API}/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": new_name,
                "phone": new_phone
            },
            timeout=10
        )
        
        if response.status_code == 200:
            updated_profile = response.json()
            print_result(
                True,
                "Profile atualizado com sucesso",
                f"Nome: {updated_profile.get('name', 'N/A')} | Telefone: {updated_profile.get('phone', 'N/A')}"
            )
            
            # Restore original values
            print("   Restaurando valores originais...")
            restore_response = requests.put(
                f"{API}/auth/profile",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": current_profile.get("name", "Admin TJ"),
                    "phone": current_profile.get("phone", "(11) 98888-1111")
                },
                timeout=10
            )
            if restore_response.status_code == 200:
                print("   ✅ Valores originais restaurados")
            else:
                print(f"   ⚠️  Falha ao restaurar valores originais: {restore_response.status_code}")
        else:
            print_result(False, f"PUT profile falhou com status {response.status_code}", f"Response: {response.text}")
    except Exception as e:
        print_result(False, "Erro ao atualizar profile", f"Exception: {str(e)}")

def test_forgot_password():
    """Test 6: POST /api/auth/forgot-password with identifier admin.tj"""
    print_section("TEST 6: POST /api/auth/forgot-password")
    
    try:
        response = requests.post(
            f"{API}/auth/forgot-password",
            json={"identifier": "admin.tj"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result(
                True,
                "Forgot password bem-sucedido",
                f"Message: {data.get('message', 'N/A')}"
            )
        else:
            print_result(False, f"Forgot password falhou com status {response.status_code}", f"Response: {response.text}")
    except Exception as e:
        print_result(False, "Erro ao testar forgot password", f"Exception: {str(e)}")

def test_users_list(token: str):
    """Test 7: GET /api/users (authenticated as admin)"""
    print_section("TEST 7: GET /api/users (autenticado como admin)")
    
    if not token:
        print_result(False, "Token não disponível para teste de listagem de usuários")
        return
    
    try:
        response = requests.get(
            f"{API}/users",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            users = response.json()
            print_result(
                True,
                f"Lista de usuários recuperada com sucesso ({len(users)} usuários)",
                f"Primeiros usuários: {', '.join([u.get('name', 'N/A') for u in users[:3]])}"
            )
            
            # Check for new fields (username, cpf, phone)
            if users:
                first_user = users[0]
                has_username = "username" in first_user
                has_cpf = "cpf" in first_user
                has_phone = "phone" in first_user
                print(f"   Campos novos presentes: username={has_username}, cpf={has_cpf}, phone={has_phone}")
        else:
            print_result(False, f"GET users falhou com status {response.status_code}", f"Response: {response.text}")
    except Exception as e:
        print_result(False, "Erro ao buscar lista de usuários", f"Exception: {str(e)}")

def test_health():
    """Test 8: GET /api/health"""
    print_section("TEST 8: GET /api/health")
    
    try:
        response = requests.get(f"{API}/health", timeout=10)
        
        if response.status_code == 200:
            health = response.json()
            status = health.get("status", "unknown")
            db_status = health.get("db", "unknown")
            
            if status == "healthy" and db_status == "ok":
                print_result(True, "Health check passou", f"Status: {status} | DB: {db_status}")
            else:
                print_result(False, "Health check retornou status não saudável", f"Status: {status} | DB: {db_status}")
        else:
            print_result(False, f"Health check falhou com status {response.status_code}", f"Response: {response.text}")
    except Exception as e:
        print_result(False, "Erro ao fazer health check", f"Exception: {str(e)}")

def main():
    """Run all test scenarios."""
    print("\n" + "="*80)
    print("  GESTAO TJ - TESTES DE BACKEND")
    print(f"  Backend URL: {BASE_URL}")
    print("="*80)
    
    # Test 1: Login with username
    admin_token = test_login_username()
    
    # Test 2: Login with email (master)
    master_token = test_login_email_master()
    
    # Test 3: Invalid login
    test_login_invalid()
    
    # Test 4: Get profile (using admin token)
    current_profile = test_profile_get(admin_token)
    
    # Test 5: Update profile (using admin token)
    test_profile_update(admin_token, current_profile)
    
    # Test 6: Forgot password
    test_forgot_password()
    
    # Test 7: List users (using admin token)
    test_users_list(admin_token)
    
    # Test 8: Health check
    test_health()
    
    print("\n" + "="*80)
    print("  TESTES COMPLETOS")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
