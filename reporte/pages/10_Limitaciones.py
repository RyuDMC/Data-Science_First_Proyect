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
from reporte.data import load_scores, load_anuncios, load_empresas, load_campo
from reporte.theme import apply_style, fig_ax, color_for_prop, label_for_prop


st.set_page_config(page_title="Limitaciones", page_icon="⚠️", layout="wide")
apply_style()

st.title("⚠️ Limitaciones")

st.markdown("""
Este reporte se basa en **datos observacionales de oferta**, no en un censo de circulación.
Todas las conclusiones deben leerse con estas limitaciones en mente.
""")

# ======= LIMITACIONES ESTRUCTURALES =======
st.header("1️⃣ Limitaciones estructurales")

limitaciones = pd.DataFrame({
    "Área": [
        "Oferta ≠ Circulación",
        "Tamaño de muestra (n)",
        "Sesgo de fuentes online",
        "Trabajo de campo: muestra cerrada",
        "vedca.cu caído",
        "Normalización min-max intra-grupo",
        "Imputación neutra (0.5)",
        "Repuestos proxy débil",
    ],
    "Qué significa": [
        "Anuncios y catálogos miden **oferta declarada**, no triciclos rodando. Un modelo muy anunciado puede no ser el más común en calle.",
        "42 modelos en el ranking (41 nombres distintos: el STAR aparece en dos propulsiones) de 70 anuncios online + 68 fichas empresas (10 catálogos). Muchos modelos con n=1. Scores con n_criterios < 5 son poco fiables.",
        "Fuentes: clasificados (Revolico), tiendas WooCommerce, Telegram, Facebook. No cubren mercado informal completo ni todas las MIPYMEs.",
        "La muestra de calle es **final**: 30 observaciones en 5 de los 15 municipios, dos semanas. **No habrá más trabajo de campo** (decisión 2026-10-31), así que no se puede cerrar 'el más común de La Habana': solo describir la muestra. Con n=30 los intervalos de confianza se solapan (el 1º y el 3º no se distinguen) y no hay denominador (triciclos/hora o /km), así que tampoco hay densidad.",
        "Catálogo oficial VEDCA no disponible desde 2024. Cobertura vía Telegram/islagrande es parcial y con precios EUR históricos.",
        "Un modelo extremo (muy barato/muy caro) mueve la escala de **todo el grupo**. Al añadir Facebook, el ranking eléctrico cambió.",
        "Ausentes → 0.5 neutro + n_criterios. No castiga, pero oculta que el score se basa en menos evidencia. Ver columna n_criterios.",
        "9/42 modelos tienen repuestos_proxy=1 (los que se anuncian en más de una fuente). Es un proxy, no disponibilidad real de repuestos: mide presencia en el mercado, no stock de piezas."
    ],
    "Impacto": ["ALTO", "ALTO", "MEDIO", "ALTO", "MEDIO", "MEDIO", "BAJO", "BAJO"]
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
| **Datos de repuestos reales** (talleres, importadores) | Criterio repuestos significativo (hoy solo 9/42 modelos tienen >1 fuente). |
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

st.markdown("""
| Archivo | Fuente | Última actualización | Registros | Notas |
|---------|--------|---------------------|-----------|-------|
| `anuncios_triciclos.jsonl` | 5 scrapers | 2026-10-19 | 41 | vedca.cu caído; 1 excluido por el usuario |
| `anuncios_facebook.jsonl` | parse_fb.py | 2026-10-19 | 29 | 1 excluido (Artemisa) |
| `empresas_*.jsonl` (10) | scrape_empresas.py | 2026-10-31 | 68 | 5 catálogos previos + 5 nuevos; excluidos 1 genérico, 1 cuatriciclo y 2 accesorios |
| `modelos_canonicos.json` | **curado a mano** | 2026-10-31 | 137 productos | Fuente de verdad de la identidad (3 excluidos) |
| `score_modelos.csv` | analisis.py | 2026-10-19 | 42 filas (41 nombres) | Recalculado tras la limpieza de nombres |
| `registro_ubicaciones.csv` | **CAMPO** (`parse_campo.py`) | 2026-10-25 | 30 | 5/15 municipios; sin datos personales |

**Corte propuesto para reporte final:** 30 noviembre 2026
""")

st.markdown("---")

st.caption("""
**Principio rector:** *No inventar datos.* Rangos → límite inferior. Ausentes → 0.5 neutro + n_criterios.
Si un dato no se puede verificar, no se usa. La transparencia sobre lo que **no sabemos** 
es tan importante como lo que mostramos.
""")
