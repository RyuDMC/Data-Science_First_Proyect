"""
Página 3: Mercado — KPIs, mix por propulsión/fuente, estadísticas.
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
from reporte.data import load_anuncios, load_empresas, get_kpis
from reporte.theme import apply_style, fig_ax, donut_chart, bar_ranking, PROP_COLORS, PROP_LABELS, MUTED, GRID_COLOR, TEXT_COLOR


st.set_page_config(page_title="Mercado", page_icon="📊", layout="wide")
apply_style()

st.title("📊 Panorama del Mercado")

# Cargar datos
df_online = load_anuncios()
df_empresas = load_empresas()
kpis = get_kpis(df_online)

# ======= KPIs =======
st.subheader("📌 Indicadores Clave (Anuncios Online)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total anuncios", f"{kpis.get('total_anuncios', 0):,}")
c2.metric("Modelos únicos", f"{kpis.get('total_modelos', 0):,}")
c3.metric("Precio mediana", f"${kpis.get('precio_median', 0):,.0f}" if kpis.get('precio_median') else "—")
c4.metric("Autonomía mediana", f"{kpis.get('autonomia_median', 0):.0f} km" if kpis.get('autonomia_median') else "—")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Carga mediana", f"{kpis.get('carga_median', 0):.0f} kg" if kpis.get('carga_median') else "—")
c6.metric("Eléctricos", kpis.get('propulsion_dist', {}).get('electrico', 0))
c7.metric("Híbridos", kpis.get('propulsion_dist', {}).get('hibrido', 0))
c8.metric("Gasolina", kpis.get('propulsion_dist', {}).get('gasolina', 0))

st.markdown("---")

# ======= MIX PROPULSIÓN =======
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("⚡ Mix por propulsión")
    if not df_online.empty:
        prop_counts = df_online["propulsion"].value_counts()
        labels = [PROP_LABELS.get(p, p) for p in prop_counts.index]
        values = prop_counts.values
        colors = [PROP_COLORS.get(p, "#7f7f7f") for p in prop_counts.index]

        fig, ax = fig_ax(figsize=(5, 4))
        donut_chart(ax, values, labels, colors, "Anuncios por propulsión")
        st.pyplot(fig)

with col_right:
    st.subheader("🔗 Mix por fuente")
    if not df_online.empty and "fuente" in df_online.columns:
        fuente_counts = df_online["fuente"].value_counts()
        fig, ax = fig_ax(figsize=(5, 4))
        donut_chart(ax, fuente_counts.values, fuente_counts.index.tolist(),
                    [PROP_COLORS.get("electrico", "#1f77b4")] * len(fuente_counts),
                    "Anuncios por fuente")
        st.pyplot(fig)

st.markdown("---")

# ======= ESTADÍSTICAS POR PROPULSIÓN =======
st.subheader("📈 Estadísticas por propulsión (anuncios online)")

if not df_online.empty:
    tabs = st.tabs(["⚡ Eléctricos", "🔄 Híbridos", "⛽ Gasolina"])
    for i, prop in enumerate(["electrico", "hibrido", "gasolina"]):
        with tabs[i]:
            sub = df_online[df_online["propulsion"] == prop]
            if sub.empty:
                st.info(f"Sin datos para {PROP_LABELS[prop]}")
                continue

            # Stats
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Anuncios", len(sub))
            c2.metric("Precio med.", f"${sub['precio_usd'].median():,.0f}" if sub['precio_usd'].notna().any() else "—")
            c3.metric("Aut. med.", f"{sub['autonomia_km'].median():.0f} km" if sub['autonomia_km'].notna().any() else "—")
            c4.metric("Carga med.", f"{sub['carga_kg'].median():.0f} kg" if sub['carga_kg'].notna().any() else "—")

            # Motor
            if prop == "electrico":
                c5, c6 = st.columns(2)
                c5.metric("Motor W med.", f"{sub['motor_w'].median():,.0f} W" if sub['motor_w'].notna().any() else "—")
                sub["bateria_wh"] = sub["bateria_v"] * sub["bateria_ah"]
                c6.metric("Batería Wh med.", f"{sub['bateria_wh'].median():,.0f} Wh" if sub['bateria_wh'].notna().any() else "—")
            else:
                c5 = st.columns(1)[0]
                c5.metric("Motor cc med.", f"{sub['motor_cc'].median():,.0f} cc" if sub['motor_cc'].notna().any() else "—")

            # Tabla de modelos
            if "modelo_norm" in sub.columns:
                model_stats = sub.groupby("modelo_norm").agg(
                    n=("modelo_norm", "count"),
                    precio_med=("precio_usd", "median"),
                    aut_med=("autonomia_km", "median"),
                    carga_med=("carga_kg", "median"),
                ).sort_values("n", ascending=False).head(15)
                model_stats.columns = ["Anuncios", "Precio med.", "Aut. med.", "Carga med."]
                st.dataframe(model_stats, width="stretch")

st.markdown("---")

# ======= EMPRESAS =======
st.subheader("🏢 Catálogos de empresas (oferta formal)")

if not df_empresas.empty:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total fichas", len(df_empresas))
    c2.metric("Empresas", df_empresas["fuente_empresa"].nunique() if "fuente_empresa" in df_empresas.columns else 0)
    c3.metric("Precio med.", f"${df_empresas['precio_usd'].median():,.0f}" if df_empresas['precio_usd'].notna().any() else "—")
    c4.metric("Con autonomía", df_empresas['autonomia_km'].notna().sum())

    # Por empresa
    if "fuente_empresa" in df_empresas.columns:
        emp_stats = df_empresas.groupby("fuente_empresa").agg(
            fichas=("modelo", "count"),
            precio_med=("precio_usd", "median"),
            aut_med=("autonomia_km", "median"),
            propulsiones=("propulsion", lambda x: ", ".join(x.dropna().unique()))
        )
        emp_stats.columns = ["Fichas", "Precio med.", "Aut. med.", "Propulsiones"]
        st.dataframe(emp_stats, width="stretch")

    # Top modelos empresas
    st.markdown("**Modelos en catálogos:**")
    cols = ["nombre_producto", "marca", "propulsion", "precio_usd", "autonomia_km", "carga_kg", "fuente_empresa"]
    avail = [c for c in cols if c in df_empresas.columns]
    st.dataframe(df_empresas[avail].sort_values(["fuente_empresa", "nombre_producto"]),
                 width="stretch", hide_index=True)
else:
    st.info("Sin datos de empresas")

st.markdown("---")

# ======= CONDICIÓN / LEGALIDAD =======
st.subheader("📋 Condición y legalidad (anuncios online)")

if not df_online.empty:
    col1, col2 = st.columns(2)
    with col1:
        if "condicion" in df_online.columns:
            cond = df_online["condicion"].value_counts()
            fig, ax = fig_ax(figsize=(5, 3))
            donut_chart(ax, cond.values, cond.index.tolist(),
                        [PROP_COLORS.get("electrico", "#1f77b4")] * len(cond),
                        "Condición declarada")
            st.pyplot(fig)
    with col2:
        if "legalizacion" in df_online.columns:
            leg = df_online["legalizacion"].notna().value_counts()
            leg_labels = ["Menciona legalidad" if k else "No menciona" for k in leg.index]
            fig, ax = fig_ax(figsize=(5, 3))
            donut_chart(ax, leg.values, leg_labels,
                        [PROP_COLORS.get("electrico", "#1f77b4"), MUTED],
                        "Legalidad declarada")
            st.pyplot(fig)