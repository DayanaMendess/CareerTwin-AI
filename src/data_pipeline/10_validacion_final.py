"""
10 - Validación final de los datos (Catalina) — día 11

  1. TRAZABILIDAD: revisa que cada archivo producido exista, de qué script sale
     y cuántas filas tiene.
  2. RECÁLCULO INDEPENDIENTE: vuelve a calcular algunos números desde los CSV
     originales (sin usar los resultados intermedios) y los compara.
  3. CÁLCULOS DEL SIMULADOR: recalcula a mano la compatibilidad de los perfiles
     de ejemplo y la compara con data/app/perfiles_ejemplo.json.
  4. FIGURAS Y TABLAS para el informe (PNG en reports/figuras/).

Salidas:
  reports/validacion_final_datos.md      informe de validación (entregable)
  reports/validacion_final_datos.json
  reports/figuras/*.png                  figuras para el trabajo escrito
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from habilidades_utils import VALORES_VACIOS, separar_habilidades, normalizar_habilidades

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw"
PROC = RAIZ / "data" / "processed"
APP = RAIZ / "data" / "app"
REPORTES = RAIZ / "reports"
FIG = REPORTES / "figuras"
FIG.mkdir(parents=True, exist_ok=True)
BLOQUE = 50_000

# Paleta de referencia (un solo tono para series únicas; azul y naranja para 2 categorías)
AZUL, NARANJA = "#2a78d6", "#eb6834"
FONDO, TEXTO, TEXTO2, REJILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0"


def leer_json(ruta):
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None


# ---------------------------------------------------------------- 1. Trazabilidad
print("[1/4] Revisando trazabilidad de los archivos...")
ARTEFACTOS = [
    ("reports/auditoria_dataset.json", "src/audit_data.py"),
    ("reports/auditoria_detallada.json", "01a–01d_auditoria_*.py"),
    ("reports/catalogo_habilidades_top1000.csv", "02_normalizacion.py"),
    ("reports/clasificacion_habilidades_revisada.csv", "03a + revisión manual"),
    ("reports/skills_vocab_piloto.json", "03b_vocabulario_piloto.py"),
    ("data/processed/muestra_50k.parquet", "04_muestra.py"),
    ("data/processed/datos_entrenamiento.parquet", "05_particiones.py"),
    ("data/processed/familias_laborales.parquet", "07_familias_laborales.py"),
    ("data/processed/habilidades_por_familia.parquet", "07_familias_laborales.py"),
    ("data/processed/relaciones_skills.parquet", "07_familias_laborales.py"),
    ("data/processed/grafo_aristas.parquet", "08_grafo_transiciones.py"),
    ("data/processed/transiciones_familias.parquet", "08_grafo_transiciones.py"),
    ("data/app/familias.json", "09_datos_graficas.py"),
    ("data/app/perfiles_ejemplo.json", "09_datos_graficas.py"),
]
traza = []
for ruta, script in ARTEFACTOS:
    p = RAIZ / ruta
    filas = None
    if p.exists() and p.suffix == ".parquet":
        filas = len(pd.read_parquet(p))
    elif p.exists() and p.suffix == ".csv":
        filas = len(pd.read_csv(p))
    traza.append({"archivo": ruta, "script": script, "existe": p.exists(), "filas": filas})

# ---------------------------------------------------------------- 2. Recálculo independiente
print("[2/4] Recalculando números desde los CSV originales (puede tardar ~2 minutos)...")
controles = {}
ofertas_fam = pd.read_parquet(PROC / "ofertas_familias.parquet")
familias = pd.read_parquet(PROC / "familias_laborales.parquet")
hpf = pd.read_parquet(PROC / "habilidades_por_familia.parquet")

total_postings = sum(len(b) for b in pd.read_csv(RAW / "linkedin_job_postings.csv",
                                                  usecols=["job_link"], chunksize=200_000))
controles["ofertas_por_familia_suman_total_postings"] = (
    int(familias["ofertas"].sum()) == total_postings == len(ofertas_fam))
recuento = ofertas_fam["familia"].value_counts()
controles["recuento_familias_coincide"] = bool(
    (familias.set_index("familia")["ofertas"] == recuento.reindex(familias["familia"]).to_numpy()).all())

# Elegir 3 pares (familia, habilidad) de la tabla y recalcularlos desde job_skills.csv
muestra_pares = (hpf[hpf["familia"] != "Otros"].sort_values("ofertas", ascending=False)
                 .groupby("familia").head(1).head(3))
link_fam = dict(zip(ofertas_fam["job_link"], ofertas_fam["familia"]))
objetivo = {(f, h): 0 for f, h in zip(muestra_pares["familia"], muestra_pares["habilidad"])}
fams_obj = {f for f, _ in objetivo}
for b in pd.read_csv(RAW / "job_skills.csv", chunksize=BLOQUE, keep_default_na=False, dtype=str):
    b = b[~b["job_skills"].str.strip().str.lower().isin(VALORES_VACIOS)]
    b = b[b["job_link"].map(link_fam).isin(fams_obj)]
    if b.empty:
        continue
    normal = normalizar_habilidades(separar_habilidades(b["job_skills"].str.strip()))
    pares = pd.DataFrame({"fila": normal.index, "h": normal.to_numpy()}).drop_duplicates()
    pares["f"] = b.loc[pares["fila"], "job_link"].map(link_fam).to_numpy()
    for (f, h) in objetivo:
        objetivo[(f, h)] += int(((pares["f"] == f) & (pares["h"] == h)).sum())
recalculo = []
for r in muestra_pares.itertuples():
    nuevo = objetivo[(r.familia, r.habilidad)]
    recalculo.append({"familia": r.familia, "habilidad": r.habilidad,
                      "ofertas_tabla": int(r.ofertas), "ofertas_recalculadas": nuevo,
                      "coincide": int(r.ofertas) == nuevo})
controles["recalculo_habilidad_por_familia_coincide"] = all(x["coincide"] for x in recalculo)

part = leer_json(REPORTES / "particiones_resumen.json")
if part:
    tam = {k: v["registros"] for k, v in part["particiones"].items()}
    controles["particiones_suman_50000"] = sum(tam.values()) == 50_000
    controles["particiones_sin_fuga"] = part["grupos_en_mas_de_una_particion"] == 0

# ---------------------------------------------------------------- 3. Cálculos del simulador
print("[3/4] Verificando los cálculos del simulador...")
fam_app = leer_json(APP / "familias.json")
perf_app = leer_json(APP / "perfiles_ejemplo.json")
sim = []
if fam_app and perf_app:
    habs_fam = {f["familia"]: f["habilidades"] for f in fam_app["familias"]}

    def cob(perfil, habs):
        peso = {h["habilidad"]: h["pct_en_familia"] * max(h["lift"], 1) for h in habs}
        tot = sum(peso.values())
        return round(sum(v for k, v in peso.items() if k in perfil) / tot * 100, 1) if tot else 0.0

    for p in perf_app["perfiles"]:
        for r in p["top_familias"][:3]:
            mano = cob(set(p["habilidades"]), habs_fam[r["familia"]])
            sim.append({"perfil": p["perfil"], "familia": r["familia"], "json": r["cobertura_pct"],
                        "a_mano": mano, "coincide": abs(mano - r["cobertura_pct"]) <= 0.1})
        e = p["escenario"]
        if e:
            despues = cob(set(p["habilidades"]) | {e["aprender"]}, habs_fam[e["familia"]])
            sim.append({"perfil": p["perfil"], "familia": e["familia"] + " (después)",
                        "json": e["cobertura_despues"], "a_mano": despues,
                        "coincide": abs(despues - e["cobertura_despues"]) <= 0.1})
    controles["simulador_coincide_a_mano"] = all(x["coincide"] for x in sim)

# ---------------------------------------------------------------- 4. Figuras
print("[4/4] Generando figuras para el informe...")


def estilo(ax, titulo, xlabel):
    ax.set_title(titulo, loc="left", fontsize=12, color=TEXTO, pad=12)
    ax.set_xlabel(xlabel, color=TEXTO2, fontsize=9)
    ax.tick_params(colors=TEXTO2, labelsize=9, length=0)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(REJILLA)
    ax.grid(axis="x", color=REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)


def barras(etiquetas, valores, titulo, xlabel, archivo, colores=None, fmt="{:,.0f}", leyenda=None):
    alto = max(3, 0.32 * len(etiquetas) + 1.2)
    fig, ax = plt.subplots(figsize=(8, alto), facecolor=FONDO)
    ax.set_facecolor(FONDO)
    ax.barh(range(len(valores)), valores, color=colores or AZUL, height=0.7)
    ax.set_yticks(range(len(etiquetas)), etiquetas)
    ax.invert_yaxis()
    for i, v in enumerate(valores):
        ax.text(v, i, "  " + fmt.format(v).replace(",", "."), va="center", fontsize=8, color=TEXTO2)
    ax.set_xlim(0, max(valores) * 1.15)
    estilo(ax, titulo, xlabel)
    if leyenda:
        ax.legend(handles=leyenda, frameon=False, fontsize=9, ncol=2, loc="lower right", bbox_to_anchor=(1, 1.0))
    fig.tight_layout()
    fig.savefig(FIG / archivo, dpi=200, facecolor=FONDO)
    plt.close(fig)
    return archivo


figuras = []
f = familias.sort_values("ofertas", ascending=False)
figuras.append(("Ofertas por familia laboral", barras(
    f["familia"].tolist(), f["ofertas"].tolist(), "Ofertas por familia laboral",
    "Número de ofertas (dataset completo)", "fig_ofertas_por_familia.png")))

glob = (hpf.drop_duplicates("habilidad").sort_values("pct_global", ascending=False).head(20))
cls = pd.read_csv(REPORTES / "clasificacion_habilidades_revisada.csv", keep_default_na=False)
cat = dict(zip(cls["habilidad"], cls["categoria_final"]))
col = [AZUL if cat.get(h) == "tecnica" else NARANJA for h in glob["habilidad"]]
from matplotlib.patches import Patch
figuras.append(("Habilidades más pedidas", barras(
    glob["habilidad"].tolist(), glob["pct_global"].round(1).tolist(),
    "Las 20 habilidades más pedidas", "% de ofertas con habilidades", "fig_top_habilidades.png",
    colores=col, fmt="{:.1f}%", leyenda=[Patch(color=AZUL, label="Técnica"),
                                        Patch(color=NARANJA, label="Blanda")])))

aud = leer_json(REPORTES / "auditoria_detallada.json")
mues = leer_json(REPORTES / "muestra_50k_resumen.json")
if aud and mues:
    etapas = [("Ofertas originales", aud["1_conteos_por_archivo"]["linkedin_job_postings.csv"]["filas_totales"]),
              ("Con las 3 tablas", aud["2_relaciones_entre_archivos"]["cruces"]["con_postings_skills_y_summary"]),
              ("Con habilidades", aud["3_calidad"]["habilidades"]["ofertas_con_habilidades"]),
              ("≥ 50 palabras", mues["universo"]["ofertas_tras_filtros"]),
              ("Textos únicos", mues["universo"]["textos_unicos"]),
              ("Muestra de entrenamiento", mues["muestra"]["filas"])]
    figuras.append(("Etapas de preparación de los datos", barras(
        [e for e, _ in etapas], [v for _, v in etapas], "De 1,3 millones de ofertas a la muestra",
        "Número de ofertas", "fig_etapas_datos.png")))

if part:
    figuras.append(("Particiones", barras(
        ["Entrenamiento", "Validación", "Prueba"], [tam["train"], tam["val"], tam["test"]],
        "División 70/15/15 por grupo de texto", "Número de ofertas", "fig_particiones.png")))

bf = leer_json(REPORTES / "big_five_resumen.json")
if bf:
    d = sorted(bf["pct_ofertas_de_la_muestra_que_piden_el_rasgo"].items(), key=lambda x: -x[1])
    figuras.append(("Big Five", barras(
        [k for k, _ in d], [v for _, v in d], "Rasgos Big Five que piden las ofertas",
        "% de ofertas de la muestra", "fig_big_five.png", fmt="{:.1f}%")))

# ---------------------------------------------------------------- Informe
todo_ok = all(controles.values()) and all(t["existe"] for t in traza)
res = {"todo_correcto": todo_ok, "controles": controles, "trazabilidad": traza,
       "recalculo": recalculo, "simulador": sim, "figuras": [a for _, a in figuras]}
(REPORTES / "validacion_final_datos.json").write_text(
    json.dumps(res, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

md = ["# Validación final de los datos — CareerTwin AI", "",
      "Generado por `src/data_pipeline/10_validacion_final.py`.", "",
      f"**Resultado general:** {'✅ todo correcto' if todo_ok else '⚠️ revisar los controles marcados'}", "",
      "## 1. Trazabilidad", "", "| Archivo | Script que lo genera | Existe | Filas |", "|---|---|---|---|"]
for t in traza:
    filas = "" if t["filas"] is None else f"{t['filas']:,}".replace(",", ".")
    md.append(f"| `{t['archivo']}` | `{t['script']}` | {'✅' if t['existe'] else '❌'} | {filas} |")
md += ["", "## 2. Recálculo independiente desde los CSV originales", "",
       "| Familia | Habilidad | Ofertas en la tabla | Ofertas recalculadas | Coincide |", "|---|---|---|---|---|"]
md += [f"| {r['familia']} | {r['habilidad']} | {r['ofertas_tabla']:,} | {r['ofertas_recalculadas']:,} | "
       f"{'✅' if r['coincide'] else '❌'} |".replace(",", ".") for r in recalculo]
md += ["", "## 3. Cálculos del simulador (perfiles de demostración)", "",
       "| Perfil | Familia | Compatibilidad (JSON) | Recalculada a mano | Coincide |", "|---|---|---|---|---|"]
md += [f"| {s['perfil']} | {s['familia']} | {s['json']} % | {s['a_mano']} % | "
       f"{'✅' if s['coincide'] else '❌'} |" for s in sim]
md += ["", "## 4. Controles", "", "| Control | Resultado |", "|---|---|"]
md += [f"| {k} | {'✅' if v else '❌'} |" for k, v in controles.items()]
md += ["", "## 5. Figuras para el informe", ""]
md += [f"- **Figura {i}.** {t} — `reports/figuras/{a}`" for i, (t, a) in enumerate(figuras, 1)]
md += ["", "## 6. Limitaciones", "",
       "- Datos de LinkedIn de enero de 2024, solo EE. UU., Reino Unido, Canadá y Australia.",
       "- Las habilidades fueron extraídas automáticamente; tienen ruido (Jaccard 0,265 entre copias).",
       "- Las familias se asignan con reglas de palabras clave; el 9,7 % de las ofertas queda en «Otros».",
       "- Las transiciones son patrones observados en las ofertas, no garantías de empleo."]
(REPORTES / "validacion_final_datos.md").write_text("\n".join(md), encoding="utf-8")

print(json.dumps({"todo_correcto": todo_ok, "controles": controles,
                  "recalculo": recalculo, "figuras": [a for _, a in figuras]}, indent=2, ensure_ascii=False))
