# CareerTwin AI — Base de trabajo en equipo

**Curso:** Inteligencia Artificial · **Equipo:** Sofia, Catalina y Sergio  
**Proyecto:** NLP + red neuronal multietiqueta + análisis de habilidades + simulación de trayectorias + módulo adicional de detección de ofertas potencialmente fraudulentas.

> Estado: **estructura inicial**, no contiene modelos entrenados ni resultados de evaluación. Los porcentajes y predicciones solo se mostrarán cuando existan modelos validados. El dataset de LinkedIn 2024 no contiene etiquetas de fraude; para ese módulo se necesita otro dataset etiquetado, por ejemplo EMSCAD.

## Instalar y ejecutar — Windows PowerShell

1. Instalar Git y Python 3 (verificar con `git --version` y `py --version`).
2. Abrir esta carpeta en VS Code.
3. Crear entorno virtual y dependencias mínimas:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> Si PowerShell bloquea activar el entorno, usar `cmd` con `.venv\Scripts\activate.bat`, o ejecutar ` .venv\Scripts\python.exe ...` sin activación. No desactivar políticas de seguridad del sistema por este proyecto.

4. Ejecutar pruebas:

```powershell
python -m pytest -q
```

5. Ejecutar sitio de prueba:

```powershell
python -m flask --app app.main run --debug
```

Abrir http://127.0.0.1:5000. La pantalla solo valida que Flask funciona.

## Datos — auditoría preliminar, sin cargar todo a RAM

Fuente: https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024

Descargar desde Kaggle los tres archivos con **exactamente** estos nombres y guardarlos localmente en `data/raw/`:

- `linkedin_job_postings.csv`
- `job_skills.csv`
- `job_summary.csv`

No añadir archivos CSV gigantes a Git ni compartirlos mediante commits.

Primera prueba (1000 registros de cada CSV):

```powershell
python -m src.audit_data --limit 1000
```

Auditoría completa por lectura de archivos en streaming:

```powershell
python -m src.audit_data --limit 0
```

Se guarda un informe JSON en `reports/auditoria_dataset.json` que sí se puede compartir por Git. Las cifras de filas y duplicados son por archivo; **la cantidad de filas después de cruzar los CSV sigue pendiente** de validación. La auditoría no modifica los datos y no reemplaza una limpieza ETL posterior.

## Colaboración con Git

1. Una persona crea un repositorio privado llamado `careertwin-ai`, sube estos archivos a `main` e invita a los otros dos usuarios de GitHub.
2. Cada integrante clona el repositorio y crea una rama para una tarea pequeña.
3. Ejemplo:

```powershell
git switch main
git pull origin main
git switch -c feature/auditoria-inicial
# editar archivos...
git status
git add src/audit_data.py docs/
git commit -m "feat: auditoria inicial del corpus"
git push -u origin feature/auditoria-inicial
```

4. Abrir un **Pull Request**, pedir revisión a otro integrante, incorporar ajustes y fusionar a `main`.
5. Antes de comenzar una tarea nueva, actualizar `main` con `git pull origin main`.

**Convención:** `feature/<nombre>`, `fix/<nombre>`, `docs/<nombre>`; commits `feat:`, `fix:`, `docs:`, `test:`.

## Acuerdos de responsabilidades iniciales

| Integrante | Prioridad inicial | Entregable |
| --- | --- | --- |
| Catalina (16 GB) | Descargar/auditar, proponer limpieza y documentar variables | `reports/auditoria_dataset.json`, diccionario de datos y EDA |
| Sofia (24 GB) | Arquitectura NLP, experimentos básicos/neuronal con datos de muestra | especificación de etiquetas, esquema de evaluación y primer notebook |
| Sergio (8 GB) | Flask, interfaz inicial, pruebas y documentación del despliegue | endpoints, pruebas automáticas y vista de prueba |

El entrenamiento pesado podrá ejecutarse en Colab; los tres deben poder explicar el modelo.

## Contratos mínimos (borrador)

Los tres CSV se relacionan por `job_link`. Para limpieza y modelado, el equipo validará columnas existentes reales y definirá estas salidas comunes:

- `job_id` / `job_link` normalizado: identificador de la oferta.
- `job_title`: título del puesto.
- `job_summary_clean`: descripción normalizada (sin borrar términos técnicos importantes).
- `skills_normalized`: lista de competencias canonicalizadas.

**API planificada** (todavía no implementada):

- `POST /api/analyze-profile`: extrae y clasifica habilidades del texto.
- `POST /api/match`: busca perfiles laborales similares.
- `POST /api/simulate`: compara escenarios de nuevas habilidades.
- `POST /api/fraud-risk`: evalúa señales de fraude desde un modelo separado, con advertencias.

Hasta que estos modelos existan, sus endpoints no deben entregar porcentajes simulados como resultados reales.

## Alcance y evaluación académica

- Red neuronal principal NLP: clasificador multietiqueta de habilidades (Keras), frente a baseline TF-IDF.
- Metodología: confirmar cuál(es) vieron en clase; CRISP-DM es una propuesta, **no** un dato confirmado en la guía.
- Evaluación: Micro/Macro-F1, Precision@K y Recall@K; evitar fuga de datos por descripciones repetidas, agrupando textos duplicados antes del split.
- Fraude: EMSCAD (segundo dataset), métricas Recall-Fraude y PR-AUC. **LinkedIn 2024 no está etiquetado como fraudulento**.
- Interfaz: mínimo tres gráficas sobre datos/resultados reales.
- Producción: entrenar *fuera* del servidor; desplegar un modelo de inferencia compacto y los datos de consulta previamente preparados.
- Informe académico APA 7, PDF de mínimo 10 páginas, código, README y archivo ZIP; se entrega antes de la sustentación del 10-11-2026.

## Entrega corta de cada Pull Request

- [ ] Archivo(s) y tarea claramente definidos
- [ ] Código corre localmente
- [ ] Pruebas realizadas
- [ ] No incluye CSV, secretos ni modelos grandes
- [ ] Descripción de qué cambió y evidencia capturada
- [ ] Otro integrante revisó
