
import argparse
import sys

# Evitar errores de caracteres especiales en Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
import keras
from keras import layers
from sklearn.metrics import f1_score

# Rutas del proyecto
RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"
MODELOS = RAIZ / "models"

MODELOS.mkdir(exist_ok=True)
REPORTES.mkdir(exist_ok=True)

# Configuración reproducible
SEMILLA = 42
random.seed(SEMILLA)
np.random.seed(SEMILLA)
tf.random.set_seed(SEMILLA)

parser = argparse.ArgumentParser()
parser.add_argument("--epochs", type=int, default=2)
parser.add_argument("--limite-train", type=int, default=None)
parser.add_argument("--limite-val", type=int, default=None)
args = parser.parse_args()

print("Iniciando entrenamiento CareerTwin AI")

# Cargar vocabulario de Catalina
with open(REPORTES / "skills_vocab.json", encoding="utf-8") as f:
    vocabulario = json.load(f)

N_HABILIDADES = len(vocabulario["etiquetas"])
assert N_HABILIDADES == 100

# Cargar dataset final
datos = pd.read_parquet(
    DATOS / "datos_entrenamiento.parquet",
    columns=["particion", "job_title", "job_summary_clean"]
)


def cargar_particion(nombre, limite=None):
    parte = datos[datos["particion"] == nombre]
    etiquetas = np.load(DATOS / f"Y_{nombre}.npy")

    if len(parte) != len(etiquetas):
        raise ValueError(f"Filas y etiquetas no coinciden: {nombre}")

    if etiquetas.shape[1] != N_HABILIDADES:
        raise ValueError("El vocabulario no coincide con las etiquetas")

    if limite is not None:
        parte = parte.iloc[:limite]
        etiquetas = etiquetas[:limite]

    textos = (
        parte["job_title"].fillna("").astype(str)
        + ". "
        + parte["job_summary_clean"].fillna("").astype(str)
    )

    return textos.tolist(), etiquetas.astype(np.float32)


x_train, y_train = cargar_particion("train", args.limite_train)
x_val, y_val = cargar_particion("val", args.limite_val)

print("Entrenamiento:", len(x_train))
print("Validación:", len(x_val))
print("Habilidades:", N_HABILIDADES)

# Vectorización textual: vocabulario aprendido solo de train
vectorizador = layers.TextVectorization(
    max_tokens=15000,
    standardize="lower",
    output_mode="int",
    output_sequence_length=256
)

vectorizador.adapt(
    tf.data.Dataset.from_tensor_slices(x_train).batch(64)
)

# Arquitectura neuronal CNN
entrada = keras.Input(shape=(), dtype="string")

x = vectorizador(entrada)
x = layers.Embedding(
    input_dim=len(vectorizador.get_vocabulary()),
    output_dim=32
)(x)
x = layers.Conv1D(32, 3, activation="relu")(x)
x = layers.GlobalMaxPooling1D()(x)
x = layers.Dense(64, activation="relu")(x)
x = layers.Dropout(0.3)(x)

salida = layers.Dense(
    N_HABILIDADES,
    activation="sigmoid"
)(x)

modelo = keras.Model(entrada, salida)

modelo.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    loss="binary_crossentropy",
    metrics=[
        keras.metrics.Precision(name="precision"),
        keras.metrics.Recall(name="recall")
    ]
)

modelo.summary()

# Preparar lotes
def crear_dataset(textos, etiquetas, entrenamiento=False):
    ds = tf.data.Dataset.from_tensor_slices((textos, etiquetas))
    if entrenamiento:
        ds = ds.shuffle(
            min(len(textos), 4000),
            seed=SEMILLA
        )
    return ds.batch(32).prefetch(tf.data.AUTOTUNE)


ds_train = crear_dataset(x_train, y_train, True)
ds_val = crear_dataset(x_val, y_val)

ruta_modelo = MODELOS / "career_skills.keras"
ruta_historial = REPORTES / "historial_entrenamiento.csv"

callbacks = [
    keras.callbacks.ModelCheckpoint(
        str(ruta_modelo),
        monitor="val_loss",
        save_best_only=True
    ),
    keras.callbacks.CSVLogger(str(ruta_historial))
]


class ProgresoEntrenamiento(keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}

        print(
            f"Epoca {epoch + 1}: "
            f"loss={logs.get('loss', 0):.4f} | "
            f"val_loss={logs.get('val_loss', 0):.4f} | "
            f"precision={logs.get('precision', 0):.4f} | "
            f"recall={logs.get('recall', 0):.4f}",
            flush=True
        )


callbacks.append(ProgresoEntrenamiento())

# Entrenar
modelo.fit(
    ds_train,
    validation_data=ds_val,
    epochs=args.epochs,
    callbacks=callbacks,
    verbose=0
)

# Evaluar el mejor modelo sobre validación
mejor_modelo = keras.models.load_model(str(ruta_modelo))
probabilidades = mejor_modelo.predict(ds_val, verbose=0)
predicciones = (probabilidades >= 0.5).astype(int)

print("\n--- RESULTADOS DE VALIDACIÓN ---")
print("Micro-F1:", round(
    f1_score(y_val, predicciones, average="micro", zero_division=0), 4
))
print("Macro-F1:", round(
    f1_score(y_val, predicciones, average="macro", zero_division=0), 4
))
print("Modelo guardado en:", ruta_modelo)
print("Historial guardado en:", ruta_historial)



# Diagnostico de predicciones en validacion
print("\n--- DIAGNOSTICO DE PREDICCIONES ---")

print("Etiquetas positivas reales:", int(y_val.sum()))

print("Probabilidad minima:", round(float(probabilidades.min()), 4))
print("Probabilidad media:", round(float(probabilidades.mean()), 4))
print("Probabilidad maxima:", round(float(probabilidades.max()), 4))

for umbral in [0.1, 0.2, 0.3, 0.4, 0.5]:
    pred = (probabilidades >= umbral).astype(int)

    micro = f1_score(
        y_val, pred, average="micro", zero_division=0
    )
    macro = f1_score(
        y_val, pred, average="macro", zero_division=0
    )

    print(
        f"Umbral {umbral:.1f} | "
        f"Positivos predichos: {int(pred.sum())} | "
        f"Micro-F1: {micro:.4f} | "
        f"Macro-F1: {macro:.4f}"
    )
