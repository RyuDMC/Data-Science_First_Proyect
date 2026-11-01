"""Identidad de producto: las decisiones del usuario, convertidas en tests.

La identidad vive en `Data/modelos_canonicos.json` y en `codes/norm_modelo.py`.
Si alguien fusiona dos productos que el usuario separó, o reintroduce una
errata, esto falla.
"""

import json
import re
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
    erratas = nombres.str.contains(
        r"(?<![A-Z])JINPEN(?![A-Z])|JIMPEG|JIMPENG", regex=True
    ).any()
    assert not erratas


def test_oim_agrega_las_dos_ofertas():
    oim = SCORE[SCORE["modelo_norm"] == "OIM GELPB"]
    assert len(oim) == 1
    assert int(oim.iloc[0]["n_anuncios_total"]) == 2


def test_star_electrico_y_hibrido_son_productos_distintos():
    star = SCORE[SCORE["modelo_norm"] == "STAR"]
    assert set(star["propulsion"]) == {"electrico", "hibrido"}
    assert len(star) == 2


def test_rally_sin_especificacion_en_el_nombre():
    """La spec no forma parte del nombre (decisión del usuario, 2026-10-31).

    Las 5 fichas RALLY siguen separadas por URL; la variante de 800 kg se
    distingue con el campo `carga_kg`, no con "RALLY 800".
    """
    modelos = set(_modelos_canonicos())
    assert "RALLY" in modelos
    assert "RALLY 800" not in modelos
    # El nombre de uso no debe volver al nombre canónico.
    assert not any("PASAJ" in m for m in modelos)


UNIDADES = {"AH", "AMP", "AMPERIOS", "W", "WATT", "WATTS", "V", "CC", "KG",
            "KGS", "KM", "KM/H", "4T", "VOLT", "VOLTIOS"}


def test_nombres_sin_descriptores_ni_grafias_duplicadas():
    """Los aditamentos, el uso, la propulsión y las specs no son parte del
    nombre.

    Tampoco las grafías duplicadas que el usuario unificó (MINGHONG/MIGHONG,
    MOSHOZUKI/MISHOZUKI, FUGUIQUAN/FUGUIGUAN) ni las erratas del grupo
    JINPENG (JINPEING/JIMPEG/JINPEN/JIMPENG).
    """
    prohibidos = [
        "PANEL", "SOLAR", "EXTENSOR", "FOTOVOLTAICO",       # aditamentos
        "MZ PRODUCTS",                                      # marca repetida
        "MINGHONG", "MOSHOZUKI", "FUGUIQUAN",               # grafía duplicada
        "JIMPEG", "JIMPENG", "JINPEING", "JEINPEING",       # erratas JINPENG
        "TRICICLO", "TAXI",                                 # genérico / uso
    ]
    errata_jinpen = re.compile(r"(?<![A-Z])JINPEN(?![A-Z])")
    for v in CANON["por_url"].values():
        for o in (v.get("opciones") or [v]):
            modelo = str(o.get("modelo") or "").upper()
            for p in prohibidos:
                assert p not in modelo, f"{modelo!r} contiene {p}"
            assert not errata_jinpen.search(modelo), f"errata en {modelo!r}"
            for t in re.split(r"[^A-Z0-9\-/]+", modelo):
                assert t not in UNIDADES, f"{modelo!r} deja la unidad {t!r}"
            assert not re.search(r"\d+ ?(?:AH|AMP|WATTS?|W|V|CC|KG|KM)$", modelo), \
                f"{modelo!r} termina en Numero+unidad"
            if "E-CARGO" not in modelo:
                assert "CARGA" not in modelo, f"{modelo!r} contiene CARGA"

    modelos = set(_modelos_canonicos())
    # Grafías canónicas presentes: misma marca/modelo, decoración fuera.
    assert "MIGHONG" in modelos
    assert "MISHOZUKI ULTRA" in modelos
    assert "FUGUIGUAN" in modelos
    # El grupo JINPENG unificado (2026-10-31): la marca/modelo JINPENG
    # aparece en la tabla; sus erratas no.
    assert "JINPENG" in modelos

    # El mismo criterio debe sostener el dataset publicado: si el scraper
    # reintrodujese un descriptor o una spec, el JSONL ya nacería con él.
    for path in sorted((ROOT / "Data").rglob("*.jsonl")):
        df = pd.read_json(path, lines=True)
        if "modelo" not in df.columns:
            continue
        nombres = df["modelo"].dropna().astype(str).str.upper()
        for p in prohibidos:
            assert not nombres.str.contains(p, na=False).any(), \
                f"{path}: {p} dentro de {sorted(set(nombres[nombres.str.contains(p)]))}"
        if not len(nombres):
            continue
        con_carga = nombres[
            (nombres.str.contains("CARGA", na=False))
            & (~nombres.str.contains("E-CARGO", na=False))
        ]
        assert con_carga.empty, \
            f"{path}: CARGA dentro de {sorted(set(con_carga))}"
        con_spec = nombres[
            nombres.str.contains(r"\d+ ?(?:AH|AMP|WATTS?|W|V|CC|KG|KM)$",
                                 regex=True, na=False)
        ]
        assert con_spec.empty, \
            f"{path}: specs en el nombre {sorted(set(con_spec))}"


def test_grupo_jinpeng_esta_unificado():
    """Decisión del usuario (2026-10-31): JIMPEG y JINPEN son JINPENG.

    Al nivel marca, las cuatro grafías erratas (`JINPEING`, `JIMPEG`,
    `JINPEN`, `JIMPENG`) normalizan a JINPENG. Al nivel producto, los tres
    híbridos del grupo comparten la identidad JINPENG (3 anuncios) y el
    eléctrico queda separado por propulsión. La evolución de la decisión
    está en `opencode/auditoria_jinpen.md`.
    """
    from codes.norm_modelo import normalizar_marca

    for grafia in ("JINPEING", "JEINPEING", "JIMPEG", "JIMPENG", "JINPEN"):
        assert normalizar_marca(grafia) == "JINPENG", grafia
    jinpeng = SCORE[SCORE["modelo_norm"] == "JINPENG"]
    hibrido = jinpeng[jinpeng["propulsion"] == "hibrido"]
    assert len(hibrido) == 1
    assert int(hibrido.iloc[0]["n_anuncios_total"]) == 3
    nombres = set(SCORE["modelo_norm"].astype(str).str.upper())
    assert "JINPEN" not in nombres and "JIMPEG" not in nombres
    assert (ROOT / "opencode" / "auditoria_jinpen.md").exists()


def test_canonicos_no_reintroducen_erratas():
    modelos = _modelos_canonicos()
    assert not any("JINPEING" in m for m in modelos)


def test_triciclo_generico_sin_marca_no_es_valido():
    """Decisión 2026-10-31: 'TRICICLO ...' sin marca no identifica un modelo."""
    invalidos = [
        (v.get("modelo"), v.get("marca"), u)
        for u, v in CANON["por_url"].items()
        if "TRICICLO" in str(v.get("modelo") or "").upper()
        and not str(v.get("marca") or "").strip()
    ]
    assert not invalidos, invalidos

    for path in sorted((ROOT / "Data").rglob("*.jsonl")):
        df = pd.read_json(path, lines=True)
        if "modelo" not in df.columns or "marca" not in df.columns:
            continue
        malos = df[
            df["modelo"].astype(str).str.contains("TRICICLO", case=False, na=False)
            & (df["marca"].isna() | (df["marca"].astype(str).str.strip() == ""))
        ]
        assert malos.empty, (
            f"{path}: {malos[['modelo', 'marca', 'url']].to_dict('records')}"
        )


def test_marca_presente_si_el_modelo_la_nombra():
    """Si el modelo contiene una marca conocida, `marca` no puede quedar vacía."""
    marcas = {
        str(v["marca"]).strip().upper()
        for v in CANON["por_url"].values() if v.get("marca")
    }
    for path in sorted((ROOT / "Data").rglob("*.jsonl")):
        df = pd.read_json(path, lines=True)
        if "modelo" not in df.columns or "marca" not in df.columns:
            continue
        faltan = df[
            df["marca"].isna() | (df["marca"].astype(str).str.strip() == "")
        ]
        for r in faltan.itertuples():
            modelo = str(r.modelo or "").upper()
            hits = [
                m for m in marcas
                if re.search(rf"(?<![A-Z0-9]){re.escape(m)}(?![A-Z0-9])", modelo)
            ]
            assert not hits, (
                f"{path}: modelo={r.modelo!r} sin marca; contiene {hits}"
            )
