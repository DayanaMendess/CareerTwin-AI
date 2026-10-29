
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
REPORTES = RAIZ / "reports"
N_PILOTO = 100
VALIDAS = {"tecnica", "blanda"}
UMBRAL_MUY_FRECUENTE = 20.0  # % de ofertas; por encima, la etiqueta es poco informativa

revisada = pd.read_csv(REPORTES / "clasificacion_habilidades_revisada.csv",
                       keep_default_na=False)
catalogo = pd.read_csv(REPORTES / "catalogo_habilidades_top1000.csv",
                       keep_default_na=False)

# Categoría de la revisión manual + conteos actualizados del catálogo.
# Las habilidades que se unieron como sinónimos ya no están en el catálogo
# y quedan fuera automáticamente.
datos = revisada[["habilidad", "categoria_final", "nota"]].merge(
    catalogo[["habilidad", "ofertas", "porcentaje_ofertas"]], on="habilidad", how="inner")

desaparecidas = sorted(set(revisada["habilidad"]) - set(datos["habilidad"]))

validas = (datos[datos["categoria_final"].isin(VALIDAS)]
           .sort_values("ofertas", ascending=False)
           .reset_index(drop=True))

if len(validas) < N_PILOTO:
    raise SystemExit(f"Solo hay {len(validas)} habilidades válidas revisadas; "
                     f"se necesitan {N_PILOTO}. Revisa más filas del catálogo.")

piloto = validas.head(N_PILOTO).copy()
piloto.insert(0, "indice", range(N_PILOTO))  # posición de la etiqueta en la salida de la red

muy_frecuentes = piloto[piloto["porcentaje_ofertas"] > UMBRAL_MUY_FRECUENTE]

# ---------- Guardar ----------
piloto.to_csv(REPORTES / "vocabulario_piloto.csv", index=False, encoding="utf-8-sig")

vocab = {
    "version": "piloto-v1",
    "n_etiquetas": N_PILOTO,
    "criterio": ("Habilidades clasificadas como tecnica o blanda en la revisión manual, "
                 "ordenadas por número de ofertas que las piden. Se excluyen requisitos "
                 "(títulos, licencias, experiencia) y elementos descartados "
                 "(beneficios, condiciones del puesto, términos genéricos)."),
    "fuente_conteos": "reports/catalogo_habilidades_top1000.csv",
    "fuente_categorias": "reports/clasificacion_habilidades_revisada.csv",
    "normalizacion": "src/data_pipeline/habilidades_utils.py",
    "etiquetas": piloto["habilidad"].tolist(),
    "categoria": dict(zip(piloto["habilidad"], piloto["categoria_final"])),
    "ofertas": dict(zip(piloto["habilidad"], piloto["ofertas"].astype(int))),
    "advertencia_muy_frecuentes": muy_frecuentes["habilidad"].tolist(),
}
with open(REPORTES / "skills_vocab_piloto.json", "w", encoding="utf-8") as f:
    json.dump(vocab, f, indent=2, ensure_ascii=False)

# ---------- Resumen ----------
print(f"Habilidades revisadas: {len(revisada)}")
print(f"Ya no existen en el catálogo (unidas como sinónimos): {desaparecidas}")
print(f"Válidas disponibles: {len(validas)}")
print(f"\nVocabulario piloto: {N_PILOTO} etiquetas")
print(piloto["categoria_final"].value_counts().to_string())
print(f"\nMás frecuente:  {piloto.iloc[0]['habilidad']} ({piloto.iloc[0]['porcentaje_ofertas']}% de ofertas)")
print(f"Menos frecuente: {piloto.iloc[-1]['habilidad']} ({piloto.iloc[-1]['porcentaje_ofertas']}% de ofertas)")
print(f"\nEtiquetas en más del {UMBRAL_MUY_FRECUENTE:.0f}% de las ofertas:")
for _, r in muy_frecuentes.iterrows():
    print(f"   {r['habilidad']}: {r['porcentaje_ofertas']}%")
print("\nLas 100 etiquetas:")
print(", ".join(piloto["habilidad"]))