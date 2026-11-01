#!/usr/bin/env python3
"""
Parsea Data/raw_data/data_from_FB (formato clave: valor) y emite
Data/clean_data/anuncios_facebook.jsonl con el esquema común del pipeline.

Reglas de limpieza:
- Tolerar errores de sintaxis: 'null.' → 'null', 'autonomia' → 'autonomia_km',
  'url' sin ':', 'fuente'/'fuentes' unificado, puntos finales.
- Normalizar marca/modelo (Kivitova/Kvitova→KIVITOVA, STAR/Star→STAR, TOPMAQ/TopMAQ→TOPMAQ).
- Inferir propulsion='electrico' (todo es 60/72V).
- Municipio: 'Boyero'→'Boyeros', 'Habana' genérico→null, Artemisa (fuera de 15)→excluir.
- fuente='facebook', vendedor_tipo='particular', moneda='USD'.
- Mantener campos extra: legalizacion, condicion, bateria_v, bateria_ah, bateria_w, motor_w.
"""

import re
import json
import sys
from pathlib import Path

# Normalización de la identidad del producto (decisión del usuario, 2026-10-19).
# 2026-10-31: del grupo JINPENG, "JIMPENG"/"JIMPEG" son erratas de la marca
# JINPENG; la tabla canónica corrige además los NOMBRES por URL.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from norm_modelo import canonizar_registro, cargar_canonicos  # noqa: E402

RAW_PATH = Path("Data/raw_data/data_from_FB")
OUT_PATH = Path("Data/clean_data/anuncios_facebook.jsonl")

# Mapeo de normalización de marcas
MARCA_MAP = {
    "kivitova": "KIVITOVA",
    "kvitova": "KIVITOVA",
    "topmaq": "TOPMAQ",
    "star": "STAR",
    "panther": "PANTHER",
    "jimpeng": "JINPENG",       # errata del usuario, 2026-10-31
    "jinghan": "JINGHAN",
    "traktion": "TRAKTION",
    "jimpeg": "JINPENG",        # errata del usuario, 2026-10-31
    "maf": "MAF",
    "mishozuki": "MISHOZUKI",
    "viento rapido": "VIENTO RAPIDO",
    "onebot": "ONEBOT",
    "mvp": "MVP",
}

# Mapeo de modelos (para fusión posterior en analisis.py)
MODELO_ALIAS = {
    "bryderk": "BRIDERK",
    "bryderk-topmaq": "BRIDERK",
    "bryderk-topmaq": "BRIDERK",
    "kvitova premium": "KIVITOVA PREMIUM",
    "jimpeg panter 2026": "JINPENG PANTER 2026",  # errata, 2026-10-31
    "mvp power": "MVP POWER",
}

# Municipios válidos de La Habana (15)
MUNICIPIOS_HABANA = {
    "arroyo naranjo", "boyeros", "centro habana", "cerro", "cotorro",
    "diez de octubre", "guanabacoa", "habana del este", "habana vieja",
    "la lisa", "marianao", "plaza de la revolucion", "playa", "regla",
    "san miguel del padron"
}


def parse_line(line: str) -> dict:
    """Parsea una línea 'clave: valor, clave2: valor2' tolerando errores."""
    # Reemplazar 'null.' por 'null,' para que el split funcione
    line = line.replace("null.", "null,")
    # Unificar 'autonomia:' a 'autonomia_km:'
    line = line.replace("autonomia:", "autonomia_km:")
    # Arreglar 'url https' → 'url: https'
    line = line.replace("url https", "url: https")
    # Unificar 'fuentes:' a 'fuente:'
    line = line.replace("fuentes:", "fuente:")

    d = {}
    # Split por ', ' pero cuidando que los valores pueden tener comas (URLs)
    # Estrategia: split por ', ' y luego reconstruir pares clave:valor
    parts = re.split(r",\s*(?=[a-z_]+:)", line)
    for part in parts:
        part = part.strip().rstrip(".")
        if not part:
            continue
        if ":" not in part:
            continue
        k, v = part.split(":", 1)
        k = k.strip().lower()
        v = v.strip().rstrip(".").strip()
        # Normalizar 'null' string a None
        if v.lower() == "null":
            v = None
        d[k] = v
    return d


def normalizar_marca(marca: str) -> str:
    if not marca:
        return None
    key = marca.strip().lower()
    return MARCA_MAP.get(key, marca.upper())


def normalizar_modelo(modelo: str, marca: str = None) -> str:
    if not modelo or modelo.lower() == "null":
        # Usar marca como fallback
        if marca:
            return normalizar_marca(marca)
        return None
    key = modelo.strip().lower()
    return MODELO_ALIAS.get(key, modelo.upper())


def normalizar_municipio(mun: str) -> str:
    if not mun or mun.lower() == "null":
        return None
    key = mun.strip().lower()
    if key == "boyero":
        return "Boyeros"
    if key == "habana":
        return None  # genérico, no sirve
    if key == "artemisa":
        return None  # fuera de los 15
    if key in MUNICIPIOS_HABANA:
        return mun.strip().title()
    return None


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with RAW_PATH.open("r", encoding="utf-8") as f:
        content = f.read()

    # Separar por líneas vacías
    raw_lines = [block.strip() for block in content.split("\n\n") if block.strip()]

    print(f"Registros brutos: {len(raw_lines)}")

    escritos = 0
    canon = cargar_canonicos()
    with OUT_PATH.open("w", encoding="utf-8") as out:
        for i, block in enumerate(raw_lines, 1):
            d = parse_line(block)

            marca = normalizar_marca(d.get("marca"))
            modelo = normalizar_modelo(d.get("modelo"), marca)
            municipio = normalizar_municipio(d.get("municipio"))

            # Saltar si es Artemisa (municipio fuera de rango)
            mun_raw = d.get("municipio", "")
            if mun_raw and mun_raw.strip().lower() == "artemisa":
                print(f"  [{i}] Excluido (Artemisa): {marca} {modelo}")
                continue

            # Construir registro con esquema común
            rec = {
                "modelo": modelo,
                "modelo_norm": None,  # se rellena en analisis.py
                "marca": marca,
                "propulsion": "electrico",
                "motor_w": int(d["motor_w"]) if d.get("motor_w") and d["motor_w"].isdigit() else None,
                "motor_cc": None,
                "bateria_v": int(d["bateria_v"]) if d.get("bateria_v") and d["bateria_v"].isdigit() else None,
                "bateria_ah": int(d["bateria_ah"]) if d.get("bateria_ah") and d["bateria_ah"].isdigit() else None,
                "bateria_w": int(d["bateria_w"]) if d.get("bateria_w") and d["bateria_w"].isdigit() else None,
                "bateria_quimica": None,
                "autonomia_km": int(d["autonomia_km"]) if d.get("autonomia_km") and d["autonomia_km"].isdigit() else None,
                "carga_kg": int(d["carga_kg"]) if d.get("carga_kg") and d["carga_kg"].isdigit() else None,
                "precio_usd": float(d["precio_usd"]) if d.get("precio_usd") and d["precio_usd"] != "null" else None,
                "precio_valor": float(d["precio_usd"]) if d.get("precio_usd") and d["precio_usd"] != "null" else None,
                "moneda": "USD",
                "precio_desde": False,
                "ano": None,
                "condicion": d.get("condicion") if d.get("condicion") not in (None, "null") else None,
                "disponibilidad": None,
                "legalizacion": d.get("legalizacion") if d.get("legalizacion") not in (None, "null") else None,
                "vendedor_tipo": "particular",
                "municipio_anuncio": municipio,
                "url": d.get("url") if d.get("url") not in (None, "null") else None,
                "fecha_captura": d.get("fecha_captura"),
                "fecha_anuncio": None,
                "fuente": "facebook",
                "oferta_viva": True,
                "n_anuncios": 1,
            }

            # Normalización de la identidad del producto (decisión del usuario,
            # 2026-10-19): la tabla curada (Data/modelos_canonicos.json) manda;
            # lo que no esté en ella se resuelve con la regla heurística.
            canonizar_registro(rec, canon)
            rec.pop("_estado_norm", None)

            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            escritos += 1
            print(f"  [{i}] {marca} {modelo} | {municipio} | ${rec['precio_usd']} | {rec['autonomia_km']}km | {rec['carga_kg']}kg")

    print(f"\n✅ Escritos {escritos} registros limpios a {OUT_PATH}")


if __name__ == "__main__":
    main()