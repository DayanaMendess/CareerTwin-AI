
"""Servicio de integración de IA para CareerTwin AI."""

from functools import lru_cache


@lru_cache(maxsize=1)
def cargar_detector():
    """Carga una sola vez el detector de habilidades."""
    from src.data_pipeline.detector_habilidades import DetectorHabilidades
    return DetectorHabilidades()


def analizar_perfil(texto_perfil: str) -> dict:
    """Combina las predicciones de la red con las habilidades del texto."""

    if not isinstance(texto_perfil, str) or not texto_perfil.strip():
        raise ValueError("El perfil profesional no puede estar vacío.")

    texto = texto_perfil.strip()

    # Modelo CNN entrenado con 100 habilidades.
    from src.predict_skills import predecir_habilidades

    resultado_modelo = predecir_habilidades(
        texto,
        top_k=100
    )

    # Detector de Catalina: catálogo más habilidades técnicas extra.
    detector = cargar_detector()

    habilidades = detector.combinar_habilidades(
        texto,
        resultado_modelo["habilidades_detectadas"],
        umbral=resultado_modelo["umbral"]
    )

    return {
        "status": "ok",
        "models_loaded": True,
        "umbral_modelo": resultado_modelo["umbral"],
        "habilidades_detectadas": habilidades,
        "total_habilidades": len(habilidades),
        "advertencia": (
            "Las puntuaciones del modelo no son probabilidades "
            "calibradas ni certifican las habilidades de una persona. "
            "El modelo fue entrenado con ofertas laborales en inglés; "
            "el análisis de perfiles personales es exploratorio."
        )
    }
