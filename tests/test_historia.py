"""Contratos de «La Historia»: página estática aparte del reporte técnico.

historia/ hereda la regla central del proyecto: ninguna cifra escrita a
mano. `codes/generar_historia.py` genera historia/datos.json y datos.js
desde los archivos versionados; historia/index.html solo dibuja lo que
esos archivos traen. Estos tests garantizan:
  1. `generar_historia.py --check` pasa (los datos no divergieron).
  2. Los conteos del JSON coinciden con Data/metadata.json y con la pila.
  3. El HTML solo referencia cifras que existen en el JSON (data-cifra)
     y los ids de anclaje usados por su JS están presentes.
  4. La página no introduce PII (mismos patrones del test de privacidad).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORIA = ROOT / "historia"
DATOS = HISTORIA / "datos.json"
INDEX = HISTORIA / "index.html"


def _resuelve(raiz: dict, ruta: str):
    """Resuelve 'a.b.0.c' sobre el JSON (None si no existe)."""
    cur = raiz
    for parte in ruta.split("."):
        if isinstance(cur, list):
            if not parte.isdigit() or int(parte) >= len(cur):
                return None
            cur = cur[int(parte)]
        elif isinstance(cur, dict) and parte in cur:
            cur = cur[parte]
        else:
            return None
    return cur


def test_check_del_generador_pasa():
    r = subprocess.run(
        [sys.executable, str(ROOT / "codes" / "generar_historia.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_cifras_coinciden_con_metadata():
    d = json.loads(DATOS.read_text(encoding="utf-8"))
    m = json.loads((ROOT / "Data" / "metadata.json").read_text(
        encoding="utf-8"))
    assert d["conteos"] == m["conteos"], "conteos divergen del metadata"
    assert d["cortes"] == m["cortes"], "cortes divergen del metadata"
    # la pila dibuja exactamente los anuncios y fuentes del conteo oficial
    assert len(d["pila"]["fichas"]) == m["conteos"]["anuncios"]
    assert len(d["pila"]["fuentes"]) == m["conteos"]["fuentes_anuncios"]
    assert sum(f["n"] for f in d["pila"]["fuentes"]) == \
        m["conteos"]["anuncios"]
    # el histograma de anuncios cubre TODO el ranking
    assert sum(f["modelos"] for f in d["ranking"]["hist_n_anuncios"]) == \
        m["conteos"]["modelos_ranking"]


def test_index_referencia_solo_cifras_existentes():
    html = INDEX.read_text(encoding="utf-8")
    d = json.loads(DATOS.read_text(encoding="utf-8"))
    huecos = [m for m in re.findall(r'data-cifra="([^"]+)"', html)
              if _resuelve(d, m) is None]
    assert not huecos, f"data-cifra sin dato en datos.json: {huecos}"
    # ids que el JS busca a mano; sin ellos la página queda en blanco
    ids_requeridos = [
        "svg-pila", "leyenda-fuentes", "texto-fuentes", "svg-pesos",
        "citas-pesos", "svg-dona", "texto-mercado", "svg-dumbbell",
        "texto-conflicto", "svg-hist", "svg-rangos", "texto-subvuelo",
        "texto-sensib", "podio-chips", "moraleja-titulo",
        "asterisco-un-anuncio", "asterisco-sin-precio", "sin-datos",
    ]
    presentes = set(re.findall(r'id="([^"]+)"', html))
    faltan = [i for i in ids_requeridos if i not in presentes]
    assert not faltan, f"ids que el JS necesita y el HTML no trae: {faltan}"


def test_historia_sin_pii():
    patrones = [
        r"\b[0-9]{11}\b",             # CI de 11 dígitos
        r"\b[56][0-9]{7}\b",          # móvil/CI incompleto de 8
        r"\+53[ -]?[0-9]{7,8}",       # prefijo internacional
    ]
    for ruta in (INDEX, DATOS, HISTORIA / "datos.js"):
        texto = ruta.read_text(encoding="utf-8")
        for pat in patrones:
            assert not re.search(pat, texto), \
                f"PII con patrón {pat} en {ruta.name}"
