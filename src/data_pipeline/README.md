# Pipeline de datos — Auditoría 

Scripts para auditar el dataset *1.3M LinkedIn Jobs & Skills (2024)*.
Requieren los 3 CSV en `data/raw/` y las librerías de `requirements-ml.txt`.

## Orden de ejecución

Ejecutar desde la carpeta raíz del proyecto:

| # | Script | Qué hace | Resultado |
|---|---|---|---|
| 1 | `01a_auditoria_mirar.py` | Columnas y primeras filas de cada CSV | Pantalla |
| 2 | `01b_auditoria_contar.py` | Filas, nulos y `job_link` duplicados (lectura por bloques) | `reports/auditoria_conteos.json` |
| 3 | `01c_auditoria_relaciones.py` | Cruces entre archivos, verificación de banderas y distribuciones | `reports/auditoria_relaciones.json` |
| 4 | `01d_auditoria_calidad.py` | Calidad de descripciones, habilidades y títulos; une los resultados anteriores | `reports/auditoria_detallada.json` |
| 5 | `01e_verificar_nulos_skills.py` | Explica la diferencia de nulos en `job_skills` frente a `src/audit_data.py` | Pantalla |
| 6 | `02_normalizacion.py` | Separa y normaliza las habilidades (reglas en `habilidades_utils.py`) | `reports/catalogo_habilidades_top1000.csv`, `reports/normalizacion_resumen.json` |
| 7 | `02b_candidatos_sinonimos.py` | Sugiere grupos de posibles sinónimos para revisión manual | `reports/candidatos_sinonimos.csv` |
| 8 | `03a_clasificar_sugerencias.py` | Clasificación automática sugerida del top 300 | `reports/clasificacion_top300_sugerida.csv` |
| — | *(revisión manual)* | Se corrige la categoría y se documenta el motivo | `reports/clasificacion_habilidades_revisada.csv` |
| 9 | `03b_vocabulario_piloto.py` | Elige las 100 habilidades válidas más frecuentes | `reports/skills_vocab_piloto.json` |
| 10 | `04_muestra.py` | Muestra de 50.000 textos únicos (semilla 42), limpieza y duplicados finos | `data/processed/muestra_50k.parquet` |
| 11 | `04b_verificar_muestra.py` | Verifica los términos técnicos y la consistencia de las etiquetas | `reports/verificacion_muestra.json` |

El script `01d` tarda unos 15 minutos con el dataset completo.

## Validación cruzada con `src/audit_data.py`

Los conteos de filas, duplicados y nulos coinciden con el script de Sofia,
excepto los vacíos de `job_skills`: 2.007 (audit_data) frente a 2.085 (pandas).
La diferencia son 78 celdas con los textos "None" (50), "N/A" (27) y "NA" (1),
que pandas convierte en nulos por defecto. Se tratarán como vacíos de forma
explícita en la limpieza.