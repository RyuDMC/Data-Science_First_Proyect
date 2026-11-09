# 🗂️ Estructura

- 📦 **[Data-Science_First_Proyect](https://github.com/RyuDMC/Data-Science_First_Proyect)**
  - 🔧 **[`codes/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/codes)** — Scrapers, normalización, scoring, campo, sensibilidad, metadata y el generador de datos de «La Historia».
  - 🗃️ **[`Data/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data)** — Datos, tabla canónica, metadata y documentación.
    - 🗄️ **[`archive/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/archive)** — Versiones históricas; ranking legado del 2026-10-11.
    - 🧹 **[`clean_data/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/clean_data)** — JSONL procesados y CSV derivados (score, campo, sensibilidad).
    - 🏢 **[`empresas/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/empresas)** — Catálogos de las 10 empresas en JSONL.
    - 🧩 **[`Estructuras/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/Estructuras)** — Esquema JSON de un anuncio.
    - 📥 **[`raw_data/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/raw_data)** — Capturas genuinas: transcripción de Facebook y hoja de campo (esta última ignorada por git). El JSONL del scraper vive una sola vez en [`clean_data/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/clean_data).
  - 🖥️ **[`reporte/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/reporte)** — Aplicación Streamlit multipágina.
    - ⚙️ **[`.streamlit/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/reporte/.streamlit)** — Configuración de tema y servidor.
    - 📄 **[`pages/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/reporte/pages)** — Las 10 páginas del reporte.
  - 🌐 **[`historia/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/historia)** — «La Historia»: página estática scrollytelling, aparte del reporte técnico (`index.html` + `datos.json`/`datos.js` generados por `codes/generar_historia.py`).
  - 🧪 **[`tests/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/tests)** — Cifras, contratos, identidad, páginas, historia y privacidad.
  - 📓 **[`opencode/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/opencode)** — Handoff, diario de trabajo y auditoría JINPEN.
  - 💬 **[`Prompts/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Prompts)** — Prompts e instrucciones del proyecto.
  - 📌 **[`requirements.txt`](https://github.com/RyuDMC/Data-Science_First_Proyect/blob/main/requirements.txt)** — Dependencias del pipeline y del reporte.
  - 🛠️ **[`requirements-dev.txt`](https://github.com/RyuDMC/Data-Science_First_Proyect/blob/main/requirements-dev.txt)** — Dependencias de desarrollo y tests.
  - 🚫 **[`.gitignore`](https://github.com/RyuDMC/Data-Science_First_Proyect/blob/main/.gitignore)** — Entorno y datos personales excluidos.
  - 📖 **[`README.md`](https://github.com/RyuDMC/Data-Science_First_Proyect/blob/main/README.md)** — Este documento.

## ▶️ Montar la página

**Prerrequisitos:** Python 3.12 o superior y Git.

Desde la raíz del proyecto, paso a paso:

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/RyuDMC/Data-Science_First_Proyect.git
   cd Data-Science_First_Proyect
   ```

2. **Crear el entorno e instalar dependencias**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate               # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Montar la página**

   ```bash
   streamlit run reporte/app.py
   ```

   Se abre en `http://localhost:8501` (la consola muestra la URL local).
   Para detenerla, pulsa `Ctrl+C` en la terminal.
   En Windows, sustituye `python3` por `python`.

4. **Ver «La Historia», la página estática aparte**

   ```bash
   python3 codes/generar_historia.py     # genera historia/datos.json y datos.js
   python3 -m http.server --directory historia
   # → http://localhost:8000  (Ctrl+C para parar)
   ```

   También funciona con doble clic en `historia/index.html`: los datos van
   embebidos en `datos.js`, no hay fetch ni dependencias externas. Alinear
   con el estado real de los datos:

   ```bash
   python3 codes/generar_historia.py --check
   # [check] OK: historia/datos.json y datos.js coinciden con los datos de Data/
   ```

   Para publicarla (opcional), GitHub Pages → *Settings* → *Pages* →
   *Deploy from a branch* → `main` basta: no hace falta ningún workflow
   nuevo y la página queda en `https://<usuario>.github.io/Data-Science_First_Proyect/historia/`.

> Los datos ya generados (`Data/clean_data/*.csv` y `*.jsonl`, `Data/metadata.json`)
> están versionados, así que la página funciona sin re-scrapear.
>
> **Opcional — regenerar los datos** (requiere red; mismo orden que usa el pipeline):
>
> ```bash
> python3 codes/scrape_triciclos.py
> python3 codes/parse_fb.py
> python3 codes/crear_canonicos.py
> python3 codes/scrape_empresas.py
> python3 codes/parse_campo.py
> python3 codes/norm_modelo.py --migrar
> python3 codes/crear_canonicos.py
> python3 codes/norm_modelo.py --migrar
> python3 codes/analisis.py
> python3 codes/analisis_campo.py
> python3 codes/sensibilidad.py
> python3 codes/generar_metadata.py
> python3 codes/generar_historia.py
> ```
>
> Al terminar, verifica la coherencia con `python3 codes/generar_metadata.py --check`
> y `python3 codes/generar_historia.py --check` (hace coincidir la historia
> con los datos); y, si instalaste `requirements-dev.txt`, ejecuta la suite
> con `python3 -m pytest -q tests/`.
>
> **Nota de reproducibilidad:** `codes/parse_campo.py` necesita
> `Data/raw_data/data_personas.txt`, que está ignorado por contener datos
> personales. Un clon público **no puede regenerar** el trabajo de campo desde
> cero; sí puede usar el `Data/registro_ubicaciones.csv` ya anonimizado.
> `codes/norm_modelo.py --migrar` normaliza a `Data/raw_data_migrado/` y solo
> pisa la copia única (clean_data/ o empresas/) si hay cambios; el modo
> destructivo requiere `--en-sitio`.

## 🧭 Qué responde y cómo se calcula

El reporte responde *¿qué triciclo comprar en La Habana y por qué?* con tres
fuentes separadas: **anuncios online** (oferta y precios), **catálogos de
empresas** (oferta formal) y **trabajo de campo** (circulación observada, que
no entra al score).

El score es una suma ponderada: precio 0.40, autonomía 0.25, carga 0.20,
legalidad 0.10, repuestos 0.05. Cada criterio se normaliza **min-max dentro de
su propulsión**. Los criterios ausentes **no se imputan**: el score se calcula
re-ponderando solo los criterios con dato y se publica `n_criterios`. Los
modelos sin `precio_usd` (catálogo en EUR) **no entran al ranking principal de
precio**; se muestran aparte con un score sin precio y un aviso de que no son
comparables. Por eso:

- **Los scores no son comparables entre propulsiones.** El reporte muestra el
  top de cada grupo, no un "mejor global".
- **El orden depende de la muestra.** 25 de 40 modelos tienen un solo anuncio
  (desde el split JINPENG del 2026-11-06, cada híbrido es n=1);
  el análisis de sensibilidad (`codes/sensibilidad.py`) mide cuánto aguanta.
- **No es una medida absoluta de calidad.** Añadir o quitar un anuncio mueve la
  escala de todo el grupo.
- **Cobertura desigual:** un score con `n_criterios = 3` no es lo mismo que uno
  con 5. La tabla muestra esa columna y el ranking permite filtrarla.

## ⚠️ Limitaciones principales

- **Oferta ≠ circulación.** Un modelo muy anunciado no es necesariamente el más
  usado en la calle.
- **Muestra de campo cerrada:** 30 observaciones en 5 de 15 municipios, de
  conveniencia y sin denominador. Describe la muestra; no se extrapola a La
  Habana. Los IC de Wilson suponen muestreo aleatorio y aquí hay conglomerados.
- **Precios EUR:** 7 modelos del catálogo VEDCA (9 fichas de islagrande y 6
  anuncios de vedca_telegram) no tienen `precio_usd`. No se inventa un tipo de
  cambio ni se imputa un precio neutro: quedan fuera del ranking principal de
  precio y se muestran aparte con un score calculado solo con los criterios
  disponibles.
- **Legalidad** = el anuncio **menciona** papeles; no verifica el trámite. No
  hay casos "no/sin" en los datos, así que mide mención publicitaria, no
  legalidad comprobada.
- **Repuestos** = proxy de presencia en más de una fuente, no stock de piezas.
- **Sensibilidad:** el top 1 y el podio cambian en varios escenarios de omisión
  (ver la página de Ranking y `Data/clean_data/sensibilidad_resumen.csv`).

## 🔐 Privacidad y ética

- No se publican carnés ni teléfonos. El test `tests/test_privacidad.py` busca
  CI de 11 dígitos, números de 8 dígitos tipo móvil o CI incompleto, `+53` y
  números tras "WhatsApp". En `legalizacion` apareció un número de 8 dígitos
  sin identificar (el texto dice `WhatsApp:`): se sustituyó por
  `[DATO PERSONAL REDACTADO]` por precaución. **No se afirma** si era teléfono
  o un CI incompleto; el texto original no lo permite decidir.
- El archivo crudo del campo (`Data/raw_data/data_personas.txt`) está ignorado
  y nunca debe commitearse. **Pendiente de decisión:** dejar de capturar nombre
  y CI en el próximo trabajo de campo; para un estudio de mercado basta un
  `obs_id`.
- `Data/raw_data/data_from_FB` es una **transcripción manual** de publicaciones
  de Facebook, no una captura automática: puede tener campos incompletos y no
  conserva el HTML original. Se documenta como fuente secundaria.
- **Scraping respetuoso:** los scrapers web usan User-Agent de navegador
  (Chrome/120), pausa de 2 s entre peticiones y backoff exponencial. El
  `robots.txt` de las 16 fuentes fue revisado el 2026-11-06 y ninguna página
  desautorizada fue scrapeada; Facebook (que prohíbe la recolección
  automatizada) solo aparece vía transcripción manual. Detalle por fuente en
  [`docs/etica_y_legal.md`](docs/etica_y_legal.md) §2a; hay un test que obliga
  a re-verificar antes de cambiar las fuentes.
- **Historial de git:** si algún dato personal estuvo en un commit anterior,
  borrarlo del HEAD no lo borra del historial. En ese caso hay que reescribir
  la historia (`git filter-repo`) o mantener el repo privado. **Sigue pendiente
  para el número de 8 dígitos de `legalizacion`.**

## 🤖 Uso de IA

Este proyecto se desarrolló con asistencia de IA (OpenCode). La declaración
completa —herramienta, tareas, qué se verificó y qué decisiones son del autor—
está en [`docs/uso_de_ia.md`](docs/uso_de_ia.md). En resumen: la IA ayudó a
escribir y revisar código, tests y documentación; el autor define la
metodología, revisa los resultados y asume la defensa oral del trabajo.

## 📜 Licencia

[MIT](LICENSE) para todo el repositorio (código, datos estructurados y
documentación): se puede reutilizar y modificar con atribución y aviso de la
licencia, sin garantías. Sobre los datos de terceros: hay que asumir los
límites de las fuentes originales y las reglas de
[`docs/etica_y_legal.md`](docs/etica_y_legal.md) (citando la fuente original
de cada anuncio; el dataset no es una enumeración completa del mercado).

