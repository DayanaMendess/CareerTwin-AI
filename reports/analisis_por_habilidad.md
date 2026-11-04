# Análisis del rendimiento por habilidad — CareerTwin AI

Generado por `src/data_pipeline/11_analisis_por_habilidad.py` a partir de las métricas de Sofia (7.500 ofertas de prueba, umbral 0,20). No se ajustó nada con el conjunto de prueba.

**Micro-F1:** 0.3443 · **Macro-F1:** 0.1343 · **Habilidades con F1 = 0:** 38 · **Nunca predichas:** 25

## 1. La frecuencia explica gran parte del resultado

Correlación de Spearman entre frecuencia y F1: **0.478**.

| Frecuencia en prueba | Habilidades | F1 promedio | Recall promedio | Con F1 = 0 |
|---|---|---|---|---|
| menos de 2 % | 35 | 0.071 | 0.061 | 21 |
| 2 a 4 % | 34 | 0.083 | 0.072 | 15 |
| 4 a 8 % | 20 | 0.183 | 0.192 | 2 |
| más de 8 % | 11 | 0.402 | 0.588 | 0 |

Las 11 habilidades que aparecen en más del 8 % de las ofertas tienen F1 promedio de 0.402; las de menos del 2 % apenas 0.071. Con pocos ejemplos positivos y un umbral único de 0,20, la red casi nunca supera el umbral en las raras.

## 2. Las más frecuentes se sobrepredicen

| Habilidad | Predicciones / casos reales | Precisión | Recall |
|---|---|---|---|
| microsoft office | 2.5 | 0.2312 | 0.5791 |
| teamwork | 2.42 | 0.2678 | 0.6493 |
| problem solving | 2.22 | 0.3454 | 0.7663 |
| patient education | 2.12 | 0.1984 | 0.4205 |
| leadership | 2.09 | 0.3015 | 0.6314 |
| communication | 2.02 | 0.4746 | 0.9587 |

La red predice estas habilidades unas dos veces más de lo que aparecen. Es el efecto del desbalance que advertimos en la validación de etiquetas (día 5): communication está en el 42 % de las ofertas.

## 3. Lo específico se aprende mejor que lo genérico

**Poco frecuentes pero con buen F1** (vocabulario propio y claro):

| Habilidad | % en prueba | F1 |
|---|---|---|
| financial reporting | 1.4 | 0.4504 |
| merchandising | 1.19 | 0.3086 |
| retail | 1.29 | 0.2932 |
| financial analysis | 1.87 | 0.2445 |
| food preparation | 1.13 | 0.2385 |
| food safety | 1.48 | 0.2384 |

**Frecuentes pero con F1 casi nulo** (habilidades genéricas o que el extractor etiquetó de forma inconsistente):

| Habilidad | % en prueba | F1 | Veces que la red la predijo |
|---|---|---|---|
| adaptability | 4.91 | 0.0153 | 24 |
| written communication | 4.67 | 0.0057 | 2 |
| verbal communication | 4.05 | 0.0 | 0 |
| organization | 4.01 | 0.0 | 10 |
| microsoft word | 3.85 | 0.0 | 7 |
| quality assurance | 3.68 | 0.0 | 0 |
| research | 3.68 | 0.0 | 1 |
| reporting | 3.67 | 0.0 | 1 |
| presentation skills | 3.65 | 0.0396 | 29 |
| quality control | 3.6 | 0.0 | 10 |
| supervision | 3.43 | 0.0073 | 17 |
| computer skills | 3.08 | 0.0 | 0 |
| safety | 3.04 | 0.0413 | 14 |

Habilidades como *financial reporting* o *merchandising* aparecen en pocas ofertas pero con palabras muy reconocibles, y la red las aprende. En cambio *verbal communication*, *research*, *reporting* u *organization* aparecen en el 3–5 % de las ofertas y la red casi nunca acierta: son genéricas, aparecen en textos de cualquier oficio y, como mostró la verificación del día 3 (Jaccard 0,265 entre copias del mismo texto), el extractor las incluye o no de forma poco consistente.

## 4. Técnicas frente a blandas

| Categoría | Habilidades | F1 promedio | Con F1 = 0 |
|---|---|---|---|
| blanda | 40 | 0.105 | 17 |
| tecnica | 60 | 0.154 | 21 |

Las blandas rinden peor: son más vagas y se superponen entre sí (*communication*, *verbal communication*, *written communication*).

## 5. Nunca predichas (25)

verbal communication, computer skills, quality assurance, planning, mentoring, compliance, professionalism, data entry, initiative, performance management, teaching, maintenance, team player, integrity, regulatory compliance, empathy, ability to work independently, cleaning, networking, writing, innovation, medical terminology, manufacturing, counseling, continuous improvement

## 6. Recomendaciones

1. **Umbral por habilidad** elegido con el conjunto de **validación** (no con el de prueba).
2. **Pesos por clase** en la pérdida, para que las habilidades raras cuenten más.
3. **Leer más texto:** la red usa 256 tokens y la mediana de las descripciones es de 490 palabras (auditoría); muchas habilidades aparecen al final, en *Requirements*.
4. **Usar el detector de texto** (`detector_habilidades.py`) como complemento: cubre las habilidades que la red nunca predice cuando el usuario las escribe explícitamente.
5. **Revisar el vocabulario v2:** unir o quitar etiquetas genéricas que se solapan (*verbal/written communication*, *team player*, *organization*).

## 7. Figura

- `reports/figuras/fig_f1_vs_frecuencia.png`: F1 de cada habilidad frente a su frecuencia.