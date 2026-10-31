"""
Página 4: Ranking interactivo — Filtro por propulsión, tabla ordenable, comparador.
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
from reporte.data import load_scores, filter_by_propulsion
from reporte.theme import apply_style, fig_ax, bar_ranking, color_for_prop, label_for_prop


st.set_page_config(page_title="Ranking", page_icon="🏆", layout="wide")
apply_style()

st.title("🏆 Ranking de Modelos (Score Ponderado)")

df_scores = load_scores()

if df_scores.empty:
    st.error("No hay datos de scoring. Ejecuta `python3 codes/analisis.py` primero.")
    st.stop()

# ======= FILTROS =======
st.sidebar.markdown("### 🎛️ Filtros")

prop_options = ["Todos"] + sorted(df_scores["propulsion"].unique().tolist())
selected_prop = st.sidebar.selectbox("Propulsión", prop_options, index=0)

min_criteria = st.sidebar.slider("Mín. criterios con dato (n_criterios)", 1, 5, 3)
only_viva = st.sidebar.checkbox("Solo ofertas vivas", value=True)
top_n = st.sidebar.slider("Top N a mostrar", 5, 50, 20)

# Aplicar filtros
df = df_scores.copy()
if selected_prop != "Todos":
    df = df[df["propulsion"] == selected_prop]
df = df[df["n_criterios"] >= min_criteria]
if only_viva:
    df = df[df["oferta_viva"] == True]
df = df.head(top_n).reset_index(drop=True)

st.caption(f"Mostrando {len(df)} de {len(df_scores)} modelos | Filtro: {selected_prop} | n_criterios ≥ {min_criteria} | Oferta viva: {only_viva}")

# ======= TABLA PRINCIPAL =======
st.subheader("📋 Tabla de Ranking")

# Columnas a mostrar
display_cols = [
    "modelo_norm", "propulsion", "score", "n_criterios",
    "precio_usd", "autonomia_km", "carga_kg",
    "legalidad_bin", "repuestos_proxy",
    "oferta_viva", "n_anuncios", "n_anuncios_total",
    "motor_w_med", "motor_cc_med", "marcas", "fuentes",
    "en_catalogo", "n_empresas", "precio_empresa_med",
    "marca_en_catalogo", "n_empresas_marca",
]
avail = [c for c in display_cols if c in df.columns]
# Las columnas de catálogo sin ningún positivo se ocultan (evita 3 columnas
# vacías): el aviso de abajo explica qué significa ese vacío.
for col, flag in [("en_catalogo", "en_catalogo"),
                  ("n_empresas", "en_catalogo"),
                  ("precio_empresa_med", "en_catalogo"),
                  ("marca_en_catalogo", "marca_en_catalogo"),
                  ("n_empresas_marca", "marca_en_catalogo")]:
    if col in avail and flag in df.columns and not df[flag].fillna(False).any():
        avail.remove(col)

# Formatear para display
df_show = df[avail].copy()
fmt_map = {
    "score": "{:.3f}",
    "precio_usd": "${:,.0f}",
    "precio_empresa_med": "${:,.0f}",
    "autonomia_km": "{:.0f} km",
    "carga_kg": "{:.0f} kg",
    "motor_w_med": "{:,.0f} W",
    "motor_cc_med": "{:,.0f} cc",
}
for col, fmt in fmt_map.items():
    if col in df_show.columns:
        df_show[col] = df_show[col].apply(lambda v: fmt.format(v) if pd.notna(v) else "—")
if "en_catalogo" in df_show.columns:
    df_show["en_catalogo"] = df_show["en_catalogo"].map({True: "Sí", False: "No"})
if "marca_en_catalogo" in df_show.columns:
    df_show["marca_en_catalogo"] = df_show["marca_en_catalogo"].map({True: "Sí", False: "No"})

# Renombrar columnas
rename_map = {
    "modelo_norm": "Modelo", "propulsion": "Propulsión", "score": "Score",
    "n_criterios": "N crit.", "precio_usd": "Precio", "autonomia_km": "Autonomía",
    "carga_kg": "Carga", "legalidad_bin": "Legal", "repuestos_proxy": "Repuestos",
    "oferta_viva": "Viva", "n_anuncios": "Anunc. vivos", "n_anuncios_total": "Total anunc.",
    "motor_w_med": "Motor W", "motor_cc_med": "Motor cc", "marcas": "Marcas", "fuentes": "Fuentes",
    "en_catalogo": "En catálogo", "n_empresas": "N empresas",
    "precio_empresa_med": "Precio tienda (med.)",
    "marca_en_catalogo": "Marca en catálogo", "n_empresas_marca": "N empresas (marca)",
}
df_show = df_show.rename(columns=rename_map)

st.dataframe(
    df_show,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.NumberColumn(format="%.3f"),
    }
)
st.caption(
    "**Contexto de catálogo (no entra al score).** Hoy ningún modelo de los "
    "catálogos de empresa coincide con la identidad de un anuncio (los catálogos "
    "venden otras gamas), así que no hay columna de modelo; sí se marca la "
    "**marca** que alguna tienda formal vende (ONEBOT). El score y el precio "
    "salen solo de anuncios: el precio de tienda no es comparable (envío, "
    "garantía y margen distintos)."
)

# ======= GRÁFICO DE BARRAS =======
st.subheader("📊 Visualización del Ranking")

if not df.empty:
    # Selector para resaltar
    highlight_idx = st.selectbox(
        "Resaltar modelo en gráfico:",
        options=[-1] + list(range(len(df))),
        format_func=lambda i: "Ninguno" if i == -1 else f"{i+1}. {df.iloc[i]['modelo_norm']}"
    )

    models = df["modelo_norm"].tolist()
    scores = df["score"].tolist()
    props = df["propulsion"].tolist()

    fig, ax = fig_ax(figsize=(10, max(6, len(df) * 0.35)))
    bar_ranking(ax, models, scores, props,
                highlight_idx=highlight_idx if highlight_idx >= 0 else None,
                title=f"Ranking {label_for_prop(selected_prop) if selected_prop != 'Todos' else 'Todos'} (Score 0-1)")
    st.pyplot(fig)

st.markdown("---")

# ======= COMPARADOR =======
st.subheader("⚖️ Comparador de modelos")

if len(df) >= 2:
    col1, col2, col3 = st.columns(3)
    with col1:
        m1 = st.selectbox("Modelo A", df["modelo_norm"].tolist(), index=0)
    with col2:
        m2 = st.selectbox("Modelo B", df["modelo_norm"].tolist(), index=min(1, len(df)-1))
    with col3:
        m3 = st.selectbox("Modelo C (opcional)", ["—"] + df["modelo_norm"].tolist(), index=0)

    compare_models = [m for m in [m1, m2, m3] if m != "—"]
    if compare_models:
        comp_df = df[df["modelo_norm"].isin(compare_models)].set_index("modelo_norm")

        # Métricas en columnas
        st.markdown("**Métricas crudas:**")
        metrics_cols = ["precio_usd", "autonomia_km", "carga_kg", "legalidad_bin", "repuestos_proxy", "n_criterios", "score"]
        avail_m = [c for c in metrics_cols if c in comp_df.columns]

        for col in avail_m:
            c1, c2, c3 = st.columns(3)
            vals = comp_df[col].tolist()
            for i, (model, val) in enumerate(zip(comp_df.index, vals)):
                label = {"precio_usd": "Precio ($)", "autonomia_km": "Autonomía (km)",
                         "carga_kg": "Carga (kg)", "legalidad_bin": "Legalidad (0/1)",
                         "repuestos_proxy": "Repuestos (0/1)", "n_criterios": "N criterios",
                         "score": "Score"}[col]
                with [c1, c2, c3][i % 3]:
                    if isinstance(val, float):
                        st.metric(label, f"{val:.2f}" if col == "score" else f"{val:,.0f}" if col == "precio_usd" else f"{val:.0f}")
                    else:
                        st.metric(label, val)

        # Radar chart comparativo
        st.markdown("**Radar de criterios normalizados (0-1):**")
        norm_cols = ["precio_usd_norm", "autonomia_km_norm", "carga_kg_norm", "legalidad_norm", "repuestos_norm"]
        avail_n = [c for c in norm_cols if c in comp_df.columns]
        if avail_n:
            import numpy as np
            from reporte.theme import fig_ax

            categories = ["Precio\n(menor=mejor)", "Autonomía", "Carga", "Legalidad", "Repuestos"][:len(avail_n)]
            values_dict = {}
            for model in compare_models:
                row = comp_df.loc[model]
                values_dict[model] = [row[c] for c in avail_n]

            fig, ax = fig_ax(figsize=(6, 6), subplot_kw=dict(projection="polar"))
            # Radar manual
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
            ax.grid(color="#dddddd", linewidth=0.8)

            for (name, vals), prop in zip(values_dict.items(), comp_df["propulsion"]):
                color = color_for_prop(prop)
                vals_closed = vals + vals[:1]
                ax.plot(angles, vals_closed, color=color, linewidth=2, label=name, zorder=3)
                ax.fill(angles, vals_closed, color=color, alpha=0.15)

            ax.set_title("Comparativa normalizada por criterio", pad=20, fontsize=12)
            ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)
            st.pyplot(fig)
else:
    st.info("Se necesitan al menos 2 modelos para comparar.")