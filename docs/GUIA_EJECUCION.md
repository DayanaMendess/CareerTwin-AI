# CareerTwin AI — Guía de instalación y ejecución

## 1. Descripción

CareerTwin AI es un proyecto académico de inteligencia artificial que utiliza procesamiento de lenguaje natural (NLP) para analizar habilidades profesionales y explorar oportunidades laborales.

El sistema integra:

- Una red neuronal CNN multietiqueta entrenada con 100 habilidades.
- Un detector de habilidades basado en texto.
- Un backend Flask.
- Una interfaz web con gráficas del mercado laboral.
- Módulos de Skill Gap y similitud semántica laboral.

## 2. Requisitos

- Windows 10 u 11.
- Python 3.11.
- Git.
- Visual Studio Code.
- Conexión a internet para instalar dependencias.

## 3. Obtener el proyecto

Clonar el repositorio:

`git clone https://github.com/DayanaMendess/CareerTwin-AI.git`

Ingresar a la carpeta:

`cd CareerTwin-AI`

## 4. Preparar el entorno

Crear el entorno virtual:

`py -3.11 -m venv .venv`

Instalar dependencias generales:

`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`

Instalar dependencias de inteligencia artificial:

`.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt`

Las dependencias de IA incluyen TensorFlow 2.19.1 y las bibliotecas utilizadas para el análisis NLP.

## 5. Configurar el modelo entrenado

El archivo `career_skills.keras` no está incluido en GitHub, ya que se excluye mediante `.gitignore`.

Se debe obtener una copia del modelo entrenado del equipo y colocarla en:

`models/career_skills.keras`

También se necesitan los archivos de vocabulario y evaluación disponibles en:

- `reports/skills_vocab.json`
- `reports/evaluacion_final_skills.json`
- `reports/clasificacion_habilidades_revisada.csv`

No es necesario volver a entrenar el modelo para ejecutar las predicciones.

## 6. Ejecutar las pruebas

Desde la raíz del proyecto:

`.\.venv\Scripts\python.exe -X utf8 -m pytest -q`
Durante la integración de Fraud Shield se verificaron 25 pruebas automatizadas aprobadas.

El resultado puede cambiar si posteriormente se agregan más pruebas.

## 7. Iniciar la aplicación

Ejecutar:

`.\.venv\Scripts\python.exe -X utf8 -m app.main`

Abrir en un navegador:

`http://127.0.0.1:5000`

La aplicación permite ingresar un perfil profesional, sus habilidades y su objetivo laboral.

El servidor de desarrollo Flask se utiliza únicamente para pruebas locales.

## 8. API de análisis

**Endpoint:** `POST /api/analyze-profile`

Ejemplo de solicitud:

`{"profile_text": "Software developer with Python, SQL and C++ experience"}`

Cuando el análisis es exitoso, el servicio devuelve:

- Estado de la operación.
- Habilidades identificadas.
- Fuente de detección: texto, modelo o ambos.
- Puntuaciones del modelo cuando correspondan.
- Número total de habilidades.
- Advertencias sobre las limitaciones del análisis.

## 9. Resultados del modelo

El modelo CNN fue entrenado durante 30 épocas y evaluado sobre 7.500 ofertas de prueba.

| Métrica | Resultado |
|---|---:|
| Micro-F1 | 0.3443 |
| Macro-F1 | 0.1343 |
| Umbral seleccionado | 0.20 |
| Etiquetas del modelo | 100 |

El detector textual complementa las predicciones con un catálogo de habilidades y términos técnicos adicionales.

## 10. Limitaciones

- El modelo fue entrenado principalmente con ofertas laborales en inglés.
- Las habilidades identificadas no certifican las competencias de una persona.
- Las puntuaciones del modelo no son probabilidades calibradas.
- Las estadísticas del mercado corresponden a los datos utilizados en el proyecto, no necesariamente al mercado laboral colombiano actual.
- Los resultados personalizados y los módulos complementarios deben validarse antes de considerarlos completamente terminados.



## 11. Fraud Shield — Detección de ofertas fraudulentas

Fraud Shield es un módulo independiente que analiza el texto
de una oferta laboral y detecta señales de posible fraude.

### Dataset y entrenamiento

Se utiliza EMSCAD, un conjunto de ofertas laborales reales
y fraudulentas.

Preparar los datos:

`.\.venv\Scripts\python.exe -X utf8 src\preparar_fraude.py`

Entrenar el detector:

`.\.venv\Scripts\python.exe -X utf8 src\entrenar_fraude.py`

El modelo utiliza TF-IDF y regresión logística con
ponderación de clases.

Se emplean particiones de entrenamiento (70 %),
validación (15 %) y prueba (15 %), aproximadamente.

### Modelo entrenado

El archivo `models/fraud_detector.joblib` no se incluye en
GitHub y debe obtenerse directamente del equipo.

Por seguridad, solo deben cargarse archivos de modelo
generados por fuentes confiables.

### API de fraude

**Endpoint:** `POST /api/fraud-risk`

Ejemplo de solicitud JSON:

```json
{
  "job_text": "Remote Python developer position with SQL experience."
}
```

La respuesta contiene:

- Clasificación de posible fraude.
- Indicador de riesgo detectado.
- Puntuación del modelo.
- Umbral utilizado.
- Advertencia sobre las limitaciones del resultado.

### Resultados de evaluación

El umbral 0.60 se seleccionó usando validación.

Resultados en el conjunto de prueba:

| Métrica | Resultado |
|---|---:|
| Precision de fraude | 0.8172 |
| Recall de fraude | 0.7379 |
| F1 de fraude | 0.7755 |
| Average precision | 0.8132 |
| Ofertas de prueba | 2374 |
| Fraudulentas detectadas | 76 |
| Fraudulentas no detectadas | 27 |

Reportes:

- `reports/preparacion_fraude.json`
- `reports/entrenamiento_fraude.json`

### Limitaciones

El detector identifica señales estadísticas de riesgo,
pero no confirma que exista fraude.

Una oferta no señalada puede seguir siendo fraudulenta.
Las puntuaciones no son probabilidades calibradas.

La auditoría de calidad de datos y las pruebas con ofertas
externas siguen siendo necesarias para validar su
generalización.


## 12. Equipo

**Proyecto:** CareerTwin AI

**Integrantes:**

- Sofia Mendes — Entrenamiento, evaluación e integración de inteligencia artificial.
- Catalina Cortés — Procesamiento, auditoría y detección de habilidades.
- Sergio Pérez — Backend Flask, interfaz web y visualización de resultados.

**Repositorio:** https://github.com/DayanaMendess/CareerTwin-AI