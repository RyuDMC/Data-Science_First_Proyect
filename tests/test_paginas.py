"""Smoke test de las 11 pantallas con Streamlit AppTest.

No valida el contenido: garantiza que cada página arranca sin excepción con
los datos versionados. Es el mismo chequeo que se hacía a mano.
"""

import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGETS = [ROOT / "reporte" / "app.py"] + sorted(
    (ROOT / "reporte" / "pages").glob("*.py")
)


@pytest.mark.parametrize("path", TARGETS, ids=[p.name for p in TARGETS])
def test_pagina_sin_excepciones(path):
    at = AppTest.from_file(str(path), default_timeout=60)
    at.run()
    if at.exception:
        detalle = "; ".join(str(e.value) for e in at.exception)
        pytest.fail(f"{path.name}: {detalle}")
