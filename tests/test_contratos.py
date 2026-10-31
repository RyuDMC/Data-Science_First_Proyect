"""Contratos del dataset y de las decisiones que sostienen el reporte.

Estos tests nacen en verde con los datos actuales. Si alguien cambia un
conteo, un nombre o el orden del ranking sin querer, fallan aquí y no en la
portada.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SCORE = pd.read_csv(ROOT / "Data" / "clean_data" / "score_modelos.csv")
CAMPO = pd.read_csv(ROOT / "Data" / "registro_ubicaciones.csv")
EMPRESAS = list((ROOT / "Data" / "empresas").glob("*.jsonl"))


def test_ranking_tiene_las_filas_y_nombres_esperados():
    assert len(SCORE) == 41
    assert SCORE["modelo_norm"].nunique() == 40
    assert SCORE["score"].between(0, 1).all()
    assert (SCORE["n_anuncios_total"] > 0).all()
    assert not SCORE["modelo_norm"].str.contains("SIN IDENTIFICAR", na=False).any()


def test_ranking_tiene_rango_explicito_por_propulsion():
    """El podio se selecciona por `rank_propulsion`, no por posición del CSV."""
    assert "rank_propulsion" in SCORE.columns
    assert SCORE.groupby("propulsion")["rank_propulsion"].apply(
        lambda s: sorted(s.tolist()) == list(range(1, len(s) + 1))
    ).all()


def test_conteos_del_dataset():
    assert int(SCORE["repuestos_proxy"].fillna(0).sum()) == 9
    assert len(EMPRESAS) == 10
    assert len(pd.concat([pd.read_json(p, lines=True) for p in EMPRESAS],
                         ignore_index=True)) == 68
    assert len(CAMPO) == 30
    assert CAMPO["municipio"].nunique() == 5
    assert CAMPO["marca"].nunique() == 12
    canonicos = json.loads(
        (ROOT / "Data" / "modelos_canonicos.json").read_text(encoding="utf-8")
    )
    assert len(canonicos["por_url"]) == 137
    assert len(canonicos["excluidos"]) == 3


def test_top_por_anuncios_no_depende_del_orden():
    from reporte.data import top_por_anuncios

    fila = top_por_anuncios(SCORE)
    assert fila is not None
    assert fila["modelo_norm"] == "TOPMAQ BRIDERK 2026 GELPB"
    assert int(fila["n_anuncios_total"]) == 9

    desordenado = SCORE.sample(frac=1, random_state=7)
    assert top_por_anuncios(desordenado)["modelo_norm"] == fila["modelo_norm"]


def test_top_por_score_no_depende_del_orden():
    from reporte.data import top_por_score

    fila = top_por_score(SCORE)
    assert fila is not None
    assert fila["modelo_norm"] == "TOPMAQ BRIDERK 2026 GELPB"
    assert abs(float(fila["score"]) - 0.785540) < 1e-6


def test_top_por_propulsion_es_estable_y_no_mezcla_grupos():
    from reporte.data import top_por_propulsion

    electricos = top_por_propulsion(SCORE, "electrico", 3)
    assert electricos["modelo_norm"].tolist() == [
        "TOPMAQ BRIDERK 2026 GELPB",
        "ONEBOT CLASIC 2026",
        "KIVITOVA GELPB",
    ]
    assert (electricos["propulsion"] == "electrico").all()

    desordenado = SCORE.sample(frac=1, random_state=11)
    assert top_por_propulsion(desordenado, "electrico", 3)["modelo_norm"].tolist() == \
        electricos["modelo_norm"].tolist()


def test_resumen_usa_los_helpers_y_no_iloc():
    """Guarda contra volver a 'Lo más ofertado' con el primer score del CSV."""
    fuente = (ROOT / "reporte" / "pages" / "1_Resumen.py").read_text(encoding="utf-8")
    assert "top_por_anuncios" in fuente
    assert "top_por_score" in fuente
    assert "df_scores.iloc[0]" not in fuente


def test_sin_use_container_width():
    """Streamlit 1.66 deprecó el parámetro; el reemplazo es width='stretch'."""
    for path in (ROOT / "reporte").rglob("*.py"):
        if ".venv" in path.parts:
            continue
        assert "use_container_width" not in path.read_text(encoding="utf-8"), \
            f"queda use_container_width en {path}"


def test_dependencias_del_pipeline_estan_declaradas():
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "requests==" in req
    assert "beautifulsoup4==" in req
    assert "-r reporte/requirements.txt" in req
    dev = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    assert "-r requirements.txt" in dev
    assert "pytest==" in dev


def test_pipeline_documentado_en_app_incluye_los_pasos():
    app = (ROOT / "reporte" / "app.py").read_text(encoding="utf-8")
    for paso in ["crear_canonicos.py", "norm_modelo.py --migrar",
                 "sensibilidad.py", "generar_metadata.py"]:
        assert paso in app, f"falta {paso} en el pipeline de app.py"
