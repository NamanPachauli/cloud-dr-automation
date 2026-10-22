
import os

import requests

BASE_URL = os.getenv("APP_TEST_URL", "http://127.0.0.1:8080")


def test_home_endpoint():
    response = requests.get(f"{BASE_URL}/", timeout=5)
    assert response.status_code == 200
    assert "LocalStack simulation" in response.text


def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_backup_and_restore():
    payload = {
        "service": "cloud-dr-demo",
        "environment": "test",
        "record": 123,
    }

    created = requests.post(
        f"{BASE_URL}/backup",
        json=payload,
        timeout=10,
    )
    assert created.status_code == 201

    key = created.json()["key"]

    restored = requests.post(
        f"{BASE_URL}/restore",
        json={"key": key},
        timeout=10,
    )
    assert restored.status_code == 200
    assert restored.json()["restored_data"] == payload


def test_metrics_endpoint():
    response = requests.get(f"{BASE_URL}/metrics", timeout=5)
    assert response.status_code == 200
    assert "cloud_dr_requests_total" in response.text
