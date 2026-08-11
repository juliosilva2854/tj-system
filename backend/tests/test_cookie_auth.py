"""Tests for HttpOnly cookie-based authentication (Phase 1 remediation).

Validates:
- Login sets httpOnly access_token and refresh_token cookies
- Login body returns only {user: ...} (no tokens leaked)
- /auth/me works via cookie alone
- /auth/me works via Authorization Bearer header (backward compat)
- /auth/me without auth returns 401
- /auth/refresh works via cookie
- /auth/logout clears cookies (Max-Age=0)
- Other authenticated endpoints work via cookie
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-edit-perms.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN_CREDS = {"identifier": "admin.tj", "password": "Admin@2026", "is_master": False}
MASTER_CREDS = {"identifier": "master@sconnecta.com.br", "password": "Master@2026", "is_master": True}


def _login(session, creds):
    # Tiny backoff to avoid rate-limit collisions across test functions
    for attempt in range(3):
        r = session.post(f"{API}/auth/login", json=creds)
        if r.status_code != 429:
            return r
        time.sleep(7)
    return r


# === Login: cookies set + body shape ===

def test_login_admin_username_sets_cookies_and_no_token_in_body():
    s = requests.Session()
    r = _login(s, ADMIN_CREDS)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"

    body = r.json()
    assert "user" in body
    assert body["user"]["username"] == "admin.tj"
    # No tokens in body
    assert "access_token" not in body
    assert "refresh_token" not in body
    assert "token" not in body

    # Cookies set
    cookies = {c.name: c for c in s.cookies}
    assert "access_token" in cookies, f"Cookies: {list(cookies.keys())}"
    assert "refresh_token" in cookies

    # httpOnly flag check via Set-Cookie header
    raw = r.headers.get("set-cookie", "") or ""
    raw_lower = raw.lower()
    assert "httponly" in raw_lower, f"Set-Cookie missing HttpOnly: {raw}"


def test_login_master_email_sets_cookies():
    s = requests.Session()
    r = _login(s, MASTER_CREDS)
    assert r.status_code == 200, f"Master login failed: {r.status_code} {r.text}"
    body = r.json()
    assert body["user"]["is_master_access"] is True
    assert "access_token" in {c.name for c in s.cookies}
    assert "refresh_token" in {c.name for c in s.cookies}


# === /auth/me ===

def test_me_without_auth_returns_401():
    r = requests.get(f"{API}/auth/me")
    assert r.status_code == 401


def test_me_with_cookie_only():
    s = requests.Session()
    lr = _login(s, ADMIN_CREDS)
    assert lr.status_code == 200
    r = s.get(f"{API}/auth/me")
    assert r.status_code == 200, f"/auth/me via cookie failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["username"] == "admin.tj"
    assert "password_hash" not in data


def test_me_with_bearer_header_fallback():
    """Backward compat: a non-browser client passing JWT in Authorization should still work.
    We obtain a token by calling /auth/login then reading the access_token cookie value as the JWT.
    """
    s = requests.Session()
    lr = _login(s, ADMIN_CREDS)
    assert lr.status_code == 200
    token = s.cookies.get("access_token")
    assert token, "access_token cookie missing"

    # Use a fresh session (no cookies) and pass Authorization
    s2 = requests.Session()
    r = s2.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"Bearer fallback failed: {r.status_code} {r.text}"
    assert r.json()["username"] == "admin.tj"


# === /auth/refresh ===

def test_refresh_with_cookie():
    s = requests.Session()
    lr = _login(s, ADMIN_CREDS)
    assert lr.status_code == 200
    old_access = s.cookies.get("access_token")
    # Wait 1s so the new JWT has a different iat
    time.sleep(1)
    r = s.post(f"{API}/auth/refresh")
    assert r.status_code == 200, f"Refresh failed: {r.status_code} {r.text}"
    new_access = s.cookies.get("access_token")
    assert new_access, "access_token cookie not re-set after refresh"
    assert new_access != old_access, "access_token did not rotate"


# === /auth/logout clears cookies ===

def test_logout_clears_cookies():
    s = requests.Session()
    lr = _login(s, ADMIN_CREDS)
    assert lr.status_code == 200
    r = s.post(f"{API}/auth/logout")
    assert r.status_code == 200
    set_cookie = r.headers.get("set-cookie", "") or ""
    # Should contain Max-Age=0 (delete_cookie semantics) for both cookies
    sc_lower = set_cookie.lower()
    assert "access_token=" in sc_lower
    assert "refresh_token=" in sc_lower
    assert "max-age=0" in sc_lower, f"Logout did not set Max-Age=0: {set_cookie}"


# === Other authenticated endpoints via cookie ===

def test_dashboard_stats_via_cookie():
    s = requests.Session()
    lr = _login(s, ADMIN_CREDS)
    assert lr.status_code == 200
    r = s.get(f"{API}/dashboard/stats")
    assert r.status_code == 200, f"/dashboard/stats via cookie failed: {r.status_code} {r.text}"
    # Should be a JSON object with at least some keys
    data = r.json()
    assert isinstance(data, dict)


def test_notifications_unread_count_via_cookie():
    s = requests.Session()
    lr = _login(s, ADMIN_CREDS)
    assert lr.status_code == 200
    r = s.get(f"{API}/notifications/unread-count")
    assert r.status_code == 200, f"/notifications/unread-count via cookie failed: {r.status_code} {r.text}"
    data = r.json()
    assert "count" in data
    assert isinstance(data["count"], int)


def test_invalid_credentials_returns_401_and_no_cookie():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"identifier": "admin.tj", "password": "wrong"})
    assert r.status_code == 401
    assert "access_token" not in {c.name for c in s.cookies}
