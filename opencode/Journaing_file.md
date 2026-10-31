# JOURNAL — Diario operativo

Memoria episódica del agente. Consultar antes de actuar; escribir solo después de actuar. Formato de consulta: "Consulta de diario: [criterio]. Entradas relevantes: [resumen]. Aplicaré: [acción]."

Fuente del protocolo: `Prompts/Journaling Prompt.md`.

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-05 — sesión en opencode; activación del protocolo de journaling sobre el clon real (disco externo `17bd76d4`)
- **Tarea:** Activar el protocolo de journaling y crear un diario nuevo en `Data/Journaing_file.md`
- **Acción(es):** Leído `Prompts/Journaling Prompt.md`; detectado que el clon de trabajo real está en el disco externo (tiene `.git`) y no en `~/Projects`; verificado `git status` limpio; confirmado que el diario previo se borró a propósito en el commit pusheado `30a210f` ("removing Journaling"); creado este diario vacío, sin arrastrar las 14 entradas del anterior
- **Resultado:** Diario nuevo creado y protocolo activo para el resto de la sesión
- **Error/éxito:** Éxito, con un paso perdido: se clonó el repo en `~/Projects/Data-Science` asumiendo que ahí vivía el proyecto; el proyecto real estaba en el disco externo
- **Lección:** Antes de clonar o crear archivos de proyecto, localizar el clon real por `.git`. Un clon nuevo en otro sitio es una copia divergente, no la fuente de verdad
- **Próxima vez:** Ante una ruta de proyecto, verificar primero si es un repo y cuál es su remoto, antes de escribir. Considerar `AGENTS.md` en la raíz del proyecto para que el protocolo sobreviva al reinicio de sesión
- **Etiquetas:** setup, journaling, infraestructura, git, disco-externo, ubicacion

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-05 — sesión en opencode; tras leer `Prompts/handoff_prompt.md`
- **Tarea:** Fijar cuándo se genera el documento de handoff y dónde se guarda
- **Acción(es):** Leído el prompt de handoff (5 secciones: Contexto, Estado actual, Pendiente, Recursos, Advertencias; máx. una página; sin inventar). Registrada la instrucción del usuario: el handoff **solo** se genera al finalizar la sesión, como archivo en `Data/`
- **Resultado:** Regla de escritura acordada: nada de handoff durante la sesión; al cerrar, un archivo nuevo en `Data/` (probablemente `Data/HANDOFF.md`, el nombre que el repo ya usó antes). Queda pendiente de ejecutar
- **Error/éxito:** Éxito
- **Lección:** El handoff y el diario resuelven problemas distintos y no se mezclan: el diario es memoria persistente entrada por entrada, el handoff es una foto de cierre para otra IA. Generar el handoff antes de terminar lo convierte en una foto con trabajo a medias
- **Próxima vez:** Al abrir sesión, leer este diario y comprobar si quedó un `HANDOFF.md` pendiente de retomar
- **Etiquetas:** handoff, journaling, protocolo, cierre-de-sesion, convenciones

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-05 — sesión en opencode; limpieza tras activar el protocolo
- **Tarea:** (1) borrar el clon sobrante `~/Projects/Data-Science`; (2) decidir sobre las 14 entradas del diario anterior
- **Acción(es):** Verificado `git status --porcelain` del clon sobrante antes de borrar (única diferencia: el `Data/Journaing_file.md` que yo mismo había eliminado ahí). Ejecutado `rm -rf ~/Projects/Data-Science`. Punto 2 decidido por el usuario: **no** recuperar las entradas de `3ee4f6b`; el diario nuevo sigue empezando desde cero
- **Resultado:** `~/Projects` vuelve a estar vacío. El repo real en el disco externo queda como única copia de trabajo
- **Error/éxito:** Éxito. Sin pérdida: el clon borrado era redundante y todo su contenido es recuperable del remoto público
- **Lección:** Antes de clonar un proyecto hay que localizar su copia real (por `.git`). Clonar primero genera una copia divergente que hay que limpiar después, y el nombre del repo no dice en qué disco está
- **Próxima vez:** Ante una ruta de proyecto, `ls` + buscar `.git` antes de clonar o escribir. No proponer recuperar historia borrada salvo que el usuario lo pida (ya se decidió: el diario empieza limpio). Tampoco proponer `AGENTS.md`: el usuario lo rechazó explícitamente; el protocolo se aplica en sesión, sin archivo de arranque
- **Etiquetas:** limpieza, git, clon-divergente, ubicacion, decision

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-05 — sesión en opencode; diseño e implementación del proyecto triciclos La Habana
- **Tarea:** Crear scripts de scraping y análisis para el proyecto de mercado de triciclos en La Habana
- **Acción(es):** 
  1. Definido estructura de datos: CSV para inventario municipal (15 municipios, sin hora), JSONL para anuncios online
  2. Aprobados criterios de "mejor" con pesos: precio 0.4, autonomía 0.25, carga 0.2, legalidad 0.1, repuestos 0.05
  3. Creado `scrape_triciclos.py` (416 líneas): scrapea Revolico + 3 tiendas WooCommerce (KikiHabana, CubanCargos, CompraMás), visita detalle de cada anuncio, extrae 17 campos, guarda JSONL
  4. Creado `analisis.py`: carga ambos datasets, calcula score ponderado, compara campo vs online, genera CSVs de salida
  5. Actualizado `registro_ubicaciones.csv` con nueva cabecera (inventario municipal)
- **Resultado:** Infraestructura lista. Pendiente: instalar bs4 y ejecutar scraping, luego trabajo de campo en 15 municipios
- **Error/éxito:** Éxito en creación de archivos. bs4 no instalado (entorno externally-managed), usuario lo hará
- **Lección:** Separar inventario municipal (espacial) de conteo horario fue clave para ajustar a 8h reales. JSONL es mejor que CSV para anuncios por campos variables y nulables.
- **Próxima vez:** Usuario instala bs4 (`pip install beautifulsoup4 --break-system-packages` o en venv), ejecuta `python3 scrape_triciclos.py`, luego hace trabajo de campo 3 rutas × 5 municipios, finalmente `python3 analisis.py`
- **Etiquetas:** triciclos, scraping, analisis, implementacion, jsonl, csv, pesos, habana

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-05 — sesión en opencode; corrección: añadir triciclos de combustión al scraper
- **Tarea:** El usuario notó que el scraper original solo cubría eléctricos; había que incluir gasolina
- **Acción(es):**
  1. Revisado `Data/Posibles fuentes de datos.md`: KikiHabana tiene categoría "motos-de-gasolina-y-electrica", Revolico tiene subcategory distinta para gasolina
  2. Actualizado `scrape_triciclos.py` (561 líneas): 8 fuentes ahora (3 Revolico: eléctrico, gasolina, vehículos de trabajo; 2 KikiHabana: eléctrico y gasolina; CubanCargos, CompraMás, elyerromenu)
  3. Añadido campo `propulsion` (electrico/gasolina/indeterminado) y `motor_cc` para combustión
  4. Función `detect_propulsion()` combina hint de URL + palabras clave en título/descripción
  5. Actualizado `analisis.py`: agrupa score por propulsión, normaliza min-max dentro de cada grupo, estima autonomía burda para gasolina (cc/10 * 3 * 12L)
  6. Salidas CSV ahora incluyen columna `propulsion` en todas las tablas
- **Resultado:** Infraestructura lista para ambos tipos. Pendiente: instalar bs4 y ejecutar
- **Error/éxito:** Éxito en refactor. La estimación de autonomía para gasolina es muy aproximada y se documenta como tal
- **Lección:** En Cuba los triciclos de gasolina (CG200, GY6, 150-250cc) son mercado aparte del eléctrico; mezclararlos en un solo ranking distorsiona. Separar por propulsión en el scoring es correcto.
- **Próxima vez:** Usuario instala bs4, ejecuta scraper, verifica que salen ambos tipos en el resumen final ("Por propulsión: electrico: X, gasolina: Y")
- **Etiquetas:** triciclos, combustion, gasolina, scraping, refactor, propulsion

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-05 — sesión en opencode; cierre de sesión tras implementar infraestructura completa del proyecto triciclos La Habana
- **Tarea:** Finalizar sesión: generar handoff, reflexión final, cerrar diario
- **Acción(es):**
  1. Protocolo de journaling activado desde el inicio (3 entradas previas + esta)
  2. Repo real identificado en disco externo `/run/media/ryudmc/17bd76d4-.../Oliver/Study/DS Proyects/Data-Science`
  3. Creados 3 archivos base en `Data/`:
     - `registro_ubicaciones.csv` — hoja de inventario municipal (11 campos, 15 municipios, sin hora)
     - `scrape_triciclos.py` (561 líneas) — scraper 8 fuentes (3 Revolico, 2 KikiHabana, CubanCargos, CompraMás, elyerromenu), detecta propulsión (electrico/gasolina), extrae 17 campos, guarda JSONL
     - `analisis.py` (245 líneas) — carga campo + online, score ponderado por propulsión (pesos: precio 0.4, autonomía 0.25, carga 0.2, legalidad 0.1, repuestos 0.05), compara frecuencias, genera 4 CSVs salida
  4. Diario actualizado con 4 entradas completas (formato verificado 8/8 campos)
  5. Usuario rechaza `AGENTS.md`; decide no recuperar diario anterior (14 entradas en commit `3ee4f6b`)
  6. Clon sobrante en `~/Projects/Data-Science` eliminado
- **Resultado:** Infraestructura lista para ejecutar. Pendiente por usuario: instalar bs4, ejecutar scraper, trabajo de campo 8h (3 rutas × 5 municipios), ejecutar análisis
- **Error/éxito:** Éxito. Sin datos ejecutados aún (solo infraestructura). bs4 no instalado (externally-managed-environment), usuario lo hará
- **Lección:** Separar inventario municipal (espacial) de conteo horario fue clave para ajustar a 8h reales. Separar scoring por propulsión (eléctrico vs gasolina) evita comparar peras con manzanas. JSONL supera a CSV para anuncios por campos variables/nulables.
- **Próxima vez:** 
  1. `pip install beautifulsoup4 --break-system-packages` (o en venv)
  2. `python3 scrape_triciclos.py` → verifica resumen "Por propulsión: electrico: X, gasolina: Y"
  3. Trabajo de campo: 3 días × ~2.5h = 15 municipios, rellenar `registro_ubicaciones.csv`
  4. `python3 analisis.py` → genera `score_modelos.csv`, `comparacion_campo_online.csv`, `frecuencia_por_municipio.csv`, `frecuencia_por_tipo_uso.csv`
  5. Redactar reporte final en `Data/reporte_triciclos_2026-10-XX.md`
- **Etiquetas:** cierre, handoff, triciclos, implementacion, completa, sesion

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-07 — sesión en opencode; debugging scraping: Cloudflare en Revolico, DNS fail en KikiHabana/CompraMás
- **Tarea:** El usuario reporta que el scraping no extrajo ningún registro
- **Acción(es):**
  1. Verificado estado: bs4 instalado OK, pero fuentes tienen problemas:
     - Revolico: 403 Cloudflare ("Just a moment...")
     - KikiHabana: DNS fail (no resuelve kikihabana.com)
     - CompraMás: DNS fail (no resuelve compramasonline.com)
     - elyerromenu: responde 200 pero sin triciclos visibles
     - **CubanCargos: FUNCIONA** (200, productos en /triciclos/electricos-cuba/ y /triciclos/gasolina-cuba/)
  2. Analizada estructura CubanCargos: Tailwind CSS, productos en `<a class="group relative flex flex-col...">` con `<h3>` y href `/triciclos/.../`
  3. Detalle de producto tiene specs en texto: motor (W/cc), batería (V Ah), carga (kg), autonomía (km)
- **Resultado:** Solo CubanCargos es viable ahora. Revolico necesita bypass (Playwright/Selenium o API alternativa). KikiHabana/CompraMás dominios caídos.
- **Error/éxito:** Scraper original falla en 4/5 fuentes. CubanCargos sí entrega datos.
- **Lección:** Verificar disponibilidad de fuentes ANTES de escribir scrapers completos. Sitios cubanos cambian/dominios expiran. Revolico bloquea bots simples.
- **Próxima vez:** 
  1. Reescribir scraper enfocado en CubanCargos (fuente principal viable)
  2. Para Revolico: intentar html.duckduckgo.com/html?q=site:revolico.com+triciclos o Playwright
  3. Buscar fuentes alternativas en `Data/Posibles fuentes de datos.md`
- **Etiquetas:** debugging, scraping, cloudflare, dns-fail, cubancargos, revolico, fuentes-caidas

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-07 — sesión en opencode; continúa el debugging del scraping
- **Tarea:** El usuario reporta "el scraping no extrajo ningún registro"; corregir el pipeline scraper → JSONL → score
- **Acción(es):**
  1. **Causa raíz del 0:** había DOS copias del scraper. `codes/scrape_triciclos.py` (Oct 5, commiteada en `d1a7437`) apunta a Revolico (403), KikiHabana y CompraMás (DNS no resuelven) → escribió `codes/anuncios_triciclos.jsonl` vacío a las 09:10. La versión nueva estaba en `Data/` y sí daba registros. El código no estaba roto: se ejecutó el archivo equivocado.
  2. **Fuente nueva y verificada:** `habana.casalindashop.com/vehiculos/triciclos.html` (Magento, 200 OK, 5 productos: 2 combustión Magic Bike 200cc/250cc + 3 eléctricos) con precio en USD y specs en el título. CubanCargos `/triciclos/gasolina-cuba` NO tiene productos propios: solo enlaza a los 4 eléctricos y sus modelos de gasolina (150/200/250/300cc) aparecen únicamente en reseñas de clientes, sin ficha.
  3. **Bugs corregidos en el scraper:** `extract_price_usd` borraba el punto decimal (`$4751.00` → 475100) y no entendía el formato europeo (`3.100,00 USD`); regex `\b(el[eé]ctric|...)\b` nunca coincidía con "eléctrico" (termina en `o`); sin dedupe por URL la página de gasolina duplicaba los 4 eléctricos; `normalize_modelo` fusionaba M004/M005 en "MAGIC BIKE" y dos modelos distintos de Casalinda en "TRICICLO EL", y troceaba "ELÉCTRICO" en "CTRICO" por no quitar tildes.
  4. **Corrección de dato falso:** 3 de los 4 triciclos de CubanCargos se anuncian como `Tipo: Híbrido` en su tabla de especificaciones, y el código los clasificaba como `electrico`. La propulsión ahora sale del campo `Tipo` (dato autoritativo), no del texto libre de la página. Añadida la categoría `hibrido`.
  5. **Dato inventado eliminado:** `analisis.py` estimaba la autonomía de gasolina con `cc/10*3*12` y Magic BIKE salía con "810 km" sin ninguna fuente. Fórmula borrada (viola la regla de no inventar datos).
  6. **Decisiones del usuario:** (a) criterios sin dato → imputación neutra 0.5, con columna `n_criterios` que expone la cobertura de cada score; (b) de aquí en adelante los scripts van en `codes/` y los datos en `Data/` — ambos scripts resuelven `DATA_DIR = padre/padre/Data`, se ejecutan desde la raíz y `codes/` ya no contiene archivos de datos.
- **Resultado:** `python3 codes/scrape_triciclos.py` → **9 registros únicos** (4 eléctrico, 3 híbrido, 2 gasolina) en `Data/anuncios_triciclos.jsonl`; `python3 codes/analisis.py` → `Data/score_modelos.csv` con score sin NaN. Ranking: eléctrico = ELECTRICO CARGA TECHO 72V (0.725, US$2850, 850kg); gasolina = MAGIC BIKE M004 (0.625, US$3100); híbrido = PORTO BELLO (0.550, US$5320, 140km, 700kg).
- **Error/éxito:** Éxito. **Advertencia metodológica sin resolver:** cobertura de los criterios ponderados — precio 100% (peso 0.40), legalidad 44% (0.10), carga 44% (0.20), autonomía 33% (0.25), repuestos **0%** (0.05). `repuestos_proxy` da 0 en todos porque ningún modelo aparece en más de una fuente: ese criterio está inerte y el 45% del peso cae sobre datos ausentes.
- **Lección:** Con dos copias de un mismo script, verificar QUÉ archivo se ejecutó antes de depurar el código: el error estaba en la ruta, no en la lógica. Y nunca dejar que una heurística ("estimación muy burda") alimente un criterio ponderado: fabrica un dato que el informe no podrá defender.
- **Próxima vez:**
  1. Decidir el destino de `repuestos_proxy` (siempre 0): redefinir el proxy o retirarlo de los pesos con el visto del usuario
  2. Cubrir autonomía y carga de los modelos de Casalinda sin inventarlos (buscar ficha técnica en otra fuente) o aceptar `n_criterios=3` y declararlo como limitación en el reporte
  3. Revolico sigue bloqueado (403): probar Playwright o descartarlo como fuente de precios
  4. Trabajo de campo sin empezar: `Data/registro_ubicaciones.csv` sigue con solo cabecera
- **Etiquetas:** scraping, duplicados, casalindashop, cubancargos, hibrido, dato-inventado-eliminado, imputacion-neutra, codes-vs-data, cobertura-de-criterios

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-07 (misma sesión) — el usuario pide: "utilizando como base las páginas que ya scrapeaste, busca otras que sean validas y tambien puedas scrapear"
- **Tarea:** Sondear candidatas de `Data/Posibles fuentes de datos.md` y búsqueda web, e incorporar al scraper solo las que devuelvan 200 con triciclos realmente listados.
- **Acción(es):**
  1. **Barrido de candidatas (todas verificadas con status + contenido, no solo status):** Cloudflare activo en `revolico` (403 item y search, también vía webfetch), `compramasonline`, `islagrande`, `multiservicesxpress`, `patuisla`, `mundoenvio`, `envioscubamerica`; DNS caído en `kikihabana`; y **200 pero sin triciclos** en `cubisima`, `autocubana`, `ventacuba`, `ofertas.cu` ("no hay nada que se ajuste a tus criterios"), `cubamax` (404 en el resultado de búsqueda), `cuballama`, `dimecuba`, `atrexport`, `mcvcommercial`. Los `site:` queries devolvían el reflejo del query en el buscador, no resultados: hay que leer el cuerpo, no el contador de coincidencias.
  2. **Fuente nueva 1 — `elyerromenu.com/b/cuba-sobre-ruedas`** (clasificados comerciales, vendedor "Cuba sobre ruedas", dirección declarada **Boyeros, La Habana**). Solo había mirado la portada; la sección de clasificados tiene triciclos con precio y specs. Categoría = catálogo vivo: 20 fichas de las cuales 3 son basura (cuatriciclo, cargador, gomas) → **17 triciclos**. El sitemap es la única enumeración completa (17 sub-sitemaps, 129 MB / 122 s) pero hay 7 triciclos sin categorizar fuera del listado — no se incluyen; queda como limitación anotada.
  3. **Fuente nueva 2 — `vedca.cu`** (fabricante estatal Vehículos Eléctricos del Caribe). Catálogo con `filter-tri`: 5 triciclos, pero solo **C-800 y C-400** tienen ficha `.html` (los otros 3 tienen `href="#"`). Aporta specs de tabla (`Peso de carga`, `Autonomía`, `Potencia del motor`) y **no publica precio**.
  4. **Bugs encontrados al integrar:** (a) el filtro de descarte usaba `bater[ií]a` en el slug y cazó `triciclos-electricos-maf-bateria-lifepo4`; (b) exigir la palabra "triciclo" en el cuerpo borraba los 3 ONEBOT, que no la mencionan — la evidencia correcta es la **categoría que el vendedor declara en el pie de la ficha**; (c) `requests` asume ISO-8859-1 cuando el servidor no declara `charset` y `vedca.cu` no lo declara → "Autonomía" llegaba como "AutonomÃ­a" y la especificación no se detectaba; corregido en `fetch()` (meta charset de los bytes, si no `apparent_encoding`).
  5. **Decisiones tomadas (revisables):** `vendedor_tipo="tienda"` para elyerromenu y `"fabricante"` para VEDCA; se añade `precio_texto_usd` cuando el texto del anuncio declara un precio distinto al campo estructurado, en vez de elegir uno sin poder verificar cuál está vigente; alias en `normalize_modelo` (`VEDCA C-400` ≡ `VEDCA C400`, `PORTO BELLO` ≡ `PORTOBELLO`) para que cuente `repuestos_proxy`.
- **Resultado:** `python3 codes/scrape_triciclos.py` → **28 registros únicos** de 4 fuentes (18 eléctrico, 8 híbrido, 2 gasolina) en `Data/anuncios_triciclos.jsonl`. Cobertura de los criterios ponderados: precio 92,9% (0.40), **autonomía 64,3% (0.25) — era 33%**, carga 53,6% (0.20) — era 44%, legalidad 60,7% (0.10) — era 44%, repuestos 3,7% (0.05) — era 0%. Peso cubierto: **0.702, era ~0.61**. `n_criterios`: 7 modelos con 3, 10 con 4, 10 con 5. Nuevo ranking eléctrico: KIVITOVA 2026 (0.795), TOPMAQ BRIDERK (0.676), ELECTRICO CARGA TECHO (0.670).
- **Error/éxito:** Éxito, con **tres hallazgos que hay que declarar en el reporte**: (1) `VEDCA C400` tiene specs en conflicto entre fabricante (400 kg / 90 km / 600 W) y revendedor (500 kg / 120 km / 1200 W) y la mediana los promociona silenciosamente (450 kg / 105 km / 900 W); (2) 3 anuncios con precio contradictorio (`precio_texto_usd`: TOPMAQ 4700 vs 5000, ONEBOT TANK 6500 vs 6600, MEJOR PRECIO 3600 vs 3650); (3) `repuestos_proxy` sigue prácticamente inerte — 1 modelo de 27 (VEDCA C400).
- **Lección:** Un contador de coincidencias no es evidencia: en las dos búsquedas que devolvían "resultados" el término solo aparecía reflejado en el propio buscador. Y cuando la categoría de un catálogo es la única afirmación disponible de que un producto es un triciclo (los ONEBOT), esa categoría del vendedor ES el dato — filtrar por palabras del cuerpo estaba sustituyendo la fuente por mi propia suposición.
- **Próxima vez:**
  1. Decidir con el usuario el destino de `repuestos_proxy` (1/27 modelos): redefinirlo o retirarlo de los pesos
  2. Resolver el conflicto de specs de VEDCA C400 y los 3 precios contradictorios (preguntar al vendedor o declararlo como limitación)
  3. Decidir si se recupera alguna de las 7 fichas sin categoría de elyerromenu o se acepta el catálogo vivo
  4. Trabajo de campo sin empezar: `Data/registro_ubicaciones.csv` sigue con solo cabecera
- **Etiquetas:** scraping, fuentes-nuevas, elyerromenu, vedca, boyeros, cloudflare, charset, cobertura-de-criterios, precio-contradictorio, specs-en-conflicto

---

### Entrada de diario
- **Fecha/contexto:** 2026-10-07, sesión reabierta tras el cierre. El usuario repite la petición: "utilizando como base las páginas que ya scrapeaste, busca otras que sean validas y tambien puedas scrapear". Aplicada la consulta de diario previa (descubrimiento agotado en la lista de candidatas → ángulo nuevo: minar enlaces de las 4 fuentes activas).
- **Tarea:** hallar fuentes nuevas partiendo de las páginas ya scrapeadas, verificadas y scrapeables.
- **Acción(es):**
  1. **Mina de enlaces** de las 4 fuentes (internos + externos). Externos relevantes: subdominios casalindashop de otras provincias (fuera de alcance), `elyerroapp.com`, `supermarket23.com`, `katapulk.com`, canal WhatsApp de Cuban Cargo, Facebook, YouTube y **`t.me/MotosBateriasElectricasCuba` (enlazado desde vedca.cu)**.
  2. **Categorías internas y búsquedas**: `catalogsearch` de casalinda con q=triciclo/triciclos/carga → los mismos 5 productos (q=carga solo añade una lavadora); `/vehiculos.html` → mismos 5 triciclos + 1 cuatriciclo; cubancargos `/tienda` → solo la categoría Triciclos; elyerromenu `/?s=` (JS, 'tricic'=0) y `/search` (solo enlace de categoría); categoría `motos-y-bicimotos` → 5 fichas "Agotado" cuyo contenido real es bicimotos/motos de 2 ruedas (el slug `moto-rali-de-tres-ruedas` está reciclado: el contenido es "Bicimotos VEDCA 2026").
  3. **Descartados con evidencia**: elyerroapp (empresa de software, 'tricic'=0), supermarket23 (búsqueda JS, 'tricic'=0 en HTML crudo), katapulk ('tricic'=0), canal WhatsApp de Cuban Cargo (shell sin posts sin la app), Facebook (redirect a /login, 400), YouTube (sin texto SSR), vedca fb618/lt4202/lt4206/lt4209 (200 pero no son triciclos), sh001/L01/4211 (404: no tienen ficha).
  4. **Fuente nueva: canal público de Telegram de VEDCA** (`t.me/s/MotosBateriasElectricasCuba`, enlace en vedca.cu). Servido sin login; enumerable con paginación `?before=` → **130 mensajes desde el canal (14 páginas), 27 con 'tricic', 7 con specs registrables**. Integrada como 5ª fuente: `parse_tg_list` en `codes/scrape_triciclos.py` (pagina internamente, sin fase de detalle; rangos con límite inferior, convención de elyerromenu; `fecha_anuncio`; `municipio_anuncio="Boyeros"` solo si el mensaje declara la dirección del almacén).
  5. **2 bugs corregidos en caliente**: (a) `dict()` sobre tuplas de 3 de `_tg_mensajes` → comprensión `pid -> (fecha, texto)`; (b) el grupo de captura del token de modelo no incluía la "C" → guardaba "VEDCA 400" y NO se unificaba con "VEDCA C400" de las otras fuentes → `f"VEDCA C{...}"`. Añadido además `[A-Z]?` al alias de `normalize_modelo` para que "C400A" no colapse en "C400".
- **Resultado:** `python3 codes/scrape_triciclos.py` → **35 registros únicos de 5 fuentes** (25 eléctrico, 8 híbrido, 2 gasolina); 29 modelos. **2 modelos nuevos**: VEDCA C600 (auto 50, carga 600, 1200W, 60V/90Ah) y VEDCA C400A (auto 80, carga 400, 1500W, 60V/80Ah) — inexistentes en vedca.cu. VEDCA C400 unificado en 6 anuncios (1 elyerromenu, 1 vedca.cu, 4 telegram): precio mediana 4550→**3860** (el telegram incrusta precio de islagrande US$3.170 del 2024-12), autonomía 105→**80**, carga 450→**400**, motor 1200W (600 fabricante / 1200 revendedor / 1500 islagrande). Descubiertos **C800A y LT4211** solo como enlaces (sin ficha publicada: vedca.cu no tiene página para ellos). Ranking sin cambios de podio: KIVITOVA 2026 (0.801), TOPMAQ BRIDERK (0.676), ELECTRICO CARGA TECHO (0.675); C600 y C400A cierran la tabla (0.267 y 0.307, sin precio). Bonus para campo: el canal declara **Almacén VEDCA, Av. Independencia s/n entre Crucero de Armada y calle 100, Boyeros** (recogida lunes a viernes) y "Sólo queda 3" de stock en 2024-11; noticia institucional (2025-06-07): ventas de VEDCA 220 M de pesos en 2024, +30% vs 2023.
- **Error/éxito:** Éxito tras 2 bugs corregidos en la misma ejecución. La fuente nueva no alteró los podios; sí agrava el conflicto pendiente de VEDCA C400 (ahora 3 frentes: specs, precio y antigüedad del anuncio).
- **Lección:** Un enlace saliente de una fuente ya validada (vedca.cu → t.me) rinde más que cualquier `site:` query: el canal público de Telegram es enumerable con `?before=`, sin login ni Playwright. Y los slugs de elyerromenu se reciclan: el contenido del cuerpo manda sobre el URL.
- **Próxima vez:**
  1. Preguntar al usuario: los 3 frentes del conflicto C400 (¿precio de 2024 cuenta igual que el de 2026? ¿la mediana de 6 anuncios es la especificación "oficial"?)
  2. C400A y C400 comparten carga (400) pero no motor: no fusionarlos jamás en alias
  3. Guardar la dirección del almacén VEDCA (Boyeros) en `registro_ubicaciones.csv` como punto del inventario
  4. Trabajo de campo sigue sin empezar (15 municipios, 8h)
- **Etiquetas:** fuentes-nuevas, telegram, vedca, mina-de-enlaces, c400-conflicto, c600, c400a, catalogsearch, slugs-reciclados

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-11 — sesión en opencode; reapertura tras el cierre del 2026-10-07. El usuario pide "sigue el protocolo" y luego elige "arreglar rutas y correr pipeline"
- **Tarea:** Arrancar según protocolo (leer diario) y desbloquear el pipeline, roto por la reorganización de carpetas hecha entre sesiones
- **Acción(es):**
  1. Leído el HANDOFF (desde GitHub) y las 10 entradas del diario; verificado el repo real en el disco externo `17bd76d4` (limpio salvo `data_from_FB`)
  2. **Detectada la rotura:** los datos se movieron a `Data/raw_data/` y el diario/handoff a `opencode/`, pero `scrape_triciclos.py` y `analisis.py` seguían apuntando a `Data/anuncios_triciclos.jsonl` (inexistente). `analisis.py` habría fallado y el scraper habría creado un archivo divergente en `Data/`
  3. **Fix de rutas:** `DATA_DIR` sigue siendo `Data/`; se añadió `RAW_DIR = DATA_DIR / "raw_data"`. El scraper escribe en `RAW_DIR` (con `mkdir` previo) y el análisis lee el JSONL de `RAW_DIR`; los CSV procesados y `registro_ubicaciones.csv` siguen en `Data/`. Docstrings actualizados
  4. Backup del JSONL crudo antes de sobrescribir: `/tmp/opencode/anuncios_triciclos.prebackup.20261011-221602.jsonl`
  5. Ejecutado `python3 codes/scrape_triciclos.py` (5 fuentes) y `python3 codes/analisis.py`
- **Resultado:** Pipeline funcionando. Scraper → **33 registros / 28 modelos** (23 eléctrico, 8 híbrido, 2 gasolina) de casalindashop(5), cubancargos(4), elyerromenu(17), vedca_telegram(7). `diff` contra el backup: **idéntico salvo `fecha_captura`** → el scraper es determinista y no se perdió nada. Score regenerado: podio sin cambios (KIVITOVA 2026 0.801; híbrido JINPEN 0.678; gasolina MAGIC BIKE M004 0.625). Git: 5 archivos `M` (2 scripts + 3 datos), sin commitear
- **Error/éxito:** Éxito. **Falló la fuente `vedca`** (`ConnectionError: Connection reset by peer`); verificado con curl: `vedca.cu` con y sin `www` da reset, sin `www` ni resuelve DNS. Es caída externa (el 7-oct respondía), no un bug. Por eso el total es 33 y no los 35 del handoff: faltan los 2 registros de `vedca.cu` (C-800, C-400 fabricante). El JSONL commiteado por el usuario ya venía sin ellos
- **Lección:** Cuando el usuario reorganiza carpetas entre sesiones, los scripts con rutas hardcodeadas quedan rotos en silencio: hay que verificar las rutas REALES en disco antes de correr, no fiarse del diario/handoff (repite la lección del 2026-10-07: el error estaba en la ruta). Y antes de que un scraper sobrescriba datos, `diff` contra un backup para confirmar que reproduce y no destruye
- **Próxima vez:**
  1. Reintentar `vedca.cu` (fuente del fabricante) cuando vuelva: sin ella no hay C-800 ni specs autoritativas de C-400
  2. Decidir e integrar `Data/raw_data/data_from_FB` (~14 registros manuales de Facebook): hoy no lo lee ningún script y no es JSON válido
  3. Pendientes vivos del handoff: conflicto VEDCA C400 (specs/precio/antigüedad), destino de `repuestos_proxy` y `precio_texto_usd`, trabajo de campo (15 municipios, 8h)
  4. Considerar `.gitignore` para `__pycache__/` (se generó al verificar con `py_compile`)
- **Etiquetas:** pipeline, rutas, raw_data, reorganizacion, vedca-caido, backup, diff, journaling, sesion-reabierta, determinismo

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-11 (misma sesión) — el usuario pide resolver el conflicto VEDCA C400; elige la regla **B: "oferta viva manda"**
- **Tarea:** Resolver los 3 frentes del conflicto C400: (a) specs contradictorias, (b) precio 3170 vs 4550, (c) si el anuncio de 2024 pesa igual que el de 2026
- **Acción(es):**
  1. Recuperado de la historia de git (commit `4b08583`) el registro del **fabricante**: `vedca.cu/c400.html` → 600 W, 400 kg, 90 km, 60 V **50 Ah**, sin precio (el sitio está caído hoy)
  2. Releído el **texto crudo** de los mensajes de Telegram (ids 1640/1643/1647/1722) y de la ficha elyerromenu. Hallazgo: `islagrande.com` es un marketplace donde el vendedor es **VEDCA** (SKU `VDC042-C400-60V80AH-Habana`); su C400: 1500 W, 400 kg, 80–90 km, **GelPb 60 V 80 Ah**, **$3.170**
  3. Verificado en vivo: `islagrande.com` responde **200** (ya no hay Cloudflare), pero la ficha del C400 da **404 (deslistado)** y el C600 está "Out of stock" (en EUR). La **única oferta viva** del C400 es elyerromenu ($4.550)
  4. **Diagnóstico:** fabricante y tienda de VEDCA coinciden en carga (400) y autonomía (~80–90); el revendedor **infla** (500 kg, 120 km). Motor y batería difieren incluso entre canales de VEDCA (600 W/50 Ah vs 1500 W/80 Ah) → configuraciones/SKU distintos, **no promediable**. La mediana (3860 / 450 kg / 1350 W) **no corresponde a ninguna oferta real**
  5. **Implementada la regla B en `analisis.py`:** `VENTANA_VIGENCIA="2026-01-01"`; columna `es_viva` (sin fecha de publicación = catálogo vigente; con fecha, solo si cae dentro de la ventana). En `score_modelos()` se descartan las publicaciones históricas **cuando el modelo tiene oferta viva**. Añadidas columnas `oferta_viva`, `n_anuncios` (usadas) y `n_anuncios_total`
  6. Corregido el comentario del scraper que daba `islagrande` por bloqueada
- **Resultado:** `VEDCA C400` ahora = oferta viva de elyerromenu: **1200 W · 500 kg · 120 km · 60 V 90 Ah · $4.550**, `oferta_viva=True`, `n_anuncios=1`, `n_anuncios_total=5`. Score **0.563 → 0.647** (sube al puesto 5 en eléctricos). `C600` y `C400A` quedan `oferta_viva=False` (solo canal). Ningún otro modelo cambió
- **Error/éxito:** Éxito. Corrección de paso: `n_anuncios` contaba solo los anuncios **con precio** (C400 salía "2" cuando son 5); ahora `n_anuncios` = ofertas usadas y `n_anuncios_total` = todas
- **Lección:** Un promedio entre **procedencias y años** distintos no representa a nadie: la mediana del C400 fabricaba una oferta inexistente. Separar por **vigencia** y por **jerarquía de fuente** elimina el artefacto. Y verificar los sitios en vivo: islagrande pasó de "bloqueado por Cloudflare" a accesible con el producto deslistado
- **Próxima vez:**
  1. Evaluar `islagrande.com` como **fuente nueva** (ya responde 200): su categoría lista triciclos VEDCA vivos
  2. Reintentar `vedca.cu` (fabricante) cuando vuelva
  3. Llevar la vigencia por fecha también al scraper (hoy `fecha_anuncio` solo viene del canal de Telegram)
  4. Pendientes vivos: integrar `data_from_FB`, destino de `repuestos_proxy`/`precio_texto_usd`, trabajo de campo
- **Etiquetas:** c400-conflicto, oferta-viva-manda, vigencia, islagrande, vedca, mediana-artefacto, analisis, decision-usuario

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-11 (misma sesión), tras resolver el C400. El usuario pide "integrar islagrande"
- **Tarea:** Evaluar `islagrande.com` (candidata del handoff) y decidir cómo integrarla como fuente
- **Acción(es):**
  1. **Reconocimiento:** la categoría `/vehiculos-electricos/triciclos.html` lista **11 fichas** (9 en La Habana; 2 de Holguín/Santiago). Todas salen del **Almacén VEDCA, Av. Independencia, Boyeros**
  2. **Moneda:** el selector Magento (EUR/USD) hace POST a `/directory/currency/switch/` y **exige `form_key`**; incluso extrayéndolo de la página, responde "Invalid Form Key" y los precios siguen en **EUR**. No se convierte (regla del proyecto: no inventar tasa)
  3. **Specs por variante** (bloque `Details`). **Hallazgo 1 — el "conflicto C400" se disuelve en gran parte: eran SKUs distintos.** Existen C400A (GelPb 80 Ah), C400 (LiFePO4 90 Ah) y C400 (LiFePO4Mn 90 Ah). La oferta viva de elyerromenu (LiFePO4 90 Ah) es **el mismo SKU** que el C400 LiFePO4 de islagrande, que declara **90–100 km** — no los 120 de elyerromenu → confirma que el revendedor infla la autonomía
  4. **Hallazgo 2:** los 11 triciclos figuran **"Out of stock"** (verificado: sin formulario de compra) → con la regla B, ninguno es oferta viva
  5. **Preguntas al usuario (2):** precio EUR → *"registrar EUR tal cual"* (recomendado); variantes del mismo modelo → *"separar por variante"* (no promediar químicas distintas)
- **Resultado:** Plan aprobado: islagrande entra como **catálogo del fabricante** (sustituye a vedca.cu, caído): precio en `precio_valor` + `moneda="EUR"` (nunca en `precio_usd`), `condicion="agotado"`, y **variantes por química de batería**
- **Error/éxito:** Éxito en la evaluación. El switch de moneda de Magento quedó **descartado** (form_key no persiste); se documenta en la cabecera del scraper
- **Lección:** Un mismo nombre comercial ("C400") esconde 3 SKUs con química y motor distintos; la química de la batería es el discriminante fiable. Y verificar el **cuerpo** de cada ficha, no el título: la URL del C400 GelPb (que enlazaba el canal) está **deslistada (404)** pero su equivalente C400A sigue en catálogo
- **Próxima vez:**
  1. No fusionar C400/C400A/C400 LiFePO4Mn en ninguna tabla: son variantes separadas por decisión del usuario
  2. Si se necesita el precio en USD de islagrande, pedir al usuario una tasa documentada (no inferirla del selector Magento)
  3. El C800A (LiFePO4Mn) aparece solo en "Up-Sell Products" de otras fichas y como enlace en el canal: no tiene ficha propia
- **Etiquetas:** islagrande, fuente-nueva, vedca, moneda-eur, magento-form-key, variantes-bateria, sku, c400-desambiguado, agotado

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-11 (misma sesión) — implementación de la integración de `islagrande` aprobada
- **Tarea:** Integrar islagrande en scraper y análisis, con precio en EUR y variantes por química, sin romper lo anterior
- **Acción(es):**
  1. **Helper `extract_bateria_quimica(text)`**: prioridad LiFePO4Mn → LiFePO4 → GelPb → Plomo → Litio; normaliza subíndices (LiFePO₄→LiFePO4); comprueba **LiFePO4 antes que "gel"** para no confundir la frase "Digital Li/gel with NFC" de las fichas de litio
  2. **Química en las fuentes existentes**: elyerromenu (cuerpo), vedca (tabla), telegram (texto). Verificado con los textos reales: Kivitova "6 Baterías de GEL", MVP "72V 58Ah GEL", C400A telegram "Gel Plomo", C600 "LiFePO4"
  3. **`parse_islagrande_list` / `parse_islagrande_detail`**: filtro `"triciclo"` en la URL (excluye el accesorio batería/cargador `bateria-cargador-lifep4-64v-90ah.html`), exclusión de `-holguin`/`-santiago`/`-santaclara`; specs **solo** desde `.product.attribute.description`; autonomía = **límite inferior** (c400_lfp "between 90 and 100 km"→90; c300 "Up to 60… ~40 cargado"→40); carga por etiqueta (net load/load capacity/cargo weight/max payload); `precio_valor` desde `data-price-amount`; `condicion="agotado"`
  4. **Bug corregido en caliente:** la primera versión acotaba el texto desde la palabra "Details" con una ventana fija → se colaba en la sección **"Up-Sell Products"** y metía "C800A LiFePO4Mn" en la química del **C400A y del SH001** (daban LiFePO4Mn). El contenedor correcto es `.product.attribute.description`
  5. **`analisis.py`**: campos `bateria_quimica`/`precio_valor`/`moneda`; `modelo_norm` incluye la química **solo en eléctricos** (en híbridos la batería es el extensor, no define variante); `es_viva` excluye `condicion="agotado"`; columnas nuevas `precio_valor` y `monedas`
  6. **Cabecera del scraper** actualizada: islagrande pasa a fuente activa; vedca.cu marcado caído; nota del selector de moneda
- **Resultado:** Scraper **33 → 42 registros** (+9 islagrande) / **28 → 35 modelos**. `VEDCA C400 LIFEPO4` mantiene sus números intactos (**1200 W · 500 kg · 120 km · $4.550**, `oferta_viva=True`, `n_anuncios=1/2`; solo cambia el nombre al separarse de GelPb). Nuevos modelos islagrande (todos `oferta_viva=False`, precio en **EUR**): C400 GELPB, C400A GELPB, C400 LIFEPO4MN, C600 LIFEPO4, C600 GELPB, C800B, C800B FOTOVOLTAICO, C300, SH001. Se renombran por química 9 eléctricos de elyerromenu (p. ej. KIVITOVA→…GELPB). **Efecto colateral:** 3 modelos eléctricos no-VEDCA cambian de score (ELECTRICO CARGA TECHO 0.675→0.683; NIPPON SE 0.532→0.591; VIENTO RAPIDO 0.477→0.545) porque el **min/max del grupo eléctrico** se amplía con las specs de islagrande (la normalización es intra-grupo)
- **Error/éxito:** Éxito tras corregir el bug de contaminación por "Up-Sell". Backup del JSONL en `/tmp/opencode/anuncios_triciclos.prebackup.20261011-231056.jsonl` y del score en `/tmp/opencode/score_modelos.prebackup.*.csv`. Compilan ambos scripts. Git: 6 archivos `M` + `__pycache__/` sin ignorar
- **Lección:** Acotar la extracción por **contenedor del DOM**, no por ventana de texto: los carruseles de "productos recomendados" contaminan química y specs (mismo patrón que el pie "Categorías" de elyerromenu). Y al añadir una fuente, los scores **relativos** de todo el grupo pueden moverse aunque esa fuente no tenga precio: la normalización min-max es sensible a los extremos nuevos
- **Próxima vez:**
  1. Decidir el destino de `Data/raw_data/data_from_FB` (sigue sin integrar)
  2. Pendientes vivos: `repuestos_proxy` (1 modelo de 35), `precio_texto_usd` (3 anuncios contradictorios), trabajo de campo (15 municipios, 8h)
  3. Considerar `.gitignore` para `__pycache__/`
  4. Mejora menor detectada: `extract_battery` de elyerromenu no lee "72v/58ah" (barra) — Kivitova queda sin V/Ah (preexistente)
- **Etiquetas:** islagrande, integracion, variantes-bateria, quimica-bateria, bug-upsell, precio-eur, es-viva, agotado, analisis, min-max-grupo

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-12 (sesión nueva) — el usuario pide "extraer modelos de catálogos pertenecientes a empresas"
- **Tarea:** Extraer fichas de triciclos de **catálogos propios de empresas** (distinto de los clasificados), en un **dataset aparte por empresa**, sin tocar el pipeline de triciclos
- **Acción(es):**
  1. **Aclaración de criterio (preguntas al usuario):** quiere *empresas nuevas que yo busque* (no las ya conocidas), *fichas completas como islagrande*, *dataset aparte por empresa*, alcance *triciclos, La Habana*. Formato elegido: **solo JSONL por empresa**
  2. **Investigación:** las MIPYMEs cubanas (MVP, MZ Productions, Kvitova…) publican **solo en Revolico/Facebook** (bloqueados); su web propia es mínima (**VoltHabana** existe pero su catálogo no tiene triciclos). Los catálogos propios extraíbles son tiendas que **envían a Cuba**. Candidatas con triciclos y entrega en La Habana: **KikiHabana, MZ Products, A Cuba Envíos Cargo, Mr Cuba Miami**. Descartadas: `kubazuki.com` ("pronto en línea"), `TriSol` (Pinar del Río, kits solares), `vedca.cu` (caído), `SuperMarket23`/`TodoTriciclos` (SPA/sin respuesta)
  3. **Nuevo script `codes/scrape_empresas.py`** (independiente): reutiliza helpers de `scrape_triciclos` (import, sin ejecutar su `main`); escribe `Data/empresas/<empresa>.jsonl` con el mismo esquema del crudo (+ `disponibilidad` y `fuente`/`vendedor_tipo="empresa"`); precios en **USD** (`precio_usd` + `moneda="USD"`)
  4. **Bugs corregidos durante el reconocimiento:**
     - **KikiHabana:** la categoría "carritos y triciclos" mezcla **cuatriciclos**. El "Carrito eléctrico JY-MX8" dice "4 ruedas" y el "MAGIKBIKE" se llama "Carrito": se excluyen (`carrito`/`4 ruedas`). ONEBOT T414, aunque su slug es `carrito-…`, se anuncia como "Triciclo eléctrico" → se conserva
     - **Batería cirílica:** RALLY PASAJEROS declara "120 **АН**" (А/Н cirílicas) → no se detectaba; se normalizan cirílicos a latinos antes de buscar V/Ah
     - **Motor con miles por espacio:** MZ "E-CARGO ULTRA" escribe "3 000W" → `extract_motor_w` devolvía `0`; se juntan miles separados por espacio
     - **Autonomía vs. velocidad:** KikiHabana usa "Kilometraje de conducción" (no "autonomía") y "Velocidad máxima 70 km/h"; se exige etiqueta de autonomía (autonomía/rango/recorrido/kilometraje/range) y se descartan los `km/h` (BD TAXI 70→**110**, MIGHONG 70→**100**, RALLY PASAJEROS → **70**)
     - **Carga vs. peso neto:** HUAIHAI daba 260 kg (peso **neto**) → se prioriza "capacidad de carga"/"carga útil"/"peso máx" → **780 kg**
     - **MZ:** la página `?s=triciclo` incluye enlaces de "compartir en Facebook" con "triciclo" en la URL → filtro por dominio
- **Resultado:** 4 datasets en `Data/empresas/`: **kikihabana 9**, **mzproducts 7**, **acubaenvioscargo 3**, **mrcuba 2** (21 fichas). MZ: 5 eléctricos + 2 gasolina, specs etiquetadas. KikiHabana: 9 eléctricos con batería/motor/autonomía/carga. A Cuba: 3 eléctricos (specs solo del título, sin página de detalle). Mr Cuba: **fino** (Wix, 2 fichas: solo modelo/precio)
- **Error/éxito:** Éxito. Complica el caso MZ "Triciclo Eléctrico Combustión 200cc" (slug) cuyo H1 dice "de Combustión Pasajero 200cc" → clasificado `gasolina` por el H1 (a revisar si fuera híbrido). Git: `codes/scrape_empresas.py`, `Data/empresas/` y `__pycache__` **sin commitear** (decisión del usuario)
- **Lección:** Partir del **H1/slug de la ficha**, no del nombre de la categoría: las tiendas cuelgan cuatriciclos bajo "triciclos" y usan slugs engañosos (`carrito-…`). Y normalizar la entrada (cirílico, miles con espacio) antes de aplicar los regex de specs, o fallan en silencio (V/Ah, motor)
- **Próxima vez:**
  1. Decidir con el usuario si estos datasets se integran al pipeline o quedan aparte; completar `marca` (p. ej. "MZ PRODUCTS") si se quiere
  2. Revisar con el usuario: MAGIKBIKE (excluido como "carrito", ¿es triciclo?) y MZ 200cc (¿gasolina o híbrido?)
  3. Mr Cuba (Wix) es frágil y sin specs: valorar si merece seguir o se descarta
  4. Pendientes heredados: integrar `Data/raw_data/data_from_FB`; reintentar vedca.cu; `repuestos_proxy` y `precio_texto_usd`; trabajo de campo
- **Etiquetas:** empresas, catalogos, dataset-aparte, kikihabana, mzproducts, acubaenvioscargo, mrcuba, wix, woocommerce, cuatriciclo-excluido, cirilico, specs, sin-commit

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-12 (misma sesión) — revisiones del usuario sobre el dataset de empresas
- **Tarea:** Aplicar las 4 decisiones del usuario sobre los datasets `Data/empresas/`
- **Acción(es):**
  1. **Enlace del conflicto entregado al usuario:** `mzproducts.com/producto/triciclo-electrico-combustion-200cc-mz-products-c-runer/` (H1 dice "de Combustión", pero el slug dice "electrico-combustion")
  2. **Propulsión MZ 200cc → `hibrido`** (decisión del usuario; antes `gasolina` por el H1). Se detecta combinando **título + slug** en `_propulsion_catalogo`: "electrico"+combustión → híbrido. La gasolina 250cc (slug solo "combustion") mantiene `gasolina`
  3. **Marca MZ → "MZ PRODUCTS"** (antes `null`): `st._marca_from_titulo` no la reconoce, se rellena con el campo de la empresa
  4. **Mr Cuba → se mantiene** (aunque sea fino: Wix, 2 fichas sin specs)
  5. **Bug de contaminación evitado en MZ:** antes, si la ficha no tenía el bloque "Potencia del motor", se usaba **toda la página** como `ficha` → los "productos relacionados" podían colarse en specs. Ahora se extrae SOLO de `div.wd-single-content` (bloque de descripción del producto verificado en ambas plantillas); si no existe, `ficha=""` (no se usan specs de la página entera)
- **Resultado:** Valor final `TRICICLO DE COMBUSTION PASAJERO 200CC MZ PRODUCTS` → `propulsion=hibrido`, `marca=MZ PRODUCTS`, `cc=200`, `carga=2000` (de su propia descripción). Las 7 fichas MZ regeneradas sin contaminación
- **Error/éxito:** Éxito. El 200cc no tiene specs de batería/motor en la ficha (solo "Motor: 200 cc"): el `híbrido` se apoya en el slug + confirmación del usuario, no en el texto libre
- **Lección:** Cuando una página no declara specs con las anclas esperadas, **no** retroceder a la página entera: los carruseles de productos relacionados vuelven a contaminar (el mismo patrón del bug "Up-Sell" de islagrande). Mejor contenedor del DOM (`div.wd-single-content`)
- **Próxima vez:** pendientes heredados siguen vivos (integrar `data_from_FB`, `repuestos_proxy`, `precio_texto_usd`, trabajo de campo, vedca.cu); decidir si estos datasets de empresas se integran al pipeline o quedan aparte
- **Etiquetas:** empresas, mzproducts, hibrido, gasolina-200cc, marca, wd-single-content, contaminacion-related-products, sin-commit

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-12 (misma sesión) — el usuario pide cerrar la sesión
- **Tarea:** Cierre de sesión: escribir el HANDOFF en el archivo correcto y reflejar el cierre en el diario
- **Acción(es):**
  1. El usuario pidió "cerrar sesión"; el primer handoff quedó **solo en el chat**, no en archivo
  2. El usuario lo señaló ("¿dónde actualizaste el handoff?"): la convención de la entrada 2026-10-05 es que el handoff se **escribe como archivo** al cerrar sesión (y no se mezcla con el diario). Se sobrescribió `opencode/HANDOFF.md` (cierre 2026-10-12, sesión 4) con las 5 secciones del prompt, incluido el nuevo estudio de empresas
  3. Verificado el working tree: `M` journal + handoff, `??` scrape_empresas.py, `??` Data/empresas/, `??` __pycache__. Nada commitado (el usuario revisa antes)
- **Resultado:** Handoff en `opencode/HANDOFF.md`; diario con esta entrada de cierre. Trabajo sin commitear listo para revisión del usuario
- **Error/éxito:** Éxito tras corrección: el primer cierre omitió el paso de escribir el handoff en disco
- **Lección:** "Cerrar sesión" incluye materializar el handoff en `opencode/HANDOFF.md`, no solo mostrarlo en el chat; verificar el archivo tras escribirlo (como se hace con los datos)
- **Próxima vez:** Al pedir cierre, escribir handoff + entrada de diario de forma explícita (no asumir que mostrar en el chat basta)
- **Etiquetas:** cierre-de-sesion, handoff, journaling, protocolo, sin-commit

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-14 — sesión nueva; el usuario decide integrar Facebook como fuente completa
- **Tarea:** Integrar `Data/raw_data/data_from_FB` como 6ª fuente del pipeline y crear la capa de datos limpios `Data/clean_data/`
- **Acción(es):**
  1. Creado `codes/parse_fb.py` → escribe `Data/clean_data/anuncios_facebook.jsonl` (**29 registros**; 1 excluido: Artemisa). Correcciones durante el parseo: fallback de `modelo` nulo → marca; bug de sintaxis `null.`; `autonomia`→`autonomia_km`; `url` sin dos puntos; unificación `fuente`/`fuentes`; normalización de mayúsculas de marca/modelo; "Habana"→null
  2. Creada la capa `Data/clean_data/` (misma altura que `raw_data`): copiados `anuncios_triciclos.jsonl` y los 4 JSONL de `Data/empresas/`
  3. `codes/analisis.py` ahora lee de `CLEAN_DIR` (ambos anuncios: scraper + Facebook) y escribe sus salidas en `clean_data/`; añadida la tabla `MODELO_ALIAS` + `apply_alias` para fusionar nombres de Facebook con los del scraper
- **Resultado:** 42 anuncios scraper + 29 Facebook = **71 anuncios → 43 modelos únicos** (33 eléctricos, 8 híbridos, 2 gasolina). Alias aplicados: BRIDERK→`TRICICLOS TOPMAQ BRIDERK 2026 GELPB`; MVP POWER→`…MVP POWER GELPB`; ONEBOT→`ONEBOT CLASIC 2026`; KIVITOVA→`…KIVITOVA 2026 GELPB`; TOPMAQ→BRIDERK; VIENTO RAPIDO→`ELECTRICO VIENTO RAPIDO`; MAF→`…MAF BATERIA LIFEPO4`; JINPENG→`JINPENG GELPB`
- **Error/éxito:** Éxito. **STAR eléctrico (FB) NO se fusiona** con `TRICICLOS HIBRIDOS STAR` (híbrido). Top eléctrico tras integrar: **TOPMAQ BRIDERK 2026 GELPB 0.736** (n=5), **ONEBOT CLASIC 2026 0.725** (n=5)
- **Lección:** Facebook no aporta specs nuevas pero sí **conteos de anuncios** y nombres; fusionar por nombre exige tabla de alias explícita y verificar que no se mezclen variantes de **propulsión distinta**. Al ampliar el grupo, los scores relativos pueden moverse (misma sensibilidad min-max intra-grupo que con islagrande)
- **Próxima vez:** Cualquier fuente nueva fusionada por nombre → alias explícito + comprobar propulsión antes de unir
- **Etiquetas:** facebook, fuente-nueva, clean-data, parse-fb, alias, fusion-modelos, min-max-grupo, analisis

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-14 (misma sesión) — construir el entregable
- **Tarea:** Crear el reporte interactivo (Streamlit + Matplotlib) que lea en vivo de `Data/clean_data/`, con storytelling-de-datos, cubriendo las 3 fuentes (anuncios, empresas, trabajo de campo)
- **Acción(es):**
  1. Decidido: **app Streamlit** (no markdown aparte) con gráficos **Matplotlib estáticos**; estructura `reporte/` con `app.py`, `data.py` (capa de datos con `st.cache_data`), `theme.py` (paleta por propulsión + helpers), `.streamlit/config.toml`, `requirements.txt`
  2. Creadas **10 páginas** en `reporte/pages/`: Resumen, Método, Mercado, Ranking, Precio/Autonomía/Carga (burbuja + frontera Pareto), Contendientes (top + radar), Mejor Opción (4 escenarios), Trabajo de Campo (protocolo + placeholders), Empresas (21 fichas), Limitaciones
  3. Regla respetada: los gráficos **no limpian** datos; toda la limpieza vive en `codes/` y se materializa en `clean_data/`
  4. `.gitignore` creado (`.venv/`, `__pycache__/`, `*.pyc`, etc.); `git rm -r --cached codes/__pycache__`
- **Resultado:** Reporte completo en `reporte/`; sección de trabajo de campo visible como "pendiente" con los 11 campos del registro intactos
- **Error/éxito:** Éxito en creación, **pero sin probar en un servidor real**; el arranque del servidor reveló fallos de importación (ver entrada 2026-10-15)
- **Lección:** Crear la app sin arrancarla deja bugs latentes; conviene un smoke-test del servidor antes de darla por terminada
- **Próxima vez:** Tras crear páginas Streamlit, arrancar el servidor y navegar cada página antes de cerrar la tarea
- **Etiquetas:** reporte, streamlit, matplotlib, storytelling, paginas, theme, data-layer, gitignore

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-15 — sesión en opencode; el usuario reporta "en el reporte solamente aparece el campo de app, los demás están vacíos"
- **Tarea:** Diagnosticar y corregir las páginas vacías del reporte
- **Acción(es):**
  1. Reproducido con `AppTest` (todas las vistas): 3 errores → `fig_ax()` no aceptaba `subplot_kw` (radar/polar en páginas 4, 5 y 6) y faltaban imports en la página 3 (`MUTED`, `GRID_COLOR`, `TEXT_COLOR`) y la 6 (`GRID_COLOR`)
  2. **Causa raíz del "vacío":** las páginas importan `from reporte.data import ...`, pero Streamlit añade a `sys.path` **solo la carpeta del script principal** (`reporte/`, o `""` si se lanza `cd reporte && streamlit run app.py`), **no la raíz del repo** → `ModuleNotFoundError: No module named 'reporte'` → cada página renderiza en blanco. Reproducido simulando el `sys.path` real
  3. Arreglo: bloque de bootstrap al inicio de cada página que inserta la raíz del repo en `sys.path` (sirve en ambos modos de lanzamiento); `fig_ax(**kwargs)`; imports añadidos
  4. Renombrado `5_P_A_C.py` → `5_Precio_Carga.py` (la barra lateral mostraba "P_A_C")
  5. Entorno: `python3 -m venv reporte/.venv` (Python 3.14); Arch/Archcraft es *externally-managed* (PEP 668) → `pip` solo dentro del venv; instalados **streamlit 1.66.0**, matplotlib 3.11.2, pandas, numpy
- **Resultado:** Verificado en 3 niveles: (a) `AppTest` de las 11 vistas → 0 excepciones; (b) simulación del `sys.path` real en ambos modos → OK; (c) **servidor real por WebSocket** → la navegación lista 11 entradas y las 10 páginas ejecutan sin excepción. Servidor en `http://localhost:8501` (detenido al cerrar)
- **Error/éxito:** Éxito. El commit `a9fd9ee "created reporte"` (2026-10-15 10:19) ya incluye el bootstrap y el renombre
- **Lección:** En apps Streamlit multipágina, importar por paquete (`from reporte.x import`) **rompe** salvo que se garantice la raíz del repo en `sys.path`: Streamlit solo añade la carpeta del script principal. La prueba con `python -c` **no vale** (ese sí añade el CWD); hay que probar con el **servidor real** o simular su `sys.path`
- **Próxima vez:** Al crear páginas Streamlit en subcarpetas, añadir el bootstrap de `sys.path` desde el inicio y verificar con el servidor real, no solo importando el módulo
- **Etiquetas:** streamlit, multipagina, sys-path, import-error, pagina-en-blanco, fig-ax, radar, venv, pep668, archcraft, bug-fix

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-15 (misma sesión) — aclaración de ubicación del código
- **Tarea:** Resolver dónde vive el código del reporte
- **Acción(es):** El usuario preguntó "¿escribiste el código de la página en codes?"; verificado el árbol: `codes/` solo contiene el pipeline (`scrape_triciclos.py`, `parse_fb.py`, `scrape_empresas.py`, `analisis.py`); el reporte vive en `reporte/` (`app.py`, `data.py`, `theme.py`, `pages/`). El usuario decidió **dejarlo en `reporte/`**
- **Resultado:** Convención fijada: pipeline de datos en `codes/`, app de visualización en `reporte/`, datos limpios en `Data/clean_data/`
- **Error/éxito:** Éxito
- **Lección:** Mantener separado el pipeline (produce datos) de la app (los consume) evita mezclas y aclara responsabilidades
- **Próxima vez:** No mover `reporte/` dentro de `codes/`; respetar la separación acordada
- **Etiquetas:** convenciones, estructura, reporte, codes, decision

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-15 (misma sesión) — el usuario pide cerrar sesión y actualizar journaling + handoff
- **Tarea:** Cierre de sesión: actualizar `opencode/HANDOFF.md` y el diario
- **Acción(es):**
  1. Detenido el servidor Streamlit (puerto 8501)
  2. Verificado el working tree: `HEAD = a9fd9ee "created reporte"`; **solo `.gitignore` sin commitear** (`??`)
  3. Reescrito `opencode/HANDOFF.md` (cierre 2026-10-15, sesión 5) con las 5 secciones del prompt
  4. Añadidas las entradas de esta sesión al diario
- **Resultado:** Handoff y diario al día; servidor detenido; único pendiente de git: `.gitignore`
- **Error/éxito:** Éxito
- **Lección:** El commit `created reporte` ya lo había hecho el usuario; antes de redactar el handoff conviene mirar `git log`/`git status` para no declarar como "sin commitear" algo que ya está en el historial
- **Próxima vez:** Primero `git log -3` + `git status --porcelain`, luego redactar el estado real
- **Etiquetas:** cierre-de-sesion, handoff, journaling, git-status, decision

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-15 — sesión en opencode (sesión 6); reapertura tras el cierre de la sesión 5. El usuario pide leer los dos archivos de `opencode/` desde GitHub y, después, "documentación real que justifique esos parámetros" (los pesos del scoring)
- **Tarea:** Aplicar el protocolo de apertura (leer handoff + diario) y aportar fuentes reales que justifiquen los pesos del scoring (precio 0.40, autonomía 0.25, carga 0.20, legalidad 0.10, repuestos 0.05)
- **Acción(es):**
  1. Leídos `opencode/HANDOFF.md` (sesión 5) y `opencode/Journaing_file.md` (427 líneas, 17 entradas) vía raw.githubusercontent — protocolo de apertura cumplido
  2. Explicados los pesos: tabla de 5 criterios, mecánica (min-max intra-propulsión, ausentes → 0.5 + `n_criterios`, rangos → límite inferior, oferta viva) y cobertura declarada como limitación
  3. Búsqueda literaria con verificación de enlaces: 13 URLs comprobadas por HTTP (11×200; IEEE, AP News y cubanet solo responden en navegador). Descarga de PDFs a `/tmp/opencode/docs` y extracción con `pdftotext` para confirmar cifras antes de citarlas (ISAHP 2022: *local priority* 0.40 de precio/combustible y 0.05 de *frequent repairs*; Hong et al. 2024: WTP por km de autonomía)
  4. Justificación por criterio: precio → Niu et al. 2024 (IEEE Access, peso precio **0.417**) + ISAHP 2022; autonomía → Hidrue et al. 2011 + Hong et al. 2024; carga → Trung & Ersoy 2025 (tabla de 20 estudios MCDM); legalidad → Resolución 47/2026 MINTRAN + licencias temporales sin matrícula (3 fuentes cubanas); repuestos → apoyo indirecto ISAHP
  5. Preguntado al usuario dónde materializarlo → elige **`Data/fuentes_justificacion.md`**
  6. **Fricción:** el disco externo no estaba montado (tras un reinicio del servidor a mitad de la tarea). Preguntado en vez de escribir una copia en otro sitio; con el disco montado ("try again"), escrito el archivo: 5 secciones de criterio + tabla metodológica + nota de honestidad (los pesos exactos = juicio experto del proyecto, calibrado con literatura)
  7. Verificado `git log -3` + `git status` antes del cierre: el usuario ya había commiteado `c2fa8a5 "created fuentes_justificacion.md"` y `4a9aeab "added gitignore"` (pendiente 2 de la sesión 5, resuelto)
- **Resultado:** `Data/fuentes_justificacion.md` en el repo y commiteado por el usuario. Justificación documental lista para la página Método del reporte, con enlaces verificados y estados HTTP anotados
- **Error/éxito:** Éxito. Fricción resuelta: disco externo no montado + reinicio del servidor a mitad de la tarea. Ninguna fuente citada sin verificar su contenido (los PDF con cifras se descargaron y leyeron antes de citar)
- **Lección:** Verificar que el disco externo esté montado antes de intentar escribir en el repo; si no lo está, preguntar al usuario y no crear copias divergentes (misma lección de ubicación que el 2026-10-05). Y cuando pidan "documentación real que justifique X", distinguir honestamente entre lo que la literatura respalda (orden y magnitudes) y lo que es decisión normativa del proyecto (valores exactos): la credibilidad del informe depende de esa distinción
- **Próxima vez:**
  1. Pendientes ofertados y no ejecutados: (a) añadir la justificación a `reporte/pages/2_Metodo.py`; (b) análisis de sensibilidad de pesos ±25% en `analisis.py` (estándar, como Niu et al. 2024) para demostrar estabilidad de los podios
  2. Re-verificar los enlaces de `fuentes_justificacion.md` antes de publicar/deployar (pueden caducar; IEEE/AP News bloquean bots)
  3. Pendientes heredados siguen vivos: trabajo de campo, `use_container_width`, destino de `Data/empresas/`, `repuestos_proxy`, `precio_texto_usd`, `vedca.cu`
- **Etiquetas:** justificacion-de-pesos, literatura, mcdm, fuentes-verificadas, disco-externo, fuentes_justificacion, protocolo-apertura, reinicio-servidor

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-19 — sesión en opencode (sesión 7); el usuario corrige a mano los `Data/clean_data/*.jsonl` (4 commits: `bef8d6b`, `64e0131`, `d560e5f`, `39590f3`) y pide revisar sus cambios, compararlos con los míos y analizar qué se hizo mal al limpiar la data
- **Tarea:** Analizar la curaduría manual del usuario, detectar sus efectos sobre el pipeline y dejar la limpieza **en el origen** (regla aplicada en el scraper) para no volver a perderla
- **Acción(es):**
  1. **Análisis del cambio del usuario** (4 commits sobre `clean_data/`): la regla es *`modelo` = nombre propio del producto* — se quitan genéricos de categoría (TRICICLO/S, ELÉCTRICO/S, HÍBRIDO/S, DE COMBUSTION, DE CARGA), marketing (DISPONIBLE, MAS GRANDE, MEJOR PRECIO, PANEL SOLAR) y specs (72V, 85AH, LITHIUM, LIFEPO4); si no queda nombre, `modelo` = null y la identidad pasa a la `marca` (CHILWEE, CYT, MAF, KIVITOVA, LAITUNG, STAR, JINPEN, Hercules, Tiger). También corrigió `JIMPENG → JINPEN` y borró el registro `TRICICLOS HIBRIDOS MEJOR PRECIO`
  2. **Medido el impacto, no supuesto**: copié el repo a `/tmp/opencode/ds_old` (commit `8523c44`) y `/tmp/opencode/ds_new` (HEAD) y corrí `codes/analisis.py` en ambos. Resultado: el `modelo` null se convertía en **`"NONE"`** (`df["modelo"].astype(str)`) → 7 registros de 5 productos distintos colapsaban en 3 grupos fantasma, y **`NONE GELPB` encabezaba el ranking eléctrico con 0.826**. Además la tabla `MODELO_ALIAS` (nombres antiguos) rompía la fusión con Facebook (TOPMAQ BRIDERK se partía en 2 grupos, n=9 → 8+1) y el rename creaba colisiones indebidas (2 OIM, 2 RALLY, 3 E-CARGO, 2 VEDCA C800B)
  3. **Decisiones del usuario** (preguntadas): identidad = marca cuando no hay modelo (con guarda de propulsión); el registro `MEJOR PRECIO` se queda fuera a propósito; los productos que no son exactamente iguales se separan y se cuentan por separado; **la limpieza va en el scraper** (raw_data nace limpio)
  4. **Nuevo `codes/norm_modelo.py`**: la regla como código (token sets de genéricos/marketing/química, extracción de `marca X` del texto, `limpiar_nombre()`, `canonizar()`, `canonizar_registro()`, `identidad()` vectorizada). **Nuevo `Data/modelos_canonicos.json`**: tabla curada por producto (clave: URL) generada con `codes/crear_canonicos.py`; incluye los 7 productos con la misma URL (mrcuba) como `opciones` con discriminante de nombre y de propulsión
  5. **Conectado en el origen**: `scrape_triciclos.py`, `scrape_empresas.py` y `parse_fb.py` normalizan antes de escribir → `raw_data/` y `Data/empresas/` nacen con los nombres ya limpios (migrados en el sitio, sin red). `reporte/data.py` usa la **misma** función (`codes.norm_modelo.identidad`), así que el reporte y el análisis no pueden divergir
  6. **`codes/analisis.py`**: identidad = modelo → marca → `SIN IDENTIFICAR` (con aviso); + química en eléctricos; + alias; **propulsión dentro de la clave** (`modelo_norm`,`propulsion`) en score, `repuestos_proxy`, `n_anuncios_total` y `comparar_campo_online` → el STAR eléctrico y el híbrido dejan de poder fusionarse
  7. **Dos bugs de agregación encontrados y corregidos**: (a) `n_anuncios=("modelo","count")` contaba 0 en los registros sin nombre → `("fuente","size")`; (b) **`repuestos_proxy` se calculaba por archivo**, así que un modelo presente en el scraper y en Facebook no se detectaba → ahora se calcula sobre el dataset unido: el criterio (peso 0.05) pasa de 1/35 a **9/42 modelos**
  8. **Reporte**: `2_Metodo.py` (nueva sección "Identidad del producto" + alias actualizados + cifras), `10_Limitaciones.py` (cifras, pendientes nuevos, tabla de versionado), `3_Mercado.py` y `9_Empresas.py` (columna `nombre_producto`: si no hay modelo, se muestra la marca), `app.py` (70/42 y corte de datos)
  9. **Verificado**: `analisis.py` sin errores (70 anuncios → 41 nombres / 42 filas de ranking; **0 identificadores vacíos, 0 "NONE", 0 n_anuncios=0**); `AppTest` de las 11 vistas sin excepciones; **servidor real por WebSocket** (protobuf de Streamlit 1.66) con las 11 vistas en OK; migración **idempotente** (`norm_modelo.py --check` → 0 cambios)
- **Resultado:** La curaduría del usuario quedó **integrada en el código**, no en el JSONL: `Data/modelos_canonicos.json` es la fuente de verdad y el scraper la aplica. `clean_data/` reproduce exactamente lo que el usuario curó, salvo las 7 separaciones de variante que él mismo aprobó. Ranking eléctrico: TOPMAQ BRIDERK 2026 GELPB 0.786 (9 anuncios) > ONEBOT CLASIC 2026 0.775 > KIVITOVA GELPB 0.723. Nada commiteado (lo revisa el usuario)
- **Error/éxito:** Éxito con dos errores propios detectados y corregidos en el camino: (1) la primera versión de la tabla canónica no desambiguaba los 2 productos de mrcuba (misma URL) y le asignaba a los dos la marca del segundo; (2) al migrar el crudo en el sitio se perdieron los nombres originales, que son el discriminante → se recuperan de `git show HEAD:<fichero>` y se añade la propulsión como segundo discriminante
- **Lección:** La curaduría manual del usuario era una **especificación de la regla**, no un parche: convertirla en tabla versionada + código es lo que evita que la próxima pasada del scraper la revierta. Y medir el efecto (copiar el repo y correr el pipeline dos veces) en vez de razonarlo fue lo que reveló el bug de `"NONE"` y el de `repuestos_proxy` por archivo: los dos eran invisibles leyendo el código
- **Próxima vez:**
  1. El usuario debe revisar `Data/modelos_canonicos.json` (90 productos) y decidir si cura los 3 nombres crudos de `acubaenvioscargo` ("TRICICLO FLY RACING MOTOR 1500W BATERÍA 72V80AMP") y la marca "MAGIC BIKE" del triciclo eléctrico de cabina (no aparece en la ficha: la ficha solo dice 1800 W y 72 V; además declara **Carga máxima 650 kg**, que está en `null` en la data)
  2. Re-verificar el proxy de repuestos: ahora 9/42 modelos, pero sigue siendo ">1 fuente", no disponibilidad real de repuestos
  3. Pendientes heredados: trabajo de campo (15 municipios, 8h), `precio_texto_usd` (3 contradictorios), conflicto C400, `use_container_width` → `width="stretch"`, `vedca.cu` caído, destino de `Data/empresas/` (sigue fuera del scoring)
  4. Ofertado y no ejecutado: análisis de sensibilidad de pesos ±25%; página de justificación documental (`fuentes_justificacion.md`) en `2_Metodo.py`
- **Etiquetas:** curacion-manual, identidad-de-producto, modelos-canonicos, norm-modelo, none-fantasma, repuestos-proxy, fusion-por-propulsion, scraper-en-origen, idempotencia, mrcuba-url-compartida

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-19 — sesión en opencode (sesión 7, continuación). El usuario corrigió **otros** errores a mano en los datos limpios de empresas (5 commits: `cc4e7fe`, `04f2b14`, `17a4764`, `461059a`, `afd83b0`) y pide revisar
- **Tarea:** Revisar las correcciones del usuario en `Data/clean_data/*empresas*.jsonl` y dejarlas integradas en el pipeline (tabla canónica + scraper), sin que la próxima pasada las revierta
- **Acción(es):**
  1. **Qué cambió el usuario**: en `acubaenvioscargo.jsonl` → `modelo` "FLY RACING" y `marca` "RACING" (2 fichas) y `modelo` null + `marca` "RACING" (la 3ª); en `mzproducts.jsonl` → **revirtió** las 3 separaciones de variante que yo había hecho: los tres "E-CARGO 80AH/60AH/100AH MZ PRODUCTS" vuelven a ser "E-CARGO MZ PRODUCTS" (la capacidad ya está en su campo `bateria_ah`). En un commit intermedio dejó un JSON roto (`"modelo": "null,`) que corrigió en el siguiente
  2. **Riesgo detectado y corregido**: la tabla canónica aún tenía mis sufijos de variante → la próxima migración habría **revertido** su curaduría. Actualizado `codes/crear_canonicos.py`: fuera los 3 overrides de E-CARGO (con nota de por qué), añadida la lista `OVERRIDES` (nombres fijados a mano **aunque el producto aún no esté en `clean_data`**), `acubaenvioscargo` sale de `SIN_CURAR`
  3. **Data gap encontrado en el scraper**: la categoría de A Cuba Envíos Cargo tiene **4** productos y solo se capturaban 3. El 4º ("Triciclo Fly Racing 2027", $4.580) está "Próximamente" → **no tiene botón de compra**, así que no hay `add-to-cart=<id>` y el scraper no podía identificarlo (el id es la clave del producto). Verificado en el HTML vivo (4 `.wd-product-wrapper`, 3 ids)
  4. **Corregido `scrape_empresas.py`**: (a) si no hay id de carrito, se usa el **permalink** del producto (`/tienda/...`) como URL; (b) "Próximamente" se comprueba **antes** que "En stock" (el producto aparece con las dos etiquetas y no es comprable); (c) si el título no dice el tipo, la **categoría** ("Triciclos Eléctricos") da la propulsión → `electrico` en vez de `indeterminado`
  5. **Re-scrape solo de acuba** (sitio accesible): 3 fichas con los nombres del usuario + la 4ª recuperada ("FLY RACING 2027" / RACING / eléctrico / $4.580 / "Próximamente"). Precios de las 3 anteriores **sin cambios**
  6. Migración aplicada (`norm_modelo.py --migrar`): `clean_data/` reproduce la curaduría del usuario y `Data/empresas/` (el crudo) queda alineado. **Idempotente**: `--check` → 0 cambios. `analisis.py` sin cambios (las empresas siguen fuera del scoring)
  7. **Reporte**: cifras de empresas 21 → **22** fichas (`app.py`, `2_Metodo.py`, `9_Empresas.py`, `10_Limitaciones.py`); nuevo pendiente: nombres repetidos en empresas (3 E-CARGO, 2 FLY RACING) que se agregarían si el dataset entrara al scoring
  8. Verificado: `AppTest` 11/11 sin excepciones y **servidor real** 11/11 OK
- **Resultado:** La curaduría del usuario (2ª tanda) integrada en la tabla canónica; el pipeline ya no la revierte. Se recupera un producto que faltaba (Fly Racing 2027) y se corrigen dos errores del scraper (identificación por permalink, disponibilidad "Próximamente"). Nada commiteado
- **Error/éxito:** Éxito. Dos cosas que fallaron y se corrigieron: (1) mi tabla canónica habría revertido la curaduría del usuario (se avisó comparando el estado del repo con la tabla antes de migrar); (2) el override del producto nuevo no entraba en la tabla porque la tabla se construye desde `clean_data` y ese producto aún no estaba ahí → los overrides manuales se añaden siempre, haya o no registro
- **Lección:** Cuando el usuario corrige a mano, hay que **comparar sus cambios con la tabla canónica ANTES de migrar**: la tabla es lo que manda y se genera desde `clean_data`, así que cualquier cambio manual no refletido ahí se pierde en la siguiente pasada. Y un producto sin botón de compra no es un producto "faltante": es un producto que hay que identificar por otra vía (permalink) y whose estado ("Próximamente") hay que leer antes que "En stock"
- **Próxima vez:**
  1. El usuario debe revisar el nuevo registro "FLY RACING 2027" (nombre y marca puestos por mí siguiendo su regla; las specs no están en la web: sin motor ni batería) y decidir si `Data/empresas/` entra o no en el scoring
  2. Sigue pendiente: la marca "MAGIC BIKE" del eléctrico de cabina de Casalinda (no está en la ficha; la ficha declara "Carga máxima 650 KG" y está en `null`)
  3. Heredados: trabajo de campo, `precio_texto_usd`, conflicto C400, `use_container_width` → `width="stretch"`, `vedca.cu` caído, análisis de sensibilidad ±25%, página de `fuentes_justificacion.md` en `2_Metodo.py`
- **Etiquetas:** curacion-manual, acubaenvioscargo, fly-racing, producto-que-faltaba, permalink, proximamente, scraping-acuba, tabla-canonica, override, idempotencia, e-cargo-revertido

---

### Entrada de diario

- **Fecha/contexto:** 2026-10-31 — sesión en opencode; el usuario aporta la hoja de campo real (`Data/raw_data/data_personas.txt`, 30 registros, sin trackear)
- **Tarea:** "Procesa los registros" — convertir la hoja de captura en datos del pipeline
- **Acción(es):**
  1. Diagnóstico previo: el `HANDOFF.md` estaba desfasado (`HEAD=afd83b0`, decía que `registro_ubicaciones.csv` seguía con solo cabecera); el repo ya tenía 3 commits más y un `Data/resumen_pesos_scoring.md` nuevo. Verificado con `git log -3` + `git status` antes de escribir
  2. **Privacidad primero**: la hoja lleva nombre y CI de cada propietario y el repo es público → descartados en la lectura (nunca se copian), verificación de que no queda ningún número de 11 dígitos en la salida, y `.gitignore` para el txt
  3. `codes/parse_campo.py` (nuevo): txt → `Data/registro_ubicaciones.csv`; fecha ISO, municipio oficial (valida contra los 15), uso al esquema (`familiar`→`ocio_paseo`, `pasaje`→`pasajeros`, `carga y pasaje`→`mixto`) conservando el texto en `uso_original`, `electrico + paneles` → `con_paneles=1`, motor a `1500W`, batería V/Ah, autonomía; `--check` idempotente
  4. **No inventar**: el registro 2 trae "bateria: 78 50ah" (78 V no es múltiplo de 12) → se conserva y se marca en `notas`; `modelo`, `estado` y `observador` quedan vacíos porque la hoja no los capturó
  5. Alias de marca a `codes/norm_modelo.py` (`MARCA_ALIAS`: ONEBOOT→ONEBOT, KVITOVA→KIVITOVA, MAGICBIKE→MAGIC BIKE, JINPEING→JINPENG), eje distinto de `ALIAS_MODELOS`; `identidad(df, con_alias=False)` también en `load_campo` (con alias se inventaría "ONEBOT CLASIC 2026" en la calle)
  6. **Comparación a nivel MARCA**: el campo no distingue modelo, así que la comparación por identidad queda casi vacía (JINPENG vs "JINPENG GELPB"). Nuevo `comparacion_campo_online_marca.csv` con `pct_campo`/`pct_online`/`delta_pct`; la comparación por identidad se conserva como referencia
  7. Reporte: `8_Trabajo_Campo.py` deja de ser placeholders (KPIs, top marcas, calle vs anuncios en cuotas, tablas por municipio y uso, aviso de muestra de conveniencia); `app.py`, `1_Resumen`, `2_Metodo` y `10_Limitaciones` actualizados a 30 obs / 5-15 municipios. El campo **no** entra al scoring
  8. Verificado: AppTest 11/11 sin excepciones, servidor real en :8599 (health 200), `parse_campo.py --check` OK, `norm_modelo.py --check` 0 cambios, `score_modelos.csv` intacto
- **Resultado:** 30 observaciones en 5/15 municipios (Centro Habana, Plaza, Habana del Este, La Lisa, Playa), 12 marcas, 29 eléctricos + 1 híbrido (uno con paneles). En calle JINPENG 20% > KIVITOVA/ONEBOT 16.7% > TOPMAQ 10%; VEDCA encabeza la oferta online (24%) con 0 apariciones en calle. Nada commiteado
- **Error/éxito:** Éxito, con dos correcciones propias: (1) el primer gráfico comparaba conteos brutos 30 vs 70 (universos distintos) → pasado a cuota dentro de cada fuente; (2) `load_campo` del reporte y el de `analisis.py` normalizaban distinto → unificado en `identidad()` + `marca_norm()`
- **Lección:** cuando cambia el nivel de agregación (marca vs modelo) hay que cambiar también la comparación, no forzar la identidad; y una muestra de 30 con 70 anuncios solo se compara en porcentajes, nunca en conteos
- **Próxima vez:**
  1. Confirmar con el usuario: `familiar`→`ocio_paseo` (¿o `pasajeros`?), y si JINPEN/JIMPENG son la misma marca que JINPENG (cambiaría JINPENG de 6 a 8-9 en calle y de 2 a 4 online)
  2. Marcas sin par online: DC (2), MINERVA (2), MOTO FORM (1), VELGA (1) — ¿son grafías de marcas ya conocidas?
  3. Faltan 10 municipios; `tipo=triciclo` es supuesto (la hoja no registra cuatriciclos)
  4. `HANDOFF.md` sigue con el estado del 2026-10-19: no se toca hasta el cierre de sesión
- **Etiquetas:** trabajo-campo, parse-campo, privacidad, pii, anonimizacion, alias-de-marca, nivel-marca, cuotas, no-inventar-datos, idempotencia, streamlit

### Entrada de diario

- **Fecha/contexto:** 2026-10-31 (misma sesión) — el usuario responde a las 4 preguntas abiertas del ingest de campo
- **Tarea:** aplicar las decisiones y proponer cómo integrar los datos de campo al pipeline
- **Acción(es):**
  1. `familiar` → **pasajeros** (no `ocio_paseo`): uso queda pasajeros 18 / mixto 6 / carga 6
  2. **JINPEN y JIMPENG son la misma marca que JINPENG**: añadidos a `MARCA_ALIAS` (la marca se fusiona; el producto no: JINPENG eléctrico ≠ JINPEN híbrido)
  3. **VELGA es VEDCA**: alias añadido; VEDCA pasa a 1 observación en calle (antes 0) frente a 17 anuncios
  4. **Voltaje 78 V → 72 V** en OBS-002: tabla explícita `CORRECCIONES_BATERIA_V` + columna nueva `bateria_v_origen` (la corrección deja rastro, no sobrescribe la evidencia)
  5. Reporte: caption de VEDCA en `8_Trabajo_Campo.py` y fila de pendientes en `10_Limitaciones.py` corregidas (VEDCA ya no es "0 en calle"); texto de alias en `2_Metodo.py` ampliado
- **Resultado:** JINPENG 20% (6) / KIVITOVA 16.7% / ONEBOT 16.7% / TOPMAQ 10% en calle; online JINPENG sube a 5 y VEDCA sigue liderando con 17. `parse_campo.py --check` OK, AppTest 11/11
- **Error/éxito:** Éxito. Ninguna decisión del usuario obligó a tocar el scoring
- **Lección:** una errata confirmada por el dueño de los datos se corrige **con tabla y columna de origen**, no reescribiendo el valor: así el dato es auditable y la regla "no inventar" sigue en pie
- **Próxima vez:** decidir si el campo entra al análisis más allá de lo descriptivo (índice de circulación, uso, promesa vs realidad) — ver propuesta entregada al usuario
- **Etiquetas:** campo, decisiones-usuario, alias-de-marca, vedca, jinpeng, correccion-trazable, bateria, uso-pasajeros

### Entrada de diario

- **Fecha/contexto:** 2026-10-31 (misma sesión) — el usuario aprueba implementar A + C + `analisis_campo.py`
- **Tarea:** integrar el campo al pipeline más allá de lo descriptivo: índice de circulación con incertidumbre (A) y ponderar escenarios por uso real (C)
- **Acción(es):**
  1. **Nuevo `codes/analisis_campo.py`**: única fuente de las cifras de campo. Escribe `campo_resumen.csv` (por marca: n, cuota, **IC 95% de Wilson**, municipios, uso dominante, autonomía/batería/motor medianos, oferta online, mejor modelo y score de la marca) y `campo_uso.csv` (por uso: n, cuota, IC, marcas más vistas)
  2. **A — "más común vs mejor valorado"**: `8_Trabajo_Campo.py` gana una tabla que cruza calle con el ranking y una lectura automática. Resultado: JINPENG manda en calle (6) pero su mejor modelo puntúa 0.651; el mejor valorado es TOPMAQ BRIDERK (0.786) con 3 avistamientos
  3. **IC en los gráficos**: barras con error bar asimétrico (Wilson). El gráfico deja ver que con n=30 el 1º (20% [10-37]) y el 3º (17% [7-34]) no se distinguen
  4. **C — escenarios por uso real**: `7_Mejor_Opcion.py` muestra los 3 usos observados como métricas y **ordena los escenarios por esa frecuencia** (pasajeros 60% primero), con la cuota en el título del expander
  5. **Refactor**: la comparación por marca salió de `analisis.py` (quedaba duplicada) — ahora `analisis.py` = oferta/identidad y `analisis_campo.py` = campo. Eliminado `comparacion_campo_online_marca.csv`; `data.py` expone `load_campo_resumen`/`load_campo_uso`
  6. Documentado en `2_Metodo.py` (pipeline, regla de incertidumbre), `10_Limitaciones.py` (IC solapados, sin denominador) y `app.py` (orden de ejecución)
- **Resultado:** el campo ya responde la pregunta central sin tocar el scoring: uso dominante = pasajeros (60%), marca más vista = JINPENG (20%), y el desajuste calle/oferta/score queda explícito (VEDCA 24% de anuncios y 3% de calle)
- **Error/éxito:** Éxito. Dos decisiones de diseño: (1) el IC se calcula en el script, no en el gráfico; (2) no se ordena "quién gana" en calle porque los intervalos se solapan — se publica el IC en vez de un ganador falso
- **Lección:** con n=30 el valor de un ranking no está en el orden sino en el intervalo; y una tabla de "más común vs mejor valorado" contesta la pregunta del estudio mejor que dos rankings separados
- **Próxima vez:** pendiente B (promesa vs realidad), E (denominador y cuotas por municipio para la 2ª ronda), F/G (perfil del propietario y repuestos con evidencia)
- **Etiquetas:** campo, analisis-campo, wilson, incertidumbre, mas-comun-vs-mejor, uso-observado, escenarios, refactor, fuente-unica

### Entrada de diario

- **Fecha/contexto:** 2026-10-31 (cierre) — el usuario confirma que **no habrá más trabajo de campo**
- **Tarea:** ajustar todo el proyecto a que la muestra de campo es definitiva y reencuadrar la pregunta central
- **Acción(es):**
  1. **Campo cerrado (decisión 2026-10-31)**: 30 observaciones / 5 municipios / 2026-10-13→25 son la evidencia de calle definitiva. Eliminados todos los textos de "en curso", "pendiente", "3 rutas × 5 municipios ≈ 8h", "15 municipios a cubrir" y "faltan 10 municipios"
  2. `8_Trabajo_Campo.py`: título "Circulación Real (muestra cerrada)"; bloque **"Alcance de la muestra"** con la tabla de los 15 municipios marcados (✅ observado / — no) y dos listas explícitas: qué **se puede** afirmar y qué **NO** (p. ej. "que una marca sea la más común en La Habana")
  3. `10_Limitaciones.py`: la limitación de campo pasa a "muestra cerrada" con `❌ Cerrado por decisión del usuario`; prioridad ALTA→BAJA; la fila "si tuviéramos 15 municipios" ahora dice *Cerrado: no se hará*
  4. `2_Metodo.py` y `app.py`: estado de la fuente = "Cerrado (muestra final)"; el protocolo de captura se conserva como documentación histórica de cómo se procesó (no como plan futuro)
  5. **Reencuadre de la pregunta central** (decisión del usuario): de *"¿Cuál es el triciclo más común en La Habana?, ¿por qué es ese?, ¿existe una mejor opción?"* → **"¿Qué triciclo comprar en La Habana y por qué?"**. "Lo más común" queda como **indicador** (oferta + calle), no como respuesta. Actualizado en portada, `2_Metodo` y el titular 1 de `1_Resumen` ("Lo más ofertado (indicador)")
  6. Consistencia menor: escenario de presupuesto unificado en **<$4000** (1_Resumen decía <$3500 y 7_Mejor_Opcion usa <$4000)
- **Resultado:** el reporte ya no promete algo que no puede entregar (un ranking poblacional de La Habana) y la pregunta central coincide con lo que el estudio sí responde: qué comprar y por qué, con la evidencia de oferta + la foto de calle
- **Error/éxito:** Éxito. `AppTest` 11/11 sin excepciones, `parse_campo --check` OK, servidor real :8601 health 200
- **Lección:** cuando una fuente se cierra por debajo del diseño previsto, lo honesto es **cambiar la pregunta** al alcance real en vez de dejar la pregunta grande con respuestas chicas
- **Próxima vez:** `opencode/HANDOFF.md` está desfasado (2026-10-19); reescribir al cierre de sesión. Nada commiteado: revisión y commit a cargo del usuario
- **Etiquetas:** campo-cerrado, alcance, pregunta-central, decision, limitaciones, coherencia

### Entrada de diario

- **Fecha/contexto:** 2026-10-31 (misma sesión) — el usuario pide reescribir el handoff y "añadir más muestras a catálogos de empresas"
- **Tarea:** ampliar `Data/empresas/` con un catálogo nuevo verificado y refrescar los existentes; reescribir `HANDOFF.md` al estado real
- **Acción(es):**
  1. **Búsqueda de fuentes (verificada con HTTP, sin inventar):** `cubancargos` ya está en `scrape_triciclos` (duplicarlo sería doble conteo); `multiservicesxpress`, `sunwellcaribe`, `cubamax`, `cuballama`, `mallhabana`, `dimecuba` → sin triciclos; `kubazuki` sigue "pronto en línea". **CompraMasonline** (WooCommerce) sí: 11 productos en "Triciclos", 8 son vehículos
  2. **Nuevo `scrape_compramasonline()`** en `codes/scrape_empresas.py`: excluye los 2 "Extensor de rango" sueltos y el "Minicarrito" (4 ruedas); specs de la pestaña de descripción; precio actual con `ins` (rebajas); marca desde la etiqueta `Marca:` (cortando en la siguiente etiqueta de la plantilla, p. ej. "Talla")
  3. **Tres reglas nuevas, en el scraper (no a mano):** (a) `_cma_bateria` prioriza la etiqueta "Batería" para no confundir el cargador `AC110V` con la batería; (b) `_cma_propulsion` prioriza "Tipo de conducción" porque las fichas son plantillas con `Desplazamiento: <110cc` y todo saldría híbrido; (c) `_cma_carga` solo acepta etiquetas de capacidad de carga (nunca peso neto/bruto)
  4. **Autonomía:** el patrón ahora reconoce `Gama` y `Kilómetros por carga` (sin unidad repetida). Recupera 2 datos reales en KikiHabana (ONEBOT T414 85 km, HUAIHAI 120 km) y ONEBOT de CompraMasonline (113 km)
  5. **Refresco completo** de los 4 catálogos previos: sin altas/bajas; solo 2 precios MZ (+$20/+$100) y las 2 autonomías. Total **30 fichas / 5 empresas**
  6. **Integración:** `norm_modelo.py` copia también `compramasonline` a `clean_data`; `crear_canonicos.py` lo lee; **`reporte/data.py` descubre las empresas por glob** (ya no hay lista fija); tabla canónica **99 productos**; cifras 22→30 en `app.py`, `2_Metodo`, `9_Empresas`, `10_Limitaciones`
  7. **`HANDOFF.md` reescrito** (2026-10-31): pregunta central nueva, campo cerrado, pipeline con `analisis_campo`, empresas 30/5, 99 canónicos, pendientes y advertencias
- **Resultado:** el catálogo de empresas crece un 36% (22→30) con datos verificados; el scoring **no cambia** (md5 idéntico); 11/11 páginas OK; `norm_modelo --check` y `parse_campo --check` limpios
- **Error/éxito:** Éxito. Decisiones anotadas para el usuario: RALLY marcado **híbrido** (extensor de gasolina en el título) y los dos "TRICICLO ELÉCTRICO DE CARGA"/"…MINGHONG" comparten identidad MINGHONG con precios distintos
- **Lección:** clasificar con el texto completo de estas fichas engaña (plantillas con `110cc` y bloques de accesorios copiados): hay que dar prioridad a las etiquetas explícitas ("Tipo de conducción", "Batería", "Marca") y dejar `null` lo que no está declarado
- **Próxima vez:** revisar/commitear; decidir la colisión MINGHONG y si empresas entra al scoring
- **Etiquetas:** empresas, compramasonline, scraper, woocommerce, autonomia, bateria, identidad, canonicos, handoff

### Entrada de diario

- **Fecha/contexto:** 2026-10-31 (cierre de sesión) — el usuario confirma RALLY híbrido, excluir el genérico, dejar el nombre "RALLY", integrar empresas con A + B y quitar los pendientes del reporte
- **Tarea:** cerrar las decisiones abiertas de CompraMasonline, integrar los catálogos al pipeline sin tocar el score y limpiar la página de limitaciones
- **Acción(es):**
  1. **Decisiones aplicadas en el origen:** `EXCLUIDOS` de `crear_canonicos.py` incluye el genérico "TRICICLO ELÉCTRICO DE CARGA" (sin modelo propio, duplicaba MINGHONG); `OVERRIDES` fija `("RALLY","RALLY")`. `scrape_empresas compramasonline` baja a **7 fichas**; la tabla canónica queda en **98 productos** (2 excluidos)
  2. **(A) Proxy de repuestos con empresas:** `calcular_repuestos_proxy(df_online, df_empresas)` y `load_empresas_online()` en `codes/analisis.py`. Los 5 catálogos suman fuentes, pero el proxy sigue en **9/42** porque ningún modelo cruza
  3. **(B) Contexto de catálogo en el ranking:** `integrar_empresas()` añade `n_empresas`, `precio_empresa_med`, `en_catalogo` (nivel modelo) y `marca_en_catalogo`, `n_empresas_marca` (nivel marca). El score no cambia (columna `score` idéntica, 42 filas)
  4. **Hallazgo mostrado, no maquillado:** modelos de catálogo y anuncios **no comparten identidad**; solo la marca **ONEBOT** cruza (3 modelos). Ranking y Contendientes muestran la marca en catálogo y ocultan las columnas de modelo vacías; la página 9 avisa de que no hay modelos en común y no compara precios
  5. **Limpieza del reporte:** eliminada la sección "Pendientes técnicos (datos)" de `10_Limitaciones.py`; renumeradas las secciones 1→5 y título "Limitaciones" (sin "y Pendientes")
  6. **Cifras corregidas a 29 fichas / 98 productos** en `app.py`, `2_Metodo`, `9_Empresas`, `10_Limitaciones` y `HANDOFF.md`
- **Resultado:** pipeline con A + B, score intacto, reporte sin pendientes y con el contexto de catálogo visible donde sí aporta (marca). `AppTest` 11/11, `parse_campo --check` OK, `crear_canonicos --check` estable
- **Error/éxito:** Éxito. Aporta un dato honesto: la oferta formal de importación y el mercado de clasificados son universos casi disjuntos
- **Lección:** un cruce que devuelve 0 no es un fallo del código: es un resultado. Se muestra el vacío con su explicación en vez de forzar equivalencias por marca
- **Próxima vez:** revisar/commitear; decidir si empresas entra al scoring completo (cambiaría extremos min-max y exige antes/después)
- **Etiquetas:** empresas, integracion, repuestos-proxy, ranking, limitaciones, decisiones, canonicos

### Entrada de diario

- **Fecha/contexto:** 2026-10-31 (cierre) — ampliación de catálogos de empresas y revisión final del reporte
- **Tarea:** sumar catálogos verificados sin tocar el scoring, cerrar la identidad de las variantes nuevas y dejar las cifras coherentes en todo el reporte
- **Acción(es):**
  1. **Cinco scrapers nuevos en `codes/scrape_empresas.py`:** `mundoenvio` (10; excluye el cuatriciclo de 4 ruedas), `patuisla` (11; specs en `.summary` cuando la pestaña solo trae el envío), `francismotors` (11 desde JSON-LD: 3 gasolina, 4 híbridos, 4 eléctricos), `bluewavecuba` (5 desde `<dt>/<dd>`; el "extensor de autonomía" es generador → híbrido) y `zonalibreonline` (2 desde JSON-LD + `og:image:alt`)
  2. **Helpers en el origen:** rangos → límite inferior (motor, autonomía, carga, precio); separadores de miles; `bateria_v` sin `ah` deja `ah=null`; `motor_w > 20000` se descarta con nota (MIGHONG "25000W"); "extensor de autonomía/rango" no contamina la autonomía
  3. **Identidad:** `crear_canonicos.py` gana `OVERRIDES` para las 39 URLs nuevas y `norm_modelo.py --migrar` descubre empresas por glob. Tabla canónica: **137 productos / 3 excluidos / 126 con nombre**
  4. **Variantes separadas (decisión del usuario):** RALLY HIBRIDO ≠ RALLY CARGA ≠ RALLY CARGA 800; CYT 80 KM ≠ CYT 100 KM; MIGHONG 400 KG ≠ MIGHONG 600 KG; IZUKI 120 AH ≠ IZUKI 127 AH. Tras el split no queda ninguna identidad multi-fuente con specs declaradas distintas
  5. **Reporte:** 68 fichas / 10 catálogos en `app.py`, `2_Metodo`, `9_Empresas` y `10_Limitaciones`; nota de marcas que cruzan (ONEBOT, TOPMAQ, VEDCA, MISHOZUKI); corregidas las filas obsoletas de versionado y la lista de empresas
  6. **Verificación:** `AppTest` 11/11; `crear_canonicos --check` estable; `norm_modelo --migrar` → 0 heurísticos y 0 "revisar"; `analisis.py` → 42 filas y score idéntico (TOPMAQ BRIDERK 0.786)
- **Resultado:** 68 fichas de 10 catálogos, identidad sin colisiones y reporte coherente; el score no cambia
- **Error/éxito:** Éxito. El campo `n_empresas` sigue en 0 (ningún modelo cruza con anuncios); solo hay cruce a nivel de marca, y así se muestra
- **Lección:** el mismo nombre comercial puede esconder specs incompatibles entre vendedores; separar por el dato declarado evita promedios que nadie publicó
- **Próxima vez:** revisar/commitear los 5 JSONL nuevos, sus copias en `clean_data`, los scrapers, la tabla canónica y las páginas del reporte
- **Etiquetas:** empresas, scrapers, canonicos, variantes, reporte, verificacion

### Entrada de diario

- **Fecha/contexto:** 2026-10-31 (cierre documental) — tras aplicar el split de variantes y la revisión final del reporte
- **Tarea:** dejar `HANDOFF.md` y el diario sincronizados con el estado real antes de que el usuario commitee
- **Acción(es):**
  1. Confirmado el split RALLY/CYT/MIGHONG/IZUKI en `crear_canonicos.py`; ninguna identidad multi-fuente queda con specs declaradas distintas
  2. Verificación final: `AppTest` 11/11, `parse_campo --check` OK, `norm_modelo --migrar` sin heurísticos, copias `empresas/`↔`clean_data/` idénticas, score 42 filas intacto
  3. Corregidos dos encabezados mal formados del diario (`---### Entrada` → `---` + `### Entrada`)
- **Resultado:** documentación al día; 68 fichas / 10 catálogos, 137 canónicos (126 con nombre, 3 excluidos)
- **Error/éxito:** Éxito. Sin cambios de datos en este paso
- **Lección:** el cierre documental debe registrar el HEAD real y qué queda sin commitear, no solo las cifras
- **Próxima vez:** revisar/commitear; no tocar `Data/raw_data/data_personas.txt` (PII)
- **Etiquetas:** journaling, handoff, cierre, git, verificacion
