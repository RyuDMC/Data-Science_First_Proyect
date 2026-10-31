# HANDOFF — Triciclos La Habana (cierre 2026-10-31)

## 1. Contexto
- Investigación de mercado de triciclos en La Habana. **Pregunta central nueva (decisión 2026-10-31):** *"¿Qué triciclo comprar en La Habana y por qué?"*. "Lo más común" pasó a ser un **indicador** (oferta + calle), no la respuesta.
- Entregable = reporte Streamlit con 3 fuentes: anuncios online, catálogos de empresas y trabajo de campo.
- **El trabajo de campo está cerrado** (decisión del usuario): 30 observaciones en 5 municipios son la muestra definitiva; no se extrapola a La Habana y no habrá más captación.
- Esta sesión: (1) integrar el campo al pipeline (cuotas + IC95 + uso), (2) ajustar todo el proyecto al campo cerrado, (3) reescribir la pregunta central, (4) ampliar los catálogos de empresas con un scraper nuevo (CompraMasonline).

## 2. Estado actual
- **Campo (cerrado):** 30 obs, 5 municipios (Centro Habana, Plaza, Habana del Este, La Lisa, Playa), 2026-10-13→25. 12 marcas; JINPENG 20% [10–37], KIVITOVA/ONEBOT 16.7% [7–34]. Uso: pasajeros 60%, carga 20%, mixto 20%. 29 eléctricos + 1 híbrido.
- **Nuevo `codes/parse_campo.py`:** txt → `Data/registro_ubicaciones.csv` (anonimiza PII, normaliza, `--check` idempotente).
- **Nuevo `codes/analisis_campo.py`:** única fuente de las cifras de campo → `campo_resumen.csv` (marca: n, cuota, **IC95 Wilson**, uso dominante, specs medianas, oferta online, mejor score de la marca) y `campo_uso.csv`.
- **Reporte al día:** página 8 reescrita (IC, "más común vs mejor valorado", uso, alcance de la muestra con los 15 municipios marcados); página 7 ordena escenarios por uso observado; portada, Resumen, Método y Limitaciones sin textos de "campo en curso/pendiente".
- **Catálogos de empresas: 22 → 29 fichas, 4 → 5 empresas.** Nuevo `scrape_compramasonline()` (7 fichas: 6 eléctricos + 1 híbrido RALLY con extensor de rango; excluye 2 extensores sueltos, el "Minicarrito" de 4 ruedas y el genérico "TRICICLO ELÉCTRICO DE CARGA", que duplicaba MINGHONG). Refresco de las 4 empresas existentes: solo cambian 2 autonomías (Kiki ONEBOT T414 85 km, HUAIHAI 120 km) y 2 precios MZ (+$20/+$100).
- **Identidad:** `Data/modelos_canonicos.json` pasa a **98 productos** (2 excluidos); `norm_modelo.py --check` → 0 cambios. Decisiones 2026-10-31: RALLY se llama **RALLY**, se mantiene **híbrido**, y se excluye el genérico de CompraMasonline. `reporte/data.py` descubre las empresas por glob de `Data/empresas/` (añadir una empresa ya no exige tocar el reporte).
- **Scoring intacto:** los scores son idénticos (mismo md5 de la columna `score`); TOPMAQ BRIDERK 0.786 > ONEBOT CLASIC 0.775 > KIVITOVA GELPB 0.723.
- **Empresas integradas (A + B, decisión del usuario 2026-10-31):** (A) los 5 catálogos suman fuentes al `repuestos_proxy` (sigue en 9/42: no hay modelo que cruce); (B) `integrar_empresas()` añade a `score_modelos.csv` contexto que **no entra al score**: `n_empresas`, `precio_empresa_med`, `en_catalogo` (nivel modelo) y `marca_en_catalogo`, `n_empresas_marca` (nivel marca). Se muestran en Ranking y Contendientes.
- **Hallazgo:** ningún modelo de catálogo coincide con la identidad de un anuncio; solo la marca **ONEBOT** cruza (3 modelos). No se fuerza la equivalencia por marca.
- **Verificado:** `AppTest` 11/11 sin excepciones; `parse_campo --check` OK; `crear_canonicos --check` estable; compila todo.
- **Git:** HEAD `e406bf9`. **Nada commiteado** (varios modificados + nuevos, incluidos `parse_campo.py`, `analisis_campo.py`, `compramasonline.jsonl` y 4 CSV de campo).

## 3. Pendiente
1. **Revisar y commitear** todo lo de esta sesión (incluye `codes/parse_campo.py`, `codes/analisis_campo.py`, `Data/empresas/compramasonline.jsonl`, `Data/clean_data/compramasonline.jsonl` y los CSV de campo).
2. **Decidir si `Data/empresas/` entra al scoring completo** (hoy solo da contexto; si entra, los 3 E-CARGO y 2 FLY RACING se agregarían y habría que publicar el antes/después).
3. **Campo: nada más que hacer** — no reabrir la captación ni prometer 15 municipios en el reporte.
4. Heredados: `use_container_width` → `width="stretch"` (Streamlit 1.66), `precio_texto_usd` (3 contradictorios), conflicto VEDCA C400, MAGIKBIKE, Mr Cuba (Wix frágil), `vedca.cu` caído, llevar `Data/fuentes_justificacion.md` a `2_Metodo`, deploy.

## 4. Recursos
- **Repo:** `/run/media/ryudmc/17bd76d4-00a3-4be2-a374-79313809c703/Oliver/Study/DS Proyects/Data-Science` (disco externo) · remoto `github.com/RyuDMC/Data-Science`.
- **Pipeline:** `codes/scrape_triciclos.py` (anuncios) · `codes/parse_fb.py` · `codes/scrape_empresas.py` (5 catálogos) · `codes/parse_campo.py` · `codes/analisis.py` (scoring) · `codes/analisis_campo.py` (campo) · `codes/norm_modelo.py` + `codes/crear_canonicos.py` (identidad).
- **Datos:** `Data/raw_data/` (crudo, PII ignorada) · `Data/empresas/*.jsonl` (5) · `Data/clean_data/` (JSONL + `score_modelos.csv` + `campo_resumen.csv` + `campo_uso.csv`) · `Data/modelos_canonicos.json` (98).
- **Reporte:** `reporte/app.py`, `reporte/data.py`, `reporte/theme.py`, `reporte/pages/*` (10 páginas).
- **Docs:** `Data/Posibles fuentes de datos.md`, `Data/Links de Referencias.md`, `Data/fuentes_justificacion.md` · Diario `opencode/Journaing_file.md` (29 entradas).
- **Orden de ejecución:** `scrape_triciclos` → `parse_fb` → `scrape_empresas` → `parse_campo` → `analisis` → `analisis_campo` → `norm_modelo --migrar` → `crear_canonicos` → `parse_campo --check` → `streamlit run reporte/app.py`.
- **Pesos (no cambiar sin decisión):** precio 0.40, autonomía 0.25, carga 0.20, legalidad 0.10, repuestos 0.05; min-max intra-propulsión; ausentes 0.5 + `n_criterios`. **No comparar scores entre propulsiones.**

## 5. Advertencias
- **Prohibido inventar datos.** Rangos → límite inferior; ausentes → 0.5 + `n_criterios`; si una ficha solo declara voltaje, `bateria_ah` queda `null` (no se estima).
- **La identidad se cambia en `Data/modelos_canonicos.json` / `codes/crear_canonicos.py`, NUNCA a mano en los JSONL** (el scraper sobrescribe). Tras editar: `norm_modelo.py --migrar` → `analisis.py`.
- **El campo no entra al scoring** (mide circulación, no oferta) y **no se generaliza**: 5 de 15 municipios, sin denominador.
- **PII:** `Data/raw_data/data_personas.txt` (nombre + CI) está en `.gitignore`. No commitear ni copiar a otro sitio.
- **Disco externo:** comprobar montaje antes de escribir; si no está, preguntar (nunca duplicar el repo).
- **Streamlit:** mantener el bootstrap de `sys.path` en cada página; verificar con `streamlit.testing.v1.AppTest` (11 páginas) y con servidor real.
- **PEP 668:** `pip` solo dentro de `reporte/.venv`.
- **El usuario decide metodología y commitea.** Handoff se reescribe al cerrar sesión (este documento se pidió expresamente).
