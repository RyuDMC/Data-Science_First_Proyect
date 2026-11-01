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
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
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
