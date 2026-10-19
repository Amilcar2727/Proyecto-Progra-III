# PENDIENTES.md — Estado del informe

## Hecho (19/10/2026)

- [x] Capítulos actualizados al modelo vial real (OSM + Dijkstra); ya no se describe un grafo simulado.
- [x] Análisis Big-O corregido: partición D&C Θ(n log² n), ruta por zonas O(n²/K), emergencia O(R), backtracking O(b^d) / O(V·V!).
- [x] Tabla de casos de prueba con resultados esperados (Tabla 7.2).
- [x] Benchmarks regenerados (`benchmarks/resultados_benchmark.json`) y figuras 1-4 (`python informe/generar_figuras.py`).
- [x] Capturas de la GUI en `informe/figuras/gui/` (generadas con `python tools/prueba_gui.py --capturas informe/figuras/gui`) y Anexo D.
- [x] `main.pdf` recompilado.

## Por revisar antes de entregar

- [ ] Portada: autores y docente/asesor (los docentes del curso son M.Sc. Hector E. Ugarte R. y M.Sc. Boris Chullo Llave).
- [ ] Si se vuelve a correr el benchmark, los tiempos cambian y hay que actualizar las tablas del Capítulo 7 (las conclusiones no cambian).
- [ ] Confirmar en campo los ocho lugares cuyo ajuste vial supera 60 m (Anexo B).

## Compilar

```bash
cd informe
latexmk -pdf main.tex
```
