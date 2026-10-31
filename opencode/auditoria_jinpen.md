# Auditoría de identidad: JINPEN / JINPENG / JINPEING / JIMPENG

Fecha: 2026-10-31. Datos: `Data/clean_data/anuncios_triciclos.jsonl`,
`Data/modelos_canonicos.json`, `Data/clean_data/score_modelos.csv`.
No se modificó ningún dato: esta auditoría solo documenta la decisión.

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

## Por qué no se fusiona `JINPEN` con `JINPENG`

No son el mismo producto: cambian motor, batería, autonomía, carga y precio.
Fusionarlos por marca colapsaría dos fichas híbridas con specs distintas
($4.751 / 72 V · 89 Ah / 1100 W frente a $4.300 / 72 V · 58 Ah / 1500 W) y
también las separaría mal del eléctrico de 60 V · 45 Ah. La propulsión sola no
basta para distinguirlos: hay dos híbridos.

## Decisión

**No fusionar a nivel producto.** Mantener:

- marca normalizada: `JINPEN`, `JIMPENG`, `JINPEING` → `JINPENG`;
- identidad de producto: `JINPENG GELPB`, `JINPENG`, `JINPEN HIBRIDO` y
  `JINPEN`, cada una con sus specs y su URL.

Si el usuario confirma que `JINPEN` es solo una errata de marca y que los dos
híbridos son el mismo producto, el cambio debe hacerse en
`Data/modelos_canonicos.json` con un `OVERRIDE` explícito por URL, seguido de
`norm_modelo.py --migrar` y `analisis.py`. No se hace por alias automático.

## Verificación

- `tests/test_identidad.py` comprueba que `normalizar_marca("JINPEN") ==
  "JINPENG"`, que las dos identidades de producto siguen existiendo y que
  `JINPEING` no vuelve.
- `crear_canonicos.py --check` y `norm_modelo.py --check` siguen pasando.
