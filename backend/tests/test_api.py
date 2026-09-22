import os
os.environ["DATABASE_URL"] = "sqlite:///./test_brokeproof.db"
os.environ["SECRET_KEY"] = "test-secret"

from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app


def auth_headers(client):
    today = date.today()
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Demo Student",
            "email": "demo@example.com",
            "password": "password123",
            "starting_balance": 10000,
            "cycle_start": (today - timedelta(days=2)).isoformat(),
            "cycle_end": (today + timedelta(days=27)).isoformat(),
        },
    )
    if response.status_code == 409:
        response = client.post("/api/auth/login", json={"email": "demo@example.com", "password": "password123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_add_transaction_dashboard():
    with TestClient(app) as client:
        headers = auth_headers(client)
        tx = client.post(
            "/api/transactions/manual",
            headers=headers,
            json={"amount": 250, "merchant": "Swiggy", "category": "Food"},
        )
        assert tx.status_code == 200
        dash = client.get("/api/dashboard", headers=headers)
        assert dash.status_code == 200
        body = dash.json()
        assert body["spent"] >= 250
        assert "safe_to_spend_today" in body
        assert "broke_date" in body
