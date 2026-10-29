
import json
import time
from collections import Counter
from pathlib import Path

import pandas as pd

from habilidades_utils import VALORES_VACIOS, separar_habilidades, normalizar_habilidades

RAIZ = Path(__file__).resolve().parents[2]
RUTA_SKILLS = RAIZ / "data" / "raw" / "job_skills.csv"
PROCESADOS = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"
PROCESADOS.mkdir(parents=True, exist_ok=True)
TAMANO_BLOQUE = 50_000

# Términos técnicos que el contrato exige preservar (para verificarlo al final)
TERMINOS_A_VERIFICAR = ["c++", "c#", ".net", "node.js", "python", "sql", "excel"]

inicio = time.time()
ofertas_por_habilidad = Counter()  # en cuántas ofertas aparece cada habilidad normalizada
variantes = Counter()              # pares (normalizada, original): qué se unificó
ofertas_con_habilidades = 0
ofertas_vacias = 0
parentesis_desbalanceados = 0      # señal de que algún corte quedó mal

print("Normalizando habilidades...")
for i, bloque in enumerate(pd.read_csv(RUTA_SKILLS, chunksize=TAMANO_BLOQUE,
                                       keep_default_na=False, dtype=str)):
    texto = bloque["job_skills"].str.strip()

    # Ofertas sin habilidades (vacías o con "None", "N/A", "NA")
    vacias = texto.str.lower().isin(VALORES_VACIOS)
    ofertas_vacias += int(vacias.sum())
    texto = texto[~vacias]

    # "Python, SQL, Excel" -> una fila por habilidad
    original = separar_habilidades(texto)
    original = original[original != ""]
    normal = normalizar_habilidades(original)

    # ¿Quedaron habilidades con "(" sin ")" o al revés?
    parentesis_desbalanceados += int((original.str.count(r"\(")
                                      != original.str.count(r"\)")).sum())

    pares = pd.DataFrame({"oferta": original.index,
                          "original": original.values,
                          "normal": normal.values})
    pares = pares[pares["normal"] != ""]
    ofertas_con_habilidades += pares["oferta"].nunique()

    # Registrar qué variantes originales terminaron en cada habilidad normalizada
    variantes.update(pares.groupby(["normal", "original"]).size().to_dict())

    # Contar ofertas (no menciones): una habilidad repetida en la misma oferta cuenta 1
    unicas = pares.drop_duplicates(["oferta", "normal"])
    ofertas_por_habilidad.update(unicas["normal"].value_counts().to_dict())

    if i % 5 == 0:
        print(f"    bloque {i + 1}: {ofertas_con_habilidades:,} ofertas procesadas")

# ---------- Catálogo ----------
print("Construyendo el catálogo...")
catalogo = pd.DataFrame(ofertas_por_habilidad.items(), columns=["habilidad", "ofertas"])
catalogo["porcentaje_ofertas"] = (catalogo["ofertas"] / ofertas_con_habilidades * 100).round(3)

var = pd.DataFrame([(n, o, c) for (n, o), c in variantes.items()],
                   columns=["habilidad", "variante", "menciones"])
catalogo = catalogo.merge(var.groupby("habilidad").size().rename("n_variantes"),
                          on="habilidad")
catalogo = catalogo.sort_values("ofertas", ascending=False).reset_index(drop=True)

# Ejemplos de variantes solo para las 1.000 más frecuentes (para la revisión manual)
top = catalogo.head(1000).copy()
var_top = (var[var["habilidad"].isin(top["habilidad"])]
           .sort_values("menciones", ascending=False)
           .groupby("habilidad")["variante"]
           .apply(lambda v: " | ".join(v.head(4))))
top["variantes_ejemplo"] = top["habilidad"].map(var_top)

catalogo.to_csv(PROCESADOS / "catalogo_habilidades_completo.csv", index=False, encoding="utf-8")
top.to_csv(REPORTES / "catalogo_habilidades_top1000.csv", index=False, encoding="utf-8-sig")

# ---------- Resumen ----------
originales = int(var["variante"].nunique())
normalizadas = len(catalogo)
resumen = {
    "ofertas_con_habilidades": ofertas_con_habilidades,
    "ofertas_sin_habilidades": ofertas_vacias,
    "habilidades_distintas_originales": originales,
    "habilidades_distintas_normalizadas": normalizadas,
    "reduccion_porcentaje": round((1 - normalizadas / originales) * 100, 1),
    "habilidades_con_parentesis_desbalanceados": parentesis_desbalanceados,
    "en_1_sola_oferta": int((catalogo["ofertas"] == 1).sum()),
    "en_100_o_mas_ofertas": int((catalogo["ofertas"] >= 100).sum()),
    "en_1000_o_mas_ofertas": int((catalogo["ofertas"] >= 1000).sum()),
    "verificacion_terminos_tecnicos": {t: int(ofertas_por_habilidad.get(t, 0))
                                       for t in TERMINOS_A_VERIFICAR},
    "top_30": dict(zip(catalogo["habilidad"].head(30),
                       catalogo["ofertas"].head(30).astype(int))),
    "minutos": round((time.time() - inicio) / 60, 1),
}
with open(REPORTES / "normalizacion_resumen.json", "w", encoding="utf-8") as f:
    json.dump(resumen, f, indent=2, ensure_ascii=False)

print(json.dumps(resumen, indent=2, ensure_ascii=False))