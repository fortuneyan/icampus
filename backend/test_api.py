"""Test script for API testing"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"
ADMIN = {"username": "admin", "password": "admin123"}


def test_login():
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json=ADMIN)
    print(f"Login: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        return data["data"]["access_token"]
    return None


def test_grades(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{BASE_URL}/api/v1/edu/grades?page=1&page_size=5", headers=headers
    )
    print(f"Grades: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total grades: {data.get('total', 0)}")
        for item in data.get("items", [])[:3]:
            print(f"  - {item.get('name')} ({item.get('code')})")


def test_classes(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{BASE_URL}/api/v1/edu/classes?page=1&page_size=5", headers=headers
    )
    print(f"Classes: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total classes: {data.get('total', 0)}")


def test_students(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{BASE_URL}/api/v1/edu/students?page=1&page_size=5", headers=headers
    )
    print(f"Students: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total students: {data.get('total', 0)}")


def test_courses(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{BASE_URL}/api/v1/edu/courses?page=1&page_size=5", headers=headers
    )
    print(f"Courses: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total courses: {data.get('total', 0)}")


if __name__ == "__main__":
    print("Testing Smart Campus API...")
    token = test_login()
    if token:
        print(f"Token: {token[:20]}...")
        test_grades(token)
        test_classes(token)
        test_students(token)
        test_courses(token)
    else:
        print("Login failed!")
