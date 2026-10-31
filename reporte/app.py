"""
Punto de entrada del reporte interactivo: Triciclos La Habana.
Ejecución: streamlit run reporte/app.py
"""

import os as _os
import sys as _sys

import streamlit as st

# La portada también lee `reporte/data.py`; hace falta la raíz del repo en
# sys.path (Streamlit solo añade la carpeta del script).
_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)
from reporte.data import load_metadata  # noqa: E402

# Configuración de página (debe ser lo primero)
st.set_page_config(
    page_title="Triciclos La Habana — Reporte Interactivo",
    page_icon="🛺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Única fuente de las cifras: Data/metadata.json (codes/generar_metadata.py).
_meta = load_metadata()
_conteos = _meta.get("conteos", {})
_cortes = _meta.get("cortes", {})


def _n(clave):
    """Conteo por clave, o "—" si falta el metadata."""
    return _conteos.get(clave, "—")

# Sidebar con info del proyecto
with st.sidebar:
    st.markdown("## 🛺 Triciclos La Habana")
    st.caption("Investigación de mercado · La Habana")
    st.markdown("---")
    st.markdown("**Pregunta central:**")
    st.info("¿Qué triciclo comprar en La Habana y por qué?")
    st.caption(
        f"\"Lo más común\" queda como **indicador**, no como respuesta: se mide con "
        f"{_n('anuncios')} anuncios + {_n('fichas_empresa')} fichas de empresas + "
        f"{_n('observaciones_campo')} observaciones de calle en "
        f"{_n('municipios_campo')} municipios. "
        "**No hay censo** y el trabajo de campo está cerrado."
    )
    st.markdown("---")
    st.markdown("**Fuentes de datos:**")
    st.markdown(f"- Anuncios online ({_n('fuentes_anuncios')} fuentes)")
    st.markdown(f"- Catálogos de empresas ({_n('empresas')} empresas)")
    st.markdown(
        f"- Trabajo de campo (muestra cerrada, {_n('municipios_campo')} municipios)"
    )
    st.markdown("---")
    st.caption(
        f"Corte de datos: anuncios {_cortes.get('anuncios', '—')} · "
        f"catálogos {_cortes.get('catalogos', '—')}"
    )
    st.caption("Stack: Streamlit + Matplotlib + Pandas")

# La navegación multipágina de Streamlit usa la carpeta pages/ automáticamente
# No hay código adicional necesario aquí; las páginas en reporte/pages/ se cargan solas.

# Página de portada (esta es la que se ve al entrar)
st.title("🛺 Triciclos en La Habana: Reporte Interactivo")
st.markdown(f"""
Este reporte presenta el análisis del mercado de triciclos en La Habana,
integrando **tres fuentes de evidencia**:

| Fuente | Qué mide | Registros | Unidades |
|--------|----------|-----------|----------|
| **Anuncios online** | Oferta y competencia de precios | {_n('anuncios')} | {_n('modelos_ranking')} modelos |
| **Catálogos de empresas** | Oferta formal y disponibilidad | {_n('fichas_empresa')} | {_n('fichas_empresa')} fichas |
| **Trabajo de campo** | Circulación real (inventario municipal) | {_n('observaciones_campo')} | {_n('marcas_campo')} marcas, {_n('municipios_campo')} municipios |

*Muestra de campo **cerrada**: {_n('observaciones_campo')} observaciones en {_n('municipios_campo')} municipios, dos semanas. No es censo y no se generaliza a toda La Habana.*

---

### 🎯 Navegación del reporte
Usa el **menú lateral** (☰) para ir a cada sección:

1. **📋 Resumen** — La pregunta y los 3 titulares clave
2. **🔬 Método** — Pesos, normalización, reglas de decisión
3. **📊 Mercado** — KPIs, mix por propulsión y fuentes
4. **🏆 Ranking** — Filtro por grupo, tabla ordenable, comparador
5. **💰 Precio / Autonomía / Carga** — Burbuja y frontera eficiente
6. **🎯 Contendientes** — Top por grupo + radar de criterios
7. **✅ Mejor opción** — Recomendación por escenario
8. **🗺️ Trabajo de campo** — Circulación real observada (muestra cerrada, 5 municipios)
9. **🏢 Empresas** — {_n('fichas_empresa')} fichas de catálogos
10. **⚠️ Limitaciones** — Qué no sabemos y por qué

---

### 🔄 Cómo se actualiza
```bash
# 1. Scraping + análisis
python3 codes/scrape_triciclos.py
python3 codes/parse_fb.py
python3 codes/crear_canonicos.py      # fija los nombres canónicos
python3 codes/scrape_empresas.py
python3 codes/parse_campo.py      # hoja de campo -> registro_ubicaciones.csv
python3 codes/norm_modelo.py --migrar
python3 codes/crear_canonicos.py      # consolida tras la migración
python3 codes/norm_modelo.py --migrar
python3 codes/analisis.py
python3 codes/analisis_campo.py   # campo: cuotas, IC95, uso, cruce con score
python3 codes/sensibilidad.py     # robustez del ranking (no cambia el score)
python3 codes/generar_metadata.py # conteos, cortes y resultados -> Data/metadata.json

# 2. El reporte lee Data/clean_data/ en vivo → refresca y listo
streamlit run reporte/app.py
```
""")

st.markdown("---")
st.caption("💡 Consejo: usa el filtro de propulsión (eléctrico / híbrido / gasolina) en las páginas de Ranking y Contendientes.")