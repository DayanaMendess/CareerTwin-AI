"""
05 - Datos de entrenamiento (Catalina) — día 4

Decisiones acordadas con Sofia:
  * Etiquetas por UNIÓN: se juntan las habilidades normalizadas de todas las copias
    de cada grupo de descripción equivalente (duplicados finos de 04_muestra.py).
  * Solo se admiten etiquetas del vocabulario piloto de 100 habilidades.
  * Se guarda el SOPORTE de cada etiqueta: en cuántas copias del grupo aparece.
  * División 70 % entrenamiento / 15 % validación / 15 % prueba, semilla 42,
    POR GRUPO (un mismo grupo de descripción nunca queda en dos particiones).

Salidas:
  data/processed/datos_entrenamiento.parquet        archivo final (no va a Git; va al Drive)
  data/processed/Y_{train,val,test}.npy             matriz multietiqueta 0/1 (no va a Git)
  reports/skills_vocab.json                         orden de las columnas de Y
  reports/particiones_resumen.json                  registros y habilidades por partición
  reports/conteo_habilidades_por_particion.csv      ejemplos de cada habilidad en cada partición
  reports/verificacion_grupos_manual.csv            grupos para revisar a mano
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from habilidades_utils import separar_habilidades, normalizar_habilidades

SEMILLA = 42
PROPORCIONES = {"train": 0.70, "val": 0.15, "test": 0.15}
N_REVISION_MANUAL = 20        # grupos repetidos que se exportan para revisar a mano
MIN_POSITIVOS_TEST = 30       # menos ejemplos que esto en prueba = métrica poco confiable
BLOQUE = 50_000

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw"
PROC = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

vocab_piloto = json.loads((REPORTES / "skills_vocab_piloto.json").read_text(encoding="utf-8"))
ETIQUETAS = vocab_piloto["etiquetas"]
INDICE = {h: i for i, h in enumerate(ETIQUETAS)}

muestra = pd.read_parquet(PROC / "muestra_50k.parquet",
                          columns=["job_id", "job_link", "job_title", "job_summary_clean",
                                   "skills_piloto", "grupo_texto", "ofertas_con_mismo_texto"])
muestra = muestra.rename(columns={"ofertas_con_mismo_texto": "n_copias"})

# ---------------------------------------------------------------- 1. Consolidar habilidades por grupo
print("[1/5] Consolidando las habilidades de todas las copias de cada grupo...")
indice = pd.read_parquet(PROC / "indice_duplicados.parquet")
copias = indice[indice["grupo_texto"].isin(set(muestra["grupo_texto"]))]
link_a_grupo = dict(zip(copias["job_link"], copias["grupo_texto"]))

soporte = defaultdict(Counter)    # grupo -> {habilidad: número de copias que la traen}
for b in pd.read_csv(RAW / "job_skills.csv", chunksize=BLOQUE, keep_default_na=False, dtype=str):
    b = b[b["job_link"].isin(link_a_grupo)]
    if b.empty:
        continue
    normal = normalizar_habilidades(separar_habilidades(b["job_skills"].str.strip()))
    normal = normal[normal.isin(INDICE)]                     # solo vocabulario piloto
    pares = pd.DataFrame({"fila": normal.index, "h": normal.to_numpy()}).drop_duplicates()
    for fila, h in zip(pares["fila"], pares["h"]):
        soporte[link_a_grupo[b.at[fila, "job_link"]]][h] += 1  # una vez por copia


def etiquetas_de(grupo):
    c = soporte.get(grupo, Counter())
    orden = sorted(c, key=lambda h: (-c[h], INDICE[h]))      # más respaldadas primero
    return orden, [int(c[h]) for h in orden]


pares_etq = muestra["grupo_texto"].map(etiquetas_de)
muestra["etiquetas"] = pares_etq.map(lambda x: x[0])
muestra["soporte_etiquetas"] = pares_etq.map(lambda x: x[1])
muestra["etiquetas_una_copia"] = muestra["skills_piloto"].map(lambda l: sorted(set(l)))
muestra["n_etiquetas"] = muestra["etiquetas"].map(len)

# ---------------------------------------------------------------- 2. División por grupo 70/15/15
print("[2/5] Dividiendo 70/15/15 por grupo de descripción (semilla 42)...")
grupos = muestra["grupo_texto"].drop_duplicates().sample(frac=1, random_state=SEMILLA).to_numpy()
n = len(grupos)
n_train = round(n * PROPORCIONES["train"])
n_val = round(n * PROPORCIONES["val"])
asignacion = {**{g: "train" for g in grupos[:n_train]},
              **{g: "val" for g in grupos[n_train:n_train + n_val]},
              **{g: "test" for g in grupos[n_train + n_val:]}}
muestra["particion"] = muestra["grupo_texto"].map(asignacion)

fuga = int(muestra.groupby("grupo_texto")["particion"].nunique().gt(1).sum())
assert fuga == 0, f"¡Fuga de datos! {fuga} grupos aparecen en más de una partición"

# ---------------------------------------------------------------- 3. Matriz multietiqueta y archivo final
print("[3/5] Construyendo la matriz multietiqueta y guardando el Parquet final...")


def matriz(etiquetas: pd.Series) -> np.ndarray:
    Y = np.zeros((len(etiquetas), len(ETIQUETAS)), dtype=np.uint8)
    for fila, lista in enumerate(etiquetas):
        for h in lista:
            Y[fila, INDICE[h]] = 1
    return Y


orden_part = {"train": 0, "val": 1, "test": 2}
final = (muestra.assign(_o=muestra["particion"].map(orden_part))
         .sort_values(["_o", "job_id"]).drop(columns="_o").reset_index(drop=True))
columnas = ["job_id", "particion", "job_title", "job_summary_clean", "etiquetas",
            "soporte_etiquetas", "n_copias", "n_etiquetas", "grupo_texto"]
final[columnas].to_parquet(PROC / "datos_entrenamiento.parquet", index=False)

conteos, resumen_part = {}, {}
for nombre in orden_part:
    parte = final[final["particion"] == nombre]
    Y = matriz(parte["etiquetas"])
    np.save(PROC / f"Y_{nombre}.npy", Y)               # mismas filas y orden que el Parquet
    conteos[nombre] = Y.sum(axis=0)
    resumen_part[nombre] = {
        "registros": len(parte),
        "porcentaje": round(len(parte) / len(final) * 100, 1),
        "grupos_de_descripcion": int(parte["grupo_texto"].nunique()),
        "registros_sin_etiquetas": int((parte["n_etiquetas"] == 0).sum()),
        "etiquetas_por_registro_promedio": round(float(parte["n_etiquetas"].mean()), 2),
        "total_etiquetas_positivas": int(Y.sum()),
        "habilidades_con_al_menos_1_ejemplo": int((conteos[nombre] > 0).sum()),
        "habilidad_mas_frecuente": ETIQUETAS[int(conteos[nombre].argmax())],
        "habilidad_menos_frecuente": ETIQUETAS[int(conteos[nombre].argmin())],
    }

tabla = pd.DataFrame({"indice": range(len(ETIQUETAS)), "habilidad": ETIQUETAS,
                      "categoria": [vocab_piloto["categoria"].get(h, "") for h in ETIQUETAS]})
for nombre in orden_part:
    tabla[f"{nombre}_ejemplos"] = conteos[nombre].astype(int)
    tabla[f"{nombre}_pct"] = (conteos[nombre] / resumen_part[nombre]["registros"] * 100).round(2)
tabla.to_csv(REPORTES / "conteo_habilidades_por_particion.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 4. Grupos para verificación manual
print("[4/5] Exportando grupos para la verificación manual...")
repetidos = final[final["n_copias"] >= 2]
revision = repetidos.sample(n=min(N_REVISION_MANUAL, len(repetidos)), random_state=SEMILLA).copy()
revision["etiquetas_con_soporte"] = [
    "; ".join(f"{h} ({s}/{c})" for h, s in zip(e, sop))
    for e, sop, c in zip(revision["etiquetas"], revision["soporte_etiquetas"], revision["n_copias"])]
revision["etiquetas_una_copia"] = revision["etiquetas_una_copia"].map("; ".join)
revision["inicio_texto"] = revision["job_summary_clean"].str.slice(0, 400).str.replace("\n", " ")
revision["revision_ok"] = ""          # se llena a mano: si / no / parcial
revision["comentario"] = ""           # se llena a mano
revision[["job_id", "job_title", "n_copias", "etiquetas_con_soporte", "etiquetas_una_copia",
          "inicio_texto", "revision_ok", "comentario"]].to_csv(
    REPORTES / "verificacion_grupos_manual.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 5. Resúmenes
print("[5/5] Guardando el vocabulario y el resumen...")
vocab = {
    "version": "piloto-v1-union",
    "n_etiquetas": len(ETIQUETAS),
    "etiquetas": ETIQUETAS,
    "categoria": vocab_piloto["categoria"],
    "nota": "El orden de 'etiquetas' es el orden de las columnas de Y_*.npy y de las neuronas de salida.",
}
(REPORTES / "skills_vocab.json").write_text(json.dumps(vocab, indent=2, ensure_ascii=False),
                                            encoding="utf-8")

frec_train = conteos["train"] / resumen_part["train"]["registros"] * 100
frec_test = conteos["test"] / resumen_part["test"]["registros"] * 100
rep = final["n_copias"] > 1
sop_todos = [s for lista in final["soporte_etiquetas"] for s in lista]
resumen = {
    "estrategia_etiquetas": "union de copias del grupo (decision de Sofia)",
    "semilla": SEMILLA,
    "division": "70/15/15 por grupo de descripcion",
    "registros_totales": len(final),
    "grupos_en_mas_de_una_particion": fuga,
    "particiones": resumen_part,
    "efecto_de_la_union": {
        "registros_con_copias": int(rep.sum()),
        "etiquetas_por_registro_una_copia": round(float(final["etiquetas_una_copia"].map(len).mean()), 2),
        "etiquetas_por_registro_union": round(float(final["n_etiquetas"].mean()), 2),
        "solo_con_copias_una_copia": round(float(final.loc[rep, "etiquetas_una_copia"].map(len).mean()), 2),
        "solo_con_copias_union": round(float(final.loc[rep, "n_etiquetas"].mean()), 2),
        "etiquetas_respaldadas_por_1_sola_copia": int(sum(1 for s in sop_todos if s == 1)),
        "etiquetas_respaldadas_por_2_o_mas_copias": int(sum(1 for s in sop_todos if s >= 2)),
    },
    "diferencia_maxima_frecuencia_train_vs_test_puntos": round(float(np.abs(frec_train - frec_test).max()), 2),
    f"habilidades_con_menos_de_{MIN_POSITIVOS_TEST}_ejemplos_en_test":
        [ETIQUETAS[i] for i in np.where(conteos["test"] < MIN_POSITIVOS_TEST)[0]],
}
(REPORTES / "particiones_resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False),
                                                   encoding="utf-8")
print(json.dumps(resumen, indent=2, ensure_ascii=False))
