#!/usr/bin/env python3
"""
Scraper de triciclos para fuentes cubanas VERIFICADAS (2026-10-07).

Estructura del repo (decisión del usuario, ajuste 2026-10-11):
  codes/ -> scripts    Data/ -> datos procesados y de campo
  Data/raw_data/ -> datos crudos (salida del scraper)

Fuentes activas:
  ✅ casalinda   — habana.casalindashop.com  (Magento; 2 combustión + 3 eléctricos, con precio)
  ✅ cubancargos — cubancargos.com/triciclos (Tailwind; 4 triciclos: 3 Híbrido + 1 Eléctrico,
                  specs de la tabla 'Especificaciones técnicas' del detalle)
  ✅ elyerromenu — elyerromenu.com/b/cuba-sobre-ruedas (clasificados comerciales, Boyeros;
                  20 fichas en la categoría de triciclos, precio + specs en el texto libre)
  ⚠️ vedca       — vedca.cu (fabricante estatal; fichas de especificaciones en tabla,
                  SIN precio: aporta carga_kg y autonomia_km, no precio_usd).
                  CAÍDO al 2026-10-11 (Connection reset); se conserva por si vuelve.
  ✅ vedca_telegram — t.me/s/MotosBateriasElectricasCuba (canal PÚBLICO del fabricante,
                  enlazado desde vedca.cu; se pagina con ?before= hasta el inicio del
                  canal: 130 mensajes, 27 con 'tricic', 7 con specs registrables:
                  C400 x4 —una con precio US$3.170 del 2024-12—, C600 x2, C400A x1.
                  Aporta los modelos C600 y C400A, que no existen en vedca.cu)
  ✅ islagrande  — islagrande.com/vehiculos-electricos/triciclos.html (tienda oficial
                  del fabricante VEDCA, Magento). 11 fichas (9 en La Habana; se excluyen
                  las variantes de Holguín/Santiago/Santa Clara), specs por variante
                  (química de batería) y estado de stock; al 2026-10-11 TODOS
                  'Out of stock' -> condicion="agotado" (no puntúan como oferta viva).
                  Precios en EUR (precio_valor + moneda="EUR"): el selector de moneda
                  de Magento exige form_key y no persiste, así que NO se convierte a
                  USD (no se inventa tasa). Sustituye a vedca.cu (caído) como catálogo
                  del fabricante y desambigua las variantes C400/C400A/C600/C800B.

Fuentes descartadas (verificadas muertas/bloqueadas, 2026-10-07):
  ❌ revolico.com, multiservicesxpress.com,
     patuisla.com, mundoenvio.com, envioscubamerica.com → reto de Cloudflare (403 o challenge)
  ⚠️ compramasonline.com → el 2026-10-07 daba challenge; el 2026-10-31 responde 200
     y su categoría 'Triciclos' (8 vehículos) se cubre en codes/scrape_empresas.py.
  ❌ vedca.cu → caído (Connection reset by peer; DNS no resuelve) en 2026-10-11.
     Su catálogo se cubre ahora vía islagrande (misma empresa/fabricante).
  ❌ kikihabana.com → DNS no resuelve
  ❌ cubisima.com, autocubana.com, ventacuba.com, ofertas.cu, cubamax.com, cuballama.com,
     dimecuba.com, atrexport.com, mcvcommercial.com → 200 pero sin triciclos
  ❌ html.duckduckgo.com → 403 en queries site:
  ❌ facebook.com → redirige a /login (400); youtube.com → sin texto SSR util;
     whatsapp.com/channel de Cuban Cargo → shell sin posts sin la app ('tricic'=0)
  ❌ elyerroapp.com (empresa de software, 'tricic'=0), supermarket23.com (búsqueda
     JS, 'tricic'=0 en HTML crudo), katapulk.com ('tricic'=0) → enlaces salientes
     de las fuentes activas, sondeados 2026-10-07
  ❌ subdominios casalindashop de otras provincias (santiago, camaguey, holguin,
     sanctispiritus) → fuera del alcance (15 municipios de La Habana)
  Nota: las búsquedas internas (catalogsearch de casalinda, /search de cubancargos,
  ?s= y /search de elyerromenu) no añaden triciclos fuera de los catálogos vivos.

Límite conocido de elyerromenu: el sitemap (129 MB) es la única enumeración completa,
así que se usa la página de categoría = catálogo vivo. Hay 7 fichas de triciclos sin
categorizar (archivadas, una marcada "Agotado") que quedan fuera.

Uso:
    python3 codes/scrape_triciclos.py      # escribe Data/raw_data/anuncios_triciclos.jsonl
"""

import json
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Convención de carpetas (ajustada 2026-10-11):
#   codes/ -> scripts, Data/ -> datos procesados/campo, Data/raw_data/ -> crudos
DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
RAW_DIR = DATA_DIR / "raw_data"

# Normalización de nombres de modelo (decisión del usuario, 2026-10-19):
# la identidad del producto sale de Data/modelos_canonicos.json (curada) y,
# para lo que no esté en la tabla, de la regla de codes/norm_modelo.py.
# Se aplica ANTES de escribir el JSONL, de modo que raw_data nace con los
# nombres ya normalizados (no hay que editar el JSONL a mano después).
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from norm_modelo import (  # noqa: E402
    canonizar_registro,
    cargar_canonicos,
    url_excluido,
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

SOURCES = {
    "casalinda": {
        "url": "https://habana.casalindashop.com/vehiculos/triciclos.html",
        "list_parser": "parse_casalinda_list",
        "detail_parser": None,          # specs completas ya vienen en el listado
        "propulsion_hint": "indeterminado",
    },
    "cubancargos": {
        "url": "https://cubancargos.com/triciclos",
        "list_parser": "parse_cubancargos_list",
        "detail_parser": "parse_cubancargos_detail",
        "propulsion_hint": "indeterminado",
    },
    "elyerromenu": {
        "url": "https://elyerromenu.com/b/cuba-sobre-ruedas/category/"
               "triciclos-electricos-y-con-extensor",
        "list_parser": "parse_elyerromenu_list",
        "detail_parser": "parse_elyerromenu_detail",   # precio y specs solo en la ficha
        "propulsion_hint": "indeterminado",
    },
    "vedca": {
        "url": "http://www.vedca.cu/",
        "list_parser": "parse_vedca_list",
        "detail_parser": "parse_vedca_detail",
        "propulsion_hint": "electrico",
    },
    "vedca_telegram": {
        # Canal público del fabricante (enlace en vedca.cu). t.me/s/ sirve el
        # historial sin login; el parser pagina internamente con ?before=.
        "url": "https://t.me/s/MotosBateriasElectricasCuba",
        "list_parser": "parse_tg_list",
        "detail_parser": None,          # el mensaje completo ya viene en la lista
        "propulsion_hint": "electrico",
    },
    "islagrande": {
        # Tienda oficial del fabricante (VEDCA): catálogo Magento, precios en
        # EUR (no hay forma limpia de obtener USD: el selector exige form_key).
        # Es el catálogo del fabricante que faltaba desde que vedca.cu cayó:
        # aporta specs por variante (química de batería) y estado de stock.
        "url": "https://islagrande.com/vehiculos-electricos/triciclos.html",
        "list_parser": "parse_islagrande_list",
        "detail_parser": "parse_islagrande_detail",
        "propulsion_hint": "electrico",
    },
}

OUTPUT_FILE = RAW_DIR / "anuncios_triciclos.jsonl"
REQUEST_DELAY = 2
TIMEOUT = 30


# ==================== LIMPIEZA / EXTRACCIÓN ====================
def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ").strip())


def extract_price_usd(text):
    """Devuelve (precio_entero_USD, es_desde). Maneja '3.100,00 USD' y '$4751.00'."""
    if not text:
        return None, False
    t = clean_text(text)
    desde = bool(re.search(r"\bdesde\b", t, re.I))
    # Captura números con separadores de miles/decimales
    m = re.search(r"([\d]{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{1,2})?|[\d]+(?:[.,]\d{1,2})?)", t)
    if not m:
        return None, desde
    raw = m.group(1).strip()
    return _to_int_price(raw), desde


def _to_int_price(raw):
    """'3.100,00' -> 3100 | '$4751.00' -> 4751 | '1,234' -> 1234 | '475100' -> 475100"""
    if not raw:
        return None
    s = raw.replace(" ", "")
    # Último separador decide: si finaliza en ,XX o .XX (1-2 dígitos) → decimal
    m_dec = re.search(r"[.,](\d{1,2})$", s)
    if m_dec:
        s = s[: m_dec.start()]              # corta el decimal
        s = s.replace(".", "").replace(",", "")  # el resto son miles
    else:
        # sin decimal: cualquier separador es de miles si agrupa de 3
        if re.search(r"[.,]\d{3}$", s):
            s = s.replace(".", "").replace(",", "")
        # si no, es un número simple
    digits = re.sub(r"[^\d]", "", s)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def extract_motor_w(text):
    if not text:
        return None
    m = re.search(r"(\d{3,5})\s*[wW]\b", text)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*[kK][wW]\b", text)
    if m:
        return int(float(m.group(1)) * 1000)
    return None


def extract_cc(text):
    if not text:
        return None
    m = re.search(r"(\d{2,4})\s*cc\b", text, re.I)
    return int(m.group(1)) if m else None


def extract_battery(text):
    """Devuelve (V, Ah)."""
    if not text:
        return None, None
    m = re.search(r"(\d{2,3})\s*[vV]\s*(\d{1,3})\s*[aA][hH]?", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    # formatos separados: "72 V" y "58 Ah" cercanos
    v = re.search(r"(\d{2,3})\s*[vV]\b", text)
    ah = re.search(r"(\d{1,3})\s*[aA][hH]\b", text)
    if v and ah:
        return int(v.group(1)), int(ah.group(1))
    return None, None


def extract_bateria_quimica(text):
    """Química de la batería declarada en el texto, normalizada (variante).

    Orden de prioridad: LiFePO4Mn -> LiFePO4 -> GelPb -> Plomo -> Litio.
    LiFePO4 se comprueba ANTES que Gel porque fichas de LiFePO4 incluyen la
    frase 'Digital Li/gel with NFC'; si se buscara 'gel' primero se
    clasificarían como plomo. Devuelve None si el texto no la declara.
    """
    if not text:
        return None
    t = text.lower().translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
    if re.search(r"lifepo\s*4\s*mn|life\s*-?\s*po\s*4\s*mn|lifepo4mn", t):
        return "LIFEPO4MN"
    if re.search(r"lifepo\s*4|life\s*-?\s*po\s*4|lifepo\b", t):
        return "LIFEPO4"
    if re.search(r"gel\s*-?\s*(pb|plomo|lead)|\bgelpb\b|\bgel\b", t):
        return "GELPB"
    if re.search(r"plomo|lead\s*acid|[áa]cido", t):
        return "PLOMO"
    if re.search(r"li-?ion\b|litio", t):
        return "LITIO"
    return None


def extract_carga_kg(text):
    if not text:
        return None
    m = re.search(r"(?:capacidad|carga)[^\d]{0,20}(\d{2,4})\s*kg", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d{2,4})\s*kg", text, re.I)
    return int(m.group(1)) if m else None


def detect_propulsion(text, hint="indeterminado"):
    """Detecta propulsión. Devuelve: hibrido | electrico | gasolina | indeterminado.

    OJO: 'hibrido' es categoría propia. En CubanCargos 3 de 4 triciclos se
    anuncian como híbridos (motor de gasolina + asistencia eléctrica) y
    clasificarlos como 'electrico' sería dato falso.
    """
    if not text:
        return hint
    t = text.lower()
    # \w* al final porque 'eléctrico' termina en 'o': \b ahí nunca coincide.
    if re.search(r"\bel[eé]ctric\w*", t):
        return "electrico"
    if re.search(r"\bcombusti[oó]n\b|\bgasolina\b|\d{1,4}\s?cc\b|cilindrada|4\s*tiempos|carburador|enfriamiento por", t):
        return "gasolina"
    if re.search(r"\bh[ií]brid\w*", t):
        return "hibrido"
    if re.search(r"\bbater[ií]a\b|\blitio\b|cargador|\d{2,3}\s?v\b|\d{1,3}\s?ah\b|\d{3,5}\s?w\b", t):
        return "electrico"
    if hint in ("electrico", "gasolina", "hibrido"):
        return hint
    return "indeterminado"


def normalize_modelo(text):
    """Identificador de producto distintivo (no confundir con la marca).

    OJO: dos Magic Bike distintos (M004 200cc, M005 250cc) NO deben fusionarse,
    y los títulos genéricos de Casalinda no deben colapsar en "TRICICLO EL".
    """
    if not text:
        return "indeterminado"
    u = text.upper()

    # 1) 'Marca: Magic Bike, Modelo: M004' -> 'MAGIC BIKE M004'
    marca_m = re.search(r"MARCA[:\s]+([A-Za-z0-9 ]+?)(?:,|$)", u)
    mod_m = re.search(r"MODELO[:\s]+([A-Z0-9\-]+)", u)
    if marca_m and mod_m:
        return f"{marca_m.group(1).strip()} {mod_m.group(1)}".strip()

    # 2) Códigos de modelo conocidos
    for k in ["SK-2101", "SK2101", "PORTO BELLO", "FURIKAZAN",
              "NIPPON SE", "NIPPON"]:
        if k in u:
            return k
    # "JINPEING"/"JEINPEING" son erratas de JINPENG (confirmado por el usuario,
    # 2026-10-31): se corrigen aquí para que raw_data nazca ya normalizado.
    if "JINPEING" in u or "JEINPEING" in u:
        return "JINPENG"

    # 3) Solo código de modelo: 'MODELO: M005'
    if mod_m:
        return mod_m.group(1)

    # 3b) Alias entre fuentes: mismo producto redactado de forma distinta.
    #     vedca.cu dice 'Modelo : C- 400' y elyerromenu 'VEDCA C400' -> mismo modelo.
    #     La letra final cuenta: 'C400A' es un modelo distinto de 'C400'.
    m = re.search(r"VEDCA\s*C[\s\-]*(\d{2,4}[A-Z]?)", u)
    if m:
        return f"VEDCA C{m.group(1)}"
    if re.search(r"PORTO\s?BELLO", u):
        return "PORTO BELLO"

    # 4) Fallback: palabras distintivas, sin artículos/genéricos de triciclo.
    #    Se quitan tildes ANTES de trocear: "ELÉCTRICO" si no, parte en "EL"+"CTRICO".
    u_ascii = "".join(c for c in unicodedata.normalize("NFD", u)
                      if unicodedata.category(c) != "Mn")
    STOP = {"TRICICLO", "DE", "LA", "EL", "LOS", "LAS", "CON", "Y", "A", "EN",
            "POR", "PARA", "TIPO", "CERRADA", "CERRADO", "TRASERO", "TRASERA", "MARCA"}
    words = [w for w in re.split(r"[^A-Za-z0-9]+", u_ascii) if w and w not in STOP]
    return " ".join(words[:4]) if words else "indeterminado"


# ==================== PARSER: CASALINDA (Magento) ====================
def parse_casalinda_list(soup, base_url, hint):
    for item in soup.select(".products-grid .item, .product-item"):
        name_el = item.select_one(".product-item-link, .product-name a, a.product-item-link")
        link_el = item.select_one("a[href]")
        price_el = item.select_one(".price")
        if not (name_el and link_el):
            continue
        titulo = clean_text(name_el.get_text())
        if not titulo:
            continue
        detail_url = link_el.get("href", "")
        precio, desde = extract_price_usd(clean_text(price_el.get_text())) if price_el else (None, False)

        propulsion = detect_propulsion(titulo, hint)
        v, ah = extract_battery(titulo)
        yield {
            "modelo": normalize_modelo(titulo),
            "marca": _marca_from_titulo(titulo),
            "propulsion": propulsion,
            "motor_w": extract_motor_w(titulo) if propulsion == "electrico" else None,
            "motor_cc": extract_cc(titulo),
            "bateria_v": v,
            "bateria_ah": ah,
            "autonomia_km": _km_from_text(titulo),
            "carga_kg": extract_carga_kg(titulo),
            "precio_usd": precio,
            "precio_desde": desde,
            "ano": None,
            "condicion": "nuevo",
            "legalizacion": None,
            "vendedor_tipo": "tienda",
            "municipio_anuncio": "La Habana",
            "url": detail_url,
            "fecha_captura": datetime.now().isoformat(),
            "fuente": "casalindashop",
            "_titulo_raw": titulo,
        }


# ==================== PARSER: CUBANCARGOS (Tailwind) ====================
def parse_cubancargos_list(soup, base_url, hint):
    seen = set()
    for link in soup.select('a[href^="/triciclos/"]'):
        href = link.get("href", "")
        if not href or href in ("/triciclos/", "/triciclos/electricos-cuba", "/triciclos/gasolina-cuba"):
            continue
        if href in seen:
            continue
        seen.add(href)
        h3 = link.select_one("h3")
        titulo = clean_text(h3.get_text()) if h3 else clean_text(link.get_text())
        if len(titulo) < 5:
            continue
        propulsion = detect_propulsion(titulo, hint)
        v, ah = extract_battery(titulo)
        yield {
            "modelo": normalize_modelo(titulo),
            "marca": _marca_from_titulo(titulo),
            "propulsion": propulsion,
            "motor_w": extract_motor_w(titulo) if propulsion == "electrico" else None,
            "motor_cc": extract_cc(titulo),
            "bateria_v": v,
            "bateria_ah": ah,
            "autonomia_km": _km_from_text(titulo),
            "carga_kg": extract_carga_kg(titulo),
            "precio_usd": None,   # no hay precio en listado
            "precio_desde": False,
            "ano": None,
            "condicion": "nuevo",
            "legalizacion": None,
            "vendedor_tipo": "tienda",
            "municipio_anuncio": None,
            "url": urljoin(base_url, href),
            "fecha_captura": datetime.now().isoformat(),
            "fuente": "cubancargos",
            "_titulo_raw": titulo,
        }


def parse_cubancargos_detail(soup, record):
    """Completa specs desde la tabla 'Especificaciones técnicas'.

    La tabla es `table` con `tr` > 2 `td` (etiqueta, valor). El campo `Tipo`
    es el dato autoritativo de propulsión (Híbrido / Eléctrico / Gasolina),
    no el texto libre de la página (que menciona 'Eléctricos' en el menú).
    """
    specs = _specs_from_table(soup)
    record["_specs"] = specs

    # 1) Propulsión: `Tipo` manda si existe
    tipo = specs.get("Tipo") or specs.get("tipo")
    if tipo:
        record["propulsion"] = _propulsion_from_tipo(tipo)
    else:
        # fallback: título del producto, no la página completa
        h1 = soup.find("h1")
        base = clean_text(h1.get_text()) if h1 else record.get("_titulo_raw", "")
        record["propulsion"] = detect_propulsion(base, record.get("propulsion", "indeterminado"))

    # 2) Motor
    if not record.get("motor_w"):
        record["motor_w"] = extract_motor_w(specs.get("Motor", "")) or \
                            extract_motor_w(record.get("_titulo_raw", ""))
    # 3) Batería
    if not record.get("bateria_v"):
        v, ah = extract_battery(specs.get("Batería", "") or specs.get("Bateria", ""))
        if v:
            record["bateria_v"], record["bateria_ah"] = v, ah
    # 4) Autonomía — primer número ('50–60 km' -> 50 conservador)
    if not record.get("autonomia_km"):
        record["autonomia_km"] = _first_int(specs.get("Autonomía", ""))
    # 5) Carga
    if not record.get("carga_kg"):
        record["carga_kg"] = _first_int(specs.get("Capacidad de carga", "")) or \
                             extract_carga_kg(specs.get("Carga", ""))
    # 6) Legalización: Factura / Documentación (criterio ponderado)
    if not record.get("legalizacion"):
        legal = specs.get("Factura") or specs.get("Documentación") or specs.get("Documentacion")
        if legal:
            record["legalizacion"] = clean_text(legal)[:120]
    # 7) Garantía (informativo)
    if specs.get("Garantía"):
        record["garantia"] = clean_text(specs["Garantía"])[:80]
    # 8) Extensor de rango (señal de mercado relevante)
    if specs.get("Extensor de rango"):
        record["extensor_rango_w"] = extract_motor_w(specs["Extensor de rango"])

    # 9) Precio: 'Precio: $5320.00' es el actual; el siguiente es el tachado
    if not record.get("precio_usd"):
        m = re.search(r"Precio:\s*\$\s*([\d.,]+)", soup.get_text(" ", strip=True))
        if m:
            record["precio_usd"] = _to_int_price(m.group(1))
        else:
            m2 = re.findall(r"\$\s*([\d,]{4,}(?:\.\d{1,2})?)", soup.get_text(" ", strip=True))
            if m2:
                record["precio_usd"] = _to_int_price(m2[0])


def _specs_from_table(soup):
    """Extrae pares etiqueta/valor de la(s) tabla(s) del detalle."""
    specs = {}
    for tr in soup.select("table tr"):
        tds = tr.select("td")
        if len(tds) >= 2:
            key = clean_text(tds[0].get_text())
            val = clean_text(tds[1].get_text(" ", strip=True))
            if key and val and key not in specs:
                specs[key] = val
    return specs


def _propulsion_from_tipo(tipo):
    """'Híbrido' -> hibrido | 'Eléctrico' -> electrico | 'Gasolina' -> gasolina."""
    t = tipo.lower()
    if "brid" in t:
        return "hibrido"
    if re.search(r"el[eé]ctric", t):
        return "electrico"
    if "gasolina" in t or "combusti" in t:
        return "gasolina"
    return detect_propulsion(tipo, "indeterminado")


def _first_int(text):
    if not text:
        return None
    m = re.search(r"(\d[\d.,]*)", text)
    if not m:
        return None
    # '50–60' -> 50 ; '1.60' es decimal de dimensión, pero aquí son cantidades enteras
    return _to_int_price(m.group(1))


# ==================== PARSER: ELYERROMENU ("Cuba sobre ruedas", Boyeros) ====================
# Clasificados comerciales: el precio sale del bloque 'Imagen N de M <precio> USD'
# y las specs del texto libre del anuncio (muy irregular: '70kl', '1200 wat', '58amp').
# La categoría del producto NO se puede filtrar por la palabra 'triciclo' en el cuerpo:
# los ONEBOT no la mencionan; la evidencia es la categoría que el vendedor declara
# en el pie de la ficha ('Categorías -> Triciclos Eléctricos y con extensor').
_NO_ES_TRICICLO = re.compile(r"cuatriciclo|cargador|\bgomas?\b|accesorio", re.I)


def _texto_ficha(soup):
    """Devuelve (cuerpo, pie) del texto visible, sin <head> ni chrome.

    El pie ('Categorías ...') trae rótulos de sección que falsearían la
    propulsión y la legalidad si se mezclaran con el cuerpo del anuncio.
    """
    for t in soup(["script", "style", "head", "nav", "footer", "svg", "header", "noscript"]):
        t.decompose()
    texto = clean_text(soup.get_text(" ", strip=True))
    corte = re.search(r"\bCategor[ií]as\b", texto)
    if not corte:
        return texto, ""
    return texto[: corte.start()], texto[corte.start():]


def _propulsion_el_yerro(texto):
    """Híbrido manda: los anuncios de híbridos también dicen 'Eléctrico'.

    Orden: híbrido -> gasolina (señal fuerte: cc / 4 tiempos, sin batería de
    tracción) -> eléctrico -> gasolina débil.
    """
    t = texto.lower()
    if re.search(r"\bh[ií]brid\w*", t):
        return "hibrido"
    if re.search(r"\d{1,4}\s?cc\b|4\s*tiempos|carburador", t) and \
       not re.search(r"\d{2,3}\s?v\b|\d{1,3}\s?ah\b|bater[ií]a", t):
        return "gasolina"
    if re.search(r"\bel[eé]ctric\w*", t) or re.search(r"bater[ií]a|\d{2,3}\s?v\b|\d{1,3}\s?ah\b", t):
        return "electrico"
    if re.search(r"\bgasolina\b|combusti[oó]n", t):
        return "gasolina"
    return "indeterminado"


def parse_elyerromenu_list(soup, base_url, hint):
    """Enlaces de producto de la página de categoría (catálogo vivo).

    Todo el contenido útil está en la ficha, así que el listado solo aporta la URL.
    """
    prefijo = "/b/cuba-sobre-ruedas/product/"
    seen = set()
    for link in soup.select('a[href*="/product/"]'):
        url = urljoin(base_url, link.get("href", ""))
        if urlparse(url).path.startswith(prefijo) and url not in seen:
            seen.add(url)
            yield {
                "modelo": None,
                "marca": None,
                "propulsion": "indeterminado",
                "motor_w": None,
                "motor_cc": None,
                "bateria_v": None,
                "bateria_ah": None,
                "autonomia_km": None,
                "carga_kg": None,
                "precio_usd": None,
                "precio_desde": False,
                "ano": None,
                "condicion": None,
                "legalizacion": None,
                "vendedor_tipo": "tienda",
                "municipio_anuncio": "Boyeros",
                "url": url,
                "fecha_captura": datetime.now().isoformat(),
                "fuente": "elyerromenu",
                "_requiere_detalle": True,
            }


def parse_elyerromenu_detail(soup, record):
    h1 = soup.find("h1")
    titulo = clean_text(h1.get_text()) if h1 else ""
    slug = urlparse(record["url"]).path.rsplit("/", 1)[-1]
    cuerpo, pie = _texto_ficha(soup)
    cuerpo = re.sub(r"Triciclos\s+El[ée]ctricos\s+y\s+con\s+extensor", " ", cuerpo, flags=re.I)

    # La categoría del vendedor incluye por error accesorios y un cuatriciclo.
    if _NO_ES_TRICICLO.search(slug):
        record["_descartar"] = True
        return
    es_triciclo = bool(re.search(r"triciclo", cuerpo, re.I)) or \
        bool(re.search(r"Triciclos\s+El[ée]ctricos\s+y\s+con\s+extensor", pie, re.I))
    if not es_triciclo:
        record["_descartar"] = True
        return

    record["_titulo_raw"] = titulo
    record["modelo"] = normalize_modelo(titulo) if titulo else None
    if record["modelo"] is None:
        record["_descartar"] = True
        return
    record["marca"] = _marca_from_titulo(titulo)
    record["propulsion"] = _propulsion_el_yerro(cuerpo)

    # Precio publicado en la ficha
    m = re.search(r"Imagen\s+\d+\s+de\s+\d+\s+([\d.,]+)\s*USD", cuerpo, re.I) or \
        re.search(r"([\d]{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d{3,5})\s*USD", cuerpo, re.I)
    record["precio_usd"] = _to_int_price(m.group(1)) if m else None

    # Algunos anuncios declaran un precio distinto en el texto que en el campo
    # estructurado (p. ej. TOPMAQ 4.700 vs 5.000). No se puede saber cuál es el
    # vigente: se conserva el estructurado y se deja constancia del otro.
    if record["precio_usd"]:
        otros = set()
        for mm in re.finditer(r"(\d{1,3}(?:[.,]\d{3})+|\d{3,5})(?:[.,]\d{2})?\s*(?:usd|us\$)",
                              cuerpo, re.I):
            v = _to_int_price(mm.group(1))
            if v and v != record["precio_usd"] and \
               0.6 * record["precio_usd"] <= v <= 1.6 * record["precio_usd"]:
                otros.add(v)
        if otros:
            record["precio_texto_usd"] = sorted(otros)[0]

    # Autonomía: 'Autonomía: 120 Km', 'Autonomía 70kl', '30-40 km de autonomía'
    m = re.search(r"autonom\w*[^0-9]{0,22}(\d{1,3})(?:\s*[-–]\s*\d{1,3})?\s*(?:km|kl)(?!/h)",
                  cuerpo, re.I) or \
        re.search(r"(\d{1,3})\s*(?:km|kl)(?!/h)\s*de\s*autonom", cuerpo, re.I)
    record["autonomia_km"] = int(m.group(1)) if m else None

    # Carga
    m = re.search(r"(?:capacidad de carga|carga m[aá]x\w*|carga)[^0-9]{0,25}"
                  r"(\d{1,4}(?:[.,]\d{1,2})?)\s*kg", cuerpo, re.I)
    record["carga_kg"] = _to_int_price(m.group(1)) if m else None

    # Motor: 'Motor 1500W'. Si solo está el extensor de rango, NO es el motor.
    m = re.search(r"motor[^0-9]{0,22}(\d{3,4})\s*(?:w|wat\w*)\b", cuerpo, re.I)
    if not m:
        for mm in re.finditer(r"(\d{3,4})\s*(?:w|wat\w*)\b", cuerpo, re.I):
            if "extensor" not in cuerpo[max(0, mm.start() - 40): mm.start()].lower():
                m = mm
                break
    record["motor_w"] = int(m.group(1)) if m else None

    m = re.search(r"extensor[^0-9]{0,25}(\d{3,4})\s*(?:w|wat\w*)\b", cuerpo, re.I)
    if m:
        record["extensor_rango_w"] = int(m.group(1))

    # Batería: '72V×58Ah', '60 vol x 58amp', '63ah × 72v'
    m = re.search(r"(\d{2,3})\s*(?:volt\w*|vol|v)\s*[x×\-–—]?\s*(\d{1,3})\s*(?:amp\w*|ah)\b",
                  cuerpo, re.I)
    if m:
        record["bateria_v"], record["bateria_ah"] = int(m.group(1)), int(m.group(2))
    else:
        m = re.search(r"(\d{1,3})\s*(?:amp\w*|ah)\s*[x×\-–—]\s*(\d{2,3})\s*(?:volt\w*|vol|v)\b",
                      cuerpo, re.I)
        if m:
            record["bateria_ah"], record["bateria_v"] = int(m.group(1)), int(m.group(2))

    record["bateria_quimica"] = extract_bateria_quimica(cuerpo)

    m = re.search(r"(\d{1,4})\s*cc\b", cuerpo, re.I)
    record["motor_cc"] = int(m.group(1)) if m else None

    # Legalización (criterio ponderado 0.10)
    for p in [r"factura\w*", r"papeles en regla", r"documentaci[oó]n a nombre",
              r"a nombre del cliente", r"directo a chapa", r"lista para chapa"]:
        m = re.search(p, cuerpo, re.I)
        if m:
            record["legalizacion"] = clean_text(cuerpo[m.start(): m.start() + 110])
            break

    m = re.search(r"\b(20[0-2]\d)\b", titulo)
    ano = int(m.group(1)) if m else None
    record["ano"] = ano if ano and 2000 <= ano <= datetime.now().year else None

    if re.search(r"usado|segunda mano", cuerpo, re.I):
        record["condicion"] = "usado"
    elif re.search(r"nuevo|\b0\s*km\b", cuerpo, re.I):
        record["condicion"] = "nuevo"


# ==================== PARSER: VEDCA (fabricante, vedca.cu) ====================
def parse_vedca_list(soup, base_url, hint):
    """Triciclos del catálogo: `.portfolio-item.filter-tri` con enlace a ficha `.html`."""
    for item in soup.select(".portfolio-item.filter-tri"):
        a = item.select_one("a.link-details[href]")
        if not a or not a.get("href", "").endswith(".html"):
            continue          # 3 de 5 triciclos no tienen ficha propia (href="#")
        yield {
            "modelo": None,
            "marca": "VEDCA",
            "propulsion": "electrico",
            "motor_w": None,
            "motor_cc": None,
            "bateria_v": None,
            "bateria_ah": None,
            "autonomia_km": None,
            "carga_kg": None,
            "precio_usd": None,   # VEDCA no publica precio: se cotiza por Facebook/teléfono
            "precio_desde": False,
            "ano": None,
            "condicion": "nuevo",
            "legalizacion": None,
            "vendedor_tipo": "fabricante",
            "municipio_anuncio": None,
            "url": urljoin(base_url, a.get("href")),
            "fecha_captura": datetime.now().isoformat(),
            "fuente": "vedca",
            "_requiere_detalle": True,
        }


def parse_vedca_detail(soup, record):
    """Modelo y specs desde la tabla 'Característica | Parámetros'."""
    texto = clean_text(soup.get_text(" ", strip=True))
    specs = _specs_from_table(soup)
    record["_specs"] = specs

    m = re.search(r"Modelo\s*:\s*([^:]{0,30}?)(?=\s+(?:Color|Documentaci|Tipo\b)|$)", texto)
    if m and clean_text(m.group(1)):
        record["modelo"] = normalize_modelo(f"VEDCA {clean_text(m.group(1))}")

    record["propulsion"] = "electrico" if re.search(r"triciclo\s+el[eé]ctric", texto, re.I) \
        else detect_propulsion(texto, record.get("propulsion", "electrico"))
    record["marca"] = "VEDCA"

    if not record.get("autonomia_km"):
        record["autonomia_km"] = _first_int(specs.get("Autonomía", ""))
    if not record.get("carga_kg"):
        record["carga_kg"] = _first_int(specs.get("Peso de carga", "")) or \
                             _first_int(specs.get("Capacidad de carga", ""))
    if not record.get("motor_w"):
        record["motor_w"] = extract_motor_w(specs.get("Potencia del motor", ""))
    if not record.get("bateria_v"):
        # 'Tipo de batería' aparece 2 veces en c800.html y _specs_from_table
        # conserva la primera ('Lifepo4 / Plomo Ácido', sin cifras): buscar en el texto.
        v, ah = extract_battery(texto)
        if v:
            record["bateria_v"], record["bateria_ah"] = v, ah

    record["bateria_quimica"] = extract_bateria_quimica(
        specs.get("Tipo de batería", "") + " " + texto)


# ==================== PARSER: TELEGRAM PÚBLICO (canal de VEDCA) ====================
def _tg_mensajes(soup):
    """(post_id, fecha_iso, texto) de una página de t.me/s/<canal>."""
    out = []
    for m in soup.select(".tgme_widget_message_wrap .tgme_widget_message"):
        t = m.select_one(".tgme_widget_message_text")
        d = m.select_one(".tgme_widget_message_date time")
        pid = (m.get("data-post") or "").rsplit("/", 1)[-1]
        if t and pid.isdigit():
            out.append((pid, d.get("datetime", "") if d else "",
                        clean_text(t.get_text(" ", strip=True))))
    return out


def parse_tg_list(soup, base_url, hint):
    """Mensajes del canal público con paginación `?before=`.

    No hay detalle separado: cada mensaje ya viene completo en la página de la
    lista. Solo se registran mensajes de triciclo CON specs o precio; los que
    son enlaces secos (islagrande bloqueado por Cloudflare) se contabilizan y
    se descartan, dejando constancia de los modelos que solo existen así.

    CONVENCIÓN de rangos: 'Autonomía: 80-90Km' -> 80 (límite inferior), igual
    que hace el parser de elyerromenu. No se inventa el punto medio.
    """
    canal = base_url.rstrip("/").rsplit("/", 1)[-1]
    todos = {pid: (f, t) for pid, f, t in _tg_mensajes(soup)}   # pid -> (fecha, texto)

    # Paginación hasta el inicio del canal (~14 páginas, ~15 msgs cada una)
    while True:
        ids = [int(p) for p in todos]
        if min(ids) <= 1:
            break
        try:
            nuevas = _tg_mensajes(BeautifulSoup(
                fetch(f"{base_url.rstrip('/')}?before={min(ids)}"),
                "html.parser"))
        except Exception as e:
            print(f"  WARNING paginación Telegram: {type(e).__name__}: {e}")
            break
        antes = len(todos)
        for pid, f, t in nuevas:
            todos.setdefault(pid, (f, t))
        if len(todos) == antes:               # página ya vista: fin
            break
        time.sleep(REQUEST_DELAY)

    print(f"  Mensajes del canal: {len(todos)} (desde el inicio)")
    sin_tricic = descartados = 0
    modelos_solo_enlace = set()
    registros = []

    for pid, (fecha, texto) in sorted(todos.items(), key=lambda kv: int(kv[0])):
        if not re.search(r"tricic", texto, re.I):
            sin_tricic += 1
            continue

        # Modelo: token C<num>[letra] en el cuerpo o en el enlace
        # (C400, C600, C400A...; ojo: C400A NO debe colapsar en C400).
        m = re.search(r"\bC[\s\-]?(\d{3,4}[A-Z]?)\b", texto, re.I)
        modelo = f"VEDCA C{m.group(1).upper()}" if m else None

        auto = re.search(
            r"autonom\w*[^0-9]{0,22}(\d{1,3})(?:\s*[-–]\s*\d{1,3})?\s*(?:km|kl)(?!/h)",
            texto, re.I)
        carga = re.search(
            r"(?:capacidad de carga|carga m[aá]x\w*|carga)[^0-9]{0,25}"
            r"(\d{1,4}(?:[.,]\d{1,2})?)\s*kg", texto, re.I)
        precio = re.search(
            r"\$\s*([\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?|\d{3,5})", texto) or \
            re.search(r"([\d]{1,3}(?:[.,]\d{3})+)\s*USD", texto)
        motor = re.search(r"potencia del motor[^0-9]{0,20}(\d{3,5})\s*w", texto, re.I)

        autonomia = int(auto.group(1)) if auto else None
        carga_kg = _to_int_price(carga.group(1)) if carga else None
        precio_usd = _to_int_price(precio.group(1)) if precio else None
        motor_w = int(motor.group(1)) if motor else extract_motor_w(texto)
        bat_v, bat_ah = extract_battery(texto)

        if not modelo or not any([autonomia, carga_kg, precio_usd, motor_w]):
            # Enlace seco (p. ej. a islagrande) o noticia institucional.
            descartados += 1
            for sm in re.finditer(r"\b(c\d{3,4}[a-z]?|lt\d{3,4})\b", texto, re.I):
                modelos_solo_enlace.add(sm.group(1).upper())
            continue

        legalizacion = None
        for p in [r"factura\w*", r"papeles en regla", r"documentaci[oó]n a nombre",
                  r"a nombre del cliente", r"directo a chapa", r"lista para chapa"]:
            mm = re.search(p, texto, re.I)
            if mm:
                legalizacion = clean_text(texto[mm.start(): mm.start() + 110])
                break

        registros.append({
            "modelo": modelo,
            "marca": "VEDCA",
            "propulsion": detect_propulsion(texto, hint),
            "motor_w": motor_w,
            "motor_cc": None,
            "bateria_v": bat_v,
            "bateria_ah": bat_ah,
            "bateria_quimica": extract_bateria_quimica(texto),
            "autonomia_km": autonomia,
            "carga_kg": carga_kg,
            "precio_usd": precio_usd,
            "precio_desde": False,
            "ano": None,
            "condicion": None,
            "legalizacion": legalizacion,
            "vendedor_tipo": "fabricante",
            # Solo si el mensaje declara la dirección del almacén (Boyeros).
            "municipio_anuncio": "Boyeros" if "Boyeros" in texto else None,
            "url": f"https://t.me/s/{canal}/{pid}",
            "fecha_captura": datetime.now().isoformat(),
            "fecha_anuncio": fecha,
            "fuente": "vedca_telegram",
        })

    print(f"  Sin 'tricic': {sin_tricic} | descartados sin datos útiles: {descartados}")
    retenidos = {r["modelo"].replace("VEDCA ", "") for r in registros}
    extra = sorted(modelos_solo_enlace - retenidos)
    if extra:
        print(f"  Modelos solo en enlaces (sin ficha publicada): {', '.join(extra)}")
    return registros


# ==================== PARSER: ISLAGRANDE (tienda del fabricante VEDCA) ====================
# Catálogo Magento de la tienda oficial de VEDCA. Precios en EUR (el selector
# de moneda exige form_key y no persiste: no hay USD limpio). Todos los
# triciclos figuran 'Out of stock' al 2026-10-11 -> condicion="agotado": con la
# regla "oferta viva manda" no puntúan precio, pero aportan specs por VARIANTE
# (química de batería) del catálogo del fabricante, que faltaba desde que
# vedca.cu cayó.
# Alcance La Habana: se excluyen las variantes -holguin / -santiago / -santaclara.
_ISLA_NO_HABANA = re.compile(r"-(holguin|santiago|santaclara)\.html$", re.I)


def _isla_base_model(slug):
    """Modelo base a partir del slug; conserva la variante no-química
    (p. ej. C800B FOTOVOLTAICO). La química se guarda aparte (bateria_quimica)."""
    s = slug.lower()
    if "sh001" in s:
        return "VEDCA SH001"
    if "c800b" in s:
        return "VEDCA C800B" + (" FOTOVOLTAICO" if "fotovoltaico" in s else "")
    if "c600" in s:
        return "VEDCA C600"
    if "c400a" in s:
        return "VEDCA C400A"
    if "c400" in s:
        return "VEDCA C400"
    if "c300" in s:
        return "VEDCA C300"
    return None


def _isla_rango_km(bloque):
    """Límite inferior de la autonomía declarada (convención del proyecto).

    'between 90 and 100 km' -> 90 ; '50 - 70 km' -> 50 ; '80 km' -> 80 ;
    'Up to 60 km ... approximately 40 km' -> 40 (el menor de los km citados).
    """
    m = re.search(r"(?:average\s+range|range|autonom\w*)[^.]{0,140}", bloque, re.I)
    s = m.group(0) if m else bloque[:200]
    pares = re.findall(r"(\d{1,3})\s*(?:-|–|—|to|and|a)\s*(\d{1,3})\s*km", s, re.I)
    if pares:
        return min(int(x) for par in pares for x in par)
    nums = re.findall(r"(\d{1,3})\s*km", s, re.I)
    return min(int(n) for n in nums) if nums else None


def parse_islagrande_list(soup, base_url, hint):
    """Solo aporta la URL de cada ficha (precio y specs están en el detalle)."""
    seen = set()
    for a in soup.select("a.product-item-link[href]"):
        url = urljoin(base_url, a.get("href", ""))
        if not url.endswith(".html") or url in seen:
            continue
        if "triciclo" not in url.lower():
            continue                      # accesorios (p. ej. batería/cargador)
        if _ISLA_NO_HABANA.search(urlparse(url).path):
            continue                      # variante de otra provincia
        seen.add(url)
        yield {
            "modelo": None,
            "marca": "VEDCA",
            "propulsion": "electrico",
            "motor_w": None,
            "motor_cc": None,
            "bateria_v": None,
            "bateria_ah": None,
            "bateria_quimica": None,
            "autonomia_km": None,
            "carga_kg": None,
            "precio_usd": None,           # se publica en EUR (precio_valor)
            "precio_desde": False,
            "precio_valor": None,
            "moneda": "EUR",
            "ano": None,
            "condicion": None,
            "legalizacion": None,
            "vendedor_tipo": "fabricante",
            "municipio_anuncio": "Boyeros",   # Almacén VEDCA, Av. Independencia
            "url": url,
            "fecha_captura": datetime.now().isoformat(),
            "fuente": "islagrande",
            "_requiere_detalle": True,
        }


def parse_islagrande_detail(soup, record):
    slug = urlparse(record["url"]).path.rsplit("/", 1)[-1]
    if _ISLA_NO_HABANA.search(urlparse(record["url"]).path):
        record["_descartar"] = True
        return

    base = _isla_base_model(slug)
    if not base:
        record["_descartar"] = True
        return
    record["modelo"] = base

    # Texto para el estado de stock (toda la página).
    for t in soup(["script", "style", "head", "nav", "footer", "svg", "header", "noscript"]):
        t.decompose()
    texto = clean_text(soup.get_text(" ", strip=True))

    # Specs: SOLO la descripción del producto. La sección 'Up-Sell Products'
    # contamina la química (p. ej. metía C800A LiFePO4Mn en la ficha del C400A).
    desc = soup.select_one(".product.attribute.description") or soup.select_one("#description")
    bloque = clean_text(desc.get_text(" ", strip=True)) if desc else texto

    record["bateria_quimica"] = extract_bateria_quimica(bloque)

    # Batería V/Ah: primero la viñeta 'Battery:', luego el bloque completo.
    mb = re.search(r"battery\s*[:\-]\s*([^•\.]{0,50})", bloque, re.I)
    v, ah = extract_battery(mb.group(1) if mb else bloque)
    if not v:
        v, ah = extract_battery(bloque)
    record["bateria_v"], record["bateria_ah"] = v, ah

    # Motor: 'Motor Power: 60V 1500W' / 'Motor: 60V 1000W'
    mm = re.search(r"motor(?:\s*power)?\s*[:\-]?\s*(?:\d{2,3}\s*v\s*)?(\d{3,5})\s*w",
                   bloque, re.I)
    record["motor_w"] = int(mm.group(1)) if mm else extract_motor_w(bloque)

    record["autonomia_km"] = _isla_rango_km(bloque)

    # Carga: la etiqueta explícita manda sobre cualquier otro 'NNN kg'.
    for pat in [r"net load[^0-9]{0,20}(\d{2,4})\s*kg",
                r"load capacity[^0-9]{0,20}(\d{2,4})\s*kg",
                r"cargo weight[^0-9]{0,20}(\d{2,4})\s*kg",
                r"maximum payload[^0-9]{0,20}(\d{2,4})\s*kg",
                r"capacidad de carga[^0-9]{0,20}(\d{2,4})\s*kg"]:
        mc = re.search(pat, bloque, re.I)
        if mc:
            record["carga_kg"] = int(mc.group(1))
            break

    # Precio publicado en EUR (no se convierte: no se inventa tasa de cambio).
    mp = re.search(r'data-price-amount="([0-9.]+)"', str(soup))
    if mp:
        try:
            record["precio_valor"] = float(mp.group(1))
        except ValueError:
            record["precio_valor"] = None

    # Stock: al 2026-10-11 todos figuran agotados -> no son oferta viva.
    tl = texto.lower()
    record["condicion"] = "agotado" if ("out of stock" in tl or "agotado" in tl) else "nuevo"


# ==================== HELPERS ====================
def _marca_from_titulo(titulo):
    u = titulo.upper()
    for k in ["MAGIC BIKE", "IZUKI", "HUAIHAI", "RALLY", "MIGHONG", "ZONGSHEN", "LONCIN",
              "YAMAHA", "HONDA", "ZNEN", "JIALING", "BAJAJ", "TVS", "PORTO BELLO",
              "JINPEING", "JEINPEING", "FURIKAZAN", "NIPPON", "SK-2101", "SK2101",
              "VEDCA", "ONEBOT", "JINPENG", "JINPEN", "JIPEN", "OIM", "MVP",
              "TOPMAQ", "KVITOVA", "LAITUNG", "RAINBOW", "VIENTO"]:
        if k in u:
            # Errata de la marca JINPENG (confirmada 2026-10-31).
            return "JINPENG" if k in ("JINPEING", "JEINPEING") else k
    m = re.search(r"MARCA[:\s]+([A-Za-z0-9 ]+?)(?:,|Model|$)", titulo, re.I)
    if m:
        return m.group(1).strip()
    return None


def _km_from_text(text):
    if not text:
        return None
    m = re.search(r"(\d{2,3})\s*km\b", text, re.I)
    return int(m.group(1)) if m else None


# ==================== NÚCLEO ====================
def fetch(url):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            # requests asume ISO-8859-1 cuando el servidor no declara charset.
            # vedca.cu lo omite: sin esto 'Autonomía' llega como 'AutonomÃ­a'
            # y la especificación no se detecta.
            if not r.encoding or r.encoding.lower() in ("iso-8859-1", "latin-1"):
                m = re.search(rb"""charset=["']?([\w\-]+)""", r.content[:4096], re.I)
                r.encoding = m.group(1).decode("ascii", "ignore") if m \
                    else (r.apparent_encoding or r.encoding)
            return r.text
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def scrape_source(key, config):
    print(f"\n=== {key.upper()} ===")
    print(f"Listado: {config['url']}")
    try:
        html = fetch(config["url"])
    except Exception as e:
        print(f"  ERROR listado: {type(e).__name__}: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    list_fn = globals()[config["list_parser"]]
    records = list(list_fn(soup, config["url"], config.get("propulsion_hint", "indeterminado")))
    print(f"  Items en listado: {len(records)}")

    detail_fn = globals()[config["detail_parser"]] if config.get("detail_parser") else None
    if not detail_fn:
        print("  (sin página de detalle: specs ya extraídas del listado)")
        return records

    for i, rec in enumerate(records, 1):
        print(f"  [{i}/{len(records)}] Detalle: {rec['url']}")
        try:
            detail_fn(BeautifulSoup(fetch(rec["url"]), "html.parser"), rec)
        except Exception as e:
            print(f"    WARNING detalle: {type(e).__name__}: {e}")
            # Sin detalle no hay ni precio ni modelo: no sirve como registro.
            if rec.get("_requiere_detalle"):
                rec["_descartar"] = True
        time.sleep(REQUEST_DELAY)

    descartados = [r for r in records if r.get("_descartar")]
    if descartados:
        print(f"  Descartadas {len(descartados)} fichas sin datos útiles o no triciclos")
        records = [r for r in records if not r.get("_descartar")]
    return records


def main():
    all_records = []
    for key, config in SOURCES.items():
        try:
            recs = scrape_source(key, config)
            all_records.extend(recs)
            print(f"  -> {len(recs)} registros")
        except Exception as e:
            print(f"  ERROR fuente {key}: {type(e).__name__}: {e}")

    # Dedupe por URL (conserva el primero)
    deduped, seen = [], set()
    for rec in all_records:
        u = rec.get("url")
        if u in seen:
            continue
        seen.add(u)
        deduped.append(rec)

    # Normalización de la identidad del producto (decisión del usuario,
    # 2026-10-19): tabla curada + regla heurística. Los productos excluidos
    # por el usuario no se escriben (pero quedan en la tabla, con su motivo).
    canon = cargar_canonicos()
    normalizados, excluidos, a_revisar = [], [], []
    for rec in deduped:
        motivo = url_excluido(rec.get("url"), canon)
        if motivo:
            excluidos.append((rec.get("url"), motivo))
            continue
        canonizar_registro(rec, canon)
        estado = rec.pop("_estado_norm", "heuristico")
        if estado == "revisar":
            a_revisar.append((rec.get("modelo"), rec.get("marca"), rec.get("url")))
        normalizados.append(rec)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for rec in normalizados:
            out = {k: v for k, v in rec.items() if not k.startswith("_")}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    print(f"\n=== TOTAL: {len(normalizados)} registros únicos en {OUTPUT_FILE} ===")
    if excluidos:
        print(f"    ({len(excluidos)} excluidos por decisión del usuario)")
        for u, m in excluidos:
            print(f"      - {u}: {m}")
    if a_revisar:
        print(f"    ({len(a_revisar)} con nombre de modelo a REVISAR)")
        for mo, ma, u in a_revisar:
            print(f"      - {mo!r} / {ma!r} <- {u}")
    if len(all_records) != len(deduped):
        print(f"    ({len(all_records) - len(deduped)} duplicados por URL eliminados)")

    by_prop, by_src = {}, {}
    for r in normalizados:
        by_prop[r.get("propulsion", "indeterminado")] = by_prop.get(r.get("propulsion"), 0) + 1
        by_src[r.get("fuente", "?")] = by_src.get(r.get("fuente", "?"), 0) + 1
    print("\nPor propulsión:")
    for p, c in sorted(by_prop.items()):
        print(f"  {p}: {c}")
    print("Por fuente:")
    for s, c in sorted(by_src.items()):
        print(f"  {s}: {c}")

    if not normalizados:
        print("\nADVERTENCIA: 0 registros.")


if __name__ == "__main__":
    main()
