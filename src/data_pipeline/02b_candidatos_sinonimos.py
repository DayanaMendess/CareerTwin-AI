
import re
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
REPORTES = RAIZ / "reports"

top = pd.read_csv(REPORTES / "catalogo_habilidades_top1000.csv")


def clave_parecido(habilidad: str) -> str:
    """Quita lo que suele variar entre dos formas de la misma habilidad."""
    h = habilidad.lower()
    h = re.sub(r"\bskills?\b", "", h)   # "organizational skills" -> "organizational"
    h = h.replace("&", "and")           # "health & safety" -> "health and safety"
    h = re.sub(r"[\s\-_/]+", "", h)     # sin espacios, guiones ni barras
    return h


top["clave"] = top["habilidad"].map(clave_parecido)

# Grupos con más de una habilidad bajo la misma clave = candidatos
candidatos = (top.groupby("clave")
                 .filter(lambda g: len(g) > 1)
                 .sort_values(["clave", "ofertas"], ascending=[True, False]))

# Sugerencia: la forma más frecuente del grupo
candidatos["sugerencia_canonica"] = (candidatos.groupby("clave")["habilidad"]
                                               .transform("first"))

columnas = ["clave", "habilidad", "ofertas", "sugerencia_canonica", "variantes_ejemplo"]
candidatos[columnas].to_csv(REPORTES / "candidatos_sinonimos.csv",
                            index=False, encoding="utf-8-sig")

print(f"Grupos candidatos: {candidatos['clave'].nunique()}")
print(f"Habilidades involucradas: {len(candidatos)}\n")
for clave, grupo in candidatos.groupby("clave", sort=False):
    formas = " | ".join(f"{h} ({o:,})" for h, o in zip(grupo["habilidad"], grupo["ofertas"]))
    print(f"  {formas}")