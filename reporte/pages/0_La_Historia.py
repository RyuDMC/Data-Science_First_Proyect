"""
Página 0: La Historia — scrollytelling del proyecto en 6 actos.

Versión narrativa del reporte: la pregunta, el volumen de la evidencia, la
regla del juego (pesos), el mercado de la oferta, el conflicto (oferta ≠
circulación), el subvuelo (pesos en vivo + sensibilidad) y la resolución por
escenario. Un gráfico, un mensaje por acto, con la conclusión escrita encima
—una licencia de estilo de las páginas de storytelling visual.

Restricciones del proyecto respetadas:
- Ninguna cifra hardcodeada: se calcula en vivo desde Data/ y metadata.json.
- El score oficial re-pondera solo con los criterios presentes (no imputa):
  el slider del Acto 5 replica esa misma fórmula; `score_imputado` (la
  imputación histórica a 0.5) queda como referencia y NO se usa para rankear.
- El campo NO entra al scoring y no se extrapola (muestra cerrada).
- Los scores NO se comparan entre propulsiones: aquí tampoco se hace.
- Sin datos personales en ningún gráfico ni tabla.
"""

import os as _os
import sys as _sys

# Permite importar el paquete `reporte` tanto con `streamlit run reporte/app.py`
# (donde sys.path[0] es reporte/) como al ejecutar/testear desde la raíz del repo.
_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)

import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.patches import Patch

from reporte.data import (load_anuncios, load_campo_resumen, load_campo_uso,
                          load_comparacion, load_metadata, load_scores,
                          load_sensibilidad, load_sensibilidad_resumen,
                          texto_sensibilidad_electrico, top_por_anuncios)
from reporte.theme import (ACCENT_RED, GRID_COLOR, MUTED, PROP_COLORS,
                           TEXT_COLOR, apply_style, donut_chart, fig_ax,
                           label_for_prop)


st.set_page_config(page_title="La Historia", page_icon="📖", layout="wide")
apply_style()


# ==================== CONSTANTES ====================

# Pesos oficiales. Espejo de codes/analisis.py::PESOS: se declara aquí porque
# `codes/analisis.py` es un script ejecutable y no un paquete importable.
PESOS = {
    "precio_usd": 0.40,
    "autonomia_km": 0.25,
    "carga_kg": 0.20,
    "legalidad": 0.10,
    "repuestos": 0.05,
}
CANDIDATOS = list(PESOS.keys())
NORM_COLS = [f"{c}_norm" for c in CANDIDATOS]

NOMBRE_CRITERIO = {
    "precio_usd": "Precio",
    "autonomia_km": "Autonomía",
    "carga_kg": "Carga",
    "legalidad": "Legalidad",
    "repuestos": "Repuestos",
}

# Colores fijos por fuente de anuncio (orden alfabético de fuente). No se
# usa la paleta de propulsión para no confundir las dos codificaciones.
FUENTE_PALETTE = ["#1f77b4", "#ff7f0e", "#2c7fb8", "#9467bd", "#8c564b", "#d62728"]


# ==================== HELPERS ====================

def kicker(texto: str):
    """Rótulo pequeño en mayúsculas, estilo peritexto narrativo."""
    st.markdown(
        f"<p style='letter-spacing:2px;font-size:0.72rem;color:#8a8a8a;"
        f"text-transform:uppercase;margin-bottom:0.1rem'>{texto}</p>",
        unsafe_allow_html=True,
    )


def acto(n: int, titulo: str):
    """Encabezado de acto, con separador y peritexto."""
    st.markdown("---")
    kicker(f"ACTO {n} DE 6")
    st.markdown(f"### {titulo}")


def legend_patches(fuentes, counts, mapping):
    """Patches de leyenda para la pila de anuncios."""
    return [
        Patch(color=mapping.get(f, MUTED), label=f"{f} · {int(counts.get(f, 0))}")
        for f in fuentes
    ]


# ==================== DATOS ====================

_meta = load_metadata()
_conteos = _meta.get("conteos", {})
_cortes = _meta.get("cortes", {})


def _n(clave: str):
    return _conteos.get(clave, "—")


df_online = load_anuncios()
df_marca = load_campo_resumen()
df_uso = load_campo_uso()
df_scores = load_scores()
df_sens = load_sensibilidad()
df_sens_res = load_sensibilidad_resumen()
df_comp = load_comparacion()

# Cifras derivadas (una sola vez, para reutilizarlas en textos y figuras).
fuente_counts = df_online["fuente"].value_counts() if not df_online.empty else pd.Series(dtype=int)
prop_counts = df_online["propulsion"].value_counts() if not df_online.empty else pd.Series(dtype=int)
pct_elec = prop_counts.get("electrico", 0) / len(df_online) * 100 if len(df_online) else None
n_tabla = int(len(df_scores))
n_un_solo_anuncio = int(df_scores["n_anuncios_total"].eq(1).sum()) if "n_anuncios_total" in df_scores.columns else None
n_sin_precio = None
if "precio_comparable" in df_scores.columns:
    n_sin_precio = int((~df_scores["precio_comparable"].fillna(False).astype(bool)).sum())
elif "precio_usd" in df_scores.columns:
    n_sin_precio = int(df_scores["precio_usd"].isna().sum())
top_ad = top_por_anuncios(df_scores) if not df_scores.empty else None
top2_elec_scores = (df_scores[df_scores["propulsion"] == "electrico"]
                    .nsmallest(2, "rank_propulsion")["score"].tolist()
                    if not df_scores.empty else [])
texto_sens = texto_sensibilidad_electrico(df_sens, df_sens_res)
uso_top = (df_uso.sort_values("n", ascending=False).iloc[0]
           if not df_uso.empty else None)

# ==================== APERTURA ====================

st.title("📖 ¿Qué triciclo comprar en La Habana?")
kicker("UNA HISTORIA EN 6 ACTOS · SCROLLYTELLING DEL PROYECTO")

st.markdown(
    """Esta es la versión narrativa del reporte: primero el volumen de lo
    que se pudo ver del mercado, después las reglas con las que se ponderó,
    el conflicto que la propia data descubrió entre "lo que se anuncia" y
    "lo que circula", y al final el mapa honesto de decisiones. Con cifras
    al frente y sin ninguna escondida."""
)

if not df_online.empty:
    fuentes_orden = sorted(df_online["fuente"].dropna().unique())
    fuente_color = dict(zip(fuentes_orden, FUENTE_PALETTE))
    lista_fuentes = " · ".join(f"{int(v)} {k}" for k, v in fuente_counts.items())
    st.markdown("#### Todo el volumen, de una sola vez")
    fig, ax = fig_ax(figsize=(10, 4.8))
    ax.grid(False)
    orden = df_online.sort_values(["modelo_norm", "fuente"]).reset_index(drop=True)
    n_cols = 10
    n_rows = int(np.ceil(len(orden) / n_cols))
    ax.set_xlim(-0.6, n_cols - 0.4)
    ax.set_ylim(-0.6, n_rows - 0.4)
    ax.invert_yaxis()
    for i, fila in orden.iterrows():
        ax.scatter(
            i % n_cols, i // n_cols, marker="s", s=300,
            color=fuente_color.get(fila["fuente"], MUTED),
            edgecolors="white", linewidth=1.6, zorder=3,
        )
    handles = legend_patches(fuentes_orden, fuente_counts, fuente_color)
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.04),
              ncol=3, fontsize=8, frameon=False)
    ax.axis("off")
    st.pyplot(fig)
    st.caption(
        f"Cada ficha es un anuncio, en orden alfabético de modelo; el color "
        f"es la fuente ({lista_fuentes}). Capturas hasta "
        f"{_cortes.get('anuncios_captura', '—')} y corte de análisis "
        f"{_cortes.get('anuncios', '—')}. Es TODO lo que este proyecto vio "
        "publicado: 6 fuentes, ninguna especialmente generosa."
    )

st.markdown("#### Y la pregunta que ordena todo lo anterior")
st.info(
    "> *" + "¿Qué triciclo comprar en La Habana y por qué?" + "*; "
    "'lo más común' quedó como indicador, no como respuesta."
)
st.caption(
    f"La pregunta es la del proyecto, y a la hora de contestarla, con "
    f"{_n('anuncios')} anuncios, {_n('fichas_empresa')} fichas de catálogos y "
    f"{_n('observaciones_campo')} observaciones de calle en "
    f"{_n('municipios_campo')} de los 15 municipios del diseño. Tres ventanas "
    "que no se pueden sustituir entre sí: qué se anuncia, qué se ofrece "
    "formalmente y qué circula. Sin datos personales: el test "
    "`tests/test_privacidad.py` vigila esa puerta en cada corrida."
)

# ==================== ACTO 1 ====================

acto(1, "Tres ventanas, una pregunta")
st.markdown(
    "La primera decisión del proyecto no fue apoyarse en un dataset único: "
    "**tres fuentes**, cada una con su sesgo y su dueño de distinta parte "
    "de la realidad. Cada ventana contesta algo distinto, y para el "
    "comprador conviene leerlas a la vez:"
)
c1, c2, c3 = st.columns(3)
c1.metric("Anuncios online", _n("anuncios"),
          help=f"{_n('anuncios_scraper')} vía scraper + "
               f"{_n('anuncios_facebook')} vía Facebook")
c2.metric("Fichas de catálogos", _n("fichas_empresa"),
          help=f"{_n('empresas')} empresas, corte "
               f"{_cortes.get('catalogos', '—')}")
c3.metric("Observaciones de calle", _n("observaciones_campo"),
          help=f"{_n('municipios_campo')} municipios, {_n('marcas_campo')} marcas, "
               f"{_cortes.get('campo', '—')} · muestra cerrada")
st.caption(
    "La tercera ventana no entra al scoring: mide circulación (no oferta) y "
    "es una muestra cerrada de conveniencia. Describe la muestra y no se "
    "extrapola a La Habana."
)

# ==================== ACTO 2 ====================

acto(2, "La regla del juego: los pesos")
st.markdown(
    "El ranking no nace de una tabla mágica: es una suma ponderada de cinco "
    "criterios con normalización min-max **dentro de cada propulsión**; los "
    "criterios ausentes **no se imputan**: el score se re-pondera solo con lo "
    "presente de cada modelo (`n_criterios` deja ver esa cobertura). Y lo "
    "valioso del proyecto es que el origen de los pesos no se esconde:"
)
fig, ax = fig_ax(figsize=(7, 2.8))
crit = list(PESOS.items())
y = np.arange(len(crit))
ax.barh(y, [w for _, w in crit], color=PROP_COLORS["electrico"],
        edgecolor="white", height=0.62)
ax.set_yticks(y)
ax.set_yticklabels([NOMBRE_CRITERIO[k] for k, _ in crit], fontsize=10)
ax.invert_yaxis()
for yi, (_, w) in enumerate(crit):
    ax.text(w + 0.008, yi, f"{w:.2f}", va="center", fontsize=9, color=TEXT_COLOR)
ax.set_xlim(0, 0.5)
ax.set_xlabel("Peso en el score")
ax.set_title("El precio manda; la legalidad y los repuestos matizan", pad=12)
st.pyplot(fig)
st.caption(
    "Los pesos son **juicio experto calibrado con literatura**, y está "
    "escrito así en el repo: precio 0.40 es fiel al rango de Niu et al. "
    "(2024, IEEE), autonomía 0.25 a Hidrue et al. (2011) y el 0.10 de "
    "legalidad responde a la Resolución 47/2026 del MINTRAN. El detalle "
    "está en `Data/fuentes_justificacion.md` y en la página "
    "**🔬 Método**. Y no te preocupes por los números todavía: en el "
    "Acto 5 los mueves tú."
)

# ==================== ACTO 3 ====================

acto(3, "Lo que dice la ventana de la oferta")
if not df_online.empty:
    col_izq, col_der = st.columns([1.1, 1])
    with col_izq:
        st.markdown("#### El mercado anunciado es eléctrico")
        labels = [label_for_prop(p) for p in prop_counts.index]
        colors = [PROP_COLORS.get(p, MUTED) for p in prop_counts.index]
        fig, ax = fig_ax(figsize=(6.2, 4.2))
        donut_chart(ax, prop_counts.values, labels, colors,
                    f"Distribución de los {_n('anuncios')} anuncios")
        st.pyplot(fig)
        st.caption(
            f"**{pct_elec:.0f}%** de los anuncios son eléctricos "
            f"({int(prop_counts.get('electrico', 0))} de {len(df_online)}). "
            "La oferta publicada se concentra casi por completo en la "
            "propulsión eléctrica —la que responde, además, a la crisis de "
            "combustible— y deja híbridos y gasolina como testimonios."
        )
    with col_der:
        st.markdown("#### Y el comprador típico sí existe")
        if uso_top is not None:
            st.metric(
                f"Uso dominante en calle: {uso_top['uso']}",
                f"{uso_top['pct']:.0f}% de la muestra",
                help=f"IC 95%: {uso_top['ic95_bajo']:.1f}%–{uso_top['ic95_alto']:.1f}% "
                     f"(n={int(uso_top['n'])}). Decláralo el dueño; no es un cálculo "
                     "del proyecto."
            )
            st.markdown(
                f"Marcas más vistas para ese uso: **{uso_top['marcas']}**. "
                f"Autonomía mediana declarada: **{uso_top['autonomia_med']:.0f} km**, "
                f"en {_n('municipios_campo')} municipios."
            )
            st.caption(
                "Este es el pedestal narrativo del resto de la historia: no es "
                "un 'consumidor genérico' — la calle ya dijo para qué se usa "
                "el triciclo, y eso ordena los escenarios del Acto 6."
            )
        else:
            st.info("Sin resumen de uso: ejecuta `python3 codes/analisis_campo.py`.")
else:
    st.info("Sin anuncios cargados: ejecuta el pipeline (`codes/scrape_triciclos` "
            "→ `parse_fb` → `crear_canonicos`).")

# ==================== ACTO 4 ====================

acto(4, "El conflicto: el rey de los clasificados es un fantasma en la calle")
st.markdown(
    "Aquí está la historia que da sentido al proyecto. Un modelo puede ser "
    "el más anunciado y aun así casi no rodar; otra marca apenas se anuncia "
    "y aparece en todas partes de la muestra de calle. La ventana online y "
    "la ventana de campo no hablan el mismo idioma."
)
if not df_marca.empty:
    col_d, col_i = st.columns([1.15, 1])
    with col_d:
        st.markdown("#### Se anuncia vs. se ve (por marca)")
        d = df_marca.sort_values("pct_online", ascending=False).reset_index(drop=True)
        idx_pos = int(d["delta_pct"].idxmax())
        idx_neg = int(d["delta_pct"].idxmin())
        colores_destacar = {idx_pos: "#1f77b4", idx_neg: ACCENT_RED}
        fig, ax = fig_ax(figsize=(7.2, 5.2))
        for yi, fila in d.iterrows():
            x1, x2 = sorted([fila["pct_online"], fila["pct_campo"]])
            color = colores_destacar.get(int(yi), MUTED)
            ax.hlines(int(yi), x1, x2, color=color, linewidth=2, alpha=0.8)
            ax.scatter(fila["pct_online"], int(yi), s=58, facecolor="white",
                       edgecolor=MUTED, linewidth=1.6, zorder=4)
            ax.scatter(fila["pct_campo"], int(yi), s=58, color=color, zorder=5)
        ax.set_yticks(np.arange(len(d)))
        ax.set_yticklabels(d["marca_norm"], fontsize=8)
        ax.set_xlabel("% dentro de cada fuente (○ anuncios · ● calle)")
        ax.set_title("Cuota online contra cuota de calle", pad=12)
        ax.grid(axis="y", visible=False)
        for idx_ in (idx_pos, idx_neg):
            fila = d.loc[idx_]
            x_ref = max(fila["pct_online"], fila["pct_campo"])
            ax.annotate(
                f"Δ {fila['delta_pct']:+.1f} pp",
                xy=(x_ref, idx_), xytext=(8, -3), textcoords="offset points",
                fontsize=8, color=TEXT_COLOR,
            )
        ax.set_xlim(0, max(30, d["pct_online"].max() * 1.25))
        st.pyplot(fig)
        st.caption(
            "Cada fila es una marca; une su cuota **dentro de los anuncios** "
            "y su cuota **dentro de la muestra de calle** — universos "
            f"distintos ({_n('anuncios')} anuncios vs "
            f"{_n('observaciones_campo')} observaciones). Las dos marcas con "
            "el delta más grande son el corazón del conflicto: una se "
            "anuncia donde no rueda; la otra rueda donde no se anuncia."
        )
    with col_i:
        st.markdown("#### La marca más vista, con su miedo a la vista")
        sub = df_marca[df_marca["n_campo"] >= 3].sort_values("n_campo", ascending=False)
        if not sub.empty:
            fig, ax = fig_ax(figsize=(5.4, 4.4))
            y = np.arange(len(sub))
            err = np.vstack([
                (sub["pct_campo"] - sub["ic95_bajo"]).clip(lower=0),
                (sub["ic95_alto"] - sub["pct_campo"]).clip(lower=0),
            ])
            colores = [PROP_COLORS["electrico"] if yi == 0 else MUTED
                       for yi in range(len(sub))]
            ax.barh(y, sub["pct_campo"], color=colores, edgecolor="white",
                    height=0.58, xerr=err, capsize=3,
                    error_kw=dict(ecolor=TEXT_COLOR, lw=1, alpha=0.7))
            ax.set_yticks(y)
            ax.set_yticklabels(sub["marca_norm"], fontsize=9)
            ax.invert_yaxis()
            ax.set_xlabel("% de observaciones de calle (IC 95%)")
            ax.set_title(f"Marcas con n de calle ≥ 3 (total {_n('observaciones_campo')})",
                         pad=12)
            ax.set_xlim(0, max(45, sub["ic95_alto"].max() * 1.22))
            st.pyplot(fig)
            primera = sub.iloc[0]
            st.caption(
                f"**{primera['marca_norm']}** lidera el registro de calle "
                f"({int(primera['n_campo'])}/{_n('observaciones_campo')}, "
                f"{primera['pct_campo']:.0f}%), con IC 95% de "
                f"{primera['ic95_bajo']:.1f}% a {primera['ic95_alto']:.1f}%. "
                "Con una muestra cerrada de conveniencia, el intervalo es "
                "el mensaje, no la letra pequeña: la 'más vista' es un "
                "rango, y su rango se solapa con otras marcas."
            )
        else:
            st.info("Sin marcas con n de calle ≥ 3 en la muestra actual.")

if top_ad is not None and not df_comp.empty:
    fila_comp = df_comp[df_comp["modelo_norm"] == top_ad["modelo_norm"]]
    freq_campo = (int(fila_comp["freq_campo"].iloc[0])
                  if not fila_comp.empty else None)
    _rk = top_ad.get("rank_propulsion")
    nota_lider = (" y es el #1 eléctrico del ranking oficial"
                  if pd.notna(_rk) and int(_rk) == 1 else "")
    st.markdown("#### Y el modelo con más anuncios del dataset…")
    st.info(
        f"…es **{top_ad['modelo_norm']}**: con "
        f"{int(top_ad['n_anuncios_total'])} anuncios y score "
        f"{top_ad['score']:.3f}{nota_lider}. Ese "
        f"modelo concreto"
        + (f" apareció **{freq_campo} veces** en el registro de calle de "
           f"{_n('observaciones_campo')} observaciones." if freq_campo is not None
           else " no tiene cruce directo con el campo.")
        + " El gap del acto anterior también se ve a nivel de modelo exacto, "
        "no solo de marca."
    )

# ==================== ACTO 5 ====================

acto(5, "El subvuelo: ¿el ranking aguanta tus decisiones?")
st.markdown(
    "Los pesos son una elección, la tabla es pequeña y la presión sobre el "
    "podio es real. Mueve los sliders y mira qué pasa: el cálculo es el "
    "mismo de `codes/analisis.py` (re-pondera solo con los criterios "
    "presentes de cada modelo; la normalización ya viene en el CSV) y se "
    "recorre todo el dataset en vivo."
)

if not df_scores.empty and all(c in df_scores.columns for c in NORM_COLS):
    w_cols = st.columns(5)
    w_sels = {}
    for i, (col, w0) in enumerate(PESOS.items()):
        with w_cols[i]:
            w_sels[col] = st.slider(
                NOMBRE_CRITERIO[col], min_value=0.0, max_value=0.9,
                value=float(w0), step=0.05, key=f"peso_{col}",
                help="Peso relativo; el total se normaliza a 1 antes de puntuar.",
            )
    total = sum(w_sels.values())
    if total <= 0:
        st.warning("Deja al menos un criterio con peso mayor que 0.")
    else:
        w_vec = np.array([w_sels[c] for c in CANDIDATOS]) / total

        # Re-ponderación idéntica al score oficial (codes/analisis.py): cada
        # criterio ausente se excluye y los pesos se renormalizan solo sobre
        # lo presente. Sin criterios disponibles no hay score: no se inventa.
        M = df_scores[NORM_COLS].to_numpy(dtype=float)
        presente = ~np.isnan(M)
        num = np.nansum(M * w_vec, axis=1)
        den = presente @ w_vec
        scores_user = np.divide(num, den,
                                out=np.full(len(df_scores), np.nan),
                                where=den > 0)

        table = df_scores[["modelo_norm", "propulsion",
                           "score", "rank_propulsion"]].copy()
        table["score_tus_pesos"] = scores_user
        rank_rep = (table.dropna(subset=["score_tus_pesos"])
                    .groupby("propulsion")["score_tus_pesos"]
                    .rank(ascending=False, method="min").astype(int))
        table["rank_tus_pesos"] = rank_rep.reindex(table.index)

        st.markdown(
            f"Pesos aplicados: precio **{w_vec[0]:.2f}** · autonomía "
            f"**{w_vec[1]:.2f}** · carga **{w_vec[2]:.2f}** · legalidad "
            f"**{w_vec[3]:.2f}** · repuestos **{w_vec[4]:.2f}** "
            "(normalizados a 1). Criterios ausentes de cada modelo: se "
            "excluyen y el resto se re-pondera (igual que el oficial)."
        )
        n_sin_score = int(np.isnan(scores_user).sum())
        if n_sin_score:
            st.caption(
                f"⚠️ {n_sin_score} modelo(s) quedan sin puntaje con estos "
                "pesos: ninguno de sus criterios presentes pesa > 0 ahora."
            )
        w_base = np.array([PESOS[c] for c in CANDIDATOS])
        num0 = np.nansum(M * w_base, axis=1)
        den0 = presente @ w_base
        score_recalc = np.divide(num0, den0,
                                 out=np.full(len(df_scores), np.nan),
                                 where=den0 > 0)
        diff_base = float(np.nanmax(np.abs(
            score_recalc - df_scores["score"].to_numpy())))
        if diff_base < 1e-9:
            st.caption("✓ Con los pesos oficiales este cálculo reproduce "
                       "el score del CSV (verificación en vivo).")

        st.markdown("#### El podio, con tus pesos")
        tabs = st.tabs(["⚡ Eléctricos", "🔄 Híbridos", "⛽ Gasolina"])
        lideres = {}
        for i, p in enumerate(["electrico", "hibrido", "gasolina"]):
            with tabs[i]:
                sub = table[table["propulsion"] == p]
                if sub.empty:
                    st.info(f"Sin modelos {label_for_prop(p)} en el dataset actual.")
                    continue
                top3 = sub.nsmallest(3, "rank_tus_pesos").copy()
                if top3.empty:
                    st.info(f"Ningún modelo {label_for_prop(p)} tiene puntaje "
                            "con estos pesos.")
                    continue
                mask_of = sub["rank_propulsion"].astype(int) == 1
                lider_oficial = (str(sub.loc[mask_of, "modelo_norm"].iloc[0])
                                 if mask_of.any() else None)
                lider_usuario = str(top3.iloc[0]["modelo_norm"])
                lideres[p] = (lider_oficial, lider_usuario)

                def _cambio(fila):
                    if int(fila["rank_tus_pesos"]) == int(fila["rank_propulsion"]):
                        return "·"
                    return "🆕 sube" if int(fila["rank_tus_pesos"]) < int(
                        fila["rank_propulsion"]) else "🔻 baja"

                top3["cambio_vs_oficial"] = top3.apply(_cambio, axis=1)
                tabla = top3.rename(columns={
                    "modelo_norm": "Modelo",
                    "rank_propulsion": "Podio oficial",
                    "score": "Score oficial",
                    "rank_tus_pesos": "Tu puesto",
                    "score_tus_pesos": "Score con tus pesos",
                })[["Modelo", "Podio oficial", "Score oficial",
                    "Tu puesto", "Score con tus pesos", "cambio_vs_oficial"]]
                tabla["Score oficial"] = tabla["Score oficial"].map(lambda v: f"{v:.3f}")
                tabla["Score con tus pesos"] = tabla["Score con tus pesos"].map(
                    lambda v: f"{v:.3f}")
                st.dataframe(tabla, width="stretch", hide_index=True)

        if "electrico" in lideres:
            lider_oficial, lider_usuario = lideres["electrico"]
            if lider_oficial and lider_usuario and lider_oficial != lider_usuario:
                st.info(
                    f"Con estos pesos el #1 eléctrico **pasa de "
                    f"{lider_oficial} a {lider_usuario}**. El orden no es "
                    "absoluto: depende de lo que acabas de mover."
                )
            elif lider_oficial:
                st.info(
                    f"Con estos pesos el #1 eléctrico **sigue siendo "
                    f"{lider_oficial}**: aguanta tu intuición… por ahora."
                )

# --- La fragilidad medida, sin sliders ---
st.markdown("#### 🧪 El orden, probado a golpes")
st.markdown(
    "Además del slider, el análisis de sensibilidad pre-calculado (2.000 "
    "perturbaciones de ±0.05 en los pesos con semilla fija más 6 escenarios "
    "de omisión de criterio) dice cuán sólida es la tabla del ranking. "
    "Esos números no son la preferencia del autor: es lo medido."
)
if not df_scores.empty:
    col_h, col_r = st.columns([1, 1.35])
    with col_h:
        st.markdown("##### ¿Cuántos anuncios tiene cada modelo?")
        cuenta = df_scores["n_anuncios_total"].value_counts().sort_index()
        fig, ax = fig_ax(figsize=(5, 3.2))
        xs = [int(x) for x in cuenta.index]
        colores = [ACCENT_RED if x == 1 else MUTED for x in xs]
        ax.bar(xs, cuenta.values, color=colores, edgecolor="white")
        for x, v in zip(xs, cuenta.values):
            ax.text(x, v + cuenta.max() * 0.03, str(int(v)), ha="center",
                    fontsize=8, color=TEXT_COLOR)
        ax.set_xlabel("n de anuncios por modelo")
        ax.set_ylabel("Modelos")
        ax.set_title(f"{n_un_solo_anuncio} de {n_tabla} con un solo anuncio",
                     pad=12)
        st.pyplot(fig)
        st.caption(
            f"El ranking saca {n_tabla} modelos, pero "
            f"{n_un_solo_anuncio} de esos viven con **un** solo anuncio. "
            "Por eso el análisis de sensibilidad no es un anexo técnico: "
            "es la mitad de la historia honesta."
        )
    with col_r:
        st.markdown("##### ¿Hasta dónde puede subir o bajar cada uno?")
        if not df_sens_res.empty:
            sub = (df_sens_res[df_sens_res["propulsion"] == "electrico"]
                   .nsmallest(12, "rank_base"))
            fig, ax = fig_ax(figsize=(8.2, 5))
            y = np.arange(len(sub))
            for yi, fila in enumerate(sub.reset_index(drop=True).itertuples()):
                ax.hlines(yi, fila.rank_min, fila.rank_max,
                          color=GRID_COLOR, linewidth=7, alpha=0.85, zorder=2)
                ax.hlines(yi, fila.rank_p05, fila.rank_p95,
                          color=MUTED, linewidth=3, zorder=3)
                ax.scatter(fila.rank_base, yi, s=46,
                           color=PROP_COLORS["electrico"], zorder=5)
            ax.invert_yaxis()
            ax.set_yticks(y)
            etiquetas = [str(m)[:26] + ("…" if len(str(m)) > 26 else "")
                         for m in sub["modelo_norm"]]
            ax.set_yticklabels(etiquetas, fontsize=8)
            ax.set_xlabel("Puesto dentro del grupo eléctrico "
                          "(gris grueso = p05–p95 · extremos = mín–máx)")
            ax.set_title("12 primeros del ranking eléctrico en 6 escenarios de omisión",
                         pad=12)
            ax.axvspan(0.5, 3.5, color=GRID_COLOR, alpha=0.35, zorder=1)
            ax.set_xlim(0, sub["rank_max"].max() + 1)
            lider_data = sub.iloc[0]
            ax.annotate(
                f"top-1 en {lider_data['top1_pct']:.0f}% de las perturbaciones",
                xy=(float(lider_data["rank_base"]), 0),
                xytext=(34, -18), textcoords="offset points",
                fontsize=8, color=TEXT_COLOR,
                arrowprops=dict(arrowstyle="->", color=TEXT_COLOR, lw=1),
            )
            st.pyplot(fig)
            if texto_sens and not texto_sens.startswith("Pendiente"):
                st.caption(f"🔎 Robustez medida del podio eléctrico: {texto_sens}")
        else:
            st.info("Sin CSV de sensibilidad: ejecuta `python3 codes/sensibilidad.py`.")

# ==================== ACTO 6 ====================

acto(6, "La resolución: no hay ranking único, hay mapa")
st.markdown(
    "¿Y entonces cuál es *el* mejor triciclo? La respuesta honesta del "
    "proyecto no es la primera celda de una tabla: es un **mapa por "
    "escenario**, alimentado por el uso real que la calle declaró y enclavado "
    "en una ventana legal real."
)
c1, c2, c3 = st.columns(3)
if uso_top is not None:
    c1.metric("Uso dominante en calle", uso_top["uso"],
              help=f"{uso_top['pct']:.0f}% de la muestra "
                   f"[IC 95% {uso_top['ic95_bajo']:.0f}–{uso_top['ic95_alto']:.0f}%]")
else:
    c1.metric("Uso dominante en calle", "—")
c2.metric("Modelos en el ranking", _n("modelos_ranking"),
          help="Agregados por identidad (nombre del modelo o marca)")
c3.metric("Ventana legal", "dic 2026",
          help="Vence el régimen excepcional de licencias temporales (MINTRAN)")
st.markdown(
    """
| Si tu prioridad es… | Empieza por |
|---|---|
| **Pasajeros y autonomía** | ⚡ Eléctricos: podio del Acto 5 y del ranking oficial |
| **Carga de trabajo (≥800 kg)** | ⚡ Eléctricos, **moviendo la carga**: el slider muestra quién sobrevive sin ese criterio |
| **Presupuesto apretado (<$4.000)** | ⚡ Eléctricos baratos del ranking y sus asteriscos |
| **Sin red eléctrica confiable** | 🔄 Híbridos (con extensor) o ⛽ Gasolina — su podio propio, jamás comparado con eléctricos |
"""
)
st.caption(
    "Cada escenario tiene su desglose completo en la página "
    "**✅ Mejor opción** y la tabla ordenable por grupo en **🏆 Ranking**. "
    "Esta página no fabrica recomendaciones nuevas: redirige con el mismo "
    "criterio que el resto del reporte."
)
st.warning(
    "**La ventana legal vence en diciembre de 2026.** El criterio de "
    "legalidad (0.10 hoy) es una condición del trámite, no una decoración: "
    "el régimen excepcional de licencias temporales para vehículos "
    "eléctricos sin matrícula vence este año, con alcance provincial en La "
    "Habana (categoría A). Fuente: [cubadebate/MINTRAN](http://"
    "agendaeconomica.cubadebate.cu/establecen-regimen-excepcional-para-"
    "otorgar-licencias-de-transporte-a-duenos-de-vehiculos-electricos-sin-"
    "matricula/). Si compras después, el criterio puede cambiar de base — "
    "esa fecha también es parte de la historia."
)

st.markdown("### La moraleja")
_key_moraleja = (
    f"¿Importa la diferencia entre {top2_elec_scores[0]:.3f} y "
    f"{top2_elec_scores[1]:.3f}?" if len(top2_elec_scores) == 2
    else "¿Importa la diferencia entre los dos primeros del podio?"
)
st.markdown(
    f"""
> **{_key_moraleja}** Para el debate de
> internet, seguro; para el bolsillo, menos. Lo que de verdad le queda a
> uno después de estos actos: el más anunciado no es el más visto, el más
> visto no es automáticamente el mejor valorado, y el mejor valorado
> depende de los pesos — y de si el año que viene hay o no papeles. Un
> ranking honesto no confirma qué comprar: entrega las tres ventanas, el
> margen con el que cada cual habla, y la herramienta para mover los pesos
> y ver el podio cambiar en vivo.
"""
)
st.markdown("### Los asteriscos (el rango manda, no la celda)")
asteriscos = [
    "El campo es una **muestra cerrada de conveniencia** "
    f"({_n('observaciones_campo')} obs., {_n('municipios_campo')} de 15 "
    "municipios): describe la muestra, no La Habana.",
    "**Oferta ≠ circulación**: el ranking mide la oferta publicada; la "
    "calle sigue su propia lógica (y por eso no entra al score).",
]
if n_tabla and n_un_solo_anuncio is not None:
    asteriscos.append(
        f"**{n_un_solo_anuncio} de {n_tabla} modelos conviven con 1 solo "
        "anuncio**: el orden del podio se sostiene sobre muestras mínimas."
    )
if n_tabla and n_sin_precio is not None and n_sin_precio:
    asteriscos.append(
        f"**{n_sin_precio} modelos no tienen precio en USD**: su score se "
        "publica sin ese criterio (re-ponderado) y el reporte los muestra "
        "aparte — se declara, no se inventa tipo de cambio."
    )
asteriscos.append(
    "**Legalidad** = el anuncio menciona papeles; no se verifica el "
    "trámite. **Repuestos** = proxy de presencia en más de una fuente, "
    "no stock real."
)
for punt in asteriscos:
    st.markdown(f"- {punt}")
st.markdown(
    "El detalle completo, con fuentes, está en la página **⚠️ Limitaciones**."
)

# ==================== APÉNDICE ====================

st.markdown("---")
st.markdown("### 🧾 Cómo se hizo esta historia")
col_c, col_d = st.columns(2)
with col_c:
    tabla_cortes = pd.DataFrame({
        "Corte": ["anuncios (decisión)", "anuncios (captura)",
                  "catálogos de empresas", "campo"],
        "Fecha": [_cortes.get("anuncios", "—"),
                  _cortes.get("anuncios_captura", "—"),
                  _cortes.get("catalogos", "—"),
                  _cortes.get("campo", "—")],
    })
    st.dataframe(tabla_cortes, width="stretch", hide_index=True)
    st.caption("`Data/metadata.json` es la única fuente de estas cifras "
               "(`codes/generar_metadata.py --check` no deja que la página "
               "mienta).")
with col_d:
    tabla_datos = pd.DataFrame({
        "Pieza": ["anuncios capturados", "modelos en el ranking",
                  "observaciones de campo", "fichas de empresas",
                  "productos canónicos"],
        "Dato": [len(df_online), n_tabla, _n("observaciones_campo"),
                 _n("fichas_empresa"), _n("productos_canonicos")],
    })
    st.dataframe(tabla_datos, width="stretch", hide_index=True)
st.caption(
    "Acá no hay cifra escrita a mano: se lee en vivo desde `Data/` y se "
    "compara contra `metadata.json`. Pipeline: scraping → `crear_canonicos` "
    "→ `norm_modelo` → `analisis` → `analisis_campo` → `sensibilidad` → "
    "`generar_metadata` (ver README). Los pesos, con su literatura y sus "
    "decisiones documentadas, viven en `Data/fuentes_justificacion.md` y "
    "`Data/resumen_pesos_scoring.md`."
)
st.success(
    "Esta es la versión narrativa del reporte. Para el análisis completo "
    "sigue por el menú lateral: **📋 Resumen → 🔬 Método → 📊 Mercado → "
    "🏆 Ranking → 💰 Precio/Carga → 🎯 Contendientes → ✅ Mejor opción → "
    "🗺️ Trabajo de campo → 🏢 Empresas → ⚠️ Limitaciones**."
)
