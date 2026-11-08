# Auditoría del dataset EMSCAD — Fraud Shield

Generado por `src/data_pipeline/12_auditoria_fraude.py`. No se modificaron los datos, el modelo ni las particiones.

**Dataset:** *Real or Fake: Fake Job Posting Prediction* (EMSCAD), Kaggle — `data/raw/fake_job_postings.csv`.

## 1. Clases y desbalance

| Total | Reales | Fraudulentas | % fraudulentas |
|---|---|---|---|
| 17.880 | 17.014 | 866 | 4.84 % |

Hay **1 fraudulenta por cada 19.6 reales**. Un modelo que siempre diga «real» tendría **95.16 % de accuracy** sin detectar ningún fraude, así que la accuracy **no sirve** para evaluar este modelo.

## 2. Valores nulos o vacíos

| Columna | % vacíos | % en reales | % en fraudulentas | Diferencia (puntos) |
|---|---|---|---|---|
| salary_range | 83.96 | 84.45 | 74.25 | -10.2 |
| department | 64.61 | 64.78 | 61.32 | -3.46 |
| required_education | 45.33 | 44.99 | 52.08 | 7.09 |
| benefits | 40.36 | 40.28 | 41.92 | 1.64 |
| required_experience | 39.43 | 38.88 | 50.23 | 11.35 |
| function | 36.1 | 35.96 | 38.91 | 2.95 |
| industry | 27.42 | 27.2 | 31.76 | 4.56 |
| employment_type | 19.41 | 18.98 | 27.83 | 8.85 |
| company_profile | 18.5 | 15.99 | 67.78 | 51.79 |
| requirements | 15.08 | 14.95 | 17.67 | 2.72 |
| location | 1.94 | 1.92 | 2.19 | 0.27 |
| description | 0.01 | 0.0 | 0.12 | 0.12 |
| title | 0.0 | 0.0 | 0.0 | 0.0 |
| has_questions | 0.0 | 0.0 | 0.0 | 0.0 |
| telecommuting | 0.0 | 0.0 | 0.0 | 0.0 |
| has_company_logo | 0.0 | 0.0 | 0.0 | 0.0 |

Columnas cuya ausencia es muy distinta entre clases (≥ 10 puntos): `salary_range`, `required_experience`, `company_profile`. Que falte un campo ya es una señal para el modelo; si se rellena sin cuidado, esa señal se pierde, y si el modelo depende demasiado de ella, puede fallar con ofertas de otra fuente.

## 3. Duplicados

| Medida | Valor |
|---|---|
| filas identicas sin job id | 281 |
| ofertas con texto repetido | 3.164 |
| grupos de texto repetido | 849 |
| textos unicos | 15.565 |
| repetidas entre fraudulentas | 276 |
| grupos con etiquetas contradictorias | 0 |
| descripcion identica solo descripcion | 3.477 |

Si una misma oferta (o casi la misma) queda en entrenamiento y en prueba, la métrica sale inflada (fuga de datos), igual que en el corpus de LinkedIn. No hay textos repetidos con etiquetas contradictorias.

## 4. Posibles fugas de información y sesgos

**job_id.** Tasa de fraude por décil de `job_id` (%): [2.13, 4.36, 4.03, 8.5, 4.42, 2.35, 2.63, 0.84, 0.45, 18.74]. Variación máxima: 18.29 puntos. `job_id` es un identificador: **no debe usarse como variable**, aunque parezca predictivo.

**Marcadores anonimizados** (`#URL_…#`, `#EMAIL_…#`, `#PHONE_…#`):

| Marcador | % en reales | % en fraudulentas |
|---|---|---|
| URL | 31.47 | 30.83 |
| EMAIL | 6.82 | 20.09 |
| PHONE | 2.63 | 9.12 |

Son tokens del dataset original y **no aparecen en ofertas reales**. Antes de entrenar hay que convertirlos a los mismos marcadores del proyecto (`[URL]`, `[EMAIL]`; teléfono → `[PHONE]`), para que el modelo vea lo mismo que verá en producción.

**Campos binarios** (tasa de fraude según el valor):

| Campo | % fraude si = 1 | % fraude si = 0 | % de ofertas con 1 |
|---|---|---|---|
| telecommuting | 8.34 | 4.69 | 4.29 |
| has_company_logo | 1.99 | 15.93 | 79.53 |
| has_questions | 2.84 | 6.78 | 49.17 |

`has_company_logo` y `has_questions` vienen de la plataforma original y **no existen** en el texto que pega un usuario ni en el corpus de LinkedIn. Si el modelo los usa, funcionará bien en la prueba pero no en la app (diferencia entre entrenamiento y uso real).

**Ubicación.** El 59.6 % de las ofertas son de EE. UU. Las 3 ciudades con más fraude concentran el **17.67 %** de todas las fraudulentas:

| Ciudad | Ofertas | Fraudulentas | % fraude |
|---|---|---|---|
| US, TX, Houston | 270 | 92 | 34.07 |
| AU, NSW, Sydney | 82 | 31 | 37.8 |
| US, CA, Bakersfield | 32 | 30 | 93.75 |
| US, ,  | 339 | 28 | 8.26 |
| US, CA, San Mateo | 49 | 24 | 48.98 |
| US, CA, Los Angeles | 194 | 23 | 11.86 |
| US, NY, New York | 674 | 20 | 2.97 |
|  | 346 | 19 | 5.49 |

Si se usa la ubicación, el modelo puede aprender «ciudad X = fraude», que es un sesgo, no una señal de fraude.

## 5. Calidad del texto

| Medida | Valor |
|---|---|
| palabras descripcion mediana reales | 147 |
| palabras descripcion mediana fraudulentas | 113 |
| descripcion menos de 20 palabras | 315 |
| con html | 0 |
| con mas de 20pct no ascii | 101 |
| valores distintos employment type | 6 |
| valores distintos required experience | 8 |
| valores distintos required education | 14 |
| valores distintos industry | 132 |
| valores distintos function | 38 |

## 6. Recomendaciones para preparar y evaluar el modelo

**Preparación**
1. Usar solo campos que existirán en la app: título y texto (descripción, requisitos, beneficios, perfil de la empresa). **No usar** `job_id`, `has_company_logo`, `has_questions` ni, en lo posible, la ubicación.
2. Reemplazar `#URL_…#`, `#EMAIL_…#` y `#PHONE_…#` por los marcadores del proyecto (`[URL]`, `[EMAIL]`, `[PHONE]`), con la misma limpieza del corpus de LinkedIn (sin borrar C++, C#, .NET).
3. Tratar los campos vacíos de forma explícita (por ejemplo, el texto «sin perfil de empresa») en vez de eliminar las filas.
4. Agrupar los textos repetidos **antes** de dividir y revisar o excluir los grupos con etiquetas contradictorias.

**División**
5. Entrenamiento / validación / prueba **estratificada por clase y agrupada por texto**, con semilla 42, para que cada partición tenga la misma proporción de fraude y ningún texto quede en dos particiones.

**Entrenamiento**
6. Pesos por clase (o sobremuestreo **solo** del entrenamiento) para compensar el desbalance.
7. Comparar contra un modelo base (TF-IDF + regresión logística).

**Evaluación**
8. Métricas principales: **recall de la clase fraude**, **precisión de la clase fraude**, **F1 de fraude** y **PR-AUC**. Reportar también la matriz de confusión. **No usar accuracy** como métrica principal.
9. Elegir el umbral con el conjunto de **validación** y usar la prueba una sola vez.
10. Revisar a mano falsos positivos y falsos negativos.

**Presentación en la app**
11. Mostrarlo como **riesgo estimado**, no como prueba de fraude (contrato de datos).
12. Advertir el **cambio de dominio**: EMSCAD tiene ofertas de 2012–2014 y de otra plataforma; el rendimiento en ofertas de LinkedIn 2024 puede ser menor que en la prueba.