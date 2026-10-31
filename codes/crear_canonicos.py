#!/usr/bin/env python3
"""
Genera `Data/modelos_canonicos.json`: la tabla de nombres de modelo CURADA.

La tabla se construye a partir de `Data/clean_data/` (los nombres que el
usuario revisó a mano el 2026-10-19) más las separaciones de variante que
decidió ese mismo día, y se versiona en el repo: es la fuente de verdad de
la identidad de cada producto.

Reglas aplicadas al construir la tabla:
  - clave = URL del producto (estable entre corridas; un producto = una URL);
  - `por_url`: {modelo, marca} canónicos;
  - `excluidos`: URL + motivo (productos que el usuario decidió dejar fuera);
  - `variantes`: separaciones explícitas de productos que comparten nombre
    pero NO son el mismo (specs distintas) -> se cuentan por separado.

Uso:
    python3 codes/crear_canonicos.py            # escribe Data/modelos_canonicos.json
    python3 codes/crear_canonicos.py --check     # solo muestra el resumen
"""

import json
import subprocess
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
CLEAN_DIR = DATA_DIR / "clean_data"
OUT_PATH = DATA_DIR / "modelos_canonicos.json"

# ---- Separaciones de variante decididas por el usuario (2026-10-19) ----
# "si no son exactamente iguales, déjalos separados y cuéntalos por separado"
#
# NOTA (2026-10-19, 2ª corrección del usuario): los tres "E-CARGO" de MZ
# Products VUELVEN al mismo nombre ("E-CARGO MZ PRODUCTS") porque la
# capacidad ya está en su propio campo (bateria_ah). Se conservan como
# fichas separadas en las tablas, pero comparten identidad: si el dataset de
# empresas entrara en el scoring, se agregarían. Queda anotado como riesgo
# en el reporte (Limitaciones).
VARIANTES = {
    # RALLY de KikiHabana: el de carga (2.000 kg) es un producto distinto del
    # de pasajeros, que ya se llama solo "RALLY" (ver OVERRIDES).
    "https://kikihabana.com/producto/triciclos-para-cuba/":
        ("RALLY CARGA", "RALLY"),
    # VEDCA C800B: el "fotovoltaico" es una variante con panel (precio propio).
    "https://islagrande.com/triciclo-electrico-carga-pasajeros-c800b-fotovoltaico-lifepo4-60v-90ah-habana.html":
        ("VEDCA C800B FOTOVOLTAICO", "VEDCA"),
}

# ---- Nombres fijados a mano (2026-10-19) ----
# "Fly Racing 2027" de A Cuba Envíos Cargo: no tiene specs en el título ni
# botón de compra (está "Próximamente"), así que se identifica por su
# permalink. El usuario le puso la misma marca "RACING" que a los otros
# dos Fly Racing.
OVERRIDES = {
    "https://www.acubaenvioscargo.com/tienda/transporte/triciclos-electricos/triciclo-fly-racing-2027/":
        ("FLY RACING 2027", "RACING"),
    # Cubancargos escribe "JINPEING" en el título y la URL; es una errata de
    # la marca JINPENG (confirmado por el usuario, 2026-10-31). Se corrige el
    # nombre canónico en el origen, no el JSONL a mano. El producto sigue
    # siendo un híbrido distinto del JINPENG eléctrico (la propulsión y las
    # specs no se tocan).
    "https://cubancargos.com/triciclos/electricos-cuba/triciclo-jeinpeing":
        ("JINPENG", "JINPENG"),
    # "PASAJE"/"PASAJEROS" son descriptores de uso, no nombres de modelo
    # (decisión del usuario, 2026-10-31): se eliminan del nombre canónico.
    # OIM: el anuncio "de pasaje" queda en la identidad OIM (misma batería y
    # autonomía que el "disponible"; el precio distinto se conserva como
    # oferta, no como producto).
    "https://elyerromenu.com/b/cuba-sobre-ruedas/product/triciclos-oim-de-pasaje":
        ("OIM", "OIM"),
    # RALLY de KikiHabana: queda RALLY; no colisiona con RALLY CARGA,
    # RALLY HIBRIDO ni RALLY CARGA 800.
    "https://kikihabana.com/producto/triciclos-electricos-para-cuba-2/":
        ("RALLY", "RALLY"),
    # RALLY con extensor de rango de CompraMasonline: el título de la tienda
    # trae el accesorio ('... + EXTENSOR DE RANGO'). El extensor queda
    # documentado en el campo `notas` del registro.
    #
    # Variantes RALLY/CYT/MIGHONG/IZUKI separadas el 2026-10-31 (decisión del
    # usuario): si dos fichas del mismo nombre declaran specs distintas, van
    # como identidades distintas. El sufijo solo usa el dato declarado que
    # diferencia la ficha, no una estimación.
    "https://compramasonline.com/tienda/triciclo-de-carga-rally/":
        ("RALLY HIBRIDO", "RALLY"),
    # KikiHabana: mismas variantes que los catálogos nuevos (CYT 80 km,
    # IZUKI 120 Ah, MIGHONG 400 kg). Así cada identidad conserva su spec.
    "https://kikihabana.com/producto/triciclo-panel-solar-para-cuba/":
        ("CYT 80 KM", "CYT"),
    "https://kikihabana.com/producto/triciclo-electrico-para-cuba-2/":
        ("IZUKI 120 AH", "IZUKI"),
    "https://kikihabana.com/producto/mighong-panel-solar/":
        ("MIGHONG 400 KG", "MIGHONG"),
    # ---- Catálogos añadidos el 2026-10-31 ----
    # Se conserva el nombre declarado (sin quitar specs que forman parte del
    # modelo, p. ej. '250 CC') y se separan las variantes que, tras la
    # limpieza heurística, quedarían con el mismo nombre.
    # MundoEnvío
    "https://mundoenvio.com/tienda/triciclo-electrico-para-cuba-2/":
        ("BOSN BBX-S600", "BOSN"),
    "https://mundoenvio.com/tienda/triciclo-electrico-para-cuba/":
        ("CYT 80 KM", "CYT"),
    "https://mundoenvio.com/tienda/triciclo-electrico-para-cuba-5/":
        ("RALLY CARGA 800", "RALLY"),
    "https://mundoenvio.com/tienda/envio-a-cuba-de-triciclo-electrico/":
        ("FUGUIGUAN", "FUGUIGUAN"),
    "https://mundoenvio.com/tienda/triciclo-electrico-para-cuba-3/":
        ("JOBANG ZUIMI", "JOBANG"),
    "https://mundoenvio.com/tienda/triciclo-electrico-mighong-con-panel-solar/":
        ("MIGHONG 600 KG", "MIGHONG"),
    "https://mundoenvio.com/tienda/triciclo-electrico-para-cuba-4/":
        ("ONEBOT", "ONEBOT"),
    "https://mundoenvio.com/tienda/triciclo-electrico-de-carga/":
        ("MINGHONG", "MINGHONG"),
    "https://mundoenvio.com/tienda/triciclo-pasajero-para-cuba/":
        ("HUAIHAI", "HUAIHAI"),
    "https://mundoenvio.com/tienda/triciclo-marca-sotek/":
        ("SOTEK", "SOTEK"),
    # Patuisla (mismos productos que MundoEnvío cuando comparten nombre)
    "https://patuisla.com/producto/triciclo-panel-solar/":
        ("CYT 100 KM", "CYT"),
    "https://patuisla.com/producto/triciclo-electrico-para-cuba/":
        ("HUAIHAI", "HUAIHAI"),
    "https://patuisla.com/producto/triciclo-electrico-para-cuba-3/":
        ("IZUKI 127 AH", "IZUKI"),
    "https://patuisla.com/producto/triciclos-electricos-para-cuba/":
        ("JOBANG ZUIMI", "JOBANG"),
    "https://patuisla.com/producto/triciclo-panel-solar-para-cuba/":
        ("MIGHONG 400 KG", "MIGHONG"),
    "https://patuisla.com/producto/triciclo-electrico-para-cuba-4/":
        ("MISHOZUKI ULTRA", "MISHOZUKI"),
    "https://patuisla.com/producto/triciclos-electricos-para-cuba-2/":
        ("ONEBOT", "ONEBOT"),
    "https://patuisla.com/producto/triciclo-electrico-panel-solar/":
        ("RICKSHAW", None),
    "https://patuisla.com/producto/triciclos-electricos-para-cuba-3/":
        ("RALLY CARGA", "RALLY"),
    "https://patuisla.com/producto/triciclo-electrico-para-cuba-2/":
        ("FUGUIGUAN EXTENSOR", "FUGUIGUAN"),
    "https://patuisla.com/producto/vedca-c800/":
        ("VEDCA C800", "VEDCA"),
    # Francis Motors
    "https://francismotors.org/triciclos/blue-carga-1000w/":
        ("BLUE CARGA 1000W", None),
    "https://francismotors.org/triciclos/bravo-250-cc/":
        ("BRAVO 250 CC", None),
    "https://francismotors.org/triciclos/dg-blue-72v/":
        ("DG BLUE 72V", None),
    "https://francismotors.org/triciclos/fenix-hibrido/":
        ("FENIX HIBRIDO", None),
    "https://francismotors.org/triciclos/hercules-pro/":
        ("HERCULES PRO HIBRIDO 72V 85AH", None),
    "https://francismotors.org/triciclos/phantom-200cc/":
        ("PHANTOM 200CC", None),
    "https://francismotors.org/triciclos/tiger-1800w-hibrido-72v-65ah/":
        ("TIGER 1800W HIBRIDO 72V 65AH", None),
    "https://francismotors.org/triciclos/tiger-hibrido/":
        ("TIGER HIBRIDO", None),
    "https://francismotors.org/triciclos/topmaq-2000w/":
        ("TOPMAQ 2000W", "TOPMAQ"),
    "https://francismotors.org/triciclos/trion-fm-151/":
        ("TRION FM-151", None),
    "https://francismotors.org/triciclos/white-trek-250cc-4t/":
        ("WHITE TREK 250CC 4T", None),
    # Bluewave Logistics: el catálogo no declara marca ni modelo propio; se
    # conserva el nombre tal como lo publica la tienda.
    "https://bluewavecuba.com/triciclos/tiger":
        ("TIGER", None),
    "https://bluewavecuba.com/triciclos/triciclo-hibrido-solar":
        ("TRICICLO HIBRIDO SOLAR", None),
    "https://bluewavecuba.com/triciclos/triciclo-hibrido-litio":
        ("TRICICLO HIBRIDO LITIO", None),
    "https://bluewavecuba.com/triciclos/triciclo-jmd-hibrido":
        ("TRICICLO JMD HIBRIDO", None),
    "https://bluewavecuba.com/triciclos/triciclo-electrico":
        ("TRICICLO ELECTRICO", None),
    # Zona Libre Online
    "https://zonalibreonline.com/product/triciclo-electrico-abl-con-panel-solar/":
        ("ABL PANEL SOLAR", "ABL MOTORS"),
    "https://zonalibreonline.com/product/triciclo-electrico-mishozuki-e-cargo/":
        ("MISHOZUKI E-CARGO 8000W", "MISHOZUKI"),
}

# ---- Productos que el usuario decidió dejar fuera (2026-10-19) ----
# "TRICICLOS HIBRIDOS MEJOR PRECIO": nombre 100% publicitario, sin modelo
# identificable; era una de las 3 ofertas con precio contradictorio declaradas
# como limitación. Se excluye, pero queda constancia del motivo para que una
# corrida futura no lo resucite en silencio.
EXCLUIDOS = {
    "https://elyerromenu.com/b/cuba-sobre-ruedas/product/triciclos-hibridos-el-mejor-precio-de":
        "Nombre 100% publicitario ('MEJOR PRECIO'), sin modelo identificable; "
        "excluido por decisión del usuario (2026-10-19).",
    # CompraMasonline: ficha sin modelo propio ('TRICICLO ELÉCTRICO DE CARGA')
    # que cae en la marca MINGHONG y duplica la identidad del otro MINGHONG
    # con distinto precio ($2.500 vs $2.580). Se excluye el genérico y se
    # conserva el que sí se puede nombrar (decisión del usuario, 2026-10-31).
    "https://compramasonline.com/tienda/triciclo-electrico-de-carga/":
        "Sin modelo propio; duplica la identidad de MINGHONG con otro precio; "
        "excluido por decisión del usuario (2026-10-31).",
    # MundoEnvío: el 'Mini triciclo eléctrico 4 ruedas' es un cuatriciclo.
    "https://mundoenvio.com/tienda/carrito-electrico-para-cuba/":
        "Cuatriciclo ('4 ruedas'), fuera del alcance de triciclos.",
}

# ---- Ficheros que el usuario NO curó: se conservan tal cual y se avisa ----
# (2026-10-19: acubaenvioscargo ya quedó curado por el usuario → vacío)
SIN_CURAR = set()

# ---- Pares (curado -> crudo) para poder desambiguar por el nombre original ----
# El fichero crudo conserva el nombre tal como venía de la web; sirve para
# distinguir productos que comparten URL (mrcuba: una sola página de Wix).
ORIGEN_CRUDE = {
    "anuncios_triciclos.jsonl": "raw_data/anuncios_triciclos.jsonl",
    "kikihabana.jsonl": "empresas/kikihabana.jsonl",
    "mzproducts.jsonl": "empresas/mzproducts.jsonl",
    "mrcuba.jsonl": "empresas/mrcuba.jsonl",
    "acubaenvioscargo.jsonl": "empresas/acubaenvioscargo.jsonl",
    "compramasonline.jsonl": "empresas/compramasonline.jsonl",
    "mundoenvio.jsonl": "empresas/mundoenvio.jsonl",
    "patuisla.jsonl": "empresas/patuisla.jsonl",
    "francismotors.jsonl": "empresas/francismotors.jsonl",
    "bluewavecuba.jsonl": "empresas/bluewavecuba.jsonl",
    "zonalibreonline.jsonl": "empresas/zonalibreonline.jsonl",
}


def _nombres_crudos(rel):
    """Nombres originales de los productos de un fichero crudo.

    Se lee primero la versión del último commit (el fichero crudo se
    normaliza al migrar, así que los nombres originales ya no están en el
    archivo de trabajo) y, si no está en git, el fichero actual.
    """
    ruta = DATA_DIR / rel
    try:
        # Ruta RELATIVA a la raíz del repo (git la necesita así).
        rel_repo = ruta.relative_to(DATA_DIR.parent).as_posix()
        out = subprocess.run(["git", "show", f"HEAD:{rel_repo}"],
                             capture_output=True, text=True, check=True).stdout
        lineas = out.strip().split("\n")
    except Exception:
        if not ruta.exists():
            return {}
        lineas = [l for l in open(ruta, encoding="utf-8").read().split("\n") if l.strip()]
    res = {}
    for l in lineas:
        l = l.strip()
        if not l:
            continue
        try:
            rr = json.loads(l)
        except json.JSONDecodeError:
            continue
        nombre = (rr.get("modelo") or "").strip().upper()
        res.setdefault(rr.get("url"), []).append(nombre)
    return res


def main():
    check = "--check" in sys.argv
    por_url = {}
    pendientes = {}

    for f in sorted(CLEAN_DIR.glob("*.jsonl")):
        # Nombre original del mismo producto (fichero crudo): permite
        # desambiguar cuando una URL sirve a varios productos.
        crudo_por_url = {}
        rel = ORIGEN_CRUDE.get(f.name)
        if rel:
            crudo_por_url = _nombres_crudos(rel)

        # ¿Alguna URL de este fichero sirve a más de un producto?
        conteo = {}
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            u = r.get("url")
            if u and u not in EXCLUIDOS:
                conteo[u] = conteo.get(u, 0) + 1

        vistos = {}
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            url = r.get("url")
            if not url or url in EXCLUIDOS:
                continue
            if url in OVERRIDES:
                modelo, marca = OVERRIDES[url]
                por_url[url] = {"modelo": modelo, "marca": marca, "origen": "manual"}
                continue
            if url in VARIANTES:
                modelo, marca = VARIANTES[url]
                por_url[url] = {"modelo": modelo, "marca": marca, "origen": "variante"}
                continue

            if conteo.get(url, 0) > 1:
                # Varios productos con la misma URL: se guardan como opciones y
                # se elige la que casa con el nombre original; si el nombre ya
                # está normalizado, se usa la propulsión como discriminante
                # (mrcuba: la página única de Wix sirve dos productos).
                idx = vistos.get(url, 0)
                vistos[url] = idx + 1
                crudos = crudo_por_url.get(url, [])
                match = crudos[idx] if idx < len(crudos) else (r.get("modelo") or "")
                por_url.setdefault(url, {"opciones": []})["opciones"].append({
                    "match": match,
                    "propulsion": (r.get("propulsion") or "").lower(),
                    "modelo": r.get("modelo"),
                    "marca": r.get("marca"),
                    "origen": "curado",
                })
                continue

            por_url[url] = {
                "modelo": r.get("modelo"),
                "marca": r.get("marca"),
                "origen": "curado",
            }
            if f.name in SIN_CURAR:
                pendientes[url] = f.name

    # Los productos de Facebook comparten la misma URL base con variantes
    # distintas (permisos); la clave por URL no los distingue, así que para
    # Facebook se indexa además por (marca, modelo) en la tabla de alias del
    # análisis. Aquí solo se registran las URLs canónicas de las fichas
    # scrapeadas (una URL = un producto).
    # Los overrides manuales se añaden SIEMPRE, aunque el producto todavía no
    # esté en clean_data (p.ej. un producto recién captado por el scraper):
    # son decisiones del usuario sobre un producto concreto.
    for url, (modelo, marca) in OVERRIDES.items():
        por_url.setdefault(url, {"modelo": modelo, "marca": marca, "origen": "manual"})

    data = {
        "version": "2026-10-19",
        "nota": (
            "Tabla curada de identidad de producto (clave: URL). La usan "
            "codes/norm_modelo.py y los scrapers, de modo que raw_data nace "
            "con los nombres ya normalizados. Editar aquí, no a mano en los "
            "JSONL: la siguiente pasada del scraper sobrescribe lo editado "
            "a mano."
        ),
        "por_url": por_url,
        "excluidos": EXCLUIDOS,
        "sin_curar": pendientes,
    }

    if not check:
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        print(f"-> Escrito: {OUT_PATH}")

    n_mod = sum(1 for v in por_url.values() if v.get("modelo"))
    n_sin = sum(1 for v in por_url.values() if not v.get("modelo"))
    print(f"Productos en la tabla: {len(por_url)} "
          f"(con nombre de modelo: {n_mod}, sin nombre: {n_sin})")
    print(f"Excluidos: {len(EXCLUIDOS)} | variantes separadas: {len(VARIANTES)}")
    print(f"Sin curar por el usuario: {len(pendientes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
