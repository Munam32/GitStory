#!/usr/bin/env python3
import requests
import sys

BASE_URL = "http://localhost:8001"

print("Testing auth endpoints...")

# Test 1: Health
try:
    r = requests.get(f"{BASE_URL}/", timeout=5)
    print(f"Health: {r.status_code}")
except Exception as e:
    print(f"Health error: {e}")

# Test 2: Register
try:
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": "test@example.com", "password": "pass123", "name": "Test"},
        timeout=10
    )
    print(f"Register: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Response: {data}")
    else:
        print(f"  Error: {r.text[:100]}")
except Exception as e:
    print(f"Register error: {e}")

print("Done")