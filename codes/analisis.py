#!/usr/bin/env python3
"""
Análisis combinado: datos de campo + datos online.
Calcula score de "mejor opción" con pesos predefinidos.
Maneja triciclos eléctricos, híbridos y de combustión.

Estructura del repo (decisión del usuario, ajuste 2026-10-11):
  codes/ -> scripts    Data/ -> datos procesados y de campo
  Data/raw_data/ -> datos crudos (entrada del análisis)

Regla de vigencia (decisión del usuario, 2026-10-11 — "oferta viva manda"):
  - Una oferta es VIGENTE si no tiene fecha de publicación (catálogo actual) o
    si su fecha cae dentro de VENTANA_VIGENCIA. Las publicaciones de canal fuera
    de la ventana son históricas y NO puntúan cuando el modelo tiene una oferta
    vigente. Evita mezclar un precio deslistado de 2024 con el de 2026.
  - Un producto marcado condicion="agotado" (catálogo islagrande) NO es oferta
    viva aunque no tenga fecha.
  - Si un modelo solo existe en publicaciones históricas (p.ej. VEDCA C600/C400A
    solo en el canal), se conserva con oferta_viva=False.

Variantes (decisión del usuario, 2026-10-11): dos triciclos con el mismo número
de modelo pero distinta química de batería (p.ej. VEDCA C400 LiFePO4 vs GelPb)
son modelos distintos: el identificador de agrupación incluye la química.

Identidad del producto (decisión del usuario, 2026-10-19):
  - `modelo` es el NOMBRE PROPIO del producto, ya normalizado en el origen por
    codes/norm_modelo.py (tabla curada Data/modelos_canonicos.json + regla).
  - Si `modelo` es null (el producto no tiene nombre de modelo, solo marca),
    la IDENTIDAD es la MARCA. Antes esto producía un grupo fantasma "NONE"
    que además encabezaba el ranking.
  - La identidad va SIEMPRE acompañada de la propulsión: dos productos que
    comparten nombre pero no propulsión (p.ej. el STAR eléctrico de Facebook y
    el STAR híbrido de elyerromenu) NUNCA se fusionan.
  - La normalización min-max es intra-propulsión: no se comparan scores entre
    propulsiones distintas.

Datos de campo (2026-10-31):
  - La hoja de captura NO distingue modelo: solo marca. El análisis de campo
    (cuotas, IC, uso, cruce con el score) vive en codes/analisis_campo.py ->
    clean_data/campo_resumen.csv + campo_uso.csv.
  - Aquí solo se mantiene la comparación por IDENTIDAD (campo vs anuncios),
    que queda casi vacía por diseño: es la prueba de que no se puede comparar
    por modelo.
  - Al campo NO se le aplican los alias de modelo (ONEBOT -> "ONEBOT CLASIC
    2026"): inventaría un modelo que el observador no leyó.
  - El campo NO entra al scoring: mide circulación real, no oferta.

Uso:
    python3 codes/analisis.py   # lee Data/clean_data/*.jsonl; escribe en clean_data/
"""

import json
import ast
import numpy as np
import pandas as pd
from pathlib import Path

# Identidad del producto y tabla de alias (compartidas con el reporte).
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from norm_modelo import ALIAS_MODELOS, aplicar_alias, identidad  # noqa: E402


# ==================== PESOS APROBATOS ====================
# Nota: "autonomia_km" solo se usa si viene en la fuente. NO se estima para
# gasolina (regla del proyecto: no inventar datos). Los criterios ausentes se
# imputan como 0.5 neutro (decisión del usuario, 2026-10-07) y la cobertura
# real de cada score se reporta en la columna n_criterios.

PESOS = {
    "precio_usd": 0.40,        # menor es mejor (invertir)
    "autonomia_km": 0.25,      # mayor es mejor
    "carga_kg": 0.20,          # mayor es mejor
    "legalidad": 0.10,         # binario: 1 si menciona legalización, 0 si no
    "repuestos": 0.05,         # proxy: 1 si modelo aparece en >1 fuente, 0 si no
}

# Ventana de vigencia de las ofertas (decisión del usuario, 2026-10-11).
# Las publicaciones con fecha anterior a esta se consideran históricas.
VENTANA_VIGENCIA = "2026-01-01"

# Convención de carpetas (ajustada 2026-10-14):
#   codes/ -> scripts
#   Data/raw_data/ -> crudos inmutables
#   Data/clean_data/ -> limpios listos para análisis (entrada de analisis.py)
DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
CLEAN_DIR = DATA_DIR / "clean_data"

ONLINE_FIELDS = [
    "modelo", "marca", "propulsion", "motor_w", "motor_cc",
    "bateria_v", "bateria_ah", "bateria_wh", "bateria_quimica",
    "autonomia_km", "carga_kg", "precio_usd", "precio_desde",
    "precio_valor", "moneda",
    "ano", "condicion", "legalizacion", "vendedor_tipo",
    "municipio_anuncio", "url", "fecha_captura", "fecha_anuncio", "fuente",
]


def load_online(jsonl_path: str) -> pd.DataFrame:
    """Carga JSONL y normaliza."""
    records = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    if not records:
        return pd.DataFrame(columns=ONLINE_FIELDS)

    df = pd.DataFrame(records)

    for col in ONLINE_FIELDS:
        if col not in df.columns:
            df[col] = None

    # Normalizar la identidad del producto (decisión del usuario, 2026-10-19).
    # La regla vive en codes/norm_modelo.py (compartida con el reporte):
    #   modelo -> si no hay, la marca; + química en eléctricos; + alias.
    # Antes se usaba `modelo.astype(str)`, que convertía los null en "None" y
    # creaba un grupo fantasma que además encabezaba el ranking.
    df["modelo_norm"] = identidad(df)
    sin_id = df["modelo_norm"].eq("SIN IDENTIFICAR")
    if sin_id.any():
        fuentes = sorted(df.loc[sin_id, "fuente"].dropna().unique())
        print(f"  AVISO: {int(sin_id.sum())} registros sin modelo ni marca "
              f"(fuentes: {fuentes}). Se identifican como 'SIN IDENTIFICAR'.")

    # Alias de modelos para fusión entre fuentes (scraper + facebook + empresas)
    # La tabla vive en codes/norm_modelo.py (compartida con el reporte).
    MODELO_ALIAS = ALIAS_MODELOS

    def apply_alias(x: str) -> str:
        return MODELO_ALIAS.get(x, x)

    df["modelo_norm"] = df["modelo_norm"].apply(apply_alias)

    # Propulsión: normalizar valores
    df["propulsion"] = df["propulsion"].fillna("indeterminado").str.lower()

    # Vigencia de la oferta (decisión del usuario, 2026-10-11): sin fecha de
    # publicación = catálogo vigente; con fecha, vigente solo si cae dentro de
    # la ventana. Las publicaciones de canal antiguas (2024-2025) quedan fuera.
    df["fecha_anuncio_dt"] = pd.to_datetime(df.get("fecha_anuncio"), utc=True, errors="coerce")
    # Un producto agotado no es oferta viva aunque no tenga fecha (decisión del
    # usuario 2026-10-11: islagrande publica todo su catálogo como agotado).
    df["agotado"] = df["condicion"].astype(str).str.lower().str.strip().eq("agotado")
    df["es_viva"] = (
        df["fecha_anuncio_dt"].isna()
        | (df["fecha_anuncio_dt"] >= pd.Timestamp(VENTANA_VIGENCIA, tz="UTC"))
    ) & ~df["agotado"]

    # Batería Wh
    df["bateria_wh"] = df["bateria_v"] * df["bateria_ah"]

    # NOTA: NO se estima la autonomía de los triciclos de gasolina.
    # Una fórmula tipo "cc/10*3*12" inventaría datos no verificables, lo cual
    # está prohibido en este proyecto. Los NaN se manejan en score_modelos()
    # re-pesando los criterios disponibles.

    # Legalidad binaria
    df["legalidad_bin"] = df["legalizacion"].notna().astype(int)

    # Repuestos proxy: se calcula DESPUÉS de unir todos los ficheros (en
    # main), porque "aparece en más de una fuente" solo tiene sentido con
    # el dataset completo: el scraper y Facebook son fuentes distintas.

    return df


def calcular_repuestos_proxy(df_online: pd.DataFrame,
                             df_empresas: pd.DataFrame | None = None) -> pd.DataFrame:
    """Marca los modelos que aparecen en más de una fuente (proxy de repuestos).

    La identidad incluye la propulsión (decisión del usuario, 2026-10-19): el
    STAR eléctrico y el STAR híbrido son productos distintos y no cuentan como
    el mismo modelo.

    `df_empresas` (decisión del usuario, 2026-10-31): los catálogos de empresas
    suman fuentes al proxy ('se vende en tienda, no solo en clasificados'),
    pero NO entran al score ni a los precios del ranking: ver
    `integrar_empresas()`, que solo añade contexto.
    """
    if df_online.empty:
        return df_online
    base = df_online
    if df_empresas is not None and not df_empresas.empty:
        base = pd.concat([df_online, df_empresas], ignore_index=True)
    fuente_por_modelo = base.groupby(["modelo_norm", "propulsion"])["fuente"].nunique()
    df_online["repuestos_proxy"] = [
        int(fuente_por_modelo.get((m, p), 0) > 1)
        for m, p in zip(df_online["modelo_norm"], df_online["propulsion"])
    ]
    return df_online


def load_empresas_online() -> pd.DataFrame:
    """Fichas de catálogos de empresas, normalizadas como los anuncios.

    Solo se usan como fuente adicional del proxy de repuestos y como contexto
    en `integrar_empresas()`. El score se sigue calculando sin ellas.
    """
    empresas_dir = DATA_DIR / "empresas"
    if not empresas_dir.exists():
        return pd.DataFrame()
    frames = []
    for p in sorted(empresas_dir.glob("*.jsonl")):
        f = CLEAN_DIR / p.name
        if f.exists():
            frames.append(load_online(str(f)))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _marcas_lista(valor) -> set:
    """`marcas` viaja como texto de lista ("['ONEBOT']"); tolera nulos."""
    if isinstance(valor, (list, tuple, set)):
        return {str(v).strip().upper() for v in valor if v}
    if not isinstance(valor, str) or not valor.strip():
        return set()
    try:
        parsed = ast.literal_eval(valor)
    except (ValueError, SyntaxError):
        parsed = [valor]
    if isinstance(parsed, str):
        parsed = [parsed]
    return {str(v).strip().upper() for v in parsed if v}


def integrar_empresas(df_score: pd.DataFrame,
                      df_empresas: pd.DataFrame) -> pd.DataFrame:
    """Añade contexto de catálogo al ranking SIN tocar el score.

    Columnas nuevas (nivel MODELO):
      - `n_empresas`: en cuántos catálogos de empresa aparece el modelo.
      - `precio_empresa_med`: precio mediano en catálogo (USD).
      - `en_catalogo`: True si aparece en al menos un catálogo.

    Columnas nuevas (nivel MARCA):
      - `marca_en_catalogo`: True si la marca del anuncio se vende en algún
        catálogo de empresa (hoy solo ONEBOT cruza).
      - `n_empresas_marca`: en cuántos catálogos aparece esa marca.

    Aclaración: las fichas de catálogo y los clasificados **no comparten
    modelos** hoy (identidad modelo+propulsión), así que el contexto de modelo
    sale vacío; el de marca sí aporta. No se fuerza la coincidencia por marca
    para no inventar equivalencias de producto.

    No se mezclan universos: el score y `precio_usd` siguen saliendo solo de
    anuncios; el precio de tienda se muestra aparte para no comparar peras con
    manzanas (un clasificado no incluye envío ni garantía de tienda).
    """
    if df_score.empty:
        return df_score
    if df_empresas is None or df_empresas.empty:
        df_score["n_empresas"] = 0
        df_score["precio_empresa_med"] = pd.NA
        df_score["en_catalogo"] = False
        df_score["marca_en_catalogo"] = False
        df_score["n_empresas_marca"] = 0
        return df_score

    agg = (df_empresas.dropna(subset=["modelo_norm"])
           .groupby(["modelo_norm", "propulsion"])
           .agg(n_empresas=("fuente", "nunique"),
                precio_empresa_med=("precio_usd", "median"))
           .reset_index())
    out = df_score.merge(agg, on=["modelo_norm", "propulsion"], how="left")
    out["n_empresas"] = out["n_empresas"].fillna(0).astype(int)
    out["en_catalogo"] = out["n_empresas"] > 0

    marca_agg = (df_empresas.dropna(subset=["marca"])
                 .assign(marca=lambda d: d["marca"].astype(str).str.strip().str.upper())
                 .groupby("marca")
                 .agg(n_empresas_marca=("fuente", "nunique"))
                 .reset_index())
    cat_marcas = dict(zip(marca_agg["marca"], marca_agg["n_empresas_marca"]))
    out["n_empresas_marca"] = [max((cat_marcas.get(m, 0)
                                    for m in _marcas_lista(v)), default=0)
                               for v in out["marcas"]]
    out["marca_en_catalogo"] = out["n_empresas_marca"] > 0
    return out


def load_campo(csv_path: str) -> pd.DataFrame:
    """Carga CSV de inventario municipal (salida de codes/parse_campo.py)."""
    if not Path(csv_path).exists():
        return pd.DataFrame(columns=["obs_id", "fecha", "municipio", "tipo", "uso",
                                      "uso_original", "propulsion", "modelo", "marca",
                                      "motor", "bateria_v", "bateria_ah", "autonomia_km",
                                      "con_paneles", "estado", "observador", "notas"])
    df = pd.read_csv(csv_path)
    if "propulsion" in df.columns:
        df["propulsion"] = df["propulsion"].fillna("indeterminado").str.lower()
    # Misma regla de identidad que en los datos online (decisión del usuario,
    # 2026-10-19): si no hay nombre de modelo, la identidad es la marca.
    # `con_alias=False`: en la calle solo se ve la marca, así que aplicar los
    # alias de MODELO (ONEBOT -> "ONEBOT CLASIC 2026") inventaría un modelo
    # que el observador no pudo leer. La marca ya viene normalizada en origen.
    df["modelo_norm"] = identidad(df, con_alias=False)
    # El nivel MARCA (cuotas, IC, uso) lo calcula codes/analisis_campo.py.
    return df


def score_modelos(df_online: pd.DataFrame) -> pd.DataFrame:
    """Calcula score ponderado por modelo (agregado), separado por propulsión."""
    if df_online.empty:
        return pd.DataFrame()

    # Filtro de vigencia (decisión usuario 2026-10-11: "oferta viva manda").
    # Si el modelo tiene alguna oferta vigente, se descartan sus publicaciones
    # históricas; si solo tiene históricas, se conserva (oferta_viva=False).
    # La comprobación es por (modelo, propulsión): un mismo nombre con otra
    # propulsión es otro producto y no le afecta la vigencia de este.
    if "es_viva" in df_online.columns:
        tiene_viva = df_online.groupby(["modelo_norm", "propulsion"])["es_viva"].transform("any")
        base = df_online[df_online["es_viva"] | ~tiene_viva]
    else:
        base = df_online

    # Agregar por modelo + propulsión (solo ofertas vigentes cuando existan)
    agg = base.groupby(["modelo_norm", "propulsion"]).agg(
        precio_usd=("precio_usd", "median"),
        autonomia_km=("autonomia_km", "median"),
        carga_kg=("carga_kg", "median"),
        legalidad_bin=("legalidad_bin", "max"),
        repuestos_proxy=("repuestos_proxy", "max"),
        n_anuncios=("fuente", "size"),           # ofertas usadas (vigentes)
        motor_w_med=("motor_w", "median"),
        motor_cc_med=("motor_cc", "median"),
        marcas=("marca", lambda x: list(x.dropna().unique())),
        fuentes=("fuente", lambda x: list(x.dropna().unique())),
        precio_valor=("precio_valor", "median"),   # EUR tal cual (no comparable con precio_usd)
        monedas=("moneda", lambda x: list(x.dropna().unique())),
    ).reset_index()

    # Anotar total de anuncios (incl. históricos) y si hay oferta vigente.
    # También por (modelo, propulsión), para no contar anuncios de otro
    # producto que comparta el nombre.
    por_modelo = df_online.groupby(["modelo_norm", "propulsion"])
    claves = list(zip(agg["modelo_norm"], agg["propulsion"]))
    agg["n_anuncios_total"] = [por_modelo.size().get(k, 0) for k in claves]
    if "es_viva" in df_online.columns:
        agg["oferta_viva"] = [bool(por_modelo["es_viva"].any().get(k, False)) for k in claves]
    else:
        agg["oferta_viva"] = True

    # Normalizar cada criterio a 0-1 (min-max) DENTRO de cada grupo de propulsión
    # para comparar eléctricos con eléctricos y gasolina con gasolina
    agg["precio_usd_norm"] = 0.5
    agg["autonomia_km_norm"] = 0.5
    agg["carga_kg_norm"] = 0.5

    for prop in agg["propulsion"].unique():
        mask = agg["propulsion"] == prop
        sub = agg[mask]
        for col in ["precio_usd", "autonomia_km", "carga_kg"]:
            if sub[col].notna().any():
                mn, mx = sub[col].min(), sub[col].max()
                if mx > mn:
                    if col == "precio_usd":
                        agg.loc[mask, f"{col}_norm"] = 1 - (sub[col] - mn) / (mx - mn)
                    else:
                        agg.loc[mask, f"{col}_norm"] = (sub[col] - mn) / (mx - mn)
                else:
                    agg.loc[mask, f"{col}_norm"] = 0.5

    agg["legalidad_norm"] = agg["legalidad_bin"]
    agg["repuestos_norm"] = agg["repuestos_proxy"]

    # Score ponderado con imputación neutra 0.5 (decisión del usuario
    # 2026-10-07, ver PESOS): un criterio ausente vale "medio", ni castiga ni
    # beneficia, y todos los scores quedan comparables entre sí.
    # La alternativa (re-ponderar solo con los criterios presentes) NO se
    # aplica aquí: se evalúa como análisis de robustez en codes/sensibilidad.py.
    # Cobertura real: con cuántos criterios SÍ tiene dato cada modelo.
    # Se calcula sobre los datos CRUDOS, no sobre las normas (que ya van
    # imputadas a 0.5 y ocultarían la ausencia).
    raw_cols = ["precio_usd", "autonomia_km", "carga_kg", "legalidad_bin", "repuestos_proxy"]
    agg["n_criterios"] = agg[raw_cols].apply(pd.to_numeric, errors="coerce").notna().sum(axis=1)

    cols = ["precio_usd_norm", "autonomia_km_norm", "carga_kg_norm",
            "legalidad_norm", "repuestos_norm"]
    w = [PESOS["precio_usd"], PESOS["autonomia_km"], PESOS["carga_kg"],
         PESOS["legalidad"], PESOS["repuestos"]]

    M = agg[cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    W = np.array(w, dtype=float)

    # Imputación neutra 0.5 (decisión del usuario 2026-10-07): un criterio
    # ausente vale "medio", ni castiga ni beneficia, y todos los scores quedan
    # comparables entre sí. n_criterios expone la fiabilidad de cada score.
    M = np.where(np.isnan(M), 0.5, M)
    agg["score"] = M @ W

    agg = agg.sort_values(["propulsion", "score"], ascending=[True, False]).reset_index(drop=True)
    # Rango dentro de cada propulsión: el reporte selecciona por rango, no por
    # posición del CSV. Así un cambio de orden no altera el podio mostrado.
    agg["rank_propulsion"] = (
        agg.groupby("propulsion")["score"]
        .rank(method="first", ascending=False)
        .astype(int)
    )
    return agg


def comparar_campo_online(df_campo: pd.DataFrame, df_online: pd.DataFrame) -> pd.DataFrame:
    """Compara frecuencias: qué se ve en la calle vs qué se anuncia.

    La identidad incluye la propulsión (decisión del usuario, 2026-10-19): un
    mismo nombre con propulsiones distintas son productos distintos.
    """
    if df_campo.empty or df_online.empty:
        return pd.DataFrame()

    campo_freq = (df_campo.groupby(["modelo_norm", "propulsion"]).size()
                  .reset_index(name="freq_campo"))
    online_freq = (df_online.groupby(["modelo_norm", "propulsion"]).size()
                   .reset_index(name="freq_online"))

    comp = pd.merge(campo_freq, online_freq, on=["modelo_norm", "propulsion"],
                    how="outer").fillna(0)
    comp["freq_campo"] = comp["freq_campo"].astype(int)
    comp["freq_online"] = comp["freq_online"].astype(int)
    comp["total"] = comp["freq_campo"] + comp["freq_online"]
    comp = comp.sort_values("total", ascending=False).reset_index(drop=True)

    return comp


def main():
    # Cargar TODOS los JSONL de clean_data (anuncios + facebook + empresas)
    online_files = [
        CLEAN_DIR / "anuncios_triciclos.jsonl",
        CLEAN_DIR / "anuncios_facebook.jsonl",
    ]
    campo_path = DATA_DIR / "registro_ubicaciones.csv"

    print("=== CARGANDO DATOS ===")
    dfs = []
    for p in online_files:
        if p.exists():
            df = load_online(str(p))
            dfs.append(df)
            print(f"  {p.name}: {len(df)} anuncios, {df['modelo_norm'].nunique()} modelos únicos")
        else:
            print(f"  {p.name}: NO ENCONTRADO")
    df_online = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    # Empresas: fuente extra del proxy y contexto del ranking (no al score).
    df_empresas = load_empresas_online()
    if not df_empresas.empty:
        print(f"  Empresas (proxy/contexto): {len(df_empresas)} fichas, "
              f"{df_empresas['fuente'].nunique()} catálogos")
    # El proxy de repuestos necesita el dataset completo (scraper + Facebook +
    # catálogos de empresa).
    if not df_online.empty:
        df_online = calcular_repuestos_proxy(df_online, df_empresas)
    df_campo = load_campo(str(campo_path))

    print(f"Online: {len(df_online)} anuncios, {df_online['modelo_norm'].nunique()} modelos únicos")
    if not df_online.empty:
        print(f"  Propulsión: {df_online['propulsion'].value_counts().to_dict()}")
    print(f"Campo:  {len(df_campo)} observaciones, {df_campo['marca'].nunique()} marcas únicas")
    if not df_campo.empty and "propulsion" in df_campo.columns:
        print(f"  Propulsión: {df_campo['propulsion'].value_counts().to_dict()}")

    # 1. Score de mejor opción (por propulsión)
    print("\n=== SCORE MEJOR OPCIÓN (POR PROPULSIÓN) ===")
    df_score = score_modelos(df_online)
    # Contexto de catálogo (no cambia el score): cuántas empresas lo venden y
    # a qué precio. Las empresas NO entran al cálculo del ranking.
    df_score = integrar_empresas(df_score, df_empresas)
    if not df_score.empty:
        # Mostrar top 10 por propulsión
        for prop in df_score["propulsion"].unique():
            sub = df_score[df_score["propulsion"] == prop].head(10)
            print(f"\n--- {prop.upper()} ---")
            cols = ["modelo_norm", "rank_propulsion", "score", "n_criterios", "precio_usd", "precio_valor", "monedas",
                    "autonomia_km", "carga_kg",
                    "legalidad_bin", "repuestos_proxy", "oferta_viva", "n_anuncios", "n_anuncios_total",
                    "motor_w_med", "motor_cc_med", "n_empresas", "precio_empresa_med",
                    "marca_en_catalogo", "n_empresas_marca"]
            cols = [c for c in cols if c in sub.columns]
            print(sub[cols].to_string(index=False))

        df_score.to_csv(CLEAN_DIR / "score_modelos.csv", index=False)
        print("\n-> Guardado: clean_data/score_modelos.csv")

    # 2. Comparación campo vs online
    print("\n=== COMPARACIÓN CAMPO vs ONLINE ===")
    df_comp = comparar_campo_online(df_campo, df_online)
    if not df_comp.empty:
        print(df_comp.head(20).to_string(index=False))
        df_comp.to_csv(CLEAN_DIR / "comparacion_campo_online.csv", index=False)
        print("\n-> Guardado: clean_data/comparacion_campo_online.csv")

    # 3. Resumen por municipio (campo)
    if not df_campo.empty:
        print("\n=== POR MUNICIPIO (CAMPO) ===")
        muni = df_campo.groupby(["municipio", "modelo_norm", "propulsion"]).size().reset_index(name="count")
        muni = muni.sort_values(["municipio", "count"], ascending=[True, False])
        print(muni.to_string(index=False))
        muni.to_csv(CLEAN_DIR / "frecuencia_por_municipio.csv", index=False)
        print("\n-> Guardado: clean_data/frecuencia_por_municipio.csv")

    # 4. Resumen por tipo/uso
    if not df_campo.empty:
        print("\n=== POR TIPO Y USO (CAMPO) ===")
        tipo_uso = df_campo.groupby(["tipo", "uso", "modelo_norm", "propulsion"]).size().reset_index(name="count")
        tipo_uso = tipo_uso.sort_values(["tipo", "uso", "count"], ascending=[True, True, False])
        print(tipo_uso.to_string(index=False))
        tipo_uso.to_csv(CLEAN_DIR / "frecuencia_por_tipo_uso.csv", index=False)
        print("\n-> Guardado: clean_data/frecuencia_por_tipo_uso.csv")

    # 5. Resumen online por propulsión
    if not df_online.empty:
        print("\n=== ONLINE: ESTADÍSTICAS POR PROPULSIÓN ===")
        for prop in df_online["propulsion"].unique():
            sub = df_online[df_online["propulsion"] == prop]
            print(f"\n{prop.upper()} ({len(sub)} anuncios):")
            print(f"  Precio median: ${sub['precio_usd'].median():.0f}" if sub['precio_usd'].notna().any() else "  Precio: N/A")
            print(f"  Autonomía median: {sub['autonomia_km'].median():.0f} km" if sub['autonomia_km'].notna().any() else "  Autonomía: N/A")
            print(f"  Carga median: {sub['carga_kg'].median():.0f} kg" if sub['carga_kg'].notna().any() else "  Carga: N/A")
            if prop == "electrico":
                print(f"  Motor W median: {sub['motor_w'].median():.0f} W" if sub['motor_w'].notna().any() else "  Motor: N/A")
                print(f"  Batería Wh median: {sub['bateria_wh'].median():.0f} Wh" if sub['bateria_wh'].notna().any() else "  Batería: N/A")
            else:
                print(f"  Motor cc median: {sub['motor_cc'].median():.0f} cc" if sub['motor_cc'].notna().any() else "  Motor cc: N/A")


if __name__ == "__main__":
    main()
