
import re
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
REPORTES = RAIZ / "reports"
N_REVISAR = 300

# Patrones de palabras para cada categoría
PATRON_DESCARTAR = re.compile(
    r"\b(401k|401\(k\)|health insurance|dental insurance|vision insurance|"
    r"life insurance|paid time off|pto|employee discount|benefits package)\b")

PATRON_REQUISITO = re.compile(
    r"\b(degree|diploma|ged|high school|license|licensure|certification|"
    r"certified|certificate|cpr|bls|acls|first aid)\b")

PATRON_BLANDA = re.compile(
    r"(communication|teamwork|team player|leadership|problem solving|"
    r"time management|attention to detail|interpersonal|collaboration|"
    r"organizational skills|multitasking|adaptability|flexibility|"
    r"critical thinking|decision making|listening|negotiation|creativity|"
    r"motivated|detail oriented|work ethic|professionalism|reliability|"
    r"dependab|empathy|attitude|integrity|initiative|punctual|patience|"
    r"conflict resolution|emotional intelligence|self starter|prioritization|"
    r"analytical skills|customer focus)")


def sugerir_categoria(habilidad: str) -> str:
    """El orden importa: primero lo que se descarta, luego requisitos, luego blandas."""
    if PATRON_DESCARTAR.search(habilidad):
        return "descartar"
    if PATRON_REQUISITO.search(habilidad):
        return "requisito"
    if PATRON_BLANDA.search(habilidad):
        return "blanda"
    return "tecnica"


top = pd.read_csv(REPORTES / "catalogo_habilidades_top1000.csv").head(N_REVISAR).copy()
top.insert(0, "posicion", range(1, len(top) + 1))
top["categoria_sugerida"] = top["habilidad"].map(sugerir_categoria)
top["categoria_final"] = top["categoria_sugerida"]  # tú la corriges donde haga falta
top["nota"] = ""                                    # para explicar los cambios

columnas = ["posicion", "habilidad", "ofertas", "porcentaje_ofertas",
            "categoria_sugerida", "categoria_final", "nota", "variantes_ejemplo"]
top[columnas].to_csv(REPORTES / "clasificacion_top300_sugerida.csv",
                     index=False, encoding="utf-8-sig")

print("Resumen de la sugerencia automática:")
print(top["categoria_sugerida"].value_counts().to_string())

for categoria in ["requisito", "descartar", "blanda", "tecnica"]:
    grupo = top[top["categoria_sugerida"] == categoria]
    print(f"\n--- {categoria.upper()} ({len(grupo)}) ---")
    print(", ".join(grupo["habilidad"].head(40)))