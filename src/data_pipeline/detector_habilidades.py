"""
Detector de habilidades del perfil (Catalina)

Complementa la red neuronal de Sofia:
  - La red predice 100 habilidades (vocabulario piloto).
  - Este módulo busca en el texto las 219 habilidades válidas del catálogo
    (técnicas y blandas de reports/clasificacion_habilidades_revisada.csv)
    más algunas habilidades técnicas EXTRA (C++, C#, .NET, Node.js) que solo se
    detectan en el texto: NO forman parte del vocabulario de entrenamiento de la red.
  - combinar_habilidades() une las dos listas sin duplicados y marca de dónde
    sale cada habilidad: "texto", "modelo" o "texto+modelo".

Reglas acordadas con Sofia:
  1. Usa la normalización de habilidades_utils.py (normalizar_una), que conserva
     C++, C#, .NET y Node.js.
  2. Busca TÉRMINOS COMPLETOS: "java" no aparece dentro de "javascript",
     "excel" no aparece dentro de "excellent" y "sql" no aparece dentro de "t-sql".
  3. Si dos habilidades se solapan, gana la más larga: en "project management"
     se detecta "project management", no también "management".
  4. Cada resultado dice su fuente.

Uso:
    from src.data_pipeline.detector_habilidades import DetectorHabilidades
    detector = DetectorHabilidades()
    en_texto = detector.detectar_en_texto(texto_del_cv)
    perfil = detector.combinar_habilidades(texto_del_cv, predicciones_del_modelo)
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

try:
    from .habilidades_utils import SINONIMOS, normalizar_una
except ImportError:  # cuando se ejecuta como script
    from habilidades_utils import SINONIMOS, normalizar_una

RAIZ = Path(__file__).resolve().parents[2]
RUTA_CLASIFICACION = RAIZ / "reports" / "clasificacion_habilidades_revisada.csv"
CATEGORIAS_VALIDAS = {"tecnica", "blanda"}

# Técnicas adicionales que se detectan solo si están escritas explícitamente.
# No cambian el vocabulario de 100 habilidades del modelo.
HABILIDADES_EXTRA = {"c++": "tecnica", "c#": "tecnica", ".net": "tecnica", "node.js": "tecnica"}
ALIAS_EXTRA = {
    "cpp": "c++", "c sharp": "c#", "dotnet": ".net", "dot net": ".net",
    "asp.net": ".net", "asp.net core": ".net", ".net core": ".net",
    "nodejs": "node.js", "node js": "node.js",
}

# Sinónimos de UNA palabra muy común que darían falsos positivos en un CV
# ("in a word", "my computer", "a presentation"). La forma completa sí se busca
# ("microsoft word", "computer skills", "presentation skills").
ALIAS_AMBIGUOS = {"word", "computer", "presentation"}

# Antes de la habilidad no puede haber letra, número, guion, + ni #.
# Después no puede haber letra, número, + ni #  (sí puede venir un punto o una coma).
_ANTES = r"(?<![\w\-+#])"
_DESPUES = r"(?![\w+#])"


def _texto_comparable(texto: str) -> str:
    """Minúsculas, guiones raros unificados y espacios simples (mismas reglas que la normalización)."""
    t = str(texto).lower()
    t = re.sub(r"[‐-―]", "-", t)
    return re.sub(r"\s+", " ", t)


def cargar_catalogo(ruta: Path = RUTA_CLASIFICACION, incluir_extra: bool = True) -> dict[str, str]:
    """habilidad -> categoría (técnicas y blandas de la revisión manual + extras)."""
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        catalogo = {normalizar_una(fila["habilidad"]): fila["categoria_final"]
                    for fila in csv.DictReader(f)
                    if fila["categoria_final"] in CATEGORIAS_VALIDAS}
    if incluir_extra:
        for h, cat in HABILIDADES_EXTRA.items():
            catalogo.setdefault(h, cat)
    return catalogo


class DetectorHabilidades:
    def __init__(self, catalogo: dict[str, str] | None = None):
        self.catalogo = catalogo if catalogo is not None else cargar_catalogo()
        self.alias = self._construir_alias()
        # Una sola expresión con todas las formas, de la más larga a la más corta,
        # para que en cada posición gane la coincidencia más larga.
        formas = sorted(self.alias, key=len, reverse=True)
        self._patron = re.compile(_ANTES + "(" + "|".join(map(re.escape, formas)) + ")" + _DESPUES)

    def _construir_alias(self) -> dict[str, str]:
        """Forma escrita -> habilidad canónica."""
        alias = {}
        for h in self.catalogo:
            alias[h] = h
            if " " in h:                                   # "problem solving"
                alias.setdefault(h.replace(" ", "-"), h)   # "problem-solving"
        for variante, canonica in ALIAS_EXTRA.items():
            if canonica in self.catalogo:
                alias.setdefault(variante, canonica)       # "nodejs" -> "node.js"
        for variante, canonica in SINONIMOS.items():
            canonica = normalizar_una(canonica)
            if canonica in self.catalogo and variante not in ALIAS_AMBIGUOS:
                alias.setdefault(variante, canonica)       # "ms excel" -> "excel"
        return alias

    def detectar_en_texto(self, texto: str) -> list[dict]:
        """Habilidades del catálogo que aparecen escritas en el texto."""
        encontradas = {}
        for m in self._patron.finditer(_texto_comparable(texto)):
            h = self.alias[m.group(1)]
            if h not in encontradas:
                encontradas[h] = {"habilidad": h, "categoria": self.catalogo[h],
                                  "fuente": "texto", "probabilidad": None,
                                  "evidencia": m.group(1),
                                  "solo_detector": h in HABILIDADES_EXTRA}
        return list(encontradas.values())

    def combinar_habilidades(self, texto: str, predicciones_modelo=None,
                             umbral: float = 0.20) -> list[dict]:
        """Une lo detectado en el texto con lo que predice la red, sin duplicados.

        predicciones_modelo puede ser:
          - la salida de predict_skills.py: lista de dicts {"habilidad", "score_modelo"}
          - dict {habilidad: probabilidad}
          - lista de (habilidad, probabilidad)
          - lista de habilidades (ya filtradas por el modelo)
        Las predicciones con probabilidad menor que `umbral` se descartan
        (0,20 es el umbral elegido por Sofia en validación).
        """
        resultado = {d["habilidad"]: d for d in self.detectar_en_texto(texto)}

        if predicciones_modelo is None:
            predicciones_modelo = []
        if isinstance(predicciones_modelo, dict):
            pares = list(predicciones_modelo.items())
        else:
            pares = [_a_par(p) for p in predicciones_modelo]

        for nombre, prob in pares:
            if prob is not None and prob < umbral:
                continue
            h = normalizar_una(nombre)
            prob = None if prob is None else round(float(prob), 4)
            if h in resultado:
                resultado[h]["fuente"] = "texto+modelo"
                resultado[h]["probabilidad"] = prob
            else:
                resultado[h] = {"habilidad": h, "categoria": self.catalogo.get(h, ""),
                                "fuente": "modelo", "probabilidad": prob, "evidencia": None,
                                "solo_detector": False}

        orden = {"texto+modelo": 0, "texto": 1, "modelo": 2}
        return sorted(resultado.values(),
                      key=lambda d: (orden[d["fuente"]], -(d["probabilidad"] or 0), d["habilidad"]))


def _a_par(p):
    """Convierte una predicción a (habilidad, probabilidad)."""
    if isinstance(p, dict):                       # formato de predict_skills.py
        nombre = p.get("habilidad")
        prob = p.get("score_modelo", p.get("probabilidad"))
        if nombre is None:
            raise ValueError(f"Predicción sin campo 'habilidad': {p}")
        return nombre, prob
    if isinstance(p, (tuple, list)):
        return p[0], (p[1] if len(p) > 1 else None)
    return p, None


def habilidades_del_perfil(texto: str, predicciones_modelo=None, umbral: float = 0.20,
                           detector: DetectorHabilidades | None = None) -> set[str]:
    """Atajo para el Skill Gap: solo el conjunto de nombres de habilidades."""
    detector = detector or DetectorHabilidades()
    return {d["habilidad"] for d in detector.combinar_habilidades(texto, predicciones_modelo, umbral)}


if __name__ == "__main__":
    detector = DetectorHabilidades()
    cv = ("Data analyst with 3 years of experience in SQL, Python3 and MS Excel. "
          "Built dashboards in Power BI, used C++ and C# for small tools and .NET APIs. "
          "Strong problem-solving and project management skills. Excellent communication. "
          "I know JavaScript but not Java.")
    modelo = [{"habilidad": "data analysis", "score_modelo": 0.81},   # formato de predict_skills.py
              {"habilidad": "sql", "score_modelo": 0.64},
              {"habilidad": "communication", "score_modelo": 0.55},
              {"habilidad": "teamwork", "score_modelo": 0.12}]
    print(f"Catálogo: {len(detector.catalogo)} habilidades\n")
    print("CV de ejemplo:\n ", cv, "\n")
    for d in detector.combinar_habilidades(cv, modelo):
        p = "" if d["probabilidad"] is None else f"  p={d['probabilidad']}"
        e = "" if d["evidencia"] is None else f'  (texto: "{d["evidencia"]}")'
        print(f"  {d['fuente']:13} {d['habilidad']:22} {d['categoria']:7}{p}{e}")
