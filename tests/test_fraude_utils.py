"""Pruebas del procesamiento compartido de Fraud Shield (no necesitan el dataset)."""
from src.data_pipeline.fraude_utils import (clave_duplicado, limpiar_texto,
                                            texto_para_modelo, unir_campos)


def test_marcadores_de_emscad_se_convierten():
    t = limpiar_texto("Write to #EMAIL_0b13a2cf# or see #URL_86fd830a# / #PHONE_ab12#")
    assert "[EMAIL]" in t and "[URL]" in t and "[PHONE]" in t
    assert "#" not in t


def test_correos_enlaces_y_telefonos_reales():
    t = limpiar_texto("Mail hr@acme.com, visit https://acme.com/jobs or call +1 (555) 123-4567")
    assert t.count("[EMAIL]") == 1 and t.count("[URL]") == 1 and t.count("[PHONE]") == 1
    assert "acme.com" not in t


def test_telefono_completo_sin_restos():
    for tel in ["+1 (555) 123-4567.", "(555) 123-4567", "555.123.4567", "+57 300 123 4567"]:
        t = limpiar_texto(f"Call {tel} now")
        assert "[PHONE]" in t
        assert not any(c.isdigit() for c in t), t


def test_numeros_que_no_son_telefonos_se_conservan():
    t = limpiar_texto("Salary 50000 per year, 2 years of experience, ISO 9001")
    assert "[PHONE]" not in t and "50000" in t


def test_html_y_terminos_tecnicos():
    t = limpiar_texto("<p>Skills: C++, C#, .NET &amp; Node.js</p>")
    assert t == "Skills: C++, C#, .NET & Node.js"


def test_mismo_texto_en_entrenamiento_y_en_la_app():
    fila_emscad = {"title": "Clerk", "description": "Contact #EMAIL_abc123# or #URL_ff01#.",
                   "requirements": "", "benefits": "Weekly pay"}
    pegado_en_app = "Clerk\nContact jobs@empresa.co or https://empresa.co.\nWeekly pay"
    assert texto_para_modelo(unir_campos(fila_emscad)) == texto_para_modelo(pegado_en_app)
    assert texto_para_modelo(pegado_en_app) == "clerk contact [EMAIL] or [URL]. weekly pay"


def test_no_usa_columnas_con_fuga():
    texto = unir_campos({"title": "Clerk", "has_company_logo": "0", "job_id": "17",
                         "location": "US, TX, Houston", "description": "Work"})
    assert texto == "Clerk\nWork"


def test_clave_agrupa_casi_iguales_y_separa_tecnicos():
    a = clave_duplicado("Senior C++ Developer. Apply at #URL_aa11#!")
    b = clave_duplicado("senior c++ developer   apply at https://x.com")
    c = clave_duplicado("Senior C# Developer. Apply at #URL_aa11#!")
    assert a == b
    assert a != c
