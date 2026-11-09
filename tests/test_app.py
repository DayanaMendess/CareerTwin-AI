
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
    assert result.json["models_loaded"] is True


def test_api_health():
    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_analyze_profile_invalid():
    response = app.test_client().post(
        "/api/analyze-profile",
        json={"profile_text": ""}
    )

    assert response.status_code == 400



def test_analyze_profile_success(monkeypatch):
    from app import servicio_ia

    def modelo_simulado(texto):
        return {
            "status": "ok",
            "models_loaded": True,
            "umbral_modelo": 0.2,
            "habilidades_detectadas": [
                {"habilidad": "python", "fuente": "texto+modelo"}
            ],
            "total_habilidades": 1
        }

    monkeypatch.setattr(
        servicio_ia, "analizar_perfil", modelo_simulado
    )

    response = app.test_client().post(
        "/api/analyze-profile",
        json={"profile_text": "I have experience with Python"}
    )

    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["total_habilidades"] == 1


def test_analyze_profile_without_model(monkeypatch):
    from app import servicio_ia

    def modelo_no_disponible(texto):
        raise FileNotFoundError("Modelo no encontrado")

    monkeypatch.setattr(
        servicio_ia, "analizar_perfil", modelo_no_disponible
    )

    response = app.test_client().post(
        "/api/analyze-profile",
        json={"profile_text": "I have experience with Python"}
    )

    assert response.status_code == 503
    assert response.json["models_loaded"] is False

