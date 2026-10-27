# Pipeline de datos — Auditoría (Catalina)

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

El script `01d` tarda unos 15 minutos con el dataset completo.

## Validación cruzada con `src/audit_data.py`

Los conteos de filas, duplicados y nulos coinciden con el script de Sofia,
excepto los vacíos de `job_skills`: 2.007 (audit_data) frente a 2.085 (pandas).
La diferencia son 78 celdas con los textos "None" (50), "N/A" (27) y "NA" (1),
que pandas convierte en nulos por defecto. Se tratarán como vacíos de forma
explícita en la limpieza.