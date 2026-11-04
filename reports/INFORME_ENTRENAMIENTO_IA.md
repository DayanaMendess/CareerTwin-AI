# CareerTwin AI - Informe de entrenamiento

## Configuracion

- Modelo: CNN multietiqueta con Keras
- Entrenamiento: 35.000 ofertas
- Validacion: 7.500 ofertas
- Prueba: 7.500 ofertas
- Etiquetas profesionales: 100
- Epocas ejecutadas: 30
- Mejor epoca: 6
- Mejor perdida de validacion: 0.1395
- Umbral elegido con validacion: 0.2

## Resultados finales sobre test

| Metrica | Valor |
|---|---:|
| Micro-F1 | 0.3443 |
| Macro-F1 | 0.1343 |
| Precision micro | 0.3343 |
| Recall micro | 0.3549 |
| Precision@5 | 0.2990 |

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
