"""Identidad de producto: las decisiones del usuario, convertidas en tests.

La identidad vive en `Data/modelos_canonicos.json` y en `codes/norm_modelo.py`.
Si alguien fusiona dos productos que el usuario separó, o reintroduce una
errata, esto falla.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SCORE = pd.read_csv(ROOT / "Data" / "clean_data" / "score_modelos.csv")
CANON = json.loads(
    (ROOT / "Data" / "modelos_canonicos.json").read_text(encoding="utf-8")
)


def _modelos_canonicos() -> list[str]:
    return [str(v.get("modelo") or "").upper() for v in CANON["por_url"].values()]


def test_no_quedan_erratas_en_el_ranking():
    nombres = SCORE["modelo_norm"].astype(str).str.upper()
    assert not nombres.str.contains("JINPEING", na=False).any()
    assert not nombres.str.contains("PASAJ", na=False).any()


def test_oim_agrega_las_dos_ofertas():
    oim = SCORE[SCORE["modelo_norm"] == "OIM GELPB"]
    assert len(oim) == 1
    assert int(oim.iloc[0]["n_anuncios_total"]) == 2


def test_star_electrico_y_hibrido_son_productos_distintos():
    star = SCORE[SCORE["modelo_norm"] == "STAR"]
    assert set(star["propulsion"]) == {"electrico", "hibrido"}
    assert len(star) == 2


def test_rally_y_rally_carga_siguen_separados():
    modelos = set(_modelos_canonicos())
    assert {"RALLY", "RALLY CARGA", "RALLY CARGA 800"} <= modelos
    # El nombre de uso no debe volver al nombre canónico.
    assert not any("PASAJ" in m for m in modelos)


def test_jinpen_y_jinpeng_estan_documentados():
    """JINPEN/JINPENG comparten marca, pero son productos distintos.

    El alias de marca (`normalizar_marca`) los une a nivel marca; la identidad
    de producto los mantiene separados porque las specs difieren. La auditoría
    está en `opencode/auditoria_jinpen.md`; no se fusionan sin decisión.
    """
    from codes.norm_modelo import normalizar_marca

    assert normalizar_marca("JINPEN") == "JINPENG"
    assert normalizar_marca("JINPENG") == "JINPENG"
    assert {"JINPEN", "JINPENG"} <= set(SCORE["modelo_norm"])
    assert (ROOT / "opencode" / "auditoria_jinpen.md").exists()


def test_canonicos_no_reintroducen_erratas():
    modelos = _modelos_canonicos()
    assert not any("JINPEING" in m for m in modelos)
