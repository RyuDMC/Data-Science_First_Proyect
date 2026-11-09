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
    # 40 filas desde el split JINPENG (decisión del usuario, 2026-11-06):
    # los 3 híbridos JINPENG son 3 filas (una por URL) y desaparece la fila
    # agregada n=3. Los únicos nombres repetidos siguen siendo los productos
    # anunciados con el mismo nombre en dos propulsiones (STAR).
    assert len(SCORE) == 40
    assert SCORE["modelo_norm"].nunique() == 39
    assert SCORE["score"].notna().all()
    assert SCORE["score"].between(0, 1).all()
    assert (SCORE["n_anuncios_total"] > 0).all()
    assert not SCORE["modelo_norm"].str.contains("SIN IDENTIFICAR", na=False).any()


def test_score_es_reponderado_y_conserva_el_imputado():
    """El score oficial usa solo criterios presentes; 0.5 queda como referencia."""
    assert "score_imputado" in SCORE.columns
    assert "precio_comparable" in SCORE.columns

    # 33 modelos con precio USD (el split JINPENG añade 2: 3 anuncios →
    # 3 filas con precio propio); 7 del catálogo VEDCA quedan fuera.
    assert int(SCORE["precio_comparable"].sum()) == 33
    assert int((~SCORE["precio_comparable"]).sum()) == 7
    assert SCORE.loc[~SCORE["precio_comparable"], "precio_usd"].isna().all()
    assert SCORE.loc[SCORE["precio_comparable"], "precio_usd"].notna().all()

    # El score imputado no puede ser idéntico al re-ponderado en todos los casos:
    # si lo fuera, la nueva regla no estaría haciendo nada.
    assert not np.allclose(SCORE["score"], SCORE["score_imputado"])

    # Reproducción independiente del score re-ponderado y del imputado.
    cols = ["precio_usd_norm", "autonomia_km_norm", "carga_kg_norm",
            "legalidad_norm", "repuestos_norm"]
    pesos = np.array([0.40, 0.25, 0.20, 0.10, 0.05])
    M = SCORE[cols].to_numpy(dtype=float)
    presente = ~np.isnan(M)
    den = (presente * pesos).sum(axis=1)
    esperado = np.nansum(M * pesos, axis=1) / den
    assert np.allclose(SCORE["score"], esperado, atol=1e-9)
    imputado = np.where(np.isnan(M), 0.5, M) @ pesos
    assert np.allclose(SCORE["score_imputado"], imputado, atol=1e-9)


def test_ranking_principal_excluye_modelos_sin_precio():
    """Los rankings de precio nunca deben incluir modelos con `precio_usd` NaN."""
    from reporte.data import top_por_propulsion, top_por_score

    for prop in SCORE["propulsion"].unique():
        top = top_por_propulsion(SCORE, prop, 10)
        assert top["precio_comparable"].all(), f"{prop} incluye un modelo sin precio"
        assert top["precio_usd"].notna().all()

    # El top general del grupo tampoco puede ser un modelo sin precio.
    for prop in SCORE["propulsion"].unique():
        fila = top_por_score(SCORE, prop)
        assert fila is not None
        assert bool(fila["precio_comparable"]) is True

    # Y con `solo_precio=False` sí aparecen, para poder mostrarlos aparte.
    todos = top_por_propulsion(SCORE, "electrico", 100, solo_precio=False)
    assert (~todos["precio_comparable"]).any()


def test_ranking_tiene_rango_explicito_por_propulsion():
    """El podio se selecciona por `rank_propulsion`, no por posición del CSV."""
    assert "rank_propulsion" in SCORE.columns
    assert SCORE.groupby("propulsion")["rank_propulsion"].apply(
        lambda s: sorted(s.tolist()) == list(range(1, len(s) + 1))
    ).all()


def test_conteos_del_dataset():
    # 9 (antes 10): con la fila agregada JINPENG, `repuestos_proxy` acreditaba
    # "más de una fuente" a tres productos distintos que el grupo fusionaba;
    # desde el split (2026-11-06) cada híbrido es un producto de UNA fuente
    # (proxy = aparece en ≥2 fuentes con la misma identidad).
    assert int(SCORE["repuestos_proxy"].fillna(0).sum()) == 9
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
    # Desde el split JINPENG (2026-11-06) el mejor híbrido es el 1000W:
    # solo tiene 3 criterios presentes (precio, legalidad, motor) y el score
    # re-ponderado no imputa; el 1500W (5 criterios) queda en 0.707.
    assert hibrido["modelo_norm"] == "JINPENG HIBRIDO 1000W"
    # El híbrido no debe aparecer al pedir eléctricos.
    assert hibrido["propulsion"] == "hibrido"


def test_top_por_propulsion_es_estable_y_no_mezcla_grupos():
    from reporte.data import top_por_propulsion

    electricos = top_por_propulsion(SCORE, "electrico", 3)
    assert electricos["modelo_norm"].tolist() == [
        "TOPMAQ BRIDERK 2026 GELPB",
        "ONEBOT CLASIC 2026",
        "CHILWEE",
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

    # El escenario `imputado_05` reconstruye el método anterior y debe coincidir
    # con la columna histórica `score_imputado`.
    viejo = sens[sens["escenario"] == "imputado_05"]
    mv = SCORE.merge(viejo, on=["propulsion", "modelo_norm"], suffixes=("", "_viejo"))
    assert len(mv) == len(SCORE)
    assert np.allclose(mv["score_imputado"], mv["score_viejo"], atol=1e-6)

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


def test_documentacion_cubre_las_fuentes():
    """Cada dominio presente en los datos debe estar en docs/etica_y_legal.md.

    Es el test que sostiene la revisión de robots.txt/ToS del 2026-11-06: si se
    añade una fuente nueva veya se cambian las rutas, la tabla §2a deja de
    cubrir y el test obliga a re-hacer la comprobación antes de pushes.
    """
    fuente = (ROOT / "docs" / "etica_y_legal.md").read_text(encoding="utf-8")
    # La revisión debe estar fechada y no puede seguir marcada como pendiente.
    assert "2026-11-06" in fuente

    from urllib.parse import urlparse

    urls = []
    for ruta in ["Data/clean_data/anuncios_triciclos.jsonl",
                 "Data/clean_data/anuncios_facebook.jsonl"]:
        urls += pd.read_json(ROOT / ruta, lines=True)["url"].dropna().astype(str).tolist()
    for p in ROOT.glob("Data/empresas/*.jsonl"):
        urls += pd.read_json(p, lines=True)["url"].dropna().astype(str).tolist()

    dominios = sorted({urlparse(u).netloc for u in urls if u})
    assert dominios, "no se encontraron URLs en los datos"
    for dom in dominios:
        assert dom in fuente, f"El dominio {dom} no está documentado en etica_y_legal.md §2a"

