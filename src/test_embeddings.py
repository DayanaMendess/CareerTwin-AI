
from time import perf_counter
from sentence_transformers import SentenceTransformer
import os
import psutil

print("Iniciando CareerTwin AI - Prueba NLP")

inicio = perf_counter()

# Modelo neuronal preentrenado para embeddings
modelo = SentenceTransformer(
    "BAAI/bge-small-en-v1.5",
    device="cpu"
)

# Perfil y ofertas de ejemplo en inglés
textos = [
    "Software developer with Python, SQL and machine learning skills.",
    "We are hiring a Python developer with SQL experience.",
    "Restaurant manager with customer service and sales experience."
]

# Convertir textos en vectores numéricos
vectores = modelo.encode(
    textos,
    normalize_embeddings=True,
    show_progress_bar=False
)

print("Modelo cargado correctamente")
print("Dimensiones:", vectores.shape)

# Comparación semántica
similitud_1 = float(vectores[0] @ vectores[1])
similitud_2 = float(vectores[0] @ vectores[2])

print("Afinidad con oferta de Python:", round(similitud_1, 4))
print("Afinidad con oferta de restaurante:", round(similitud_2, 4))
print("Tiempo total (segundos):", round(perf_counter() - inicio, 2))



# Benchmark con 100 textos de prueba
print("\nIniciando prueba de rendimiento con 100 textos...")

textos_prueba = textos * 33 + [textos[0]]

inicio_prueba = perf_counter()

vectores_prueba = modelo.encode(
    textos_prueba,
    batch_size=16,
    normalize_embeddings=True,
    show_progress_bar=True
)

tiempo_prueba = perf_counter() - inicio_prueba

print("Cantidad procesada:", len(textos_prueba))
print("Dimensiones:", vectores_prueba.shape)
print("Tiempo de procesamiento:", round(tiempo_prueba, 2), "segundos")
print("Velocidad:", round(len(textos_prueba) / tiempo_prueba, 2), "textos/segundo")

# Medir memoria RAM utilizada por nuestro proceso
proceso = psutil.Process(os.getpid())

ram_mb = proceso.memory_info().rss / (1024 ** 2)

print("\n--- RECURSOS DEL MODELO ---")
print("RAM del proceso:", round(ram_mb, 2), "MB")
print("RAM disponible:", round(
    psutil.virtual_memory().available / (1024 ** 3), 2
), "GB")