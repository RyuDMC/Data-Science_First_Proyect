"""Contratos del dataset y de las decisiones que sostienen el reporte.

Estos tests nacen en verde con los datos actuales. Si alguien cambia un
conteo, un nombre o el orden del ranking sin querer, fallan aquí y no en la
portada.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SCORE = pd.read_csv(ROOT / "Data" / "clean_data" / "score_modelos.csv")
CAMPO = pd.read_csv(ROOT / "Data" / "registro_ubicaciones.csv")
EMPRESAS = list((ROOT / "Data" / "empresas").glob("*.jsonl"))


def test_ranking_tiene_las_filas_y_nombres_esperados():
    assert len(SCORE) == 38
    assert SCORE["modelo_norm"].nunique() == 37
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
    assert int(SCORE["repuestos_proxy"].fillna(0).sum()) == 10
    assert len(EMPRESAS) == 10
    assert len(pd.concat([pd.read_json(p, lines=True) for p in EMPRESAS],
                         ignore_index=True)) == 64
    assert len(CAMPO) == 30
    assert CAMPO["municipio"].nunique() == 5
    assert CAMPO["marca"].nunique() == 12
    canonicos = json.loads(
        (ROOT / "Data" / "modelos_canonicos.json").read_text(encoding="utf-8")
    )
    assert len(canonicos["por_url"]) == 133
    assert len(canonicos["excluidos"]) == 7


def test_top_por_anuncios_no_depende_del_orden():
    from reporte.data import top_por_anuncios

    fila = top_por_anuncios(SCORE)
    assert fila is not None
    assert fila["modelo_norm"] == "TOPMAQ BRIDERK 2026 GELPB"
    assert int(fila["n_anuncios_total"]) == 9

    desordenado = SCORE.sample(frac=1, random_state=7)
    assert top_por_anuncios(desordenado)["modelo_norm"] == fila["modelo_norm"]


def test_top_por_score_es_por_propulsion_y_no_global():
    """El mejor score se elige DENTRO de un grupo, nunca mezclando grupos.

    JINPENG (híbrido) tiene un score mayor que TOPMAQ (eléctrico), pero sus
    escalas no son comparables: la función exige la propulsión.
    """
    from reporte.data import top_por_score

    electrico = top_por_score(SCORE, "electrico")
    assert electrico is not None
    assert electrico["modelo_norm"] == "TOPMAQ BRIDERK 2026 GELPB"

    desordenado = SCORE.sample(frac=1, random_state=7)
    assert top_por_score(desordenado, "electrico")["modelo_norm"] == \
        electrico["modelo_norm"]

    hibrido = top_por_score(SCORE, "hibrido")
    assert hibrido["modelo_norm"] == "JINPENG"
    # El híbrido no debe aparecer al pedir eléctricos.
    assert hibrido["propulsion"] == "hibrido"


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
    assert 'top_por_propulsion(df_scores, "electrico"' in fuente
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


def test_sensibilidad_reproduce_el_ranking_oficial():
    """El escenario base no puede tener NaN ni un orden distinto al oficial."""
    sens = pd.read_csv(ROOT / "Data" / "clean_data" / "sensibilidad_pesos.csv")
    base = sens[sens["escenario"] == "base"]
    assert len(base) == len(SCORE)
    assert base["score"].notna().all(), "el escenario base tiene scores NaN"

    m = SCORE.merge(base, on=["propulsion", "modelo_norm"], suffixes=("", "_sens"))
    assert len(m) == len(SCORE)
    assert np.allclose(m["score"], m["score_sens"], atol=1e-6)
    assert (m["rank_propulsion"] == m["rank"]).all()

    res = pd.read_csv(ROOT / "Data" / "clean_data" / "sensibilidad_resumen.csv")
    assert res["rank_base"].notna().all()
    m2 = SCORE.merge(res, on=["propulsion", "modelo_norm"], suffixes=("", "_res"))
    assert (m2["rank_base"] == m2["rank_propulsion"]).all()


def test_pareto_no_devuelve_puntos_dominados():
    """Con X=autonomía e Y=carga, la frontera real es TOPMAQ y ONEBOT."""
    from reporte.data import frontera_pareto

    df = SCORE[(SCORE["propulsion"] == "electrico")
               & SCORE["autonomia_km"].notna()
               & SCORE["carga_kg"].notna()].copy()
    frontera = frontera_pareto(df, "autonomia_km", "carga_kg")
    assert set(frontera["modelo_norm"]) == {
        "TOPMAQ BRIDERK 2026 GELPB", "ONEBOT CLASIC 2026",
    }
    for _, r in frontera.iterrows():
        dominado = df[
            (df["autonomia_km"] >= r["autonomia_km"])
            & (df["carga_kg"] >= r["carga_kg"])
            & ((df["autonomia_km"] > r["autonomia_km"])
               | (df["carga_kg"] > r["carga_kg"]))
        ]
        assert dominado.empty, f"{r['modelo_norm']} está dominado"


def test_texto_de_sensibilidad_no_niega_el_cambio_de_podio():
    from reporte.data import texto_sensibilidad_electrico

    sens = pd.read_csv(ROOT / "Data" / "clean_data" / "sensibilidad_pesos.csv")
    res = pd.read_csv(ROOT / "Data" / "clean_data" / "sensibilidad_resumen.csv")
    texto = texto_sensibilidad_electrico(sens, res).lower()
    assert "el podio, no" not in texto
    assert "podio" in texto
    # Debe decir cuántos escenarios cambian, no una frase fija.
    assert "escenarios" in texto


def test_resumen_no_presenta_un_mejor_global():
    fuente = (ROOT / "reporte" / "pages" / "1_Resumen.py").read_text(encoding="utf-8")
    assert "top_por_score(df_scores)" not in fuente
    assert 'top_por_propulsion(df_scores, "electrico"' in fuente


def test_paginas_no_mezclan_grupos_en_el_podio():
    pagina7 = (ROOT / "reporte" / "pages" / "7_Mejor_Opcion.py").read_text(encoding="utf-8")
    assert "top 10 global" not in pagina7.lower()
    assert 'df.sort_values("score", ascending=False).head(10)' not in pagina7
    pagina6 = (ROOT / "reporte" / "pages" / "6_Contendientes.py").read_text(encoding="utf-8")
    assert "get_top_models" in pagina6
    assert ".head(top_n)" not in pagina6

