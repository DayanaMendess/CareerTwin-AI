
import json
from pathlib import Path

import keras
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import precision_recall_fscore_support

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"
MODELOS = RAIZ / "models"

print("=== CAREERTWIN AI ===")
print("Evaluacion individual de 100 habilidades")

# 1. Cargar el mejor modelo entrenado
modelo = keras.models.load_model(
    MODELOS / "career_skills.keras",
    compile=False
)

# 2. Cargar vocabulario
with open(REPORTES / "skills_vocab.json", encoding="utf-8") as f:
    vocabulario = json.load(f)

habilidades = vocabulario["etiquetas"]
categorias = vocabulario.get("categoria", {})

# 3. Cargar el umbral elegido en validacion
with open(
    REPORTES / "evaluacion_final_skills.json",
    encoding="utf-8"
) as f:
    evaluacion = json.load(f)

umbral = float(
    evaluacion["umbral_seleccionado_en_validacion"]
)

print("Umbral:", umbral)

# 4. Cargar exclusivamente la particion TEST
datos = pd.read_parquet(
    DATOS / "datos_entrenamiento.parquet",
    columns=[
        "particion",
        "job_title",
        "job_summary_clean"
    ]
)

test = datos.loc[
    datos["particion"] == "test"
]

textos = (
    test["job_title"].fillna("").astype(str)
    + ". "
    + test["job_summary_clean"].fillna("").astype(str)
).tolist()

y_test = np.load(
    DATOS / "Y_test.npy",
    allow_pickle=False
)

assert len(textos) == len(y_test)
assert y_test.shape[1] == len(habilidades)
assert len(habilidades) == 100

print("Ofertas de prueba:", len(textos))
print("Habilidades:", len(habilidades))

# 5. Generar predicciones sin entrenar nuevamente
print("Calculando predicciones...")

ds = tf.data.Dataset.from_tensor_slices(
    textos
).batch(64)

probabilidades = modelo.predict(
    ds,
    verbose=0
)

assert probabilidades.shape == y_test.shape

predicciones = (
    probabilidades >= umbral
).astype(int)

# 6. Calcular metricas individuales
precision, recall, f1, soporte = (
    precision_recall_fscore_support(
        y_test,
        predicciones,
        average=None,
        zero_division=0
    )
)

verdaderos_positivos = np.sum(
    (y_test == 1) & (predicciones == 1),
    axis=0
)

falsos_positivos = np.sum(
    (y_test == 0) & (predicciones == 1),
    axis=0
)

falsos_negativos = np.sum(
    (y_test == 1) & (predicciones == 0),
    axis=0
)

# 7. Construir el reporte
reporte = pd.DataFrame({
    "habilidad": habilidades,
    "categoria": [
        categorias.get(h, "")
        for h in habilidades
    ],
    "precision": np.round(precision, 4),
    "recall": np.round(recall, 4),
    "f1": np.round(f1, 4),
    "ejemplos_test": soporte.astype(int),
    "predicciones_positivas": predicciones.sum(axis=0),
    "verdaderos_positivos": verdaderos_positivos,
    "falsos_positivos": falsos_positivos,
    "falsos_negativos": falsos_negativos,
    "frecuencia_test_pct": np.round(
        soporte / len(y_test) * 100, 2
    )
})

# 8. Guardar el CSV
ruta = REPORTES / "metricas_por_habilidad.csv"

reporte.to_csv(
    ruta,
    index=False,
    encoding="utf-8-sig"
)

print("\n=== RESULTADOS ===")
print("Habilidades evaluadas:", len(reporte))
print("CSV guardado:", ruta)

print("\n5 habilidades con mayor F1:")
print(
    reporte.sort_values(
        "f1", ascending=False
    )[["habilidad", "f1", "ejemplos_test"]]
    .head(5)
    .to_string(index=False)
)

print("\nHabilidades con F1 igual a cero:")
print(int((reporte["f1"] == 0).sum()))

print("\nEvaluacion completada correctamente.")
