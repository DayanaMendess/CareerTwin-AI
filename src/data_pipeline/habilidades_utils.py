
import pandas as pd

# Textos que significan "sin habilidades".
# Decisión explícita (ver docs/INFORME_CALIDAD_DATOS.md, sección 4).
VALORES_VACIOS = {"", "none", "n/a", "na", "null", "nan"}

# Una coma separa habilidades SOLO si no está dentro de paréntesis:
# "Microsoft Office (Word, Excel), SQL" -> ["Microsoft Office (Word, Excel)", "SQL"]
SEPARADOR = r",(?![^()]*\))"

# Sinónimos: variante -> forma canónica.
# Empieza pequeño a propósito; se amplía después de la revisión manual.
SINONIMOS = {
    # Palabras pegadas por el scraper (perdieron el guion)
    "problemsolving": "problem solving",
    "problemsolving skills": "problem solving",
    "decisionmaking": "decision making",
    "decisionmaking skills": "decision making",
    "detailoriented": "detail oriented",
    # Variantes con guion
    "problem-solving": "problem solving",
    "decision-making": "decision making",
    "detail-oriented": "detail oriented",
    "self-motivated": "self motivated",
    "multi-tasking": "multitasking",
    # Misma habilidad con y sin "skills" (se quita cuando se entiende igual)
    "management skills": "management",
    "project management skills": "project management",
    "communication skills": "communication",
    "basic math skills": "basic math",
    "collaboration skills": "collaboration",
    "critical thinking skills": "critical thinking",
    "customer service skills": "customer service",
    "leadership skills": "leadership",
    "listening skills": "listening",
    "math skills": "math",
    "negotiation skills": "negotiation",
    "problem solving skills": "problem solving",
    "research skills": "research",
    "sales skills": "sales",
    "teamwork skills": "teamwork",
    "time management skills": "time management",
    "verbal communication skills": "verbal communication",
    "writing skills": "writing",
    "written communication skills": "written communication",
    # Casos en que la forma con "skills" es más clara (la otra es ambigua)
    "computer": "computer skills",
    "presentation": "presentation skills",
    "organization skills": "organizational skills",
    # Otras variantes de escritura
    "team work": "teamwork",
    "health care": "healthcare",
    # Herramientas
    "word": "microsoft word",
    "ms word": "microsoft word",
    "budget management": "budgeting",
    "python programming": "python",
    "python scripting": "python",
    "python3": "python",
    "python 3": "python",
    "python (programming language)": "python",
    "microsoft excel": "excel",
    "ms excel": "excel",
    "microsoft office suite": "microsoft office",
    "ms office": "microsoft office",
}


def separar_habilidades(serie: pd.Series) -> pd.Series:
    """'Python, SQL' -> una fila por habilidad, respetando comas entre paréntesis."""
    return serie.str.split(SEPARADOR, regex=True).explode().str.strip()


def normalizar_habilidades(serie: pd.Series) -> pd.Series:
    """Convierte cada habilidad a su forma canónica."""
    s = serie.astype(str).str.lower()
    # Unificar los guiones "raros" de Unicode (–, —) en un guion normal (-)
    s = s.str.replace(r"[\u2010-\u2015]", "-", regex=True)
    # Varios espacios seguidos -> uno solo
    s = s.str.replace(r"\s+", " ", regex=True)
    # Quitar espacios, comas, comillas y asteriscos sobrantes al inicio y al final.
    # NO se quita el punto inicial (".net") ni signos internos (c++, c#, node.js).
    s = s.str.strip(" ,;:'\"*")
    # Quitar solo los puntos FINALES ("teamwork." -> "teamwork")
    s = s.str.replace(r"\.+$", "", regex=True)
    # Aplicar sinónimos (si no está en el diccionario, se deja igual)
    return s.map(SINONIMOS).fillna(s)


# ---------------------------------------------------------------------
# Demostración: solo se ejecuta si corres este archivo directamente
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("SEPARAR:")
    texto = pd.Series(["Microsoft Office (Word, Excel), SQL, Teamwork"])
    for h in separar_habilidades(texto):
        print(f"   {h}")

    print("\nNORMALIZAR:")
    ejemplos = pd.Series(["Python3", "  Problem-Solving. ", "Communication Skills",
                          "MS Excel", "C++", "C#", ".NET", "Node.js", "T-SQL"])
    for antes, despues in zip(ejemplos, normalizar_habilidades(ejemplos)):
        print(f"   {antes!r:25} -> {despues!r}")