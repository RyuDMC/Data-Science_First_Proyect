# Ética, privacidad y legalidad del scraping

Este proyecto es público y usa datos de terceros. Este documento fija qué se
hace, qué no se hace y qué queda pendiente. No sustituye una revisión legal.

## 1. Datos personales

- **Trabajo de campo:** la hoja original (`Data/raw_data/data_personas.txt`)
  contiene nombre y carné de identidad. Está **ignorada por git** y
  `codes/parse_campo.py` la anonimiza: descarta nombre y CI y conserva solo
  `obs_id`, municipio, uso, marca y specs del vehículo.
- **Anuncios:** se publican URLs de publicaciones y texto de `legalizacion`.
  Ese texto puede incluir teléfonos, carnés o nombres de vendedores. Los datos
  personales detectados se redactan (`[DATO PERSONAL REDACTADO]`); en
  `legalizacion` apareció un **CI mal escrito de 8 dígitos** (no era un
  teléfono) y se sustituyó. `tests/test_privacidad.py` bloquea CI de 11
  dígitos, números de 8 dígitos tipo móvil o CI incompleto, `+53` y números
  tras "WhatsApp".
- **Regla:** si un dato identifica a una persona y no es imprescindible para la
  pregunta de mercado, no se publica.

## 2. Scraping

- Se capturan catálogos públicos y anuncios de Facebook con un User-Agent de
  navegador y pausas entre peticiones (`time.sleep`, backoff exponencial).
- **Pendiente:** revisar los términos de servicio de cada fuente y `robots.txt`
  antes de volver a ejecutar los scrapers. Este repo no incluye un registro de
  esa revisión.
- **No hacer:** eludir autenticación, capturar datos privados, martillear un
  servidor sin pausas o revender los datos.

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

No hay `LICENSE`. Sin licencia explícita, el código y los datos quedan bajo
"todos los derechos reservados": nadie puede reutilizarlos legalmente. La
decisión de licencia corresponde al autor; si se quiere permitir reutilización,
MIT/Apache-2.0 para código y CC-BY-4.0 para datos son opciones habituales
(verificar compatibilidad con las fuentes originales).
