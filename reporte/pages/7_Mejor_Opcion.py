"""
Página 7: Mejor Opción — Recomendación por escenario.
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
from reporte.data import load_scores, load_campo_uso, filter_by_propulsion
from reporte.theme import apply_style, fig_ax, bar_ranking, color_for_prop, label_for_prop


st.set_page_config(page_title="Mejor Opción", page_icon="✅", layout="wide")
apply_style()

st.title("✅ La Mejor Opción — Por Escenario")

df_scores = load_scores()

if df_scores.empty:
    st.error("No hay datos de scoring. Ejecuta `python3 codes/analisis.py` primero.")
    st.stop()

# Solo ofertas vivas
df = df_scores[df_scores["oferta_viva"] == True].copy()

st.markdown("""
La "mejor opción" **depende de tu caso de uso**. No hay un ganador universal.
Aquí presentamos recomendaciones por escenario, **ordenadas por la frecuencia con
la que ese uso aparece en la calle** (trabajo de campo), no por un orden arbitrario.
""")

# ======= USO OBSERVADO (DATO DE CAMPO) =======
df_uso = load_campo_uso()
cuota_uso = {}
if not df_uso.empty:
    st.markdown("#### 📦 Cómo se usa en la calle")
    cols = st.columns(len(df_uso))
    for col, (_, r) in zip(cols, df_uso.iterrows()):
        col.metric(r["uso"].capitalize(), f"{r['pct']:.0f}%",
                   help=f"n={int(r['n'])} · IC 95%: {r['ic95_bajo']:.0f}–{r['ic95_alto']:.0f}%")
    cuota_uso = dict(zip(df_uso["uso"], df_uso["pct"]))
    st.caption(
        f"Uso declarado por {int(df_uso['n'].sum())} propietarios en 5 municipios "
        "(muestra cerrada, no censo). Es la ponderación que ordena los escenarios de abajo."
    )

# ======= ESCENARIOS =======
st.subheader("🎯 Recomendaciones por escenario")

escenarios = [
    {
        "titulo": "📦 Carga pesada (≥800 kg)",
        "filtro": "carga_kg >= 800",
        "orden": "score",
        "icon": "📦",
        "uso": "carga",
        "descripcion": "Para mover mercancía, materiales, equipamiento. Prioriza carga y robustez."
    },
    {
        "titulo": "👥 Pasajeros / Autonomía alta (≥100 km)",
        "filtro": "autonomia_km >= 100",
        "orden": "score",
        "icon": "👥",
        "uso": "pasajeros",
        "descripcion": "Para transporte de personas, recorridos largos. Prioriza autonomía y comodidad."
    },
    {
        "titulo": "💰 Presupuesto ajustado (<$4000)",
        "filtro": "precio_usd < 4000",
        "orden": "score",
        "icon": "💰",
        "uso": None,
        "descripcion": "Mejor relación valor/precio. Prioriza score alto con precio bajo."
    },
    {
        "titulo": "🔌 Sin infraestructura de carga (gasolina/híbrido)",
        "filtro": "propulsion in ['hibrido', 'gasolina']",
        "orden": "score",
        "icon": "⛽",
        "uso": None,
        "descripcion": "Donde no hay electricidad confiable. Híbrido = autonomía extendida; Gasolina = simple."
    }
]

# Orden por frecuencia observada del uso; los escenarios transversales
# (presupuesto, sin enchufe) van al final.
for esc in escenarios:
    esc["cuota"] = cuota_uso.get(esc["uso"]) if esc["uso"] else None
escenarios.sort(key=lambda e: (e["cuota"] is None, -(e["cuota"] or 0)))

for esc in escenarios:
    etiqueta = f"{esc['icon']} **{esc['titulo']}**"
    if esc["cuota"] is not None:
        etiqueta += f" — {esc['cuota']:.0f}% del uso observado"
    with st.expander(etiqueta, expanded=True):
        st.caption(esc['descripcion'])
        
        # Aplicar filtro
        if esc['filtro'] == "carga_kg >= 800":
            sub = df[df["carga_kg"] >= 800]
        elif esc['filtro'] == "autonomia_km >= 100":
            sub = df[df["autonomia_km"] >= 100]
        elif esc['filtro'] == "precio_usd < 4000":
            sub = df[df["precio_usd"] < 4000]
        elif esc['filtro'] == "propulsion in ['hibrido', 'gasolina']":
            sub = df[df["propulsion"].isin(["hibrido", "gasolina"])]
        else:
            sub = df
        
        sub = sub.sort_values(esc['orden'], ascending=False).head(3)
        
        if sub.empty:
            st.warning("No hay modelos que cumplan el criterio.")
            continue
        
        # Mostrar top 3
        for i, (_, row) in enumerate(sub.iterrows()):
            medal = ["🥇", "🥈", "🥉"][i]
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            col1.markdown(f"{medal} **{row['modelo_norm']}** ({label_for_prop(row['propulsion'])})")
            col2.metric("Score", f"{row['score']:.3f}")
            col3.metric("$", f"{row['precio_usd']:,.0f}" if pd.notna(row['precio_usd']) else "—")
            col4.metric("km", f"{row['autonomia_km']:.0f}" if pd.notna(row['autonomia_km']) else "—")
            col5.metric("kg", f"{row['carga_kg']:.0f}" if pd.notna(row['carga_kg']) else "—")

st.markdown("---")

# ======= MATRIZ DE DECISIÓN =======
st.subheader("📊 Matriz de decisión rápida")

# Crear matriz: filas = modelos top, columnas = escenarios
top_overall = df.sort_values("score", ascending=False).head(10)

matriz_data = []
for _, row in top_overall.iterrows():
    precio_ok = pd.notna(row['precio_usd']) and row['precio_usd'] < 4000
    carga_ok = pd.notna(row['carga_kg']) and row['carga_kg'] >= 800
    aut_ok = pd.notna(row['autonomia_km']) and row['autonomia_km'] >= 100
    no_electrico = row['propulsion'] in ['hibrido', 'gasolina']
    
    matriz_data.append({
        "Modelo": row['modelo_norm'],
        "Prop.": label_for_prop(row['propulsion']),
        "Score": f"{row['score']:.3f}",
        "Precio": f"${row['precio_usd']:,.0f}" if pd.notna(row['precio_usd']) else "—",
        "Aut.": f"{row['autonomia_km']:.0f}" if pd.notna(row['autonomia_km']) else "—",
        "Carga": f"{row['carga_kg']:.0f}" if pd.notna(row['carga_kg']) else "—",
        "Carga ≥800kg": "✅" if carga_ok else "❌",
        "Aut. ≥100km": "✅" if aut_ok else "❌",
        "Precio <$4k": "✅" if precio_ok else "❌",
        "Sin enchufe": "✅" if no_electrico else "❌",
    })

matriz_df = pd.DataFrame(matriz_data)
st.dataframe(matriz_df, width="stretch", hide_index=True)

st.caption("✅ = cumple criterio | ❌ = no cumple | Score ya pondera todos los criterios")

st.markdown("---")

# ======= GRÁFICO RESUMEN =======
st.subheader("📈 Score vs Precio (top 10 global)")

fig, ax = fig_ax(figsize=(10, 6))

top10 = df.sort_values("score", ascending=False).head(10)
colors = [color_for_prop(p) for p in top10["propulsion"]]

# Scatter score vs precio
for i, (_, row) in enumerate(top10.iterrows()):
    ax.scatter(row['precio_usd'], row['score'], s=200, c=colors[i], alpha=0.8, 
               edgecolors="white", linewidth=1, zorder=3)
    ax.annotate(row['modelo_norm'], (row['precio_usd'], row['score']),
                fontsize=8, ha="center", va="bottom", xytext=(0, 5), textcoords="offset points")

ax.set_xlabel("Precio (USD)")
ax.set_ylabel("Score (0-1)")
ax.set_title("Top 10 global: Score vs Precio — ¿Vale la pena pagar más?", pad=12)

# Leyenda
from matplotlib.patches import Patch
seen = set()
handles = []
for p in top10["propulsion"]:
    if p not in seen:
        handles.append(Patch(color=color_for_prop(p), label=label_for_prop(p)))
        seen.add(p)
ax.legend(handles=handles, loc="best", fontsize=9)

st.pyplot(fig)

st.markdown("""
**Lectura:** Modelos **arriba a la izquierda** = alto score, bajo precio (mejor valor).
Modelos **arriba a la derecha** = alto score, alto precio (premium).
La pendiente implícita te dice cuánto score "compras" por cada $1000 extra.
""")
