# Entrega académica — CareerTwin AI

**Corporación Universitaria del Huila — CORHUILA**  
**Programa:** Ingeniería de Sistemas · **Asignatura:** Inteligencia Artificial · **Periodo:** 2026-2  
**Docente:** José Miguel Llanos Mosquera  
**Integrantes:** Dayana Sofía Mendes Perafán; Andrea Catalina Cortes; Sergio Andres Perez Ramirez

## Informe final

Colocar aquí ambos archivos correspondientes a la **versión corregida** y revisada sobre la plantilla APA de CORHUILA:

- `Informe_Final_CareerTwin_AI_CORHUILA_Plantilla_APA7_CORREGIDO.pdf` — documento principal de entrega.
- `Informe_Final_CareerTwin_AI_CORHUILA_Plantilla_APA7_CORREGIDO.docx` — versión editable.

La versión final contiene portada institucional, resumen y abstract, contenido, índices de tablas y figuras, introducción, justificación, objetivos, metodología, desarrollo de la red neuronal CNN, resultados, evaluación de Fraud Shield, conclusiones y referencias.

**Nota sobre la entrega:** incluir el PDF y el Word en esta carpeta. Git solo puede incluirlos en el ZIP una vez se hayan añadido y confirmado en el repositorio.

## Reproducción y evidencias

- Código de la aplicación: `app/`, `src/`, `tests/`.
- Métricas CNN: `reports/evaluacion_final_skills.json` y `reports/INFORME_ENTRENAMIENTO_IA.md`.
- Métricas Fraud Shield: `reports/entrenamiento_fraude.json`.
- Figuras originales: `reports/figuras/`.
- Guía de ejecución: `docs/GUIA_EJECUCION.md`.
- **Validación final:** 34 pruebas automatizadas aprobadas en Ubuntu 24.04.
- **Enlace público:** Cloudflare Quick Tunnel se utilizó para la demostración, pero es temporal y **no equivale a un despliegue persistente de producción**.

## Crear el ZIP desde Git

Una vez que los dos documentos estén confirmados en `main`, se pueden incluir automáticamente con:

```powershell
git switch main
git pull --ff-only origin main
git archive --format=zip --output="C:\Proyectos\CareerTwin-AI_Entrega.zip" main
```

El ZIP del repositorio no incluirá los modelos binarios locales `.keras` y `.joblib`, excluidos de Git para evitar archivos pesados. Si se necesita una copia ejecutable sin reconstruir los modelos, entregar esos archivos mediante Drive con las precauciones habituales.
