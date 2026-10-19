# PENDIENTES.md — Capturas de pantalla de la GUI para el Anexo D

Este archivo lista las capturas de pantalla de la interfaz gráfica que deben
tomarse manualmente y añadirse al informe como Anexo D antes de la entrega.

## Capturas requeridas (tomar con la app `main.py` corriendo)

| # | Pestaña / Acción | Nombre sugerido del archivo | Descripción |
|---|---|---|---|
| 1 | **Inicio — Pestaña Mapa** | `captura_01_mapa_inicial.png` | Vista del grafo de 20 nodos de Cusco con todos los nodos y aristas visibles, sin ninguna ruta calculada. |
| 2 | **Pestaña Pedidos** | `captura_02_tabla_pedidos.png` | Tabla con los 30 pedidos cargados, mostrando columnas de ID, cliente, sector, prioridad y peso. |
| 3 | **Algoritmo Greedy — resultado** | `captura_03_ruta_greedy.png` | Mapa con la ruta Greedy trazada (línea azul) para los primeros 8 pedidos activos. Debe verse la distancia total en el panel lateral. |
| 4 | **Algoritmo Held-Karp — resultado** | `captura_04_ruta_held_karp.png` | Mapa con la ruta óptima Held-Karp (línea roja/rosa) para los mismos 8 pedidos. Comparar visualmente la diferencia con la ruta Greedy. |
| 5 | **Algoritmo Backtracking — calle bloqueada** | `captura_05_backtracking_bloqueo.png` | Escenario con al menos una arista bloqueada (marcada en rojo en el mapa) y la ruta alternativa encontrada por Backtracking. |
| 6 | **Pestaña Comparación — gráficos** | `captura_06_comparacion_benchmarks.png` | Pestaña de benchmarks mostrando los gráficos de barras y líneas de tiempo vs n y calidad de ruta. |
| 7 | **Pestaña Pedidos — Knapsack** | `captura_07_knapsack_seleccion.png` | Panel mostrando el resultado del Knapsack: qué pedidos fueron seleccionados y cuáles excedían la capacidad. |
| 8 | **Merge Sort — panel de ordenación** | `captura_08_merge_sort.png` | Resultado del ordenamiento por distancia al depósito mostrando la lista ordenada de pedidos. |

## Instrucciones para tomar capturas en Windows 11

1. Ejecutar la aplicación: `python main.py` desde el directorio raíz del proyecto.
2. Usar la herramienta **Recorte y anotación** (Win+Shift+S) o la tecla **Print Screen**.
3. Guardar las capturas como PNG en `informe/figuras/gui/`.
4. Añadir al `informe/contenido/cap_09_anexos.tex` la sección:

```latex
\section*{Anexo D: Capturas de la Interfaz Gráfica}
\begin{figure}[h]
  \centering
  \caption[Vista del mapa inicial]{Vista del grafo de Cusco al iniciar la aplicación.}
  \includegraphics[width=140mm]{figuras/gui/captura_01_mapa_inicial.png}
\end{figure}
% (repetir para cada captura)
```

## Estado actual

- [x] Figuras de benchmark generadas automáticamente (`fig1_tiempo_vs_n.png`, `fig2_calidad_ruta.png`, `fig3_backtracking.png`)
- [ ] Capturas de la GUI (requieren ejecución manual de `main.py`)
- [ ] Añadir capturas al Anexo D del informe

## Nota

Las capturas de la GUI son el único componente del informe que no puede generarse
automáticamente, ya que requieren la interacción visual con la aplicación en ejecución.
El PDF `informe/main.pdf` existente es anterior a la actualización del modelo híbrido; después de revisar las secciones LaTeX indicadas arriba, se debe volver a compilarlo.

## Actualización pendiente por el modelo híbrido vial

No editar los archivos LaTeX como parte de este cambio. Antes de la próxima compilación del informe, actualizar estas secciones para que describan el cache vial y los resultados actuales:

| Área | Archivo LaTeX a revisar | Cambios requeridos |
|---|---|---|
| Datos y delimitación | `contenido/cap_01_introduccion.tex`, `contenido/cap_02_planteamiento_problema.tex` | Sustituir la descripción de distancias en línea recta/grafo simulado por 20 lugares de interés y conexiones dirigidas por calles; indicar el snapshot OSM, el perfil `drive` y la atribución ODbL. |
| Modelo y metodología | `contenido/cap_04_marco_teorico.tex`, `contenido/cap_06_metodologia.tex` | Describir el enfoque híbrido, generación offline del cache, mayor componente fuertemente conexa, ajuste de coordenadas, Dijkstra manual y matriz asimétrica. Aclarar que Haversine solo se usa para asignación, partición espacial y comparación. |
| Hipótesis | `contenido/cap_05_hipotesis.tex` | Revisar afirmaciones/umbrales de calidad que se calcularon con distancias Haversine y contrastarlas con los nuevos benchmarks de red vial. |
| Resultados y discusión | `contenido/cap_07_resultados_discusion.tex`, `contenido/cap_08_conclusiones_recomendaciones.tex` | Regenerar tablas y figuras con `benchmarks/resultados_benchmark.json`; reportar resultados antes/después, factores de desvío, tiempos y limitaciones de snaps/cierres/datos `drive`. |
| Anexos | `contenido/cap_09_anexos.tex` | Añadir la tabla/figura de verificación vial y capturas actualizadas de la GUI cuando estén disponibles. |

Al revisar el modelo de datos, confirmar especialmente los ocho nodos cuyo ajuste vial supera 60 m. El JSON conserva las coordenadas originales, las coordenadas ajustadas y las propuestas de corrección; no asumir que las propuestas fueron aprobadas como ubicaciones finales.
