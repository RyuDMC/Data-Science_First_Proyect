"""
Página 9: Empresas — fichas de catálogos.
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
from reporte.data import load_empresas, load_scores
from reporte.theme import apply_style, fig_ax, bar_ranking, color_for_prop, label_for_prop, donut_chart, PROP_COLORS


st.set_page_config(page_title="Empresas", page_icon="🏢", layout="wide")
apply_style()

st.title("🏢 Catálogos de Empresas (Oferta Formal)")

df_empresas = load_empresas()

if df_empresas.empty:
    st.error("No hay datos de empresas. Ejecuta `python3 codes/scrape_empresas.py` primero.")
    st.stop()

# ======= RESUMEN =======
st.subheader("📊 Resumen de catálogos")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total fichas", len(df_empresas))
c2.metric("Empresas", df_empresas["fuente_empresa"].nunique() if "fuente_empresa" in df_empresas.columns else 0)
c3.metric("Precio mediana", f"${df_empresas['precio_usd'].median():,.0f}" if df_empresas['precio_usd'].notna().any() else "—")
c4.metric("Con autonomía", int(df_empresas['autonomia_km'].notna().sum()))

st.markdown("---")

# ======= POR EMPRESA =======
st.subheader("🏪 Fichas por empresa")

if "fuente_empresa" in df_empresas.columns:
    for empresa in sorted(df_empresas["fuente_empresa"].unique()):
        sub = df_empresas[df_empresas["fuente_empresa"] == empresa]
        with st.expander(f"📦 {empresa} ({len(sub)} fichas)", expanded=False):
            # Stats rápidos
            c1, c2, c3 = st.columns(3)
            c1.metric("Precio med.", f"${sub['precio_usd'].median():,.0f}" if sub['precio_usd'].notna().any() else "—")
            c2.metric("Aut. med.", f"{sub['autonomia_km'].median():.0f} km" if sub['autonomia_km'].notna().any() else "—")
            c3.metric("Carga med.", f"{sub['carga_kg'].median():.0f} kg" if sub['carga_kg'].notna().any() else "—")
            
            # Tabla
            cols = ["nombre_producto", "marca", "propulsion", "precio_usd", "autonomia_km", "carga_kg",
                    "motor_w", "motor_cc", "bateria_v", "bateria_ah", "bateria_quimica",
                    "disponibilidad", "condicion", "legalizacion", "url"]
            avail = [c for c in cols if c in sub.columns]
            df_show = sub[avail].copy()
            for col in ["precio_usd", "autonomia_km", "carga_kg", "motor_w", "motor_cc", "bateria_v", "bateria_ah"]:
                if col in df_show.columns:
                    df_show[col] = df_show[col].apply(lambda v: f"{v:,.0f}" if pd.notna(v) else "—")
            st.dataframe(df_show, width="stretch", hide_index=True)

st.markdown("---")

# ======= ANÁLISIS CRUZADO =======
st.subheader("🔍 Análisis cruzado: Empresas vs Anuncios Online")

df_scores = load_scores()

# Modelos que aparecen en ambos
if not df_scores.empty:
    modelos_online = set(df_scores[df_scores["oferta_viva"] == True]["modelo_norm"].unique())
    modelos_empresas = set()
    if "modelo_norm" in df_empresas.columns:
        modelos_empresas = set(df_empresas["modelo_norm"].dropna().unique())
    elif "modelo" in df_empresas.columns:
        modelos_empresas = set(df_empresas["modelo"].dropna().str.upper().str.strip().unique())
    
    en_ambos = modelos_online & modelos_empresas
    solo_online = modelos_online - modelos_empresas
    solo_empresas = modelos_empresas - modelos_online
    
    c1, c2, c3 = st.columns(3)
    c1.metric("En ambos", len(en_ambos))
    c2.metric("Solo online", len(solo_online))
    c3.metric("Solo empresas", len(solo_empresas))
    
    if en_ambos:
        st.markdown("**Modelos en ambas fuentes:**")
        for m in sorted(en_ambos):
            st.caption(f"• {m}")
    
    if solo_empresas:
        st.markdown("**Solo en catálogos de empresas (no anunciados online):**")
        for m in sorted(solo_empresas):
            st.caption(f"• {m}")

    if not en_ambos:
        st.info(
            "Ningún modelo coincide exactamente entre catálogos y anuncios: los "
            "catálogos venden otra gama (marcas de importación) y los clasificados "
            "se centran en el mercado informal. A nivel de **marca** sí cruzan "
            "**ONEBOT, TOPMAQ, VEDCA y MISHOZUKI**; por eso no se comparan "
            "precios modelo a modelo."
        )

st.markdown("---")

# ======= COMPARATIVA DE PRECIOS =======
st.subheader("💰 Comparativa de precios: Empresa vs Online (modelos en común)")

if not df_scores.empty and en_ambos:
    # Precio mediana online por modelo
    online_precios = df_scores[df_scores["modelo_norm"].isin(en_ambos)][["modelo_norm", "precio_usd"]].copy()
    online_precios.columns = ["modelo_norm", "precio_online"]
    
    # Precio empresa por modelo
    if "modelo_norm" in df_empresas.columns:
        emp_precios = df_empresas[df_empresas["modelo_norm"].isin(en_ambos)][["modelo_norm", "precio_usd"]].copy()
        emp_precios.columns = ["modelo_norm", "precio_empresa"]
    else:
        emp_precios = df_empresas[df_empresas["modelo"].str.upper().str.strip().isin(en_ambos)][["modelo", "precio_usd"]].copy()
        emp_precios.columns = ["modelo_norm", "precio_empresa"]
    
    emp_precios = emp_precios.groupby("modelo_norm")["precio_empresa"].median().reset_index()
    
    comp = pd.merge(online_precios, emp_precios, on="modelo_norm", how="inner")
    comp["diferencia"] = comp["precio_empresa"] - comp["precio_online"]
    comp["pct_diff"] = (comp["diferencia"] / comp["precio_online"] * 100).round(1)
    
    st.dataframe(comp.sort_values("diferencia"), width="stretch", hide_index=True,
                 column_config={
                     "precio_online": st.column_config.NumberColumn("Online ($)", format="$%,.0f"),
                     "precio_empresa": st.column_config.NumberColumn("Empresa ($)", format="$%,.0f"),
                     "diferencia": st.column_config.NumberColumn("Diff ($)", format="$%,.0f"),
                     "pct_diff": st.column_config.NumberColumn("Diff (%)", format="%.1f%%"),
                 })
    
    # Gráfico
    fig, ax = fig_ax(figsize=(10, 5))
    y = range(len(comp))
    ax.barh(list(y), comp["precio_online"], height=0.4, label="Online", color=PROP_COLORS["electrico"], alpha=0.7)
    ax.barh([yi + 0.4 for yi in y], comp["precio_empresa"], height=0.4, label="Empresa", color=PROP_COLORS["hibrido"], alpha=0.7)
    ax.set_yticks([yi + 0.2 for yi in y])
    ax.set_yticklabels(comp["modelo_norm"], fontsize=8)
    ax.set_xlabel("Precio (USD)")
    ax.set_title("Precio Online vs Empresa (modelos en común)")
    ax.legend()
    ax.invert_yaxis()
    st.pyplot(fig)

st.markdown("---")

# ======= NOTAS METODOLÓGICAS =======
st.subheader("📝 Notas sobre los catálogos de empresas")

st.markdown("""
| Empresa | Plataforma | Fichas | Notas |
|---------|------------|--------|-------|
| **KikiHabana** | WooCommerce | 9 | Eléctricos con specs completas (batería, motor, autonomía, carga). Excluidos cuatriciclos (JY-MX8, MAGIKBIKE). ONEBOY T414 conservado. |
| **MZ Products** | WooCommerce | 7 | 5 eléctricos + 2 gasolina. MZ 200cc clasificado **híbrido** (slug dice "electrico-combustion"). Marca = "MZ PRODUCTS". Specs solo de `div.wd-single-content`. |
| **A Cuba Envíos Cargo** | WooCommerce | 4 | Solo specs del título (sin página de detalle). Incluye el "Fly Racing 2027" en "Próximamente". |
| **Mr Cuba** | Wix | 2 | **Frágil**: solo modelo + precio. Sin specs técnicas. |
| **CompraMasonline** | WooCommerce | 7 | 6 eléctricos + 1 híbrido (RALLY con extensor de rango de gasolina). Specs de la pestaña de descripción; precio actual (`ins`) si hay rebaja. Excluidos 2 extensores sueltos, el "Minicarrito" de 4 ruedas y el genérico "TRICICLO ELÉCTRICO DE CARGA" (sin modelo propio, duplicaba la identidad de MIGHONG con otro precio). |
| **MundoEnvío** | WooCommerce | 10 | Categoría "Triciclos Eléctricos". Excluido el "Mini triciclo 4 ruedas" (cuatriciclo). Precio de rango = límite inferior. La ficha del MIGHONG declara "Fuerza; 25000W" (errata): no se registra `motor_w` y queda anotado. |
| **Patuisla** | WooCommerce | 11 | Categoría "Envío de Triciclos a Cuba". En varias fichas las specs están en `.summary` (la pestaña de descripción solo trae el envío). Precio actual (`ins`) en rebajas. |
| **Francis Motors** | Estático (JSON-LD) | 11 | 3 gasolina, 4 híbridos y 4 eléctricos. Specs desde `additionalProperty`; precio y disponibilidad desde `offers`. Las specs del título no forman parte del nombre (decisión 2026-10-31): "BRAVO 250 CC" → BRAVO, "HERCULES PRO 72V 85AH" → HERCULES PRO. |
| **Bluewave Logistic** | Estático (Next.js) | 1 | Specs en pares `<dt>/<dd>`. El catálogo no declara marca ni modelo propio; excluidas por decisión del usuario las 4 fichas genéricas "TRICICLO ..." sin marca. Queda TIGER, que nombra la marca en el propio modelo (criterio marca-desde-nombre); el extensor de autonomía es generador: se marca híbrido. |
| **Zona Libre Online** | WooCommerce | 2 | Specs en JSON-LD + `og:image:alt`. ABL 1500W (60V/45Ah) y Mishozuki E-Cargo 8000W (72V/60Ah); la potencia no entra en el nombre canónico (MISHOZUKI E-CARGO). |

**Decisiones aplicadas:**
- Precios en **USD** (`precio_usd` + `moneda="USD"`)
- `vendedor_tipo="empresa"` para distinguir de particulares/tiendas
- `disponibilidad` capturada cuando existe (ej. "Consultar disponibilidad")
- **MAGIKBIKE** excluido en KikiHabana por ser "carrito 4 ruedas" (decisión del usuario)
- Rangos → **límite inferior** (autonomía, carga, motor, precio)
- Si la ficha solo declara voltaje, `bateria_ah` queda en `null` (no se inventa)
""")
