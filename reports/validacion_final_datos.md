# Validación final de los datos — CareerTwin AI

Generado por `src/data_pipeline/10_validacion_final.py`.

**Resultado general:** ✅ todo correcto

## 1. Trazabilidad

| Archivo | Script que lo genera | Existe | Filas |
|---|---|---|---|
| `reports/auditoria_dataset.json` | `src/audit_data.py` | ✅ |  |
| `reports/auditoria_detallada.json` | `01a–01d_auditoria_*.py` | ✅ |  |
| `reports/catalogo_habilidades_top1000.csv` | `02_normalizacion.py` | ✅ | 1.000 |
| `reports/clasificacion_habilidades_revisada.csv` | `03a + revisión manual` | ✅ | 300 |
| `reports/skills_vocab_piloto.json` | `03b_vocabulario_piloto.py` | ✅ |  |
| `data/processed/muestra_50k.parquet` | `04_muestra.py` | ✅ | 50.000 |
| `data/processed/datos_entrenamiento.parquet` | `05_particiones.py` | ✅ | 50.000 |
| `data/processed/familias_laborales.parquet` | `07_familias_laborales.py` | ✅ | 23 |
| `data/processed/habilidades_por_familia.parquet` | `07_familias_laborales.py` | ✅ | 575 |
| `data/processed/relaciones_skills.parquet` | `07_familias_laborales.py` | ✅ | 18.916 |
| `data/processed/grafo_aristas.parquet` | `08_grafo_transiciones.py` | ✅ | 6.993 |
| `data/processed/transiciones_familias.parquet` | `08_grafo_transiciones.py` | ✅ | 110 |
| `data/app/familias.json` | `09_datos_graficas.py` | ✅ |  |
| `data/app/perfiles_ejemplo.json` | `09_datos_graficas.py` | ✅ |  |

## 2. Recálculo independiente desde los CSV originales

| Familia | Habilidad | Ofertas en la tabla | Ofertas recalculadas | Coincide |
|---|---|---|---|---|
| Enfermería | nursing | 79.516 | 79.516 | ✅ |
| Gerencia y dirección | communication | 72.860 | 72.860 | ✅ |
| Comercio y tiendas | customer service | 54.440 | 54.440 | ✅ |

## 3. Cálculos del simulador (perfiles de demostración)

| Perfil | Familia | Compatibilidad (JSON) | Recalculada a mano | Coincide |
|---|---|---|---|---|
| Ejemplo 1 - Analista junior | Datos y análisis | 53.3 % | 53.3 % | ✅ |
| Ejemplo 1 - Analista junior | Tecnología e informática | 22.3 % | 22.3 % | ✅ |
| Ejemplo 1 - Analista junior | Administración y oficina | 16.0 % | 16.0 % | ✅ |
| Ejemplo 1 - Analista junior | Datos y análisis (después) | 61.6 % | 61.6 % | ✅ |
| Ejemplo 2 - Auxiliar de restaurante | Restaurantes y alimentos | 48.8 % | 48.8 % | ✅ |
| Ejemplo 2 - Auxiliar de restaurante | Atención al cliente | 33.0 % | 33.0 % | ✅ |
| Ejemplo 2 - Auxiliar de restaurante | Comercio y tiendas | 27.2 % | 27.2 % | ✅ |
| Ejemplo 2 - Auxiliar de restaurante | Restaurantes y alimentos (después) | 61.6 % | 61.6 % | ✅ |
| Ejemplo 3 - Enfermera | Enfermería | 57.1 % | 57.1 % | ✅ |
| Ejemplo 3 - Enfermera | Salud y medicina | 28.1 % | 28.1 % | ✅ |
| Ejemplo 3 - Enfermera | Administración y oficina | 16.1 % | 16.1 % | ✅ |
| Ejemplo 3 - Enfermera | Enfermería (después) | 63.1 % | 63.1 % | ✅ |

## 4. Controles

| Control | Resultado |
|---|---|
| ofertas_por_familia_suman_total_postings | ✅ |
| recuento_familias_coincide | ✅ |
| recalculo_habilidad_por_familia_coincide | ✅ |
| particiones_suman_50000 | ✅ |
| particiones_sin_fuga | ✅ |
| simulador_coincide_a_mano | ✅ |

## 5. Figuras para el informe

- **Figura 1.** Ofertas por familia laboral — `reports/figuras/fig_ofertas_por_familia.png`
- **Figura 2.** Habilidades más pedidas — `reports/figuras/fig_top_habilidades.png`
- **Figura 3.** Etapas de preparación de los datos — `reports/figuras/fig_etapas_datos.png`
- **Figura 4.** Particiones — `reports/figuras/fig_particiones.png`
- **Figura 5.** Big Five — `reports/figuras/fig_big_five.png`

## 6. Limitaciones

- Datos de LinkedIn de enero de 2024, solo EE. UU., Reino Unido, Canadá y Australia.
- Las habilidades fueron extraídas automáticamente; tienen ruido (Jaccard 0,265 entre copias).
- Las familias se asignan con reglas de palabras clave; el 9,7 % de las ofertas queda en «Otros».
- Las transiciones son patrones observados en las ofertas, no garantías de empleo.