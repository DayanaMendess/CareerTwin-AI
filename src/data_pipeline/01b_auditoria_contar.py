import os
import json
import time
import pandas as pd

from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]  # la carpeta CareerTwin-AI
CARPETA = RAIZ / "data" / "raw"
REPORTES = RAIZ / "reports"
ARCHIVOS = ["linkedin_job_postings.csv", "job_skills.csv", "job_summary.csv"]
TAMANO_BLOQUE = 50_000  # filas que se leen a la vez

resultados = {}

for nombre in ARCHIVOS:
    print(f"\nProcesando {nombre}... (puede tardar unos minutos)")
    inicio = time.time()
    ruta = os.path.join(CARPETA, nombre)

    total_filas = 0
    nulos = None
    links = []

    # Leemos el archivo por pedazos de 50.000 filas
    for bloque in pd.read_csv(ruta, chunksize=TAMANO_BLOQUE):
        total_filas += len(bloque)

        # Contamos los valores vacíos (nulos) de cada columna en este bloque
        nulos_bloque = bloque.isna().sum()
        nulos = nulos_bloque if nulos is None else nulos + nulos_bloque

        # Guardamos solo los job_link para revisar duplicados al final
        links.append(bloque["job_link"].copy())

    # Unimos todos los job_link y contamos los repetidos
    todos_links = pd.concat(links, ignore_index=True)
    duplicados = int(todos_links.duplicated().sum())
    unicos = int(todos_links.nunique())

    segundos = round(time.time() - inicio, 1)

    resultados[nombre] = {
        "filas_totales": total_filas,
        "job_link_unicos": unicos,
        "job_link_duplicados": duplicados,
        "nulos_por_columna": {col: int(n) for col, n in nulos.items()},
        "segundos_de_lectura": segundos,
    }

    print(f"  Filas totales:        {total_filas:,}")
    print(f"  job_link únicos:      {unicos:,}")
    print(f"  job_link duplicados:  {duplicados:,}")
    print(f"  Tiempo:               {segundos} s")

    # Liberamos memoria antes del siguiente archivo
    del links, todos_links

# Guardamos los resultados en un archivo JSON (UTF-8, con tildes correctas)
with 	open(REPORTES / "auditoria_conteos.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, indent=2, ensure_ascii=False)

print("\nListo. Resultados guardados en auditoria_conteos.json")