import requests
import sys
import time

BASE_URL = "http://localhost:8005"
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "testpass123"
TEST_NAME = "Test User"

print("=" * 50)
print("Auth Tests Only")
print("=" * 50)

results = {"passed": 0, "failed": 0}
access_token = None
refresh_token = None

# 1. Register
print("\n[1] Register")
try:
    r = requests.post(f"{BASE_URL}/api/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": TEST_NAME}, timeout=10)
    if r.ok:
        data = r.json().get("data", {})
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        print("  [PASS]")
        results["passed"] += 1
    else:
        print(f"  [FAIL] {r.text[:60]}")
        results["failed"] += 1
except Exception as e:
    print(f"  [FAIL] {e}")
    results["failed"] += 1

# 2. Login
print("\n[2] Login")
try:
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}, timeout=10)
    if r.ok:
        data = r.json().get("data", {})
        if not access_token: access_token = data.get("access_token")
        if not refresh_token: refresh_token = data.get("refresh_token")
        print("  [PASS]")
        results["passed"] += 1
    else:
        print(f"  [FAIL] {r.text[:60]}")
        results["failed"] += 1
except Exception as e:
    print(f"  [FAIL] {e}")
    results["failed"] += 1

if not access_token:
    print("\n[!] No token, skipping protected tests")
    sys.exit(1)

headers = {"Authorization": f"Bearer {access_token}"}

# 3. Get Profile
print("\n[3] Get Profile")
try:
    r = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=10)
    print("  [PASS]" if r.ok else f"  [FAIL] {r.text[:60]}")
    results["passed" if r.ok else "failed"] += 1
except Exception as e:
    print(f"  [FAIL] {e}")
    results["failed"] += 1

# 4. Refresh Token
print("\n[4] Refresh Token")
try:
    r = requests.post(f"{BASE_URL}/api/auth/refresh", json={"refresh_token": refresh_token}, timeout=10)
    if r.ok:
        access_token = r.json().get("data", {}).get("access_token")
        print("  [PASS]")
        results["passed"] += 1
    else:
        print(f"  [FAIL] {r.text[:60]}")
        results["failed"] += 1
except Exception as e:
    print(f"  [FAIL] {e}")
    results["failed"] += 1

# 5. Forgot Password
print("\n[5] Forgot Password")
try:
    r = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": TEST_EMAIL}, timeout=10)
    reset_token = r.json().get("data", {}).get("reset_token") if r.ok else None
    print("  [PASS]" if r.ok else f"  [FAIL] {r.text[:60]}")
    results["passed" if r.ok else "failed"] += 1
except Exception as e:
    print(f"  [FAIL] {e}")
    results["failed"] += 1

# 6. Reset Password
print("\n[6] Reset Password")
try:
    r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": reset_token, "new_password": "newpass123"}, timeout=10)
    print("  [PASS]" if r.ok else f"  [FAIL] {r.text[:60]}")
    results["passed" if r.ok else "failed"] += 1
except Exception as e:
    print(f"  [FAIL] {e}")
    results["failed"] += 1

# 7. Login with new password
print("\n[7] Login with new password")
try:
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": TEST_EMAIL, "password": "newpass123"}, timeout=10)
    if r.ok:
        data = r.json().get("data", {})
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        print("  [PASS]")
        results["passed"] += 1
    else:
        print(f"  [FAIL] {r.text[:60]}")
        results["failed"] += 1
except Exception as e:
    print(f"  [FAIL] {e}")
    results["failed"] += 1

# 8. Logout
print("\n[8] Logout")
try:
    r = requests.post(f"{BASE_URL}/api/auth/logout", json={"refresh_token": refresh_token}, headers=headers, timeout=10)
    print("  [PASS]" if r.ok else f"  [FAIL] {r.text[:60]}")
    results["passed" if r.ok else "failed"] += 1
except Exception as e:
    print(f"  [FAIL] {e}")
    results["failed"] += 1

print("\n" + "=" * 50)
print(f"Results: {results['passed']} passed, {results['failed']} failed")
print("=" * 50)