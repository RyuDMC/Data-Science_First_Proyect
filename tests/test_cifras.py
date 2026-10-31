"""Contrato de cifras: `Data/metadata.json`, los datos y el README.

Si alguien cambia los datos o escribe una cifra a mano, estos tests fallan.
Es la red que evita el 42-vs-41 y el 30-vs-68.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
META = json.loads((ROOT / "Data" / "metadata.json").read_text(encoding="utf-8"))
C = META["conteos"]


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


def test_readme_coincide_con_metadata():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    esperados = [
        f'{C["anuncios"]} anuncios · {C["modelos_ranking"]} modelos',
        f'{C["fichas_empresa"]} fichas · {C["empresas"]} empresas',
        f'{C["observaciones_campo"]} observaciones · {C["municipios_campo"]} municipios',
        f'{C["modelos_con_repuestos"]} de {C["modelos_ranking"]} modelos',
    ]
    for texto in esperados:
        assert texto in readme, f"README no contiene: {texto!r}"


def test_sin_cifras_viejas_en_el_reporte():
    """Guarda contra la recaída: 42 modelos / 42 filas / 9 de 42."""
    archivos = list((ROOT / "reporte").rglob("*.py")) + [ROOT / "README.md"]
    obsoletas = ["42 modelos", "42 filas", "9/42", "9 de 42"]
    for path in archivos:
        texto = path.read_text(encoding="utf-8")
        for vieja in obsoletas:
            assert vieja not in texto, f"Cifra obsoleta {vieja!r} en {path}"
