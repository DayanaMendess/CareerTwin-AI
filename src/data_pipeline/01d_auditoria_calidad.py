import os
import json
import time
from collections import Counter

import numpy as np
import pandas as pd

from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]  # la carpeta CareerTwin-AI
CARPETA = RAIZ / "data" / "raw"
REPORTES = RAIZ / "reports"
TAMANO_BLOQUE = 50_000


def ruta(nombre):
    return os.path.join(CARPETA, nombre)


def resumen_numerico(valores):
    """Mínimo, percentiles, promedio y máximo de una lista de números."""
    v = np.asarray(valores)
    p1, p25, p50, p75, p99 = np.percentile(v, [1, 25, 50, 75, 99])
    return {
        "minimo": int(v.min()),
        "percentil_1": int(p1),
        "percentil_25": int(p25),
        "mediana": int(p50),
        "promedio": round(float(v.mean()), 1),
        "percentil_75": int(p75),
        "percentil_99": int(p99),
        "maximo": int(v.max()),
    }


inicio_total = time.time()

# ======================================================================
# 1. DESCRIPCIONES (job_summary.csv) -> el archivo de 5 GB, por bloques
# ======================================================================
print("[1/3] Analizando descripciones... (es la parte más lenta)")

PATRON_HTML = r"<\s*/?\s*[a-zA-Z][^>]*>"            # etiquetas como <br> o <p>
PATRON_ENTIDAD = r"&(?:nbsp|amp|lt|gt|quot|#\d+);"  # códigos como &nbsp;
PATRON_EMAIL = r"[\w.+-]+@[\w-]+\.[\w.-]+"          # correos electrónicos
PATRON_URL = r"https?://|www\."                      # enlaces web

largos_caracteres, largos_palabras, huellas = [], [], []
con_html = con_entidades = con_email = con_url = mucho_no_ascii = 0
filas_leidas = 0

for i, bloque in enumerate(pd.read_csv(ruta("job_summary.csv"), chunksize=TAMANO_BLOQUE)):
    texto = bloque["job_summary"].fillna("").astype(str)
    n_caracteres = texto.str.len()

    largos_caracteres.append(n_caracteres.to_numpy(dtype="int64"))
    largos_palabras.append(texto.str.count(r"\S+").to_numpy(dtype="int64"))

    con_html += int(texto.str.contains(PATRON_HTML, regex=True).sum())
    con_entidades += int(texto.str.contains(PATRON_ENTIDAD, regex=True).sum())
    con_email += int(texto.str.contains(PATRON_EMAIL, regex=True).sum())
    con_url += int(texto.str.contains(PATRON_URL, regex=True).sum())

    # Proporción de caracteres que no son del alfabeto inglés básico
    no_ascii = texto.str.count(r"[^\x00-\x7F]")
    mucho_no_ascii += int((no_ascii / n_caracteres.clip(lower=1) > 0.2).sum())

    # "Huella digital" del texto normalizado para detectar descripciones repetidas
    normalizado = texto.str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    huellas.append(pd.util.hash_pandas_object(normalizado, index=False).to_numpy())

    filas_leidas += len(bloque)
    if i % 5 == 0:
        print(f"    {filas_leidas:,} filas procesadas...")

caracteres = np.concatenate(largos_caracteres)
palabras = np.concatenate(largos_palabras)
huellas = pd.Series(np.concatenate(huellas))

calidad_descripciones = {
    "filas_analizadas": int(len(caracteres)),
    "caracteres": resumen_numerico(caracteres),
    "palabras": resumen_numerico(palabras),
    "menos_de_20_palabras": int((palabras < 20).sum()),
    "menos_de_50_palabras": int((palabras < 50).sum()),
    "menos_de_100_palabras": int((palabras < 100).sum()),
    "mas_de_2000_palabras": int((palabras > 2000).sum()),
    "con_etiquetas_html": con_html,
    "con_entidades_html": con_entidades,
    "con_correos_electronicos": con_email,
    "con_enlaces_web": con_url,
    "con_mas_de_20pct_caracteres_no_ascii": mucho_no_ascii,
    "descripciones_repetidas_exactas": int(huellas.duplicated().sum()),
}
del largos_caracteres, largos_palabras, huellas
print(f"    Listo en {round(time.time() - inicio_total)} s")

# ======================================================================
# 2. HABILIDADES (job_skills.csv)
# ======================================================================
print("[2/3] Analizando habilidades...")
inicio = time.time()

conteo_original = Counter()    # habilidades tal cual vienen
conteo_normalizado = Counter() # en minúsculas y sin espacios extra
habilidades_por_oferta = []

for bloque in pd.read_csv(ruta("job_skills.csv"), chunksize=TAMANO_BLOQUE):
    habilidades = bloque["job_skills"].dropna()

    # "Python, SQL, Excel" -> una fila por habilidad
    lista = habilidades.str.split(",").explode().str.strip()
    lista = lista[lista != ""]

    habilidades_por_oferta.append(lista.groupby(level=0).size().to_numpy())
    conteo_original.update(lista.value_counts().to_dict())

    normal = lista.str.lower().str.replace(r"\s+", " ", regex=True)
    conteo_normalizado.update(normal.value_counts().to_dict())

por_oferta = np.concatenate(habilidades_por_oferta)
frecuencias = np.array(list(conteo_normalizado.values()))


def variantes(palabra, top=8):
    """Formas distintas en que aparece una habilidad en los datos originales."""
    encontradas = {k: v for k, v in conteo_original.items() if palabra in k.lower()}
    mejores = sorted(encontradas.items(), key=lambda x: -x[1])[:top]
    return {k: int(v) for k, v in mejores}


calidad_habilidades = {
    "ofertas_con_habilidades": int(len(por_oferta)),
    "habilidades_por_oferta": resumen_numerico(por_oferta),
    "total_menciones": int(sum(conteo_original.values())),
    "habilidades_distintas_originales": len(conteo_original),
    "habilidades_distintas_en_minusculas": len(conteo_normalizado),
    "aparecen_solo_1_vez": int((frecuencias == 1).sum()),
    "aparecen_10_o_mas_veces": int((frecuencias >= 10).sum()),
    "aparecen_100_o_mas_veces": int((frecuencias >= 100).sum()),
    "aparecen_1000_o_mas_veces": int((frecuencias >= 1000).sum()),
    "top_30": {k: int(v) for k, v in conteo_normalizado.most_common(30)},
    "variantes_python": variantes("python"),
    "variantes_communication": variantes("communication"),
    "variantes_excel": variantes("excel"),
}
del conteo_original, conteo_normalizado
print(f"    Listo en {round(time.time() - inicio)} s")

# ======================================================================
# 3. TÍTULOS Y OFERTAS REPETIDAS (linkedin_job_postings.csv)
# ======================================================================
print("[3/3] Analizando títulos...")
p = pd.read_csv(ruta("linkedin_job_postings.csv"),
                usecols=["job_title", "company", "job_location"])

titulos = p["job_title"].str.lower().str.strip()

calidad_titulos = {
    "titulos_distintos_en_minusculas": int(titulos.nunique()),
    "repetidas_mismo_titulo_empresa_y_lugar": int(
        p.duplicated(subset=["job_title", "company", "job_location"]).sum()),
    "top_20_titulos": {k: int(v) for k, v in titulos.value_counts().head(20).items()},
}

# ======================================================================
# 4. UNIR TODO EN auditoria_dataset.json
# ======================================================================
with open(REPORTES / "auditoria_conteos.json", encoding="utf-8") as f:
    conteos = json.load(f)
with open(REPORTES / "auditoria_relaciones.json", encoding="utf-8") as f:
    relaciones = json.load(f)

auditoria = {
    "dataset": "1.3M LinkedIn Jobs & Skills (2024) - Kaggle (asaniczka)",
    "fecha_auditoria": time.strftime("%Y-%m-%d %H:%M"),
    "responsable": "Catalina",
    "1_conteos_por_archivo": conteos,
    "2_relaciones_entre_archivos": relaciones,
    "3_calidad": {
        "descripciones": calidad_descripciones,
        "habilidades": calidad_habilidades,
        "titulos": calidad_titulos,
    },
}

with open(REPORTES / "auditoria_detallada.json", "w", encoding="utf-8") as f:
    json.dump(auditoria, f, indent=2, ensure_ascii=False)

print(f"\nAuditoría completa en {round((time.time() - inicio_total) / 60, 1)} minutos.")
print("Guardada en reports/auditoria_detallada.json")