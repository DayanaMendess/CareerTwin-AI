import os
import json
import pandas as pd

from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]  # la carpeta CareerTwin-AI
CARPETA = RAIZ / "data" / "raw"
REPORTES = RAIZ / "reports"

def ruta(nombre):
    return os.path.join(CARPETA, nombre)

print("Leyendo job_link de cada archivo...")

# usecols -> solo leemos la columna job_link, no los textos largos
links_skills = set(pd.read_csv(ruta("job_skills.csv"), usecols=["job_link"])["job_link"])
links_summary = set(pd.read_csv(ruta("job_summary.csv"), usecols=["job_link"])["job_link"])

# De postings leemos solo las columnas que vamos a analizar
postings = pd.read_csv(
    ruta("linkedin_job_postings.csv"),
    usecols=["job_link", "got_summary", "got_ner", "job_level",
             "job_type", "search_country", "first_seen"],
)
links_postings = set(postings["job_link"])

# 1. Cruces entre archivos (operaciones de conjuntos)
con_las_tres = links_postings & links_skills & links_summary
skills_huerfanas = links_skills - links_postings
summary_huerfanas = links_summary - links_postings

# 2. ¿Las banderas got_summary / got_ner dicen la verdad?
postings["tiene_summary"] = postings["job_link"].isin(links_summary)
postings["tiene_skills"] = postings["job_link"].isin(links_skills)

def tabla_cruzada(col_bandera, col_real):
    conteo = postings.groupby([col_bandera, col_real]).size()
    return {f"{bandera} -> {real}": int(n) for (bandera, real), n in conteo.items()}

# 3. Distribuciones
def contar(columna, top=None):
    conteo = postings[columna].value_counts(dropna=False)
    if top:
        conteo = conteo.head(top)
    return {str(k): int(v) for k, v in conteo.items()}

resultados = {
    "cruces": {
        "ofertas_en_postings": len(links_postings),
        "con_postings_skills_y_summary": len(con_las_tres),
        "skills_sin_posting": len(skills_huerfanas),
        "summary_sin_posting": len(summary_huerfanas),
    },
    "verificacion_banderas": {
        "got_summary -> tiene_summary": tabla_cruzada("got_summary", "tiene_summary"),
        "got_ner -> tiene_skills": tabla_cruzada("got_ner", "tiene_skills"),
    },
    "distribuciones": {
        "job_level": contar("job_level"),
        "job_type": contar("job_type"),
        "search_country_top10": contar("search_country", top=10),
        "first_seen_rango": {
            "desde": str(postings["first_seen"].min()),
            "hasta": str(postings["first_seen"].max()),
        },
    },
}

with open(REPORTES / "auditoria_relaciones.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, indent=2, ensure_ascii=False)

print("Listo. Resultados guardados en auditoria_relaciones.json")