"""Auditoría inicial CSV en streaming. No hace merge y no modifica el dataset.

Ejecutar: python -m src.audit_data --limit 1000 (prueba)
          python -m src.audit_data --limit 0 (total)
"""
import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

INPUTS = (
    "linkedin_job_postings.csv",
    "job_skills.csv",
    "job_summary.csv",
)


def analyze_one(path: Path, limit: int) -> dict:
    nulls = Counter()
    rows = 0
    seen = set()
    duplicates = 0
    missing_key = 0
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        csv.field_size_limit(sys.maxsize if sys.maxsize < 2**31 else 2**30)
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        if "job_link" not in columns:
            raise ValueError(f"{path.name}: falta la columna job_link. Columnas: {columns}")
        for row in reader:
            rows += 1
            for field in columns:
                value = row.get(field)
                if value is None or not str(value).strip():
                    nulls[field] += 1
            key = str(row.get("job_link") or "").strip()
            if not key:
                missing_key += 1
            elif key in seen:
                duplicates += 1
            else:
                seen.add(key)
            if limit and rows >= limit:
                break
    return {
        "filas_analizadas": rows,
        "auditoria_parcial": bool(limit),
        "columnas": columns,
        "total_columnas": len(columns),
        "nulos_o_vacios_por_columna": {c: nulls[c] for c in columns},
        "porcentaje_vacios_por_columna": {
            c: round(100 * nulls[c] / rows, 3) if rows else 0 for c in columns
        },
        "job_link_vacio": missing_key,
        "job_link_duplicado": duplicates,
        "job_link_unicos_no_vacios": len(seen),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--limit", type=int, default=1000, help="0 = todas las filas")
    parser.add_argument("--output", type=Path, default=Path("reports/auditoria_dataset.json"))
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit debe ser 0 o mayor")
    missing = [f for f in INPUTS if not (args.data_dir / f).exists()]
    if missing:
        parser.error(f"Faltan archivos en {args.data_dir}: {', '.join(missing)}")
    result = {
        "creado_utc": datetime.now(timezone.utc).isoformat(),
        "fuente": "1.3M Linkedin Jobs & Skills (2024) Kaggle",
        "limite_por_archivo": args.limit,
        "advertencia": "Este reporte no mide filas post-merge ni la calidad de etiquetas NLP.",
        "archivos": {},
    }
    for file in INPUTS:
        print(f"Auditando {file} ...", flush=True)
        result["archivos"][file] = analyze_one(args.data_dir / file, args.limit)
        print(f"  filas: {result['archivos'][file]['filas_analizadas']:,}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Informe guardado: {args.output}")

if __name__ == "__main__":
    main()
