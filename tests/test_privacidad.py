"""Reglas de privacidad del proyecto, convertidas en tests.

El trabajo de campo se captura con nombre y carné de identidad. El repo es
público, así que la regla es simple: ni un CI ni un teléfono en archivos
versionados, y el archivo crudo siempre ignorado.

Además de los CI de 11 dígitos se buscan teléfonos cubanos: móviles de 8
dígitos que empiezan por 5 o 6, prefijo internacional +53 y números pegados a
la palabra "WhatsApp". El caso real que motivó esto: un **número de 8 dígitos
sin identificar** aparecía en el campo `legalizacion` de tres anuncios, tras
`WhatsApp:`. No se sabe si era un teléfono o un CI incompleto; se redacta por
precaución y el patrón de 8 dígitos lo detecta igual.
"""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

PATRONES = {
    "carné de identidad (11 dígitos)": r"\b[0-9]{11}\b",
    "8 dígitos tipo móvil o CI incompleto (5/6)": r"\b[56][0-9]{7}\b",
    "prefijo internacional +53": r"\+53[ -]?[0-9]{7,8}",
    "número tras WhatsApp": r"[Ww]hats[Aa]pp[^0-9]{0,25}[0-9]{7,}",
}


@pytest.mark.parametrize("descripcion,patron", PATRONES.items())
def test_sin_pii_en_archivos_versionados(descripcion, patron):
    """Ningún archivo versionado puede contener PII.

    `git grep` solo mira lo versionado, así que `data_personas.txt` (ignorado)
    queda fuera a propósito: es la fuente con PII, no el deliverable.
    """
    r = subprocess.run(
        ["git", "grep", "-nIE", patron],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert r.returncode == 1, (
        f"Posible PII ({descripcion}) en archivos versionados:\n"
        f"{r.stdout}{r.stderr}"
    )


def test_data_personas_esta_ignorado():
    """El archivo crudo y sus variantes no pueden entrar con `git add .`."""
    for nombre in ["data_personas.txt", "data_personas_v2.txt"]:
        r = subprocess.run(
            ["git", "check-ignore", "-q", f"Data/raw_data/{nombre}"],
            cwd=ROOT,
        )
        assert r.returncode == 0, f"Data/raw_data/{nombre} NO está ignorado"
