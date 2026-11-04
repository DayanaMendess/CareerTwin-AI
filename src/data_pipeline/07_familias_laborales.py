"""
07 - Familias laborales y relaciones entre habilidades (Catalina) — días 7 y 8

Prepara los datos que usan el matching, el Skill Gap y el Career Simulator:
  1. Normaliza los títulos de los puestos y agrupa los equivalentes
     ("lead sales associate-ft" y "-pt", "&" y "and", texto entre paréntesis...).
  2. Asigna cada oferta a una FAMILIA LABORAL con reglas de palabras clave
     (enfermería, tecnología, ventas...). Las reglas van de lo más específico
     a lo más general: "nurse manager" es Enfermería, no Gerencia.
  3. Calcula las habilidades más frecuentes de cada familia (solo habilidades
     válidas de la revisión manual: técnicas y blandas).
  4. Matriz de coocurrencia: qué habilidades aparecen juntas en las ofertas.

Todo se calcula sobre el dataset COMPLETO (1,3 millones de ofertas), leyendo por bloques.

Salidas:
  data/processed/ofertas_familias.parquet      job_link -> título normalizado y familia (no va a Git)
  data/processed/familias_laborales.parquet    resumen por familia
  data/processed/habilidades_por_familia.parquet
  data/processed/relaciones_skills.parquet     pares de habilidades que aparecen juntas
  reports/familias_laborales.csv, reports/habilidades_por_familia.csv,
  reports/relaciones_skills_top.csv, reports/familias_resumen.json   (copias livianas para Git)
"""
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

from habilidades_utils import VALORES_VACIOS, separar_habilidades, normalizar_habilidades

BLOQUE = 50_000
TOP_HABILIDADES = 25          # habilidades que se guardan por familia
MIN_COOCURRENCIAS = 50        # pares con menos ofertas juntas no se guardan

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw"
PROC = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

# Reglas de familias: (familia, patrón). Se aplica la PRIMERA que coincida,
# así que las específicas van antes que las generales.
FAMILIAS = [
    ("Enfermería", r"\b(nurse|nursing|rn|lpn|lvn|cna|aprn)\b"),
    ("Salud y medicina", r"\b(physician|doctor|md|medical|clinical|clinic|hospital|health|healthcare|"
                         r"pharmac\w*|therap\w*|radiolog\w*|sonograph\w*|technologist|dental|dentist|"
                         r"hygienist|veterinar\w*|surg\w*|patient|caregiver|phlebotom\w*|psychiatr\w*|"
                         r"anesthes\w*|respiratory|paramedic|emt|\w+ologist|pt|personal trainer|fitness)\b"),
    ("Tecnología e informática", r"\b(software|developer|devops|programmer|cloud|cyber\w*|"
                                 r"network|systems? administrator|it|full ?stack|front ?end|back ?end|"
                                 r"web|java|python|\.net|sre|salesforce|sap|database|infrastructure)\b"),
    ("Datos y análisis", r"\b(data|analytics|analyst|business intelligence|bi|machine learning|"
                         r"scientist|statistic\w*)\b"),
    ("Finanzas y contabilidad", r"\b(account(ant|ing)|finance|financial|tax|audit\w*|bookkeep\w*|"
                                r"payroll|controller|cpa|actuar\w*|underwrit\w*|loan|credit|bank\w*|teller)\b"),
    ("Recursos humanos", r"\b(human resources|hr|recruit\w*|talent|people operations)\b"),
    ("Marketing y comunicación", r"\b(marketing|brand|social media|communications|content|seo|"
                                 r"public relations|graphic|designer|copywriter|writer|editor)\b"),
    ("Legal", r"\b(attorney|lawyer|paralegal|legal|counsel|solicitor|compliance)\b"),
    ("Educación", r"\b(teach\w*|tutor|professor|instructor|educat\w*|school|lecturer|faculty|"
                  r"teaching|paraprofessional|childcare|preschool)\b"),
    ("Servicios sociales", r"\b(social worker|case manager|counselor|counsellor|behavioral|"
                           r"behavior technician|youth|family support|community)\b"),
    ("Atención al cliente", r"\b(customer service|customer support|call center|client services|"
                            r"customer success|customer care|service advisor)\b"),
    ("Restaurantes y alimentos", r"\b(restaurant|cook|chef|server|host|hostess|bartender|barista|"
                                 r"kitchen|dishwasher|food|culinary|crew member|baker|catering|to go)\b"),
    ("Comercio y tiendas", r"\b(retail|store|cashier|merchandis\w*|shopper|stock\w*|sales associate|"
                           r"shift manager|shift leader|key holder|keyholder|guest advocate|guest advisor|"
                           r"product demonstrator|buyer)\b"),
    ("Ventas", r"\b(sales|ventas|account executive|account manager|business development|"
               r"territory|representative|leasing|real estate|realtor)\b"),
    ("Logística y transporte", r"\b(driver|warehouse|logistics|supply chain|truck|delivery|forklift|"
                               r"shipping|receiving|dispatcher|courier|fleet|cdl|inventory|"
                               r"material handler|transport\w*|conductor|entrega|domicilio)\b"),
    ("Construcción", r"\b(construction|carpenter|superintendent|laborer|roofer|estimator|surveyor|"
                     r"architect\w*|site manager|foreman|flagger|traffic control)\b"),
    ("Manufactura y mantenimiento", r"\b(technician|mechanic|maintenance|operator|production|"
                                    r"manufacturing|assembler|welder|electrician|machinist|hvac|"
                                    r"plumber|installer|repair|fabricat\w*|quality)\b"),
    ("Ingeniería", r"\b(engineer\w*)\b"),
    ("Seguridad", r"\b(security officer|security guard|guard|police|correctional|safety)\b"),
    ("Limpieza y servicios generales", r"\b(housekeep\w*|janitor\w*|custodian|cleaner|cleaning|"
                                       r"environmental services|groundskeeper|porter)\b"),
    ("Administración y oficina", r"\b(administrative|admin|assistant|receptionist|office|clerk|"
                                 r"secretary|coordinator|scheduler|data entry|administrator)\b"),
    ("Gerencia y dirección", r"\b(manager|gerente|director|supervisor|lead|leader|head|chief|vp|president|"
                             r"executive|operations)\b"),
]
FAMILIAS_RE = [(f, re.compile(p)) for f, p in FAMILIAS]


def normalizar_titulo(s: pd.Series) -> pd.Series:
    t = s.fillna("").astype(str).str.lower()
    t = t.str.replace(r"\([^)]*\)", " ", regex=True)                      # quitar paréntesis
    t = t.str.replace("&", " and ", regex=False)
    t = t.str.replace(r"[-–—/|,:]+\s*(ft|pt|full[ -]?time|part[ -]?time)\b.*$", " ",
                      regex=True)                                          # -ft / -pt
    t = t.str.replace(r"\b(full|part)[ -]?time\b", " ", regex=True)
    t = t.str.replace(r"\$[\d,.]+.*$", " ", regex=True)                    # salario al final
    t = t.str.replace(r"[^a-z0-9+#. ]+", " ", regex=True)
    return t.str.replace(r"\s+", " ", regex=True).str.strip()


def asignar_familia(titulo: str) -> str:
    for familia, patron in FAMILIAS_RE:
        if patron.search(titulo):
            return familia
    return "Otros"


inicio = time.time()

# ---------------------------------------------------------------- 1. Títulos y familias
print("[1/4] Normalizando títulos y asignando familias...")
postings = pd.read_csv(RAW / "linkedin_job_postings.csv", usecols=["job_link", "job_title"],
                       keep_default_na=False, dtype=str)
postings["titulo_normalizado"] = normalizar_titulo(postings["job_title"])
unicos = postings["titulo_normalizado"].drop_duplicates()
mapa = dict(zip(unicos, unicos.map(asignar_familia)))
postings["familia"] = postings["titulo_normalizado"].map(mapa)
postings[["job_link", "titulo_normalizado", "familia"]].to_parquet(
    PROC / "ofertas_familias.parquet", index=False)
link_familia = dict(zip(postings["job_link"], postings["familia"]))

# ---------------------------------------------------------------- 2. Habilidades válidas
cls = pd.read_csv(REPORTES / "clasificacion_habilidades_revisada.csv", keep_default_na=False)
validas = cls[cls["categoria_final"].isin(["tecnica", "blanda"])]
VALIDAS = validas["habilidad"].tolist()
CATEGORIA = dict(zip(validas["habilidad"], validas["categoria_final"]))
IDX = {h: i for i, h in enumerate(VALIDAS)}

# ---------------------------------------------------------------- 3. Recorrer job_skills
print("[2/4] Contando habilidades por familia y coocurrencias (dataset completo)...")
cooc = np.zeros((len(VALIDAS), len(VALIDAS)), dtype=np.int64)
conteo_familia = {}          # (familia, habilidad) -> ofertas
ofertas_familia = {}         # familia -> ofertas con habilidades
for i, b in enumerate(pd.read_csv(RAW / "job_skills.csv", chunksize=BLOQUE,
                                  keep_default_na=False, dtype=str)):
    texto = b["job_skills"].str.strip()
    b = b[~texto.str.lower().isin(VALORES_VACIOS)]
    normal = normalizar_habilidades(separar_habilidades(b["job_skills"].str.strip()))
    normal = normal[normal.isin(IDX)]
    pares = pd.DataFrame({"fila": normal.index, "h": normal.to_numpy()}).drop_duplicates()
    pares["familia"] = b.loc[pares["fila"], "job_link"].map(link_familia).fillna("Otros").to_numpy()

    for (f, h), n in pares.groupby(["familia", "h"]).size().items():
        conteo_familia[(f, h)] = conteo_familia.get((f, h), 0) + int(n)
    fam_bloque = b["job_link"].map(link_familia).fillna("Otros").value_counts()
    for f, n in fam_bloque.items():
        ofertas_familia[f] = ofertas_familia.get(f, 0) + int(n)

    filas = pd.factorize(pares["fila"])[0]
    X = np.zeros((filas.max() + 1 if len(filas) else 0, len(VALIDAS)), dtype=np.float32)
    X[filas, pares["h"].map(IDX).to_numpy()] = 1
    cooc += (X.T @ X).astype(np.int64)
    if i % 5 == 0:
        print(f"    bloque {i + 1}...")

# ---------------------------------------------------------------- 4. Tablas finales
print("[3/4] Construyendo las tablas de familias...")
total_ofertas = sum(ofertas_familia.values())
hpf = pd.DataFrame([(f, h, n) for (f, h), n in conteo_familia.items()],
                   columns=["familia", "habilidad", "ofertas"])
hpf["ofertas_familia"] = hpf["familia"].map(ofertas_familia)
hpf["pct_en_familia"] = (hpf["ofertas"] / hpf["ofertas_familia"] * 100).round(2)
pct_global = pd.Series(np.diag(cooc) / total_ofertas * 100, index=VALIDAS)
hpf["pct_global"] = hpf["habilidad"].map(pct_global).round(2)
# lift > 1: la familia pide esa habilidad más que el promedio del mercado
hpf["lift"] = (hpf["pct_en_familia"] / hpf["pct_global"]).round(2)
hpf["categoria"] = hpf["habilidad"].map(CATEGORIA)
hpf = hpf.sort_values(["familia", "ofertas"], ascending=[True, False])
hpf["rango"] = hpf.groupby("familia").cumcount() + 1
hpf = hpf[hpf["rango"] <= TOP_HABILIDADES].reset_index(drop=True)

titulos = postings.groupby("familia")["titulo_normalizado"].agg(
    titulos_distintos="nunique",
    titulos_frecuentes=lambda t: t.value_counts().head(5).index.tolist())
familias = postings["familia"].value_counts().rename("ofertas").to_frame().join(titulos)
familias["pct_ofertas"] = (familias["ofertas"] / len(postings) * 100).round(2)
familias["habilidades_top"] = (hpf[hpf["rango"] <= 10].groupby("familia")["habilidad"].agg(list))
familias = familias.reset_index().rename(columns={"index": "familia"})
if "familia" not in familias.columns:
    familias = familias.rename(columns={familias.columns[0]: "familia"})

print("[4/4] Construyendo la matriz de coocurrencia...")
a, bb = np.triu_indices(len(VALIDAS), k=1)
juntas = cooc[a, bb]
mask = juntas >= MIN_COOCURRENCIAS
a, bb, juntas = a[mask], bb[mask], juntas[mask]
na, nb = np.diag(cooc)[a], np.diag(cooc)[bb]
rel = pd.DataFrame({
    "habilidad_a": np.array(VALIDAS)[a], "habilidad_b": np.array(VALIDAS)[bb],
    "ofertas_juntas": juntas,
    "p_b_dado_a": (juntas / na).round(4),      # de las ofertas que piden A, cuántas piden B
    "p_a_dado_b": (juntas / nb).round(4),
    "jaccard": (juntas / (na + nb - juntas)).round(4),
    "lift": (juntas * total_ofertas / (na * nb)).round(3),   # > 1: aparecen juntas más que por azar
}).sort_values("ofertas_juntas", ascending=False).reset_index(drop=True)

# ---------------------------------------------------------------- Guardar
familias.to_parquet(PROC / "familias_laborales.parquet", index=False)
hpf.to_parquet(PROC / "habilidades_por_familia.parquet", index=False)
rel.to_parquet(PROC / "relaciones_skills.parquet", index=False)
familias.assign(titulos_frecuentes=familias["titulos_frecuentes"].map(" | ".join),
                habilidades_top=familias["habilidades_top"].map(
                    lambda l: " | ".join(l) if isinstance(l, list) else "")).to_csv(
    REPORTES / "familias_laborales.csv", index=False, encoding="utf-8-sig")
hpf.to_csv(REPORTES / "habilidades_por_familia.csv", index=False, encoding="utf-8-sig")
rel.head(500).to_csv(REPORTES / "relaciones_skills_top.csv", index=False, encoding="utf-8-sig")

otros = postings[postings["familia"] == "Otros"]["titulo_normalizado"].value_counts().head(20)
resumen = {
    "ofertas": len(postings),
    "titulos_distintos_originales": int(postings["job_title"].str.lower().nunique()),
    "titulos_distintos_normalizados": int(postings["titulo_normalizado"].nunique()),
    "familias": len(FAMILIAS),
    "ofertas_clasificadas_pct": round(float((postings["familia"] != "Otros").mean() * 100), 2),
    "ofertas_por_familia": familias.set_index("familia")["ofertas"].astype(int).to_dict(),
    "titulos_mas_frecuentes_sin_familia": otros.astype(int).to_dict(),
    "habilidades_validas_usadas": len(VALIDAS),
    "pares_de_habilidades_guardados": len(rel),
    "minutos": round((time.time() - inicio) / 60, 1),
}
(REPORTES / "familias_resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False),
                                               encoding="utf-8")
print(json.dumps(resumen, indent=2, ensure_ascii=False))
