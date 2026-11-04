"""
09 - Datos validados para las gráficas de la app (Catalina) — día 9

Prepara archivos JSON pequeños que Flask puede cargar directo, para:
  Gráfica 1 - Habilidades presentes y faltantes: habilidades más pedidas por familia.
  Gráfica 2 - Compatibilidad profesional: cobertura de un perfil frente a cada familia.
  Gráfica 3 - Comparativa de escenarios: antes y después de aprender una habilidad.
Además genera estadísticas del mercado y resultados de PERFILES DE EJEMPLO para
comparar (claramente marcados como demostración, no como usuarios reales).

Cada indicador indica su FUENTE y su DENOMINADOR, y se validan automáticamente.

Salidas:
  data/app/mercado.json                 estadísticas generales del mercado
  data/app/familias.json                habilidades por familia (para gráficas 1 y 2)
  data/app/transiciones.json            transiciones con similitud >= 0,2 (para gráfica 3)
  data/app/perfiles_ejemplo.json        resultados de 3 perfiles de demostración
  reports/validacion_datos_graficas.json
"""
import json
from pathlib import Path

import pandas as pd

MIN_SIMILITUD = 0.2
TOP_MERCADO = 20

RAIZ = Path(__file__).resolve().parents[2]
PROC = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"
APP = RAIZ / "data" / "app"
APP.mkdir(parents=True, exist_ok=True)

FUENTE = "1.3M LinkedIn Jobs & Skills (2024), Kaggle — ofertas de enero de 2024 (EE. UU., UK, Canadá, Australia)"

familias = pd.read_parquet(PROC / "familias_laborales.parquet")
hpf = pd.read_parquet(PROC / "habilidades_por_familia.parquet")
rel = pd.read_parquet(PROC / "relaciones_skills.parquet")
trans = pd.read_parquet(PROC / "transiciones_familias.parquet")
cls = pd.read_csv(REPORTES / "clasificacion_habilidades_revisada.csv", keep_default_na=False)
CATEGORIA = dict(zip(cls["habilidad"], cls["categoria_final"]))

total_ofertas = int(familias["ofertas"].sum())
ofertas_con_habilidades = int(hpf.drop_duplicates("familia")["ofertas_familia"].sum())

# ---------------------------------------------------------------- Mercado
print("[1/4] Estadísticas del mercado...")
glob = hpf.drop_duplicates("habilidad")[["habilidad", "pct_global"]]
glob = glob.sort_values("pct_global", ascending=False)
glob["categoria"] = glob["habilidad"].map(CATEGORIA)

mercado = {
    "fuente": FUENTE,
    "total_ofertas": total_ofertas,
    "ofertas_con_habilidades": ofertas_con_habilidades,
    "ofertas_por_familia": [
        {"familia": f, "ofertas": int(o), "porcentaje": round(o / total_ofertas * 100, 2)}
        for f, o in familias.sort_values("ofertas", ascending=False)[["familia", "ofertas"]].values],
    "habilidades_mas_pedidas": [
        {"habilidad": h, "categoria": c, "porcentaje": round(float(p), 2)}
        for h, p, c in glob.head(TOP_MERCADO)[["habilidad", "pct_global", "categoria"]].values],
    "denominadores": {
        "ofertas_por_familia.porcentaje": "total de ofertas del dataset (total_ofertas)",
        "habilidades_mas_pedidas.porcentaje": "ofertas que tienen al menos una habilidad válida",
    },
}
ruta_bf = REPORTES / "big_five_resumen.json"
if ruta_bf.exists():
    bf = json.loads(ruta_bf.read_text(encoding="utf-8"))
    mercado["big_five_pct_ofertas"] = bf["pct_ofertas_de_la_muestra_que_piden_el_rasgo"]
    mercado["denominadores"]["big_five_pct_ofertas"] = "muestra de 50.000 ofertas (datos_entrenamiento)"

# ---------------------------------------------------------------- Familias
print("[2/4] Habilidades por familia...")
fams_json = []
for f, g in hpf.groupby("familia"):
    g = g.sort_values("ofertas", ascending=False)
    fila = familias[familias["familia"] == f].iloc[0]
    fams_json.append({
        "familia": f,
        "ofertas": int(fila["ofertas"]),
        "ofertas_con_habilidades": int(g["ofertas_familia"].iloc[0]),
        "titulos_frecuentes": list(fila["titulos_frecuentes"]),
        "habilidades": [
            {"habilidad": h, "categoria": CATEGORIA.get(h, ""), "pct_en_familia": round(float(p), 2),
             "pct_mercado": round(float(pm), 2), "lift": round(float(l), 2)}
            for h, p, pm, l in g[["habilidad", "pct_en_familia", "pct_global", "lift"]].values],
    })
fams_json.sort(key=lambda x: -x["ofertas"])
familias_app = {
    "fuente": FUENTE,
    "denominadores": {
        "pct_en_familia": "ofertas de esa familia que tienen al menos una habilidad válida",
        "pct_mercado": "todas las ofertas con al menos una habilidad válida",
        "lift": "pct_en_familia / pct_mercado (> 1: la familia la pide más que el mercado)",
    },
    "familias": fams_json,
}

# ---------------------------------------------------------------- Transiciones
t = trans[trans["similitud"] >= MIN_SIMILITUD].copy()
transiciones_app = {
    "fuente": FUENTE,
    "criterio": f"solo transiciones con similitud >= {MIN_SIMILITUD}",
    "nota": "Patrones observados en las ofertas; no garantizan que el cambio de carrera sea posible.",
    "transiciones": [
        {"origen": r.familia_origen, "destino": r.familia_destino, "similitud": float(r.similitud),
         "compartidas": [h for h in r.compartidas_ejemplo.split(" | ") if h],
         "a_aprender": [h for h in r.habilidades_a_aprender.split(" | ") if h]}
        for r in t.itertuples()],
}


# ---------------------------------------------------------------- Perfiles de ejemplo
print("[3/4] Resultados de perfiles de ejemplo...")
def cobertura(perfil: set, g: pd.DataFrame) -> dict:
    """% del 'peso' de las habilidades de la familia que el perfil ya tiene.
    Peso = pct_en_familia x max(lift, 1): pesan más las habilidades muy pedidas
    y, sobre todo, las PROPIAS de la familia. Así, tener solo habilidades
    genéricas (communication, teamwork) no hace parecer compatible con todo."""
    g = g.assign(peso=g["pct_en_familia"] * g["lift"].clip(lower=1))
    total = g["peso"].sum()
    tiene = g[g["habilidad"].isin(perfil)]
    falta = g[~g["habilidad"].isin(perfil)].sort_values("peso", ascending=False)
    return {
        "cobertura_pct": round(float(tiene["peso"].sum() / total * 100), 1) if total else 0.0,
        "presentes": tiene["habilidad"].tolist(),
        "faltantes_principales": falta["habilidad"].head(5).tolist(),
    }


PERFILES = {
    "Ejemplo 1 - Analista junior": {"sql", "excel", "data analysis", "communication", "python"},
    "Ejemplo 2 - Auxiliar de restaurante": {"customer service", "food preparation", "cash handling",
                                            "teamwork", "food safety"},
    "Ejemplo 3 - Enfermera": {"nursing", "patient care", "medication administration",
                              "communication", "teamwork"},
}
grupos = {f: g for f, g in hpf[hpf["familia"] != "Otros"].groupby("familia")}
perfiles_json = []
for nombre, habs in PERFILES.items():
    resultados = sorted(({"familia": f, **cobertura(habs, g)} for f, g in grupos.items()),
                        key=lambda x: -x["cobertura_pct"])
    mejor = resultados[0]
    # Escenario: aprender la habilidad faltante más pedida de su mejor familia
    nueva = mejor["faltantes_principales"][0] if mejor["faltantes_principales"] else None
    despues = cobertura(habs | {nueva}, grupos[mejor["familia"]]) if nueva else None
    perfiles_json.append({
        "perfil": nombre,
        "habilidades": sorted(habs),
        "top_familias": resultados[:5],
        "escenario": None if not nueva else {
            "familia": mejor["familia"], "aprender": nueva,
            "cobertura_antes": mejor["cobertura_pct"], "cobertura_despues": despues["cobertura_pct"]},
    })
perfiles_app = {
    "aviso": "PERFILES DE DEMOSTRACIÓN creados para probar las gráficas; no son usuarios reales.",
    "metodo": ("cobertura = suma del peso de las habilidades que el perfil tiene / suma del peso de "
               "las 25 habilidades principales de la familia; peso = pct_en_familia x max(lift, 1)"),
    "perfiles": perfiles_json,
}

# ---------------------------------------------------------------- Validación
print("[4/4] Validando porcentajes y denominadores...")
checks = {
    "suma_ofertas_familias_igual_total": int(familias["ofertas"].sum()) == total_ofertas,
    "pct_familias_suma_100": abs(sum(x["porcentaje"] for x in mercado["ofertas_por_familia"]) - 100) < 0.5,
    "pct_en_familia_entre_0_y_100": bool(hpf["pct_en_familia"].between(0, 100).all()),
    "pct_global_entre_0_y_100": bool(hpf["pct_global"].between(0, 100).all()),
    "ofertas_habilidad_menor_o_igual_ofertas_familia": bool((hpf["ofertas"] <= hpf["ofertas_familia"]).all()),
    "ofertas_con_habilidades_menor_o_igual_total": ofertas_con_habilidades <= total_ofertas,
    "lift_coherente": bool(((hpf["pct_en_familia"] / hpf["pct_global"] - hpf["lift"]).abs() < 0.05).all()),
    "similitud_entre_0_y_1": bool(trans["similitud"].between(0, 1.0001).all()),
    "cobertura_entre_0_y_100": all(0 <= r["cobertura_pct"] <= 100
                                   for p in perfiles_json for r in p["top_familias"]),
    "escenario_no_baja_cobertura": all(p["escenario"]["cobertura_despues"] >= p["escenario"]["cobertura_antes"]
                                       for p in perfiles_json if p["escenario"]),
}
validacion = {
    "todo_correcto": all(checks.values()),
    "controles": checks,
    "notas": {
        "dos_denominadores": (f"{total_ofertas:,} ofertas en total; {ofertas_con_habilidades:,} tienen "
                              "al menos una habilidad válida. Los % de familias usan el total; los % de "
                              "habilidades usan solo las ofertas con habilidades."),
        "transiciones_filtradas": f"{len(t)} de {len(trans)} transiciones tienen similitud >= {MIN_SIMILITUD}",
    },
}

for nombre, datos in [("mercado", mercado), ("familias", familias_app),
                      ("transiciones", transiciones_app), ("perfiles_ejemplo", perfiles_app)]:
    (APP / f"{nombre}.json").write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
(REPORTES / "validacion_datos_graficas.json").write_text(
    json.dumps(validacion, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(validacion, indent=2, ensure_ascii=False))
for p in perfiles_json:
    e = p["escenario"]
    print(f"\n{p['perfil']}")
    for r in p["top_familias"][:3]:
        print(f"   {r['familia']}: {r['cobertura_pct']}%  (le falta: {', '.join(r['faltantes_principales'][:3])})")
    if e:
        print(f"   Si aprende '{e['aprender']}': {e['familia']} pasa de {e['cobertura_antes']}% a {e['cobertura_despues']}%")
