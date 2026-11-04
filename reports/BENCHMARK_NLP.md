
# CareerTwin AI — Benchmark de NLP

## Responsable
Sofia — Módulo de Inteligencia Artificial

## Hardware
- Equipo: ASUS
- Procesador: Intel Core 5 120U
- Núcleos: 10
- Procesadores lógicos: 12
- RAM instalada: 24 GB

## Modelo evaluado
BAAI/bge-small-en-v1.5

## Resultados
- Textos de prueba: 100
- Dimensiones de embeddings: 384
- Tiempo de procesamiento: 0.46 segundos
- Velocidad observada: 217.05 textos/segundo
- Memoria del proceso al finalizar: 581.45 MB
- RAM disponible en Windows: 5.21 GB

## Metodología
Se ejecutó el modelo en CPU utilizando Sentence
Transformers, con lotes de 16 textos.

Los textos utilizados eran ejemplos cortos repetidos.
La medición se realizó después de cargar el modelo.

## Conclusión
Se comprobó que BGE-Small puede ejecutarse localmente
y generar embeddings correctamente.

Los resultados son preliminares y no representan
el rendimiento con las descripciones reales del dataset.

## Próximas pruebas
- Evaluar descripciones reales de LinkedIn.
- Medir consumo máximo de RAM.
- Preparar entrenamiento neuronal con Keras.
- Ejecutar entrenamiento piloto de hasta 30 épocas.
