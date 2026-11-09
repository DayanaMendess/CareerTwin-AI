
"""Pruebas del endpoint Fraud Shield."""

from unittest.mock import patch

from app.main import app


def test_fraude_respuesta_exitosa():
    resultado = {
        "status": "ok",
        "riesgo_detectado": False,
        "clasificacion": "sin_indicios_suficientes",
        "puntuacion_modelo": 0.2745,
        "umbral": 0.6,
        "advertencia": "Resultado orientativo.",
    }

    with patch(
        "app.servicio_fraude.analizar_oferta",
        return_value=resultado,
    ) as mock_analizar:
        cliente = app.test_client()
        respuesta = cliente.post(
            "/api/fraud-risk",
            json={"job_text": "Oferta laboral de ejemplo"},
        )

    assert respuesta.status_code == 200
    assert respuesta.get_json() == resultado
    mock_analizar.assert_called_once_with(
        "Oferta laboral de ejemplo"
    )


def test_fraude_texto_vacio():
    cliente = app.test_client()
    respuesta = cliente.post(
        "/api/fraud-risk",
        json={"job_text": ""},
    )

    assert respuesta.status_code == 400


def test_fraude_sin_texto():
    cliente = app.test_client()
    respuesta = cliente.post(
        "/api/fraud-risk",
        json={},
    )

    assert respuesta.status_code == 400


def test_fraude_modelo_no_disponible():
    with patch(
        "app.servicio_fraude.analizar_oferta",
        side_effect=FileNotFoundError("Modelo ausente"),
    ):
        cliente = app.test_client()
        respuesta = cliente.post(
            "/api/fraud-risk",
            json={"job_text": "Oferta laboral de ejemplo"},
        )

    assert respuesta.status_code == 503
    assert respuesta.get_json()["status"] == "model_unavailable"


def test_fraude_texto_demasiado_largo():
    cliente = app.test_client()
    respuesta = cliente.post(
        "/api/fraud-risk",
        json={"job_text": "A" * 20001},
    )

    assert respuesta.status_code == 400
