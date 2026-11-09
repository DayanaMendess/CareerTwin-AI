"""
13 - Preparación de EMSCAD para Fraud Shield (Catalina)

Reemplaza a src/preparar_fraude.py aplicando las recomendaciones de
reports/auditoria_fraude.md, con las MISMAS funciones que usa la app (fraude_utils.py):
  1. Texto = title + description + requirements + benefits, pasado por
     texto_para_modelo(): limpio, en minúsculas y con [URL] / [EMAIL] / [PHONE].
  2. Agrupa ofertas repetidas o CASI iguales (no solo idénticas) con clave_duplicado().
     Los grupos con etiquetas contradictorias se excluyen; de cada grupo queda una sola
     oferta (n_copias dice cuántas había).
  3. División 70/15/15 estratificada por clase con train_test_split (semilla 42).
     Como queda una oferta por grupo, ningún grupo cae en dos particiones.

Salidas (los mismos nombres y columnas que ya lee src/entrenar_fraude.py):
  data/processed/fraude_train.csv, fraude_val.csv, fraude_test.csv
      columnas: texto, fraudulent, grupo_texto, n_copias   (no van a Git)
  reports/preparacion_fraude.json

Uso:  python src/data_pipeline/13_preparar_fraude.py
No entrena nada ni modifica data/raw/fake_job_postings.csv.
"""
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from fraude_utils import (CAMPOS_TEXTO, COLUMNAS_EXCLUIDAS, clave_duplicado,
                          texto_para_modelo, unir_campos)

SEMILLA = 42
MIN_CARACTERES = 20

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "data" / "raw" / "fake_job_postings.csv"
SALIDA = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"
SALIDA.mkdir(parents=True, exist_ok=True)
REPORTES.mkdir(parents=True, exist_ok=True)

if not ENTRADA.is_file():
    raise FileNotFoundError(f"No se encontró: {ENTRADA}")

df = pd.read_csv(ENTRADA, keep_default_na=False, dtype=str, low_memory=False)
faltantes = [c for c in CAMPOS_TEXTO + ["fraudulent"] if c not in df]
if faltantes:
    raise ValueError(f"Columnas faltantes: {faltantes}")
originales = len(df)
print("=== PREPARACIÓN FRAUD SHIELD (13) ===")
print("Registros originales:", originales)

# ------------------------------------------------------------- 1. Texto
df["fraudulent"] = pd.to_numeric(df["fraudulent"], errors="coerce")
df = df[df["fraudulent"].isin([0, 1])].copy()
df["fraudulent"] = df["fraudulent"].astype(int)

df["texto_crudo"] = [unir_campos(f) for f in df[CAMPOS_TEXTO].to_dict("records")]
df["texto"] = df["texto_crudo"].map(texto_para_modelo)
cortos = int((df["texto"].str.len() < MIN_CARACTERES).sum())
df = df[df["texto"].str.len() >= MIN_CARACTERES].copy()

marcadores_emscad = int(df["texto"].str.contains(r"#(?:url|email|phone)_", regex=True).sum())
assert marcadores_emscad == 0, "Quedaron marcadores de EMSCAD sin convertir"
con_marcador = {m: int(df["texto"].str.contains(f"[{m}]", regex=False).sum())
                for m in ["URL", "EMAIL", "PHONE"]}

# ------------------------------------------------------------- 2. Grupos de ofertas repetidas
df["grupo_texto"] = df["texto_crudo"].map(clave_duplicado)
df["n_copias"] = df.groupby("grupo_texto")["grupo_texto"].transform("size")

etiquetas = df.groupby("grupo_texto")["fraudulent"].nunique()
contradictorios = set(etiquetas[etiquetas > 1].index)
excluidas_contradiccion = int(df["grupo_texto"].isin(contradictorios).sum())
df = df[~df["grupo_texto"].isin(contradictorios)]

en_grupos_repetidos = int((df["n_copias"] > 1).sum())
antes = len(df)
df = df.drop_duplicates(subset=["grupo_texto"]).copy()
copias_quitadas = antes - len(df)

# ------------------------------------------------------------- 3. División 70/15/15
train, temporal = train_test_split(df, test_size=0.30, stratify=df["fraudulent"],
                                   random_state=SEMILLA)
val, test = train_test_split(temporal, test_size=0.50, stratify=temporal["fraudulent"],
                             random_state=SEMILLA)

particiones = {"train": train, "val": val, "test": test}
for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
    assert set(particiones[a]["grupo_texto"]).isdisjoint(particiones[b]["grupo_texto"]), \
        f"Fuga: hay grupos en {a} y {b}"

reporte = {
    "script": "src/data_pipeline/13_preparar_fraude.py",
    "semilla": SEMILLA,
    "registros_originales": originales,
    "registros_finales": len(df),
    "texto": {
        "campos_usados": CAMPOS_TEXTO,
        "columnas_excluidas": COLUMNAS_EXCLUIDAS,
        "textos_cortos_excluidos": cortos,
        "marcadores_emscad_restantes": marcadores_emscad,
        "ofertas_con_marcador": con_marcador,
    },
    "duplicados": {
        "ofertas_en_grupos_repetidos": en_grupos_repetidos,
        "copias_quitadas": copias_quitadas,
        "grupos_con_etiquetas_contradictorias": len(contradictorios),
        "ofertas_excluidas_por_contradiccion": excluidas_contradiccion,
    },
    "particiones": {},
    "uso_en_la_app": ("from src.data_pipeline.fraude_utils import texto_para_modelo; "
                      "modelo.predict_proba([texto_para_modelo(job_text)])"),
}
for nombre, datos in particiones.items():
    datos[["texto", "fraudulent", "grupo_texto", "n_copias"]].to_csv(
        SALIDA / f"fraude_{nombre}.csv", index=False, encoding="utf-8")
    conteo = datos["fraudulent"].value_counts()
    reporte["particiones"][nombre] = {"total": len(datos),
                                      "reales": int(conteo.get(0, 0)),
                                      "fraudulentas": int(conteo.get(1, 0))}

(REPORTES / "preparacion_fraude.json").write_text(
    json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(reporte, indent=2, ensure_ascii=False))
print("\nPreparación completada correctamente.")
