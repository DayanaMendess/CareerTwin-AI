
import json
import re

from predict_skills import predecir_habilidades


def normalizar(texto):
    # Conserva los signos de habilidades como C++, C# y .NET
    return re.sub(r"\s+", " ", texto.strip().casefold())


def analizar_skill_gap(texto_oferta, habilidades_usuario):
    if not isinstance(habilidades_usuario, list):
        raise ValueError("Las habilidades deben ser una lista")

    # Predecir habilidades relacionadas con la oferta
    resultado = predecir_habilidades(
        texto_oferta,
        top_k=100
    )

    predichas = resultado["habilidades_detectadas"]

    # Habilidades declaradas por el usuario
    habilidades_normalizadas = {
        normalizar(h) for h in habilidades_usuario
        if isinstance(h, str) and h.strip()
    }

    coincidencias = []
    brechas = []

    for item in predichas:
        habilidad = item["habilidad"]

        if normalizar(habilidad) in habilidades_normalizadas:
            coincidencias.append(item)
        else:
            brechas.append(item)

    return {
        "habilidades_declaradas": habilidades_usuario,
        "habilidades_sugeridas_por_ia": len(predichas),
        "habilidades_coincidentes": coincidencias,
        "brechas_potenciales": brechas,
        "nota": (
            "Las brechas son estimaciones basadas en "
            "habilidades predichas por el modelo, "
            "no requisitos confirmados por la empresa."
        )
    }


if __name__ == "__main__":
    oferta = (
        "We are hiring a project manager with experience "
        "in communication, leadership, project planning, "
        "budgeting, teamwork and time management."
    )

    habilidades = [
        "communication",
        "leadership",
        "teamwork",
        "python"
    ]

    resultado = analizar_skill_gap(oferta, habilidades)

    print(json.dumps(
        resultado,
        ensure_ascii=False,
        indent=2
    ))
