from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_decide_and_latest_flow():
    client = TestClient(app)
    post_resp = client.post("/decide", params={"symbol": "AAPL"})
    assert post_resp.status_code == 200
    decision = post_resp.json()
    assert decision["symbol"] == "AAPL"

    get_resp = client.get("/latest", params={"symbol": "AAPL"})
    assert get_resp.status_code == 200
    latest = get_resp.json()
    assert latest["symbol"] == "AAPL"
    assert latest["action"] in {"BUY", "SELL", "HOLD"}
