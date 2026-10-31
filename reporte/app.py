"""
Punto de entrada del reporte interactivo: Triciclos La Habana.
Ejecución: streamlit run reporte/app.py
"""

import streamlit as st

# Configuración de página (debe ser lo primero)
st.set_page_config(
    page_title="Triciclos La Habana — Reporte Interactivo",
    page_icon="🛺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar con info del proyecto
with st.sidebar:
    st.markdown("## 🛺 Triciclos La Habana")
    st.caption("Investigación de mercado · La Habana")
    st.markdown("---")
    st.markdown("**Pregunta central:**")
    st.info("¿Qué triciclo comprar en La Habana y por qué?")
    st.caption(
        "\"Lo más común\" queda como **indicador**, no como respuesta: se mide con 70 "
        "anuncios + 29 fichas de empresas + 30 observaciones de calle en 5 municipios. "
        "**No hay censo** y el trabajo de campo está cerrado."
    )
    st.markdown("---")
    st.markdown("**Fuentes de datos:**")
    st.markdown("- Anuncios online (6 fuentes)")
    st.markdown("- Catálogos de empresas (5 empresas)")
    st.markdown("- Trabajo de campo (muestra cerrada, 5 municipios)")
    st.markdown("---")
    st.caption("Corte de datos: 2026-10-19")
    st.caption("Stack: Streamlit + Matplotlib + Pandas")

# La navegación multipágina de Streamlit usa la carpeta pages/ automáticamente
# No hay código adicional necesario aquí; las páginas en reporte/pages/ se cargan solas.

# Página de portada (esta es la que se ve al entrar)
st.title("🛺 Triciclos en La Habana: Reporte Interactivo")
st.markdown("""
Este reporte presenta el análisis del mercado de triciclos en La Habana,
integrando **tres fuentes de evidencia**:

| Fuente | Qué mide | Registros | Unidades |
|--------|----------|-----------|----------|
| **Anuncios online** | Oferta y competencia de precios | 70 | 42 modelos |
| **Catálogos de empresas** | Oferta formal y disponibilidad | 29 | 29 fichas |
| **Trabajo de campo** | Circulación real (inventario municipal) | 30 | 12 marcas, 5 municipios |

*Muestra de campo **cerrada**: 30 observaciones en 5 municipios, dos semanas. No es censo y no se generaliza a toda La Habana.*

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
9. **🏢 Empresas** — 29 fichas de catálogos
10. **⚠️ Limitaciones** — Qué no sabemos y por qué

---

### 🔄 Cómo se actualiza
```bash
# 1. Scraping + análisis
python3 codes/scrape_triciclos.py
python3 codes/parse_fb.py
python3 codes/scrape_empresas.py
python3 codes/parse_campo.py      # hoja de campo -> registro_ubicaciones.csv
python3 codes/analisis.py
python3 codes/analisis_campo.py   # campo: cuotas, IC95, uso, cruce con score

# 2. El reporte lee Data/clean_data/ en vivo → refresca y listo
streamlit run reporte/app.py
```
""")

st.markdown("---")
st.caption("💡 Consejo: usa el filtro de propulsión (eléctrico / híbrido / gasolina) en las páginas de Ranking y Contendientes.")