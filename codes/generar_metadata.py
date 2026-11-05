#!/usr/bin/env python3
"""
Metadatos del dataset: conteos y cortes en un solo sitio.

Por qué existe
--------------
Las cifras del proyecto (70 anuncios, 38 filas de ranking, 64 fichas, 30
observaciones, 10/38 con repuestos…) se escribían a mano en la portada, el
README, Método y Limitaciones. Ya habían divergido dos veces (42 vs 41; 30 vs
68). Este script las calcula desde los datos y escribe `Data/metadata.json`; el
reporte y los tests leen de ahí.

Qué se calcula y qué se declara
-------------------------------
- **Conteos**: siempre desde los archivos (`clean_data/`, `Data/empresas/`,
  `registro_ubicaciones.csv`, `score_modelos.csv`). Si cambian los datos,
  cambian solos.
- **Cortes**: catálogos y campo salen de la fecha máxima de captura. El corte
  de anuncios es una **decisión de proyecto** (fecha de congelación), no un
  campo: `fecha_captura` llega hasta 2026-10-11 y `fecha_anuncio` hasta
  2025-11-09, así que se declara en `CORTE_ANUNCIOS` y el test lo contrasta
  contra el README.
- **Resultados**: top-3 por propulsión y marca más observada en calle, para que
  el README no tenga que escribir scores ni porcentajes a mano.
- **Procedencia**: opcional (`--procedencia`). Por defecto el archivo es
  determinista: dos corridas con los mismos datos producen el mismo JSON. La
  fecha y el commit se añaden solo cuando se piden y `--check` los ignora.

Uso
---
    python3 codes/generar_metadata.py
    python3 codes/generar_metadata.py --check   # falla si conteos/cortes/resultados cambiaron
    python3 codes/generar_metadata.py --procedencia  # añade fecha/commit (no determinista)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data"
CLEAN_DIR = DATA / "clean_data"
EMPRESAS_DIR = DATA / "empresas"
SALIDA = DATA / "metadata.json"

ANUNCIOS = [CLEAN_DIR / "anuncios_triciclos.jsonl",
            CLEAN_DIR / "anuncios_facebook.jsonl"]
CAMPO = DATA / "registro_ubicaciones.csv"
CAMPO_RESUMEN = CLEAN_DIR / "campo_resumen.csv"
SCORE = CLEAN_DIR / "score_modelos.csv"
CANONICOS = DATA / "modelos_canonicos.json"

# Decisión de proyecto: fecha de congelación del dataset de anuncios.
# No se deduce de los datos (ver docstring).
CORTE_ANUNCIOS = "2026-10-19"

ESQUEMA = 1


def _leer_jsonl(rutas):
    """Concatena varios JSONL; falla con un mensaje claro si falta alguno."""
    faltan = [str(p.relative_to(ROOT)) for p in rutas if not p.exists()]
    if faltan:
        sys.exit(f"Faltan archivos de datos: {faltan}. "
                 "Ejecuta antes el pipeline de scraping.")
    return pd.concat([pd.read_json(p, lines=True) for p in rutas],
                     ignore_index=True)


def _fecha_max(serie) -> str:
    """Fecha ISO (YYYY-MM-DD) del máximo de una columna de fechas."""
    fechas = pd.to_datetime(serie, errors="coerce").dropna()
    if fechas.empty:
        sys.exit("No hay fechas válidas para calcular el corte.")
    return fechas.max().date().isoformat()


def _commit() -> str | None:
    """Commit corto en el momento de generar (solo con --procedencia)."""
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           cwd=ROOT, capture_output=True, text=True, check=True)
        return r.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _resultados(score: pd.DataFrame, campo_resumen: pd.DataFrame) -> dict:
    """Top-3 por propulsión y marca más vista en calle.

    Son resultados, no conteos: cambian si cambia el scoring o el campo. El
    README los cita; este bloque es su fuente y el test los contrasta.
    """
    top_por_propulsion = {}
    for prop, grupo in score.groupby("propulsion", sort=True):
        top = grupo.sort_values(
            ["score", "modelo_norm"], ascending=[False, True], kind="mergesort",
        ).head(3)
        top_por_propulsion[str(prop)] = [
            {"modelo": str(r.modelo_norm), "score": round(float(r.score), 6)}
            for r in top.itertuples()
        ]

    if campo_resumen.empty or "n_campo" not in campo_resumen.columns:
        campo_top = None
    else:
        fila = campo_resumen.sort_values(
            ["n_campo", "marca_norm"], ascending=[False, True], kind="mergesort",
        ).iloc[0]
        campo_top = {
            "marca": str(fila["marca_norm"]),
            "n": int(fila["n_campo"]),
            "total": int(campo_resumen["n_campo"].sum()),
            "pct": round(float(fila["pct_campo"]), 1),
            "ic95_bajo": round(float(fila["ic95_bajo"]), 1),
            "ic95_alto": round(float(fila["ic95_alto"]), 1),
        }
    return {
        "top_por_propulsion": top_por_propulsion,
        "campo_marca_top": campo_top,
    }


def calcular() -> dict:
    """Devuelve el metadata completo (sin escribir)."""
    anuncios = _leer_jsonl(ANUNCIOS)
    empresas = _leer_jsonl(sorted(EMPRESAS_DIR.glob("*.jsonl")))
    campo = pd.read_csv(CAMPO)
    campo_resumen = pd.read_csv(CAMPO_RESUMEN)
    score = pd.read_csv(SCORE)
    canonicos = json.loads(CANONICOS.read_text(encoding="utf-8"))

    conteos = {
        "anuncios": int(len(anuncios)),
        "anuncios_scraper": int(len(pd.read_json(ANUNCIOS[0], lines=True))),
        "anuncios_facebook": int(len(pd.read_json(ANUNCIOS[1], lines=True))),
        "fuentes_anuncios": int(anuncios["fuente"].nunique()),
        "modelos_ranking": int(len(score)),
        "nombres_modelo": int(score["modelo_norm"].nunique()),
        "modelos_con_repuestos": int(score["repuestos_proxy"].fillna(0).sum()),
        "fichas_empresa": int(len(empresas)),
        "empresas": int(len(sorted(EMPRESAS_DIR.glob("*.jsonl")))),
        "productos_canonicos": int(len(canonicos["por_url"])),
        "productos_excluidos": int(len(canonicos["excluidos"])),
        "observaciones_campo": int(len(campo)),
        "municipios_campo": int(campo["municipio"].nunique()),
        "marcas_campo": int(campo["marca"].nunique()),
    }
    cortes = {
        # `anuncios` es la fecha de congelación declarada (decisión de
        # proyecto), no la última captura. Se publican ambas para que el
        # reporte no sugiera que hay datos hasta la fecha de congelación.
        "anuncios": CORTE_ANUNCIOS,
        "anuncios_captura": _fecha_max(anuncios["fecha_captura"]),
        "catalogos": _fecha_max(empresas["fecha_captura"]),
        "campo": _fecha_max(campo["fecha"]),
    }
    return {
        "esquema": ESQUEMA,
        "conteos": conteos,
        "cortes": cortes,
        "resultados": _resultados(score, campo_resumen),
    }


def _json(meta: dict) -> str:
    return json.dumps(meta, ensure_ascii=False, indent=2) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Genera Data/metadata.json.")
    ap.add_argument("--check", action="store_true",
                    help="no escribe: falla si conteos/cortes/resultados no coinciden")
    ap.add_argument("--procedencia", action="store_true",
                    help="añade fecha y commit (no determinista; no se commitea)")
    args = ap.parse_args()

    meta = calcular()
    if args.procedencia:
        meta["procedencia"] = {
            "generado": datetime.now().astimezone().isoformat(timespec="seconds"),
            "commit": _commit(),
            "script": "codes/generar_metadata.py",
        }

    if args.check:
        if not SALIDA.exists():
            sys.exit(f"[check] FALTA {SALIDA.relative_to(ROOT)}. "
                     "Ejecuta python3 codes/generar_metadata.py")
        actual = json.loads(SALIDA.read_text(encoding="utf-8"))
        # `procedencia` es opcional y no forma parte del contrato.
        estable = ("esquema", "conteos", "cortes", "resultados")
        diferencias = [k for k in estable if actual.get(k) != meta[k]]
        if diferencias:
            sys.exit("[check] DESACTUALIZADO: cambian "
                     f"{', '.join(diferencias)}. Regenera metadata.json.")
        print(f"[check] OK: conteos, cortes y resultados de "
              f"{SALIDA.relative_to(ROOT)} coinciden con los datos")
        return

    SALIDA.write_text(_json(meta), encoding="utf-8")
    c = meta["conteos"]
    print(f"-> Escrito: {SALIDA.relative_to(ROOT)}")
    print(f"   {c['anuncios']} anuncios ({c['fuentes_anuncios']} fuentes) · "
          f"{c['modelos_ranking']} filas de ranking ({c['nombres_modelo']} nombres)")
    print(f"   {c['fichas_empresa']} fichas de {c['empresas']} empresas · "
          f"{c['productos_canonicos']} productos canónicos "
          f"({c['productos_excluidos']} excluidos) · "
          f"{c['observaciones_campo']} observaciones de campo "
          f"({c['municipios_campo']} municipios, {c['marcas_campo']} marcas)")
    print(f"   Cortes: anuncios {meta['cortes']['anuncios']} "
          f"(captura hasta {meta['cortes']['anuncios_captura']}) · "
          f"catálogos {meta['cortes']['catalogos']} · campo {meta['cortes']['campo']}")
    top_e = meta["resultados"]["top_por_propulsion"].get("electrico", [])
    if top_e:
        print("   Top eléctrico: " + " > ".join(
            f"{r['modelo']} ({r['score']:.3f})" for r in top_e))
    campo_top = meta["resultados"]["campo_marca_top"]
    if campo_top:
        print(f"   Campo: {campo_top['marca']} "
              f"({campo_top['n']}/{campo_top['total']}, {campo_top['pct']:.1f}%)")


if __name__ == "__main__":
    main()
