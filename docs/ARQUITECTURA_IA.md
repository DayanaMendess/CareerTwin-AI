
# CareerTwin AI — Arquitectura de Inteligencia Artificial

## 1. Objetivo

Desarrollar un sistema basado en Procesamiento de Lenguaje Natural (NLP) y redes neuronales que permita identificar habilidades profesionales, analizar compatibilidad laboral y simular posibles trayectorias de crecimiento profesional.

## 2. Fuentes de datos

### Dataset principal
1.3M LinkedIn Jobs & Skills 2024.

Archivos:
- linkedin_job_postings.csv
- job_summary.csv
- job_skills.csv

Unión de los archivos mediante `job_link`.

El corpus completo se utilizará para análisis y estadísticas. Para entrenamiento se emplearán conjuntos preparados y particionados evitando duplicados entre entrenamiento, validación y prueba.

### Dataset secundario
EMSCAD, para entrenar y evaluar el módulo de detección de ofertas potencialmente fraudulentas.

## 3. Modelo neuronal principal

Tarea: clasificación multietiqueta de habilidades profesionales.

Entrada: título y descripción textual de una oferta.

Procesamiento:
1. Limpieza y normalización.
2. Tokenización.
3. Conversión del texto a secuencias numéricas.
4. Representación mediante una capa Embedding.
5. Extracción de patrones mediante Conv1D.
6. GlobalMaxPooling.
7. Capas Dense y Dropout.
8. Salida Sigmoid multietiqueta.

Función de pérdida: Binary Crossentropy.

Vocabulario piloto: 100 habilidades.
Ampliación propuesta: aproximadamente 300 habilidades, según cobertura y calidad de las etiquetas.

## 4. Modelo de embeddings

Modelo propuesto: BAAI/bge-small-en-v1.5.

Objetivo: representar semánticamente perfiles profesionales y ofertas laborales.

Dimensión: 384.

Longitud máxima: 512 tokens.

Las descripciones extensas requerirán una estrategia de segmentación para evitar pérdida de información.

## 5. Módulos de aplicación

### Skill Intelligence
Predicción e identificación de habilidades asociadas a textos profesionales.

### Job Matching
Cálculo de similitud semántica entre perfiles profesionales y ofertas.

### Skill Gap
Comparación de habilidades presentes y faltantes.

### Career Simulator
Simulación del cambio de afinidad laboral al incorporar nuevas habilidades.

### Fraud Shield
Estimación de riesgo de fraude utilizando un modelo entrenado con datos etiquetados.

## 6. Evaluación

Modelo multietiqueta:
- Precision
- Recall
- Micro-F1
- Macro-F1
- Precision@5

Se utilizarán conjuntos separados de entrenamiento, validación y prueba sin duplicados cruzados.

Las etiquetas extraídas automáticamente se considerarán etiquetas de referencia imperfectas.

## 7. Integración con Flask

La aplicación recibirá un perfil profesional en texto.

La API llamará a los servicios de NLP y devolverá habilidades, coincidencias y resultados del simulador.

Los resultados mostrados deberán provenir de cálculos reales y no de porcentajes inventados.

## 8. Tecnologías

- Python 3.11
- TensorFlow y Keras
- Sentence Transformers
- Scikit-learn
- Pandas / Polars
- Flask
- Git y GitHub

## 9. Consideraciones

El dataset corresponde principalmente a ofertas en inglés de enero de 2024.

Los resultados no representan automáticamente el mercado laboral colombiano actual.

Las puntuaciones de afinidad no equivalen a probabilidades de contratación.
