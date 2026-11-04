
import json
from pathlib import Path

import keras
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score
)

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"
MODELOS = RAIZ / "models"

print("=== EVALUACION FINAL CAREERTWIN AI ===")

# Cargar mejor modelo, sin volver a entrenar
modelo = keras.models.load_model(
    MODELOS / "career_skills.keras",
    compile=False
)

datos = pd.read_parquet(
    DATOS / "datos_entrenamiento.parquet",
    columns=[
        "particion",
        "job_title",
        "job_summary_clean"
    ]
)

with open(REPORTES / "skills_vocab.json", encoding="utf-8") as f:
    habilidades = json.load(f)["etiquetas"]


def cargar_datos(particion):
    parte = datos.loc[datos["particion"] == particion]
    etiquetas = np.load(DATOS / f"Y_{particion}.npy")

    textos = (
        parte["job_title"].fillna("").astype(str)
        + ". "
        + parte["job_summary_clean"].fillna("").astype(str)
    ).tolist()

    assert len(textos) == len(etiquetas)
    assert etiquetas.shape[1] == len(habilidades)

    return textos, etiquetas


x_val, y_val = cargar_datos("val")
x_test, y_test = cargar_datos("test")

print("Validacion:", len(x_val))
print("Prueba:", len(x_test))
print("Habilidades:", len(habilidades))


def predecir(textos):
    ds = tf.data.Dataset.from_tensor_slices(
        textos
    ).batch(64)

    return modelo.predict(ds, verbose=0)


# Elegir umbral usando SOLO validacion
print("\nBuscando mejor umbral en validacion...")

prob_val = predecir(x_val)
resultados = []

for i in range(5, 51, 5):
    umbral = i / 100
    pred = (prob_val >= umbral).astype(int)

    micro = f1_score(
        y_val, pred, average="micro", zero_division=0
    )
    macro = f1_score(
        y_val, pred, average="macro", zero_division=0
    )

    resultados.append({
        "umbral": umbral,
        "micro_f1": float(micro),
        "macro_f1": float(macro)
    })

    print(
        f"Umbral {umbral:.2f} | "
        f"Micro-F1: {micro:.4f} | "
        f"Macro-F1: {macro:.4f}"
    )

mejor = max(
    resultados,
    key=lambda r: r["micro_f1"]
)
umbral = mejor["umbral"]

print("\nMejor umbral seleccionado:", umbral)

# Evaluacion final: TEST no usado para elegir umbral
print("\nEvaluando 7500 ofertas de prueba...")

prob_test = predecir(x_test)
pred_test = (prob_test >= umbral).astype(int)

metricas = {
    "umbral_seleccionado_en_validacion": umbral,
    "registros_test": len(y_test),
    "micro_f1": float(f1_score(
        y_test, pred_test,
        average="micro", zero_division=0
    )),
    "macro_f1": float(f1_score(
        y_test, pred_test,
        average="macro", zero_division=0
    )),
    "precision_micro": float(precision_score(
        y_test, pred_test,
        average="micro", zero_division=0
    )),
    "recall_micro": float(recall_score(
        y_test, pred_test,
        average="micro", zero_division=0
    )),
}

# Precision@5
top5 = np.argsort(prob_test, axis=1)[:, -5:]
metricas["precision_at_5"] = float(
    np.take_along_axis(
        y_test, top5, axis=1
    ).mean()
)

ruta = REPORTES / "evaluacion_final_skills.json"
ruta.write_text(
    json.dumps(metricas, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("\n=== RESULTADOS FINALES ===")

for nombre, valor in metricas.items():
    print(f"{nombre}: {valor}")

print("\nReporte guardado en:", ruta)
