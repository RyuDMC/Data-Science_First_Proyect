# Triciclos La Habana

Análisis de datos de la oferta y la circulación de triciclos en La Habana.

**Pregunta:** ¿qué triciclo comprar en La Habana y por qué?

`Python` · `Pandas` · `Streamlit` · `Matplotlib`

---

## Vista general

| Fuente | Qué mide | Registros |
|---|---|---:|
| Anuncios online | Oferta y competencia de precios | 70 anuncios · 41 modelos |
| Catálogos de empresas | Oferta formal y disponibilidad | 68 fichas · 10 empresas |
| Trabajo de campo | Circulación observada en calle | 30 observaciones · 5 municipios |

El trabajo de campo es una **muestra cerrada** (13–25 oct 2026, 5 de 15 municipios): describe lo observado, no toda La Habana. "Lo más común" se usa como indicador, no como respuesta.

## Reporte

Reporte interactivo de 10 páginas:

1. Resumen ejecutivo
2. Método y pesos
3. Mercado
4. Ranking
5. Precio / autonomía / carga
6. Contendientes
7. Mejor opción por escenario
8. Trabajo de campo
9. Catálogos de empresas
10. Limitaciones

## Estructura

| Árbol | Descripción | URL |
|---|---|---|
| `codes/` | Scripts del pipeline: scraping, parsing, identidad, scoring, campo, sensibilidad y metadata. | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/codes) |
| `Data/` | Datos del proyecto, tabla canónica, metadata y documentación de datos. | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data) |
| `├── archive/` | Versiones históricas; hoy solo el ranking legado del 2026-10-11. | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/archive) |
| `├── clean_data/` | JSONL procesados (anuncios y empresas) y CSV derivados (score, campo, sensibilidad). | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/clean_data) |
| `├── empresas/` | Catálogos scrapeados de las 10 empresas, en JSONL. | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/empresas) |
| `├── Estructuras/` | Esquema JSON de un anuncio y sus campos. | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/Estructuras) |
| `└── raw_data/` | Capturas crudas de los scrapers y de Facebook. | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Data/raw_data) |
| `reporte/` | Aplicación Streamlit: `app.py`, `data.py`, `theme.py` y páginas. | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/reporte) |
| `├── .streamlit/` | Configuración de tema y servidor del reporte. | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/reporte/.streamlit) |
| `└── pages/` | Las 10 páginas del reporte (Resumen, Método, Ranking, Campo…). | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/reporte/pages) |
| `tests/` | Pruebas de cifras, contratos, identidad, páginas y privacidad. | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/tests) |
| `opencode/` | Handoff, diario de trabajo y auditoría de identidad JINPEN. | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/opencode) |
| `Prompts/` | Prompts e instrucciones con los criterios del proyecto. | [abrir](https://github.com/RyuDMC/Data-Science_First_Proyect/tree/main/Prompts) |

En la raíz: [`requirements.txt`](https://github.com/RyuDMC/Data-Science_First_Proyect/blob/main/requirements.txt) (pipeline + reporte), [`requirements-dev.txt`](https://github.com/RyuDMC/Data-Science_First_Proyect/blob/main/requirements-dev.txt) (tests) y [`.gitignore`](https://github.com/RyuDMC/Data-Science_First_Proyect/blob/main/.gitignore) (entorno y PII).

## Uso

```bash
# entorno
python3 -m venv reporte/.venv
source reporte/.venv/bin/activate
pip install -r requirements.txt      # pipeline + reporte (versiones exactas)

# solo el reporte (lo usa Streamlit Cloud)
pip install -r reporte/requirements.txt

# reporte
streamlit run reporte/app.py
```

Pipeline completo para regenerar los datos:

```bash
python3 codes/scrape_triciclos.py
python3 codes/parse_fb.py
python3 codes/crear_canonicos.py      # fija los nombres canónicos
python3 codes/scrape_empresas.py
python3 codes/parse_campo.py
python3 codes/norm_modelo.py --migrar
python3 codes/crear_canonicos.py      # consolida tras la migración
python3 codes/norm_modelo.py --migrar
python3 codes/analisis.py
python3 codes/analisis_campo.py
python3 codes/sensibilidad.py         # robustez del ranking (no altera el score)
python3 codes/generar_metadata.py     # conteos, cortes y resultados -> Data/metadata.json
```

`Data/metadata.json` es la **única fuente de las cifras** que muestran el reporte y el README (70 anuncios, 41 modelos, 68 fichas, 30 observaciones, cortes, top-3 por propulsión y marca de calle). Se genera al final del pipeline; no se edita a mano y es determinista (la fecha/commit solo se añaden con `--procedencia`). Si los datos cambian, se regenera y los tests avisan de cualquier desincronización:

```bash
python3 codes/generar_metadata.py --check   # falla si metadata.json está desactualizado
pip install -r requirements-dev.txt
python -m pytest -q tests/
```

## Metodología

Score ponderado de "mejor opción":

| Criterio | Peso |
|---|---:|
| Precio | 0.40 |
| Autonomía | 0.25 |
| Carga | 0.20 |
| Legalidad | 0.10 |
| Repuestos | 0.05 |

- Normalización min-max **dentro de cada propulsión**; los valores ausentes usan 0.5 neutro y se exponen en `n_criterios`.
- Los scores **no se comparan entre propulsiones**.
- La identidad de cada producto vive en `Data/modelos_canonicos.json` (clave: URL) y no se edita a mano en los JSONL.
- Rangos declarados → límite inferior; un dato no declarado queda en `null`.

## Resultados

Corte: anuncios 2026-10-19 · catálogos 2026-10-31 · campo 2026-10-25.

- Mejor score **eléctrico**: **TOPMAQ BRIDERK 2026 GELPB** (0.786), seguido de **ONEBOT CLASIC 2026** (0.775) y **KIVITOVA GELPB** (0.723).
- En calle, la marca más observada es **JINPENG** (20%, 6 de 30; IC95 9.5–37.3%).
- Ningún modelo de catálogo coincide con un anuncio; a nivel de marca cruzan **ONEBOT, TOPMAQ, VEDCA y MISHOZUKI**.

## Fuentes

**Anuncios online:** elyerromenu, islagrande, vedca_telegram, casalindashop, cubancargos y Facebook.

**Catálogos de empresas:** KikiHabana, MZ Products, A Cuba Envíos Cargo, Mr Cuba, CompraMasonline, MundoEnvío, Patuisla, Francis Motors, Bluewave Logistic y Zona Libre Online.

## Datos y privacidad

- `Data/clean_data/` se genera desde los scrapers y las tablas de análisis.
- Los datos personales del trabajo de campo (`Data/raw_data/data_personas.txt` y sus variantes `*personas*`) **no están en el repositorio** y están cubiertos por `.gitignore`.
- `tests/test_privacidad.py` falla si aparece un número de 11 dígitos (carné de identidad) en archivos versionados.
- Para cambiar un nombre o una variante: `codes/crear_canonicos.py` → `codes/norm_modelo.py --migrar` → `codes/analisis.py`.
- Tras cambiar datos o nombres: regenerar `Data/metadata.json` y ejecutar `pytest -q tests/`.

## Limitaciones

- Oferta declarada ≠ circulación real.
- Muestra pequeña: 41 modelos (muchos con n=1) y 30 observaciones de campo en 5 de 15 municipios.
- Las fuentes online no cubren todo el mercado informal ni todas las MIPYMEs.
- `vedca.cu` está caído; su cobertura es parcial.
- El proxy de repuestos está activo en 9 de 41 modelos y mide presencia, no stock.

## Documentación

- `Data/fuentes_justificacion.md` — justificación de los pesos.
- `Data/resumen_pesos_scoring.md` — resumen metodológico.
- `opencode/HANDOFF.md` — estado y decisiones del proyecto.
- `opencode/Journaing_file.md` — diario de trabajo.
