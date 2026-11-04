
import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parents[1]
REPORTES = RAIZ / "reports"

# Cargar resultados reales
historial = pd.read_csv(
    REPORTES / "historial_entrenamiento.csv"
)

metricas = json.loads(
    (REPORTES / "evaluacion_final_skills.json")
    .read_text(encoding="utf-8")
)

epocas = range(1, len(historial) + 1)
mejor_epoca = int(historial["val_loss"].idxmin() + 1)
mejor_loss = float(historial["val_loss"].min())

# Grafica de entrenamiento y validacion
plt.figure(figsize=(10, 5))

plt.plot(
    epocas, historial["loss"],
    label="Entrenamiento", linewidth=2
)
plt.plot(
    epocas, historial["val_loss"],
    label="Validacion", linewidth=2
)
plt.axvline(
    mejor_epoca, linestyle="--",
    label=f"Mejor epoca: {mejor_epoca}"
)

plt.title("CareerTwin AI - Curvas de aprendizaje")
plt.xlabel("Epoca")
plt.ylabel("Binary Crossentropy")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    REPORTES / "curvas_entrenamiento.png",
    dpi=180
)
plt.close()

# Reporte final
reporte = f"""# CareerTwin AI - Informe de entrenamiento

## Configuracion

- Modelo: CNN multietiqueta con Keras
- Entrenamiento: 35.000 ofertas
- Validacion: 7.500 ofertas
- Prueba: 7.500 ofertas
- Etiquetas profesionales: 100
- Epocas ejecutadas: {len(historial)}
- Mejor epoca: {mejor_epoca}
- Mejor perdida de validacion: {mejor_loss:.4f}
- Umbral elegido con validacion: {metricas['umbral_seleccionado_en_validacion']}

## Resultados finales sobre test

| Metrica | Valor |
|---|---:|
| Micro-F1 | {metricas['micro_f1']:.4f} |
| Macro-F1 | {metricas['macro_f1']:.4f} |
| Precision micro | {metricas['precision_micro']:.4f} |
| Recall micro | {metricas['recall_micro']:.4f} |
| Precision@5 | {metricas['precision_at_5']:.4f} |

## Interpretacion

El modelo completo las 30 epocas previstas.
El mejor modelo se selecciono mediante la perdida
de validacion, evitando conservar automaticamente
el modelo de la ultima epoca.

Las metricas finales se calcularon sobre datos de
prueba separados del entrenamiento y la validacion.

El modelo presenta rendimiento limitado,
especialmente en la evaluacion macro, por lo
que requiere mejoras antes de un uso productivo.

## Limitaciones

- Las etiquetas originales pueden estar incompletas.
- Las habilidades estan desbalanceadas.
- El dataset corresponde a ofertas de 2024.
- Las predicciones no garantizan contratacion.
- Big Five no debe interpretarse como una
  medicion de personalidad.

## Archivos

- models/career_skills.keras
- reports/historial_entrenamiento.csv
- reports/evaluacion_final_skills.json
- reports/curvas_entrenamiento.png
"""

ruta = REPORTES / "INFORME_ENTRENAMIENTO_IA.md"
ruta.write_text(reporte, encoding="utf-8")

print("=== REPORTE GENERADO ===")
print("Mejor epoca:", mejor_epoca)
print("Micro-F1:", round(metricas["micro_f1"], 4))
print("Macro-F1:", round(metricas["macro_f1"], 4))
print("Grafica guardada correctamente")
print("Informe:", ruta)
