#!/usr/bin/env python3
"""
Normalización de nombres de modelo (regla acordada con el usuario, 2026-10-19).

Por qué existe
--------------
El campo `modelo` es la IDENTIDAD del producto: es la clave con la que se
agrupan los anuncios de distintas fuentes y sobre la que se calcula el score.
Hasta el 2026-10-19 el nombre venía crudo del título de la web ("TRICICLOS
ELECTRICOS MAF BATERIA LIFEPO4", "TRICICLO FLY RACING MOTOR 1500W BATERÍA
72V80AMP"), así que:

  - el mismo producto escrito de dos formas no se fusionaba (KIVITOVA de
    Facebook vs "TRICICLOS KIVITOVA 2026" del scraper), y
  - el mismo nombre sí fusionaba productos distintos (los dos "OIM" de
    elyerromenu, los tres "E-CARGO" de MZ Products).

Regla (curada por el usuario el 2026-10-19, tras revisar los datos)
-------------------------------------------------------------------
`modelo` = el NOMBRE PROPIO del modelo:
  - se quitan los genéricos de categoría (TRICICLO, ELÉCTRICO, HÍBRIDO,
    DE COMBUSTION, DE CARGA, PASAJEROS...),
  - se quita el marketing (DISPONIBLE, MAS GRANDE, MEJOR PRECIO,
    PANEL SOLAR, FOTOVOLTAICO...),
  - se quitan los datos técnicos que ya viven en otros campos (72V, 85AH,
    1500W, LITHIUM, LIFEPO4, MOTOR, BATERÍA),
  - y si tras eso NO queda nombre de modelo, `modelo` queda en null y la
    identidad pasa a la `marca` (que es lo que el usuario hizo: CHILWEE,
    CYT, KIVITOVA, MAF, LAITUNG, STAR, JINPEN, Hercules, Tiger...).

Dos productos con el mismo nombre pero specs distintas NO se fusionan: se
separan con un sufijo de variante (OIM / OIM PASAJE, RALLY PASAJEROS /
RALLY CARGA, E-CARGO 80AH / 60AH / 100AH, VEDCA C800B / VEDCA C800B
FOTOVOLTAICO). Cada uno se cuenta por separado.

Cómo se aplica
--------------
1. `Data/modelos_canonicos.json` es la tabla CURADA (clave: URL del producto).
   Es la fuente de verdad: lo que el usuario revisó a mano.
2. Si una URL no está en la tabla, se aplica la regla heurística de este
   módulo y el registro se marca como `heuristico` (o `revisar` si el
   resultado es dudoso: sin nombre, o se le quitó un rasgo de variante).
3. Los scrapers llaman a `canonizar_registro()` ANTES de escribir el JSONL,
   de modo que `raw_data` nace con los nombres ya normalizados: la limpieza
   no depende de editar el JSONL a mano después.

Uso:
    python3 codes/norm_modelo.py --migrar     # normaliza raw_data/ y empresas/
    python3 codes/norm_modelo.py --check      # muestra qué queda por revisar
"""

import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
CANON_PATH = DATA_DIR / "modelos_canonicos.json"

# ==================== REGLAS ====================

# Genéricos de categoría: no identifican un producto.
GENERICOS = {
    "TRICICLO", "TRICICLOS", "ELECTRICO", "ELECTRICOS", "ELECTRICAS",
    "ELECTRICOS", "HIBRIDO", "HIBRIDOS", "HIBRIDA", "COMBUSTION",
    "GASOLINA", "CARGA", "PASAJEROS", "PASAJE", "DE", "DEL", "LA", "EL",
    "LOS", "LAS", "CON", "PARA", "CUBA", "EN", "Y", "A", "POR", "TIPO",
    "CERRADA", "CERRADO", "TRASERO", "TRASERA", "MARCA", "MOTOR", "BATERIA",
    "DEL", "UNA", "UN", "ES", "SU", "AL",
}

# Marketing o estado: no identifican un producto.
MARKETING = {
    "DISPONIBLE", "DISPONIBLES", "MAS", "GRANDE", "GRANDES", "MEJOR",
    "PRECIO", "PRECIOS", "PANEL", "SOLAR", "FOTOVOLTAICO", "OFERTA",
    "PROMOCION", "ENVIO", "GRATIS", "NOVEDAD", "NUEVO", "NUEVA",
}

# Química de batería: ya está en el campo `bateria_quimica`.
QUIMICA_TOKENS = {
    "LITHIUM", "LITIO", "LI-ION", "LIFEPO4", "LIFEPO4MN", "GELPB", "GEL",
    "PLOMO", "ACIDO", "GELPLOMO",
}

# Tokens que son un rasgo de VARIANTE: si se quitan, dos productos distintos
# pueden acabar con el mismo nombre. Se conservan en la heurística y además
# el registro se marca como `revisar` (por si hay que separarlo).
RASGOS_VARIANTE = {"FOTOVOLTAICO", "SOLAR", "PANEL"}

# Texto con la marca declarada por el vendedor: "batería de plomo-ácido
# marca CHILWEE". Es la evidencia que permite completar la marca sin
# inventarla.
MARCA_RE = re.compile(r"MARCA\s*:?\s*([A-Z][A-Z0-9À-Ü][A-Z0-9 .\-]{1,28})", re.I)

# Años: se conservan en el nombre (el usuario dejó "TOPMAQ BRIDERK 2026").
ANIO_RE = re.compile(r"^(19|20)\d{2}$")

# Specs: se eliminan del nombre (ya están en campos propios).
SPEC_RE = re.compile(
    r"^(\d{1,3}(?:V\d{1,3})?(?:AH|AMP|W|WATTS?|CC|KG|KM|L|M|LH|ML)?"
    r"(?:\s*/\s*\d{1,3}(?:V|AH|AMP|W)?)?|\d{1,3}\s*AH|"
    r"\d{1,3}\s*AMP|\d{1,3}\s*WATTS?)$"
)


def _sin_tildes(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def _tokens(nombre):
    """Parte un nombre en tokens conservando guiones internos (SK-2101, E-CARGO)."""
    if not nombre:
        return []
    s = _sin_tildes(str(nombre)).upper()
    s = s.replace("&", " ")
    # Se conservan los guiones internos; el resto es separador.
    s = re.sub(r"(?<![A-Z0-9])-(?![A-Z0-9])", " ", s)
    partes = re.split(r"[^A-Z0-9\-]+", s)
    return [p.strip("-") for p in partes if p.strip("-")]


def limpiar_nombre(nombre):
    """Aplica la regla al nombre. Devuelve (modelo_limpio, avisos).

    `avisos` es una lista de avisos: 'vacio' (no queda nombre de modelo),
    'variante' (se quitó un rasgo que podría distinguir productos).
    """
    toks = _tokens(nombre)
    avisos = []
    out = []
    for t in toks:
        if t in GENERICOS or t in MARKETING or t in QUIMICA_TOKENS:
            continue
        if SPEC_RE.match(t) and not ANIO_RE.match(t):
            continue
        if t in RASGOS_VARIANTE:
            avisos.append("variante")
            continue
        out.append(t)

    # Deduplicar tokens repetidos ("TRICICLO FLY RACING FLY RACING").
    limpio = []
    for t in out:
        if not limpio or limpio[-1] != t:
            limpio.append(t)
    modelo = " ".join(limpio).strip()

    if not modelo:
        avisos.append("vacio")
    return modelo, avisos


def detectar_marca(texto):
    """Extrae la marca declarada en el texto ('... marca CHILWEE')."""
    if not texto:
        return None
    m = MARCA_RE.search(_sin_tildes(str(texto)).upper())
    if not m:
        return None
    marca = m.group(1).strip(" .-:")
    # La frase suele seguir con la especificación: "marca CHILWEE, garantiza"
    marca = re.split(r"\s+(?:CON|GARANTIZA|CUENTA|ES|QUE|PARA)\b", marca)[0]
    return marca.strip() or None


# ==================== TABLA CANÓNICA ====================
def cargar_canonicos(path=CANON_PATH):
    """Carga Data/modelos_canonicos.json (tabla curada por el usuario)."""
    if not Path(path).exists():
        return {"por_url": {}, "excluidos": {}}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("por_url", {})
    data.setdefault("excluidos", {})
    return data


def canonizar(modelo_bruto, marca_bruto=None, texto=None, url=None, canon=None,
              propulsion=None):
    """Devuelve (modelo, marca, estado).

    estado: 'canonico'  -> viene de la tabla curada
            'heuristico' -> derivado por la regla, sin avisos
            'revisar'    -> la regla deja un resultado dudoso
    """
    canon = canon or {"por_url": {}, "excluidos": {}}
    por_url = canon.get("por_url", {})

    # 1) Tabla curada: manda siempre.
    #    Una misma URL puede servir a varios productos (mrcuba: una sola
    #    página de Wix); en ese caso la tabla guarda "opciones" y se elige
    #    la que casa con el nombre original del producto.
    if url:
        ent = por_url.get(url)
        if ent:
            if "opciones" in ent:
                bruto = _sin_tildes(str(modelo_bruto or "")).upper()
                # 1) El nombre original (el registro aún sin normalizar).
                for op in ent["opciones"]:
                    m = _sin_tildes(str(op.get("match") or "")).upper()
                    if m and m in bruto:
                        return op.get("modelo"), op.get("marca"), "canonico"
                # 2) La propulsión: discriminante que la normalización NO toca
                #    (mrcuba: una sola URL de Wix para dos productos).
                prop = str(propulsion or "").lower()
                if prop:
                    for op in ent["opciones"]:
                        if op.get("propulsion") == prop:
                            return op.get("modelo"), op.get("marca"), "canonico"
                op = ent["opciones"][0]
                return op.get("modelo"), op.get("marca"), "canonico"
            return ent.get("modelo"), ent.get("marca"), "canonico"

    # 2) Heurística.
    marca = marca_bruto
    m_det = detectar_marca(texto)
    if m_det and not marca:
        marca = m_det

    modelo, avisos = limpiar_nombre(modelo_bruto)
    if not modelo:
        return None, marca, "revisar"
    if "variante" in avisos:
        return modelo, marca, "revisar"
    return modelo, marca, "heuristico"


def canonizar_registro(record, canon=None, texto=None):
    """Normaliza `modelo`/`marca` de un registro in-place.

    Añade el campo interno `_estado_norm` ('canonico'|'heuristico'|'revisar').
    """
    canon = canon or cargar_canonicos()
    modelo, marca, estado = canonizar(
        record.get("modelo"),
        record.get("marca"),
        texto=texto or record.get("_titulo_raw"),
        url=record.get("url"),
        canon=canon,
        propulsion=record.get("propulsion"),
    )
    record["modelo"] = modelo
    record["marca"] = marca
    record["_estado_norm"] = estado
    return record


def url_excluido(url, canon=None):
    """Devuelve el motivo de exclusión si la URL está en la lista de excluidos."""
    canon = canon or cargar_canonicos()
    exc = canon.get("excluidos", {})
    if url and url in exc:
        ent = exc[url]
        if isinstance(ent, str):
            return ent
        return ent.get("motivo", "excluido por el usuario")
    return None


# ==================== IDENTIDAD (compartida con el reporte) ====================
# Alias de fusión entre fuentes: una MISMA línea se anuncia con nombres
# distintos según el vendedor. Clave: identificador crudo → canónico.
# Los nombres canónicos son los de Data/modelos_canonicos.json (curados por
# el usuario el 2026-10-19).
#
# NO fusionar (decisión del usuario):
#   - STAR: el eléctrico de Facebook y el híbrido de elyerromenu.
#   - OIM / OIM PASAJE: dos productos distintos.
#   - JINPENG (eléctrico), JINPEN (híbrido), TY150UK (Jimpeng): tres productos.
#   - DDS-OD: marca KIVITOVA, pero modelo distinto de KIVITOVA.
ALIAS_MODELOS = {
    # Facebook "BRIDERK" / "TOPMAQ" + elyerromenu "TOPMAQ BRIDERK 2026"
    "BRIDERK": "TOPMAQ BRIDERK 2026 GELPB",
    "BRIDERK GELPB": "TOPMAQ BRIDERK 2026 GELPB",
    "BRIDERK LIFEPO4": "TOPMAQ BRIDERK 2026 LIFEPO4",
    "TOPMAQ": "TOPMAQ BRIDERK 2026 GELPB",
    "TOPMAQ GELPB": "TOPMAQ BRIDERK 2026 GELPB",
    # Facebook "ONEBOT" + elyerromenu "ONEBOT CLASIC 2026"
    "ONEBOT": "ONEBOT CLASIC 2026",
    "ONEBOT GELPB": "ONEBOT CLASIC 2026 GELPB",
    # Facebook "KIVITOVA" / "KIVITOVA PREMIUM" + elyerromenu (marca KIVITOVA)
    "KIVITOVA": "KIVITOVA GELPB",
    "KIVITOVA GELPB": "KIVITOVA GELPB",
    "KIVITOVA PREMIUM": "KIVITOVA GELPB",
    "KIVITOVA LIFEPO4": "KIVITOVA LIFEPO4",
    # Facebook "MVP POWER" + elyerromenu "MVP POWER"
    "MVP POWER": "MVP POWER GELPB",
    "MVP POWER GELPB": "MVP POWER GELPB",
    # Facebook "MAF" + elyerromenu (marca MAF, sin nombre de modelo)
    "MAF": "MAF LIFEPO4",
    "MAF LIFEPO4": "MAF LIFEPO4",
    # Facebook "VIENTO RAPIDO" + elyerromenu "VIENTO RAPIDO"
    "VIENTO RAPIDO": "VIENTO RAPIDO",
}


def aplicar_alias(x):
    """Aplica la tabla de alias a un identificador (string)."""
    return ALIAS_MODELOS.get(x, x)


# ==================== ALIAS DE MARCA (nivel marca, no nivel modelo) ====================
# Grafías de la MISMA marca entre las fuentes (hoja de campo y anuncios).
# Es un eje distinto de ALIAS_MODELOS: aquí no se afirma nada sobre el modelo.
# Decisiones del usuario (2026-10-31): VELGA es VEDCA mal escrito, y JINPEN /
# JIMPENG son la misma marca que JINPENG. Fusionar la MARCA no fusiona los
# productos: la identidad de producto sigue distinguiendo JINPENG eléctrico de
# JINPEN híbrido (la propulsión forma parte de la clave).
MARCA_ALIAS = {
    "ONEBOOT": "ONEBOT",        # hoja de campo
    "KVITOVA": "KIVITOVA",      # hoja de campo
    "MAGICBIKE": "MAGIC BIKE",  # hoja de campo
    "VELGA": "VEDCA",           # hoja de campo: errata confirmada
    "JINPEING": "JINPENG",      # anuncio elyerromenu
    "JINPEN": "JINPENG",        # anuncio elyerromenu (híbrido)
    "JIMPENG": "JINPENG",       # anuncio Facebook (producto TY150UK)
}


def normalizar_marca(marca):
    """Devuelve la marca en mayúsculas, sin espacios repetidos y con alias."""
    if marca is None or (isinstance(marca, float)):
        return ""
    m = " ".join(str(marca).upper().split())
    return MARCA_ALIAS.get(m, m)


def marca_norm(df):
    """Columna `marca_norm` (nivel marca) para comparar campo y anuncios."""
    import pandas as pd  # import local

    if df.empty or "marca" not in df.columns:
        return pd.Series([], dtype="object")
    out = df["marca"].fillna("").astype(str).map(normalizar_marca)
    return out.where(out.ne(""), pd.NA)


def identidad(df, con_alias=True):
    """Calcula la columna `modelo_norm` (identidad del producto).

    Regla (decisión del usuario, 2026-10-19):
      1. `modelo` (nombre propio, ya normalizado en el origen);
      2. si no hay modelo, la identidad es la MARCA;
      3. en eléctricos se añade la química de batería (variante);
      4. se aplica la tabla de alias (fusión entre fuentes).

    Nunca devuelve "None"/"nan": un producto sin modelo ni marca se
    identifica como "SIN IDENTIFICAR" y se avisa.
    """
    import pandas as pd  # import local: el resto del módulo no lo necesita

    if df.empty:
        return pd.Series([], dtype="object")

    modelo_col = df["modelo"] if "modelo" in df.columns else None
    marca_col = df["marca"] if "marca" in df.columns else None
    if modelo_col is None:
        base = pd.Series("", index=df.index, dtype="object")
    elif marca_col is None:
        base = modelo_col
    else:
        base = modelo_col.where(modelo_col.notna(), marca_col)

    base = base.fillna("").astype(str).str.upper().str.strip()
    base = base.str.replace(r"\s+", " ", regex=True).str.strip()

    sin_identidad = base.eq("")
    if sin_identidad.any():
        base = base.where(~sin_identidad, "SIN IDENTIFICAR")

    if "propulsion" in df.columns:
        prop_low = df["propulsion"].fillna("indeterminado").astype(str).str.lower()
    else:
        prop_low = pd.Series("indeterminado", index=df.index)

    if "bateria_quimica" in df.columns:
        quimica = df["bateria_quimica"].fillna("").astype(str).str.upper().str.strip()
        quimica = quimica.where(quimica.ne("") & quimica.ne("NAN"), "")
    else:
        quimica = pd.Series("", index=df.index)

    # Solo en eléctricos: en un híbrido la batería es el extensor de rango.
    quimica = quimica.where(prop_low.eq("electrico"), "")

    out = (base + " " + quimica).str.replace(r"\s+", " ", regex=True).str.strip()
    if con_alias:
        out = out.map(aplicar_alias)
    return out


# ==================== MIGRACIÓN DE ARCHIVOS ====================
def _procesar(path_in, path_out, canon, dry_run=False):
    """Normaliza un JSONL. Devuelve un resumen dict."""
    registros = []
    with open(path_in, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                registros.append(json.loads(line))

    res = {"archivo": Path(path_in).name, "total": len(registros),
           "canonico": 0, "heuristico": 0, "revisar": 0,
           "excluidos": 0, "cambios": []}

    salida = []
    for r in registros:
        motivo = url_excluido(r.get("url"), canon)
        if motivo:
            res["excluidos"] += 1
            res["cambios"].append({"url": r.get("url"), "accion": "excluido",
                                    "motivo": motivo})
            continue
        antes = (r.get("modelo"), r.get("marca"))
        canonizar_registro(r, canon)
        estado = r.pop("_estado_norm", "heuristico")
        res[estado] = res.get(estado, 0) + 1
        if (r.get("modelo"), r.get("marca")) != antes:
            res["cambios"].append({
                "url": r.get("url"),
                "modelo_antes": antes[0], "modelo_despues": r.get("modelo"),
                "marca_antes": antes[1], "marca_despues": r.get("marca"),
                "estado": estado,
            })
        salida.append(r)

    if not dry_run and path_out:
        Path(path_out).parent.mkdir(parents=True, exist_ok=True)
        with open(path_out, "w", encoding="utf-8") as f:
            for r in salida:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return res


def _main(argv):
    canon = cargar_canonicos()
    dry = "--check" in argv and "--migrar" not in argv

    # Los datos de empresas viven en Data/empresas/ y se copian a clean_data.
    # La migración normaliza EL CRUDO en el sitio (para que raw_data y
    # empresas/ queden con los nombres ya normalizados, igual que hará la
    # próxima corrida del scraper) y luego copia a clean_data/.
    tareas = [
        (DATA_DIR / "raw_data" / "anuncios_triciclos.jsonl",
         DATA_DIR / "clean_data" / "anuncios_triciclos.jsonl"),
        (DATA_DIR / "empresas" / "kikihabana.jsonl",
         DATA_DIR / "clean_data" / "kikihabana.jsonl"),
        (DATA_DIR / "empresas" / "mzproducts.jsonl",
         DATA_DIR / "clean_data" / "mzproducts.jsonl"),
        (DATA_DIR / "empresas" / "mrcuba.jsonl",
         DATA_DIR / "clean_data" / "mrcuba.jsonl"),
        (DATA_DIR / "empresas" / "acubaenvioscargo.jsonl",
         DATA_DIR / "clean_data" / "acubaenvioscargo.jsonl"),
        (DATA_DIR / "empresas" / "compramasonline.jsonl",
         DATA_DIR / "clean_data" / "compramasonline.jsonl"),
    ]
    for src, dst in tareas:
        if not src.exists():
            print(f"[skip] {src} no existe")
            continue
        # 1) Normalizar el crudo en el sitio.
        res = _procesar(src, None if dry else src, canon, dry_run=dry)
        # 2) Copiar a clean_data/.
        if not dry:
            shutil.copyfile(src, dst)
        print(f"{res['archivo']}: {res['total']} registros | "
              f"canónicos {res['canonico']} | heurísticos {res['heuristico']} | "
              f"revisar {res['revisar']} | excluidos {res['excluidos']}")
        if dry:
            for c in res["cambios"]:
                print(f"    - {c.get('accion', 'cambio')}: "
                      f"{c.get('modelo_antes')!r}/{c.get('marca_antes')!r} -> "
                      f"{c.get('modelo_despues')!r}/{c.get('marca_despues')!r} "
                      f"[{c.get('estado','')}] {c.get('motivo','')}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
