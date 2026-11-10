"""Prueba que la app usa el mismo procesamiento de texto que el entrenamiento."""
from unittest.mock import patch

from app import servicio_fraude
from src.data_pipeline.fraude_utils import texto_para_modelo


class ModeloFalso:
    """Guarda el texto que recibe y devuelve una puntuación fija."""

    def __init__(self):
        self.recibido = None

    def predict_proba(self, textos):
        self.recibido = textos
        return [[0.3, 0.7]]


def test_app_aplica_texto_para_modelo_antes_de_predecir():
    modelo = ModeloFalso()
    oferta = "<p>Earn $500/day! Write to hr@fast.co or visit https://fast.co. Call +1 (555) 123-4567</p>"

    with patch.object(servicio_fraude, "cargar_detector",
                      return_value={"pipeline": modelo, "umbral": 0.6}):
        resultado = servicio_fraude.analizar_oferta(oferta)

    assert modelo.recibido == [texto_para_modelo(oferta)]
    texto = modelo.recibido[0]
    assert "[EMAIL]" in texto and "[URL]" in texto and "[PHONE]" in texto
    assert "hr@fast.co" not in texto and "<p>" not in texto
    assert resultado["riesgo_detectado"] is True
    assert resultado["puntuacion_modelo"] == 0.7
