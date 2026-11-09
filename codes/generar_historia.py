#!/usr/bin/env python3
"""
datos.json y datos.js de «La Historia» (página estática historia/index.html).

Por qué existe
--------------
La historia del proyecto se cuenta en una página web aparte (historia/),
no como página del reporte Streamlit. Su regla es la misma del repo:
**ninguna cifra escrita a mano**. Este script lee los archivos versionados
(Data/metadata.json, Data/clean_data/*) y genera historia/datos.json y
historia/datos.js; index.html solo dibuja lo que esos archivos traen. Si
los datos cambian, `--check` falla hasta que se regenere.

Qué se calcula y qué se declara
-------------------------------
- conteos/cortes: tal cual Data/metadata.json (única fuente de cifras).
- pila de anuncios: modelo/fuente/propulsión desde los dos JSONL limpios.
- pesos: espejo de codes/analisis.py::PESOS con su cita corta, tomada de
  Data/fuentes_justificacion.md (texto documental, no dato calculado).
- campo: campo_resumen.csv y campo_uso.csv (cuotas, IC95, uso dominante).
  El campo NO entra al scoring y no se extrapola: aquí tampoco se hace.
- conflicto: comparacion_campo_online.csv para el modelo más anunciado.
- sensibilidad: sensibilidad_resumen.csv (top-12 eléctricos) y líder por
  escenario en sensibilidad_pesos.csv.
- ventana legal: decisión documentada en fuentes_justificacion.md
  (Resolución 47/2026 del MINTRAN; licencias temporales hasta diciembre
  de 2026). Es texto documental del repo, no un dato derivado.
- og.png (solo con --og): tarjeta social 1200×630 con matplotlib. Es
  presentación, no dato: los conteos del pie salen del mismo dict y la
  paleta es espejo de la del HTML.

Uso
---
    python3 codes/generar_historia.py              # escribe historia/datos.{json,js}
    python3 codes/generar_historia.py --check      # falla si el disco no coincide
    python3 codes/generar_historia.py --og         # además renderiza historia/og.png
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data"
CLEAN = DATA / "clean_data"
HISTORIA = ROOT / "historia"
SALIDA_JSON = HISTORIA / "datos.json"
SALIDA_JS = HISTORIA / "datos.js"
SALIDA_OG = HISTORIA / "og.png"

# La identidad del anuncio (regla del 2026-10-19: sin nombre de modelo, la
# identidad es la marca) vive en codes/norm_modelo.py, igual que usa el
# reporte (reporte/data.py::load_anuncios). Se importa por paquete.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from codes.norm_modelo import identidad  # noqa: E402

ANUNCIOS = [CLEAN / "anuncios_triciclos.jsonl",
            CLEAN / "anuncios_facebook.jsonl"]
SCORE = CLEAN / "score_modelos.csv"
CAMPO_RESUMEN = CLEAN / "campo_resumen.csv"
CAMPO_USO = CLEAN / "campo_uso.csv"
COMPARACION = CLEAN / "comparacion_campo_online.csv"
SENS_RES = CLEAN / "sensibilidad_resumen.csv"
SENS_PESOS = CLEAN / "sensibilidad_pesos.csv"

# Espejo de codes/analisis.py::PESOS (script no importable como paquete).
PESOS = {
    "precio_usd": 0.40,
    "autonomia_km": 0.25,
    "carga_kg": 0.20,
    "legalidad": 0.10,
    "repuestos": 0.05,
}

# Citas cortas: de Data/fuentes_justificacion.md (tabla de decisión
# metodológica). Son referencias documentales, no números calculados.
CITAS_PESOS = {
    "precio_usd": "Niu et al. (2024), IEEE Access 12:27931–27946 "
                  "(sensibilidad de pesos ±25%)",
    "autonomia_km": "Hidrue et al. (2011); Hong et al. (2024)",
    "carga_kg": "Orden precio > autonomía > carga "
                "(Hidrue et al., 2011; Hong et al., 2024)",
    "legalidad": "Resolución 47/2026 del MINTRAN (Gaceta Oficial, 4-ago-2026)",
    "repuestos": "ISAHP 2022: mantenimientos y reparaciones pesan poco "
                 "frente al costo en la compra",
}

# Texto documental (fuentes_justificacion.md): ventana del régimen
# excepcional de licencias temporales para triciclos eléctricos sin matrícula.
# La fecha de la Gaceta sale del mismo archivo (Gaceta Oficial, 4-ago-2026).
# *_iso: versión máquina (mes-granularidad) para dibujar la cinta del
# tiempo en el HTML; la fuente tampoco declara día para el cierre.
VENTANA_LEGAL = {
    "ventana": "diciembre de 2026",
    "gaceta": "4 de agosto de 2026",
    "gaceta_iso": "2026-08",
    "cierre_iso": "2026-12",
    "detalle": "Resolución 47/2026 del MINTRAN: régimen excepcional de "
               "licencias temporales para vehículos eléctricos sin "
               "matrícula (categoría A, alcance provincial en La Habana).",
    "fuente": "Data/fuentes_justificacion.md",
}

# Paleta de fuentes: espejo de FUENTE_COLOR en historia/index.html
# (presentación, no dato). Evita los tonos semánticos de propulsión
# (#1f77b4 eléctrico, #ff7f0e híbrido, #d62728 gasolina).
OG_FUENTE_COLOR = {
    "facebook": "#0e7490",
    "elyerromenu": "#8b5cf6",
    "islagrande": "#059669",
    "vedca_telegram": "#d97706",
    "casalindashop": "#ec4899",
    "cubancargos": "#6b7280",
}


def r(x, nd=4):
    """Redondeo determinista para el JSON (o nulo si no hay dato)."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    return round(float(x), nd)


def _num(x):
    """Número o nulo: muchos anuncios no traen precio/motor/autonomía.

    Se declara el vacío (null en JSON), nunca un 0 ni una imputación —
    el popup del HTML muestra 'sin dato' y no un número inventado.
    """
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return round(f, 2)


def construir() -> dict:
    meta = json.loads((DATA / "metadata.json").read_text(encoding="utf-8"))

    datos = {
        "conteos": meta.get("conteos", {}),
        "cortes": meta.get("cortes", {}),
        "legal": VENTANA_LEGAL,
        "pesos": [
            {"criterio": c, "peso": w, "cita": CITAS_PESOS[c]}
            for c, w in PESOS.items()
        ],
        "pila": {"fichas": [], "fuentes": [], "por_propulsion": []},
        "campo": {"marcas": [], "destaca": {}, "uso": {}, "usos": []},
        "conflicto_modelo": {},
        "ranking_electrico": [],
        "ranking_hibrido": [],
        "top2_scores": [],
        "ranking": {"hist_n_anuncios": [], "sin_precio": {}},
        "sensibilidad": {"por_modelo": [], "escena_lider": [],
                         "base_lider": None},
    }

    if not SCORE.exists():
        raise SystemExit(f"[generar_historia] falta {SCORE.relative_to(ROOT)}: "
                         "corre el pipeline antes de generar la historia.")

    # --- Pila de anuncios (apertura) ---
    fichas = []
    partes = [pd.read_json(p, lines=True)
              for p in ANUNCIOS if p.exists()]
    if partes:
        df = pd.concat(partes, ignore_index=True)
        # Mismas normalizaciones que reporte/data.py::load_anuncios():
        # la identidad de pila es la MISMA que rankea (no la columna cruda
        # del JSONL, que solo existe en el de Facebook).
        if "propulsion" in df.columns:
            df["propulsion"] = df["propulsion"].fillna("indeterminado").str.lower()
        df["modelo_norm"] = identidad(df)
        # Cobertura real por anuncio (54/70 con precio, 60/70 autonomía,
        # 50/70 motor_w — lo que trae cada JSONL; nulo = sin dato público).
        orden = df.sort_values(["modelo_norm", "fuente"])
        fichas = [
            {"modelo": fila["modelo_norm"], "fuente": fila["fuente"],
             "propulsion": fila["propulsion"],
             "precio": _num(fila.get("precio_usd")),
             "autonomia": _num(fila.get("autonomia_km")),
             "motor": _num(fila.get("motor_w"))}
            for _, fila in orden.iterrows()
        ]
        fc = df["fuente"].value_counts()
        datos["pila"]["fuentes"] = [
            {"fuente": k, "n": int(v)} for k, v in fc.items()
        ]
        pp = df["propulsion"].value_counts()
        datos["pila"]["por_propulsion"] = [
            {"propulsion": k, "n": int(v)} for k, v in pp.items()
        ]
    datos["pila"]["fichas"] = fichas

    # --- Score: histograma de cobertura, sin precio, top eléctrico ---
    sc = pd.read_csv(SCORE)
    conteo = sc["n_anuncios_total"].value_counts().sort_index()
    datos["ranking"]["hist_n_anuncios"] = [
        {"n": int(n), "modelos": int(m)} for n, m in conteo.items()
    ]
    sin_precio = sorted(sc.loc[
        ~sc["precio_comparable"].fillna(False).astype(bool),
        "modelo_norm"].tolist())
    datos["ranking"]["sin_precio"] = {"n": len(sin_precio),
                                      "modelos": sin_precio}

    elec_top3 = (sc[sc["propulsion"] == "electrico"]
                 .nsmallest(3, "rank_propulsion"))
    datos["ranking_electrico"] = [
        {"rank": int(fila["rank_propulsion"]), "modelo": fila["modelo_norm"],
         "score": r(fila["score"])}
        for _, fila in elec_top3.iterrows()
    ]
    datos["top2_scores"] = [r(s) for s in
                            elec_top3["score"].head(2).tolist()]

    # Podio híbrido: se muestra DENTRO de su propulsión y jamás se compara
    # con el eléctrico (los scores no son comparables entre grupos).
    # n_criterios declara la cobertura: sin dato, el score re-pondera.
    hib_top3 = (sc[sc["propulsion"] == "hibrido"]
                .nsmallest(3, "rank_propulsion"))
    datos["ranking_hibrido"] = [
        {"rank": int(fila["rank_propulsion"]), "modelo": fila["modelo_norm"],
         "score": r(fila["score"]),
         "n_criterios": int(fila["n_criterios"])}
        for _, fila in hib_top3.iterrows()
    ]

    # --- Modelo más anunciado y su fantasma en calle ---
    top_ad = sc.sort_values(
        ["n_anuncios_total", "score", "modelo_norm"],
        ascending=[False, False, True], kind="mergesort").iloc[0]
    fila = {"modelo": top_ad["modelo_norm"],
            "n_anuncios": int(top_ad["n_anuncios_total"]),
            "score": r(top_ad["score"]), "freq_campo": None}
    if COMPARACION.exists():
        comp = pd.read_csv(COMPARACION)
        hit = comp[(comp["modelo_norm"] == top_ad["modelo_norm"])
                   & (comp["propulsion"] == top_ad["propulsion"])]
        if not hit.empty:
            fila["freq_campo"] = int(hit["freq_campo"].iloc[0])
    datos["conflicto_modelo"] = fila

    # --- Campo: marcas (conflicto + IC95) y uso dominante ---
    if CAMPO_RESUMEN.exists():
        mar = pd.read_csv(CAMPO_RESUMEN).sort_values(
            "pct_online", ascending=False, kind="mergesort")
        filas = [
            {"marca": f["marca_norm"], "n_campo": int(f["n_campo"]),
             "pct_campo": r(f["pct_campo"], 2), "pct_online": r(f["pct_online"], 2),
             "delta": r(f["delta_pct"], 2),
             "ic95_bajo": r(f["ic95_bajo"], 2), "ic95_alto": r(f["ic95_alto"], 2)}
            for _, f in mar.iterrows()
        ]
        datos["campo"]["marcas"] = filas
        if filas:
            max_d = max(range(len(filas)), key=lambda i: filas[i]["delta"])
            min_d = min(range(len(filas)), key=lambda i: filas[i]["delta"])
            datos["campo"]["destaca"] = {
                "max_delta": filas[max_d]["marca"],
                "min_delta": filas[min_d]["marca"],
            }
    if CAMPO_USO.exists():
        usos_df = pd.read_csv(CAMPO_USO).sort_values(
            "n", ascending=False, kind="mergesort")
        # Arreglo completo para el waffle del HTML (todas las filas del
        # CSV con su IC95; el campo describe la muestra, no La Habana).
        datos["campo"]["usos"] = [
            {"uso": u["uso"], "n": int(u["n"]), "pct": r(u["pct"], 2),
             "ic95_bajo": r(u["ic95_bajo"], 2), "ic95_alto": r(u["ic95_alto"], 2)}
            for _, u in usos_df.iterrows()
        ]
        # Uso dominante (métrica selección: el HTML lo cita en el Acto 3).
        uso = usos_df.iloc[0]
        datos["campo"]["uso"] = {
            "uso": uso["uso"], "pct": r(uso["pct"], 2),
            "ic95_bajo": r(uso["ic95_bajo"], 2),
            "ic95_alto": r(uso["ic95_alto"], 2),
            "n": int(uso["n"]), "marcas": str(uso["marcas"]),
            "autonomia_med": r(uso["autonomia_med"], 1),
        }

    # --- Sensibilidad (eléctricos): rangos y líder por escenario ---
    if SENS_RES.exists():
        res = pd.read_csv(SENS_RES)
        sub = (res[res["propulsion"] == "electrico"]
               .nsmallest(12, "rank_base"))
        datos["sensibilidad"]["por_modelo"] = [
            {"modelo": f["modelo_norm"], "rank_base": int(f["rank_base"]),
             "top1_pct": r(f["top1_pct"], 2), "top3_pct": r(f["top3_pct"], 2),
             "rank_p05": float(f["rank_p05"]), "rank_p95": float(f["rank_p95"]),
             "rank_min": int(f["rank_min"]), "rank_max": int(f["rank_max"])}
            for _, f in sub.iterrows()
        ]
        lider_base = datos["sensibilidad"]["por_modelo"][0]["modelo"] \
            if datos["sensibilidad"]["por_modelo"] else None
        datos["sensibilidad"]["base_lider"] = lider_base
    if SENS_PESOS.exists():
        sp = pd.read_csv(SENS_PESOS)
        e = sp[sp["propulsion"] == "electrico"]
        base_lider = datos["sensibilidad"]["base_lider"]
        escenas = [
            {"escenario": esc, "lider": g.nsmallest(1, "rank")
             ["modelo_norm"].iloc[0]}
            for esc, g in e.groupby("escenario")
        ]
        escenas = [dict(x, cambia=(x["lider"] != base_lider))
                   for x in escenas]
        # determinista: 'base' primero, resto alfabético
        escenas.sort(key=lambda x: (x["escenario"] != "base",
                                    x["escenario"]))
        datos["sensibilidad"]["escena_lider"] = escenas

    return datos


def serializar_json(datos: dict) -> str:
    return json.dumps(datos, ensure_ascii=False, sort_keys=True,
                      indent=1) + "\n"


def escribir(datos: dict) -> None:
    HISTORIA.mkdir(exist_ok=True)
    texto = serializar_json(datos)
    SALIDA_JSON.write_text(texto, encoding="utf-8")
    # datos.js: misma data, envuelta para <script src> (evita fetch/CORS y
    # permite abrir la página desde file://; sale del mismo dict, así que
    # los dos archivos no pueden divergir).
    SALIDA_JS.write_text(
        "window.HISTORIA_DATOS = "
        + json.dumps(datos, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")) + ";\n",
        encoding="utf-8")


def generar_og(datos: dict) -> None:
    """Renderiza historia/og.png (1200×630): tarjeta para redes sociales.

    Es la capa de PRESENTACIÓN, no de datos: los conteos del pie y las
    fichas del mosaico salen del mismo dict generado, y la paleta es el
    espejo OG_FUENTE_COLOR (la misma que el HTML). Con Agg no toca red ni
    ventana gráfica; se ejecuta solo con --og y --check no la mira.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    conteos = datos.get("conteos", {})
    fichas = datos.get("pila", {}).get("fichas", [])

    fig = plt.figure(figsize=(12, 6.3), dpi=100)
    fig.patch.set_facecolor("#f7f4ef")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1200)
    ax.set_ylim(630, 0)  # origen arriba-izquierda, como el HTML
    ax.axis("off")
    ax.set_facecolor("#f7f4ef")

    ax.text(64, 66, "LA HISTORIA · TRICICLOS EN LA HABANA",
            fontsize=14, fontweight="bold", color="#0e7490", va="top")
    ax.text(60, 102, "¿Qué triciclo comprar", fontsize=54,
            fontweight="bold", color="#22222a", va="top",
            family="DejaVu Serif")
    ax.text(60, 176, "en La Habana?", fontsize=54,
            fontweight="bold", color="#22222a", va="top",
            family="DejaVu Serif")
    ax.text(64, 260, "Seis actos con lo que se anuncia, lo que ofrecen los "
            "catálogos y lo que circula:", fontsize=15, color="#3f3f49",
            va="top")
    ax.text(64, 284, "los datos del proyecto, sin ninguna cifra escrita a "
            "mano.", fontsize=15, color="#3f3f49", va="top")

    # Mosaico de fichas (14×5): el mismo artefacto que abre la página.
    n_cols, tile, gap = 14, 34, 6
    x0, y0 = 64, 330
    for i, f in enumerate(fichas):
        fila_i, col_i = divmod(i, n_cols)
        ax.add_patch(FancyBboxPatch(
            (x0 + col_i * (tile + gap), y0 + fila_i * (tile + gap)),
            tile, tile, boxstyle="round,pad=0,rounding_size=6",
            facecolor=OG_FUENTE_COLOR.get(f["fuente"], "#b0b0b0"),
            edgecolor="#f7f4ef", linewidth=1.5))

    pie = " · ".join([
        f"{conteos.get('anuncios', 0)} anuncios",
        f"{conteos.get('fichas_empresa', 0)} fichas de catálogo",
        f"{conteos.get('observaciones_campo', 0)} observaciones de calle",
    ])
    ax.text(64, 556, pie, fontsize=20, fontweight="bold", color="#22222a",
            va="top")
    ax.text(64, 592, "todos los conteos salen de Data/ · se regeneran con "
            "codes/generar_historia.py", fontsize=12, color="#6b6b74",
            va="top")

    fig.savefig(SALIDA_OG, dpi=100)
    plt.close(fig)


def check() -> int:
    if not SALIDA_JSON.exists() or not SALIDA_JS.exists():
        print("[check] FALLÓ: historia/datos.json o datos.js no existen. "
              "Generá con: python3 codes/generar_historia.py")
        return 1
    regen = construir()
    actual = json.loads(SALIDA_JSON.read_text(encoding="utf-8"))
    if actual != regen:
        difs = [k for k in sorted(set(actual) | set(regen))
                if actual.get(k) != regen.get(k)]
        print(f"[check] FALLÓ: historia/datos.json difiere de los datos de "
              f"Data/. Claves cambiadas: {', '.join(difs)}. Regenerá con: "
              "python3 codes/generar_historia.py")
        return 1
    texto = SALIDA_JS.read_text(encoding="utf-8")
    esperado = ("window.HISTORIA_DATOS = "
                + json.dumps(regen, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")) + ";\n")
    if texto != esperado:
        print("[check] FALLÓ: historia/datos.js no coincide con "
              "datos.json. Regenerá con: python3 codes/generar_historia.py")
        return 1
    print("[check] OK: historia/datos.json y datos.js coinciden con "
          "los datos de Data/")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Genera historia/datos.json y datos.js desde Data/.")
    ap.add_argument("--check", action="store_true",
                    help="no escribe: verifica que el disco coincide")
    ap.add_argument("--og", action="store_true",
                    help="además renderiza historia/og.png (tarjeta social)")
    args = ap.parse_args()
    if args.check:
        return check()
    datos = construir()
    escribir(datos)
    print(f"[ok] {SALIDA_JSON.relative_to(ROOT)} y datos.js escritos")
    if args.og:
        generar_og(datos)
        print(f"[og] {SALIDA_OG.relative_to(ROOT)} escrito")
    return 0


if __name__ == "__main__":
    sys.exit(main())
