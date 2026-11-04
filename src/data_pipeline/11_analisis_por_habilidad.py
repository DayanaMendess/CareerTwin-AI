"""
11 - Análisis del rendimiento del modelo por habilidad (Catalina)

Lee reports/metricas_por_habilidad.csv (generado por Sofia con las 7.500 ofertas
de prueba y el umbral 0,20) y explica, desde los datos, por qué a unas
habilidades les va bien y a otras mal: frecuencia, desbalance, tipo de habilidad
y ruido de las etiquetas.

NO cambia el modelo ni usa el conjunto de prueba para ajustar nada.

Salidas:
  reports/analisis_por_habilidad.md
  reports/analisis_por_habilidad.json
  reports/figuras/fig_f1_vs_frecuencia.png
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
REPORTES = RAIZ / "reports"
FIG = REPORTES / "figuras"
FIG.mkdir(parents=True, exist_ok=True)

AZUL, NARANJA = "#2a78d6", "#eb6834"
FONDO, TEXTO, TEXTO2, REJILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0"

m = pd.read_csv(REPORTES / "metricas_por_habilidad.csv")
m["sobreprediccion"] = (m["predicciones_positivas"] / m["ejemplos_test"]).round(2)
m["rango_frecuencia"] = pd.cut(m["frecuencia_test_pct"], [0, 2, 4, 8, 100],
                               labels=["menos de 2 %", "2 a 4 %", "4 a 8 %", "más de 8 %"])

# ---------------------------------------------------------------- Cálculos
tp, fp, fn = m["verdaderos_positivos"].sum(), m["falsos_positivos"].sum(), m["falsos_negativos"].sum()
micro = round(float(2 * tp / (2 * tp + fp + fn)), 4)
macro = round(float(m["f1"].mean()), 4)

por_rango = (m.groupby("rango_frecuencia", observed=True)
             .agg(habilidades=("f1", "size"), f1_promedio=("f1", "mean"),
                  recall_promedio=("recall", "mean"), f1_cero=("f1", lambda x: int((x == 0).sum())))
             .round(3).reset_index())
por_categoria = (m.groupby("categoria")
                 .agg(habilidades=("f1", "size"), f1_promedio=("f1", "mean"),
                      f1_cero=("f1", lambda x: int((x == 0).sum())))
                 .round(3).reset_index())
spearman = round(float(m[["frecuencia_test_pct", "f1"]].corr("spearman").iloc[0, 1]), 3)

nunca = m[m["predicciones_positivas"] == 0]["habilidad"].tolist()
sobre = m[m["sobreprediccion"] >= 2].sort_values("sobreprediccion", ascending=False)
raras_buenas = m[(m["frecuencia_test_pct"] < 2) & (m["f1"] >= 0.2)].sort_values("f1", ascending=False)
comunes_malas = m[(m["frecuencia_test_pct"] >= 3) & (m["f1"] < 0.05)].sort_values("frecuencia_test_pct",
                                                                                  ascending=False)

# Soporte de etiquetas (unión de copias, día 4): ¿cuántas etiquetas de prueba
# vienen de UNA sola copia? Indica ruido. Solo si existe el archivo.
ruido = None
ruta_datos = RAIZ / "data" / "processed" / "datos_entrenamiento.parquet"
if ruta_datos.exists():
    d = pd.read_parquet(ruta_datos, columns=["particion", "etiquetas", "soporte_etiquetas", "n_copias"])
    d = d[(d["particion"] == "test") & (d["n_copias"] > 1)].explode(["etiquetas", "soporte_etiquetas"])
    d = d.dropna(subset=["etiquetas"])
    d["debil"] = d["soporte_etiquetas"].astype(int) < d["n_copias"] / 2
    ruido = d.groupby("etiquetas")["debil"].mean().rename("pct_etiquetas_debiles")
    m = m.merge((ruido * 100).round(1), left_on="habilidad", right_index=True, how="left")

resultado = {
    "fuente": "reports/metricas_por_habilidad.csv (Sofia, 7.500 ofertas de prueba, umbral 0,20)",
    "micro_f1_recalculado": micro,
    "macro_f1": macro,
    "habilidades_con_f1_cero": int((m["f1"] == 0).sum()),
    "habilidades_nunca_predichas": nunca,
    "correlacion_spearman_frecuencia_f1": spearman,
    "por_rango_de_frecuencia": por_rango.astype({"rango_frecuencia": str}).to_dict("records"),
    "por_categoria": por_categoria.to_dict("records"),
    "sobrepredichas_x2_o_mas": sobre[["habilidad", "sobreprediccion", "precision", "recall"]].to_dict("records"),
    "poco_frecuentes_pero_bien": raras_buenas[["habilidad", "frecuencia_test_pct", "f1"]].to_dict("records"),
    "frecuentes_pero_mal": comunes_malas[["habilidad", "frecuencia_test_pct", "f1",
                                          "predicciones_positivas"]].to_dict("records"),
}
(REPORTES / "analisis_por_habilidad.json").write_text(
    json.dumps(resultado, indent=2, ensure_ascii=False, default=float), encoding="utf-8")

# ---------------------------------------------------------------- Figura
fig, ax = plt.subplots(figsize=(8, 5), facecolor=FONDO)
ax.set_facecolor(FONDO)
for cat, color, nombre in [("tecnica", AZUL, "Técnica"), ("blanda", NARANJA, "Blanda")]:
    g = m[m["categoria"] == cat]
    ax.scatter(g["frecuencia_test_pct"], g["f1"], s=36, color=color, label=nombre,
               edgecolor=FONDO, linewidth=1.5, zorder=3)
for _, r in m[m["habilidad"].isin(["communication", "customer service", "nursing", "accounting",
                                   "financial reporting"])].iterrows():
    ax.annotate(r["habilidad"], (r["frecuencia_test_pct"], r["f1"]), xytext=(5, 4),
                textcoords="offset points", fontsize=8, color=TEXTO2)
ax.annotate(f"{int((m['f1'] == 0).sum())} habilidades con F1 = 0", (1.05, 0.0), xytext=(0, 10),
            textcoords="offset points", fontsize=8, color=TEXTO2)
ax.set_xscale("log")
ax.set_xticks([1, 2, 5, 10, 20, 40], ["1 %", "2 %", "5 %", "10 %", "20 %", "40 %"])
ax.set_ylim(-0.03, 0.7)
ax.set_title("F1 por habilidad frente a su frecuencia en la prueba", loc="left", fontsize=12, color=TEXTO, pad=12)
ax.set_xlabel("% de ofertas de prueba que tienen la habilidad (escala logarítmica)", color=TEXTO2, fontsize=9)
ax.set_ylabel("F1 (umbral 0,20)", color=TEXTO2, fontsize=9)
ax.tick_params(colors=TEXTO2, labelsize=9, length=0)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
for s in ["left", "bottom"]:
    ax.spines[s].set_color(REJILLA)
ax.grid(color=REJILLA, linewidth=0.8)
ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=9, ncol=2, loc="lower right", bbox_to_anchor=(1, 1.0))
fig.tight_layout()
fig.savefig(FIG / "fig_f1_vs_frecuencia.png", dpi=200, facecolor=FONDO)
plt.close(fig)

# ---------------------------------------------------------------- Informe
def fila(r, cols):
    return "| " + " | ".join(str(r[c]) for c in cols) + " |"

md = ["# Análisis del rendimiento por habilidad — CareerTwin AI", "",
      "Generado por `src/data_pipeline/11_analisis_por_habilidad.py` a partir de las métricas de Sofia "
      "(7.500 ofertas de prueba, umbral 0,20). No se ajustó nada con el conjunto de prueba.", "",
      f"**Micro-F1:** {micro} · **Macro-F1:** {macro} · **Habilidades con F1 = 0:** {resultado['habilidades_con_f1_cero']} "
      f"· **Nunca predichas:** {len(nunca)}", "",
      "## 1. La frecuencia explica gran parte del resultado", "",
      f"Correlación de Spearman entre frecuencia y F1: **{spearman}**.", "",
      "| Frecuencia en prueba | Habilidades | F1 promedio | Recall promedio | Con F1 = 0 |", "|---|---|---|---|---|"]
md += [fila(r, ["rango_frecuencia", "habilidades", "f1_promedio", "recall_promedio", "f1_cero"])
       for _, r in por_rango.iterrows()]
md += ["", "Las 11 habilidades que aparecen en más del 8 % de las ofertas tienen F1 promedio de "
       f"{por_rango.iloc[-1]['f1_promedio']}; las de menos del 2 % apenas {por_rango.iloc[0]['f1_promedio']}. "
       "Con pocos ejemplos positivos y un umbral único de 0,20, la red casi nunca supera el umbral en las raras.", "",
       "## 2. Las más frecuentes se sobrepredicen", "",
       "| Habilidad | Predicciones / casos reales | Precisión | Recall |", "|---|---|---|---|"]
md += [fila(r, ["habilidad", "sobreprediccion", "precision", "recall"]) for _, r in sobre.iterrows()]
md += ["", "La red predice estas habilidades unas dos veces más de lo que aparecen. Es el efecto del desbalance "
       "que advertimos en la validación de etiquetas (día 5): communication está en el 42 % de las ofertas.", "",
       "## 3. Lo específico se aprende mejor que lo genérico", "",
       "**Poco frecuentes pero con buen F1** (vocabulario propio y claro):", "",
       "| Habilidad | % en prueba | F1 |", "|---|---|---|"]
md += [fila(r, ["habilidad", "frecuencia_test_pct", "f1"]) for _, r in raras_buenas.iterrows()]
md += ["", "**Frecuentes pero con F1 casi nulo** (habilidades genéricas o que el extractor etiquetó de forma inconsistente):", "",
       "| Habilidad | % en prueba | F1 | Veces que la red la predijo |", "|---|---|---|---|"]
md += [fila(r, ["habilidad", "frecuencia_test_pct", "f1", "predicciones_positivas"]) for _, r in comunes_malas.iterrows()]
md += ["", "Habilidades como *financial reporting* o *merchandising* aparecen en pocas ofertas pero con palabras "
       "muy reconocibles, y la red las aprende. En cambio *verbal communication*, *research*, *reporting* u "
       "*organization* aparecen en el 3–5 % de las ofertas y la red casi nunca acierta: son genéricas, "
       "aparecen en textos de cualquier oficio y, como mostró la verificación del día 3 (Jaccard 0,265 entre "
       "copias del mismo texto), el extractor las incluye o no de forma poco consistente.", "",
       "## 4. Técnicas frente a blandas", "", "| Categoría | Habilidades | F1 promedio | Con F1 = 0 |", "|---|---|---|---|"]
md += [fila(r, ["categoria", "habilidades", "f1_promedio", "f1_cero"]) for _, r in por_categoria.iterrows()]
md += ["", "Las blandas rinden peor: son más vagas y se superponen entre sí (*communication*, *verbal communication*, "
       "*written communication*).", "",
       "## 5. Nunca predichas (" + str(len(nunca)) + ")", "", ", ".join(nunca), "",
       "## 6. Recomendaciones", "",
       "1. **Umbral por habilidad** elegido con el conjunto de **validación** (no con el de prueba).",
       "2. **Pesos por clase** en la pérdida, para que las habilidades raras cuenten más.",
       "3. **Leer más texto:** la red usa 256 tokens y la mediana de las descripciones es de 490 palabras "
       "(auditoría); muchas habilidades aparecen al final, en *Requirements*.",
       "4. **Usar el detector de texto** (`detector_habilidades.py`) como complemento: cubre las habilidades "
       "que la red nunca predice cuando el usuario las escribe explícitamente.",
       "5. **Revisar el vocabulario v2:** unir o quitar etiquetas genéricas que se solapan "
       "(*verbal/written communication*, *team player*, *organization*).", "",
       "## 7. Figura", "", "- `reports/figuras/fig_f1_vs_frecuencia.png`: F1 de cada habilidad frente a su frecuencia."]
(REPORTES / "analisis_por_habilidad.md").write_text("\n".join(md), encoding="utf-8")

print(json.dumps({k: resultado[k] for k in ["micro_f1_recalculado", "macro_f1", "habilidades_con_f1_cero",
                                            "correlacion_spearman_frecuencia_f1", "por_rango_de_frecuencia",
                                            "por_categoria"]}, indent=2, ensure_ascii=False, default=float))
