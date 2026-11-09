

"""API de CareerTwin AI."""

import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.json.ensure_ascii = False

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "app"


def cargar_json(nombre):
    """Carga un archivo JSON desde data/app."""
    ruta = DATA_DIR / nombre

    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
@app.get("/api/health")
def health():
    try:
        from src.predict_skills import cargar_recursos
        cargar_recursos()
        modelos_cargados = True
    except Exception:
        app.logger.exception("No fue posible cargar el modelo")
        modelos_cargados = False

    return jsonify({
        "status": "ok",
        "project": "CareerTwin AI",
        "models_loaded": modelos_cargados
    })


@app.get("/api/dashboard-data")
def dashboard_data():
    """Entrega los datos necesarios para las grÃ¡ficas."""
    try:
        datos = {
            "familias": cargar_json("familias.json"),
            "transiciones": cargar_json("transiciones.json"),
            "mercado": cargar_json("mercado.json"),
            "perfiles": cargar_json("perfiles_ejemplo.json")
        }

        return jsonify(datos)

    except (FileNotFoundError, json.JSONDecodeError, OSError):
        app.logger.exception("No fue posible cargar los datos de las grÃ¡ficas.")
        return jsonify({
            "error": "No fue posible cargar los datos del dashboard."
        }), 500


@app.post("/api/analyze-profile")
def analyze_profile():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Se requiere un objeto JSON."
        }), 400

    profile_text = data.get("profile_text")

    if not isinstance(profile_text, str) or not profile_text.strip():
        return jsonify({
            "error": "profile_text debe ser un texto no vacÃ­o."
        }), 400

    
    # Ejecutar el modelo real y el detector de habilidades.
    try:
        from .servicio_ia import analizar_perfil

        resultado = analizar_perfil(profile_text)
        return jsonify(resultado), 200

    except (FileNotFoundError, ImportError, OSError):
        app.logger.exception("Servicio de IA no disponible")
        return jsonify({
            "status": "model_unavailable",
            "models_loaded": False,
            "message": "El modelo de IA no estÃ¡ disponible."
        }), 503

    except Exception:
        app.logger.exception("Error al analizar el perfil")
        return jsonify({
            "error": "No fue posible analizar el perfil."
        }), 500


@app.post("/api/fraud-risk")
def fraud_risk():
    """Analiza señales de posible fraude en una oferta laboral."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Se requiere un objeto JSON."
        }), 400

    job_text = data.get("job_text")

    if not isinstance(job_text, str) or not job_text.strip():
        return jsonify({
            "error": "job_text debe ser un texto no vacío."
        }), 400

    if len(job_text.strip()) > 20000:
        return jsonify({
            "error": "La oferta supera los 20000 caracteres."
        }), 400

    try:
        from .servicio_fraude import analizar_oferta

        resultado = analizar_oferta(job_text)
        return jsonify(resultado), 200

    except (FileNotFoundError, ImportError, OSError):
        app.logger.exception("Modelo de fraude no disponible")
        return jsonify({
            "status": "model_unavailable",
            "message": "El detector de fraude no está disponible."
        }), 503

    except Exception:
        app.logger.exception("Error al analizar la oferta")
        return jsonify({
            "error": "No fue posible analizar la oferta."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)

