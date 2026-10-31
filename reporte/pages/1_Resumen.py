"""
Página 1: Resumen — Pregunta + 3 titulares + contador de datos.
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
from reporte.data import load_anuncios, load_empresas, load_campo, load_scores, get_kpis
from reporte.theme import color_for_prop, label_for_prop, apply_style


st.set_page_config(page_title="Resumen", page_icon="📋", layout="wide")
apply_style()

st.title("📋 Resumen Ejecutivo")

# Cargar datos
df_online = load_anuncios()
df_empresas = load_empresas()
df_campo = load_campo()
df_scores = load_scores()
kpis = get_kpis(df_online)

# Contadores
col1, col2, col3, col4 = st.columns(4)
col1.metric("Anuncios online", kpis.get("total_anuncios", 0))
col2.metric("Modelos únicos", kpis.get("total_modelos", 0))
col3.metric("Fichas empresas", len(df_empresas))
col4.metric("Observaciones campo", len(df_campo))

if not df_campo.empty:
    _top = df_campo["marca"].value_counts()
    st.caption(
        f"Campo: **{len(df_campo)} observaciones** en "
        f"**{df_campo['municipio'].nunique()} municipios** "
        f"({df_campo['fecha'].min()} → {df_campo['fecha'].max()}). "
        f"Marca más vista en calle: **{_top.index[0]}** "
        f"({_top.iloc[0]} de {len(df_campo)}, "
        f"{_top.iloc[0] / len(df_campo) * 100:.0f}%). "
        "Muestra cerrada: describe la muestra, no toda La Habana."
    )

st.markdown("---")

# ======= TITULARES =======
st.subheader("🎯 Los 3 titulares")

col_t1, col_t2, col_t3 = st.columns(3)

with col_t1:
    st.markdown("### 1️⃣ Lo más ofertado (indicador)")
    if not df_scores.empty:
        top = df_scores.iloc[0]
        st.success(f"**{top['modelo_norm']}** ({label_for_prop(top['propulsion'])})")
        st.metric("Score", f"{top['score']:.3f}", help="Score ponderado: precio 40%, autonomía 25%, carga 20%, legalidad 10%, repuestos 5%")
        st.caption(f"n_anuncios: {int(top['n_anuncios_total'])} | Oferta viva: {'Sí' if top['oferta_viva'] else 'No'}")
        if not df_campo.empty:
            _m = df_campo["marca"].value_counts()
            st.caption(
                f"En calle, la marca más vista es **{_m.index[0]}** "
                f"({_m.iloc[0]}/{len(df_campo)}). Detalle en 🗺️ Trabajo de campo."
            )
    else:
        st.info("Sin datos de scoring")

with col_t2:
    st.markdown("### 2️⃣ Por qué ese modelo")
    st.markdown("""
    - **Mejor equilibrio precio/autonomía/carga** dentro de su grupo de propulsión
    - **Oferta viva** en múltiples fuentes (repuestos_proxy)
    - **Legalidad mencionada** en anuncios/fichas
    - **Volumen de anuncios** > 1 (demanda visible)
    """)
    if not df_scores.empty:
        top = df_scores.iloc[0]
        st.caption(f"Precio: ${top['precio_usd']:,.0f} | Autonomía: {top['autonomia_km']:.0f} km | Carga: {top['carga_kg']:.0f} kg")

with col_t3:
    st.markdown("### 3️⃣ La mejor opción (según escenario)")
    st.markdown("""
    | Escenario | Recomendación |
    |-----------|---------------|
    | **Carga pesada** (≥800 kg) | Ver Ranking → Eléctricos |
    | **Pasajeros / autonomía** | Ver Ranking → Eléctricos |
    | **Presupuesto bajo** (<$4000) | Ver Ranking → Eléctricos |
    | **Sin infraestructura eléctrica** | Ver Ranking → Híbridos / Gasolina |
    """)
    st.caption("La 'mejor opción' depende de tu caso de uso. Ve a la pestaña **Mejor opción** para el detalle.")

st.markdown("---")

# ======= TOP 3 POR PROPULSIÓN =======
st.subheader("🏆 Top 3 por propulsión (score)")

if not df_scores.empty:
    tabs = st.tabs(["⚡ Eléctricos", "🔄 Híbridos", "⛽ Gasolina"])
    for i, prop in enumerate(["electrico", "hibrido", "gasolina"]):
        with tabs[i]:
            sub = df_scores[df_scores["propulsion"] == prop].head(3)
            if sub.empty:
                st.info(f"Sin modelos {label_for_prop(prop)}")
            else:
                for _, row in sub.iterrows():
                    c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
                    c1.markdown(f"**{row['modelo_norm']}**")
                    c2.metric("Score", f"{row['score']:.3f}")
                    c3.metric("$", f"{row['precio_usd']:,.0f}" if pd.notna(row['precio_usd']) else "—")
                    c4.metric("km", f"{row['autonomia_km']:.0f}" if pd.notna(row['autonomia_km']) else "—")
                    c5.metric("kg", f"{row['carga_kg']:.0f}" if pd.notna(row['carga_kg']) else "—")

st.markdown("---")

# ======= MIX DE PROPULSIÓN =======
st.subheader("📈 Mix de propulsión (anuncios online)")

if not df_online.empty and "propulsion" in df_online.columns:
    import matplotlib.pyplot as plt
    from reporte.theme import fig_ax, donut_chart, PROP_COLORS, PROP_LABELS

    prop_counts = df_online["propulsion"].value_counts()
    labels = [PROP_LABELS.get(p, p) for p in prop_counts.index]
    values = prop_counts.values
    colors = [PROP_COLORS.get(p, "#7f7f7f") for p in prop_counts.index]

    fig, ax = fig_ax(figsize=(6, 4))
    donut_chart(ax, values, labels, colors, "Distribución de anuncios por propulsión")
    st.pyplot(fig)
else:
    st.info("Sin datos de propulsión")