#!/usr/bin/env python3
"""
Extractor de fichas de triciclos desde CATÁLOGOS DE EMPRESAS (dataset aparte).

Motivación (2026-10-12, decisión del usuario): además de los clasificados y
tiendas ya cubiertos por scrape_triciclos.py, se quieren extraer las fichas que
las empresas publican en su PROPIO catálogo. Este script es independiente: NO
toca el pipeline de triciclos y escribe un JSONL por empresa en Data/empresas/.

Empresas incluidas (elegidas con el usuario; alcance: triciclos, entrega en La
Habana):
  ✅ kikihabana        — kikihabana.com (WooCommerce). Categoría
                        'carritos-y-triciclos'; se EXCLUYEN los 'carrito' (son
                        de 4 ruedas, no triciclos). Specs + precio en la ficha.
  ✅ mzproducts        — mzproducts.com (WooCommerce; sede Miami, recogida en La
                        Habana). Specs etiquetadas: 'Potencia del motor',
                        'Capacidad de la batería', 'Autonomía por carga completa'.
  ✅ acubaenvioscargo  — acubaenvioscargo.com (WooCommerce/Woodmart). Grid sin
                        página de detalle: las specs se leen del título.
  ⚠️ mrcuba            — mrcubamiami.com (Wix, página única y frágil). Solo se
                        extraen modelo y precio (van en el alt de las imágenes).
  ✅ compramasonline   — compramasonline.com (WooCommerce/Woodmart, 2026-10-31).
                        Categoría 'Triciclos': 11 productos, de los que 8 son
                        triciclos. Se EXCLUYEN los 2 'Extensor de rango' (son
                        accesorios, no vehículos) y el 'Minicarrito' (4 ruedas).
                        Specs en la pestaña de descripción; precio con `ins`
                        (rebajas: se toma el precio actual, no el tachado).
  ✅ mundoenvio        — mundoenvio.com (WooCommerce, 2026-10-31). Categoría
                        'Triciclos Eléctricos': 10 triciclos; se excluye el
                        'Mini triciclo 4 ruedas' (cuatriciclo).
  ✅ patuisla          — patuisla.com (WooCommerce, 2026-10-31). Categoría
                        'Envío de Triciclos a Cuba': 11 fichas. En varias, las
                        specs están en el resumen (.summary), no en la pestaña.
  ✅ francismotors      — francismotors.org (estático, JSON-LD Product, 2026-10-31).
                        11 triciclos (eléctricos, híbridos y de gasolina).
  ✅ bluewavecuba      — bluewavecuba.com (estático/Next.js, 2026-10-31). 5
                        triciclos con especificaciones en pares <dt>/<dd>.
  ✅ zonalibreonline   — zonalibreonline.com (WooCommerce, 2026-10-31). 2
                        triciclos; specs en el JSON-LD y en og:image:alt.

Fuera de alcance / descartadas (verificado 2026-10-12 y 2026-10-31):
  ❌ kubazuki.com      → 'pronto en línea' (sin catálogo; sigue así el 2026-10-31)
  ❌ VoltHabana        → su catálogo no tiene triciclos (solo repuestos)
  ❌ TriSol (trisol.es)→ Pinar del Río; vende kits solares, no triciclos
  ❌ vedca.cu          → caído; su catálogo ya se cubre vía islagrande
  ❌ multiservicesxpress → su buscador no devuelve triciclos (solo bicis)
  ❌ sunwellcaribe, cubamax, cuballama, mallhabana, dimecuba → sin triciclos
  ❌ micasaia.com      → 2 'tricimotos'; precio publicado como 'PRECIO DE
                        COMPRA' y nombre que mezcla marca/modelo. No se mezcla
                        con triciclos de carga.
  ❌ smilemotors.online → SPA React sin catálogo en el HTML y tienda sin
                        respuesta (curl 000); no se localizó API pública.
  ❌ cubancargos       → ya lo cubre scrape_triciclos.py (dataset de anuncios):
                        añadirlo aquí duplicaría los mismos 4 productos
  Nota: las MIPYMEs cubanas (MVP, MZ Productions, etc.) publican en Revolico y
  Facebook, ambos bloqueados, así que su 'catálogo' no es extraíble.

Esquema de cada registro: el mismo del crudo de triciclos (modelo, marca,
propulsion, motor_w/cc, bateria_v/ah/quimica, autonomia_km, carga_kg, precio,
condicion…) más 'disponibilidad' (texto de stock) y 'fuente' = empresa.
Los precios de estas tiendas se publican en USD (precio_usd + moneda='USD').

Uso:
    python3 codes/scrape_empresas.py              # todas las empresas
    python3 codes/scrape_empresas.py mzproducts   # solo una
"""

import html as html_lib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

# Reutiliza helpers y configuración del scraper principal (sin ejecutarlo:
# main() está protegido por __name__ == "__main__").
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scrape_triciclos as st  # noqa: E402
from norm_modelo import (  # noqa: E402
    canonizar_registro,
    cargar_canonicos,
    url_excluido,
)

DATA_DIR = st.DATA_DIR
OUT_DIR = DATA_DIR / "empresas"


# ==================== EXTRACCIÓN COMÚN ====================
def _texto(el):
    """Texto limpio de un elemento BeautifulSoup (o None)."""
    return st.clean_text(el.get_text(" ", strip=True)) if el else None


def _solo_texto(soup):
    """Texto visible de la página, sin ruido (script/style/nav/footer/...)."""
    copia = BeautifulSoup(str(soup), "html.parser")
    for t in copia(["script", "style", "head", "nav", "footer", "svg", "header", "noscript"]):
        t.decompose()
    return st.clean_text(copia.get_text(" ", strip=True))


# Caracteres cirílicos que 'parecen' latinos (p. ej. '120 АН' de KikiHabana) y
# miles separados por espacio ('3 000W' de MZ): hay que normalizarlos antes de
# buscar batería/motor, o no se detectan.
_RUS_A_LAT = str.maketrans("АВЕКМНОРСТУХаеорсух", "ABEKMHOPCTYXaeopcyx")


def _normaliza(texto):
    if not texto:
        return texto
    texto = texto.translate(_RUS_A_LAT)
    texto = re.sub(r"(?<=\d)\s+(?=\d{3}(?:\D|$))", "", texto)
    # '2,000 W' / '3.000 W' (miles anglosajón y español) -> '2000 W'.
    texto = re.sub(r"(?<=\d)[.,](?=\d{3}(?:\D|$))", "", texto)
    return texto


def _bateria_va(texto):
    """(V, Ah) tolerando separadores: '72V / 60Ah', '72v120AH', '72v80amp',
    'Capacidad de Batería 120 АН' (cirílico) y voltaje/capacidad separados."""
    texto = _normaliza(texto)
    if not texto:
        return None, None
    m = re.search(r"(\d{2,3})\s*[vV]\s*[/\-x·]?\s*(\d{1,3})\s*(?:[aA][hH]?|amp)", texto, re.I)
    if m:
        return int(m.group(1)), int(m.group(2))
    # Solo voltaje declarado: la capacidad queda en None (no se inventa).
    m = re.search(r"(\d{2,3})\s*[vV]\b", texto)
    if m:
        return int(m.group(1)), None
    return st.extract_battery(texto)


def _motor_w(texto):
    """Motor eléctrico en W; prioriza la etiqueta 'motor' sobre un 'W' suelto.

    Se descartan valores > 20.000 W: en estos vehículos son erratas de la
    ficha (p. ej. Mighong de MundoEnvío declara 'Fuerza; 25000W'). No se
    corrige el número: simplemente no se registra como potencia del motor.
    """
    if not texto:
        return None
    texto = _normaliza(texto)
    # Rango declarado ('Motor: 800-1500 W'): límite inferior (convención).
    mr = re.search(r"motor(?:\s*power)?[^0-9]{0,20}(\d{3,5})\s*(?:-|–|a)\s*"
                   r"\d{3,5}\s*(?:w\b|watt)", texto, re.I)
    if mr:
        return int(mr.group(1))
    m = re.search(r"motor(?:\s*power)?[^0-9]{0,20}(\d{3,5})\s*(?:w\b|watt)", texto, re.I)
    if m:
        valor = int(m.group(1))
        if 200 <= valor <= 20000:
            return valor
    valor = st.extract_motor_w(texto)
    if valor and 200 <= valor <= 20000:
        return valor
    return None


def _quimica(texto):
    """Química de batería; amplía el helper con 'lithium' (inglés)."""
    q = st.extract_bateria_quimica(texto)
    if q:
        return q
    if texto and re.search(r"lithium", texto, re.I):
        return "LITIO"
    return None


def _autonomia_km(texto):
    """Límite inferior de la autonomía declarada (convención del proyecto).

    Se exige una etiqueta de autonomía (autonomía/rango/recorrido/kilometraje/
    range) y se descartan los 'km/h' de la velocidad máxima, para no confundir
    'Velocidad máxima: 70 km/h' con la autonomía real (p. ej. 'Hasta 110 km').
    """
    if not texto:
        return None
    # 'Extensor de Rango/Autonomía: 6.000 W' no es la autonomía del vehículo.
    texto = re.sub(r"extensor(?:es)?\s+de\s+(?:autonom[ií]a|rango)",
                   "extensor", texto, flags=re.I)
    m = re.search(r"(?:autonom[ií]a|rango|recorrido|kilometraje|alcance|"
                  r"kil[oó]metros?\s+por\s+carga|gama|range)[^:]{0,30}?:?\s*"
                  r"([^.;\n]{0,90})", texto, re.I)
    if not m:
        # 'Recorrido x carga; 120km según peso' (BOSN): el valor va tras ';'.
        m2 = re.search(r"(?:recorrido|autonom[ií]a|rango|kilometraje|alcance)"
                       r"[^.\n]{0,40}?;\s*[^.;\n]{0,15}?(\d{2,3})\s*km",
                       texto, re.I)
        return int(m2.group(1)) if m2 else None
    scope = re.sub(r"km\s*/\s*h\w*", "", m.group(1), flags=re.I)
    km = st._isla_rango_km(scope)
    if km is None and re.search(r"por\s+carga", m.group(0), re.I):
        # 'Kilómetros por carga: 120' no repite la unidad: la etiqueta ya la dice.
        num = re.search(r"(\d{1,3})", m.group(1))
        if num:
            km = int(num.group(1))
    if km is None:
        # La etiqueta casó pero el valor está tras ';' (BOSN, FUGUIGUAN).
        m2 = re.search(r"(?:recorrido|autonom[ií]a|rango|kilometraje|alcance)"
                       r"[^.\n]{0,40}?;\s*[^.;\n]{0,15}?(\d{2,3})\s*km",
                       texto, re.I)
        if m2:
            km = int(m2.group(1))
    return km


def _carga_kg(texto):
    """Capacidad de carga en kg. Prioriza etiquetas explícitas de capacidad y
    evita el 'peso neto/bruto' del vehículo (p. ej. HUAIHAI: neto 260 kg)."""
    if not texto:
        return None
    for pat in [r"capacidad de carga[^0-9]{0,25}(\d{2,4})\s*kg",
                r"carga (?:m[aá]xima|[uú]til)[^0-9]{0,25}(\d{2,4})\s*kg",
                r"peso m[aá]x(?:imo)?[^0-9]{0,15}(\d{2,4})\s*kg"]:
        m = re.search(pat, texto, re.I)
        if m:
            return int(m.group(1))
    for m in re.finditer(r"(\d{2,4})\s*kg", texto, re.I):
        cola = texto[max(0, m.start() - 30):m.start()].lower()
        if not re.search(r"peso (?:net|brut)", cola):
            return int(m.group(1))
    return None


def _propulsion_catalogo(titulo):
    """Propulsión a partir del título del catálogo (no del texto libre)."""
    t = titulo.lower()
    if re.search(r"h[ií]brid", t):
        return "hibrido"
    electrico = bool(re.search(r"el[eé]ctric\w*|bater|\d{2,3}\s*v\b|\d{3,5}\s*w\b", t))
    gasolina = bool(re.search(r"combusti|gasolina|\d{2,4}\s*cc\b", t))
    if electrico and gasolina:
        return "hibrido"        # motor de gasolina + asistencia eléctrica
    if electrico:
        return "electrico"
    if gasolina:
        return "gasolina"
    return "indeterminado"


def _record(empresa, url):
    """Registro vacío con el esquema del crudo de triciclos."""
    return {
        "modelo": None,
        "marca": None,
        "propulsion": "indeterminado",
        "motor_w": None,
        "motor_cc": None,
        "bateria_v": None,
        "bateria_ah": None,
        "bateria_quimica": None,
        "autonomia_km": None,
        "carga_kg": None,
        "precio_usd": None,
        "precio_desde": False,
        "precio_valor": None,
        "moneda": "USD",
        "ano": None,
        "condicion": "nuevo",
        "disponibilidad": None,
        "legalizacion": None,
        "vendedor_tipo": "empresa",
        "municipio_anuncio": None,
        "url": url,
        "fecha_captura": datetime.now().isoformat(),
        "fuente": empresa,
    }


def _precio(rec, texto):
    valor, desde = st.extract_price_usd(texto or "")
    rec["precio_usd"], rec["precio_desde"], rec["precio_valor"] = valor, desde, valor


# ==================== EMPRESA: KIKIHABANA ====================
KIKI_CAT = "https://kikihabana.com/categoria-producto/carritos-y-triciclos/"


def _es_carrito(titulo, detalle):
    """Los 'carrito eléctrico' de KikiHabana son de 4 ruedas: fuera de alcance.

    Se detectan porque la ficha los llama 'carrito' o menciona '4 ruedas'; los
    triciclos reales (p. ej. ONEBOT) se anuncian como 'triciclo'.
    """
    texto = f"{titulo or ''} {detalle or ''}"
    return (bool(re.search(r"\bcarrito\b", texto, re.I))
            or bool(re.search(r"\b(?:4|cuatro)\s*ruedas", texto, re.I)))


def scrape_kikihabana():
    soup = BeautifulSoup(st.fetch(KIKI_CAT), "html.parser")
    urls = []
    for a in soup.select("a[href*='/producto/']"):
        u = urljoin(KIKI_CAT, a.get("href", ""))
        if u not in urls and "/producto/" in u:
            urls.append(u)

    print(f"  productos en categoría: {len(urls)}")
    recs = []
    for u in urls:
        if re.search(r"envio", u, re.I):          # servicio de envío, no triciclo
            continue
        try:
            dsoup = BeautifulSoup(st.fetch(u), "html.parser")
        except Exception as e:
            print(f"    WARNING detalle {u}: {type(e).__name__}: {e}")
            continue
        titulo = _texto(dsoup.select_one("h1.product_title, h1.product_title.entry-title"))
        if not titulo:
            continue
        resumen = _texto(dsoup.select_one(".woocommerce-product-details__short-description"))
        detalle = " ".join(filter(None, [
            resumen,
            _texto(dsoup.select_one("#tab-description, .woocommerce-Tabs-panel--description, "
                                    ".woocommerce-product-details__description")),
        ]))
        if _es_carrito(titulo, detalle):
            print(f"    - excluido (carrito/4 ruedas): {titulo}")
            continue

        rec = _record("kikihabana", u)
        rec["modelo"] = titulo.upper()
        rec["marca"] = st._marca_from_titulo(titulo)
        rec["propulsion"] = _propulsion_catalogo(titulo + " " + detalle[:600])
        rec["motor_w"] = _motor_w(detalle) if rec["propulsion"] in ("electrico", "hibrido") else None
        rec["motor_cc"] = st.extract_cc(detalle)
        rec["bateria_v"], rec["bateria_ah"] = _bateria_va(detalle)
        rec["bateria_quimica"] = _quimica(detalle)
        rec["autonomia_km"] = _autonomia_km(detalle)
        rec["carga_kg"] = _carga_kg(detalle)
        _precio(rec, _texto(dsoup.select_one("p.price")))

        pagina = _solo_texto(dsoup)
        agotado = bool(re.search(r"agotado|out of stock", pagina, re.I))
        rec["disponibilidad"] = "Agotado" if agotado else "En stock"
        rec["condicion"] = "agotado" if agotado else "nuevo"
        recs.append(rec)
        time.sleep(st.REQUEST_DELAY)
    return recs


# ==================== EMPRESA: MZ PRODUCTS ====================
MZ_SEARCH = "https://www.mzproducts.com/?s=triciclo"


def scrape_mzproducts():
    soup = BeautifulSoup(st.fetch(MZ_SEARCH), "html.parser")
    urls = []
    for a in soup.select("a[href*='/producto/']"):
        u = urljoin(MZ_SEARCH, a.get("href", ""))
        # Solo productos del propio dominio: la página de búsqueda incluye
        # enlaces de 'compartir en Facebook' que también contienen 'triciclo'.
        if urlparse(u).netloc.endswith("mzproducts.com") and "/producto/" in u \
                and "triciclo" in u.lower() and u not in urls:
            urls.append(u)

    print(f"  productos en catálogo: {len(urls)}")
    recs = []
    for u in urls:
        try:
            dsoup = BeautifulSoup(st.fetch(u), "html.parser")
        except Exception as e:
            print(f"    WARNING detalle {u}: {type(e).__name__}: {e}")
            continue
        titulo = _texto(dsoup.select_one("h1.product_title"))
        if not titulo:
            continue
        cuerpo = _solo_texto(dsoup)     # para el estado de stock/disponibilidad
        # Specs: SOLO el bloque de descripción del producto (.wd-single-content).
        # No se usa la página entera: los 'productos relacionados' contaminan la
        # ficha (p. ej. metían specs de otro triciclo de la misma marca).
        ficha = _texto(dsoup.select_one(".wd-single-content")) or ""

        rec = _record("mzproducts", u)
        rec["modelo"] = titulo.upper()
        rec["marca"] = st._marca_from_titulo(titulo) or "MZ PRODUCTS"
        # El slug aporta la propulsión real: 'electrico-combustion-200cc' es un
        # HÍBRIDO aunque el H1 solo diga 'de Combustión' (confirmado por el usuario).
        rec["propulsion"] = _propulsion_catalogo(titulo + " " + urlparse(u).path)
        rec["motor_w"] = _motor_w(ficha) if rec["propulsion"] in ("electrico", "hibrido") else None
        rec["motor_cc"] = st.extract_cc(titulo + " " + ficha)
        rec["bateria_v"], rec["bateria_ah"] = _bateria_va(ficha)
        rec["bateria_quimica"] = _quimica(ficha)
        rec["autonomia_km"] = _autonomia_km(ficha)
        rec["carga_kg"] = _carga_kg(ficha)
        _precio(rec, _texto(dsoup.select_one("p.price")))

        disp = re.search(r"disponible[^.,;:()]{0,45}", cuerpo, re.I)
        texto_disp = st.clean_text(disp.group(0)) if disp else None
        if texto_disp:
            # Recorta ruido de envío/impuestos y corta en la siguiente sección.
            texto_disp = re.split(r"\s+(?:Impuestos|Marítimos|Aproximadamente|"
                                  r"Límite|Precio|Tiempo|Entrega|Recogida)\b",
                                  texto_disp, flags=re.I)[0].strip()
            if re.search(r"costo adicional|env[ií]o|entrega a domicilio", texto_disp, re.I):
                texto_disp = None
        rec["disponibilidad"] = texto_disp
        rec["condicion"] = "agotado" if re.search(r"agotado|out of stock", cuerpo, re.I) else "nuevo"
        recs.append(rec)
        time.sleep(st.REQUEST_DELAY)
    return recs


# ==================== EMPRESA: A CUBA ENVÍOS CARGO ====================
ACUBA_CAT = "https://www.acubaenvioscargo.com/categoria-producto/transporte/triciclos-electricos/"


def scrape_acubaenvioscargo():
    soup = BeautifulSoup(st.fetch(ACUBA_CAT), "html.parser")
    bloques = soup.select(".wd-product-wrapper")
    print(f"  productos en categoría: {len(bloques)}")
    recs = []
    for blk in bloques:
        h3 = blk.select_one("h3.wd-entities-title")
        if not h3:
            continue
        titulo = _texto(h3)

        # No hay página de detalle: se identifica el producto por su id de
        # carrito. Si el producto está "Próximamente" (aún sin botón de
        # compra) no hay id: se usa su PERMALINK, que sí lo identifica.
        mid = re.search(r"add-to-cart=(\d+)", str(blk)) or \
            re.search(r'data-product_id="(\d+)"', str(blk))
        pid = mid.group(1) if mid else None
        if pid:
            url = f"{ACUBA_CAT}?add-to-cart={pid}"
        else:
            permalink = None
            for a in blk.select("a[href]"):
                href = a.get("href", "")
                if "/tienda/" in href:
                    permalink = href
                    break
            url = permalink or ACUBA_CAT

        rec = _record("acubaenvioscargo", url)
        rec["modelo"] = titulo.upper()
        rec["marca"] = st._marca_from_titulo(titulo)
        rec["propulsion"] = _propulsion_catalogo(titulo)
        # La categoría es "Triciclos Eléctricos": si el título no dice el tipo
        # (p.ej. "Triciclo Fly Racing 2027"), la categoría ES el dato.
        if rec["propulsion"] == "indeterminado":
            rec["propulsion"] = "electrico"
        rec["motor_w"] = _motor_w(titulo) if rec["propulsion"] == "electrico" else None
        rec["motor_cc"] = st.extract_cc(titulo)
        # En el título la capacidad viene como 'amp' (=Ah): 72v80amp -> 72 / 80.
        rec["bateria_v"], rec["bateria_ah"] = _bateria_va(titulo)
        rec["bateria_quimica"] = _quimica(titulo)
        _precio(rec, _texto(blk.select_one(".woocommerce-Price-amount")))

        txt = _texto(blk)
        # "Próximamente" va ANTES que "en stock": un producto sin botón de
        # compra aparece con las dos etiquetas y aún no está disponible.
        if re.search(r"pr[oó]ximamente", txt, re.I):
            rec["disponibilidad"] = "Próximamente"
            rec["condicion"] = "nuevo"
        elif re.search(r"en stock", txt, re.I):
            rec["disponibilidad"], rec["condicion"] = "En stock", "nuevo"
        elif re.search(r"agotado|out of stock", txt, re.I):
            rec["disponibilidad"], rec["condicion"] = "Agotado", "agotado"
        recs.append(rec)
    return recs


# ==================== EMPRESA: MR CUBA MIAMI (Wix, best-effort) ====================
MRCUB = "https://mrcubamiami.com/"
_MRC_MODELO = re.compile(r"(Solar|H[eé]rcules|Blue|Tiger|Tank|El[eé]ctric|H[ií]brid)", re.I)


def scrape_mrcuba():
    """Wix sirve una única página; las specs no están en el HTML estático. Se
    extraen modelo y precio del alt de las imágenes (datos finos)."""
    pagina = st.fetch(MRCUB)

    candidatos = {}          # modelo normalizado -> texto crudo
    for a in re.findall(r'alt="([^"]{4,160})"', pagina):
        a = html_lib.unescape(a).strip()
        if _MRC_MODELO.search(a) and re.search(r"triciclo|US\$", a, re.I):
            clave = re.split(r"[,;]", a)[0].strip().upper()
            candidatos.setdefault(clave, a)

    recs = []
    for crudo in candidatos.values():
        # 'Hércules Solar 72V 85Ah, triciclo de carga y pasajeros, precio US$5,900'
        modelo = re.split(r"[,;]", crudo)[0].strip()
        modelo = re.sub(r"^(?:anuncio\s+completo|anuncio|ver|comprar|m[aá]s)\s+",
                        "", modelo, flags=re.I).strip()
        if len(modelo) < 4:
            continue
        mp = re.search(r"(?:US\$|USD|\$)\s*([\d.,]+)", crudo, re.I)
        rec = _record("mrcuba", MRCUB)
        rec["modelo"] = modelo.upper()
        rec["marca"] = st._marca_from_titulo(modelo)
        rec["propulsion"] = _propulsion_catalogo(modelo)
        rec["bateria_v"], rec["bateria_ah"] = _bateria_va(modelo)
        rec["bateria_quimica"] = _quimica(modelo)
        if mp:
            rec["precio_usd"] = st._to_int_price(mp.group(1))
            rec["precio_valor"] = rec["precio_usd"]
        recs.append(rec)
    return recs


# ==================== EMPRESA: COMPRAMASONLINE ====================
CMA_CAT = "https://compramasonline.com/categoria-producto/triciclos/"


def _cma_no_es_triciclo(titulo, url):
    """Excluye accesorios y cuatriciclos de la categoría 'Triciclos'.

    - 'Extensor de rango' (600/650 USD) es un generador de carga, no un
      vehículo. El triciclo RALLY que lo INCLUYE sí entra: su título lo dice.
    - 'Minicarrito' / '4 ruedas' es un cuatriciclo.
    """
    t = f"{titulo or ''} {url or ''}".lower()
    if "minicarrito" in t or re.search(r"\b(?:4|cuatro)\s*-?\s*ruedas\b", t):
        return True
    return "extensor de rango" in t and "triciclo" not in t


def _cma_marca(titulo, ficha):
    """Marca del título o de la etiqueta 'Marca:' de la ficha."""
    marca = st._marca_from_titulo(titulo)
    if marca:
        return marca
    # '... Marca: Minghong Talla: 3200*1200*1800mm ...' → se corta en la
    # siguiente etiqueta de la ficha (Talla, Modelo, Potencia...), no en ':'
    # porque en estas plantillas la marca no lleva dos puntos al final.
    m = re.search(r"marca\s*:\s*([A-Za-z0-9ÁÉÍÓÚÑáéíóúñ][A-Za-z0-9ÁÉÍÓÚÑáéíóúñ ]{1,24}?)"
                  r"(?=\s+(?:Talla|Modelo|Tipo|Color|Tamaño|Peso|Potencia|"
                  r"Voltaje|Uso|Los|Certificación|Lugar|Tiempo|Capacidad|"
                  r"Velocidad|Marca)\b|$)", ficha, re.I)
    return m.group(1).strip().upper() if m else None


def _cma_bateria(ficha):
    """(V, Ah). Prioriza la etiqueta 'Batería' para no confundir el voltaje de
    entrada del cargador ('AC110V') con la batería del vehículo. Si la ficha
    solo declara el voltaje, se devuelve (V, None): no se inventa la capacidad.
    """
    m = re.search(r"bater[ií]as?\s*(?:de\s*)?:?\s*([^.;]{0,70})", ficha, re.I)
    if m:
        v, ah = _bateria_va(m.group(1))
        if v:
            return v, ah
    v, ah = _bateria_va(ficha)
    if v and ah:
        return v, ah
    m = re.search(r"(?:voltaje|tensi[oó]n)\s*:?\s*(\d{2,3})\s*[vV]\b", ficha, re.I)
    if m:
        return int(m.group(1)), None
    return None, None


def _cma_carga(ficha):
    """Capacidad de carga SOLO si la ficha la declara como tal.

    No se usa el peso (neto/bruto/máximo): no es capacidad de carga.
    Si la ficha declara un rango ('2.500 a 3.000 kg'), se toma el límite
    inferior (convención del proyecto).
    """
    ficha = _normaliza(ficha or "")
    for pat in [r"capacidad de carga[^0-9]{0,25}(\d{2,4})\s*(?:-|–|a)\s*\d{2,4}\s*kg",
                r"carga (?:m[aá]xima|[uú]til)[^0-9]{0,25}(\d{2,4})\s*(?:-|–|a)\s*\d{2,4}\s*kg"]:
        m = re.search(pat, ficha, re.I)
        if m:
            return int(m.group(1))
    for pat in [r"capacidad de carga[^0-9]{0,25}(\d{2,4})\s*kg",
                r"carga (?:m[aá]xima|[uú]til|hasta)[^0-9]{0,25}(\d{2,4})\s*kg",
                r"peso m[aá]x(?:imo)?[^0-9]{0,15}(\d{2,4})\s*kg"]:
        m = re.search(pat, ficha, re.I)
        if m:
            return int(m.group(1))
    # 'Capacidad de Carga: 1 tonelada' -> 1.000 kg (conversión de unidad).
    m = re.search(r"capacidad de carga[^0-9]{0,25}(\d+(?:[.,]\d+)?)\s*toneladas?",
                  ficha, re.I)
    if m:
        return int(float(m.group(1).replace(",", ".")) * 1000)
    return None


def _cma_propulsion(titulo, ficha):
    """Propulsión con prioridad a la etiqueta 'Tipo de conducción'.

    Las fichas de esta tienda son plantillas: casi todas cotizan
    'Desplazamiento: <110cc' aunque sean eléctricas; si se mira el texto
    completo, TODAS saldrían híbridas. Solo el RALLY se marca híbrido porque
    su título declara '+ EXTENSOR DE RANGO' (generador de gasolina incluido).
    """
    m = re.search(r"tipo de conducci[oó]n\s*:?\s*(el[eé]ctric\w*|gasolina|"
                  r"combusti[oó]n|h[ií]brid\w*)", ficha, re.I)
    if m:
        palabra = m.group(1).lower()
        if palabra.startswith("el"):
            return "electrico"
        if palabra.startswith("h"):
            return "hibrido"
        return "gasolina"
    if re.search(r"extensor de rango", titulo or "", re.I) and \
            re.search(r"gasolina", ficha, re.I):
        return "hibrido"
    return _propulsion_catalogo(titulo + " " + ficha[:600])


def scrape_compramasonline():
    soup = BeautifulSoup(st.fetch(CMA_CAT), "html.parser")
    urls = []
    for a in soup.select("li.product a[href*='/tienda/']"):
        u = urljoin(CMA_CAT, a["href"])
        if urlparse(u).netloc.endswith("compramasonline.com") and u not in urls:
            urls.append(u)

    print(f"  productos en categoría: {len(urls)}")
    recs = []
    for u in urls:
        try:
            dsoup = BeautifulSoup(st.fetch(u), "html.parser")
        except Exception as e:
            print(f"    WARNING detalle {u}: {type(e).__name__}: {e}")
            continue
        titulo = _texto(dsoup.select_one("h1.product_title")) or \
            _texto(dsoup.select_one("h1"))
        if not titulo:
            continue
        if _cma_no_es_triciclo(titulo, u):
            print(f"    - excluido (accesorio/cuatriciclo): {titulo}")
            continue

        ficha = _texto(dsoup.select_one("#tab-description")) or \
            _texto(dsoup.select_one(".woocommerce-Tabs-panel--description")) or ""

        rec = _record("compramasonline", u)
        rec["modelo"] = titulo.upper()
        rec["marca"] = _cma_marca(titulo, ficha)
        rec["propulsion"] = _cma_propulsion(titulo, ficha)
        rec["motor_w"] = _motor_w(ficha) if rec["propulsion"] in ("electrico", "hibrido") else None
        rec["motor_cc"] = st.extract_cc(titulo + " " + ficha) \
            if rec["propulsion"] in ("gasolina", "hibrido") else None
        rec["bateria_v"], rec["bateria_ah"] = _cma_bateria(ficha)
        rec["bateria_quimica"] = _quimica(ficha)
        rec["autonomia_km"] = _autonomia_km(ficha)
        rec["carga_kg"] = _cma_carga(ficha)

        precio = dsoup.select_one("p.price")
        if precio:
            nodo = (precio.select_one("ins .woocommerce-Price-amount")
                    or precio.select_one(".woocommerce-Price-amount"))
            if nodo:
                valor, desde = st.extract_price_usd(_texto(nodo))
                rec["precio_usd"] = rec["precio_valor"] = valor
                rec["precio_desde"] = desde

        pagina = _solo_texto(dsoup)
        if re.search(r"agotado|out of stock", pagina, re.I):
            rec["disponibilidad"], rec["condicion"] = "Agotado", "agotado"
        else:
            rec["disponibilidad"], rec["condicion"] = "En stock", "nuevo"

        # Trazabilidad: solo cuando el TÍTULO declara el extensor. Hay fichas
        # que copian al final el bloque del extensor como accesorio suelto;
        # eso no prueba que el triciclo lo incluya, así que no se anota.
        if re.search(r"extensor de rango", titulo, re.I):
            rec["notas"] = ("Extensor de rango: generador de carga de gasolina; "
                            "la tracción es eléctrica.")

        recs.append(rec)
        time.sleep(st.REQUEST_DELAY)
    return recs


# ==================== EMPRESAS: CATÁLOGOS NUEVOS (2026-10-31) ====================
# Catálogos verificados por HTTP el 2026-10-31. Todos entregan en Cuba.
#
#   ✅ mundoenvio       — WooCommerce. Categoría 'Triciclos Eléctricos': 11
#                         fichas; se excluye el 'Mini triciclo eléctrico 4
#                         ruedas' (cuatriciclo) -> 10 triciclos.
#   ✅ patuisla         — WooCommerce. Categoría 'Envío de Triciclos a Cuba':
#                         11 fichas. En varias fichas las specs están en el
#                         resumen (.summary), no en la pestaña de descripción.
#   ✅ francismotors    — sitio estático con JSON-LD Product (additionalProperty
#                         + offers.price): 11 triciclos.
#   ✅ bluewavecuba     — sitio estático (Next.js): 5 triciclos con <dl> de
#                         especificaciones. Los nombres son genéricos; la tabla
#                         canónica conserva el nombre declarado (ver OVERRIDES).
#   ✅ zonalibreonline  — WooCommerce. 2 triciclos en el sitemap; specs en el
#                         JSON-LD y en el alt de la imagen (og:image:alt).
#
# Descartados (verificado el 2026-10-31):
#   ❌ micasaia.com     — 2 'tricimotos'; el precio se publica como 'PRECIO DE
#                         COMPRA' y el nombre mezcla marca/modelo (Halcon,
#                         Mountain). No se mezcla con triciclos de carga.
#   ❌ smilemotors.online — SPA React; el HTML no trae catálogo y la tienda no
#                         respondió (curl 000). Sin API pública localizada.
MUNDOENVIO_CAT = "https://mundoenvio.com/categoria-producto/triciclos-electricos/"
PATUISLA_CAT = ("https://patuisla.com/categoria-producto/"
                "envio-a-cuba-de-triciclos-electricos/envio-de-triciclos-a-cuba/")
FRANCIS_CAT = "https://francismotors.org/triciclos/"
BLUEWAVE_CAT = "https://bluewavecuba.com/triciclos"
ZONALIBRE_SITEMAP = "https://zonalibreonline.com/product-sitemap.xml"

# Marcas que aparecen en estos catálogos y que el helper general no conoce.
# Solo se listan las que el vendedor declara en el título o en la ficha.
MARCAS_CATALOGO = (
    "ABL MOTORS", "MISHOZUKI", "FUGUIQUAN", "FUGUIGUAN", "MINGHONG",
    "MIGHONG", "ONEBOT", "HUAIHAI", "JOBANG", "SOTEK", "VEDCA", "IZUKI",
    "TOPMAQ", "CYT", "BOSN", "ZUIMI", "RALLY",
)


def _lista_woo(cat_url, patron):
    """URLs de producto de un listado WooCommerce (li.product)."""
    soup = BeautifulSoup(st.fetch(cat_url), "html.parser")
    urls = []
    for a in soup.select("li.product a[href]"):
        u = urljoin(cat_url, a.get("href", ""))
        if re.search(patron, u) and u not in urls:
            urls.append(u)
    return urls


def _ficha_woo(soup):
    """Texto de la ficha. Si la descripción no trae specs (plantillas de
    Patuisla), se añade el resumen, donde sí están."""
    principal = (_texto(soup.select_one("#tab-description"))
                 or _texto(soup.select_one(".woocommerce-Tabs-panel--description"))
                 or "")
    if re.search(r"bater|voltaje|motor|potencia|capacidad de carga",
                 principal, re.I):
        return principal
    extra = " ".join(filter(None, [
        _texto(soup.select_one(".woocommerce-product-details__short-description")),
        _texto(soup.select_one("div.summary")),
    ]))
    return " ".join(filter(None, [principal, extra]))


def _precio_woo(soup):
    """(precio, es_rango). Si hay rebaja se toma el precio actual (`ins`); si
    hay rango de variantes, el límite inferior."""
    p = soup.select_one("p.price")
    if not p:
        return None, False
    importes = p.select(".woocommerce-Price-amount")
    nodo = p.select_one("ins .woocommerce-Price-amount") or \
        (importes[0] if importes else None)
    valor = st.extract_price_usd(_texto(nodo) or "")[0] if nodo else None
    if valor is None:
        valor = st.extract_price_usd(_texto(p) or "")[0]
    rango = len(importes) >= 2 and bool(re.search(r"[–-]", _texto(p) or ""))
    return valor, rango


def _marca_catalogo(titulo, ficha):
    """Marca declarada en el título o en la etiqueta 'Marca:' de la ficha."""
    u = (titulo or "").upper()
    for k in MARCAS_CATALOGO:
        if re.search(rf"(?<![A-Z]){re.escape(k)}(?![A-Z])", u):
            return k
    return _cma_marca(titulo, ficha)


def _propulsion_ficha(titulo, ficha):
    """Propulsión con la regla del proyecto: un extensor/generador INCLUIDO
    (declarado en el título) hace híbrido el vehículo; si el título dice
    'opción'/'opcional', la tracción sigue siendo eléctrica."""
    t = titulo or ""
    if re.search(r"extensor|generador", t, re.I) and \
            re.search(r"opci[oó]n|opcional", t, re.I):
        m = re.search(r"tipo de conducci[oó]n\s*:?\s*"
                      r"(el[eé]ctric\w*|gasolina|combusti[oó]n|h[ií]brid\w*)",
                      ficha, re.I)
        if m:
            palabra = m.group(1).lower()
            if palabra.startswith("h"):
                return "hibrido"
            if palabra.startswith("g") or palabra.startswith("c"):
                return "gasolina"
        return "electrico"
    if re.search(r"extensor|generador", t, re.I):
        return "hibrido"
    return _cma_propulsion(t, ficha)


def _registro_ficha(empresa, url, soup, disponibilidad=None, notas=None):
    """Registro común para una ficha HTML (WooCommerce o estática)."""
    titulo = (_texto(soup.select_one("h1.product_title"))
              or _texto(soup.select_one("h1")) or "")
    ficha = _ficha_woo(soup)
    rec = _record(empresa, url)
    rec["modelo"] = titulo
    rec["marca"] = _marca_catalogo(titulo, ficha)
    rec["propulsion"] = _propulsion_ficha(titulo, ficha)
    if rec["propulsion"] in ("electrico", "hibrido"):
        rec["motor_w"] = _motor_w(ficha)
        rec["motor_cc"] = None
    else:
        rec["motor_w"] = None
        rec["motor_cc"] = st.extract_cc(titulo + " " + ficha)
    rec["bateria_v"], rec["bateria_ah"] = _cma_bateria(ficha)
    rec["bateria_quimica"] = _quimica(ficha)
    rec["autonomia_km"] = _autonomia_km(ficha)
    rec["carga_kg"] = _cma_carga(ficha)
    rec["precio_usd"], rec["precio_desde"] = _precio_woo(soup)
    rec["precio_valor"] = rec["precio_usd"]

    pagina = _solo_texto(soup)
    if re.search(r"agotado|out of stock|sin existencias", pagina, re.I):
        rec["disponibilidad"], rec["condicion"] = "Agotado", "agotado"
    else:
        rec["disponibilidad"] = disponibilidad or "En stock"
        rec["condicion"] = "nuevo"
    if notas:
        rec["notas"] = notas

    # Trazabilidad de erratas: se conserva la cita, no se corrige el número.
    if rec["motor_w"] is None and re.search(r"25000\s*w", ficha, re.I):
        rec["notas"] = ("La ficha declara 'Fuerza; 25000W' (valor no "
                        "plausible); no se registra motor_w.")
    return rec


def scrape_mundoenvio():
    urls = _lista_woo(MUNDOENVIO_CAT, r"/tienda/[^/]+/?$")
    print(f"  productos en categoría: {len(urls)}")
    recs = []
    for u in urls:
        try:
            soup = BeautifulSoup(st.fetch(u), "html.parser")
        except Exception as e:
            print(f"    WARNING detalle {u}: {type(e).__name__}: {e}")
            continue
        titulo = (_texto(soup.select_one("h1.product_title"))
                  or _texto(soup.select_one("h1")) or "")
        ficha = _ficha_woo(soup)
        if _es_carrito(titulo, ficha):
            print(f"    - excluido (cuatriciclo): {titulo}")
            continue
        notas = None
        if re.search(r"opci[oó]n de extensor", titulo, re.I):
            notas = ("El extensor de rango es opcional; la tracción es "
                     "eléctrica.")
        recs.append(_registro_ficha("mundoenvio", u, soup, notas=notas))
        time.sleep(st.REQUEST_DELAY)
    return recs


def scrape_patuisla():
    urls = _lista_woo(PATUISLA_CAT, r"/producto/[^/]+/?$")
    print(f"  productos en categoría: {len(urls)}")
    recs = []
    for u in urls:
        try:
            soup = BeautifulSoup(st.fetch(u), "html.parser")
        except Exception as e:
            print(f"    WARNING detalle {u}: {type(e).__name__}: {e}")
            continue
        notas = None
        titulo = (_texto(soup.select_one("h1.product_title"))
                  or _texto(soup.select_one("h1")) or "")
        if re.search(r"extensor de rango gratis", titulo, re.I):
            notas = ("Incluye extensor de rango (generador de gasolina); "
                     "la tracción es eléctrica.")
        recs.append(_registro_ficha("patuisla", u, soup, notas=notas))
        time.sleep(st.REQUEST_DELAY)
    return recs


def _ld_product(soup):
    """Primer objeto Product de los bloques JSON-LD (directo o en @graph)."""
    for bloque in soup.select("script[type='application/ld+json']"):
        try:
            data = json.loads(bloque.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        nodos = data if isinstance(data, list) else [data]
        for nodo in nodos:
            if not isinstance(nodo, dict):
                continue
            if nodo.get("@type") == "Product":
                return nodo
            for hijo in nodo.get("@graph") or []:
                if isinstance(hijo, dict) and hijo.get("@type") == "Product":
                    return hijo
    return None


def scrape_francismotors():
    soup = BeautifulSoup(st.fetch(FRANCIS_CAT), "html.parser")
    urls = []
    for a in soup.select("a[href*='/triciclos/']"):
        u = urljoin(FRANCIS_CAT, a.get("href", ""))
        if re.search(r"/triciclos/[^/]+/?$", u) and u not in urls:
            urls.append(u)

    print(f"  productos en categoría: {len(urls)}")
    recs = []
    for u in urls:
        try:
            dsoup = BeautifulSoup(st.fetch(u), "html.parser")
            prod = _ld_product(dsoup)
        except Exception as e:
            print(f"    WARNING detalle {u}: {type(e).__name__}: {e}")
            continue
        if not prod:
            print(f"    WARNING sin JSON-LD Product: {u}")
            continue

        props = {}
        for p in prod.get("additionalProperty") or []:
            k, v = p.get("name"), p.get("value")
            if k and v:
                props[str(k)] = str(v)
        nombre = prod.get("name") or (_texto(dsoup.select_one("h1")) or "")
        desc = prod.get("description") or ""
        ficha = " ".join(f"{k}: {v}." for k, v in props.items()) + " " + desc

        rec = _record("francismotors", u)
        rec["modelo"] = nombre
        rec["marca"] = _marca_catalogo(nombre, ficha)
        # La propulsión sale del nombre y de las specs declaradas; la
        # descripción comercial puede decir 'híbrido' por error (TRION).
        texto_prop = nombre + " " + " ".join(f"{k} {v}" for k, v in props.items())
        texto_prop = texto_prop.lower()
        if "híbrid" in texto_prop or "hibrid" in texto_prop or \
                any("extensor" in k.lower() for k in props):
            rec["propulsion"] = "hibrido"
        elif any("cc" in v.lower() for k, v in props.items() if "motor" in k.lower()):
            rec["propulsion"] = "gasolina"
        elif any(k.lower().startswith("bater") for k in props) or \
                any("motor" in k.lower() and "w" in v.lower() for k, v in props.items()):
            rec["propulsion"] = "electrico"
        else:
            rec["propulsion"] = _propulsion_catalogo(nombre)

        if rec["propulsion"] in ("electrico", "hibrido"):
            rec["motor_w"] = _motor_w(ficha)
            rec["motor_cc"] = None
        else:
            rec["motor_w"] = None
            rec["motor_cc"] = st.extract_cc(ficha)
        rec["bateria_v"], rec["bateria_ah"] = _cma_bateria(ficha)
        rec["bateria_quimica"] = _quimica(ficha)
        rec["autonomia_km"] = _autonomia_km(ficha)
        rec["carga_kg"] = _cma_carga(ficha)

        oferta = prod.get("offers") or {}
        if isinstance(oferta, list):
            oferta = oferta[0] if oferta else {}
        precio = oferta.get("price")
        if precio is not None:
            rec["precio_usd"] = rec["precio_valor"] = st._to_int_price(str(precio))
        disp = str(oferta.get("availability") or "")
        if "OutOfStock" in disp:
            rec["disponibilidad"], rec["condicion"] = "Agotado", "agotado"
        else:
            rec["disponibilidad"], rec["condicion"] = "En stock", "nuevo"
        recs.append(rec)
        time.sleep(st.REQUEST_DELAY)
    return recs


def _ficha_bluewave(soup):
    """Las specs de Bluewave son pares <dt>/<dd>; se descartan las entradas
    del glosario (valores largos) y se conserva el primer valor de cada
    etiqueta."""
    pares = {}
    for dt in soup.select("dt"):
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        k, v = _texto(dt), _texto(dd)
        if not k or not v or len(v) > 80:
            continue
        pares.setdefault(k, v)
    return " ".join(f"{k}: {v}." for k, v in pares.items())


def scrape_bluewave():
    soup = BeautifulSoup(st.fetch(BLUEWAVE_CAT), "html.parser")
    urls = []
    for a in soup.select("a[href*='/triciclos/']"):
        u = urljoin(BLUEWAVE_CAT, a.get("href", ""))
        if re.search(r"/triciclos/[^/]+/?$", u) and u not in urls:
            urls.append(u)

    print(f"  productos en catálogo: {len(urls)}")
    recs = []
    for u in urls:
        try:
            dsoup = BeautifulSoup(st.fetch(u), "html.parser")
        except Exception as e:
            print(f"    WARNING detalle {u}: {type(e).__name__}: {e}")
            continue
        titulo = _texto(dsoup.select_one("h1")) or ""
        ficha = _ficha_bluewave(dsoup)
        rec = _record("bluewavecuba", u)
        rec["modelo"] = titulo
        rec["marca"] = None          # el catálogo no declara marca
        rec["propulsion"] = _propulsion_ficha(titulo, ficha)
        # El 'extensor de autonomía' de Bluewave es un generador auxiliar
        # (así lo define su glosario): el vehículo es híbrido.
        if re.search(r"extensor de autonom[ií]a", ficha, re.I):
            rec["propulsion"] = "hibrido"
        rec["motor_w"] = _motor_w(ficha) \
            if rec["propulsion"] in ("electrico", "hibrido") else None
        rec["motor_cc"] = None
        rec["bateria_v"], rec["bateria_ah"] = _cma_bateria(ficha)
        rec["bateria_quimica"] = _quimica(ficha)
        rec["autonomia_km"] = _autonomia_km(ficha)
        rec["carga_kg"] = _cma_carga(ficha)

        for p in dsoup.select("p.tabular"):
            t = _texto(p) or ""
            if t.startswith("US$"):
                rec["precio_usd"] = rec["precio_valor"] = \
                    st.extract_price_usd(t)[0]
                break

        pagina = _solo_texto(dsoup)
        if re.search(r"consultar disponibilidad", pagina, re.I):
            rec["disponibilidad"] = "Consultar disponibilidad"
        elif re.search(r"agotado|out of stock", pagina, re.I):
            rec["disponibilidad"], rec["condicion"] = "Agotado", "agotado"
        else:
            rec["disponibilidad"] = "En stock"
        rec["condicion"] = rec.get("condicion") or "nuevo"
        if re.search(r"extensor de autonom[ií]a", ficha, re.I):
            rec["notas"] = ("Incluye extensor de autonomía (generador); "
                            "la tracción es eléctrica.")
        recs.append(rec)
        time.sleep(st.REQUEST_DELAY)
    return recs


def scrape_zonalibreonline():
    xml = st.fetch(ZONALIBRE_SITEMAP)
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", xml)
            if "/product/" in u and "triciclo" in u.lower()]
    print(f"  productos en sitemap: {len(urls)}")
    recs = []
    for u in urls:
        try:
            dsoup = BeautifulSoup(st.fetch(u), "html.parser")
            prod = _ld_product(dsoup)
        except Exception as e:
            print(f"    WARNING detalle {u}: {type(e).__name__}: {e}")
            continue
        if not prod:
            print(f"    WARNING sin JSON-LD Product: {u}")
            continue

        nombre = prod.get("name") or ""
        marca = None
        brand = prod.get("brand")
        if isinstance(brand, dict):
            marca = brand.get("name")
        # El alt de la imagen suele repetir las specs que no están en el JSON-LD.
        alt = dsoup.select_one("meta[property='og:image:alt']")
        ficha = " ".join(filter(None, [
            prod.get("description") or "",
            alt.get("content") if alt else "",
        ]))

        rec = _record("zonalibreonline", u)
        rec["modelo"] = nombre
        rec["marca"] = _marca_catalogo(nombre, ficha) or marca
        rec["propulsion"] = _propulsion_ficha(nombre, ficha)
        rec["motor_w"] = _motor_w(ficha) \
            if rec["propulsion"] in ("electrico", "hibrido") else None
        rec["motor_cc"] = None
        rec["bateria_v"], rec["bateria_ah"] = _cma_bateria(ficha)
        rec["bateria_quimica"] = _quimica(ficha)
        rec["autonomia_km"] = _autonomia_km(ficha)
        rec["carga_kg"] = _cma_carga(ficha)

        oferta = prod.get("offers") or {}
        if isinstance(oferta, list):
            oferta = oferta[0] if oferta else {}
        if oferta.get("price") is not None:
            rec["precio_usd"] = rec["precio_valor"] = \
                st._to_int_price(str(oferta["price"]))
        disp = str(oferta.get("availability") or "")
        if "OutOfStock" in disp:
            rec["disponibilidad"], rec["condicion"] = "Agotado", "agotado"
        else:
            rec["disponibilidad"], rec["condicion"] = "En stock", "nuevo"
        recs.append(rec)
        time.sleep(st.REQUEST_DELAY)
    return recs


# ==================== NÚCLEO ====================
EMPRESAS = {
    "kikihabana": scrape_kikihabana,
    "mzproducts": scrape_mzproducts,
    "acubaenvioscargo": scrape_acubaenvioscargo,
    "mrcuba": scrape_mrcuba,
    "compramasonline": scrape_compramasonline,
    "mundoenvio": scrape_mundoenvio,
    "patuisla": scrape_patuisla,
    "francismotors": scrape_francismotors,
    "bluewavecuba": scrape_bluewave,
    "zonalibreonline": scrape_zonalibreonline,
}


def main(argv):
    solo = argv[1] if len(argv) > 1 else None
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for clave, fn in EMPRESAS.items():
        if solo and clave != solo:
            continue
        print(f"\n=== {clave.upper()} ===")
        try:
            recs = fn()
        except Exception as e:
            print(f"  ERROR {clave}: {type(e).__name__}: {e}")
            continue
        # Normalización de la identidad del producto (decisión del usuario,
        # 2026-10-19): la tabla curada manda; lo que no esté en ella se
        # resuelve con la regla de codes/norm_modelo.py.
        canon = cargar_canonicos()
        salida_recs, a_revisar = [], []
        for r in recs:
            if url_excluido(r.get("url"), canon):
                continue
            canonizar_registro(r, canon)
            if r.pop("_estado_norm", "heuristico") == "revisar":
                a_revisar.append((r.get("modelo"), r.get("marca"), r.get("url")))
            salida_recs.append(r)
        salida = OUT_DIR / f"{clave}.jsonl"
        with open(salida, "w", encoding="utf-8") as f:
            for r in salida_recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  -> {len(salida_recs)} registros en {salida}")
        for mo, ma, u in a_revisar:
            print(f"     REVISAR: {mo!r} / {ma!r} <- {u}")

    if not solo:
        print(f"\n=== Fin. Datasets por empresa en {OUT_DIR} ===")


if __name__ == "__main__":
    main(sys.argv)
