"""
12 - Auditoría del dataset EMSCAD para Fraud Shield (Catalina)

Dataset: "Real or Fake: Fake Job Posting Prediction" (EMSCAD), Kaggle,
archivo fake_job_postings.csv en data/raw/ (no va a Git).

Revisa, SIN modificar los datos ni el modelo:
  1. Volumen y desbalance de clases (fraudulent = 0 / 1).
  2. Valores nulos y vacíos por columna, en total y por clase.
  3. Duplicados: filas repetidas, textos repetidos y textos repetidos con
     etiquetas distintas (contradicciones).
  4. Posibles fugas de información y sesgos: job_id, marcadores anonimizados
     (#URL_...#, #EMAIL_...#, #PHONE_...#), campos que no existirán en la app,
     concentración geográfica.
  5. Calidad del texto (longitud, vacíos, HTML) por clase.
  6. Compatibilidad con los datos de LinkedIn y con lo que escribe el usuario.

Salidas:
  reports/auditoria_fraude.md
  reports/auditoria_fraude.json
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
RUTA = RAIZ / "data" / "raw" / "fake_job_postings.csv"
REPORTES = RAIZ / "reports"

TEXTO = ["company_profile", "description", "requirements", "benefits"]
CATEGORICAS = ["employment_type", "required_experience", "required_education", "industry", "function"]
BINARIAS = ["telecommuting", "has_company_logo", "has_questions"]
# Campos que una oferta de LinkedIn (o el texto que pega el usuario) sí tendría
DISPONIBLES_EN_APP = ["title", "location", "description", "requirements", "benefits", "company_profile"]

if not RUTA.exists():
    raise SystemExit(f"No encuentro {RUTA}. Descarga fake_job_postings.csv de Kaggle y ponlo en data/raw/.")

df = pd.read_csv(RUTA, keep_default_na=False, dtype=str)
y = df["fraudulent"].astype(int)
n, n_fraude = len(df), int(y.sum())
pct = lambda a, b: round(a / b * 100, 2) if b else 0.0
es_vacio = lambda s: s.str.strip().isin(["", "nan", "NaN", "None"])

# ---------------------------------------------------------------- 1. Clases
clases = {
    "total": n, "reales": n - n_fraude, "fraudulentas": n_fraude,
    "pct_fraudulentas": pct(n_fraude, n),
    "proporcion": f"1 fraudulenta por cada {round((n - n_fraude) / max(n_fraude, 1), 1)} reales",
    "accuracy_de_un_modelo_que_siempre_dice_real": pct(n - n_fraude, n),
}

# ---------------------------------------------------------------- 2. Nulos
nulos = []
for c in [col for col in df.columns if col not in ("job_id", "fraudulent")]:
    v = es_vacio(df[c])
    nulos.append({"columna": c, "vacios": int(v.sum()), "pct_total": pct(v.sum(), n),
                  "pct_en_reales": pct((v & (y == 0)).sum(), n - n_fraude),
                  "pct_en_fraudulentas": pct((v & (y == 1)).sum(), n_fraude)})
nulos = pd.DataFrame(nulos).sort_values("pct_total", ascending=False)
nulos["diferencia_puntos"] = (nulos["pct_en_fraudulentas"] - nulos["pct_en_reales"]).round(2)

# ---------------------------------------------------------------- 3. Duplicados
sin_id = df.drop(columns=["job_id"])
filas_dup = int(sin_id.duplicated().sum())


def normalizar(s):
    s = s.str.lower().str.replace(r"#(url|email|phone)_[0-9a-f]+#", " ", regex=True)
    return s.str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip()


clave = normalizar(df["title"] + " " + df["description"] + " " + df["requirements"])
df["_grupo"] = pd.util.hash_pandas_object(clave, index=False)
tam = df.groupby("_grupo")["_grupo"].transform("size")
etiquetas_por_grupo = df.groupby("_grupo")["fraudulent"].nunique()
contradicciones = int((etiquetas_por_grupo > 1).sum())
duplicados = {
    "filas_identicas_sin_job_id": filas_dup,
    "ofertas_con_texto_repetido": int((tam > 1).sum()),
    "grupos_de_texto_repetido": int((df.groupby("_grupo").size() > 1).sum()),
    "textos_unicos": int(df["_grupo"].nunique()),
    "repetidas_entre_fraudulentas": int(((tam > 1) & (y == 1)).sum()),
    "grupos_con_etiquetas_contradictorias": contradicciones,
    "descripcion_identica_solo_descripcion": int(normalizar(df["description"]).duplicated().sum()),
}

# ---------------------------------------------------------------- 4. Fugas y sesgos
fugas = {}
# job_id: ¿la tasa de fraude cambia según la posición del ID?
ids = pd.to_numeric(df["job_id"], errors="coerce")
decil = pd.qcut(ids.rank(method="first"), 10, labels=False)
tasa_decil = (y.groupby(decil).mean() * 100).round(2)
fugas["tasa_fraude_por_decil_de_job_id"] = tasa_decil.tolist()
fugas["job_id_variacion_max_puntos"] = round(float(tasa_decil.max() - tasa_decil.min()), 2)

# Marcadores anonimizados del dataset original
texto_total = df[TEXTO].agg(" ".join, axis=1)
marcadores = {}
for m in ["URL", "EMAIL", "PHONE"]:
    tiene = texto_total.str.contains(rf"#{m}_[0-9a-f]+#", regex=True)
    marcadores[m] = {"pct_en_reales": pct((tiene & (y == 0)).sum(), n - n_fraude),
                     "pct_en_fraudulentas": pct((tiene & (y == 1)).sum(), n_fraude)}
fugas["marcadores_anonimizados"] = marcadores

# Binarias: tasa de fraude según el valor
binarias = {}
for c in BINARIAS:
    t = (y.groupby(df[c]).mean() * 100).round(2).to_dict()
    binarias[c] = {"tasa_fraude_si_1": t.get("1", 0.0), "tasa_fraude_si_0": t.get("0", 0.0),
                   "pct_ofertas_con_1": pct((df[c] == "1").sum(), n)}
fugas["campos_binarios"] = binarias

# Ubicación: ¿pocas ciudades concentran el fraude?
ciudad = df["location"].str.split(",").map(lambda p: ", ".join(x.strip() for x in p[:3]) if p else "")
por_ciudad = (pd.DataFrame({"ciudad": ciudad, "y": y}).groupby("ciudad")["y"]
              .agg(ofertas="size", fraudulentas="sum"))
por_ciudad = por_ciudad[por_ciudad["ofertas"] >= 30]
por_ciudad["tasa_fraude"] = (por_ciudad["fraudulentas"] / por_ciudad["ofertas"] * 100).round(2)
top_ciudades = por_ciudad.sort_values("fraudulentas", ascending=False).head(8)
fugas["ciudades_con_mas_fraude"] = top_ciudades.reset_index().to_dict("records")
fugas["pct_del_fraude_en_las_3_ciudades_principales"] = pct(
    top_ciudades["fraudulentas"].head(3).sum(), n_fraude)
pais = df["location"].str.split(",").str[0].str.strip()
fugas["pct_ofertas_en_us"] = pct((pais == "US").sum(), n)

# ---------------------------------------------------------------- 5. Calidad del texto
palabras = df["description"].str.count(r"\S+")
calidad = {
    "palabras_descripcion_mediana_reales": int(palabras[y == 0].median()),
    "palabras_descripcion_mediana_fraudulentas": int(palabras[y == 1].median()),
    "descripcion_menos_de_20_palabras": int((palabras < 20).sum()),
    "con_html": int(texto_total.str.contains(r"<\s*/?\s*[a-zA-Z][^>]*>", regex=True).sum()),
    "con_mas_de_20pct_no_ascii": int((df["description"].str.count(r"[^\x00-\x7F]")
                                      / df["description"].str.len().clip(lower=1) > 0.2).sum()),
}
for c in CATEGORICAS:
    calidad[f"valores_distintos_{c}"] = int(df[c].nunique())

resultado = {"dataset": "EMSCAD - fake_job_postings.csv (Kaggle)", "1_clases": clases,
             "2_nulos": nulos.to_dict("records"), "3_duplicados": duplicados,
             "4_fugas_y_sesgos": fugas, "5_calidad_texto": calidad,
             "6_campos_disponibles_en_la_app": DISPONIBLES_EN_APP}
(REPORTES / "auditoria_fraude.json").write_text(
    json.dumps(resultado, indent=2, ensure_ascii=False, default=lambda x: x.item()), encoding="utf-8")


# ---------------------------------------------------------------- Informe
def tabla(filas, columnas, nombres):
    out = ["| " + " | ".join(nombres) + " |", "|" + "---|" * len(nombres)]
    out += ["| " + " | ".join(str(f[c]) for c in columnas) + " |" for f in filas]
    return out


grandes_dif = nulos[nulos["diferencia_puntos"].abs() >= 10]
md = ["# Auditoría del dataset EMSCAD — Fraud Shield", "",
      "Generado por `src/data_pipeline/12_auditoria_fraude.py`. No se modificaron los datos, "
      "el modelo ni las particiones.", "",
      "**Dataset:** *Real or Fake: Fake Job Posting Prediction* (EMSCAD), Kaggle — `data/raw/fake_job_postings.csv`.", "",
      "## 1. Clases y desbalance", "",
      f"| Total | Reales | Fraudulentas | % fraudulentas |", "|---|---|---|---|",
      f"| {n:,} | {n - n_fraude:,} | {n_fraude:,} | {clases['pct_fraudulentas']} % |".replace(",", "."), "",
      f"Hay **{clases['proporcion']}**. Un modelo que siempre diga «real» tendría "
      f"**{clases['accuracy_de_un_modelo_que_siempre_dice_real']} % de accuracy** sin detectar ningún fraude, "
      "así que la accuracy **no sirve** para evaluar este modelo.", "",
      "## 2. Valores nulos o vacíos", ""]
md += tabla(nulos.to_dict("records"),
            ["columna", "pct_total", "pct_en_reales", "pct_en_fraudulentas", "diferencia_puntos"],
            ["Columna", "% vacíos", "% en reales", "% en fraudulentas", "Diferencia (puntos)"])
md += ["", "Columnas cuya ausencia es muy distinta entre clases (≥ 10 puntos): "
       + (", ".join(f"`{c}`" for c in grandes_dif["columna"]) or "ninguna") + ". "
       "Que falte un campo ya es una señal para el modelo; si se rellena sin cuidado, esa señal se pierde, "
       "y si el modelo depende demasiado de ella, puede fallar con ofertas de otra fuente.", "",
       "## 3. Duplicados", ""]
md += tabla([{"k": k.replace("_", " "), "v": f"{v:,}".replace(",", ".")} for k, v in duplicados.items()],
            ["k", "v"], ["Medida", "Valor"])
md += ["", "Si una misma oferta (o casi la misma) queda en entrenamiento y en prueba, la métrica sale "
       "inflada (fuga de datos), igual que en el corpus de LinkedIn. "
       + (f"Hay **{contradicciones}** grupos de texto repetido con etiquetas distintas: hay que revisarlos o "
          "excluirlos." if contradicciones else "No hay textos repetidos con etiquetas contradictorias."), "",
       "## 4. Posibles fugas de información y sesgos", "",
       f"**job_id.** Tasa de fraude por décil de `job_id` (%): {fugas['tasa_fraude_por_decil_de_job_id']}. "
       f"Variación máxima: {fugas['job_id_variacion_max_puntos']} puntos. "
       "`job_id` es un identificador: **no debe usarse como variable**, aunque parezca predictivo.", "",
       "**Marcadores anonimizados** (`#URL_…#`, `#EMAIL_…#`, `#PHONE_…#`):", ""]
md += tabla([{"m": k, **v} for k, v in marcadores.items()], ["m", "pct_en_reales", "pct_en_fraudulentas"],
            ["Marcador", "% en reales", "% en fraudulentas"])
md += ["", "Son tokens del dataset original y **no aparecen en ofertas reales**. Antes de entrenar hay que "
       "convertirlos a los mismos marcadores del proyecto (`[URL]`, `[EMAIL]`; teléfono → `[PHONE]`), para que "
       "el modelo vea lo mismo que verá en producción.", "",
       "**Campos binarios** (tasa de fraude según el valor):", ""]
md += tabla([{"c": k, **v} for k, v in binarias.items()],
            ["c", "tasa_fraude_si_1", "tasa_fraude_si_0", "pct_ofertas_con_1"],
            ["Campo", "% fraude si = 1", "% fraude si = 0", "% de ofertas con 1"])
md += ["", "`has_company_logo` y `has_questions` vienen de la plataforma original y **no existen** en el texto que "
       "pega un usuario ni en el corpus de LinkedIn. Si el modelo los usa, funcionará bien en la prueba pero no en "
       "la app (diferencia entre entrenamiento y uso real).", "",
       f"**Ubicación.** El {fugas['pct_ofertas_en_us']} % de las ofertas son de EE. UU. Las 3 ciudades con más "
       f"fraude concentran el **{fugas['pct_del_fraude_en_las_3_ciudades_principales']} %** de todas las "
       "fraudulentas:", ""]
md += tabla(fugas["ciudades_con_mas_fraude"], ["ciudad", "ofertas", "fraudulentas", "tasa_fraude"],
            ["Ciudad", "Ofertas", "Fraudulentas", "% fraude"])
md += ["", "Si se usa la ubicación, el modelo puede aprender «ciudad X = fraude», que es un sesgo, no una señal "
       "de fraude.", "",
       "## 5. Calidad del texto", ""]
md += tabla([{"k": k.replace("_", " "), "v": v} for k, v in calidad.items()], ["k", "v"], ["Medida", "Valor"])
md += ["", "## 6. Recomendaciones para preparar y evaluar el modelo", "",
       "**Preparación**",
       "1. Usar solo campos que existirán en la app: título y texto (descripción, requisitos, beneficios, perfil de "
       "la empresa). **No usar** `job_id`, `has_company_logo`, `has_questions` ni, en lo posible, la ubicación.",
       "2. Reemplazar `#URL_…#`, `#EMAIL_…#` y `#PHONE_…#` por los marcadores del proyecto (`[URL]`, `[EMAIL]`, "
       "`[PHONE]`), con la misma limpieza del corpus de LinkedIn (sin borrar C++, C#, .NET).",
       "3. Tratar los campos vacíos de forma explícita (por ejemplo, el texto «sin perfil de empresa») en vez de "
       "eliminar las filas.",
       "4. Agrupar los textos repetidos **antes** de dividir y revisar o excluir los grupos con etiquetas "
       "contradictorias.", "",
       "**División**",
       "5. Entrenamiento / validación / prueba **estratificada por clase y agrupada por texto**, con semilla 42, "
       "para que cada partición tenga la misma proporción de fraude y ningún texto quede en dos particiones.", "",
       "**Entrenamiento**",
       "6. Pesos por clase (o sobremuestreo **solo** del entrenamiento) para compensar el desbalance.",
       "7. Comparar contra un modelo base (TF-IDF + regresión logística).", "",
       "**Evaluación**",
       "8. Métricas principales: **recall de la clase fraude**, **precisión de la clase fraude**, **F1 de fraude** y "
       "**PR-AUC**. Reportar también la matriz de confusión. **No usar accuracy** como métrica principal.",
       "9. Elegir el umbral con el conjunto de **validación** y usar la prueba una sola vez.",
       "10. Revisar a mano falsos positivos y falsos negativos.", "",
       "**Presentación en la app**",
       "11. Mostrarlo como **riesgo estimado**, no como prueba de fraude (contrato de datos).",
       "12. Advertir el **cambio de dominio**: EMSCAD tiene ofertas de 2012–2014 y de otra plataforma; el "
       "rendimiento en ofertas de LinkedIn 2024 puede ser menor que en la prueba."]
(REPORTES / "auditoria_fraude.md").write_text("\n".join(md), encoding="utf-8")

print(json.dumps({"clases": clases, "duplicados": duplicados,
                  "nulos_diferencia_10_o_mas": grandes_dif[["columna", "pct_en_reales",
                                                            "pct_en_fraudulentas"]].to_dict("records"),
                  "campos_binarios": binarias,
                  "fraude_en_3_ciudades_principales_pct": fugas["pct_del_fraude_en_las_3_ciudades_principales"]},
                 indent=2, ensure_ascii=False, default=lambda x: x.item()))
