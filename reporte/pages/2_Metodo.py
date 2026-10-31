"""
Página 2: Método — Pesos, normalización, reglas de decisión.
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
from reporte.theme import apply_style


st.set_page_config(page_title="Método", page_icon="🔬", layout="wide")
apply_style()

st.title("🔬 Método y Decisiones Metodológicas")

st.markdown("""
Este reporte integra **tres fuentes de evidencia** para responder a la pregunta central:
> *¿Qué triciclo comprar en La Habana y por qué?*

La pregunta es de **decisión**, no de censo. "Lo más común" entra como **indicador**
(oferta anunciada + lo visto en calle) y no como respuesta: la muestra de campo está
cerrada en 5 de 15 municipios.

Cada fuente mide algo distinto y se trata de forma separada.
""")

# ======= FUENTES =======
st.header("1️⃣ Fuentes de datos")

fuentes = pd.DataFrame({
    "Fuente": [
        "Anuncios online (scraper)",
        "Catálogos de empresas (scraper)",
        "Trabajo de campo (inventario municipal)"
    ],
    "Qué mide": [
        "Oferta visible, precios, specs declaradas",
        "Oferta formal, disponibilidad, specs de fabricante",
        "Circulación real observada en calle"
    ],
    "Registros": [70, 30, 30],
    "Unidades": ["42 modelos", "29 fichas", "12 marcas"],
    "Cobertura": [
        "6 fuentes: elyerromenu, islagrande, vedca_telegram, casalindashop, cubancargos, Facebook",
        "5 empresas: KikiHabana, MZ Products, A Cuba Envíos Cargo, Mr Cuba, CompraMasonline",
        "5/15 municipios: Centro Habana, Plaza, Habana del Este, La Lisa, Playa (muestra cerrada, 2026-10-13→25)"
    ],
    "Estado": ["✅ Activo", "✅ Activo", "✅ Cerrado (muestra final)"]
})
st.dataframe(fuentes, use_container_width=True, hide_index=True)

st.caption(
    "El ranking tiene **42 filas** porque el mismo nombre puede aparecer en dos "
    "propulsiones (el STAR eléctrico y el STAR híbrido son productos "
    "distintos): 41 nombres distintos, 42 modelos en el scoring."
)

st.markdown("---")

# ======= SCORING =======
st.header("2️⃣ Scoring de 'Mejor Opción'")

st.subheader("Pesos aprobados")
pesos = pd.DataFrame({
    "Criterio": ["Precio (USD)", "Autonomía (km)", "Carga (kg)", "Legalidad (binario)", "Repuestos (proxy)"],
    "Peso": [0.40, 0.25, 0.20, 0.10, 0.05],
    "Dirección": ["Menor = mejor", "Mayor = mejor", "Mayor = mejor", "1 = menciona legalidad", "1 = >1 fuente"],
    "Fuente": ["Anuncios/Empresas", "Anuncios/Empresas", "Anuncios/Empresas", "Anuncios/Empresas", "Anuncios"]
})
st.dataframe(pesos, use_container_width=True, hide_index=True)

st.markdown("""
**Fórmula:**
```
score = Σ (criterio_norm × peso)
```
- Cada criterio se normaliza **min-max 0-1 dentro de su grupo de propulsión** (eléctricos vs eléctricos, etc.)
- **Ausentes → 0.5 neutro** (no castiga ni beneficia) + se reporta `n_criterios` (cobertura real)
- **No se comparan scores entre propulsiones** (normalización intra-grupo)
""")

st.subheader("Reglas de decisión clave")
reglas = pd.DataFrame({
    "Tema": [
        "Rangos de autonomía",
        "Datos ausentes",
        "Identidad del producto",
        "Variantes por química",
        "C400 vs C400A",
        "Oferta viva",
        "Gasolina: autonomía",
        "Repuestos proxy",
        "Precios EUR (islagrande)",
        "Campo vs online: nivel de comparación",
        "Campo: alcance (muestra cerrada)",
        "Campo: incertidumbre (n=30)"
    ],
    "Regla": [
        "Siempre límite inferior (ej. '90-100 km' → 90 km)",
        "Imputación neutra 0.5 + columna n_criterios",
        "modelo = nombre propio; si no hay, la identidad es la MARCA; + propulsión",
        "Sólo en eléctricos: modelo_norm incluye química (LiFePO4 ≠ GelPb)",
        "Modelos distintos (no se fusionan)",
        "Sin fecha = vigente; con fecha → ≥ 2026-01-01; 'agotado' = no viva",
        "NO se estima (prohibido inventar datos)",
        "1 si modelo aparece en >1 fuente, 0 si no",
        "Se guardan en precio_valor/moneda; NO se convierten a USD",
        "El campo no distingue modelo → se compara por MARCA; nunca se aplican alias de modelo al campo",
        "Muestra cerrada: 30 obs en 5 de 15 municipios. Describe la muestra; no se extrapola a La Habana",
        "Cuota con intervalo de Wilson: con 30 casos, el 1º y el 3º no se distinguen. No se ordena 'quién gana'"
    ]
})
st.dataframe(reglas, use_container_width=True, hide_index=True)

st.markdown("---")

# ======= LIMPIEZA =======
st.header("3️⃣ Pipeline de limpieza (raw → clean → score)")

st.markdown("""
```
Data/raw_data/           →  Crudos inmutables (write once)
    ├── anuncios_triciclos.jsonl
    ├── anuncios_facebook.jsonl  (parseado desde data_from_FB)
    ├── data_from_FB              (original, no se toca)
    └── data_personas.txt         (hoja de campo; NO se commitea: datos personales)

codes/parse_fb.py        →  Parsing tolerante a errores + normalización
codes/scrape_empresas.py →  Scraping catálogos + normalización
codes/parse_campo.py     →  Hoja de campo: anonimiza (descarta nombre/CI) y normaliza
        ↓
Data/clean_data/         →  Limpios listos para análisis (entrada de analisis.py)
    ├── anuncios_triciclos.jsonl
    ├── anuncios_facebook.jsonl
    ├── empresas_kikihabana.jsonl
    ├── empresas_mzproducts.jsonl
    ├── empresas_acubaenvioscargo.jsonl
    └── empresas_mrcuba.jsonl

Data/registro_ubicaciones.csv  →  Inventario de campo (17 columnas, sin datos personales)

codes/analisis.py        →  Carga clean_data/, aplica alias, scoring, genera CSVs
codes/analisis_campo.py  →  Campo: cuotas por marca, IC95 (Wilson), uso y cruce con el score
        ↓
Data/clean_data/ (outputs)
    ├── score_modelos.csv
    ├── comparacion_campo_online.csv
    ├── campo_resumen.csv          (marca: cuota, IC95, uso dominante, score)
    ├── campo_uso.csv              (uso: cuota, IC95, marcas)
    ├── frecuencia_por_municipio.csv
    └── frecuencia_por_tipo_uso.csv
""")

st.markdown("**Regla de oro:** Todos los datasets se limpian/normalizan **antes** de cualquier operación. Nada de 'limpiar al vuelo en el gráfico'.")

st.markdown("---")

# ======= ALIAS =======
st.header("4️⃣ Alias de fusión (modelos entre fuentes)")

alias_data = [
    ("BRIDERK (FB)", "TOPMAQ BRIDERK 2026 GELPB (scraper)"),
    ("TOPMAQ genérico (FB)", "TOPMAQ BRIDERK 2026 GELPB (scraper)"),
    ("MVP POWER (FB)", "MVP POWER GELPB (scraper)"),
    ("ONEBOT (FB)", "ONEBOT CLASIC 2026 (scraper)"),
    ("KIVITOVA (FB)", "KIVITOVA GELPB (scraper)"),
    ("KIVITOVA PREMIUM (FB)", "KIVITOVA GELPB (scraper)"),
    ("MAF (FB)", "MAF LIFEPO4 (scraper)"),
    ("VIENTO RAPIDO (FB)", "VIENTO RAPIDO (scraper)"),
]
alias_df = pd.DataFrame(alias_data, columns=["Nombre en Facebook", "Nombre canónico (scraper)"])
st.dataframe(alias_df, use_container_width=True, hide_index=True)

st.caption(
    "Nota: STAR eléctrico (FB) ≠ STAR híbrido (scraper) → NO se fusionan "
    "(la propulsión forma parte de la identidad). Tampoco se fusionan "
    "OIM / OIM PASAJE, ni DDS-OD (marca KIVITOVA, modelo distinto)."
)

st.markdown("""
**Alias de marca (eje distinto).** Para comparar con el trabajo de campo —que
solo lee la marca— existe una tabla aparte, `MARCA_ALIAS`: `ONEBOOT → ONEBOT`,
`KVITOVA → KIVITOVA`, `MAGICBIKE → MAGIC BIKE`, `VELGA → VEDCA` (errata
confirmada) y `JINPEING / JINPEN / JIMPENG → JINPENG`. Fusionar la marca **no**
fusiona productos: JINPENG eléctrico y JINPEN híbrido siguen siendo identidades
distintas. Al campo no se le aplica ningún alias de *modelo*: afirmar que un
ONEBOT visto en calle es el "ONEBOT CLASIC 2026" sería inventar el modelo.
""")

st.markdown("---")

# ======= IDENTIDAD =======
st.header("5️⃣ Identidad del producto (limpieza de nombres)")

st.markdown("""
El campo `modelo` es la **identidad** del producto: es la clave con la que se
agrupan los anuncios de distintas fuentes. Los nombres vienen de las webs, así
que se normalizan en el **origen** (`codes/norm_modelo.py` + la tabla curada
`Data/modelos_canonicos.json`); el JSONL crudo ya sale limpio.
""")

identidad_data = [
    ("Genéricos de categoría", "TRICICLO(S), ELÉCTRICO(S), HÍBRIDO(S), DE COMBUSTION, DE CARGA, PASAJEROS"),
    ("Marketing / estado", "DISPONIBLE, MAS GRANDE, MEJOR PRECIO, PANEL SOLAR, FOTOVOLTAICO"),
    ("Specs (ya en otros campos)", "72V, 85AH, 1500W, LITHIUM, LIFEPO4, MOTOR, BATERÍA"),
    ("Sin nombre de modelo", "`modelo` = null y la identidad pasa a la MARCA (CHILWEE, CYT, MAF, KIVITOVA…)"),
    ("Mismo nombre, producto distinto", "Se separan con sufijo de variante y se cuentan aparte (OIM / OIM PASAJE, E-CARGO 80AH / 60AH / 100AH)"),
    ("Propulsión", "Forma parte de la identidad: mismo nombre + distinta propulsión = productos distintos"),
]
st.dataframe(pd.DataFrame(identidad_data, columns=["Qué se quita / decide", "Regla"]),
             use_container_width=True, hide_index=True)

st.caption(
    "La tabla canónica (`Data/modelos_canonicos.json`) se genera con "
    "`python3 codes/crear_canonicos.py` y es la fuente de verdad: si se edita "
    "un JSONL a mano, la siguiente pasada del scraper lo sobrescribe."
)