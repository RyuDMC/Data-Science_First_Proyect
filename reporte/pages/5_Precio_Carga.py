"""
Página 5: Precio / Autonomía / Carga — Scatter burbuja + frontera eficiente.
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
import numpy as np
import matplotlib.pyplot as plt
from reporte.data import (load_scores, filter_by_propulsion, frontera_pareto,
                          sin_precio_comparable)
from reporte.theme import apply_style, fig_ax, scatter_bubble, color_for_prop, label_for_prop, ACCENT_GREEN, MUTED, GRID_COLOR, TEXT_COLOR


st.set_page_config(page_title="Precio/Autonomía/Carga", page_icon="💰", layout="wide")
apply_style()

st.title("💰 Precio vs Autonomía vs Carga")

df_scores = load_scores()

if df_scores.empty:
    st.error("No hay datos de scoring. Ejecuta `python3 codes/analisis.py` primero.")
    st.stop()

# ======= FILTROS =======
st.sidebar.markdown("### Filtros")

prop_options = ["Todos"] + sorted(df_scores["propulsion"].unique().tolist())
selected_prop = st.sidebar.selectbox("Propulsión", prop_options, index=0)

x_metric = st.sidebar.selectbox("Eje X", ["precio_usd", "autonomia_km", "carga_kg"], index=0)
y_metric = st.sidebar.selectbox("Eje Y", ["autonomia_km", "carga_kg", "precio_usd"], index=1)
size_metric = st.sidebar.selectbox("Tamaño burbuja", ["carga_kg", "autonomia_km", "precio_usd", "n_anuncios_total"], index=0)

only_viva = st.sidebar.checkbox("Solo ofertas vivas", value=True)
show_frontera = st.sidebar.checkbox("Mostrar frontera eficiente (Pareto)", value=True)
show_labels = st.sidebar.checkbox("Etiquetar modelos", value=True)

# Aplicar filtros
df = df_scores.copy()
if selected_prop != "Todos":
    df = df[df["propulsion"] == selected_prop]
if only_viva:
    df = df[df["oferta_viva"] == True]

# Eliminar filas sin datos en ejes. Si un eje es precio, esto deja fuera a los
# modelos sin precio USD (catálogo en EUR): no se inventa un precio.
df = df.dropna(subset=[x_metric, y_metric]).reset_index(drop=True)

if df.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

_n_sin_precio = len(sin_precio_comparable(df_scores))
_nota_precio = (
    f" | {_n_sin_precio} modelos sin precio USD quedan fuera"
    if "precio_usd" in (x_metric, y_metric) else ""
)
st.caption(
    f"Modelos: {len(df)} | Propulsión: {selected_prop} | "
    f"Oferta viva: {only_viva}{_nota_precio}"
)

# ======= LABELS =======
x_labels = {"precio_usd": "Precio (USD)", "autonomia_km": "Autonomía (km)", "carga_kg": "Carga (kg)"}
y_labels = {"precio_usd": "Precio (USD)", "autonomia_km": "Autonomía (km)", "carga_kg": "Carga (kg)"}

# ======= SCATTER BURBUJA =======
st.subheader("Mapa de burbujas")

# Preparar datos
x_vals = df[x_metric].values
y_vals = df[y_metric].values
size_vals = df[size_metric].values if size_metric in df.columns else np.ones(len(df))
labels = df["modelo_norm"].values
props = df["propulsion"].values

fig, ax = fig_ax(figsize=(10, 7))

# Frontera eficiente (Pareto): puntos no dominados en los dos ejes elegidos.
pareto_df = pd.DataFrame()
if show_frontera and len(df) > 1:
    pareto_df = frontera_pareto(df, x_metric, y_metric)
    if len(pareto_df) > 1:
        ax.plot(pareto_df[x_metric], pareto_df[y_metric], color=ACCENT_GREEN,
                linestyle="--", linewidth=2.5,
                label="Frontera eficiente (Pareto)", zorder=4, alpha=0.8)

# Scatter
colors = [color_for_prop(p) for p in props]
scatter = ax.scatter(x_vals, y_vals, s=np.clip(size_vals / (size_vals.max() if size_vals.max() > 0 else 1) * 800 + 50, 50, 1000),
                     c=colors, alpha=0.7, edgecolors="white", linewidth=0.5, zorder=3)

# Etiquetas
if show_labels:
    for i, (xi, yi, label) in enumerate(zip(x_vals, y_vals, labels)):
        ax.annotate(label, (xi, yi), fontsize=7, ha="center", va="bottom",
                    xytext=(0, 4), textcoords="offset points", color=TEXT_COLOR, alpha=0.8)

# Configurar ejes
ax.set_xlabel(x_labels[x_metric])
ax.set_ylabel(y_labels[y_metric])
title = f"{y_labels[y_metric]} vs {x_labels[x_metric]}"
if selected_prop != "Todos":
    title += f" — {label_for_prop(selected_prop)}"
ax.set_title(title, pad=12)

# Leyenda propulsión
from matplotlib.patches import Patch
seen = set()
handles = []
for p in props:
    if p not in seen:
        handles.append(Patch(color=color_for_prop(p), label=label_for_prop(p)))
        seen.add(p)
if handles:
    ax.legend(handles=handles + ([Patch(color=ACCENT_GREEN, linestyle="--", label="Frontera eficiente")] if show_frontera and len(pareto_df) > 1 else []), 
              loc="best", fontsize=9)

st.pyplot(fig)

# ======= INTERPRETACIÓN =======
st.markdown("---")
st.subheader("Cómo leer este gráfico")

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    **Ejes:**
    - **X:** {x_labels[x_metric]}
    - **Y:** {y_labels[y_metric]}
    - **Tamaño:** {size_metric.replace('_', ' ').title()}
    
    **Colores:** 
    - Eléctrico (azul)
    - Híbrido (naranja)
    - Gasolina (rojo)
    """)
with col2:
    st.markdown(f"""
    **Frontera eficiente (línea verde):**
    Modelos que **no están dominados** — no hay otro modelo que sea mejor en ambos ejes simultáneamente.
    
    - En **precio**, menor es mejor; en **autonomía** y **carga**, mayor es mejor.
    - La frontera se recalcula para el par de ejes que elijas (no asume que X sea precio).
    - Modelos **sobre la línea** = mejores compromisos
    - Modelos **fuera de la línea** = dominados (hay alternativa mejor en ambos criterios)
    """)

# ======= TABLA DE FRENTERA =======
if show_frontera and not pareto_df.empty:
    st.subheader("Modelos en la frontera eficiente")
    # Construcción por columnas (no `.rename`): si el criterio de ambos ejes es
    # el mismo, un dict de rename solo puede mapear un nombre y las dos columnas
    # quedan iguales → pyarrow falla con "Duplicate column names".
    x_label, y_label = x_labels[x_metric], y_labels[y_metric]
    if x_label == y_label:
        x_label, y_label = f"{x_label} (eje X)", f"{y_label} (eje Y)"
    frontera_df = pd.DataFrame({
        "Modelo": pareto_df["modelo_norm"].to_numpy(),
        x_label: pareto_df[x_metric].to_numpy(),
        y_label: pareto_df[y_metric].to_numpy(),
    })
    st.dataframe(frontera_df, width="stretch", hide_index=True)

# ======= TABLA COMPLETA =======
st.markdown("---")
st.subheader("Datos completos")

display_cols = ["modelo_norm", "propulsion", "precio_usd", "autonomia_km", "carga_kg", "score", "n_criterios", "oferta_viva"]
avail = [c for c in display_cols if c in df.columns]
df_show = df[avail].copy()
for col in ["precio_usd", "autonomia_km", "carga_kg", "score"]:
    if col in df_show.columns:
        if col == "score":
            df_show[col] = df_show[col].apply(lambda v: f"{v:.3f}")
        else:
            df_show[col] = df_show[col].apply(lambda v: f"{v:,.0f}" if pd.notna(v) else "—")
st.dataframe(df_show, width="stretch", hide_index=True)
