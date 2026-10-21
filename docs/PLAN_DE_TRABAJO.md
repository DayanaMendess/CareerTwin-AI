# Plan de trabajo — 20 octubre al 10 noviembre de 2026

## Objetivo verificable (MVP)

Un sitio Flask desplegado que recibe texto de perfil, ejecuta una red neuronal NLP entrenada y evaluada, muestra habilidades y compatibilidad, presenta **tres gráficas basadas en datos reales** y permite una simulación de habilidades explicable. Un módulo de fraude se integra después usando un segundo dataset etiquetado.

## Fases y responsables

| Fecha objetivo | Fase | Responsable | Evidencia |
| --- | --- | --- | --- |
| 20-22 oct | Base Git + auditoría preliminar + contrato | Todos / Catalina datos | Repositorio, reporte de calidad y primer PR |
| 23-25 oct | ETL + etiquetas + división sin fuga | Catalina + Sofia | Dataset procesado y EDA |
| 26-30 oct | Baseline + primera red NLP | Sofia | Métricas reproducibles, modelo exportado |
| 28 oct-1 nov | Interfaz + API y pruebas | Sergio | Flask usable con respuestas de prueba explícitas |
| 31 oct-3 nov | Matching + simulación | Catalina + Sofia | Simulador evaluado y gráficas |
| 2-5 nov | Fraude, si MVP estable | Sergio + Sofia | Modelo secundario y evaluación |
| 5-7 nov | Integración y despliegue | Sergio + Sofia | URL funcional y pruebas end-to-end |
| 7-9 nov | Informe, PDF, ZIP, ensayos | Los tres | APA 7, README, presentación ensayada |
| 10 nov | Sustentación | Los tres | Demostración en producción |

## Reunión diaria de 10-15 minutos

Cada persona responde: (1) completé..., (2) haré..., (3) estoy bloqueado por...  
Cuando un integrante cambie columnas/formatos, actualiza `docs/CONTRATO_DATOS.md` y avisa **antes** de fusionar su rama.

## Prioridad en caso de retrasos

1. Primero: **una red neuronal entrenada** que haga predicción NLP real.
2. Luego: Flask y al menos tres gráficas de resultados reales.
3. Luego: despliegue en servidor y documento APA.
4. Después: simulador sofisticado, fraude, mejoras estéticas. El tiempo restante es limitado.

## Hitos que deben aprobar antes de avanzar

- [ ] Auditoría: conteo, columnas, nulos, duplicados y cruzabilidad por `job_link`.
- [ ] Dataset procesado versionado con huella SHA256 y reporte de limpieza.
- [ ] Divisiones train/val/test por grupos de descripciones similares o idénticas.
- [ ] Red neuronal entrenada realmente; registrar semilla, versiones, hiperparámetros.
- [ ] Evaluación con Micro/Macro-F1 y Precision@K sin fugas.
- [ ] Tres gráficas visibles, con etiquetas y fuentes.
- [ ] Flask con predicción real y manejo de errores.
- [ ] Modelo compacto probado en el plan de hospedaje.
- [ ] PDF APA 7 >=10 páginas + ZIP completo, sin CSV grandes.
