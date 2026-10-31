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
from reporte.data import (load_scores, filter_by_propulsion,
                          load_sensibilidad, load_sensibilidad_resumen)
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
    width="stretch",
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

# ======= SENSIBILIDAD DEL RANKING =======
# Análisis de robustez (codes/sensibilidad.py). NO cambia el score oficial:
# responde "¿cuánto depende este orden de los pesos y de la imputación 0.5?".
st.subheader("🎚️ ¿Cuánto depende el ranking de los pesos?")

ESCENARIOS = {
    "base": "Base (0.5 neutro)",
    "reponderado": "Re-ponderado (sin imputar)",
    "sin_precio_usd": "Sin precio",
    "sin_autonomia_km": "Sin autonomía",
    "sin_carga_kg": "Sin carga",
    "sin_legalidad": "Sin legalidad",
    "sin_repuestos": "Sin repuestos",
}

df_sens = load_sensibilidad()
df_sens_res = load_sensibilidad_resumen()

if df_sens.empty or df_sens_res.empty:
    st.info(
        "Aún no hay análisis de estabilidad. Ejecuta `python3 codes/sensibilidad.py` "
        "para medir cuánto aguanta el orden ante cambios de pesos y criterios ausentes."
    )
else:
    st.caption(
        "El score usa pesos fijos (precio 0.40, autonomía 0.25, carga 0.20, "
        "legalidad 0.10, repuestos 0.05) e imputación neutra 0.5. Aquí se prueba "
        "cuánto aguanta el orden: **2.000 perturbaciones** uniformes de ±0.05 en "
        "los pesos (semilla fija), **omisión de cada criterio** con "
        "re-normalización y **re-ponderación** solo con los criterios presentes "
        "(en vez de imputar 0.5). El ranking oficial no cambia."
    )

    # --- Podio bajo cada escenario (respeta el filtro de propulsión) ---
    esc = df_sens if selected_prop == "Todos" else df_sens[df_sens["propulsion"] == selected_prop]
    filas_esc = []
    for (prop, escenario), sub in esc.groupby(["propulsion", "escenario"], sort=False):
        top = sub.nsmallest(3, "rank")["modelo_norm"].tolist()
        top += [""] * (3 - len(top))
        filas_esc.append({
            "Propulsión": label_for_prop(prop),
            "Escenario": ESCENARIOS.get(escenario, escenario),
            "1º": top[0], "2º": top[1], "3º": top[2],
        })
    st.markdown("**Podio bajo cada escenario** (la fila *Base* es el ranking oficial)")
    st.dataframe(pd.DataFrame(filas_esc), hide_index=True, width="stretch")

    # --- Estabilidad de los modelos que se están viendo ---
    st.markdown("**Estabilidad de los modelos en la tabla de arriba**")
    res = df_sens_res.merge(
        df[["modelo_norm", "propulsion"]], on=["modelo_norm", "propulsion"], how="inner",
    )
    stab = df[["modelo_norm", "propulsion", "score", "n_criterios", "n_anuncios"]].merge(
        res[["modelo_norm", "propulsion", "rank_base", "top3_pct", "rank_min",
             "rank_max", "n_escenarios_top3", "escenario_peor"]],
        on=["modelo_norm", "propulsion"], how="left",
    )
    stab_show = pd.DataFrame({
        "Modelo": stab["modelo_norm"],
        "Prop.": stab["propulsion"].map(label_for_prop),
        "Score": stab["score"].map(lambda v: f"{v:.3f}"),
        "Rank": stab["rank_base"].astype("Int64"),
        "Top-3 (±0.05)": stab["top3_pct"].map(lambda v: f"{v:.0f}%" if pd.notna(v) else "—"),
        "Rank en escenarios (min–max)": stab.apply(
            lambda r: f"{int(r['rank_min'])}–{int(r['rank_max'])}" if pd.notna(r["rank_min"]) else "—",
            axis=1,
        ),
        "Top-3 en 6 escenarios": stab["n_escenarios_top3"].astype("Int64"),
        "Peor escenario": stab["escenario_peor"].map(lambda e: ESCENARIOS.get(e, e)),
        "N crit.": stab["n_criterios"].astype("Int64"),
        "Anuncios": stab["n_anuncios"].astype("Int64"),
    })
    st.dataframe(stab_show, hide_index=True, width="stretch")

    # --- Lectura automática del resultado (sin números escritos a mano) ---
    prop_txt = selected_prop if selected_prop != "Todos" else "electrico"
    top3 = df_sens_res[df_sens_res["propulsion"] == prop_txt].nsmallest(3, "rank_base")
    if len(top3) == 3:
        pcts = top3["top3_pct"].tolist()
        nombres = top3["modelo_norm"].tolist()
        cambios = (df_sens[(df_sens["propulsion"] == prop_txt)
                           & (df_sens["rank"] == 1)
                           & (df_sens["escenario"] != "base")]
                   .set_index("escenario")["modelo_norm"])
        otros = cambios[cambios != nombres[0]]
        detalle = "; ".join(
            (f"al quitar {ESCENARIOS[e].replace('Sin ', '').lower()}"
             if e.startswith("sin_") else "al re-ponderar") + f" → {m}"
            for e, m in otros.items()
        )
        st.markdown(
            f"**{label_for_prop(prop_txt)}:** el top-3 se mantiene en "
            f"{pcts[0]:.0f}%, {pcts[1]:.0f}% y {pcts[2]:.0f}% de las perturbaciones. "
            f"El 1º puesto aguanta {len(cambios) - len(otros)} de {len(cambios)} "
            f"escenarios de omisión"
            + (f"; cambia {detalle}." if len(otros) else ".")
        )
    else:
        st.caption("Con menos de 3 modelos en el grupo, el orden no es informativo.")

    st.caption(
        "Los porcentajes son la frecuencia con que el modelo cae en el top-3 de su "
        "propulsión. El score oficial no cambia: esto mide cuánto pesa la decisión "
        "metodológica, no propone otros pesos."
    )

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