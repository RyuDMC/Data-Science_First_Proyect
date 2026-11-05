#!/usr/bin/env python3
"""
Sensibilidad del ranking a los pesos y a los criterios ausentes.

Por qué existe
--------------
El score es una suma ponderada con pesos decididos a mano (0.40 precio,
0.25 autonomía, 0.20 carga, 0.10 legalidad, 0.05 repuestos) y con imputación
neutra 0.5 para los criterios ausentes. Eso produce UN orden, pero no dice
cuánto depende ese orden de las decisiones metodológicas.

Este script responde tres preguntas, sin tocar el score oficial:

  1. ¿Y si se re-pondera en vez de imputar 0.5?  (la alternativa que el
     comentario viejo de `analisis.py` describía pero no implementaba)
  2. ¿Qué pasa si se quita un criterio entero?  (¿el podio aguanta?)
  3. ¿Cuánto se mueve cada modelo si los pesos varían ±delta?  (perturbación
     aleatoria con semilla fija, reproducible)

Regla del proyecto: esto NO cambia `score_modelos.csv`. Es un análisis de
robustez; el score que se reporta sigue siendo el aprobado (imputación 0.5).
Si la sensibilidad contradice la conclusión, se dice en el reporte, no se
esconde cambiando los pesos.

Salidas
-------
`Data/clean_data/sensibilidad_pesos.csv`   (largo: modelo × escenario)
`Data/clean_data/sensibilidad_resumen.csv` (uno por modelo: estabilidad)

Uso
---
    python3 codes/sensibilidad.py
    python3 codes/sensibilidad.py --n 5000 --delta 0.10
    python3 codes/sensibilidad.py --check     # falla si los CSV no coinciden
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from analisis import PESOS  # noqa: E402  (main() está protegido)

CLEAN_DIR = ROOT / "Data" / "clean_data"
ENTRADA = CLEAN_DIR / "score_modelos.csv"
SALIDA_LARGA = CLEAN_DIR / "sensibilidad_pesos.csv"
SALIDA_RESUMEN = CLEAN_DIR / "sensibilidad_resumen.csv"

# Orden canónico de los criterios: pesos y columnas normalizadas deben ir
# alineados posición a posición.
CRITERIOS = [
    ("precio_usd", "precio_usd_norm"),
    ("autonomia_km", "autonomia_km_norm"),
    ("carga_kg", "carga_kg_norm"),
    ("legalidad", "legalidad_norm"),
    ("repuestos", "repuestos_norm"),
]
COLS_NORM = [norm for _, norm in CRITERIOS]
# Columnas crudas: solo sirven para saber qué criterios están ausentes.
COLS_RAW = ["precio_usd", "autonomia_km", "carga_kg",
            "legalidad_bin", "repuestos_proxy"]

# Semilla fija: la perturbación debe dar el mismo CSV en cada máquina.
SEMILLA = 20261031


def _pesos_base() -> np.ndarray:
    """Pesos en el orden de CRITERIOS (valida que sumen 1)."""
    w = np.array([PESOS[clave] for clave, _ in CRITERIOS], dtype=float)
    if not np.isclose(w.sum(), 1.0):
        sys.exit(f"Los PESOS de analisis.py no suman 1 (suman {w.sum()}).")
    return w


def _ordenar_por_grupo(df: pd.DataFrame, col_score: str) -> pd.DataFrame:
    """Ranking 1..n DENTRO de cada propulsión, con desempate determinista.

    Ordena por score descendente con un sort estable. En empate se conserva el
    orden del CSV, que es el mismo que usa `rank(method="first")` en
    `analisis.py`; así `rank_base` coincide con `rank_propulsion`.
    """
    partes = []
    for _, sub in df.groupby("propulsion", sort=True):
        sub = sub.sort_values(col_score, ascending=False, kind="mergesort").copy()
        sub["rank"] = np.arange(1, len(sub) + 1)
        partes.append(sub)
    return pd.concat(partes, ignore_index=True)


def _escenarios(df: pd.DataFrame, w: np.ndarray):
    """Genera (nombre, score) para cada escenario determinista."""
    M = df[COLS_NORM].to_numpy(dtype=float)
    # Misma imputación que `analisis.py::score_modelos`: un criterio ausente
    # vale 0.5. Sin esto, `M @ w` propaga NaN y el escenario base no reproduce
    # el score oficial (era el bug: 15/38 scores NaN y 26/38 rangos distintos).
    M = np.where(np.isnan(M), 0.5, M)
    raw = df[COLS_RAW].to_numpy(dtype=float)

    # 1. Base: imputación 0.5 (la decisión oficial).
    yield "base", M @ w

    # 2. Alternativa: ignorar el criterio ausente y re-ponderar los presentes.
    #    (legalidad y repuestos nunca faltan, así que el denominador no es 0.)
    w_eff = np.where(np.isnan(raw), 0.0, w)
    yield "reponderado", (M * w_eff).sum(axis=1) / w_eff.sum(axis=1)

    # 3. Omisión de cada criterio: peso 0 y re-normalización.
    for i, (clave, _) in enumerate(CRITERIOS):
        w_sin = w.copy()
        w_sin[i] = 0.0
        yield f"sin_{clave}", M @ (w_sin / w_sin.sum())


def _perturbar(df: pd.DataFrame, w: np.ndarray, n: int, delta: float):
    """Ranking de cada modelo bajo N perturbaciones uniformes de ±delta.

    Devuelve un DataFrame con top3_pct, top1_pct y percentiles del rank.
    Se perturba cada peso por separado y se re-normaliza para que sumen 1;
    los negativos se recortan a 0.
    """
    M = df[COLS_NORM].to_numpy(dtype=float)
    M = np.where(np.isnan(M), 0.5, M)  # misma imputación que el score oficial
    nombres = df["modelo_norm"].to_numpy()
    props = df["propulsion"].to_numpy()
    grupos = {p: np.where(props == p)[0] for p in np.unique(props)}

    rng = np.random.default_rng(SEMILLA)
    ranks = np.zeros((n, len(df)), dtype=np.int16)

    for d in range(n):
        w_d = np.clip(w + rng.uniform(-delta, delta, len(w)), 0.0, None)
        w_d = w_d / w_d.sum()
        score = M @ w_d
        for idx in grupos.values():
            # lexsort: última clave es la primaria → -score, luego nombre.
            orden = idx[np.lexsort((nombres[idx], -score[idx]))]
            ranks[d, orden] = np.arange(1, len(idx) + 1)

    return pd.DataFrame({
        "propulsion": props,
        "modelo_norm": nombres,
        "top3_pct": (ranks <= 3).mean(axis=0) * 100,
        "top1_pct": (ranks == 1).mean(axis=0) * 100,
        "rank_p05": np.percentile(ranks, 5, axis=0),
        "rank_p95": np.percentile(ranks, 95, axis=0),
    })


def calcular(n_perturbaciones: int, delta: float):
    """Devuelve (largo, resumen) sin escribir nada."""
    if not ENTRADA.exists():
        sys.exit(f"No existe {ENTRADA}. Ejecuta antes: python3 codes/analisis.py")

    df = pd.read_csv(ENTRADA)
    faltan = [c for c in COLS_NORM + COLS_RAW + ["score", "propulsion", "modelo_norm"]
              if c not in df.columns]
    if faltan:
        sys.exit(f"Faltan columnas en {ENTRADA.name}: {faltan}. "
                 "Re-ejecuta python3 codes/analisis.py")

    w = _pesos_base()

    # Guardia: el CSV debe ser el que produce analisis.py. Si no, la
    # sensibilidad estaría midiendo otra cosa. Se comprueba antes de operar
    # para que un NaN no pase inadvertido: `nan > 1e-6` es False y el check
    # anterior daba OK con 15/38 scores rotos.
    score_base = df[COLS_NORM].to_numpy(dtype=float)
    score_base = np.where(np.isnan(score_base), 0.5, score_base) @ w
    score_oficial = df["score"].to_numpy(dtype=float)
    if not np.isfinite(score_base).all() or not np.isfinite(score_oficial).all():
        malos = int((~np.isfinite(score_base)).sum() + (~np.isfinite(score_oficial)).sum())
        sys.exit(f"Hay {malos} valores no finitos en el score del CSV o en su "
                 "reconstrucción. Re-ejecuta python3 codes/analisis.py.")
    dif = np.abs(score_base - score_oficial).max()
    if dif > 1e-6:
        sys.exit(f"El score del CSV no se reproduce (diferencia máx {dif:.2e}). "
                 "Re-ejecuta python3 codes/analisis.py antes de la sensibilidad.")

    # ---- Largo: modelo × escenario ----
    filas = []
    for escenario, score in _escenarios(df, w):
        tmp = df[["propulsion", "modelo_norm"]].copy()
        tmp["score"] = score
        tmp = _ordenar_por_grupo(tmp, "score")
        tmp["escenario"] = escenario
        filas.append(tmp[["propulsion", "modelo_norm", "escenario", "score", "rank"]])
    largo = pd.concat(filas, ignore_index=True)
    largo = largo.sort_values(["propulsion", "escenario", "rank"],
                              kind="mergesort").reset_index(drop=True)

    # El escenario base debe ser el ranking oficial, no solo un score parecido.
    base = (largo[largo["escenario"] == "base"]
            .set_index(["propulsion", "modelo_norm"])["rank"])
    if "rank_propulsion" in df.columns:
        oficial = df.set_index(["propulsion", "modelo_norm"])["rank_propulsion"]
        if not base.reindex(oficial.index).eq(oficial).all():
            sys.exit("El ranking base de sensibilidad no coincide con "
                     "`rank_propulsion` del CSV oficial.")
    if largo["score"].isna().any():
        sys.exit("La sensibilidad produjo scores NaN; revisa la imputación 0.5.")

    # ---- Resumen: estabilidad de cada modelo ----
    piv = largo.pivot(index=["propulsion", "modelo_norm"],
                      columns="escenario", values="rank")
    alternos = [c for c in piv.columns if c != "base"]

    resumen = pd.DataFrame({
        "rank_base": piv["base"],
        "rank_min": piv[alternos].min(axis=1),
        "rank_max": piv[alternos].max(axis=1),
        "n_escenarios_top3": (piv[alternos] <= 3).sum(axis=1),
        "escenario_peor": piv[alternos].idxmax(axis=1),
        "escenario_mejor": piv[alternos].idxmin(axis=1),
    }).reset_index()

    perturbacion = _perturbar(df, w, n_perturbaciones, delta)
    resumen = resumen.merge(
        df[["propulsion", "modelo_norm", "score", "n_criterios", "n_anuncios"]],
        on=["propulsion", "modelo_norm"], how="left",
    ).rename(columns={"score": "score_base"})
    resumen = resumen.merge(
        perturbacion, on=["propulsion", "modelo_norm"], how="left", validate="one_to_one"
    )

    resumen = resumen[[
        "propulsion", "modelo_norm", "score_base", "rank_base",
        "top3_pct", "top1_pct", "rank_p05", "rank_p95",
        "rank_min", "rank_max", "n_escenarios_top3",
        "escenario_mejor", "escenario_peor", "n_criterios", "n_anuncios",
    ]].sort_values(["propulsion", "rank_base"], kind="mergesort").reset_index(drop=True)

    # Redondeo explícito: CSV estable entre corridas (y legible).
    largo["score"] = largo["score"].round(6)
    resumen["score_base"] = resumen["score_base"].round(6)
    for col in ["top3_pct", "top1_pct", "rank_p05", "rank_p95"]:
        resumen[col] = resumen[col].round(2)
    for col in ["rank_base", "rank_min", "rank_max",
                "n_escenarios_top3", "n_criterios", "n_anuncios"]:
        resumen[col] = resumen[col].astype(int)

    return largo, resumen


def _imprimir(largo: pd.DataFrame, resumen: pd.DataFrame, n: int, delta: float):
    """Resumen legible por consola (lo que luego va al reporte)."""
    print(f"\n== SENSIBILIDAD (n_perturbaciones={n}, delta=±{delta}) ==")
    for prop in largo["propulsion"].unique():
        sub = largo[(largo.propulsion == prop) & (largo.escenario == "base")]
        base_top3 = sub.nsmallest(3, "rank")["modelo_norm"].tolist()
        print(f"\n{prop.upper()} ({len(sub)} modelos)")
        print("  base top-3: " + " > ".join(base_top3))

        res = resumen[resumen.propulsion == prop].set_index("modelo_norm")
        for m in base_top3:
            if m in res.index:
                r = res.loc[m]
                print(f"    {m}: top-3 en {r.top3_pct:.1f}% de las perturbaciones "
                      f"| rank {int(r.rank_p05)}–{int(r.rank_p95)} (p05–p95)")

        cambios = (largo[(largo.propulsion == prop) & (largo["rank"] == 1)
                         & (largo.escenario != "base")]
                   .set_index("escenario")["modelo_norm"])
        distintos = cambios[cambios != base_top3[0]].to_dict()
        print(f"  1º puesto: se mantiene en {len(cambios) - len(distintos)}/"
              f"{len(cambios)} escenarios; cambia en {distintos or 'ninguno'}")

    print(f"\n-> Guardado: {SALIDA_LARGA.relative_to(ROOT)} "
          f"({len(largo)} filas = {resumen.shape[0]} modelos × "
          f"{largo.escenario.nunique()} escenarios)")
    print(f"-> Guardado: {SALIDA_RESUMEN.relative_to(ROOT)} ({len(resumen)} filas)")


def main():
    ap = argparse.ArgumentParser(description="Sensibilidad del ranking a pesos y criterios.")
    ap.add_argument("--n", type=int, default=2000,
                    help="número de perturbaciones de pesos (default 2000)")
    ap.add_argument("--delta", type=float, default=0.05,
                    help="amplitud de la perturbación uniforme (default 0.05)")
    ap.add_argument("--check", action="store_true",
                    help="no escribe: falla si los CSV no coinciden con el cálculo")
    args = ap.parse_args()

    if args.n < 1:
        sys.exit("--n debe ser >= 1")
    if not 0 < args.delta <= 1:
        sys.exit("--delta debe estar en (0, 1]")

    largo, resumen = calcular(args.n, args.delta)
    texto_largo = largo.to_csv(index=False)
    texto_resumen = resumen.to_csv(index=False)

    if args.check:
        ok = True
        for ruta, texto in [(SALIDA_LARGA, texto_largo),
                            (SALIDA_RESUMEN, texto_resumen)]:
            if not ruta.exists():
                print(f"[check] FALTA {ruta.name}")
                ok = False
            elif ruta.read_text(encoding="utf-8") != texto:
                print(f"[check] DESACTUALIZADO {ruta.name}")
                ok = False
        if not ok:
            sys.exit(1)
        print(f"[check] OK: {SALIDA_LARGA.name} y {SALIDA_RESUMEN.name} "
              "coinciden con el cálculo")
        return

    SALIDA_LARGA.write_text(texto_largo, encoding="utf-8")
    SALIDA_RESUMEN.write_text(texto_resumen, encoding="utf-8")
    _imprimir(largo, resumen, args.n, args.delta)


if __name__ == "__main__":
    main()
