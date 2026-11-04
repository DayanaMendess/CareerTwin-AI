"""Pruebas del detector de habilidades (no necesitan los datos grandes)."""
import pytest

from src.data_pipeline.detector_habilidades import DetectorHabilidades, habilidades_del_perfil
from src.data_pipeline.habilidades_utils import normalizar_una

CATALOGO = {
    "python": "tecnica", "java": "tecnica", "javascript": "tecnica", "sql": "tecnica",
    "excel": "tecnica", "c++": "tecnica", "c#": "tecnica", ".net": "tecnica",
    "node.js": "tecnica", "project management": "tecnica", "management": "tecnica",
    "problem solving": "blanda", "communication": "blanda", "teamwork": "blanda",
    "microsoft word": "tecnica", "data analysis": "tecnica",
}


@pytest.fixture
def detector():
    return DetectorHabilidades(catalogo=CATALOGO)


def nombres(lista):
    return {d["habilidad"] for d in lista}


def test_terminos_tecnicos_se_conservan(detector):
    r = nombres(detector.detectar_en_texto("I use C++, C# and .NET with Node.js."))
    assert {"c++", "c#", ".net", "node.js"} <= r


def test_cplusplus_y_csharp_no_se_confunden(detector):
    assert nombres(detector.detectar_en_texto("Senior C# developer")) == {"c#"}
    assert nombres(detector.detectar_en_texto("Senior C++ developer")) == {"c++"}


def test_solo_terminos_completos(detector):
    r = nombres(detector.detectar_en_texto("Excellent JavaScript skills, T-SQL and Pythonic code"))
    assert "javascript" in r
    assert "java" not in r          # no dentro de javascript
    assert "excel" not in r         # no dentro de excellent
    assert "sql" not in r           # no dentro de t-sql
    assert "python" not in r        # no dentro de pythonic


def test_sinonimos_y_guiones(detector):
    r = nombres(detector.detectar_en_texto("Python3, MS Excel and problem-solving"))
    assert {"python", "excel", "problem solving"} <= r


def test_gana_la_coincidencia_mas_larga(detector):
    r = nombres(detector.detectar_en_texto("Experience in project management."))
    assert r == {"project management"}


def test_alias_ambiguo_no_se_detecta(detector):
    assert nombres(detector.detectar_en_texto("In a word, I love my job")) == set()
    assert nombres(detector.detectar_en_texto("Microsoft Word")) == {"microsoft word"}


def test_combinar_sin_duplicados_y_con_fuente(detector):
    r = detector.combinar_habilidades("SQL and Python", {"sql": 0.7, "teamwork": 0.4, "java": 0.05})
    fuentes = {d["habilidad"]: d["fuente"] for d in r}
    assert fuentes == {"sql": "texto+modelo", "python": "texto", "teamwork": "modelo"}
    assert len(r) == len(fuentes)                       # sin duplicados
    assert "java" not in fuentes                        # 0.05 < umbral 0.20


def test_combinar_acepta_lista_y_normaliza(detector):
    r = detector.combinar_habilidades("", ["Communication Skills", ("Python3", 0.9)])
    assert nombres(r) == {"communication", "python"}


def test_atajo_para_skill_gap(detector):
    assert habilidades_del_perfil("Teamwork and SQL", {"data analysis": 0.5},
                                  detector=detector) == {"teamwork", "sql", "data analysis"}


def test_normalizar_una_igual_que_la_version_con_pandas():
    pd = pytest.importorskip("pandas")
    from src.data_pipeline.habilidades_utils import normalizar_habilidades
    ejemplos = ["Python3", "  Problem-Solving. ", "Communication Skills", "MS Excel",
                "C++", "C#", ".NET", "Node.js", "T-SQL", "Data   Analysis"]
    assert [normalizar_una(e) for e in ejemplos] == normalizar_habilidades(pd.Series(ejemplos)).tolist()


def test_catalogo_real_si_existe():
    from src.data_pipeline.detector_habilidades import RUTA_CLASIFICACION
    if not RUTA_CLASIFICACION.exists():
        pytest.skip("falta reports/clasificacion_habilidades_revisada.csv")
    d = DetectorHabilidades()
    assert 200 <= len(d.catalogo) <= 230
    assert set(d.catalogo.values()) == {"tecnica", "blanda"}
