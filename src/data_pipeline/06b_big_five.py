"""
06b - Habilidades blandas según el modelo Big Five (Catalina)

Sugerencia del profesor: organizar las habilidades blandas con el modelo de
personalidad de los Cinco Grandes (Big Five / OCEAN):
  Apertura (Openness)                 curiosidad, creatividad, pensar distinto
  Responsabilidad (Conscientiousness) organización, disciplina, cumplir
  Extraversión (Extraversion)         comunicarse, liderar, relacionarse
  Amabilidad (Agreeableness)          cooperar, trabajar en equipo, empatía
  Estabilidad emocional (Neuroticism, polo opuesto)  manejar presión y estrés

IMPORTANTE: el Big Five describe rasgos de personalidad, no habilidades.
Aquí cada habilidad blanda se asigna al rasgo con el que más se relaciona.
Es una aproximación para organizar y explicar los resultados, NO una medición
de la personalidad del usuario.

Salidas:
  reports/big_five_habilidades.csv   habilidad -> rasgo
  reports/big_five_resumen.json      cuántas habilidades y ofertas hay por rasgo
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
PROC = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

RASGOS_EN = {
    "Apertura": "Openness",
    "Responsabilidad": "Conscientiousness",
    "Extraversión": "Extraversion",
    "Amabilidad": "Agreeableness",
    "Estabilidad emocional": "Emotional stability (low Neuroticism)",
}

BIG_FIVE = {
    # Apertura: pensar, analizar, crear y adaptarse a lo nuevo
    "problem solving": "Apertura", "critical thinking": "Apertura",
    "analytical skills": "Apertura", "analytical thinking": "Apertura",
    "creativity": "Apertura", "innovation": "Apertura",
    "strategic thinking": "Apertura", "adaptability": "Apertura",
    "flexibility": "Apertura", "writing": "Apertura",
    "written communication": "Apertura",
    # Responsabilidad: orden, cumplimiento, disciplina y confiabilidad
    "attention to detail": "Responsabilidad", "detail oriented": "Responsabilidad",
    "accuracy": "Responsabilidad", "time management": "Responsabilidad",
    "ability to meet deadlines": "Responsabilidad", "organization": "Responsabilidad",
    "organizational skills": "Responsabilidad", "planning": "Responsabilidad",
    "prioritization": "Responsabilidad", "multitasking": "Responsabilidad",
    "reliability": "Responsabilidad", "accountability": "Responsabilidad",
    "professionalism": "Responsabilidad", "strong work ethic": "Responsabilidad",
    "ethics": "Responsabilidad", "integrity": "Responsabilidad",
    "confidentiality": "Responsabilidad", "initiative": "Responsabilidad",
    "motivation": "Responsabilidad", "selfmotivation": "Responsabilidad",
    "decision making": "Responsabilidad", "independent work": "Responsabilidad",
    "ability to work independently": "Responsabilidad",
    # Extraversión: comunicarse, liderar, influir y relacionarse
    "communication": "Extraversión", "verbal communication": "Extraversión",
    "oral communication": "Extraversión", "interpersonal communication": "Extraversión",
    "public speaking": "Extraversión", "presentation skills": "Extraversión",
    "leadership": "Extraversión", "team leadership": "Extraversión",
    "team building": "Extraversión", "negotiation": "Extraversión",
    "networking": "Extraversión", "delegation": "Extraversión",
    "positive attitude": "Extraversión",
    # Amabilidad: cooperar, ayudar, escuchar y trabajar con otros
    "teamwork": "Amabilidad", "team player": "Amabilidad",
    "collaboration": "Amabilidad", "team collaboration": "Amabilidad",
    "ability to work independently and as part of a team": "Amabilidad",
    "interpersonal skills": "Amabilidad", "relationship building": "Amabilidad",
    "empathy": "Amabilidad", "compassion": "Amabilidad",
    "active listening": "Amabilidad", "conflict resolution": "Amabilidad",
    "coaching": "Amabilidad", "mentoring": "Amabilidad",
    "coordination": "Amabilidad",
    # Estabilidad emocional: manejar la presión y el estrés
    "stress management": "Estabilidad emocional",
    "ability to work under pressure": "Estabilidad emocional",
    "ability to work in a fastpaced environment": "Estabilidad emocional",
}

cls = pd.read_csv(REPORTES / "clasificacion_habilidades_revisada.csv", keep_default_na=False)
blandas = cls[cls["categoria_final"] == "blanda"][["habilidad", "ofertas"]].copy()

sin_rasgo = sorted(set(blandas["habilidad"]) - set(BIG_FIVE))
if sin_rasgo:
    raise SystemExit(f"Habilidades blandas sin rasgo asignado: {sin_rasgo}")

vocab = json.loads((REPORTES / "skills_vocab.json").read_text(encoding="utf-8"))
en_vocab = set(vocab["etiquetas"])

blandas["rasgo"] = blandas["habilidad"].map(BIG_FIVE)
blandas["rasgo_en"] = blandas["rasgo"].map(RASGOS_EN)
blandas["en_vocabulario_piloto"] = blandas["habilidad"].isin(en_vocab)
blandas = blandas.sort_values(["rasgo", "ofertas"], ascending=[True, False])
blandas.to_csv(REPORTES / "big_five_habilidades.csv", index=False, encoding="utf-8-sig")

# Cuántas ofertas de la muestra piden al menos una habilidad de cada rasgo
datos = pd.read_parquet(PROC / "datos_entrenamiento.parquet", columns=["etiquetas"])
ofertas_por_rasgo = {}
for rasgo in RASGOS_EN:
    habs = set(blandas.loc[blandas["rasgo"] == rasgo, "habilidad"])
    tiene = datos["etiquetas"].map(lambda l: any(h in habs for h in l))
    ofertas_por_rasgo[rasgo] = round(float(np.mean(tiene) * 100), 2)

resumen = {
    "modelo": "Big Five (OCEAN)",
    "advertencia": ("Asignación aproximada de habilidades blandas a rasgos; "
                    "no mide la personalidad de nadie."),
    "habilidades_blandas_revisadas": len(blandas),
    "habilidades_por_rasgo": blandas["rasgo"].value_counts().to_dict(),
    "habilidades_por_rasgo_en_vocabulario_piloto":
        blandas[blandas["en_vocabulario_piloto"]]["rasgo"].value_counts().to_dict(),
    "pct_ofertas_de_la_muestra_que_piden_el_rasgo": ofertas_por_rasgo,
    "rasgos": {r: sorted(blandas.loc[blandas["rasgo"] == r, "habilidad"]) for r in RASGOS_EN},
}
(REPORTES / "big_five_resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False),
                                               encoding="utf-8")
print(json.dumps({k: v for k, v in resumen.items() if k != "rasgos"}, indent=2, ensure_ascii=False))
