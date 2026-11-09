"""
Capa de datos para el reporte Streamlit.
Carga y normaliza datasets desde Data/clean_data/ con st.cache_data.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# La identidad del producto (regla del 2026-10-19) vive en codes/norm_modelo.py
# y es la MISMA que usa codes/analisis.py: si no hay nombre de modelo, la
# identidad es la marca. Aquí se importa por paquete, así que hace falta la
# raíz del repo en sys.path (Streamlit solo añade la carpeta del script).
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from codes.norm_modelo import identidad  # noqa: E402


CLEAN_DIR = REPO_ROOT / "Data" / "clean_data"
EMPRESAS_DIR = REPO_ROOT / "Data" / "empresas"
METADATA_PATH = REPO_ROOT / "Data" / "metadata.json"


@st.cache_data(show_spinner="Cargando metadatos…")
def load_metadata() -> dict:
    """Conteos y cortes del dataset (los genera `codes/generar_metadata.py`).

    Es la única fuente de las cifras que se muestran en portada, Método y
    Limitaciones. Si el archivo no existe, devuelve {} y las páginas muestran
    "—" en vez de romperse.
    """
    if not METADATA_PATH.exists():
        return {}
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


@st.cache_data(show_spinner="Cargando anuncios online…")
def load_anuncios() -> pd.DataFrame:
    """Carga y unifica anuncios_triciclos.jsonl + anuncios_facebook.jsonl."""
    files = [
        CLEAN_DIR / "anuncios_triciclos.jsonl",
        CLEAN_DIR / "anuncios_facebook.jsonl",
    ]
    dfs = []
    for f in files:
        if f.exists():
            df = pd.read_json(f, lines=True)
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)

    # Normalizaciones comunes
    if "propulsion" in df.columns:
        df["propulsion"] = df["propulsion"].fillna("indeterminado").str.lower()
    df["modelo_norm"] = identidad(df)
    if "precio_usd" in df.columns:
        df["precio_usd"] = pd.to_numeric(df["precio_usd"], errors="coerce")
    if "autonomia_km" in df.columns:
        df["autonomia_km"] = pd.to_numeric(df["autonomia_km"], errors="coerce")
    if "carga_kg" in df.columns:
        df["carga_kg"] = pd.to_numeric(df["carga_kg"], errors="coerce")
    if "motor_w" in df.columns:
        df["motor_w"] = pd.to_numeric(df["motor_w"], errors="coerce")
    if "motor_cc" in df.columns:
        df["motor_cc"] = pd.to_numeric(df["motor_cc"], errors="coerce")

    return df


@st.cache_data(show_spinner="Cargando catálogos de empresas…")
def load_empresas() -> pd.DataFrame:
    """Carga y unifica TODOS los JSONL de catálogos de empresas.

    La fuente única es `Data/empresas/` (lo que escribe
    `codes/scrape_empresas.py`), así que añadir un catálogo nuevo no obliga a
    tocar el reporte. No hay copia duplicada en `clean_data/` (unificada el
    2026-11-06: antes había dos copias idénticas de cada fichero).
    """
    nombres = (sorted(p.stem for p in EMPRESAS_DIR.glob("*.jsonl"))
               if EMPRESAS_DIR.exists() else [])
    files = [EMPRESAS_DIR / f"{n}.jsonl" for n in nombres]
    dfs = []
    for f in files:
        if f.exists():
            df = pd.read_json(f, lines=True)
            df["fuente_empresa"] = f.stem
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)

    # Normalizaciones
    if "propulsion" in df.columns:
        df["propulsion"] = df["propulsion"].fillna("indeterminado").str.lower()
    df["modelo_norm"] = identidad(df)
    # Nombre visible: si el producto no tiene nombre de modelo, se muestra
    # la marca (no un hueco en blanco en la tabla).
    if "modelo" in df.columns and "marca" in df.columns:
        df["nombre_producto"] = df["modelo"].where(
            df["modelo"].notna(), df["marca"].fillna("SIN MODELO"))
    for col in ["precio_usd", "autonomia_km", "carga_kg", "motor_w", "motor_cc"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


@st.cache_data(show_spinner="Cargando trabajo de campo…")
def load_campo() -> pd.DataFrame:
    """Carga registro_ubicaciones.csv (inventario municipal)."""
    path = CLEAN_DIR.parent / "registro_ubicaciones.csv"
    if not path.exists():
        return pd.DataFrame(columns=["fecha", "municipio", "tipo", "uso", "propulsion",
                                      "modelo", "marca", "motor", "estado", "observador", "notas"])
    df = pd.read_csv(path)
    df["modelo_norm"] = identidad(df, con_alias=False)
    if "propulsion" in df.columns:
        df["propulsion"] = df["propulsion"].fillna("indeterminado").str.lower()
    return df


@st.cache_data(show_spinner="Cargando scores…")
def load_scores() -> pd.DataFrame:
    """Carga score_modelos.csv."""
    path = CLEAN_DIR / "score_modelos.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "propulsion" in df.columns:
        df["propulsion"] = df["propulsion"].fillna("indeterminado").str.lower()
    return df


@st.cache_data(show_spinner="Cargando sensibilidad del ranking…")
def load_sensibilidad() -> pd.DataFrame:
    """Carga sensibilidad_pesos.csv (largo: modelo × escenario).

    Lo genera `codes/sensibilidad.py`. Si no existe, las páginas muestran un
    aviso en vez de fallar: el reporte sigue funcionando sin el análisis.
    """
    path = CLEAN_DIR / "sensibilidad_pesos.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner="Cargando estabilidad del ranking…")
def load_sensibilidad_resumen() -> pd.DataFrame:
    """Carga sensibilidad_resumen.csv (uno por modelo: estabilidad del rank)."""
    path = CLEAN_DIR / "sensibilidad_resumen.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def top_por_anuncios(df_scores: pd.DataFrame):
    """Fila con más anuncios (desempate: score y nombre).

    No usa `.iloc[0]`: el orden del CSV no forma parte del contrato. Devuelve
    una Serie o None si no hay datos.
    """
    if df_scores.empty or "n_anuncios_total" not in df_scores.columns:
        return None
    return df_scores.sort_values(
        ["n_anuncios_total", "score", "modelo_norm"],
        ascending=[False, False, True], kind="mergesort",
    ).iloc[0]


def solo_precio_comparable(df: pd.DataFrame) -> pd.DataFrame:
    """Quita los modelos sin `precio_usd` (catálogo en EUR).

    Su score se calcula sin precio, así que no se pueden comparar con los que
    sí tienen precio USD. El reporte los muestra aparte.
    """
    if df.empty or "precio_comparable" not in df.columns:
        return df
    return df[df["precio_comparable"].fillna(False).astype(bool)]


def sin_precio_comparable(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve solo los modelos sin `precio_usd` (para mostrarlos aparte)."""
    if df.empty or "precio_comparable" not in df.columns:
        return df.head(0)
    return df[~df["precio_comparable"].fillna(False).astype(bool)]


def top_por_score(df_scores: pd.DataFrame, propulsion: str,
                  solo_precio: bool = True):
    """Fila con mejor score DENTRO de una propulsión.

    El score se normaliza min-max dentro de cada grupo, así que NO es
    comparable entre propulsiones. `propulsion` es obligatoria a propósito:
    evita que una página vuelva a mostrar un "mejor global" que mezcle un
    híbrido con un eléctrico.

    Por defecto excluye los modelos sin `precio_usd`: su score no incluye el
    criterio de precio (peso 0.40) y no es comparable con el resto.
    """
    if df_scores.empty or "score" not in df_scores.columns:
        return None
    sub = filter_by_propulsion(df_scores, propulsion)
    if solo_precio:
        sub = solo_precio_comparable(sub)
    if sub.empty:
        return None
    return sub.sort_values(
        ["score", "n_anuncios_total", "modelo_norm"],
        ascending=[False, False, True], kind="mergesort",
    ).iloc[0]


def frontera_pareto(df: pd.DataFrame, x_col: str, y_col: str) -> pd.DataFrame:
    """Filas no dominadas en el plano (x, y), ordenadas por x.

    Un punto está dominado si otro es al menos igual de bueno en ambos ejes y
    estrictamente mejor en uno. La dirección se decide por el nombre de la
    columna: `precio_usd` es "menor = mejor"; autonomía y carga son
    "mayor = mejor". La implementación anterior recorría los puntos ordenados
    por X y solo comparaba Y, lo que devolvía puntos dominados cuando X no era
    el precio (p. ej. autonomía vs carga).
    """
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        return df.head(0)
    sub = df.dropna(subset=[x_col, y_col]).copy()
    if sub.empty:
        return sub

    x = pd.to_numeric(sub[x_col], errors="coerce").to_numpy(dtype=float)
    y = pd.to_numeric(sub[y_col], errors="coerce").to_numpy(dtype=float)
    # Orientar los dos ejes para que "mayor" sea siempre mejor.
    tx = -x if x_col == "precio_usd" else x
    ty = -y if y_col == "precio_usd" else y

    no_dominados = []
    for i in range(len(sub)):
        dominado = any(
            j != i
            and tx[j] >= tx[i] and ty[j] >= ty[i]
            and (tx[j] > tx[i] or ty[j] > ty[i])
            for j in range(len(sub))
        )
        if not dominado:
            no_dominados.append(i)

    return sub.iloc[no_dominados].sort_values(x_col, kind="mergesort")


def top_por_propulsion(df_scores: pd.DataFrame, prop: str, n: int = 3,
                       solo_precio: bool = True) -> pd.DataFrame:
    """Top N de una propulsión, por `rank_propulsion` (o score si falta).

    Es explícito: no depende de que `analisis.py` haya dejado el CSV ordenado.
    Con `solo_precio=True` (default) excluye los modelos sin precio USD.
    """
    if df_scores.empty or "propulsion" not in df_scores.columns:
        return df_scores.head(0)
    sub = df_scores[df_scores["propulsion"] == prop]
    if solo_precio:
        sub = solo_precio_comparable(sub)
    if sub.empty:
        return sub
    if "rank_propulsion" in sub.columns:
        return sub.sort_values("rank_propulsion", kind="mergesort").head(n)
    return sub.sort_values(
        ["score", "modelo_norm"], ascending=[False, True], kind="mergesort",
    ).head(n)


def texto_sensibilidad_electrico(df_sens: pd.DataFrame,
                                 df_sens_res: pd.DataFrame) -> str:
    """Frase de robustez del podio eléctrico, calculada desde los CSV.

    Se usa en Resumen y Limitaciones para que la portada no parezca más firme
    que el análisis. Si faltan los CSV, devuelve un aviso, no un número.
    """
    fallback = (
        "Pendiente: ejecutar `codes/sensibilidad.py`. El score depende de pesos "
        "fijos; su estabilidad se mide aparte."
    )
    if df_sens.empty or df_sens_res.empty:
        return fallback
    requeridas_res = {"propulsion", "rank_base", "top3_pct", "modelo_norm"}
    requeridas_pesos = {"propulsion", "rank", "escenario", "modelo_norm"}
    if not requeridas_res <= set(df_sens_res.columns):
        return fallback
    if not requeridas_pesos <= set(df_sens.columns):
        return fallback

    prop = "electrico"
    top3 = df_sens_res[df_sens_res["propulsion"] == prop].nsmallest(3, "rank_base")
    if len(top3) != 3:
        return fallback

    pcts = top3["top3_pct"].tolist()
    nombres = top3["modelo_norm"].tolist()
    sens_prop = df_sens[df_sens["propulsion"] == prop]
    alt = sens_prop[sens_prop["escenario"] != "base"]
    cambios = alt[alt["rank"] == 1].set_index("escenario")["modelo_norm"]
    omision = cambios[cambios.index.str.startswith("sin_")]
    imputado = cambios.get("imputado_05")
    otros = omision[omision != nombres[0]]
    nombres_esc = {
        "sin_precio_usd": "sin precio",
        "sin_autonomia_km": "sin autonomía",
        "sin_carga_kg": "sin carga",
        "sin_legalidad": "sin legalidad",
        "sin_repuestos": "sin repuestos",
    }
    detalle = "; ".join(
        f"al quitar {nombres_esc.get(e, e).replace('sin ', '')} → {m}"
        for e, m in otros.items()
    )

    # ¿Cuántos escenarios cambian el trío completo, no solo el 1º?
    base_top3 = set(nombres)
    cambia_top3 = [
        esc for esc, sub in alt.groupby("escenario", sort=True)
        if set(sub.nsmallest(3, "rank")["modelo_norm"]) != base_top3
    ]
    n_esc = len(omision)
    if len(otros):
        txt_1 = (f"el 1º cambia en {len(otros)} de {n_esc} escenarios de "
                 f"omisión ({detalle})")
    else:
        txt_1 = f"el 1º se mantiene en los {n_esc} escenarios de omisión"

    if imputado is None:
        txt_imp = ""
    elif imputado == nombres[0]:
        txt_imp = " La imputación 0.5 no cambia el 1º."
    else:
        txt_imp = f" Con imputación 0.5 el 1º sería {imputado}."

    if cambia_top3:
        txt_3 = (f"el trío del podio cambia en {len(cambia_top3)} de "
                 f"{len(alt)} escenarios alternativos")
    else:
        txt_3 = (f"el trío del podio se mantiene en los {len(alt)} "
                 "escenarios alternativos")

    return (
        f"Con perturbaciones de ±0.05 en los pesos, cada modelo del top-3 "
        f"eléctrico cae en el top-3 en {pcts[0]:.0f}%, {pcts[1]:.0f}% y "
        f"{pcts[2]:.0f}% de los casos; {txt_1}.{txt_imp} "
        f"Además, {txt_3}. El orden exacto —y a veces el podio— depende de "
        "los pesos."
    )


@st.cache_data(show_spinner="Cargando comparación campo vs online…")
def load_comparacion() -> pd.DataFrame:
    """Carga comparacion_campo_online.csv."""
    path = CLEAN_DIR / "comparacion_campo_online.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner="Cargando resumen de campo (marcas)…")
def load_campo_resumen() -> pd.DataFrame:
    """Carga campo_resumen.csv (marca: cuota, IC95, uso dominante, score)."""
    path = CLEAN_DIR / "campo_resumen.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner="Cargando resumen de campo (usos)…")
def load_campo_uso() -> pd.DataFrame:
    """Carga campo_uso.csv (uso: cuota, IC95, marcas)."""
    path = CLEAN_DIR / "campo_uso.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner="Cargando frecuencia por municipio…")
def load_frecuencia_municipio() -> pd.DataFrame:
    """Carga frecuencia_por_municipio.csv."""
    path = CLEAN_DIR / "frecuencia_por_municipio.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def get_kpis(df_online: pd.DataFrame) -> dict:
    """Calcula KPIs principales del dataset online."""
    if df_online.empty:
        return {}
    kpis = {
        "total_anuncios": len(df_online),
        "total_modelos": df_online["modelo_norm"].nunique(),
        "propulsion_dist": df_online["propulsion"].value_counts().to_dict(),
        "fuente_dist": df_online["fuente"].value_counts().to_dict() if "fuente" in df_online.columns else {},
        "precio_median": df_online["precio_usd"].median() if "precio_usd" in df_online.columns else None,
        "autonomia_median": df_online["autonomia_km"].median() if "autonomia_km" in df_online.columns else None,
        "carga_median": df_online["carga_kg"].median() if "carga_kg" in df_online.columns else None,
    }
    return kpis


def filter_by_propulsion(df: pd.DataFrame, prop: str) -> pd.DataFrame:
    """Filtra por propulsión (case-insensitive)."""
    if df.empty or "propulsion" not in df.columns:
        return df
    return df[df["propulsion"].str.lower() == prop.lower()]


def get_top_models(df_scores: pd.DataFrame, prop: str, n: int = 10,
                   solo_precio: bool = True) -> pd.DataFrame:
    """Top N modelos por score para una propulsión.

    Usa `rank_propulsion` cuando existe; si no, ordena por score. No confía en
    el orden en que venga el CSV. Por defecto excluye los modelos sin precio
    USD, que se muestran aparte.
    """
    return top_por_propulsion(df_scores, prop, n, solo_precio=solo_precio)
