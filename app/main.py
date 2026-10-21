"""Aplicación mínima para validar el trabajo en equipo (sin predicciones ficticias)."""
from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/health")
def health():
    return jsonify({"status": "ok", "project": "CareerTwin AI", "models_loaded": False})

if __name__ == "__main__":
    app.run(debug=True)
