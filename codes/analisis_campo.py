#!/usr/bin/env python3
"""
Análisis del trabajo de campo (inventario municipal).

Qué hace
--------
Convierte `Data/registro_ubicaciones.csv` en dos tablas listas para el reporte:

  Data/clean_data/campo_resumen.csv
      Una fila por MARCA observada en calle: cuántas veces se vio, su cuota
      dentro de la muestra, el intervalo de confianza al 95% (Wilson), el uso
      dominante y el cruce con la oferta online y con el score.

  Data/clean_data/campo_uso.csv
      Una fila por uso (pasajeros / mixto / carga): cuántas observaciones, su
      cuota y las marcas que aparecen en ese uso.

Por qué existe
--------------
1. El campo no distingue modelo (solo marca): la unidad de análisis es la marca.
2. Con n=30 y una muestra de conveniencia, un porcentaje sin intervalo invita a
   sobreinterpretar. El IC de Wilson (apropiado para proporciones con n chico)
   hace visible la incertidumbre: "20% [8-39%]" es más honesto que "20%".
3. La regla del proyecto es que el reporte LEA tablas ya calculadas, no que
   calcule al vuelo en el gráfico. Este script es el único sitio donde se
   calculan estas cifras.

El cruce con el score (opción A: "más común" vs "mejor valorado") se hace aquí
porque necesita las dos fuentes: `score_modelos.csv` (oferta) y el campo.
El campo NO entra al scoring: solo se pone al lado.

Uso:
    python3 codes/analisis_campo.py     # requiere haber corrido analisis.py
"""

import ast
import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from norm_modelo import marca_norm  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
CLEAN_DIR = DATA_DIR / "clean_data"
CAMPO_CSV = DATA_DIR / "registro_ubicaciones.csv"
SCORE_CSV = CLEAN_DIR / "score_modelos.csv"

Z95 = 1.96  # nivel de confianza 95%


def wilson(k: int, n: int, z: float = Z95) -> tuple:
    """Intervalo de confianza de Wilson para una proporción, en porcentaje.

    Se usa Wilson (no la aproximación normal) porque con n pequeño y
    proporciones cerca de 0 los límites normales se salen de [0, 1].
    """
    if n <= 0:
        return 0.0, 0.0
    p = k / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    mitad = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return round(max(0.0, centro - mitad) * 100, 1), round(min(1.0, centro + mitad) * 100, 1)


def cargar_campo() -> pd.DataFrame:
    if not CAMPO_CSV.exists():
        raise SystemExit(f"No existe {CAMPO_CSV}. Ejecuta codes/parse_campo.py.")
    df = pd.read_csv(CAMPO_CSV)
    df["marca_norm"] = marca_norm(df)
    df["propulsion"] = df["propulsion"].fillna("indeterminado").str.lower()
    # Wh por observación (no el producto de medianas) y W numéricos.
    df["bateria_wh"] = df["bateria_v"] * df["bateria_ah"]
    df["motor_w"] = pd.to_numeric(
        df["motor"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    return df


def cargar_online() -> pd.DataFrame:
    """Anuncios online (solo para contar marcas y contrastar la oferta)."""
    frames = []
    for name in ("anuncios_triciclos.jsonl", "anuncios_facebook.jsonl"):
        path = CLEAN_DIR / name
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            frames.append(pd.DataFrame([json.loads(l) for l in f if l.strip()]))
    if not frames:
        return pd.DataFrame(columns=["marca_norm"])
    df = pd.concat(frames, ignore_index=True)
    df["marca_norm"] = marca_norm(df)
    return df


def mejor_por_marca(df_score: pd.DataFrame) -> pd.DataFrame:
    """Por marca, el modelo con mejor score (para el contraste A)."""
    if df_score.empty:
        return pd.DataFrame(columns=["marca_norm", "mejor_modelo", "mejor_score",
                                     "precio_medio", "autonomia_online"])

    filas = []
    for _, row in df_score.iterrows():
        try:
            marcas = ast.literal_eval(str(row.get("marcas", "[]")))
        except (ValueError, SyntaxError):
            marcas = []
        for m in marcas if isinstance(marcas, list) else []:
            filas.append({
                "marca_norm": str(m).upper().strip(),
                "modelo": row.get("modelo_norm"),
                "score": row.get("score"),
                "precio_usd": row.get("precio_usd"),
                "autonomia_km": row.get("autonomia_km"),
            })
    if not filas:
        return pd.DataFrame(columns=["marca_norm", "mejor_modelo", "mejor_score",
                                     "precio_medio", "autonomia_online"])

    base = pd.DataFrame(filas)
    idx = base.groupby("marca_norm")["score"].idxmax()
    top = base.loc[idx].rename(columns={
        "modelo": "mejor_modelo", "score": "mejor_score",
        "precio_usd": "precio_medio", "autonomia_km": "autonomia_online",
    })
    return top.reset_index(drop=True)


def resumen_marca(df: pd.DataFrame, df_online: pd.DataFrame,
                  df_score: pd.DataFrame) -> pd.DataFrame:
    n_total = len(df)
    conteo = (df.dropna(subset=["marca_norm"])
              .groupby("marca_norm").size().reset_index(name="n_campo"))

    extra = (df.dropna(subset=["marca_norm"])
             .groupby("marca_norm")
             .agg(autonomia_med=("autonomia_km", "median"),
                  autonomia_n=("autonomia_km", "count"),
                  bateria_wh_med=("bateria_wh", "median"),
                  motor_w_med=("motor_w", "median"),
                  n_municipios=("municipio", "nunique"),
                  n_electrico=("propulsion", lambda s: int((s == "electrico").sum())))
             .reset_index())

    # Uso dominante dentro de cada marca.
    uso = (df.dropna(subset=["marca_norm"]).groupby(["marca_norm", "uso"]).size()
           .reset_index(name="n"))
    uso_dom = (uso.sort_values(["marca_norm", "n"], ascending=[True, False])
               .drop_duplicates("marca_norm")
               .rename(columns={"uso": "uso_dominante", "n": "n_uso_dominante"}))

    out = (conteo.merge(extra, on="marca_norm", how="left")
                 .merge(uso_dom, on="marca_norm", how="left"))

    # Cuota + IC de Wilson.
    out["pct_campo"] = (out["n_campo"] / n_total * 100).round(1)
    ic = [wilson(int(k), n_total) for k in out["n_campo"]]
    out["ic95_bajo"] = [i[0] for i in ic]
    out["ic95_alto"] = [i[1] for i in ic]
    out["pct_uso_dominante"] = (out["n_uso_dominante"] / out["n_campo"] * 100).round(1)

    # Oferta online (universo distinto: se compara en cuota, no en conteo).
    if not df_online.empty:
        on = (df_online.dropna(subset=["marca_norm"])
              .groupby("marca_norm").size().reset_index(name="n_online"))
        out = out.merge(on, on="marca_norm", how="left")
        n_online = int(on["n_online"].sum())
        out["n_online"] = out["n_online"].fillna(0).astype(int)
        out["pct_online"] = (out["n_online"] / n_online * 100).round(1)
        out["delta_pct"] = (out["pct_campo"] - out["pct_online"]).round(1)
    else:
        out["n_online"], out["pct_online"], out["delta_pct"] = 0, 0.0, 0.0

    # Cruce con el score (opción A): "más común" vs "mejor valorado".
    out = out.merge(mejor_por_marca(df_score), on="marca_norm", how="left")

    out["rank_campo"] = out["n_campo"].rank(method="min", ascending=False).astype(int)
    if out["mejor_score"].notna().any():
        out["rank_score"] = out["mejor_score"].rank(method="min", ascending=False)
        out.loc[out["mejor_score"].isna(), "rank_score"] = pd.NA
        out["rank_score"] = out["rank_score"].astype("Int64")
    else:
        out["rank_score"] = pd.NA

    cols = ["marca_norm", "n_campo", "pct_campo", "ic95_bajo", "ic95_alto",
            "n_municipios", "n_electrico", "uso_dominante", "pct_uso_dominante",
            "autonomia_med", "autonomia_n", "bateria_wh_med", "motor_w_med",
            "n_online", "pct_online", "delta_pct",
            "mejor_modelo", "mejor_score", "precio_medio", "autonomia_online",
            "rank_campo", "rank_score"]
    return (out[cols].sort_values(["n_campo", "n_online"], ascending=False)
            .reset_index(drop=True))


def resumen_uso(df: pd.DataFrame) -> pd.DataFrame:
    n_total = len(df)
    out = (df.groupby("uso").size().reset_index(name="n"))
    out["pct"] = (out["n"] / n_total * 100).round(1)
    ic = [wilson(int(k), n_total) for k in out["n"]]
    out["ic95_bajo"] = [i[0] for i in ic]
    out["ic95_alto"] = [i[1] for i in ic]

    marcas = (df.groupby(["uso", "marca_norm"]).size()
              .reset_index(name="k").sort_values(["uso", "k"], ascending=[True, False]))
    out["marcas"] = ["; ".join(f"{r.marca_norm} ({r.k})" for r in
                              marcas[marcas["uso"] == u].head(3).itertuples())
                     for u in out["uso"]]

    extra = (df.groupby("uso")
             .agg(autonomia_med=("autonomia_km", "median"),
                  n_municipios=("municipio", "nunique"),
                  originales=("uso_original", lambda s: "/".join(sorted(set(s.dropna())))))
             .reset_index())
    out = out.merge(extra, on="uso", how="left")
    return out.sort_values("n", ascending=False).reset_index(drop=True)


def main():
    df = cargar_campo()
    df_online = cargar_online()
    df_score = pd.read_csv(SCORE_CSV) if SCORE_CSV.exists() else pd.DataFrame()
    if df_score.empty:
        print(f"  AVISO: no existe {SCORE_CSV.name}; se omite el cruce con el score")

    print("=== CAMPO ===")
    print(f"  {len(df)} observaciones | {df['municipio'].nunique()} municipios | "
          f"{df['marca_norm'].nunique()} marcas")
    print(f"  Propulsión: {df['propulsion'].value_counts().to_dict()}")
    print(f"  Uso: {df['uso'].value_counts().to_dict()}")

    resumen = resumen_marca(df, df_online, df_score)
    usos = resumen_uso(df)

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    resumen.to_csv(CLEAN_DIR / "campo_resumen.csv", index=False)
    usos.to_csv(CLEAN_DIR / "campo_uso.csv", index=False)

    print("\n--- Por marca ---")
    print(resumen[["marca_norm", "n_campo", "pct_campo", "ic95_bajo", "ic95_alto",
                   "pct_online", "mejor_modelo", "mejor_score"]].to_string(index=False))
    print("\n--- Por uso ---")
    print(usos[["uso", "n", "pct", "marcas"]].to_string(index=False))
    print("\n-> Guardado: clean_data/campo_resumen.csv")
    print("-> Guardado: clean_data/campo_uso.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
