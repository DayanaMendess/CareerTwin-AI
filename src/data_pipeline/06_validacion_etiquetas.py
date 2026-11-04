"""
06 - Validación de etiquetas (Catalina) — día 5

Revisa la calidad de las 100 etiquetas antes y durante el entrenamiento de Sofia:
  1. Etiquetas demasiado frecuentes (> 20 % de registros) o poco frecuentes (< 1 %).
  2. Nombres con formato raro y posibles sinónimos o etiquetas redundantes
     (una contiene a la otra, o casi siempre aparecen juntas).
  3. Que las particiones no compartan descripciones duplicadas (dos controles).
  4. Cobertura del vocabulario: cuántas ofertas y menciones cubre, y cuánto
     cubriría un vocabulario ampliado (para la decisión del día 6).
  5. Recomendaciones de ajuste.

Entradas: data/processed/datos_entrenamiento.parquet, reports/skills_vocab.json,
          reports/clasificacion_habilidades_revisada.csv,
          data/processed/catalogo_habilidades_completo.csv
Salidas:  reports/validacion_etiquetas.json
          reports/validacion_etiquetas_por_habilidad.csv
"""
import json
import re
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

MUY_FRECUENTE = 20.0     # % de registros
POCO_FRECUENTE = 1.0     # % de registros
JACCARD_REDUNDANTE = 0.30
MIN_POSITIVOS_TEST = 30

RAIZ = Path(__file__).resolve().parents[2]
PROC = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

datos = pd.read_parquet(PROC / "datos_entrenamiento.parquet")
vocab = json.loads((REPORTES / "skills_vocab.json").read_text(encoding="utf-8"))
ETIQUETAS = vocab["etiquetas"]
INDICE = {h: i for i, h in enumerate(ETIQUETAS)}

Y = np.zeros((len(datos), len(ETIQUETAS)), dtype=np.uint8)
for fila, lista in enumerate(datos["etiquetas"]):
    for h in lista:
        Y[fila, INDICE[h]] = 1
n = len(datos)

# ---------------------------------------------------------------- 1. Frecuencia
print("[1/4] Frecuencia de cada etiqueta...")
tabla = pd.DataFrame({"indice": range(len(ETIQUETAS)), "habilidad": ETIQUETAS,
                      "categoria": [vocab["categoria"].get(h, "") for h in ETIQUETAS],
                      "registros": Y.sum(axis=0),
                      "porcentaje": (Y.mean(axis=0) * 100).round(2)})
for p in ["train", "val", "test"]:
    tabla[f"{p}_ejemplos"] = Y[(datos["particion"] == p).to_numpy()].sum(axis=0)
tabla["alerta"] = np.select(
    [tabla["porcentaje"] > MUY_FRECUENTE, tabla["porcentaje"] < POCO_FRECUENTE,
     tabla["test_ejemplos"] < MIN_POSITIVOS_TEST],
    ["muy frecuente", "poco frecuente", "pocos ejemplos en test"], default="")

por_registro = Y.sum(axis=1)
frecuencia = {
    "muy_frecuentes (>20%)": tabla.loc[tabla["porcentaje"] > MUY_FRECUENTE,
                                      ["habilidad", "porcentaje"]].values.tolist(),
    "poco_frecuentes (<1%)": tabla.loc[tabla["porcentaje"] < POCO_FRECUENTE,
                                      ["habilidad", "porcentaje"]].values.tolist(),
    "mas_frecuente": [tabla.iloc[tabla["registros"].idxmax()]["habilidad"],
                      float(tabla["porcentaje"].max())],
    "menos_frecuente": [tabla.iloc[tabla["registros"].idxmin()]["habilidad"],
                        float(tabla["porcentaje"].min())],
    "etiquetas_por_registro": {
        "0": int((por_registro == 0).sum()),
        "1_a_3": int(((por_registro >= 1) & (por_registro <= 3)).sum()),
        "4_a_10": int(((por_registro >= 4) & (por_registro <= 10)).sum()),
        "mas_de_10": int((por_registro > 10).sum()),
    },
}

# ---------------------------------------------------------------- 2. Nombres y sinónimos
print("[2/4] Revisando nombres y posibles sinónimos...")
nombres_raros = [h for h in ETIQUETAS
                 if re.search(r"[^a-z0-9 +#.&'()/\-]", h) or len(h) > 40
                 or h.startswith("ability to")]

palabras = {h: set(h.split()) for h in ETIQUETAS}
contenidas = [[a, b] for a, b in combinations(ETIQUETAS, 2)
              if palabras[a] < palabras[b] or palabras[b] < palabras[a]]

# Pares que aparecen juntos casi siempre (índice de Jaccard entre columnas)
inter = Y.T.astype(np.int64) @ Y.astype(np.int64)
tot = np.diag(inter)
redundantes = []
for i, j in combinations(range(len(ETIQUETAS)), 2):
    union = tot[i] + tot[j] - inter[i, j]
    if union and inter[i, j] / union >= JACCARD_REDUNDANTE:
        redundantes.append([ETIQUETAS[i], ETIQUETAS[j], round(float(inter[i, j] / union), 3)])
redundantes.sort(key=lambda x: -x[2])

# Pares que por significado podrían ser lo mismo (se revisan si ambos están en el vocabulario)
POSIBLES_SINONIMOS = [
    ("organization", "organizational skills"), ("teamwork", "team player"),
    ("teamwork", "team collaboration"), ("collaboration", "team collaboration"),
    ("adaptability", "flexibility"), ("attention to detail", "detail oriented"),
    ("analytical skills", "analytical thinking"), ("interpersonal skills", "interpersonal communication"),
    ("communication", "verbal communication"), ("communication", "oral communication"),
    ("budgeting", "budget management"), ("data analysis", "data analytics"),
    ("recruitment", "recruiting"), ("hiring", "recruitment"),
    ("microsoft word", "word"), ("crm", "customer relationship management"),
    ("independent work", "ability to work independently"),
    ("motivation", "selfmotivation"), ("quality control", "quality assurance"),
    ("inventory management", "inventory control"), ("retail", "retail management"),
    ("nursing", "patient care"), ("training", "training and development"),
]
sinonimos = [[a, b] for a, b in POSIBLES_SINONIMOS if a in INDICE and b in INDICE]

# ---------------------------------------------------------------- 3. Duplicados entre particiones
print("[3/4] Verificando que las particiones no compartan descripciones...")
grupos_cruzados = int(datos.groupby("grupo_texto")["particion"].nunique().gt(1).sum())
texto_norm = (datos["job_summary_clean"].str.lower()
              .str.replace(r"\s+", " ", regex=True).str.strip())
huella = pd.util.hash_pandas_object(texto_norm, index=False)
textos_cruzados = int(pd.DataFrame({"h": huella, "p": datos["particion"]})
                      .groupby("h")["p"].nunique().gt(1).sum())
ids_repetidos = int(datos["job_id"].duplicated().sum())

# ---------------------------------------------------------------- 4. Cobertura
print("[4/4] Calculando cobertura del vocabulario...")
cobertura = {
    "registros_con_al_menos_1_etiqueta_pct": round(float((por_registro > 0).mean() * 100), 2),
    "etiquetas_por_registro_promedio": round(float(por_registro.mean()), 2),
}
ruta_cat = PROC / "catalogo_habilidades_completo.csv"
ruta_cls = REPORTES / "clasificacion_habilidades_revisada.csv"
if ruta_cat.exists() and ruta_cls.exists():
    cat = pd.read_csv(ruta_cat, keep_default_na=False)
    cls = pd.read_csv(ruta_cls, keep_default_na=False)
    total = cat["ofertas"].sum()
    validas = cls.loc[cls["categoria_final"].isin(["tecnica", "blanda"]), "habilidad"]
    validas = cat[cat["habilidad"].isin(set(validas))]
    en_vocab = cat[cat["habilidad"].isin(INDICE)]
    cobertura.update({
        "menciones_cubiertas_por_las_100_pct": round(float(en_vocab["ofertas"].sum() / total * 100), 2),
        "habilidades_validas_revisadas": int(len(validas)),
        "menciones_cubiertas_por_todas_las_validas_revisadas_pct":
            round(float(validas["ofertas"].sum() / total * 100), 2),
        "nota": "Menciones = suma de ofertas por habilidad en todo el dataset normalizado.",
    })

# ---------------------------------------------------------------- Recomendaciones
rec = []
if frecuencia["muy_frecuentes (>20%)"]:
    nombres = ", ".join(h for h, _ in frecuencia["muy_frecuentes (>20%)"])
    rec.append(f"Etiquetas muy frecuentes ({nombres}): pueden hacer que la red las prediga casi siempre. "
               "Recomiendo usar pesos por clase o medir Macro-F1 además de Micro-F1.")
if frecuencia["poco_frecuentes (<1%)"]:
    rec.append("Hay etiquetas con menos del 1% de registros: su F1 puede salir bajo por falta de ejemplos.")
if sinonimos:
    rec.append(f"Revisar {len(sinonimos)} pares que podrían ser la misma habilidad antes de ampliar a 300.")
if redundantes:
    rec.append(f"{len(redundantes)} pares aparecen casi siempre juntos (Jaccard >= {JACCARD_REDUNDANTE}). "
               "No es un error, pero conviene tenerlo en cuenta al leer los resultados.")
if grupos_cruzados == 0 and textos_cruzados == 0:
    rec.append("Las particiones no comparten descripciones: no hay fuga de datos.")
else:
    rec.append("ATENCIÓN: hay descripciones compartidas entre particiones; hay que corregir la división.")
if frecuencia["etiquetas_por_registro"]["0"]:
    rec.append(f"{frecuencia['etiquetas_por_registro']['0']} registros no tienen ninguna etiqueta: "
               "ampliar el vocabulario a ~300 habilidades podría cubrirlos.")

resumen = {
    "registros": n,
    "etiquetas": len(ETIQUETAS),
    "1_frecuencia": frecuencia,
    "2_nombres_y_sinonimos": {
        "nombres_con_formato_raro": nombres_raros,
        "una_etiqueta_contiene_a_otra": contenidas,
        "posibles_sinonimos_en_el_vocabulario": sinonimos,
        f"aparecen_juntas_jaccard_>=_{JACCARD_REDUNDANTE}": redundantes[:20],
    },
    "3_duplicados_entre_particiones": {
        "grupos_en_mas_de_una_particion": grupos_cruzados,
        "textos_identicos_en_mas_de_una_particion": textos_cruzados,
        "job_id_repetidos": ids_repetidos,
    },
    "4_cobertura": cobertura,
    "recomendaciones": rec,
}
tabla.to_csv(REPORTES / "validacion_etiquetas_por_habilidad.csv", index=False, encoding="utf-8-sig")
(REPORTES / "validacion_etiquetas.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False,
                                                               default=int), encoding="utf-8")
print(json.dumps(resumen, indent=2, ensure_ascii=False, default=int))
