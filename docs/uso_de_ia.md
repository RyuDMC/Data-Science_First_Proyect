# Declaración de uso de IA

Este documento declara qué parte del proyecto se hizo con asistencia de IA y
qué parte es responsabilidad del autor. No sustituye la revisión del autor ni
la defensa oral del trabajo.

## Herramienta

- **OpenCode** (agente de código en terminal).
- Modelo: **DeepSeek V4.1 Flash Free**.
- Sesiones de trabajo: 2026-10-31 a 2026-11-08, sobre el repositorio
  `Data-Science_First_Proyect`.

## Tareas en las que participó la IA

- Escribir y revisar código de `codes/` y `reporte/` (scoring, sensibilidad,
  Pareto, páginas de Streamlit).
- Corregir errores: imputación NaN en `sensibilidad.py`, selección del podio
  por propulsión, frontera de Pareto, `--check` de la tabla canónica y
  migración no destructiva de `norm_modelo.py`.
- Añadir y ampliar tests (`tests/`), el workflow de CI y documentación
  (`README.md`, `docs/`).
- Redactar borradores de limitaciones, ética y privacidad.
- Ejecutar verificaciones: `pytest`, `generar_metadata.py --check`,
  `crear_canonicos.py --check` y compilación de los módulos.

## Qué verificó el autor

El autor define la pregunta de investigación, los pesos del score, la
identidad de los modelos, el alcance del trabajo de campo y las decisiones
metodológicas. Antes de publicar, el autor debe revisar:

- Que entiende **por qué** cada peso tiene el valor que tiene y qué pasa si
  cambia.
- Que puede explicar la diferencia entre **oferta anunciada** y **circulación
  observada**, y por qué no se extrapola el campo a toda La Habana.
- Que sabe defender la decisión de **re-ponderar solo los criterios presentes**
  en vez de imputar 0.5, y su efecto en los 7 modelos sin precio USD.
- Que conoce las limitaciones que el propio repo declara: n=40 modelos, 25 con
  un solo anuncio, campo cerrado con n=30 en 5 municipios, legalidad medida
  como mención y repuestos como proxy.
- Que revisó los textos y las cifras que llevan su nombre.

## Qué no debe hacer el autor

- Presentar el código o los textos generados como si los hubiera escrito
  íntegramente sin asistencia.
- Usar una cifra del reporte sin poder explicar de qué archivo sale y cómo se
  calcula.
- Omitir que la IA participó en la revisión y corrección de los errores.

## Verificación reproducible

```bash
python -m pytest -q tests/
python codes/generar_metadata.py --check
python codes/crear_canonicos.py --check
```

La suite y los `--check` son la evidencia mínima. Si el autor no puede
explicar un cambio, ese cambio no está defendido, aunque los tests pasen.
