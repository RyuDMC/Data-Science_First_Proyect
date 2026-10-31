"""
Página 8: Trabajo de Campo — circulación real, incertidumbre y uso.

Fuente: Data/registro_ubicaciones.csv (codes/parse_campo.py) y las tablas
calculadas en codes/analisis_campo.py (campo_resumen.csv, campo_uso.csv).
El campo NO entra al scoring: mide circulación, no oferta.
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
from reporte.data import (load_campo, load_campo_resumen, load_campo_uso,
                          load_metadata)
from reporte.theme import (apply_style, fig_ax, PROP_COLORS, TEXT_COLOR, MUTED,
                           ACCENT_RED)


st.set_page_config(page_title="Trabajo de Campo", page_icon="🗺️", layout="wide")
apply_style()

# Cifras desde Data/metadata.json (única fuente; ver codes/generar_metadata.py).
_c = load_metadata().get("conteos", {})
_n = lambda clave: _c.get(clave, "—")  # noqa: E731

st.title("🗺️ Trabajo de Campo — Circulación Real (muestra cerrada)")

df_campo = load_campo()
df_marca = load_campo_resumen()
df_uso = load_campo_uso()

TOTAL_MUNICIPIOS = 15

if df_campo.empty:
    st.warning("""
    ⚠️ **Sin observaciones de campo en el repositorio.** El trabajo de campo ya
    está cerrado (decisión del proyecto, 2026-10-31): si esta sección está vacía
    es porque faltan los datos, no porque se vayan a recoger más adelante. La
    evidencia disponible es la de anuncios y catálogos de empresas.
    """)
else:
    n_muni = df_campo["municipio"].nunique()
    periodo = f"{df_campo['fecha'].min()} → {df_campo['fecha'].max()}"
    st.success(
        f"✅ **{len(df_campo)} observaciones** de circulación real en "
        f"**{n_muni} municipios** ({periodo}). **Muestra cerrada**: no habrá más "
        "trabajo de campo, así que los porcentajes describen esta muestra y no "
        "se extrapolan a toda La Habana."
    )

    # ======= KPIs =======
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Observaciones", len(df_campo))
    c2.metric("Municipios observados", f"{n_muni}/{TOTAL_MUNICIPIOS}",
              help="De los 15 municipios que preveía el diseño original.")
    c3.metric("Marcas distintas", df_campo["marca"].nunique())
    pct_elec = df_campo["propulsion"].eq("electrico").mean() * 100
    c4.metric("Eléctricos", f"{pct_elec:.0f}%",
              help="Resto: híbridos/gasolina. La propulsión se leyó en el vehículo.")

    st.markdown("---")

    # ======= TOP MARCAS CON INCERTIDUMBRE =======
    izq, der = st.columns(2)

    with izq:
        st.markdown("### 🥇 Marcas más vistas en calle")
        if not df_marca.empty:
            top = df_marca.sort_values("n_campo", ascending=False)
            fig, ax = fig_ax(figsize=(7, 4.8))
            y = np.arange(len(top))
            err = np.vstack([
                (top["pct_campo"] - top["ic95_bajo"]).clip(lower=0),
                (top["ic95_alto"] - top["pct_campo"]).clip(lower=0),
            ])
            ax.barh(y, top["pct_campo"], color=PROP_COLORS["electrico"],
                    edgecolor="white", height=0.65, xerr=err, capsize=3,
                    error_kw=dict(ecolor=TEXT_COLOR, lw=1, alpha=0.7))
            ax.set_yticks(y)
            ax.set_yticklabels(top["marca_norm"], fontsize=9)
            ax.invert_yaxis()
            ax.set_xlabel("% de las observaciones (IC 95%)")
            ax.set_title(f"Marca observada (n={int(top['n_campo'].sum())})", pad=12)
            for yi, (n, pct) in enumerate(zip(top["n_campo"], top["pct_campo"])):
                ax.text(top["ic95_alto"].iloc[yi] + 1, yi, f"{int(n)} ({pct:.0f}%)",
                        va="center", fontsize=8, color=TEXT_COLOR)
            ax.set_xlim(0, max(45, top["ic95_alto"].max() * 1.25))
            st.pyplot(fig)
            primera = top.iloc[0]
            st.caption(
                f"**{primera['marca_norm']}** es la más vista ({int(primera['n_campo'])} "
                f"de {int(top['n_campo'].sum())}), pero su IC va de "
                f"{primera['ic95_bajo']:.0f}% a {primera['ic95_alto']:.0f}%: con n=30 "
                "no se distingue estadísticamente de las que le siguen."
            )
        else:
            st.info("Sin resumen por marca. Ejecuta `python3 codes/analisis_campo.py`.")

    with der:
        st.markdown("### ⚖️ Calle vs anuncios (por marca)")
        if not df_marca.empty:
            top = df_marca.sort_values(["n_campo", "n_online"], ascending=False).head(10)
            fig, ax = fig_ax(figsize=(7, 4.8))
            y = np.arange(len(top))
            h = 0.38
            ax.barh(y - h / 2, top["pct_campo"], height=h, color=PROP_COLORS["electrico"],
                    edgecolor="white", label=f"Calle ({int(df_marca['n_campo'].sum())} obs.)")
            ax.barh(y + h / 2, top["pct_online"], height=h, color=MUTED,
                    edgecolor="white", label=f"Anuncios ({int(df_marca['n_online'].sum())})")
            ax.set_yticks(y)
            ax.set_yticklabels(top["marca_norm"], fontsize=9)
            ax.invert_yaxis()
            ax.set_xlabel("% dentro de su propia fuente")
            ax.set_title("Presencia real vs oferta anunciada", pad=12)
            ax.legend(fontsize=9, loc="lower right")
            st.pyplot(fig)
            st.caption(
                f"Se compara **cuota dentro de cada fuente** (no conteos): {_n('observaciones_campo')} observaciones "
                f"y {_n('anuncios')} anuncios son universos distintos. VEDCA es la marca más anunciada "
                "(24%) y aparece **una sola vez** en calle (3%)."
            )
        else:
            st.info("Sin datos de oferta para comparar.")

    st.markdown("---")

    # ======= A. MÁS COMÚN vs MEJOR VALORADO =======
    st.markdown("### 🎯 Más común en calle vs mejor valorado en el ranking")

    if not df_marca.empty and df_marca["mejor_score"].notna().any():
        comp = df_marca[df_marca["n_campo"] > 0].copy()
        comp["% calle [IC 95%]"] = (
            comp["pct_campo"].map(lambda v: f"{v:.1f}") + " [" +
            comp["ic95_bajo"].map(lambda v: f"{v:.1f}") + "–" +
            comp["ic95_alto"].map(lambda v: f"{v:.1f}") + "]"
        )
        comp["Score del mejor modelo"] = comp["mejor_score"].map(
            lambda v: f"{v:.3f}" if pd.notna(v) else "— (no está en la oferta)")
        comp["Precio"] = comp["precio_medio"].map(
            lambda v: f"${v:,.0f}" if pd.notna(v) else "—")
        tabla = comp.rename(columns={
            "marca_norm": "Marca",
            "n_campo": "Calle",
            "mejor_modelo": "Modelo mejor valorado",
        })[["Marca", "Calle", "% calle [IC 95%]", "Modelo mejor valorado",
            "Score del mejor modelo", "Precio"]]
        st.dataframe(tabla, use_container_width=True, hide_index=True)

        # Lectura automática, sin inventar: el más visto vs el mejor puntuado.
        mas_visto = comp.sort_values("n_campo", ascending=False).iloc[0]
        con_score = comp.dropna(subset=["mejor_score"])
        mejor = con_score.sort_values("mejor_score", ascending=False).iloc[0]
        if mas_visto["marca_norm"] != mejor["marca_norm"]:
            st.info(
                f"**La más común no es la mejor valorada.** En la muestra de calle, "
                f"la más vista es **{mas_visto['marca_norm']}** "
                f"({int(mas_visto['n_campo'])} obs.), "
                f"mientras el mejor score de su marca es {mas_visto['mejor_score']:.3f} "
                f"({mas_visto['mejor_modelo']}). El mejor valorado es **{mejor['marca_norm']}** "
                f"con {mejor['mejor_score']:.3f} ({mejor['mejor_modelo']}), y solo se vio "
                f"{int(mejor['n_campo'])} vez/veces en calle. Es exactamente el hueco que "
                "la pregunta central busca: *lo que se compra* ≠ *lo que rinde mejor*."
            )
    else:
        st.caption("Sin cruce con el score: ejecuta `python3 codes/analisis.py`.")

    st.markdown("---")

    # ======= C. USO OBSERVADO =======
    st.markdown("### 📦 Para qué se usa (uso declarado por el propietario)")

    if not df_uso.empty:
        izq3, der3 = st.columns([1.1, 1])
        with izq3:
            fig, ax = fig_ax(figsize=(6.5, 3.6))
            y = np.arange(len(df_uso))
            err = np.vstack([
                (df_uso["pct"] - df_uso["ic95_bajo"]).clip(lower=0),
                (df_uso["ic95_alto"] - df_uso["pct"]).clip(lower=0),
            ])
            ax.barh(y, df_uso["pct"], color=PROP_COLORS["electrico"],
                    edgecolor="white", height=0.6, xerr=err, capsize=3,
                    error_kw=dict(ecolor=TEXT_COLOR, lw=1, alpha=0.7))
            ax.set_yticks(y)
            ax.set_yticklabels([u.capitalize() for u in df_uso["uso"]], fontsize=9)
            ax.invert_yaxis()
            ax.set_xlabel("% de las observaciones (IC 95%)")
            ax.set_title("Uso observado en calle", pad=12)
            for yi, (n, pct) in enumerate(zip(df_uso["n"], df_uso["pct"])):
                ax.text(df_uso["ic95_alto"].iloc[yi] + 1.5, yi, f"{int(n)} ({pct:.0f}%)",
                        va="center", fontsize=8, color=TEXT_COLOR)
            ax.set_xlim(0, max(80, df_uso["ic95_alto"].max() * 1.2))
            st.pyplot(fig)
        with der3:
            tabla_uso = df_uso.rename(columns={
                "uso": "Uso", "n": "Obs.", "pct": "%",
                "marcas": "Marcas más vistas",
                "autonomia_med": "Autonomía mediana (km)",
                "n_municipios": "Municipios",
            })[["Uso", "Obs.", "%", "Marcas más vistas", "Autonomía mediana (km)", "Municipios"]]
            st.dataframe(tabla_uso, use_container_width=True, hide_index=True)
            st.caption(
                "El uso es **declarado** por el dueño en la entrevista. "
                "La palabra original de la hoja (\"familiar\", \"pasaje\", \"carga y pasaje\") "
                "se conserva en `uso_original`."
            )

        dominante = df_uso.sort_values("n", ascending=False).iloc[0]
        st.info(
            f"El uso dominante es **{dominante['uso']}** "
            f"({dominante['pct']:.0f}% de la muestra, n={int(dominante['n'])}). "
            "La página **✅ Mejor opción** ordena sus escenarios con esta frecuencia "
            "observada, no con un orden arbitrario."
        )

        # Cruce uso × municipio (densidad de uso por zona).
        st.markdown("**Uso por municipio**")
        cruce = (df_campo.groupby(["municipio", "uso"]).size().unstack(fill_value=0))
        st.dataframe(cruce, use_container_width=True)
    else:
        st.caption("Sin tabla de uso: ejecuta `python3 codes/analisis_campo.py`.")

    st.markdown("---")

    # ======= POR MUNICIPIO =======
    st.markdown("### 📍 Observaciones por municipio y marca")

    izq2, der2 = st.columns([1, 1.2])
    with izq2:
        muni = (df_campo.groupby(["municipio", "marca"]).size()
                .reset_index(name="obs")
                .sort_values(["municipio", "obs"], ascending=[True, False]))
        st.dataframe(muni, use_container_width=True, hide_index=True)
    with der2:
        pivot = df_campo.groupby(["municipio", "marca"]).size().unstack(fill_value=0)
        st.markdown("**Matriz municipio × marca**")
        st.dataframe(pivot, use_container_width=True)

    st.warning(f"""
    **Cómo leer estos datos.** Muestra **cerrada** de {_n('observaciones_campo')} observaciones en {_n('municipios_campo')} de los
    {TOTAL_MUNICIPIOS} municipios del diseño, tomadas en dos semanas: **no es un censo** y no se
    extrapola a La Habana. Sirve para ver qué marcas circulan y con qué uso, no
    para estimar cuotas poblacionales. Además no hay **denominador** (triciclos
    vistos por hora o por km), así que no se puede hablar de densidad.
    El trabajo de campo **no entra al scoring** (ese mide oferta).
    """)

if not df_campo.empty:
    # ======= ALCANCE DE LA MUESTRA =======
    st.markdown("---")
    st.subheader("📋 Alcance de la muestra (cerrada el 2026-10-31)")

    st.markdown("""
    **Decisión del proyecto:** no se hará más trabajo de campo. Lo que hay —30
    observaciones, 5 municipios, 2026-10-13 a 2026-10-25— es la evidencia de calle
    definitiva del estudio.

    **Qué se puede afirmar con esto**
    - Qué marcas circulan y en qué proporción **dentro de la muestra** (con intervalo de confianza).
    - Qué uso declaran los dueños (pasajeros / carga / mixto) y con qué specs reales.
    - Si la oferta anunciada coincide o no con lo que se ve en calle.

    **Qué NO se puede afirmar**
    - Que una marca sea "la más común en La Habana": 5 de 15 municipios y sin denominador.
    - Cuotas por municipio ni densidad de flota.
    - Comparaciones entre marcas con n=1: los intervalos se solapan.
    """)

    cubiertos = set(df_campo["municipio"]) if not df_campo.empty else set()
    municipios_diseno = [
        "Arroyo Naranjo", "Boyeros", "Centro Habana", "Cerro", "Cotorro",
        "Diez de Octubre", "Guanabacoa", "Habana del Este", "Habana Vieja",
        "La Lisa", "Marianao", "Plaza de la Revolución", "Playa", "Regla",
        "San Miguel del Padrón",
    ]
    estado_muni = pd.DataFrame({
        "Municipio": municipios_diseno,
        "Observado": ["✅" if m in cubiertos else "—" for m in municipios_diseno],
        "Observaciones": [
            int((df_campo["municipio"] == m).sum()) if not df_campo.empty else 0
            for m in municipios_diseno
        ],
    })
    st.dataframe(estado_muni, use_container_width=True, hide_index=True)

# ======= ESQUEMA DE DATOS =======
st.subheader("📊 Esquema de registro")

schema = pd.DataFrame({
    "Campo": ["fecha", "municipio", "tipo", "uso", "propulsion", "modelo", "marca", "motor", "estado", "observador", "notas"],
    "Tipo": ["date", "categoría", "categoría", "categoría", "categoría", "texto", "texto", "texto", "categoría", "texto", "texto"],
    "Ejemplo": ["2026-10-15", "Boyeros", "triciclo", "carga", "electrico", "KIVITOVA 2026", "KIVITOVA", "1200W", "bueno", "Juan P.", "Carga 600kg visible"],
    "Obligatorio": ["Sí", "Sí", "Sí", "Sí", "Sí", "No", "No", "No", "No", "Sí", "No"]
})
st.dataframe(schema, use_container_width=True, hide_index=True)

st.markdown("""
**Valores permitidos:**
- `tipo`: triciclo | cuatriciclo | motocarro | otro
- `uso`: carga | pasajeros | mixto | ocio_paseo
- `propulsion`: electrico | gasolina | hibrido | indeterminado
- `estado`: nuevo_0km | bueno | regular | malo

**Columnas añadidas por la captura real:** `obs_id` (identificador anónimo),
`uso_original` (palabra textual de la hoja), `bateria_v`, `bateria_v_origen`
(para correcciones trazables), `bateria_ah`, `autonomia_km` y `con_paneles`.
`modelo` queda vacío: la hoja registra marca, no modelo.
""")

# ======= CÓMO SE PROCESÓ =======
st.subheader("▶️ Cómo se procesó la hoja de campo")

st.code("""
# La hoja original (texto libre) NUNCA se commitea: lleva datos personales.
#    Data/raw_data/data_personas.txt                 (ignorado por git)

# 1. Ingesta: anonimiza (descarta nombre y CI), normaliza y valida
python3 codes/parse_campo.py
#    -> Data/registro_ubicaciones.csv

# 2. Análisis de oferta + identidad
python3 codes/analisis.py
#    -> clean_data/score_modelos.csv
#    -> clean_data/comparacion_campo_online.csv

# 3. Análisis del campo: cuotas, IC95, uso y cruce con el score
python3 codes/analisis_campo.py
#    -> clean_data/campo_resumen.csv
#    -> clean_data/campo_uso.csv

# 4. Verificar que el CSV coincide con la hoja (idempotencia)
python3 codes/parse_campo.py --check

# El reporte lee Data/ en vivo -> refresca y listo
reporte/.venv/bin/streamlit run reporte/app.py
""", language="bash")
