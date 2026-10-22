import pandas as pd
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]  # la carpeta CareerTwin-AI
RUTA = RAIZ / "data" / "raw" / "job_skills.csv"

# keep_default_na=False -> pandas NO convierte textos como "NA" en nulos
df = pd.read_csv(RUTA, usecols=["job_skills"], keep_default_na=False, dtype=str)
valores = df["job_skills"]

# Celdas realmente vacías (en blanco o solo espacios)
vacias_reales = int((valores.str.strip() == "").sum())

# Textos que pandas convierte en nulo por defecto
TEXTOS_NULOS = ["#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan",
                "1.#IND", "1.#QNAN", "<NA>", "N/A", "NA", "NULL", "NaN",
                "None", "n/a", "nan", "null"]
convertidos = valores[valores.isin(TEXTOS_NULOS)]

print("Celdas realmente vacías:", vacias_reales)
print("Textos que pandas convierte en nulo:", len(convertidos))
print("Suma:", vacias_reales + len(convertidos))
print()
print("Cuáles son:")
print(convertidos.value_counts())