
import argparse
import json
from functools import lru_cache
from pathlib import Path

import keras
import numpy as np
import tensorflow as tf

RAIZ = Path(__file__).resolve().parents[1]
RUTA_MODELO = RAIZ / "models" / "career_skills.keras"
RUTA_VOCAB = RAIZ / "reports" / "skills_vocab.json"
RUTA_METRICAS = RAIZ / "reports" / "evaluacion_final_skills.json"


@lru_cache(maxsize=1)
def cargar_recursos():
    modelo = keras.models.load_model(
        str(RUTA_MODELO),
        compile=False
    )

    with open(RUTA_VOCAB, encoding="utf-8") as archivo:
        habilidades = json.load(archivo)["etiquetas"]

    with open(RUTA_METRICAS, encoding="utf-8") as archivo:
        metricas = json.load(archivo)

    if modelo.output_shape[-1] != len(habilidades):
        raise ValueError(
            "Las salidas del modelo no coinciden con el vocabulario"
        )

    umbral = float(
        metricas["umbral_seleccionado_en_validacion"]
    )

    return modelo, habilidades, umbral


def predecir_habilidades(texto, top_k=10):
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("Debes proporcionar un texto valido")

    modelo, habilidades, umbral = cargar_recursos()

    entrada = tf.data.Dataset.from_tensor_slices(
        [texto.strip()]
    ).batch(1)

    resultados = modelo.predict(entrada, verbose=0)
    puntuaciones = np.asarray(resultados)[0]

    indices = np.argsort(puntuaciones)[::-1]

    seleccionados = [
        int(i) for i in indices
        if puntuaciones[i] >= umbral
    ][:top_k]

    predicciones = [
        {
            "habilidad": habilidades[i],
            "score_modelo": round(float(puntuaciones[i]), 4)
        }
        for i in seleccionados
    ]

    return {
        "modelo": "CareerTwin AI",
        "umbral": umbral,
        "habilidades_detectadas": predicciones,
        "total_detectadas": len(predicciones),
        "advertencia": (
            "Los puntajes no son probabilidades calibradas "
            "ni garantizan que una persona tenga estas habilidades."
        )
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--texto", required=True)
    args = parser.parse_args()

    resultado = predecir_habilidades(args.texto)

    print(json.dumps(
        resultado,
        ensure_ascii=False,
        indent=2
    ))
