# 🗂️ Estructura

- 📦 **[Data-Science_First_Proyect](https://github.com/RyuDMC/Data-Science_First_Proyect)**
  - 🔧 **[`codes/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/codes)** — Scrapers, normalización, scoring, campo, sensibilidad y metadata.
  - 🗃️ **[`Data/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data)** — Datos, tabla canónica, metadata y documentación.
    - 🗄️ **[`archive/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/archive)** — Versiones históricas; ranking legado del 2026-10-11.
    - 🧹 **[`clean_data/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/clean_data)** — JSONL procesados y CSV derivados (score, campo, sensibilidad).
    - 🏢 **[`empresas/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/empresas)** — Catálogos de las 10 empresas en JSONL.
    - 🧩 **[`Estructuras/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/Estructuras)** — Esquema JSON de un anuncio.
    - 📥 **[`raw_data/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/raw_data)** — Capturas crudas de scrapers y Facebook.
  - 🖥️ **[`reporte/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/reporte)** — Aplicación Streamlit multipágina.
    - ⚙️ **[`.streamlit/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/reporte/.streamlit)** — Configuración de tema y servidor.
    - 📄 **[`pages/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/reporte/pages)** — Las 10 páginas del reporte.
  - 🧪 **[`tests/`](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/tests)** — Cifras, contratos, identidad, páginas y privacidad.
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
> ```
>
> Al terminar, verifica la coherencia con `python3 codes/generar_metadata.py --check`
> y, si instalaste `requirements-dev.txt`, ejecuta la suite con
> `python3 -m pytest -q tests/`.
>
> **Nota de reproducibilidad:** `codes/parse_campo.py` necesita
> `Data/raw_data/data_personas.txt`, que está ignorado por contener datos
> personales. Un clon público **no puede regenerar** el trabajo de campo desde
> cero; sí puede usar el `Data/registro_ubicaciones.csv` ya anonimizado.
> `codes/norm_modelo.py --migrar` escribe a `Data/raw_data_migrado/` y no toca
> `raw_data/`; el modo destructivo requiere `--en-sitio`.

## 🧭 Qué responde y cómo se calcula

El reporte responde *¿qué triciclo comprar en La Habana y por qué?* con tres
fuentes separadas: **anuncios online** (oferta y precios), **catálogos de
empresas** (oferta formal) y **trabajo de campo** (circulación observada, que
no entra al score).

El score es una suma ponderada: precio 0.40, autonomía 0.25, carga 0.20,
legalidad 0.10, repuestos 0.05. Cada criterio se normaliza **min-max dentro de
su propulsión** y los ausentes se imputan a **0.5 neutro**. Por eso:

- **Los scores no son comparables entre propulsiones.** El reporte muestra el
  top de cada grupo, no un "mejor global".
- **El orden depende de la muestra.** 23 de 38 modelos tienen un solo anuncio;
  el análisis de sensibilidad (`codes/sensibilidad.py`) mide cuánto aguanta.
- **No es una medida absoluta de calidad.** Añadir o quitar un anuncio mueve la
  escala de todo el grupo.

## ⚠️ Limitaciones principales

- **Oferta ≠ circulación.** Un modelo muy anunciado no es necesariamente el más
  usado en la calle.
- **Muestra de campo cerrada:** 30 observaciones en 5 de 15 municipios, de
  conveniencia y sin denominador. Describe la muestra; no se extrapola a La
  Habana. Los IC de Wilson suponen muestreo aleatorio y aquí hay conglomerados.
- **Precios EUR:** las 9 fichas de islagrande no tienen `precio_usd`; en el
  criterio de precio se imputan a 0.5 (no se inventa tipo de cambio).
- **Legalidad** = el anuncio menciona papeles; no verifica el trámite. No hay
  casos "no/sin" en los datos.
- **Repuestos** = proxy de presencia en más de una fuente, no stock de piezas.
- **Sensibilidad:** el top 1 y el podio cambian en varios escenarios de omisión
  (ver la página de Ranking y `Data/clean_data/sensibilidad_resumen.csv`).

## 🔐 Privacidad y ética

- No se publican carnés ni teléfonos. El test `tests/test_privacidad.py` busca
  CI de 11 dígitos, números de 8 dígitos tipo móvil o CI incompleto, `+53` y
  números tras "WhatsApp". En `legalizacion` apareció un CI mal escrito de 8
  dígitos: se sustituyó por `[DATO PERSONAL REDACTADO]`.
- El archivo crudo del campo (`Data/raw_data/data_personas.txt`) está ignorado
  y nunca debe commitearse.
- Los anuncios de Facebook se capturan con un User-Agent de navegador. Antes de
  reutilizar el scraper, revisa los términos de la plataforma y `robots.txt`.
- **Historial de git:** si algún dato personal estuvo en un commit anterior,
  borrarlo del HEAD no lo borra del historial. En ese caso hay que reescribir
  la historia (`git filter-repo`) o mantener el repo privado.

## 📜 Licencia

Pendiente de decisión del autor. Sin una licencia explícita, el repositorio
queda bajo "todos los derechos reservados" y no puede reutilizarse legalmente.

