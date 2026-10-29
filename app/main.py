
"""API inicial de CareerTwin AI."""

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


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

    # Pendiente conectar el modelo real de Sofia
    return jsonify({
        "status": "model_unavailable",
        "models_loaded": False,
        "message": "El modelo de IA todavía no está disponible."
    }), 503


if __name__ == "__main__":
    app.run(debug=True)
