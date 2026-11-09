# Auditoría de identidad: JINPEN / JINPENG / JINPEING / JIMPENG

Fecha: 2026-10-31. Datos: `Data/clean_data/anuncios_triciclos.jsonl`,
`Data/modelos_canonicos.json`, `Data/clean_data/score_modelos.csv`.
No se modificó ningún dato: esta auditoría solo documenta la decisión.

> **Estado final (mismo día):** el usuario revocó la separación — JIMPEG y
> JINPEN son erratas de JINPENG y el híbrido es JINPENG. Ver la sección
> "Decisión" y "Resultado" más abajo; las secciones iniciales quedan como
> registro del análisis que condujo a la pregunta.

## Los cuatro registros

| Identidad actual | Modelo declarado | Marca | Propulsión | Specs declaradas | Precio | Fuente / URL |
|---|---|---|---|---|---|---|
| `JINPENG GELPB` | JINPENG | JINPENG | eléctrico | 60 V · 45 Ah; 70 km; 600 kg | $3.300 | elyerromenu: `triciclo-marca-jinpeng` |
| `JINPENG` | JINPENG | JINPENG | híbrido | 1100 W; 72 V · 89 Ah | $4.751 | cubancargos: `triciclo-jeinpeing` |
| `JINPEN HIBRIDO` | JINPEN HIBRIDO | JINPEN | híbrido | 1000 W + extensor 4500 W; 60 V · 32 Ah | $3.800 | elyerromenu: `triciclo-jinpen-hibrido` |
| `JINPEN` | (sin modelo) | JINPEN | híbrido | 1500 W + extensor 5000 W; 72 V · 58 Ah; 100 km; 850 kg | $4.300 | elyerromenu: `triciclo-jimpeng-hibrido-2026` |

Las páginas de origen usan cuatro grafías: **JINPENG**, **Jinpen**,
**Jimpeng** y **JINPEING**. La errata `JINPEING` ya se corrigió a `JINPENG`
(confirmada por el usuario el 2026-10-31).

## Lo que ya está resuelto

- `codes/norm_modelo.py` tiene `MARCA_ALIAS` con `JINPEN → JINPENG` y
  `JIMPENG → JINPENG`: a **nivel marca**, las cuatro fichas son la misma marca.
- La identidad de **producto** no se fusiona: `identidad()` usa el nombre de
  modelo cuando existe y, si no, la marca declarada. Por eso `JINPEN` sigue
  apareciendo como identidad del producto sin modelo.
- `JINPEING` está en `ALIAS_MODELOS` y en `OVERRIDES` por URL; no queda ninguna
  fila con esa grafía en el ranking.

## Por qué no se fusiona `JINPEN` con `JINPENG` (histórico — la postura cambió)

> Cambio de postura el mismo día: el usuario decidió fusionar. Los motivos en
> favor de la separación (specs distintas) quedaron resueltos compartiendo
> **identidad** pero no **fichas**: las URLs siguen separadas con sus specs y
> el score agrega con la mediana.

No son el mismo producto: cambian motor, batería, autonomía, carga y precio.
Fusionarlos por marca colapsaría dos fichas híbridas con specs distintas
($4.751 / 72 V · 89 Ah / 1100 W frente a $4.300 / 72 V · 58 Ah / 1500 W) y
también las separaría mal del eléctrico de 60 V · 45 Ah. La propulsión sola no
basta para distinguirlos: hay dos híbridos.

## Decisión

**Fusionar a nivel producto (decisión final del usuario, 2026-10-31).**
"JIMPEG es errata de JINPENG y JINPEN híbrido también — ahí debe ir
JINPENG." Aplicado en el origen, no por alias automático:

- marca normalizada (`MARCA_ALIAS`): `JINPEING`, `JEINPEING`, `JIMPEG`,
  `JIMPENG`, `JINPEN` → `JINPENG`;
- nombres por URL (`OVERRIDES` en `codes/crear_canonicos.py`):
  - `triciclo-jinpen-hibrido` → modelo `JINPENG`, marca `JINPENG`;
  - `triciclo-jimpeng-hibrido-2026` → modelo sin nombre (como estaba) con
    marca `JINPENG`;
  - Facebook `permalink/1155238560180164` → modelo `JINPENG PANTER 2026`
    (antes "JIMPEG PANTER 2026");
  - Facebook `share/p/19rdffanLu` → modelo `TY150UK` intacto, marca
    `JINPENG` (antes "JIMPENG");
- `codes/parse_fb.py` (capa protectora): `jimpeg`/`jimpeng` → `JINPENG` y
  "jimpeg panter 2026" → JINPENG PANTER 2026;
- followed by `norm_modelo.py --migrar`, `analisis.py` y suite.

## Resultado (2026-10-31)

| Identidad | Propulsión | n anuncios | Especs agregadas (mediana) | Precio |
|---|---|---|---|---|
| `JINPENG GELPB` | eléctrico | 1 | 60 V · 45 Ah; 70 km; 600 kg | $3.300 |
| `JINPENG` | híbrido | 3 | 1100 W + extensor; 100 km; 850 kg | $4.300 |

- El híbrido comparte identidad (no specs): las fichas siguen separadas por
  URL con Motor 1000/1100/1500 W y baterías 32/58/89 Ah.
- Con el agregado, `JINPENG` híbrido (n=3, 5 criterios) pasa a tener el
  **mayor score del CSV** (0.883), aunque **no es comparable con los
  eléctricos**: cada propulsión se normaliza por separado. El eléctrico sigue
  liderado por TOPMAQ BRIDERK 2026 GELPB (0.786). Ranking: 40 → 38 filas,
  39 → 37 nombres; `repuestos_proxy` 9 → 10 (el híbrido ahora se anuncia en 2
  fuentes).
- Guarda: `tests/test_identidad.py::test_grupo_jinpeng_esta_unificado` y el
  escáner de erratas en `test_no_quedan_erratas_en_el_ranking`.

## Verificación

- `tests/test_identidad.py` comprueba que las cinco grafías erratas
  normalizan a `JINPENG`, que la identidad híbrida agrega 3 anuncios y que
  `JINPEN`/`JIMPEG` no quedan ni en el ranking ni en la tabla canónica.
- `crear_canonicos.py --check`, `norm_modelo.py --check` y la suite 36/36
  pasan tras la migración.

## 3ª pasada (2026-11-06): el híbrido agregado se divide en 3 filas

**Decisión del usuario** ("Dividir en 3 filas"): la fila `JINPENG` híbrido
(n=3) mezclaba tres fichas con specs incompatibles. El agregado con mediana
mostraba un producto que nadie vende: baterías 32/58/89 Ah en una misma fila.
Se mantiene la unificación de MARCA (erratas bloqueadas por test) y se
separa el nivel producto.

Materialización (re-ejecutable, sin URLs a mano en CSV):

- `codes/crear_canonicos.py` `OVERRIDES` por URL (la tabla curada "manda
  siempre" en `canonizar`), nombres que citan la spec real de cada ficha:
  - `triciclo-jinpen-hibrido` (elyerromenu) → `JINPENG HIBRIDO 1000W`
    (1000 W / 60 V 32 Ah, $3800, extensor 4500 W);
  - `triciclo-jimpeng-hibrido-2026` (elyerromenu) → `JINPENG HIBRIDO 1500W`
    (1500 W / 72 V 58 Ah, 100 km, 850 kg, $4300, extensor 5000 W);
  - `triciclo-jeinpeing` (cubancargos) → `JINPENG HIBRIDO 1100W`
    (1100 W / 72 V 89 Ah, $4751, garantía 1 mes de baterías);
- `norm_modelo.py --migrar --en-sitio` reescribe la copia única
  (`clean_data/anuncios_triciclos.jsonl`, unificada ese mismo día con la
  reestructuración raw/clean): diff = solo esas 3 filas;
- regeneración de `analisis.py`, `analisis_campo.py`, `sensibilidad.py`,
  `generar_metadata.py` y exámenes `--check` en verde.

**Excepción al contrato de nombres.** El repo prohíbe terminaciones
`numero+unidad` (`tests/test_identidad.py`, en pantalla y en los JSONL).
Es la única vía honesta de distinguir las 3 fichas sin inventar: los slugs
son erratas bloqueadas y los títulos reales no atan cada ficha a su spec.
Excepción cerrada (`SPEC_EN_NOMBRE_PERMITIDAS`) con las 3 cadenas exactas,
referenciada desde `OVERRIDES`; cualquier nombre-nuevo-con-spec sigue
bloqueado.

**Efectos en cifras (2026-11-06):**

| Concepto | Antes | Ahora |
|---|---|---|
| Filas del ranking | 38 | 40 |
| Nombres únicos | 37 | 39 |
| Anuncios n=1 | 23 | 25 |
| Precio comparable | 31 (+7 sin precio) | 33 (+7) |
| `repuestos_proxy` | 10 | 9 |
| Mejor híbrido por score | `JINPENG` 0.883 (n=3) | `HIBRIDO 1000W` 0.909 (n_criterios=3; `1500W` 0.707 con 5 criterios) |

- El top por score exige ≥3 criterios presentes: `1000W` y `1500W` pasan.
  `score_imputado` (0.5) sigue como referencia histórica (0.725/0.475 para
  las filas con 3 criterios).
- `repuestos_proxy` 10→9: el agregado acreditaba "más de una fuente" a tres
  productos distintos; ahora cada híbrido es de una sola fuente y el proxy
  vuelve a medir identidad con ≥2 fuentes.
- Guardas: `test_grupo_jinpeng_hibrido_son_3_filas` (sustituye a
  `test_grupo_jinpeng_esta_unificado`), `SPEC_EN_NOMBRE_PERMITIDAS` y los
  contratos de conteos en `tests/test_contratos.py` (40 filas, 33 con
  precio, 9 proxy).

## Verificación (2026-11-06)

- Suite 48/48; `crear_canonicos --check`, `generar_metadata --check`,
  `sensibilidad --check` OK; `compileall` OK; AppTest de las 11 páginas sin
  excepciones.
