import requests
import sys

BASE_URL = "http://localhost:8004"

print("1. Health check...", end=" ")
r = requests.get(f"{BASE_URL}/", timeout=5)
print(f"{r.status_code}")

print("2. Register...", end=" ")
r = requests.post(f"{BASE_URL}/api/auth/register", json={"email": "testX@test.com", "password": "pass123", "name": "Test"}, timeout=10)
print(f"{r.status_code} - {r.text[:100] if r.text else 'OK'}")

print("3. Login...", end=" ")
r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "testX@test.com", "password": "pass123"}, timeout=10)
print(f"{r.status_code} - {r.text[:100] if r.text else 'OK'}")
if r.ok:
    data = r.json().get("data", {})
    access = data.get("access_token")
    refresh = data.get("refresh_token")
    print(f"   Tokens: access={access[:20]}... refresh={refresh[:20]}...")

    print("4. Get profile...", end=" ")
    r = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {access}"}, timeout=10)
    print(f"{r.status_code}")

    print("5. Refresh token...", end=" ")
    r = requests.post(f"{BASE_URL}/api/auth/refresh", json={"refresh_token": refresh}, timeout=10)
    print(f"{r.status_code}")

    print("6. Forgot password...", end=" ")
    r = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": "testX@test.com"}, timeout=10)
    print(f"{r.status_code} - {r.text[:150] if r.text else 'OK'}")

    print("Done!")
else:
    print(f"Login failed: {r.text}")