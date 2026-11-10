
"""Servicio de detección de riesgo en ofertas laborales."""

from functools import lru_cache
from pathlib import Path

import joblib

from src.data_pipeline.fraude_utils import texto_para_modelo

RAIZ = Path(__file__).resolve().parents[1]
RUTA_MODELO = RAIZ / "models" / "fraud_detector.joblib"


@lru_cache(maxsize=1)
def cargar_detector():
    if not RUTA_MODELO.is_file():
        raise FileNotFoundError(
            f"No se encontró el modelo: {RUTA_MODELO}"
        )

    # Cargar únicamente el modelo local generado por el equipo.
    return joblib.load(RUTA_MODELO)


def analizar_oferta(texto):
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("La oferta debe contener texto válido.")

    texto = texto.strip()

    if len(texto) > 20000:
        raise ValueError("La oferta supera los 20000 caracteres.")

    detector = cargar_detector()
    modelo = detector["pipeline"]
    umbral = float(detector["umbral"])

    # Mismo procesamiento que se usó para entrenar (fraude_utils.py)
    texto_limpio = texto_para_modelo(texto)
    puntuacion = float(modelo.predict_proba([texto_limpio])[0][1])
    riesgo = puntuacion >= umbral

    return {
        "status": "ok",
        "riesgo_detectado": bool(riesgo),
        "clasificacion": (
            "posible_fraude" if riesgo
            else "sin_indicios_suficientes"
        ),
        "puntuacion_modelo": round(puntuacion, 4),
        "umbral": umbral,
        "advertencia": (
            "Resultado orientativo, no confirma fraude ni "
            "garantiza que una oferta sea legítima. "
            "La puntuación no es una probabilidad calibrada."
        ),
    }
