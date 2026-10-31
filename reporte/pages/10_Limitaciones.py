"""
Página 10: Limitaciones — Qué no sabemos y por qué.
"""

import os as _os
import sys as _sys
# Permite importar el paquete `reporte` tanto con `streamlit run reporte/app.py`
# (donde sys.path[0] es reporte/) como al ejecutar/testear desde la raíz del repo.
_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)


import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reporte.data import (load_scores, load_anuncios, load_empresas, load_campo,
                          load_sensibilidad, load_sensibilidad_resumen,
                          load_metadata)
from reporte.theme import apply_style, fig_ax, color_for_prop, label_for_prop


st.set_page_config(page_title="Limitaciones", page_icon="⚠️", layout="wide")
apply_style()

# Cifras desde Data/metadata.json (única fuente; ver codes/generar_metadata.py).
_meta = load_metadata()
_c = _meta.get("conteos", {})
_cortes = _meta.get("cortes", {})
_n = lambda clave: _c.get(clave, "—")  # noqa: E731

st.title("⚠️ Limitaciones")

st.markdown("""
Este reporte se basa en **datos observacionales de oferta**, no en un censo de circulación.
Todas las conclusiones deben leerse con estas limitaciones en mente.
""")

# ======= LIMITACIONES ESTRUCTURALES =======
st.header("1️⃣ Limitaciones estructurales")

# La frase de sensibilidad se calcula desde los CSV de codes/sensibilidad.py:
# así no se desincroniza cuando cambien los pesos o los datos.
df_sens = load_sensibilidad()
df_sens_res = load_sensibilidad_resumen()
if df_sens.empty or df_sens_res.empty:
    sens_texto = (
        "Pendiente: ejecutar `codes/sensibilidad.py`. El score depende de pesos "
        "fijos; su estabilidad se mide aparte."
    )
else:
    top3 = df_sens_res[df_sens_res["propulsion"] == "electrico"].nsmallest(3, "rank_base")
    if len(top3) == 3:
        pcts = top3["top3_pct"].tolist()
        nombres = top3["modelo_norm"].tolist()
        cambios = (df_sens[(df_sens["propulsion"] == "electrico")
                           & (df_sens["rank"] == 1)
                           & (df_sens["escenario"] != "base")]
                   .set_index("escenario")["modelo_norm"])
        otros = cambios[cambios != nombres[0]]
        nombres_esc = {
            "reponderado": "re-ponderado",
            "sin_precio_usd": "sin precio",
            "sin_autonomia_km": "sin autonomía",
            "sin_carga_kg": "sin carga",
            "sin_legalidad": "sin legalidad",
            "sin_repuestos": "sin repuestos",
        }
        detalle = "; ".join(
            (f"al quitar {nombres_esc.get(e, e).replace('sin ', '')}"
             if e.startswith("sin_") else "al re-ponderar") + f" → {m}"
            for e, m in otros.items()
        )
        sens_texto = (
            f"Con 2.000 perturbaciones de ±0.05 en los pesos, el top-3 eléctrico se "
            f"mantiene en {pcts[0]:.0f}%, {pcts[1]:.0f}% y {pcts[2]:.0f}% de los casos; "
            f"el 1º cambia en {len(otros)} de {len(cambios)} escenarios de omisión"
            + (f" ({detalle})" if detalle else "")
            + ". El orden exacto depende de los pesos; el podio, no."
        )
    else:
        sens_texto = (
            "El score depende de pesos fijos; su estabilidad se mide en "
            "`sensibilidad_resumen.csv` (ver página de Ranking)."
        )

limitaciones = pd.DataFrame({
    "Área": [
        "Oferta ≠ Circulación",
        "Tamaño de muestra (n)",
        "Sesgo de fuentes online",
        "Trabajo de campo: muestra cerrada",
        "vedca.cu caído",
        "Normalización min-max intra-grupo",
        "Imputación neutra (0.5)",
        "Sensibilidad a los pesos",
        "Repuestos proxy débil",
    ],
    "Qué significa": [
        "Anuncios y catálogos miden **oferta declarada**, no triciclos rodando. Un modelo muy anunciado puede no ser el más común en calle.",
        f"{_n('modelos_ranking')} modelos en el ranking ({_n('nombres_modelo')} nombres distintos: el STAR aparece en dos propulsiones) de {_n('anuncios')} anuncios online + {_n('fichas_empresa')} fichas empresas ({_n('empresas')} catálogos). Muchos modelos con n=1. Scores con n_criterios < 5 son poco fiables.",
        "Fuentes: clasificados (Revolico), tiendas WooCommerce, Telegram, Facebook. No cubren mercado informal completo ni todas las MIPYMEs.",
        f"La muestra de calle es **final**: {_n('observaciones_campo')} observaciones en {_n('municipios_campo')} de los 15 municipios, dos semanas. **No habrá más trabajo de campo** (decisión 2026-10-31), así que no se puede cerrar 'el más común de La Habana': solo describir la muestra. Con n={_n('observaciones_campo')} los intervalos de confianza se solapan (el 1º y el 3º no se distinguen) y no hay denominador (triciclos/hora o /km), así que tampoco hay densidad.",
        "Catálogo oficial VEDCA no disponible desde 2024. Cobertura vía Telegram/islagrande es parcial y con precios EUR históricos.",
        "Un modelo extremo (muy barato/muy caro) mueve la escala de **todo el grupo**. Al añadir Facebook, el ranking eléctrico cambió.",
        "Ausentes → 0.5 neutro + n_criterios. No castiga, pero oculta que el score se basa en menos evidencia. Ver columna n_criterios.",
        sens_texto,
        f"{_n('modelos_con_repuestos')}/{_n('modelos_ranking')} modelos tienen repuestos_proxy=1 (los que se anuncian en más de una fuente). Es un proxy, no disponibilidad real de repuestos: mide presencia en el mercado, no stock de piezas."
    ],
    "Impacto": ["ALTO", "ALTO", "MEDIO", "ALTO", "MEDIO", "MEDIO", "BAJO", "MEDIO", "BAJO"]
})

st.dataframe(limitaciones, use_container_width=True, hide_index=True,
             column_config={
                 "Impacto": st.column_config.TextColumn("Impacto", width="small"),
             })

st.markdown("---")

# ======= DATA QUALITY =======
st.header("2️⃣ Calidad de datos conocida")

df_online = load_anuncios()
df_empresas = load_empresas()
df_scores = load_scores()

if not df_online.empty:
    st.subheader("Completitud de campos (anuncios online)")
    
    fields = ["modelo", "marca", "modelo_norm", "propulsion", "precio_usd", "autonomia_km", "carga_kg",
              "motor_w", "motor_cc", "bateria_v", "bateria_ah", "bateria_quimica",
              "legalizacion", "condicion", "municipio_anuncio"]
    
    completitud = []
    for f in fields:
        if f in df_online.columns:
            pct = df_online[f].notna().mean() * 100
            completitud.append({"Campo": f, "Completitud": f"{pct:.0f}%", "Nulos": df_online[f].isna().sum()})
    
    comp_df = pd.DataFrame(completitud)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ======= QUÉ CAMBIARÍA CON MÁS DATOS =======
st.header("3️⃣ Qué cambiaría con más datos")

st.markdown("""
| Si tuviéramos... | Cambiaría... |
|------------------|--------------|
| **Trabajo de campo en los 15 municipios** | *Cerrado: no se hará.* La muestra actual (5 municipios) solo describe la muestra; no responde "el más común de La Habana". |
| **Más anuncios por modelo** (n ≥ 5) | Scores más estables, n_criterios → 5 para más modelos. |
| **Precios reales de transacción** (no solo listados) | Precio mediano más representativo, menos sesgo vendedor. |
| **Datos de repuestos reales** (talleres, importadores) | Criterio repuestos significativo (hoy solo 9/41 modelos tienen >1 fuente). |
| **VEDCA.cu operativo** | Catálogo oficial completo, specs de fabricante, precios vigentes CUP/USD. |
| **Todas las MIPYMEs** (MVP, Kvitova, etc.) | Cobertura real de oferta formal en Cuba. |
| **Histórico de precios 12+ meses** | Tendencias, estacionalidad, inflación real USD/CUP. |
""")

st.markdown("---")

# ======= REPRODUCIBILIDAD =======
st.header("4️⃣ Reproducibilidad")

st.code("""
# Entorno
python3 -m venv reporte/.venv
source reporte/.venv/bin/activate
pip install -r reporte/requirements.txt

# Pipeline completo (raw → clean → score)
python3 codes/scrape_triciclos.py    # ~4 min, 5 fuentes online
python3 codes/parse_fb.py            # Facebook → clean_data/
python3 codes/scrape_empresas.py     # 10 catálogos empresas
python3 codes/analisis.py            # scoring + CSVs en clean_data/
python3 codes/sensibilidad.py        # robustez del ranking (no cambia el score)
python3 codes/generar_metadata.py    # conteos y cortes -> Data/metadata.json

# Reporte interactivo
streamlit run reporte/app.py

# Versiones clave
python3 --version      # 3.14 (o 3.12 en venv si streamlit falla)
pandas --version       # 2.3+
streamlit --version    # 1.38+
matplotlib --version   # 3.8+
""", language="bash")

st.markdown("---")

# ======= VERSIONADO =======
st.header("5️⃣ Versionado de datos")

st.markdown(f"""
| Archivo | Fuente | Última actualización | Registros | Notas |
|---------|--------|---------------------|-----------|-------|
| `anuncios_triciclos.jsonl` | 5 scrapers | {_cortes.get('anuncios', '—')} | {_n('anuncios_scraper')} | vedca.cu caído; 1 excluido por el usuario |
| `anuncios_facebook.jsonl` | parse_fb.py | {_cortes.get('anuncios', '—')} | {_n('anuncios_facebook')} | 1 excluido (Artemisa) |
| `empresas_*.jsonl` ({_n('empresas')}) | scrape_empresas.py | {_cortes.get('catalogos', '—')} | {_n('fichas_empresa')} | 5 catálogos previos + 5 nuevos; excluidos 1 genérico, 1 cuatriciclo y 2 accesorios |
| `modelos_canonicos.json` | **curado a mano** | {_cortes.get('catalogos', '—')} | {_n('productos_canonicos')} productos | Fuente de verdad de la identidad ({_n('productos_excluidos')} excluidos) |
| `score_modelos.csv` | analisis.py | {_cortes.get('anuncios', '—')} | {_n('modelos_ranking')} filas ({_n('nombres_modelo')} nombres) | Recalculado tras la limpieza de nombres |
| `sensibilidad_pesos.csv` + `sensibilidad_resumen.csv` | sensibilidad.py | {_cortes.get('catalogos', '—')} | 287 + 41 | 7 escenarios × {_n('modelos_ranking')} modelos; **no altera el score** |
| `registro_ubicaciones.csv` | **CAMPO** (`parse_campo.py`) | {_cortes.get('campo', '—')} | {_n('observaciones_campo')} | 5/15 municipios; sin datos personales |

**Corte propuesto para reporte final:** 30 noviembre 2026
""")

st.markdown("---")

st.caption("""
**Principio rector:** *No inventar datos.* Rangos → límite inferior. Ausentes → 0.5 neutro + n_criterios.
Si un dato no se puede verificar, no se usa. La transparencia sobre lo que **no sabemos** 
es tan importante como lo que mostramos.
""")
