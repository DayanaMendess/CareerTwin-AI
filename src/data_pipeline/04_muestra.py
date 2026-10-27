"""
04 - Muestra reproducible de 50.000 ofertas (Catalina)

1. Une los tres CSV por job_link.
2. Se queda con las ofertas que tienen habilidades y una descripción de al menos 50 palabras.
3. Agrupa las descripciones repetidas, incluso las que solo cambian en
   mayúsculas, espacios, puntuación, correos o enlaces ("duplicados finos").
4. Elige 50.000 textos ÚNICOS al azar, con semilla fija (reproducible).
5. Limpia el texto: quita etiquetas HTML y reemplaza correos y enlaces por
   [EMAIL] y [URL]. No toca C++, C#, .NET, Node.js ni las mayúsculas.
6. Guarda la muestra con las columnas de docs/CONTRATO_DATOS.md.

Los CSV originales NO se modifican.

Salidas:
  data/processed/muestra_50k.parquet          (no va a Git)
  data/processed/indice_duplicados.parquet    (job_link -> grupo de texto; para el día 4)
  reports/muestra_50k_resumen.json
"""
import hashlib
import json
import time
from pathlib import Path

import pandas as pd

from habilidades_utils import VALORES_VACIOS, separar_habilidades, normalizar_habilidades

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw"
PROCESADOS = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"
PROCESADOS.mkdir(parents=True, exist_ok=True)

TAMANO_MUESTRA = 50_000
SEMILLA = 42
MIN_PALABRAS = 50
BLOQUE = 50_000
SOURCE_VERSION = "kaggle:asaniczka/1-3m-linkedin-jobs-and-skills-2024"

PATRON_HTML = r"<\s*/?\s*[a-zA-Z][^>]*>"
PATRON_EMAIL = r"[\w.+-]+@[\w-]+\.[\w.-]+"
PATRON_URL = r"(?:https?://|www\.)\S+"
PATRON_TECNICOS = r"(?i)c\+\+|c#|\.net\b|node\.js"


def limpiar_texto(s: pd.Series) -> pd.Series:
    """Limpieza que respeta el contrato: no borra signos técnicos ni cambia mayúsculas."""
    s = s.str.replace(PATRON_HTML, " ", regex=True)
    s = s.str.replace(PATRON_EMAIL, "[EMAIL]", regex=True)   # primero correos...
    s = s.str.replace(PATRON_URL, "[URL]", regex=True)       # ...luego enlaces
    s = s.str.replace(r"[ \t]+", " ", regex=True)            # espacios repetidos
    s = s.str.replace(r"\n\s*\n+", "\n", regex=True)         # líneas vacías repetidas
    return s.str.strip()


def huella(s: pd.Series):
    return pd.util.hash_pandas_object(s, index=False).to_numpy()


def leer(nombre):
    return pd.read_csv(RAW / nombre, chunksize=BLOQUE, keep_default_na=False, dtype=str)


inicio = time.time()

# ---------------------------------------------------------------- 1. Huellas de los textos
print("[1/5] Calculando huellas de las descripciones (pasada 1 por job_summary.csv)...")
partes = []
for i, b in enumerate(leer("job_summary.csv")):
    texto = b["job_summary"]
    exacto = texto.str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    fino = (limpiar_texto(texto).str.lower()
            .str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip())
    partes.append(pd.DataFrame({
        "job_link": b["job_link"].to_numpy(),
        "h_exacto": huella(exacto),
        "h_fino": huella(fino),
        "palabras": texto.str.count(r"\S+").to_numpy(),
    }))
    if i % 5 == 0:
        print(f"    {(i + 1) * BLOQUE:,} filas...")
resumenes = pd.concat(partes, ignore_index=True)
del partes

# ---------------------------------------------------------------- 2. Huellas de las habilidades
print("[2/5] Normalizando habilidades (pasada por job_skills.csv)...")
partes = []
for b in leer("job_skills.csv"):
    texto = b["job_skills"].str.strip()
    b = b[~texto.str.lower().isin(VALORES_VACIOS)]
    original = separar_habilidades(b["job_skills"].str.strip())
    normal = normalizar_habilidades(original[original != ""])
    pares = pd.DataFrame({"fila": normal.index, "h": normal.to_numpy()})
    pares = pares[pares["h"] != ""].drop_duplicates()
    # Huella del CONJUNTO de habilidades: no depende del orden
    pares["hh"] = huella(pares["h"])
    agg = pares.groupby("fila").agg(h_skills=("hh", "sum"), n_skills=("h", "size"))
    agg["job_link"] = b.loc[agg.index, "job_link"].to_numpy()
    partes.append(agg.reset_index(drop=True))
habilidades = pd.concat(partes, ignore_index=True)
del partes

# ---------------------------------------------------------------- 3. Unión y filtros
print("[3/5] Uniendo los tres archivos por job_link...")
postings = pd.read_csv(RAW / "linkedin_job_postings.csv", keep_default_na=False, dtype=str,
                       usecols=["job_link", "job_title", "company", "job_location",
                                "search_country", "job_level"])
universo = postings.merge(habilidades, on="job_link").merge(resumenes, on="job_link")
n_union = len(universo)
cortas = int((universo["palabras"] < MIN_PALABRAS).sum())
universo = universo[universo["palabras"] >= MIN_PALABRAS].reset_index(drop=True)

# Duplicados exactos vs finos
dup_exactos = len(universo) - universo["h_exacto"].nunique()
dup_finos = len(universo) - universo["h_fino"].nunique()

# Misma descripción con conjuntos de habilidades distintos
tam_grupo = universo.groupby("h_fino")["job_link"].transform("size")
universo["ofertas_con_mismo_texto"] = tam_grupo
repetidos = universo[tam_grupo > 1]
skills_por_grupo = repetidos.groupby("h_fino")["h_skills"].nunique()
grupos_conflicto = int((skills_por_grupo > 1).sum())

# Índice para el día 4: a qué grupo de texto pertenece cada oferta
universo["grupo_texto"] = universo["h_fino"].astype(str)
universo[["job_link", "grupo_texto", "ofertas_con_mismo_texto"]].to_parquet(
    PROCESADOS / "indice_duplicados.parquet", index=False)

# ---------------------------------------------------------------- 4. Muestra de textos únicos
print("[4/5] Eligiendo la muestra...")
# Un representante por grupo (el de job_link menor: determinista)
representantes = (universo.sort_values("job_link")
                          .drop_duplicates("h_fino", keep="first"))
n = min(TAMANO_MUESTRA, len(representantes))
muestra = representantes.sample(n=n, random_state=SEMILLA).reset_index(drop=True)
links = set(muestra["job_link"])

# ---------------------------------------------------------------- 5. Texto y habilidades de la muestra
print("[5/5] Limpiando el texto de la muestra (pasada 2 por job_summary.csv)...")
textos, tecnicos_antes, tecnicos_despues = [], 0, 0
for b in leer("job_summary.csv"):
    b = b[b["job_link"].isin(links)]
    if b.empty:
        continue
    limpio = limpiar_texto(b["job_summary"])
    tecnicos_antes += int(b["job_summary"].str.count(PATRON_TECNICOS).sum())
    tecnicos_despues += int(limpio.str.count(PATRON_TECNICOS).sum())
    textos.append(pd.DataFrame({"job_link": b["job_link"].to_numpy(),
                                "job_summary_clean": limpio.to_numpy()}))
textos = pd.concat(textos, ignore_index=True)

listas = []
for b in leer("job_skills.csv"):
    b = b[b["job_link"].isin(links)]
    if b.empty:
        continue
    original = separar_habilidades(b["job_skills"].str.strip())
    normal = normalizar_habilidades(original[original != ""])
    pares = pd.DataFrame({"fila": normal.index, "h": normal.to_numpy()})
    pares = pares[pares["h"] != ""].drop_duplicates()
    lst = pares.groupby("fila")["h"].agg(list)
    listas.append(pd.DataFrame({"job_link": b.loc[lst.index, "job_link"].to_numpy(),
                                "skills_normalized": lst.to_numpy()}))
listas = pd.concat(listas, ignore_index=True)

vocab = json.loads((REPORTES / "skills_vocab_piloto.json").read_text(encoding="utf-8"))
piloto = set(vocab["etiquetas"])

muestra = muestra.merge(textos, on="job_link").merge(listas, on="job_link")
muestra["skills_piloto"] = muestra["skills_normalized"].map(lambda l: [h for h in l if h in piloto])
muestra["n_skills_piloto"] = muestra["skills_piloto"].map(len)
muestra["job_id"] = muestra["job_link"].map(lambda u: hashlib.sha1(u.encode()).hexdigest()[:16])
muestra["source_version"] = SOURCE_VERSION
muestra["grupo_texto"] = muestra["h_fino"].astype(str)

columnas = ["job_id", "job_link", "job_title", "company", "job_location", "search_country",
            "job_level", "job_summary_clean", "skills_normalized", "skills_piloto",
            "n_skills_piloto", "grupo_texto", "ofertas_con_mismo_texto", "source_version"]
muestra = muestra[columnas].sort_values("job_id").reset_index(drop=True)
muestra.to_parquet(PROCESADOS / "muestra_50k.parquet", index=False)

# ---------------------------------------------------------------- Resumen
texto = muestra["job_summary_clean"]
resumen = {
    "semilla": SEMILLA,
    "universo": {
        "ofertas_con_las_3_tablas_y_skills": n_union,
        "descartadas_menos_de_50_palabras": cortas,
        "ofertas_tras_filtros": len(universo),
        "duplicados_exactos": int(dup_exactos),
        "duplicados_finos": int(dup_finos),
        "duplicados_solo_por_formato": int(dup_finos - dup_exactos),
        "textos_unicos": int(universo["h_fino"].nunique()),
        "grupos_con_texto_repetido": int(skills_por_grupo.size),
        "grupos_repetidos_con_habilidades_distintas": grupos_conflicto,
    },
    "muestra": {
        "filas": len(muestra),
        "textos_unicos": int(muestra["grupo_texto"].nunique()),
        "con_[EMAIL]": int(texto.str.contains("[EMAIL]", regex=False).sum()),
        "con_[URL]": int(texto.str.contains("[URL]", regex=False).sum()),
        "terminos_tecnicos_antes_y_despues": [tecnicos_antes, tecnicos_despues],
        "con_al_menos_1_habilidad_piloto": int((muestra["n_skills_piloto"] > 0).sum()),
        "habilidades_piloto_por_oferta_promedio": round(float(muestra["n_skills_piloto"].mean()), 2),
        "job_level": muestra["job_level"].value_counts().to_dict(),
        "paises": muestra["search_country"].value_counts().to_dict(),
    },
    "minutos": round((time.time() - inicio) / 60, 1),
}
with open(REPORTES / "muestra_50k_resumen.json", "w", encoding="utf-8") as f:
    json.dump(resumen, f, indent=2, ensure_ascii=False)
print(json.dumps(resumen, indent=2, ensure_ascii=False))
