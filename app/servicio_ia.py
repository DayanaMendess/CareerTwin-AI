"""Servicio de integración de IA para CareerTwin AI."""

import json
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_FAMILIAS = BASE_DIR / "data" / "app" / "familias.json"


@lru_cache(maxsize=1)
def cargar_detector():
    """Carga una sola vez el detector de habilidades."""
    from src.data_pipeline.detector_habilidades import DetectorHabilidades
    return DetectorHabilidades()


@lru_cache(maxsize=1)
def cargar_familias():
    """Carga las familias y sus habilidades laborales."""
    with RUTA_FAMILIAS.open("r", encoding="utf-8") as archivo:
        datos = json.load(archivo)
    return datos["familias"]


def calcular_compatibilidad(habilidades_detectadas):
    """Compara el perfil con las habilidades de cada familia laboral."""
    presentes = {
        item["habilidad"].strip().lower()
        for item in habilidades_detectadas
    }

    resultados = []

    for familia in cargar_familias():
        requeridas = familia.get("habilidades", [])

        if not requeridas:
            continue

        coincidencias = []
        brechas = []

        for item in requeridas:
            nombre = item["habilidad"].strip()
            if nombre.lower() in presentes:
                coincidencias.append(item)
            else:
                brechas.append(item)

        total = len(requeridas)
        porcentaje = round(len(coincidencias) / total * 100, 1)

        resultados.append({
            "familia": familia["familia"],
            "compatibilidad": porcentaje,
            "cobertura_pct": porcentaje,
            "habilidades_requeridas": total,
            "habilidades_coincidentes": len(coincidencias),
            "habilidades_faltantes": len(brechas),
            "coincidencias": coincidencias,
            "brechas": sorted(
                brechas,
                key=lambda x: x.get("pct_en_familia", 0),
                reverse=True
            )
        })

    return sorted(
        resultados,
        key=lambda x: x["compatibilidad"],
        reverse=True
    )


def analizar_perfil(texto_perfil: str) -> dict:
    """Analiza el perfil y calcula su compatibilidad laboral."""

    if not isinstance(texto_perfil, str) or not texto_perfil.strip():
        raise ValueError("El perfil profesional no puede estar vacío.")

    texto = texto_perfil.strip()

    from src.predict_skills import predecir_habilidades

    resultado_modelo = predecir_habilidades(texto, top_k=100)

    detector = cargar_detector()

    habilidades = detector.combinar_habilidades(
        texto,
        resultado_modelo["habilidades_detectadas"],
        umbral=resultado_modelo["umbral"]
    )

    familias = calcular_compatibilidad(habilidades)
    mejores_familias = familias[:3]

    mejor = mejores_familias[0] if mejores_familias else None

    # Reunir brechas de las tres familias mejor posicionadas.
    brechas_por_habilidad = {}

    for familia in mejores_familias:
        for item in familia["brechas"]:
            nombre = item["habilidad"]
            clave = nombre.strip().lower()

            if clave not in brechas_por_habilidad:
                brechas_por_habilidad[clave] = {
                    **item,
                    "familias_relacionadas": [familia["familia"]]
                }
            else:
                brechas_por_habilidad[clave]["familias_relacionadas"].append(
                    familia["familia"]
                )

    brechas = sorted(
        brechas_por_habilidad.values(),
        key=lambda x: x.get("pct_en_familia", 0),
        reverse=True
    )[:10]

    recomendaciones = [
        {
            "habilidad": item["habilidad"],
            "categoria": item.get("categoria", ""),
            "prioridad": item.get("pct_en_familia", 0),
            "mensaje": (
                f"Fortalecer {item['habilidad']}: "
                "es una habilidad solicitada en estas familias: "
                + ", ".join(item["familias_relacionadas"]) + "."
            )
        }
        for item in brechas[:5]
    ]

    return {
        "status": "ok",
        "models_loaded": True,
        "umbral_modelo": resultado_modelo["umbral"],
        "habilidades_detectadas": habilidades,
        "total_habilidades": len(habilidades),
        "habilidades_presentes": habilidades,
        "brechas_habilidades": brechas,
        "compatibilidad": mejor["compatibilidad"] if mejor else 0,
        "compatibilidad_nivel": mejor["familia"] if mejor else "No disponible",
        "familia_recomendada": mejor["familia"] if mejor else None,
        "compatibilidad_familias": familias,
        "mejores_familias": mejores_familias,
        "recomendaciones": recomendaciones,
        "advertencia": (
            "Las puntuaciones del modelo no son probabilidades calibradas "
            "ni certifican las habilidades de una persona. El modelo fue "
            "entrenado con ofertas laborales en inglés; el análisis de "
            "perfiles personales es exploratorio. La compatibilidad es una "
            "comparación orientativa con las habilidades registradas."
        )
    }
