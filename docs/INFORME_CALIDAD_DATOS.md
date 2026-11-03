# Informe de calidad de datos — CareerTwin AI

**Responsable:** Catalina · **Fecha:** 22 de octubre de 2026
**Dataset:** *1.3M LinkedIn Jobs & Skills (2024)* — Kaggle (asaniczka)
**Evidencia:** `reports/auditoria_dataset.json`, `reports/auditoria_detallada.json` y scripts en `src/data_pipeline/`

---

## 1. Objetivo

Auditar el dataset antes de entrenar cualquier modelo: medir su volumen real, su estructura, los valores faltantes, los duplicados, la relación entre archivos y la calidad del contenido, y definir las condiciones necesarias para usarlo en el entrenamiento. Los CSV originales no se modificaron.

## 2. Metodología

- **Lectura por bloques** de 50.000 filas (`chunksize`), porque `job_summary.csv` pesa 5,1 GB y no cabe completo en memoria.
- **Cinco scripts** ejecutados en orden (`01a` a `01e`), cuyo orden está documentado en `src/data_pipeline/README.md`.
- **Validación cruzada** con el script del equipo `src/audit_data.py` y repetición de la auditoría con dos versiones de pandas (2.3 y 3.0).
- Rutas relativas al proyecto, para que cualquier integrante pueda reproducir los resultados.

## 3. Archivos y volumen

| Archivo | Tamaño | Filas | Columnas | `job_link` duplicados |
|---|---|---|---|---|
| `linkedin_job_postings.csv` | 415 MB | 1.348.454 | 14 | 0 |
| `job_skills.csv` | 673 MB | 1.296.381 | 2 | 0 |
| `job_summary.csv` | 5,1 GB | 1.297.332 | 2 | 0 |

Las filas se contaron con pandas y no por líneas del archivo, porque las descripciones contienen saltos de línea internos y un conteo por líneas daría un valor inflado.

## 4. Valores faltantes

| Columna | Faltantes | % |
|---|---|---|
| `company` | 11 | 0,001% |
| `job_location` | 19 | 0,001% |
| `job_skills` | 2.085 | 0,16% |
| `job_summary` | 0 | 0% |
| Resto de columnas | 0 | 0% |

**Hallazgo — validación cruzada:** `src/audit_data.py` reporta 2.007 vacíos en `job_skills` y pandas 2.085. La diferencia (78) corresponde a celdas con los textos `"None"` (50), `"N/A"` (27) y `"NA"` (1), que pandas convierte en nulos por defecto (verificado con `01e_verificar_nulos_skills.py`). Como significan "sin habilidades", se considerarán vacíos, pero de forma **explícita** en la limpieza, no por el comportamiento automático de pandas.

## 5. Relación entre archivos

- Los tres archivos se relacionan por `job_link`. **No están en el mismo orden**, así que deben unirse por esa columna y nunca por posición.
- No hay registros huérfanos: todas las habilidades y descripciones pertenecen a una oferta de `linkedin_job_postings.csv`.

| Medida | Ofertas | % de postings |
|---|---|---|
| Ofertas en postings | 1.348.454 | 100% |
| Con habilidades | 1.296.381 | 96,1% |
| Con descripción | 1.297.332 | 96,2% |
| Con las tres tablas | 1.296.381 | 96,1% |
| **Con las tres tablas y habilidades no vacías** | **1.294.296** | **96,0%** |

Toda oferta con habilidades también tiene descripción; hay 951 con descripción pero sin habilidades. El conjunto útil supera el millón de registros exigido.

**Banderas del scraper:** `got_summary` y `got_ner` indican si se extrajo la descripción y las habilidades, pero fallan en 565 casos (545 y 20) en los que dicen tenerlas y no existen. Por eso la disponibilidad se midió con los datos reales y no con estas banderas.

## 6. Distribución de variables

| Variable | Distribución | Conclusión |
|---|---|---|
| `job_level` | Mid senior 89,3% · Associate 10,7% | Solo dos clases y muy desbalanceadas |
| `job_type` | Onsite 99,2% · Hybrid 0,5% · Remote 0,3% | No es informativa; no se usará |
| `search_country` | EE. UU. 85,2% · Reino Unido 8,4% · Canadá 4,2% · Australia 2,2% | Solo cuatro países, todos de habla inglesa |
| `first_seen` | 12 al 17 de enero de 2024 | Fotografía de seis días |

`search_position` **no** corresponde al puesto real: es el término que el scraper usó para buscar (por ejemplo, un *Account Executive* aparece con la búsqueda *Color Maker*). El puesto real está en `job_title`.

## 7. Calidad de las descripciones

| Medida | Valor |
|---|---|
| Palabras (mediana) | 490 |
| Palabras (percentil 1 – percentil 99) | 80 – 1.653 |
| Caracteres (mediana) | 3.382 |
| Menos de 50 palabras | 3.667 (0,28%) |
| Menos de 100 palabras | 21.354 (1,65%) |
| Más de 2.000 palabras | 5.381 (0,41%) |
| Con etiquetas HTML | 344 (0,03%) |
| Con más de 20% de caracteres no ASCII | 117 (0,01%) |
| Con correos electrónicos | 144.341 (11,1%) |
| Con enlaces web | 202.915 (15,6%) |
| **Descripciones duplicadas exactas** | **342.559 (26,4%)** |

- El texto está, en general, limpio y en inglés.
- 490 palabras equivalen a unos 650 tokens, por encima del límite de muchos modelos de embeddings.
- Los correos son datos personales de reclutadores.
- Los duplicados se detectaron comparando la huella (*hash*) de cada texto en minúsculas y con espacios normalizados. Corresponden sobre todo a cadenas que publican la misma oferta en muchas ciudades. Quedan **954.773 descripciones únicas**.

## 8. Calidad de las habilidades

| Medida | Valor |
|---|---|
| Ofertas con habilidades | 1.294.296 |
| Habilidades por oferta (mediana / máximo) | 19 / 463 |
| Menciones totales | 26.925.240 |
| Habilidades distintas (texto original) | 3.301.512 |
| Habilidades distintas (en minúsculas) | 2.772.107 (−16%) |
| Aparecen una sola vez | 1.950.157 (70%) |
| Aparecen 100 veces o más | 21.447 |
| Aparecen 1.000 veces o más | 2.619 |

Hallazgos:

- **Cola larga:** la mayoría de las habilidades distintas son rarísimas o ruido de extracción.
- **Variantes de la misma habilidad:** `problem solving` (149.036) y `problemsolving` (129.329); `communication` y `communication skills`; `Python`, `python`, `Python3`, `Python programming` y `Python (programming language)`.
- **Requisitos académicos mezclados con habilidades:** `high school diploma` y `bachelor's degree` aparecen entre las 30 más frecuentes.
- **Predominio de habilidades blandas** en el top (communication, teamwork, leadership).
- **Falsos positivos al buscar por subcadena:** buscar "excel" devuelve también "Excellence" y "Excellent communication skills".
- **Origen de las etiquetas:** según la documentación de proyectos que usan este corpus, las habilidades fueron extraídas automáticamente del texto. No son etiquetas verificadas por expertos.

## 9. Calidad de los títulos

- 579.066 títulos distintos en minúsculas, con variantes como *"hourly supervisor & training"* y *"hourly supervisor and training"*, o sufijos como *-ft* y *-pt*.
- 152.123 ofertas (11,3%) repiten título, empresa y ubicación con un enlace distinto.
- Predominan comercio, salud y restaurantes (*customer service representative*, *store manager*, *registered nurse*).

## 10. Condiciones necesarias para el entrenamiento

1. Unir los archivos **por `job_link`** y trabajar con las **1.294.296** ofertas completas.
2. Tratar `"None"`, `"N/A"` y `"NA"` en `job_skills` como vacíos, **de forma explícita**.
3. **Agrupar las descripciones duplicadas antes de dividir** en entrenamiento y prueba, para que un mismo texto no quede en ambos conjuntos (fuga de datos). Para estadísticas de mercado se conserva el corpus completo.
4. **No recortar** las descripciones largas: se dividirán en fragmentos para el modelo de embeddings (BAAI/bge-small-en-v1.5, máximo 512 tokens).
5. **Reemplazar correos y enlaces por marcadores** (`[EMAIL]`, `[URL]`) en vez de eliminarlos, para proteger la privacidad sin perder señales útiles para el módulo de fraude.
6. Descartar descripciones con menos de 50 palabras (propuesta).
7. **Normalizar las habilidades** y excluir los requisitos académicos del vocabulario. Vocabulario piloto de **100** habilidades, ampliable a **300** según cobertura y validez.
8. No usar `job_type` ni `search_position` como etiquetas. Si se usa `job_level`, aplicar pesos por clase y evaluar con F1 por clase y matriz de confusión, no solo con *accuracy*.

## 11. Limitaciones

- Datos de solo **seis días** de enero de 2024: no permiten analizar tendencias en el tiempo.
- Solo **cuatro países de habla inglesa**: CareerTwin no representa el mercado laboral colombiano ni latinoamericano.
- Sesgo hacia comercio, salud y restaurantes; los puestos de tecnología tienen menor representación.
- Las habilidades son **extracciones automáticas**, no etiquetas verificadas por humanos.
- La detección de correos, enlaces e idioma usa reglas aproximadas (expresiones regulares y proporción de caracteres no ASCII).

## 12. Pendientes

1. Agrupar duplicados que solo difieren en puntuación o formato y verificar si una misma descripción tiene habilidades distintas.
2. Revisar manualmente una muestra de habilidades para caracterizar el ruido de extracción.
3. Normalización de habilidades (`02_normalizacion.py`).
4. Vocabulario piloto clasificado en técnicas, blandas y académicas (`03_vocabulario.py`).
5. Muestra reproducible de 50.000 ofertas (`04_preparacion.py`).

## 13. Cómo reproducir

Desde la carpeta raíz del proyecto, con los CSV en `data/raw/` y `requirements-ml.txt` instalado:

    python -m src.audit_data --limit 0
    python src/data_pipeline/01a_auditoria_mirar.py
    python src/data_pipeline/01b_auditoria_contar.py
    python src/data_pipeline/01c_auditoria_relaciones.py
    python src/data_pipeline/01d_auditoria_calidad.py
    python src/data_pipeline/01e_verificar_nulos_skills.py