

"""Entrenamiento de Fraud Shield — CareerTwin AI."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    average_precision_score,
    confusion_matrix,
)

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data" / "processed"
MODELOS = RAIZ / "models"
REPORTES = RAIZ / "reports"

MODELOS.mkdir(exist_ok=True)
REPORTES.mkdir(exist_ok=True)


def cargar(nombre):
    ruta = DATOS / f"fraude_{nombre}.csv"
    if not ruta.exists():
        raise FileNotFoundError(f"Falta el archivo: {ruta}")

    df = pd.read_csv(ruta)
    if df["texto"].isna().any():
        raise ValueError(f"Hay textos vacíos en {nombre}")

    return df["texto"].astype(str), df["fraudulent"].astype(int)


def evaluar(y_real, probabilidades, umbral):
    predicciones = (probabilidades >= umbral).astype(int)
    matriz = confusion_matrix(y_real, predicciones, labels=[0, 1])

    return {
        "precision_fraude": round(
            float(precision_score(y_real, predicciones, zero_division=0)), 4
        ),
        "recall_fraude": round(
            float(recall_score(y_real, predicciones, zero_division=0)), 4
        ),
        "f1_fraude": round(
            float(f1_score(y_real, predicciones, zero_division=0)), 4
        ),
        "average_precision": round(
            float(average_precision_score(y_real, probabilidades)), 4
        ),
        "matriz_confusion": matriz.tolist(),
    }


print("=== ENTRENAMIENTO FRAUD SHIELD ===")

x_train, y_train = cargar("train")
x_val, y_val = cargar("val")
x_test, y_test = cargar("test")

print(f"Entrenamiento: {len(x_train)} ofertas")
print(f"Validación: {len(x_val)} ofertas")
print(f"Prueba: {len(x_test)} ofertas")

# El vectorizador se ajusta únicamente con entrenamiento.
modelo = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            max_features=50000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.98,
            sublinear_tf=True,
            strip_accents="unicode",
        ),
    ),
    (
        "clasificador",
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            solver="liblinear",
            random_state=42,
        ),
    ),
])

print("\nEntrenando clasificador...")
modelo.fit(x_train, y_train)

# Seleccionar el umbral usando SOLO validación.
proba_val = modelo.predict_proba(x_val)[:, 1]

umbrales = np.arange(0.10, 0.91, 0.05)

mejor_umbral = max(
    umbrales,
    key=lambda u: (
        f1_score(y_val, proba_val >= u, zero_division=0),
        recall_score(y_val, proba_val >= u, zero_division=0),
    ),
)
mejor_umbral = round(float(mejor_umbral), 2)

print(f"Umbral seleccionado: {mejor_umbral}")

metricas_val = evaluar(y_val, proba_val, mejor_umbral)

# El conjunto de prueba se evalúa una sola vez,
# después de elegir el umbral con validación.
proba_test = modelo.predict_proba(x_test)[:, 1]
metricas_test = evaluar(y_test, proba_test, mejor_umbral)

reporte = {
    "modelo": "TF-IDF + Regresión Logística",
    "semilla": 42,
    "registros": {
        "train": len(x_train),
        "val": len(x_val),
        "test": len(x_test),
    },
    "umbral": mejor_umbral,
    "validacion": metricas_val,
    "prueba": metricas_test,
    "advertencia": (
        "Las puntuaciones no son probabilidades calibradas. "
        "El detector identifica señales de riesgo, no fraude confirmado."
    ),
}

ruta_modelo = MODELOS / "fraud_detector.joblib"
joblib.dump(
    {"pipeline": modelo, "umbral": mejor_umbral},
    ruta_modelo,
)

ruta_reporte = REPORTES / "entrenamiento_fraude.json"
ruta_reporte.write_text(
    json.dumps(reporte, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("\n=== RESULTADOS ===")
print(json.dumps(reporte, indent=2, ensure_ascii=False))
print(f"\nModelo guardado: {ruta_modelo}")
print(f"Reporte guardado: {ruta_reporte}")
print("\nEntrenamiento completado correctamente.")
