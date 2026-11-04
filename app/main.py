

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
    return jsonify({
        "status": "ok",
        "project": "CareerTwin AI",
        "models_loaded": False
    })


@app.get("/api/dashboard-data")
def dashboard_data():
    """Entrega los datos necesarios para las gráficas."""
    try:
        datos = {
            "familias": cargar_json("familias.json"),
            "transiciones": cargar_json("transiciones.json"),
            "mercado": cargar_json("mercado.json"),
            "perfiles": cargar_json("perfiles_ejemplo.json")
        }

        return jsonify(datos)

    except (FileNotFoundError, json.JSONDecodeError, OSError):
        app.logger.exception("No fue posible cargar los datos de las gráficas.")
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
            "error": "profile_text debe ser un texto no vacío."
        }), 400

    # Pendiente conectar el modelo real de Sofia.
    return jsonify({
        "status": "model_unavailable",
        "models_loaded": False,
        "message": "El modelo de IA todavía no está disponible."
    }), 503


if __name__ == "__main__":
    app.run(debug=True)
