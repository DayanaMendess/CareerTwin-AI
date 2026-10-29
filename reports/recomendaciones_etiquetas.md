# Recomendaciones sobre las etiquetas — Catalina

Basado en `reports/validacion_etiquetas.json`.

## Estado actual
- No hay fuga de datos: 0 grupos, 0 textos idénticos y 0 IDs repetidos entre train, val y test.
- 84,5 % de los registros tiene al menos 1 de las 100 habilidades (4,4 en promedio).
- Las 100 habilidades cubren el 20,6 % de las menciones del dataset; las 217 válidas revisadas cubrirían el 25,5 %.

## Para el entrenamiento actual (no cambiar los datos)
1. `communication` (42,8 %) y `problem solving` (25,1 %) son muy frecuentes: medir con Macro-F1 además de Micro-F1 y, si es posible, usar pesos por clase.
2. `cleaning` (0,97 %) y `cash handling` (0,94 %) son las menos frecuentes: es normal que tengan un F1 más bajo.
3. `management` es muy general y se cruza con 6 etiquetas más específicas (project, team, risk, case, performance e inventory management): revisar cómo le va en los resultados.
4. Hay pares que casi siempre aparecen juntos (por ejemplo `problem solving` + `teamwork`, `patient care` + `nursing`). No es un error: las empresas los piden juntos.

## Para la versión 2 (vocabulario ampliado)
1. Unir `team player` en `teamwork`.
2. Mantener separadas: `organization` / `organizational skills`, `adaptability` / `flexibility`, `communication` / `verbal communication`, `quality control` / `quality assurance` y `nursing` / `patient care`, porque no significan exactamente lo mismo.
3. Ampliar a 217–300 habilidades válidas solo sube la cobertura de menciones unos 5 puntos (de 20,6 % a 25,5 %), pero puede dar etiquetas a parte de los 7.760 registros que hoy no tienen ninguna.