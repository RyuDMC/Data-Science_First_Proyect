"""Contrato de cifras: `Data/metadata.json` y los datos.

Si alguien cambia los datos o escribe una cifra a mano, estos tests fallan.
Es la red que evita el 42-vs-41 y el 30-vs-68.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
META = json.loads((ROOT / "Data" / "metadata.json").read_text(encoding="utf-8"))
C = META["conteos"]
R = META["resultados"]


def _jsonl(rutas):
    return pd.concat([pd.read_json(p, lines=True) for p in rutas], ignore_index=True)


def test_metadata_coincide_con_los_datos():
    anuncios = _jsonl([
        ROOT / "Data" / "clean_data" / "anuncios_triciclos.jsonl",
        ROOT / "Data" / "clean_data" / "anuncios_facebook.jsonl",
    ])
    empresas = _jsonl(sorted((ROOT / "Data" / "empresas").glob("*.jsonl")))
    campo = pd.read_csv(ROOT / "Data" / "registro_ubicaciones.csv")
    score = pd.read_csv(ROOT / "Data" / "clean_data" / "score_modelos.csv")
    canonicos = json.loads(
        (ROOT / "Data" / "modelos_canonicos.json").read_text(encoding="utf-8")
    )

    assert C["anuncios"] == len(anuncios)
    assert C["fichas_empresa"] == len(empresas)
    assert C["empresas"] == len(list((ROOT / "Data" / "empresas").glob("*.jsonl")))
    assert C["productos_canonicos"] == len(canonicos["por_url"])
    assert C["productos_excluidos"] == len(canonicos["excluidos"])
    assert C["modelos_ranking"] == len(score)
    assert C["nombres_modelo"] == score["modelo_norm"].nunique()
    assert C["modelos_con_repuestos"] == int(score["repuestos_proxy"].fillna(0).sum())
    assert C["observaciones_campo"] == len(campo)
    assert C["municipios_campo"] == campo["municipio"].nunique()
    assert C["marcas_campo"] == campo["marca"].nunique()

    top_e = score[score["propulsion"] == "electrico"].sort_values(
        ["score", "modelo_norm"], ascending=[False, True], kind="mergesort",
    ).head(3)
    assert [r["modelo"] for r in R["top_por_propulsion"]["electrico"]] == \
        top_e["modelo_norm"].tolist()

    campo_res = pd.read_csv(ROOT / "Data" / "clean_data" / "campo_resumen.csv")
    top_campo = campo_res.sort_values(
        ["n_campo", "marca_norm"], ascending=[False, True], kind="mergesort",
    ).iloc[0]
    assert R["campo_marca_top"]["marca"] == top_campo["marca_norm"]
    assert R["campo_marca_top"]["n"] == int(top_campo["n_campo"])
    assert R["campo_marca_top"]["total"] == int(campo_res["n_campo"].sum())


def test_metadata_es_determinista_por_defecto():
    """Sin `--procedencia`, el JSON no lleva fecha ni commit volátiles."""
    assert "procedencia" not in META


def test_score_legado_archivado():
    """La tabla de la raíz era un legado de 35 filas; solo queda el archivo."""
    assert not (ROOT / "Data" / "score_modelos.csv").exists()
    assert (ROOT / "Data" / "archive" / "score_modelos_2026-10-11.csv").exists()


def test_sin_cifras_viejas_en_el_reporte():
    """Guarda contra la recaída: 42 modelos / 42 filas / 9 de 42."""
    archivos = list((ROOT / "reporte").rglob("*.py")) + [ROOT / "README.md"]
    obsoletas = ["42 modelos", "42 filas", "9/42", "9 de 42"]
    for path in archivos:
        texto = path.read_text(encoding="utf-8")
        for vieja in obsoletas:
            assert vieja not in texto, f"Cifra obsoleta {vieja!r} en {path}"
