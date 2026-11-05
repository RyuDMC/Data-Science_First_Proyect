"""
Página 6: Contendientes — Top por grupo + radar de criterios.
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
from reporte.data import load_scores, filter_by_propulsion, get_top_models
from reporte.theme import apply_style, fig_ax, color_for_prop, label_for_prop, GRID_COLOR, MUTED, TEXT_COLOR


st.set_page_config(page_title="Contendientes", page_icon="🎯", layout="wide")
apply_style()

st.title("🎯 Contendientes: Top por Grupo + Radar")

df_scores = load_scores()

if df_scores.empty:
    st.error("No hay datos de scoring. Ejecuta `python3 codes/analisis.py` primero.")
    st.stop()

# ======= FILTROS =======
st.sidebar.markdown("### Filtros")

prop_options = ["Todos"] + sorted(df_scores["propulsion"].unique().tolist())
selected_prop = st.sidebar.selectbox("Propulsión", prop_options, index=0)
top_n = st.sidebar.slider("Top N por grupo", 3, 15, 5)

if selected_prop != "Todos":
    df = get_top_models(df_scores, selected_prop, top_n)
else:
    # Top N por cada propulsión, usando `rank_propulsion` (no el orden del CSV).
    dfs = [get_top_models(df_scores, prop, top_n)
           for prop in ["electrico", "hibrido", "gasolina"]]
    dfs = [sub for sub in dfs if not sub.empty]
    df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

df = df.reset_index(drop=True)
# Clave única visible: "STAR" existe como eléctrico y como híbrido; usar solo
# `modelo_norm` haría que `.loc["STAR"]` devolviera un DataFrame y rompiera el radar.
df["_clave"] = (df["modelo_norm"].astype(str) + " · "
                + df["propulsion"].map(label_for_prop))

st.caption(f"Modelos mostrados: {len(df)}")

# ======= TARJETAS TOP =======
st.subheader("🏅 Fichas de los contendientes")

if not df.empty:
    for prop in df["propulsion"].unique():
        sub = df[df["propulsion"] == prop]
        st.markdown(f"#### {label_for_prop(prop)}")
        
        cols = st.columns(min(3, len(sub)))
        for idx, (_, row) in enumerate(sub.iterrows()):
            with cols[idx % len(cols)]:
                st.markdown(f"**{row['modelo_norm']}**")
                st.metric("Score", f"{row['score']:.3f}")
                c1, c2 = st.columns(2)
                c1.metric("Precio", f"${row['precio_usd']:,.0f}" if pd.notna(row['precio_usd']) else "—")
                c2.metric("Autonomía", f"{row['autonomia_km']:.0f} km" if pd.notna(row['autonomia_km']) else "—")
                c3, c4 = st.columns(2)
                c3.metric("Carga", f"{row['carga_kg']:.0f} kg" if pd.notna(row['carga_kg']) else "—")
                c4.metric("N criterios", f"{int(row['n_criterios'])}/5")
                st.caption(f"Viva: {'Sí' if row['oferta_viva'] else 'No'} | Anuncios: {int(row['n_anuncios_total'])}")
                if "en_catalogo" in row.index and row.get("en_catalogo"):
                    precio_emp = row.get("precio_empresa_med")
                    precio_txt = f"${precio_emp:,.0f}" if pd.notna(precio_emp) else "—"
                    st.caption(
                        f"🏢 En catálogo de empresa ({int(row.get('n_empresas', 0))}) · "
                        f"precio tienda mediano: {precio_txt}"
                    )
                elif "marca_en_catalogo" in row.index and row.get("marca_en_catalogo"):
                    st.caption(
                        f"🏢 Marca en catálogo de empresa "
                        f"({int(row.get('n_empresas_marca', 0))}); el modelo exacto no."
                    )

st.markdown("---")

# ======= RADAR CHART =======
st.subheader("📡 Radar comparativo (criterios normalizados 0-1)")

# Selector de modelos para radar (clave única: modelo + propulsión)
available_models = df["_clave"].tolist()
selected_models = st.multiselect(
    "Selecciona modelos para comparar (máx 5):",
    available_models,
    default=available_models[:min(3, len(available_models))]
)

if len(selected_models) >= 2:
    radar_df = df[df["_clave"].isin(selected_models)].set_index("_clave")
    
    norm_cols = ["precio_usd_norm", "autonomia_km_norm", "carga_kg_norm", "legalidad_norm", "repuestos_norm"]
    avail_n = [c for c in norm_cols if c in radar_df.columns]
    
    if avail_n:
        categories = ["Precio\n(menor=mejor)", "Autonomía", "Carga", "Legalidad", "Repuestos"][:len(avail_n)]
        
        fig, ax = fig_ax(figsize=(7, 7), subplot_kw=dict(projection="polar"))
        
        N = len(categories)
        angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
        angles += angles[:1]
        
        ax.set_theta_offset(np.pi/2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=9)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8])
        ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8"], fontsize=7)
        ax.grid(color=GRID_COLOR, linewidth=0.8)
        
        for clave in selected_models:
            row = radar_df.loc[clave]
            prop = row.get("propulsion", "indeterminado")
            color = color_for_prop(prop)
            vals = [row[c] for c in avail_n]
            vals_closed = vals + vals[:1]
            ax.plot(angles, vals_closed, color=color, linewidth=2,
                    label=f"{clave}", zorder=3)
            ax.fill(angles, vals_closed, color=color, alpha=0.1)
        
        ax.set_title("Radar de criterios normalizados (0-1)", pad=20, fontsize=12)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)
        st.pyplot(fig)
        
        # Tabla de valores normalizados
        st.markdown("**Valores normalizados:**")
        norm_display = radar_df.loc[selected_models, avail_n].T
        norm_display.columns = selected_models
        norm_display.index = categories
        st.dataframe(norm_display.style.format("{:.2f}"), width="stretch")
else:
    st.info("Selecciona al menos 2 modelos para ver el radar.")

st.markdown("---")

# ======= TABLA DETALLADA =======
st.subheader("📋 Tabla detallada de contendientes")

display_cols = ["modelo_norm", "propulsion", "score", "n_criterios",
                "precio_usd", "precio_usd_norm", "autonomia_km", "autonomia_km_norm",
                "carga_kg", "carga_kg_norm", "legalidad_bin", "legalidad_norm",
                "repuestos_proxy", "repuestos_norm", "oferta_viva", "n_anuncios_total",
                "en_catalogo", "n_empresas", "precio_empresa_med",
                "marca_en_catalogo", "n_empresas_marca"]
avail = [c for c in display_cols if c in df.columns]
for col, flag in [("en_catalogo", "en_catalogo"),
                  ("n_empresas", "en_catalogo"),
                  ("precio_empresa_med", "en_catalogo"),
                  ("marca_en_catalogo", "marca_en_catalogo"),
                  ("n_empresas_marca", "marca_en_catalogo")]:
    if col in avail and flag in df.columns and not df[flag].fillna(False).any():
        avail.remove(col)

df_show = df[avail].copy()
for col in df_show.columns:
    if df_show[col].dtype in ("float64", "float32"):
        if "norm" in col or col == "score":
            df_show[col] = df_show[col].apply(lambda v: f"{v:.3f}")
        else:
            df_show[col] = df_show[col].apply(lambda v: f"{v:,.0f}" if pd.notna(v) else "—")
if "en_catalogo" in df_show.columns:
    df_show["en_catalogo"] = df_show["en_catalogo"].map({True: "Sí", False: "No"})
if "marca_en_catalogo" in df_show.columns:
    df_show["marca_en_catalogo"] = df_show["marca_en_catalogo"].map({True: "Sí", False: "No"})

st.dataframe(df_show, width="stretch", hide_index=True)
st.caption(
    "**Contexto de catálogo (no entra al score):** 'Marca en catálogo' indica que "
    "la marca se vende en una tienda formal; hoy ningún modelo coincide exactamente "
    "con los anuncios."
)
