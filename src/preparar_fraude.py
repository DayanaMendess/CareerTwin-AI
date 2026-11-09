
"""Preparación de datos para Fraud Shield — CareerTwin AI."""

import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "data/raw/fake_job_postings.csv"
SALIDA = RAIZ / "data/processed"
REPORTES = RAIZ / "reports"

SALIDA.mkdir(parents=True, exist_ok=True)
REPORTES.mkdir(parents=True, exist_ok=True)

SEMILLA = 42

if not ENTRADA.is_file():
    raise FileNotFoundError(f"No se encontró: {ENTRADA}")

df = pd.read_csv(ENTRADA, low_memory=False)

columnas = ["title", "description", "requirements", "benefits"]
faltantes = [c for c in columnas + ["fraudulent"] if c not in df]

if faltantes:
    raise ValueError(f"Columnas faltantes: {faltantes}")

print("=== PREPARACIÓN FRAUD SHIELD ===")
print("Registros originales:", len(df))

# Crear un texto unificado para el análisis NLP.
df["texto"] = (
    df[columnas]
    .fillna("")
    .astype(str)
    .agg(" ".join, axis=1)
)

# Limpiar etiquetas HTML y espacios repetidos.
df["texto"] = (
    df["texto"]
    .str.replace(r"<[^>]*>", " ", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
    .str.lower()
)

# Conservar etiquetas válidas y textos útiles.
df["fraudulent"] = pd.to_numeric(
    df["fraudulent"], errors="coerce"
)

df = df[
    df["fraudulent"].isin([0, 1])
    & (df["texto"].str.len() >= 20)
].copy()

df["fraudulent"] = df["fraudulent"].astype(int)

# Excluir textos idénticos con etiquetas contradictorias.
conflictos = (
    df.groupby("texto")["fraudulent"]
    .nunique()
)
textos_conflictivos = conflictos[conflictos > 1].index

df = df[~df["texto"].isin(textos_conflictivos)]

# Evitar que una oferta idéntica aparezca en varias particiones.
antes = len(df)
df = df.drop_duplicates(subset=["texto"]).copy()
duplicados = antes - len(df)

# División estratificada 70 / 15 / 15.
train, temporal = train_test_split(
    df,
    test_size=0.30,
    stratify=df["fraudulent"],
    random_state=SEMILLA
)

val, test = train_test_split(
    temporal,
    test_size=0.50,
    stratify=temporal["fraudulent"],
    random_state=SEMILLA
)

# Verificar que no compartan textos.
assert set(train["texto"]).isdisjoint(val["texto"])
assert set(train["texto"]).isdisjoint(test["texto"])
assert set(val["texto"]).isdisjoint(test["texto"])

particiones = {
    "train": train,
    "val": val,
    "test": test
}

reporte = {
    "semilla": SEMILLA,
    "registros_finales": len(df),
    "duplicados_eliminados": duplicados,
    "textos_conflictivos_excluidos": len(textos_conflictivos),
    "particiones": {}
}

for nombre, datos in particiones.items():
    datos[["texto", "fraudulent"]].to_csv(
        SALIDA / f"fraude_{nombre}.csv",
        index=False,
        encoding="utf-8"
    )

    conteo = datos["fraudulent"].value_counts()

    reporte["particiones"][nombre] = {
        "total": len(datos),
        "reales": int(conteo.get(0, 0)),
        "fraudulentas": int(conteo.get(1, 0))
    }

ruta_reporte = REPORTES / "preparacion_fraude.json"
ruta_reporte.write_text(
    json.dumps(reporte, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(json.dumps(reporte, indent=2, ensure_ascii=False))
print("\nPreparación completada correctamente.")
