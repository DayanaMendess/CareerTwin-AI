"""
Procesamiento compartido de ofertas para Fraud Shield (Catalina).

Lo usan IGUAL el entrenamiento (13_preparar_fraude.py) y la aplicación
(app/servicio_fraude.py), para que el modelo reciba en la app el mismo tipo de
texto con el que se entrenó. No necesita pandas: solo la librería estándar.

Funciones:
  unir_campos(oferta)       -> une title, description, requirements y benefits
                               (las mismas columnas que usa src/preparar_fraude.py)
  texto_para_modelo(texto)  -> limpia el texto y pone los marcadores [URL] [EMAIL] [PHONE].
                               En la app: texto_para_modelo(job_text) antes de predict_proba.
  clave_duplicado(texto)    -> clave para agrupar ofertas repetidas o casi iguales

Recomendaciones de reports/auditoria_fraude.md que aplica:
  * Marcadores de EMSCAD (#URL_…#, #EMAIL_…#, #PHONE_…#) -> [URL], [EMAIL], [PHONE].
  * Correos, enlaces y teléfonos reales (los que pega un usuario) -> los mismos marcadores,
    así el modelo no aprende un formato que solo existe en EMSCAD.
  * Solo texto: NO usa job_id, has_company_logo, has_questions, telecommuting ni la
    ubicación, porque no existen cuando el usuario pega una oferta.
  * C++, C#, .NET y Node.js se conservan.
"""
from __future__ import annotations

import hashlib
import html
import re

# Campos de texto que también tendrá una oferta pegada por el usuario
# Mismas columnas que src/preparar_fraude.py; la app recibe todo en un solo texto
CAMPOS_TEXTO = ["title", "description", "requirements", "benefits"]
# Columnas de EMSCAD que NO deben llegar al modelo (fuga o no existen en la app)
COLUMNAS_EXCLUIDAS = ["job_id", "has_company_logo", "has_questions", "telecommuting",
                      "location", "department", "salary_range", "company_profile"]
_EMSCAD = re.compile(r"#\s*(URL|EMAIL|PHONE)_[0-9a-fA-F]+\s*#")
_HTML = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_URL = re.compile(r"(?:https?://|www\.)\S+?(?=[.,;:!?)\]]*(?:\s|$))")
# Teléfonos: 7 a 15 dígitos con separadores habituales; exige al menos 7 dígitos
_PHONE = re.compile(r"(?<![\w])\+?\(?\d[\d\s().\-]{5,}\d(?!\d)")
_ESPACIOS = re.compile(r"[ \t ]+")
_LINEAS = re.compile(r"\n\s*\n+")

_TECNICOS = [(re.compile(r"(?i)(?<![\w])c\+\+"), " cplusplus "),
             (re.compile(r"(?i)(?<![\w])c#"), " csharp "),
             (re.compile(r"(?i)(?<![\w])f#"), " fsharp "),
             (re.compile(r"(?i)\.net\b"), " dotnet "),
             (re.compile(r"(?i)node\.js\b"), " nodejs ")]


def _es_vacio(valor) -> bool:
    return valor is None or str(valor).strip().lower() in {"", "nan", "none", "null", "n/a", "na"}


def _reemplazar_telefono(m: re.Match) -> str:
    digitos = sum(c.isdigit() for c in m.group(0))
    return "[PHONE]" if 7 <= digitos <= 15 else m.group(0)


def limpiar_texto(texto) -> str:
    """Texto limpio con los marcadores del proyecto. Conserva mayúsculas y términos técnicos."""
    if _es_vacio(texto):
        return ""
    t = html.unescape(str(texto))
    t = _EMSCAD.sub(lambda m: f" [{m.group(1).upper()}] ", t)   # marcadores de EMSCAD
    t = _HTML.sub(" ", t)
    t = _EMAIL.sub(" [EMAIL] ", t)                              # primero correos...
    t = _URL.sub(" [URL] ", t)                                  # ...luego enlaces...
    t = _PHONE.sub(_reemplazar_telefono, t)                     # ...y teléfonos
    t = _ESPACIOS.sub(" ", t)
    t = _LINEAS.sub("\n", t)
    t = re.sub(r" +([.,;:!?])(?=\s|$)", r"\1", t)
    return "\n".join(linea.strip() for linea in t.split("\n")).strip()


def unir_campos(oferta: dict) -> str:
    """Une los campos de texto de una fila de EMSCAD (dict) en un solo texto,
    igual que el texto que un usuario pega completo en la app."""
    partes = [str(oferta.get(c)).strip() for c in CAMPOS_TEXTO if not _es_vacio(oferta.get(c))]
    return "\n".join(partes)


def texto_para_modelo(texto) -> str:
    """Texto final que recibe el modelo, tanto al entrenar como en la app:
    limpio, con marcadores, en minúsculas y con espacios simples."""
    t = limpiar_texto(texto).lower()
    t = re.sub(r"\[(url|email|phone)\]", lambda m: f"[{m.group(1).upper()}]", t)
    t = re.sub(r"\s+", " ", t)
    return re.sub(r" ([.,;:!?])(?=\s|$)", r"\1", t).strip()


def clave_duplicado(texto: str) -> str:
    """Clave para agrupar ofertas iguales o casi iguales (cambian mayúsculas,
    espacios, puntuación, enlaces o correos). Protege C++, C#, .NET y Node.js."""
    t = limpiar_texto(texto)
    t = re.sub(r"\[(URL|EMAIL|PHONE)\]", " ", t)
    for patron, palabra in _TECNICOS:
        t = patron.sub(palabra, t)
    t = re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
    return hashlib.sha1(t.encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    fila_emscad = {
        "title": "Data Entry Clerk (Remote)",
        "description": "<p>Earn $500/day from home! Contact #EMAIL_0b13a2cf# or "
                       "visit #URL_86fd830a#. Call #PHONE_77ab01#.</p> Skills: C++, C#, .NET",
        "requirements": None,
        "benefits": "Weekly pay",
    }
    pegado_en_app = ("Data Entry Clerk (Remote)\nEarn $500/day from home! Contact jobs@fast.co or "
                     "visit https://fast.co. Call +1 (555) 123-4567. Skills: C++, C#, .NET\nWeekly pay")
    print("EMSCAD:", texto_para_modelo(unir_campos(fila_emscad)))
    print("App:   ", texto_para_modelo(pegado_en_app))
