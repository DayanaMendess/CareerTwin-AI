import os
import pandas as pd

# Dónde están los archivos del dataset
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]  # la carpeta CareerTwin-AI
CARPETA = RAIZ / "data" / "raw"
REPORTES = RAIZ / "reports"
ARCHIVOS = ["linkedin_job_postings.csv", "job_skills.csv", "job_summary.csv"]

# Para que pandas muestre todas las columnas sin cortarlas
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 50)

for nombre in ARCHIVOS:
    ruta = os.path.join(CARPETA, nombre)

    # nrows=3 -> solo lee las primeras 3 filas, no el archivo completo
    muestra = pd.read_csv(ruta, nrows=3)

    print("=" * 90)
    print("ARCHIVO:", nombre)
    print("Número de columnas:", len(muestra.columns))
    print("Columnas:", list(muestra.columns))
    print()
    print(muestra)
    print()