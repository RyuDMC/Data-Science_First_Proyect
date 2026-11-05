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
from reporte.data import (load_anuncios, load_empresas, load_campo, load_scores,
                          load_sensibilidad, load_sensibilidad_resumen,
                          get_kpis, top_por_anuncios,
                          top_por_propulsion, texto_sensibilidad_electrico)
from reporte.theme import color_for_prop, label_for_prop, apply_style


st.set_page_config(page_title="Resumen", page_icon="📋", layout="wide")
apply_style()

st.title("📋 Resumen Ejecutivo")

# Cargar datos
df_online = load_anuncios()
df_empresas = load_empresas()
df_campo = load_campo()
df_scores = load_scores()
df_sens = load_sensibilidad()
df_sens_res = load_sensibilidad_resumen()
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
    top_ofertado = top_por_anuncios(df_scores)
    if top_ofertado is not None:
        st.success(f"**{top_ofertado['modelo_norm']}** ({label_for_prop(top_ofertado['propulsion'])})")
        st.metric("Score", f"{top_ofertado['score']:.3f}", help="Score ponderado: precio 40%, autonomía 25%, carga 20%, legalidad 10%, repuestos 5%")
        st.caption(f"n_anuncios: {int(top_ofertado['n_anuncios_total'])} | Oferta viva: {'Sí' if top_ofertado['oferta_viva'] else 'No'}")
        if not df_campo.empty:
            _m = df_campo["marca"].value_counts()
            st.caption(
                f"En calle, la marca más vista es **{_m.index[0]}** "
                f"({_m.iloc[0]}/{len(df_campo)}). Detalle en 🗺️ Trabajo de campo."
            )
        st.caption("El más anunciado no es necesariamente el mejor valorado.")
    else:
        st.info("Sin datos de scoring")

with col_t2:
    st.markdown("### 2️⃣ El mejor eléctrico (no hay «mejor global»)")
    st.markdown("""
    - **Mejor equilibrio precio/autonomía/carga** dentro de su grupo
    - **Oferta viva** en más de una fuente (`repuestos_proxy`)
    - **Legalidad mencionada** en el anuncio
    - Los scores se normalizan **dentro de cada propulsión**: no se comparan
      eléctricos con híbridos ni con gasolina.
    """)
    _elec = top_por_propulsion(df_scores, "electrico", 2)
    if not _elec.empty:
        _top = _elec.iloc[0]
        st.caption(
            f"**{_top['modelo_norm']}** · "
            f"Precio: {f'${_top.precio_usd:,.0f}' if pd.notna(_top.precio_usd) else '—'} | "
            f"Autonomía: {f'{_top.autonomia_km:.0f} km' if pd.notna(_top.autonomia_km) else '—'} | "
            f"Carga: {f'{_top.carga_kg:.0f} kg' if pd.notna(_top.carga_kg) else '—'}"
        )
        if len(_elec) >= 2:
            _brecha = float(_elec.iloc[0]["score"] - _elec.iloc[1]["score"])
            _n_elec = df_scores[df_scores["propulsion"] == "electrico"]
            _n_un = int((_n_elec["n_anuncios_total"] == 1).sum())
            st.caption(
                f"Brecha con el 2º: **{_brecha:.3f}**. "
                f"{_n_un} de {len(_n_elec)} eléctricos tienen un solo anuncio: "
                "con esta muestra el orden no es concluyente."
            )
    else:
        st.info("Sin datos eléctricos")

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

_sens = texto_sensibilidad_electrico(df_sens, df_sens_res)
if _sens and not _sens.startswith("Pendiente"):
    st.caption(f"🔎 Robustez del podio eléctrico: {_sens}")

st.markdown("---")

# ======= TOP 3 POR PROPULSIÓN =======
st.subheader("🏆 Top 3 por propulsión (score)")

if not df_scores.empty:
    tabs = st.tabs(["⚡ Eléctricos", "🔄 Híbridos", "⛽ Gasolina"])
    for i, prop in enumerate(["electrico", "hibrido", "gasolina"]):
        with tabs[i]:
            sub = top_por_propulsion(df_scores, prop, 3)
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