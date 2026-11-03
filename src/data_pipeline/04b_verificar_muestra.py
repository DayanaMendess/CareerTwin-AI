"""
04b - Verificación de la muestra (Catalina)

Revisa dos resultados de 04_muestra.py que necesitan explicación:

A. Términos técnicos antes/después de limpiar: ¿se perdió alguno de verdad,
   o los que "faltan" estaban dentro de correos y enlaces (p. ej. "empresa.net")?
B. Descripciones repetidas con habilidades distintas: ¿qué tan distintas son?
   Se mide con el índice de Jaccard (0 = nada en común, 1 = idénticas)
   en una muestra aleatoria de grupos repetidos.

Salida: reports/verificacion_muestra.json
"""
import json
from pathlib import Path

import pandas as pd

from habilidades_utils import separar_habilidades, normalizar_habilidades

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw"
PROC = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"
SEMILLA = 42
N_GRUPOS = 1000
BLOQUE = 50_000

PATRON_EMAIL = r"[\w.+-]+@[\w-]+\.[\w.-]+"
PATRON_URL = r"(?:https?://|www\.)\S+"
TERMINOS = {"c++": r"(?i)c\+\+", "c#": r"(?i)c#", ".net": r"(?i)\.net\b", "node.js": r"(?i)node\.js"}

muestra = pd.read_parquet(PROC / "muestra_50k.parquet",
                          columns=["job_link", "job_summary_clean"])
links = set(muestra["job_link"])

# ---------------------------------------------------------------- A. Términos técnicos
print("[A] Comparando términos técnicos antes y después de limpiar...")
original = []
for b in pd.read_csv(RAW / "job_summary.csv", chunksize=BLOQUE, keep_default_na=False, dtype=str):
    b = b[b["job_link"].isin(links)]
    if not b.empty:
        original.append(b)
original = pd.concat(original, ignore_index=True)["job_summary"]
dentro = (original.str.extractall(f"({PATRON_EMAIL}|{PATRON_URL})")[0]
          .reset_index(drop=True))

terminos = {}
for nombre, patron in TERMINOS.items():
    antes = int(original.str.count(patron).sum())
    despues = int(muestra["job_summary_clean"].str.count(patron).sum())
    en_correos_o_enlaces = int(dentro.str.count(patron).sum())
    terminos[nombre] = {
        "antes": antes,
        "despues": despues,
        "diferencia": antes - despues,
        "estaban_dentro_de_correos_o_enlaces": en_correos_o_enlaces,
        "perdidos_de_verdad": antes - despues - en_correos_o_enlaces,
    }

# ---------------------------------------------------------------- B. Habilidades en textos repetidos
print("[B] Comparando habilidades dentro de grupos de texto repetido...")
indice = pd.read_parquet(PROC / "indice_duplicados.parquet")
repetidos = indice[indice["ofertas_con_mismo_texto"] > 1]
grupos = (repetidos["grupo_texto"].drop_duplicates()
          .sample(n=min(N_GRUPOS, repetidos["grupo_texto"].nunique()), random_state=SEMILLA))
pares = (repetidos[repetidos["grupo_texto"].isin(set(grupos))]
         .sort_values("job_link").groupby("grupo_texto").head(2))
links_b = set(pares["job_link"])

conjuntos = {}
for b in pd.read_csv(RAW / "job_skills.csv", chunksize=BLOQUE, keep_default_na=False, dtype=str):
    b = b[b["job_link"].isin(links_b)]
    if b.empty:
        continue
    normal = normalizar_habilidades(separar_habilidades(b["job_skills"].str.strip()))
    normal = normal[normal != ""]
    for fila, sk in normal.groupby(level=0):
        conjuntos[b.at[fila, "job_link"]] = set(sk)

jaccards, ejemplos = [], []
for grupo, g in pares.groupby("grupo_texto"):
    if len(g) < 2:
        continue
    a, b_ = (conjuntos.get(l, set()) for l in g["job_link"])
    if not (a | b_):
        continue
    j = len(a & b_) / len(a | b_)
    jaccards.append(j)
    if len(ejemplos) < 3:
        ejemplos.append({"oferta_1": sorted(a)[:12], "oferta_2": sorted(b_)[:12],
                         "jaccard": round(j, 2)})
jac = pd.Series(jaccards)

resumen = {
    "A_terminos_tecnicos": terminos,
    "B_habilidades_en_textos_repetidos": {
        "grupos_comparados": len(jac),
        "jaccard_promedio": round(float(jac.mean()), 3),
        "jaccard_mediana": round(float(jac.median()), 3),
        "pares_identicos (jaccard=1)": int((jac == 1).sum()),
        "pares_muy_parecidos (>=0.8)": int((jac >= 0.8).sum()),
        "pares_poco_parecidos (<0.5)": int((jac < 0.5).sum()),
        "ejemplos": ejemplos,
    },
}
with open(REPORTES / "verificacion_muestra.json", "w", encoding="utf-8") as f:
    json.dump(resumen, f, indent=2, ensure_ascii=False)
print(json.dumps(resumen, indent=2, ensure_ascii=False))
