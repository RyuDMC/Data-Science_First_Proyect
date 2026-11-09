# Ética, privacidad y legalidad del scraping

Este proyecto es público y usa datos de terceros. Este documento fija qué se
hace, qué no se hace y qué queda pendiente. No sustituye una revisión legal.

## 1. Datos personales

- **Trabajo de campo:** la hoja original (`Data/raw_data/data_personas.txt`)
  contiene nombre y carné de identidad. Está **ignorada por git** y
  `codes/parse_campo.py` la anonimiza: descarta nombre y CI y conserva solo
  `obs_id`, municipio, uso, marca y specs del vehículo.
- **Anuncios:** se publican URLs de publicaciones y texto de `legalizacion`.
  Ese texto puede incluir teléfonos, carnés o nombres de vendedores. En
  `legalizacion` apareció un **número de 8 dígitos sin identificar** precedido
  de `WhatsApp:`. Se sustituyó por `[DATO PERSONAL REDACTADO]` por precaución.
  **No se afirma** que sea un teléfono ni un CI: el texto original no permite
  decidirlo. `tests/test_privacidad.py` bloquea CI de 11 dígitos, números de 8
  dígitos tipo móvil o CI incompleto, `+53` y números tras "WhatsApp".
- **Transcripción de Facebook:** `Data/raw_data/data_from_FB` es texto
  transcrito a mano desde publicaciones, no una captura automática. No
  conserva el HTML original y puede tener campos incompletos; se trata como
  fuente secundaria y así se declara en el README.
- **Regla:** si un dato identifica a una persona y no es imprescindible para la
  pregunta de mercado, no se publica. En el próximo campo, **no se captura
  nombre ni CI**: basta un `obs_id` y los datos del vehículo.

## 2. Scraping

- Los dos scrapers web (`codes/scrape_triciclos.py`, `codes/scrape_empresas.py`)
  comparten un User-Agent de navegador identificado (Chrome/120, desktop),
  pausa de `REQUEST_DELAY = 2 s` entre peticiones y backoff exponencial
  (`sleep(2 ** intento)`) en fallos transitorios. No se elude autenticación ni
  se consulta ningún endpoint /api/.
- Los anuncios de Facebook **no se scrapean**: provienen de transcripción
  manual (`Data/raw_data/data_from_FB`, formato `clave: valor`) que `parse_fb.py`
  convierte a JSONL. Las URL sirven como referencia de la publicación, no como
  página capturada.
- **Revisión de robots.txt y ToS (2026-11-06):** se comprobó el `robots.txt` de
  los 14 dominios usados y se contrastó con las rutas que aparecen en los
  datos. La tabla completa está en la sección 2a; ninguna fuente con
  restricciones fue scrapeada. Puntos a destacar:
  - `www.facebook.com` declara en la cabecera de su robots.txt que la
    recolección automatizada está prohibida sin permiso escrito, y desautoriza
    `/share/` y `/groups`-adjacentes. Por eso los 29 anuncios de Facebook del
    dataset son transcripción manual.
  - `t.me` no publica robots.txt (404 al comprobar); la captura de `t.me/s/<canal>`
    es la vista web pública del canal, antes de reutilizar hay que revisar los
    ToS de Telegram.
  - Re-ejecutar los scrapers exige reponer esta comprobación (hay un test que
    obliga a que la documentación cubra cada dominio en uso).
- **No hacer:** eludir autenticación, capturar datos privados, martillear un
  servidor sin pausas o revender los datos.

### 2a. Revisión por fuente (2026-11-06)

Siete dominios de anuncios + diez catálogos. `Rutas usadas` son las que
aparecen en los JSONL. "OK" = las rutas usadas no están desautorizadas.

| Dominio | Páginas usadas (n) | robots.txt | Veredicto |
|---|---|---|---|
| elyerromenu.com | /b/… (16) | `User-agent: * Disallow:` (vacío) + 17 sitemaps | OK: sin restricciones |
| islagrande.com | /triciclo-*.html (9) | Magento: `/catalog/`, `/*?`, `/checkout/`… | OK: las fichas usadas están fuera de /catalog/ y sin query strings |
| habana.casalindashop.com | /triciclo-*.html (5) | 200 con contenido **vacío** (comprobado con el UA del scraper) | OK: sin directivas |
| cubancargos.com | /triciclos (4) | `Disallow: /api/, /checkout/, /link/`… | OK: no aplican |
| t.me | /s/<canal> (7) | 404 (no publicado) | Permitido por defecto; revisar ToS de Telegram antes de reutilizar |
| francismotors.org | /triciclos (11) | `Disallow: /admin/, /api/, /catalogo/` | OK: usa /triciclos, no /catalogo/ |
| patuisla.com | /producto (11) | WooCommerce/Yoast: logs y add-to-cart | OK: no aplican |
| mundoenvio.com | /tienda (10) | Yoast `Disallow:` (vacío) | OK: sin restricciones |
| kikihabana.com | /producto (9) | WooCommerce: add-to-cart, /wp-admin/ | OK: no aplican |
| compramasonline.com | /tienda (7) | WooCommerce: /wp-admin/ | OK: no aplican |
| www.mzproducts.com | /producto (7) | `User-agent: * Allow: /` + sitemaps | OK: sin restricciones |
| www.acubaenvioscargo.com | /categoria-producto, /tienda (4) | WooCommerce: add-to-cart, logs | OK: no aplican |
| mrcubamiami.com | /… (2) | 404 (no publicado) | Permitido por defecto |
| zonalibreonline.com | /product (2) | WooCommerce: add-to-cart, logs | OK: no aplican |
| bluewavecuba.com | /triciclos (1) | `Allow: /`, `Disallow: /admin/` | OK |
| www.facebook.com | /groups, /share/p (29) | Notice: recolección automatizada prohibida sin permiso escrito; `Disallow: /share/`, `/share.php`… | **NO scrapeado**: solo transcripción manual |

Método de la comprobación: `robots.txt` de cada dominio obtenido el
2026-11-06 con `requests` usando el mismo User-Agent del scraper, y contraste
manual de cada patrón `Disallow:` con las rutas presentes en los datos. No se
automatizó `robotparser` porque los bloques WooCommerce dependen de su
contexto; el detalle está en la tabla. Este archivo se re-verifica con el test
`test_documentacion_cubre_las_fuentes` (`tests/test_contratos.py`).

## 3. Sesgo y consentimiento

- La muestra de campo es de **conveniencia**, no probabilística. Los dueños
  entrevistados no firmaron un consentimiento documentado en el repo.
- **Pendiente:** si se reabre el trabajo de campo, usar un consentimiento
  verbal/informado registrado y un diseño muestral con denominador.

## 4. Historia de git

Borrar un dato personal (teléfono o CI) del HEAD **no lo borra de commits
anteriores**. Si el dato estuvo versionado:

```bash
# Opción A: reescribir la historia (coordinar con colaboradores)
git filter-repo --path Data/raw_data/anuncios_triciclos.jsonl --invert-paths
# o una sustitución dirigida con git filter-repo --replace-text

# Opción B: mantener el repo privado hasta limpiar
```

Después de reescribir, hay que forzar el push y avisar a quien tenga clones.

## 5. Licencia

Existe `LICENSE` desde el 2026-11-08 (decisión del autor): **MIT único** para
todo el repositorio — código, datos estructurados y documentación —, con la
condición estándar de atribución y aviso de licencia y sin garantías. Para los
datos recopilados de terceros, la nota final del `LICENSE` remite a este
documento: quien reutilice debe citar la fuente original de cada anuncio y
respetar el resto de las reglas (no presentar el dataset como enumeración
completa del mercado).
