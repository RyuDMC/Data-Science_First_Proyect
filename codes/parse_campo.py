#!/usr/bin/env python3
"""
Ingesta del trabajo de campo: `Data/raw_data/data_personas.txt` -> `Data/registro_ubicaciones.csv`.

Por qué existe
--------------
El trabajo de campo (inventario municipal) es la ÚNICA fuente de circulación
real del estudio, pero se anotó en una libreta de texto libre:

    1/ Fecha: 13/10/26
       municipio: Habana del Este
       uso: familiar
       propulsion: electrico
       marca: ONEBOOT
       motor: 1500w
       bateria: 72v 58ah
       autonomia: 100km
       propietario: NOMBRE APELLIDO CI: <11 dígitos>

`analisis.py` y el reporte leen `Data/registro_ubicaciones.csv` (11 columnas
fijas). Este script es el único puente entre ambos, y se aplica en el ORIGEN
igual que `norm_modelo.py` en los datos online: la hoja de campo nunca se
edita a mano después de capturada.

Privacidad (decisión de proyecto)
---------------------------------
El txt crudo lleva nombre y carné de identidad de cada propietario. Esos
campos NO se copian a ningún sitio: el parser los descarta en la lectura y
verifica que no quede ningún número de 11 dígitos en la salida. El txt queda
fuera del repositorio (ver `.gitignore`).

Reglas de normalización (documentadas para poder revertirlas)
-------------------------------------------------------------
- `fecha`: dd/mm/aa -> ISO (2026-10-13).
- `municipio`: nombre oficial con tilde (los 15 de La Habana).
- `uso`: valores permitidos del esquema (carga | pasajeros | mixto | ocio_paseo).
  El texto original se conserva en `uso_original`; no se pierde información.
  Decisión del usuario (2026-10-31): "familiar" se cuenta como **pasajeros**.
- `propulsion`: "electrico + paneles" -> electrico + con_paneles=1.
- `marca`: alias de erratas (tabla `MARCA_ALIAS` de codes/norm_modelo.py:
  ONEBOOT->ONEBOT, KVITOVA->KIVITOVA, MAGICBIKE->MAGIC BIKE, VELGA->VEDCA,
  JINPEING/JINPEN/JIMPENG->JINPENG).
- `motor`: "1500" / "1500w" -> "1500W" (la unidad la fija el esquema).
- `bateria`: "72v 58ah" -> bateria_v=72, bateria_ah=58. Los voltajes con errata
  confirmada por el usuario se corrigen con una tabla explícita
  (`CORRECCIONES_BATERIA_V`) y el valor original queda en `bateria_v_origen`:
  la corrección es trazable, no silenciosa.
- `autonomia`: "110 km" -> 110.
- `estado` / `observador`: no se capturaron en la hoja. Se dejan vacíos
  (regla del proyecto: no inventar datos).

Uso:
    python3 codes/parse_campo.py            # regenera registro_ubicaciones.csv
    python3 codes/parse_campo.py --check    # ¿el CSV coincide con el txt?
"""

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

# La marca se normaliza con la MISMA tabla que usan los anuncios
# (codes/norm_modelo.py): una sola fuente de verdad para el eje marca.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from norm_modelo import MARCA_ALIAS, normalizar_marca  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
SRC = DATA_DIR / "raw_data" / "data_personas.txt"
DST = DATA_DIR / "registro_ubicaciones.csv"

# Esquema fijo del CSV (las 11 columnas del protocolo + lo que se midió de más).
COLUMNAS = [
    "obs_id", "fecha", "municipio", "tipo", "uso", "uso_original", "propulsion",
    "modelo", "marca", "motor", "bateria_v", "bateria_v_origen", "bateria_ah",
    "autonomia_km", "con_paneles", "estado", "observador", "notas",
]

# Correcciones confirmadas por el usuario (2026-10-31). El valor de origen se
# conserva en `bateria_v_origen`, así que la corrección es auditable.
CORRECCIONES_BATERIA_V = {
    78: 72,  # OBS-002 "78 50ah": errata; 72 V es el estándar del dataset
}

# ==================== CATÁLOGOS ====================

MUNICIPIOS = [
    "Arroyo Naranjo", "Boyeros", "Centro Habana", "Cerro", "Cotorro",
    "Diez de Octubre", "Guanabacoa", "Habana del Este", "Habana Vieja",
    "La Lisa", "Marianao", "Plaza de la Revolución", "Playa", "Regla",
    "San Miguel del Padrón",
]

# uso capturado a mano -> valor del esquema (el original se conserva aparte).
USO_MAP = {
    # Decisión del usuario (2026-10-31): "familiar" = pasajeros.
    "familiar": "pasajeros",
    "pasaje": "pasajeros",
    "carga": "carga",
    "carga y pasaje": "mixto",
    "carga y pasajeros": "mixto",
    "mixto": "mixto",
}

# Erratas de marca: la tabla vive en codes/norm_modelo.py (compartida con los
# anuncios). Se importa arriba; aquí solo se documenta el porqué.

# No se fusionan los PRODUCTOS (decisión del usuario, 2026-10-19): JINPEN es
# el híbrido y JIMPENG la grafía de TY150UK. La MARCA sí se unifica en
# `MARCA_ALIAS` (decisión 2026-10-31): JINPEING/JINPEN/JIMPENG -> JINPENG.
# JINPEING es una errata de JINPENG, no un producto aparte.

# Bloques: "1/ Fecha: 13/10/26" seguido de líneas "clave: valor".
BLOQUE_RE = re.compile(r"^\s*(\d+)\s*/\s*Fecha:\s*(\d{2})/(\d{2})/(\d{2})\s*$", re.M)
CAMPO_RE = re.compile(r"^\s{2,}([a-záéíóúñ]+):\s*(.+?)\s*$", re.M | re.I)
CI_RE = re.compile(r"\b\d{11}\b")


def _sin_tildes(texto):
    return "".join(
        c for c in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(c) != "Mn"
    )


MUNI_POR_CLAVE = {_sin_tildes(m).lower(): m for m in MUNICIPIOS}


def normalizar_municipio(valor):
    clave = re.sub(r"\s+", " ", _sin_tildes(valor).strip().lower())
    if clave not in MUNI_POR_CLAVE:
        raise ValueError(f"municipio fuera del catálogo de 15: {valor!r}")
    return MUNI_POR_CLAVE[clave]


def normalizar_uso(valor):
    clave = re.sub(r"\s+", " ", valor.strip().lower())
    if clave not in USO_MAP:
        raise ValueError(f"uso no reconocido: {valor!r}")
    return USO_MAP[clave]


def normalizar_motor(valor):
    """'1500' / '1500w' / '1500 W' -> (1500, '1500W')."""
    m = re.search(r"(\d+)\s*(?:w|watts?)?\s*$", valor.strip().lower())
    if not m:
        return None, valor.strip()
    w = int(m.group(1))
    return w, f"{w}W"


def normalizar_bateria(valor):
    """'72v 58ah' / '78 50ah' -> (v, ah). La errata se corrige fuera, con tabla."""
    m = re.search(r"(\d+)\s*v?\s*(\d+)\s*ah", valor.strip().lower())
    if not m:
        return None, None, "batería ilegible en origen"
    return int(m.group(1)), int(m.group(2)), None


def normalizar_autonomia(valor):
    m = re.search(r"(\d+)", valor)
    return int(m.group(1)) if m else None


def normalizar_propulsion(valor):
    clave = _sin_tildes(valor).strip().lower()
    if "panel" in clave:
        return "electrico", 1
    if clave.startswith("electric"):
        return "electrico", 0
    if clave.startswith("hibrid"):
        return "hibrido", 0
    if clave.startswith("gasolina"):
        return "gasolina", 0
    return "indeterminado", 0


# ==================== PARSEO ====================

def leer_bloques(texto):
    """Parte el txt en bloques (id, fecha, campos) y descarta los datos personales."""
    marcas = list(BLOQUE_RE.finditer(texto))
    bloques = []
    for i, m in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        cuerpo = texto[m.end():fin]
        campos = {}
        for c in CAMPO_RE.finditer(cuerpo):
            clave = c.group(1).strip().lower()
            valor = c.group(2).strip()
            if clave == "propietario":
                # Dato personal: no entra al diccionario. Se anota solo que
                # el registro está identificado en el origen.
                campos["_tiene_pii"] = True
                continue
            campos[clave] = valor
        bloques.append({
            "n": int(m.group(1)),
            "fecha": f"20{m.group(4)}-{m.group(3)}-{m.group(2)}",
            "campos": campos,
        })
    return bloques


def construir_registros(bloques):
    registros = []
    for b in bloques:
        c = b["campos"]
        faltan = [k for k in ("municipio", "uso", "propulsion", "marca") if k not in c]
        if faltan:
            raise ValueError(f"registro {b['n']}: faltan campos {faltan}")

        propulsion, con_paneles = normalizar_propulsion(c["propulsion"])
        motor_w, motor_txt = normalizar_motor(c.get("motor", ""))
        bat_v, bat_ah, aviso_bat = normalizar_bateria(c.get("bateria", ""))

        notas = []
        if con_paneles:
            notas.append("paneles solares")
        if aviso_bat:
            notas.append(aviso_bat)
        if motor_w is None:
            notas.append("motor ilegible en origen")

        # Errata de voltaje: se corrige con tabla explícita y se deja rastro
        # del valor original (no se sobrescribe la evidencia).
        bat_v_origen = bat_v
        if bat_v in CORRECCIONES_BATERIA_V:
            bat_v = CORRECCIONES_BATERIA_V[bat_v_origen]
            notas.append(f"voltaje corregido {bat_v_origen} V -> {bat_v} V (errata confirmada)")
        elif bat_v is not None and bat_v % 12 != 0:
            notas.append(f"voltaje {bat_v} V a revisar (no es múltiplo de 12)")

        registros.append({
            "obs_id": f"OBS-{b['n']:03d}",
            "fecha": b["fecha"],
            "municipio": normalizar_municipio(c["municipio"]),
            "tipo": "triciclo",  # unidad de observación del estudio
            "uso": normalizar_uso(c["uso"]),
            "uso_original": c["uso"],
            "propulsion": propulsion,
            "modelo": None,  # la hoja no distingue modelo: solo marca
            "marca": normalizar_marca(c["marca"]),
            "motor": motor_txt,
            "bateria_v": bat_v,
            "bateria_v_origen": bat_v_origen,
            "bateria_ah": bat_ah,
            "autonomia_km": normalizar_autonomia(c.get("autonomia", "")),
            "con_paneles": con_paneles,
            "estado": None,      # no capturado
            "observador": None,  # no capturado
            "notas": "; ".join(notas) or None,
        })
    return registros


def parsear(texto):
    return construir_registros(leer_bloques(texto))


def main(argv):
    check = "--check" in argv
    if not SRC.exists():
        print(f"ERROR: no existe {SRC}")
        return 2

    texto = SRC.read_text(encoding="utf-8")
    registros = parsear(texto)
    df = pd.DataFrame(registros, columns=COLUMNAS)

    # Verificación de privacidad: ni nombres ni CI en la salida.
    salida = df.to_csv(index=False)
    if CI_RE.search(salida):
        print("ERROR: la salida contiene un número de 11 dígitos (¿CI?). Abortado.")
        return 3
    if len(registros) != len(leer_bloques(texto)):
        print("ERROR: se perdieron registros en el parseo. Abortado.")
        return 4

    if check:
        if not DST.exists():
            print(f"[check] {DST.name} no existe; ejecuta sin --check")
            return 1
        actual = pd.read_csv(DST)
        if actual.shape == df.shape and actual.fillna("").equals(df.fillna("")):
            print(f"[check] OK: {len(df)} registros, {df['municipio'].nunique()} municipios")
            return 0
        print("[check] DESACTUALIZADO: el CSV no coincide con el txt")
        return 1

    df.to_csv(DST, index=False)
    print(f"-> {DST.relative_to(DATA_DIR.parent)}: {len(df)} registros, "
          f"{df['municipio'].nunique()} municipios")
    print(f"   propulsión: {df['propulsion'].value_counts().to_dict()}")
    print(f"   uso: {df['uso'].value_counts().to_dict()}")
    print("   marcas: " + ", ".join(
        f"{m} ({n})" for m, n in df["marca"].value_counts().items()))
    print(f"   marcas sin alias de errata: {sorted(set(df['marca']) - set(MARCA_ALIAS.values()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
