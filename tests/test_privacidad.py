"""Reglas de privacidad del proyecto, convertidas en tests.

El trabajo de campo se captura con nombre y carné de identidad. El repo es
público, así que la regla es simple: ni un CI en archivos versionados y el
archivo crudo siempre ignorado.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_sin_numeros_de_11_digitos_en_archivos_versionados():
    """Ningún archivo versionado puede contener un número de 11 dígitos.

    `git grep` solo mira lo versionado, así que `data_personas.txt` (ignorado)
    queda fuera a propósito: es la fuente con PII, no el deliverable.
    """
    r = subprocess.run(
        ["git", "grep", "-nIE", r"\b[0-9]{11}\b"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert r.returncode == 1, (
        "Posible PII (número de 11 dígitos) en archivos versionados:\n"
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
