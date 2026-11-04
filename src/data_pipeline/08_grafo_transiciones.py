"""
08 - Grafo de habilidades y transiciones profesionales (Catalina) — día 10

Usa los resultados de 07_familias_laborales.py (dataset completo):
  1. GRAFO DE HABILIDADES: cada habilidad es un nodo; dos habilidades se conectan
     si aparecen juntas en las ofertas MÁS de lo que pasaría por azar (lift > 1)
     y en suficientes ofertas. La fuerza de la conexión es el lift.
  2. RELACIONES ENTRE TECNOLOGÍAS: el mismo grafo, solo con habilidades técnicas.
  3. TRANSICIONES PROFESIONALES: compara las familias laborales por las
     habilidades que piden MÁS que el promedio del mercado (similitud coseno). Para cada familia, las más
     parecidas son transiciones posibles, con las habilidades que ya se tienen
     y las que habría que aprender.
  4. EVIDENCIA: cada conexión y cada transición guarda los números del dataset
     que la respaldan, para verificar que no son inventadas.

Salidas:
  data/processed/grafo_nodos.parquet, data/processed/grafo_aristas.parquet
  data/processed/transiciones_familias.parquet
  reports/grafo_nodos.csv, reports/grafo_aristas_top.csv,
  reports/grafo_tecnologias.csv, reports/transiciones_familias.csv,
  reports/grafo_resumen.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

MIN_OFERTAS_JUNTAS = 200     # conexiones con menos ofertas son poco confiables
MIN_LIFT = 1.5               # aparecen juntas al menos 1,5 veces más que por azar
VECINOS_POR_HABILIDAD = 10   # para la app: las 10 habilidades más relacionadas
TRANSICIONES_POR_FAMILIA = 5
TOP_APRENDER = 6

RAIZ = Path(__file__).resolve().parents[2]
PROC = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

rel = pd.read_parquet(PROC / "relaciones_skills.parquet")
hpf = pd.read_parquet(PROC / "habilidades_por_familia.parquet")
familias = pd.read_parquet(PROC / "familias_laborales.parquet")
cls = pd.read_csv(REPORTES / "clasificacion_habilidades_revisada.csv", keep_default_na=False)
CATEGORIA = dict(zip(cls["habilidad"], cls["categoria_final"]))

# ---------------------------------------------------------------- 1. Grafo de habilidades
print("[1/3] Construyendo el grafo de habilidades...")
aristas = rel[(rel["ofertas_juntas"] >= MIN_OFERTAS_JUNTAS) & (rel["lift"] >= MIN_LIFT)].copy()
aristas["categoria_a"] = aristas["habilidad_a"].map(CATEGORIA)
aristas["categoria_b"] = aristas["habilidad_b"].map(CATEGORIA)
aristas = aristas.sort_values("lift", ascending=False).reset_index(drop=True)

# Las dos direcciones, para buscar vecinos de cada habilidad
dir_a = aristas.rename(columns={"habilidad_a": "habilidad", "habilidad_b": "vecina",
                                "p_b_dado_a": "p_vecina_dada_habilidad"})
dir_b = aristas.rename(columns={"habilidad_b": "habilidad", "habilidad_a": "vecina",
                                "p_a_dado_b": "p_vecina_dada_habilidad"})
cols = ["habilidad", "vecina", "ofertas_juntas", "p_vecina_dada_habilidad", "jaccard", "lift"]
vecinos = pd.concat([dir_a[cols], dir_b[cols]], ignore_index=True)
vecinos = vecinos.sort_values(["habilidad", "lift"], ascending=[True, False])
vecinos_top = vecinos.groupby("habilidad").head(VECINOS_POR_HABILIDAD)

nodos = pd.DataFrame({"habilidad": sorted(set(aristas["habilidad_a"]) | set(aristas["habilidad_b"]))})
nodos["categoria"] = nodos["habilidad"].map(CATEGORIA)
grado = vecinos.groupby("habilidad").size()
fuerza = vecinos.groupby("habilidad")["lift"].sum()
nodos["conexiones"] = nodos["habilidad"].map(grado).fillna(0).astype(int)
nodos["fuerza"] = nodos["habilidad"].map(fuerza).fillna(0).round(2)
nodos["vecinas_principales"] = nodos["habilidad"].map(
    vecinos_top.groupby("habilidad")["vecina"].agg(lambda v: " | ".join(v.head(5))))
# Familia donde cada habilidad es más característica (mayor lift)
fam_principal = (hpf.sort_values("lift", ascending=False)
                 .drop_duplicates("habilidad").set_index("habilidad")["familia"])
nodos["familia_mas_caracteristica"] = nodos["habilidad"].map(fam_principal)
nodos = nodos.sort_values("conexiones", ascending=False).reset_index(drop=True)

tecnologias = aristas[(aristas["categoria_a"] == "tecnica") & (aristas["categoria_b"] == "tecnica")]

# ---------------------------------------------------------------- 2. Transiciones entre familias
print("[2/3] Calculando transiciones entre familias laborales...")
hpf_f = hpf[hpf["familia"] != "Otros"].copy()
# Perfil de cada familia: cuánto MÁS que el mercado pide cada habilidad.
# Así habilidades que todas piden (communication) no hacen que todas las familias
# parezcan iguales; cuenta lo que es propio de cada una.
hpf_f["exceso"] = (hpf_f["pct_en_familia"] - hpf_f["pct_global"]).clip(lower=0)
perfil = hpf_f.pivot_table(index="familia", columns="habilidad", values="exceso",
                           fill_value=0.0)
M = perfil.to_numpy()
normas = np.linalg.norm(M, axis=1, keepdims=True)
sim = (M / np.where(normas == 0, 1, normas)) @ (M / np.where(normas == 0, 1, normas)).T
FAMS = perfil.index.tolist()

top_por_familia = {f: g.sort_values("ofertas", ascending=False)
                   for f, g in hpf_f.groupby("familia")}
filas = []
for i, origen in enumerate(FAMS):
    orden = [j for j in np.argsort(-sim[i]) if j != i][:TRANSICIONES_POR_FAMILIA]
    habs_origen = set(top_por_familia[origen]["habilidad"])
    for rango, j in enumerate(orden, start=1):
        destino = FAMS[j]
        g_dest = top_por_familia[destino]
        compartidas = [h for h in g_dest["habilidad"] if h in habs_origen]
        # Lo que habría que aprender: lo propio del destino (lift alto) que el origen no tiene
        aprender = (g_dest[~g_dest["habilidad"].isin(habs_origen)]
                    .sort_values("lift", ascending=False))
        filas.append({
            "familia_origen": origen,
            "familia_destino": destino,
            "rango": rango,
            "similitud": round(float(sim[i, j]), 3),
            "habilidades_compartidas": len(compartidas),
            "compartidas_ejemplo": " | ".join(compartidas[:6]),
            "habilidades_a_aprender": " | ".join(aprender["habilidad"].head(TOP_APRENDER)),
            "evidencia_pct_en_destino": " | ".join(
                f"{h} ({p}%)" for h, p in zip(aprender["habilidad"].head(TOP_APRENDER),
                                              aprender["pct_en_familia"].head(TOP_APRENDER))),
        })
transiciones = pd.DataFrame(filas)

# ---------------------------------------------------------------- 3. Guardar
print("[3/3] Guardando...")
nodos.to_parquet(PROC / "grafo_nodos.parquet", index=False)
aristas.to_parquet(PROC / "grafo_aristas.parquet", index=False)
transiciones.to_parquet(PROC / "transiciones_familias.parquet", index=False)
nodos.to_csv(REPORTES / "grafo_nodos.csv", index=False, encoding="utf-8-sig")
aristas.head(500).to_csv(REPORTES / "grafo_aristas_top.csv", index=False, encoding="utf-8-sig")
tecnologias.head(300).to_csv(REPORTES / "grafo_tecnologias.csv", index=False, encoding="utf-8-sig")
transiciones.to_csv(REPORTES / "transiciones_familias.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(sim, index=FAMS, columns=FAMS).round(3).to_csv(
    REPORTES / "similitud_familias.csv", encoding="utf-8-sig")

ejemplo = {}
for f in ["Restaurantes y alimentos", "Datos y análisis", "Enfermería"]:
    t = transiciones[(transiciones["familia_origen"] == f) & (transiciones["rango"] <= 3)]
    ejemplo[f] = [f"{d} (similitud {s}) -> aprender: {a}"
                  for d, s, a in zip(t["familia_destino"], t["similitud"], t["habilidades_a_aprender"])]

resumen = {
    "criterios": {"min_ofertas_juntas": MIN_OFERTAS_JUNTAS, "min_lift": MIN_LIFT},
    "grafo": {
        "nodos": len(nodos),
        "aristas": len(aristas),
        "aristas_entre_tecnologias": len(tecnologias),
        "habilidades_mas_conectadas": nodos.head(10)[["habilidad", "conexiones"]].values.tolist(),
        "conexiones_mas_fuertes": aristas.head(10)[["habilidad_a", "habilidad_b", "lift",
                                                    "ofertas_juntas"]].values.tolist(),
    },
    "transiciones": {
        "familias": len(FAMS),
        "transiciones_guardadas": len(transiciones),
        "ejemplos": ejemplo,
    },
    "nota": ("Las conexiones y transiciones se calculan con frecuencias del dataset de LinkedIn "
             "(enero 2024, 4 países). Muestran patrones observados en las ofertas, no garantizan "
             "que un cambio de carrera sea posible ni exitoso."),
}
(REPORTES / "grafo_resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False,
                                                        default=lambda x: x.item()), encoding="utf-8")
print(json.dumps(resumen, indent=2, ensure_ascii=False, default=lambda x: x.item()))
