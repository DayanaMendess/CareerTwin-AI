# Contrato de datos — Borrador v0.1

Fuente elegida: https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024

## Entradas observadas en fuentes externas (confirmar descargando el CSV exacto)

| CSV | Clave de cruce | Dato de interés |
| --- | --- | --- |
| linkedin_job_postings.csv | `job_link` | `job_title`, `company`, `job_location`, etc. |
| job_skills.csv | `job_link` | `job_skills` o `skills` según versión; **verificar encabezado** |
| job_summary.csv | `job_link` | `job_summary` |

No dar por sentada la unicidad de `job_link`, el total resultante del merge ni la proporción de textos aptos: medirlos primero.

## Esquema de salida propuesta (Parquet posterior)

- `job_id`: ID estable derivado de `job_link`.
- `job_title`: título en texto.
- `job_summary_clean`: descripción tras normalización y preservación de términos técnicos.
- `skills_normalized`: lista de skills canonicalizadas.
- `job_location`: ubicación (si está disponible).
- `source_version`: identificador de versión del dataset.

## Reglas de validación

1. No borrar `C++`, `C#`, `.NET`, `Node.js` ni otros signos que son parte de nombres tecnológicos.
2. No convertir toda coma de una frase en separación de skills sin revisar casos especiales.
3. Detectar descripciones repetidas antes de train/test.
4. No tratar la puntuación de similitud coseno como probabilidad calibrada ni como garantía de empleo.
5. Fraud Shield necesita dataset y etiquetas independientes; debe presentarse como **riesgo estimado**, no prueba de fraude.
6. No mostrar recomendaciones o resultados ficticios como si provinieran de una red entrenada.
7. Dataset de 2024: no proclamar que los resultados representan la disponibilidad de empleo actual de 2026.
