
import json
import numpy as np
from functools import lru_cache
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def cargar_modelo():
    return SentenceTransformer(
        "BAAI/bge-small-en-v1.5",
        device="cpu"
    )


def comparar_ofertas(perfil, ofertas):
    if not isinstance(perfil, str) or not perfil.strip():
        raise ValueError("El perfil no puede estar vacio")

    if not ofertas:
        raise ValueError("Debes proporcionar ofertas laborales")

    modelo = cargar_modelo()

    textos = [perfil.strip()] + [
        oferta["descripcion"] for oferta in ofertas
    ]

    vectores = modelo.encode(
        textos,
        normalize_embeddings=True,
        batch_size=16,
        show_progress_bar=False
    )

    vector_perfil = vectores[0]
    vectores_ofertas = vectores[1:]

    similitudes = np.dot(
        vectores_ofertas,
        vector_perfil
    )

    resultados = []

    for oferta, similitud in zip(ofertas, similitudes):
        resultados.append({
            "oferta": oferta["titulo"],
            "similitud_semantica": round(
                float(similitud), 4
            )
        })

    resultados.sort(
        key=lambda x: x["similitud_semantica"],
        reverse=True
    )

    return {
        "modelo": "BAAI/bge-small-en-v1.5",
        "resultados": resultados,
        "nota": (
            "La similitud semantica no representa "
            "una probabilidad de contratacion."
        )
    }


if __name__ == "__main__":

    perfil = (
        "Software developer with experience in "
        "Python, SQL, data analysis, APIs and "
        "machine learning."
    )

    ofertas = [
        {
            "titulo": "Python Developer",
            "descripcion": (
                "We are looking for a Python developer "
                "with SQL, API development and backend "
                "programming experience."
            )
        },
        {
            "titulo": "Restaurant Supervisor",
            "descripcion": (
                "Restaurant supervisor with experience "
                "in customer service, food safety "
                "and team management."
            )
        },
        {
            "titulo": "Data Analyst",
            "descripcion": (
                "Data analyst with Python, SQL, "
                "data visualization and reporting skills."
            )
        }
    ]

    resultado = comparar_ofertas(perfil, ofertas)

    print(json.dumps(
        resultado,
        ensure_ascii=False,
        indent=2
    ))
