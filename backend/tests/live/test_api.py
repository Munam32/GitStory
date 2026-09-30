#!/usr/bin/env python3
"""GitStory Backend Test Script - Tests all API endpoints."""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8005"
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "testpass123"
TEST_NAME = "Test User"


def test_all():
    print("\n" + "=" * 60)
    print("  GitStory API Test Suite")
    print("=" * 60 + "\n")

    results = {"passed": 0, "failed": 0}
    access_token = None
    refresh_token = None

    # Test 1: Health check
    print("[1] Health Check")
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=5)
        if resp.status_code == 200:
            print("  [PASS] - Health check")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Health check (status {resp.status_code})")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Health check: {e}")
        results["failed"] += 1

    # Test 2: Register
    print("\n[2] Register User")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": TEST_NAME},
            timeout=10
        )
        if resp.ok:
            data = resp.json().get("data", {})
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            print(f"  [PASS] - Register user ({TEST_EMAIL})")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Register user: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Register user: {e}")
        results["failed"] += 1

    # Test 3: Login
    print("\n[3] Login")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10
        )
        if resp.ok:
            data = resp.json().get("data", {})
            if not access_token:
                access_token = data.get("access_token")
            if not refresh_token:
                refresh_token = data.get("refresh_token")
            print("  [PASS] - Login")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Login: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Login: {e}")
        results["failed"] += 1

    if not access_token:
        print("\n[?] Skipping protected endpoints - no valid token")
        print(f"\nResults: {results['passed']} passed, {results['failed']} failed")
        return results["failed"] == 0

    headers = {"Authorization": f"Bearer {access_token}"}

    # Test 4: Get profile
    print("\n[4] Get Profile")
    try:
        resp = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=10)
        if resp.ok:
            print("  [PASS] - Get profile")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Get profile: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Get profile: {e}")
        results["failed"] += 1

    # Test 5: Update GitHub token
    print("\n[5] Update GitHub Token")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/github-token",
            json={"token": "ghp_test123"},
            headers=headers,
            timeout=10
        )
        if resp.ok:
            print("  [PASS] - Update GitHub token")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Update GitHub token: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Update GitHub token: {e}")
        results["failed"] += 1

    # Test 6: Get repositories
    print("\n[6] Get Repositories")
    try:
        resp = requests.get(f"{BASE_URL}/api/repositories", headers=headers, timeout=10)
        if resp.ok:
            print("  [PASS] - Get repositories")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Get repositories: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Get repositories: {e}")
        results["failed"] += 1

    # Test 7: Save repository
    print("\n[7] Save Repository")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/repositories",
            json={
                "name": "test-repo",
                "full_name": "testuser/test-repo",
                "url": "https://github.com/testuser/test-repo",
                "description": "Test repo",
                "is_private": False
            },
            headers=headers,
            timeout=10
        )
        if resp.ok:
            print("  [PASS] - Save repository")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Save repository: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Save repository: {e}")
        results["failed"] += 1

    # Test 8: Analyze repo (may timeout - requires external services)
    print("\n[8] Analyze Repo")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"repo_target": "https://github.com/facebook/react", "is_private": False},
            headers=headers,
            timeout=60
        )
        if resp.ok:
            print("  [PASS] - Analyze repo")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Analyze repo: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Analyze repo: {e}")
        results["failed"] += 1

    # Test 9: Timeline (may fail - requires openai)
    print("\n[9] Timeline")
    try:
        resp = requests.get(
            f"{BASE_URL}/api/timeline?repo_url=https://github.com/facebook/react",
            headers=headers,
            timeout=60
        )
        if resp.ok:
            print("  [PASS] - Timeline")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Timeline: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Timeline: {e}")
        results["failed"] += 1

    # Test 10: Hotzone (may fail - requires modules)
    print("\n[10] Hotzone")
    try:
        resp = requests.get(
            f"{BASE_URL}/api/hotzone?repo_url=https://github.com/facebook/react",
            headers=headers,
            timeout=60
        )
        if resp.ok:
            print("  [PASS] - Hotzone")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Hotzone: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Hotzone: {e}")
        results["failed"] += 1

    # Test 11: Index repo (may fail - requires RAG setup)
    print("\n[11] Index Repo")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/index-repo",
            json={"repo_url": "https://github.com/facebook/react", "is_private": False},
            headers=headers,
            timeout=30
        )
        if resp.ok:
            print("  [PASS] - Index repo")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Index repo: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Index repo: {e}")
        results["failed"] += 1

    # Test 12: Chat (may fail - requires RAG setup)
    print("\n[12] Chat")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "What is this?", "repo_name": "react"},
            headers=headers,
            timeout=30
        )
        if resp.ok or resp.status_code == 404:
            print("  [PASS] - Chat (endpoint works)")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Chat: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Chat: {e}")
        results["failed"] += 1

    # Test 13: Refresh token
    print("\n[13] Refresh Token")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=10
        )
        if resp.ok:
            data = resp.json().get("data", {})
            access_token = data.get("access_token")
            print("  [PASS] - Refresh token")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Refresh token: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Refresh token: {e}")
        results["failed"] += 1

    # Test 14: Forgot password
    print("\n[14] Forgot Password")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": TEST_EMAIL},
            timeout=10
        )
        if resp.ok:
            data = resp.json().get("data", {})
            reset_token = data.get("reset_token")
            print("  [PASS] - Forgot password")
            results["passed"] += 1

            # Test 15: Reset password
            print("\n[15] Reset Password")
            try:
                resp = requests.post(
                    f"{BASE_URL}/api/auth/reset-password",
                    json={"token": reset_token, "new_password": "newpass123"},
                    timeout=10
                )
                if resp.ok:
                    print("  [PASS] - Reset password")
                    results["passed"] += 1

                    # Test new password works
                    print("\n[15b] Login with new password")
                    try:
                        resp = requests.post(
                            f"{BASE_URL}/api/auth/login",
                            json={"email": TEST_EMAIL, "password": "newpass123"},
                            timeout=10
                        )
                        if resp.ok:
                            data = resp.json().get("data", {})
                            access_token = data.get("access_token")
                            refresh_token = data.get("refresh_token")
                            print("  [PASS] - Login with new password")
                            results["passed"] += 1
                        else:
                            print(f"  [FAIL] - Login with new password: {resp.text[:80]}")
                            results["failed"] += 1
                    except Exception as e:
                        print(f"  [FAIL] - Login with new password: {e}")
                        results["failed"] += 1
                else:
                    print(f"  [FAIL] - Reset password: {resp.text[:80]}")
                    results["failed"] += 1
            except Exception as e:
                print(f"  [FAIL] - Reset password: {e}")
                results["failed"] += 1
        else:
            print(f"  [FAIL] - Forgot password: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Forgot password: {e}")
        results["failed"] += 1

    # Test 16: Logout
    print("\n[16] Logout")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/logout",
            json={"refresh_token": refresh_token},
            headers=headers,
            timeout=10
        )
        if resp.ok:
            print("  [PASS] - Logout")
            results["passed"] += 1
        else:
            print(f"  [FAIL] - Logout: {resp.text[:80]}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] - Logout: {e}")
        results["failed"] += 1

    print("\n" + "=" * 60)
    print(f"  Results: {results['passed']} passed, {results['failed']} failed")
    print("=" * 60 + "\n")

    return results["failed"] == 0


if __name__ == "__main__":
    print("Make sure backend is running: python -m uvicorn src.main:app --port 8000")
    success = test_all()
    sys.exit(0 if success else 1)