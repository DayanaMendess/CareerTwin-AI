from app.main import app


def test_home():
    client = app.test_client()
    result = client.get("/")
    assert result.status_code == 200
    assert b"CareerTwin AI" in result.data


def test_health():
    result = app.test_client().get("/health")
    assert result.status_code == 200
    assert result.json["status"] == "ok"
    assert result.json["models_loaded"] is False
