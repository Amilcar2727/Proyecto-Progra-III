# Sistema de Gestión de Rutas Óptimas en Cusco

**Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**  
Facultad de Ingeniería Eléctrica, Electrónica, Informática y Mecánica  
Escuela Profesional de Ingeniería Informática y de Sistemas  
**Asignatura:** Programación III (2026-II)  
**Proyecto:** Primer Examen Parcial  

Aplicación de escritorio en Python con interfaz gráfica Tkinter (`ttk`) y visualización en mapa interactivo con `tkintermapview` (y fallback offline en `Canvas 2D`), orientada a la gestión logística y optimización multiparadigma de rutas de reparto en la ciudad de Cusco.

## Modelo híbrido de rutas

Los nodos del grafo de los algoritmos siguen siendo los 20 lugares de interés. Las 64 conexiones dirigidas del cache actual representan caminos por calles de OpenStreetMap: el peso es la suma de longitudes OSM en metros y cada arco conserva una polilínea con la geometría vial. La red urbana completa se descarga y procesa solo en el constructor offline; la aplicación carga `data/red_vial_cache.json` y no necesita OSMnx, NetworkX ni Internet para calcular rutas.

Dijkstra, implementado a mano, precalcula las distancias mínimas dirigidas entre lugares. Greedy, Held-Karp, D&C, el orden por distancia y Backtracking usan esos pesos. Haversine queda para la asignación de pedidos a un lugar de interés y para comparar línea recta con recorrido por calles. La GUI muestra por arista el factor de desvío `longitud de red / distancia Haversine`.

El cache se descargó el **19 de octubre de 2026** con `network_type="drive"`. Los resultados son un snapshot de OSM y reflejan los nodos ajustados a la intersección más cercana; los cierres de calle bloquean la conexión entre lugares de interés, no un tramo OSM individual. `drive` no modela restricciones peatonales. Atribución: © OpenStreetMap contributors (ODbL).

---

## 🚀 Requisitos e Instalación

### Requisitos Previos
- Python 3.10 o superior (validado en Python 3.13 en Windows 64-bit).
- Gestor de paquetes `pip`.

### Instalación de Dependencias

Clona o descarga el repositorio y ejecuta en la terminal del proyecto:

```bash
pip install -r requirements.txt
```

Las dependencias permitidas y utilizadas son:
- `tkintermapview` (≥ 1.28): Motor de mapas interactivo con tiles de OpenStreetMap / Google Maps.
- `matplotlib` (≥ 3.8.0): Gráficos empíricos comparativos incrustados en Tkinter.
- `Pillow` (≥ 10.0.0): Manipulación y rasterización de imágenes y tiles.
- `pytest` (≥ 8.0.0): Suite de pruebas unitarias automatizadas.

Para construir o verificar el cache (solo desarrollo; no es necesario para ejecutar la app):

```bash
pip install -r requirements-dev.txt
python tools/construir_red_vial.py
python tools/verificar_red_vial.py
```

El constructor requiere conexión con Overpass. Revisa en su salida cualquier snap a más de 60 m y confirma las coordenadas propuestas antes de aceptar el cache.

---

## 💻 Ejecución de la Aplicación

Para iniciar la aplicación principal:

```bash
python main.py
```

### Ejecución de Pruebas Unitarias
Para correr la suite completa de pruebas automatizadas:

```bash
pytest -v
```

### Ejecución de Benchmarks Reales
Para regenerar las mediciones de rendimiento y exportar a `benchmarks/resultados_benchmark.json`:

```bash
python benchmarks/benchmark.py
```

---

## 📁 Estructura del Proyecto

```text
rutas_cusco/
├─ main.py                      # Punto de entrada de la aplicación
├─ config.py                    # Constantes de configuración, mapa, colores y umbrales
├─ requirements.txt             # Dependencias del proyecto
├─ requirements-dev.txt         # OSMnx y NetworkX: solo para construir datos offline
├─ pytest.ini                   # Configuración para ejecución de pytest
├─ conftest.py                  # Resolución de rutas de importación en pruebas
│
├─ data/                        # Conjuntos de datos en formato JSON
│  ├─ nodos_cusco.json          # Coordenadas originales de los 20 lugares de interés
│  ├─ red_vial_cache.json       # Pesos dirigidos, snaps, geometrías y metadatos OSM
│  ├─ pedidos.json              # 30 pedidos de muestra (prioridades, pesos, valores)
│  └─ repartidores.json         # 3 repartidores con capacidad y vehículos
│
├─ core/                        # LÓGICA ALGORÍTMICA MANUAL (sin librerías de grafos)
│  ├─ modelos.py                # Dataclasses: Nodo, Arista, Grafo, Pedido, Repartidor, Ruta
│  ├─ geo.py                    # Fórmula de Haversine esférica en metros y centroides
│  ├─ grafo.py                  # Dijkstra, matriz de distancias y geometría de rutas
│  ├─ estructuras.py            # Merge Sort, Quick Sort, Búsqueda Binaria, Índices O(1)
│  ├─ greedy.py                 # Vecino Más Cercano (TSP) y Asignación de Emergencia
│  ├─ divide_venceras.py        # Partición 2D recursiva por mediana + Teorema Maestro
│  ├─ prog_dinamica.py          # Mochila 0/1 (tabla + reconstrucción) y Held-Karp (TSP Bitmask)
│  └─ backtracking.py           # DFS exhaustivo con poda por cota superior (Branch & Bound)
│
├─ gui/                         # INTERFAZ GRÁFICA DE USUARIO (Tkinter + ttk)
│  ├─ app.py                    # Ventana principal con ttk.Notebook multiresistente
│  ├─ componente_mapa.py        # Componente que envuelve mapa y conmutación offline
│  ├─ canvas_fallback.py        # Fallback offline en Canvas 2D si falla la red
│  ├─ tab_mapa.py               # Red vial interactiva y bloqueo/reapertura de calles
│  ├─ tab_pedidos.py            # Tabla de pedidos, formulario de alta, ordenación y búsqueda
│  ├─ tab_greedy.py             # Planificación voraz y despacho urgente
│  ├─ tab_dyv.py                # Segmentación espacial en zonas de color y ensamble
│  ├─ tab_pd.py                 # Matriz visual Mochila 0/1 y Held-Karp vs Greedy en hilo
│  ├─ tab_backtracking.py       # Exploración de rutas simples con métricas de podas
│  └─ tab_comparacion.py        # Gráficos Matplotlib incrustados (Tiempo vs N, Calidad vs N)
│
├─ benchmarks/
│  ├─ benchmark.py              # Suite de medición empírica de tiempos y calidad
│  └─ resultados_benchmark.json # Datos reales exportados de corridas empíricas
│
├─ tools/
│  ├─ construir_red_vial.py     # Descarga OSM y genera el cache offline (solo desarrollo)
│  └─ verificar_red_vial.py     # Tabla de desvíos y PNG de polilíneas
│
├─ tests/                       # Pruebas unitarias, de Dijkstra y del cache vial
│  ├─ test_estructuras.py       # Pruebas de MergeSort, QuickSort y búsquedas
│  ├─ test_greedy.py            # Pruebas de vecino más cercano y despacho
│  ├─ test_dyv.py               # Pruebas de partición espacial y ensamble
│  ├─ test_pd.py                # Pruebas de Mochila clásica y Held-Karp
│  ├─ test_backtracking.py      # Pruebas de exploración y podas en diamante
│  └─ test_grafo.py             # Dijkstra, conectividad, cierres y geometría vial
│
└─ docs/                        # DOCUMENTACIÓN TÉCNICA Y SUSTENTACIÓN
   ├─ informe.md                # Informe técnico formal con rigor matemático y derivaciones
   └─ guia_defensa.md           # Guion de demo de 5 min y preguntas trampa con respuestas
```

---

## 🎯 Paradigmas Algorítmicos Evaluados

| Paradigma | Algoritmo | Complejidad Temporal | Complejidad Espacial | Característica Clave |
| :--- | :--- | :---: | :---: | :--- |
| **Estructuras** | Merge Sort | $O(n \log n)$ | $O(n)$ | Ordenamiento estable manual |
| **Estructuras** | Quick Sort | $O(n \log n)$ prom | $O(\log n)$ | Partición Lomuto con mediana de 3 |
| **Estructuras** | Búsqueda Binaria | $O(\log n)$ | $O(1)$ | Búsqueda sobre lista ordenada |
| **Greedy** | Vecino Cercano | $O(n^2)$ | $O(n)$ | Heurística voraz para TSP |
| **Greedy** | Asignación Urgente | $O(R) \to O(1)$ | $O(1)$ | Mínima distancia con capacidad |
| **Divide y Vence** | Partición Espacial 2D | $O(n \log n)$ | $O(n)$ | Mediana alternada, Teorema Maestro Caso 2 |
| **Prog. Dinámica** | Mochila 0/1 | $O(N \cdot W)$ | $O(N \cdot W)$ | Matriz DP bidimensional y reconstrucción |
| **Prog. Dinámica** | Held-Karp TSP | $O(n^2 2^n)$ | $O(n 2^n)$ | Bitmask y memoización para $N \le 12$ |
| **Backtracking** | Rutas con Poda | $O(V!)$ podado | $O(V)$ | Poda Branch & Bound por costo parcial |

## Verificación de rutas por calles

`python tools/verificar_red_vial.py` imprime para cada arco la distancia Haversine, la longitud vial y el factor de desvío, y genera `data/red_vial_verificacion.png`. En el cache actual el desvío medio por arco es **1.646×**; los extremos son **1.014×** (N12→N14) y **5.854×** (N07→N01). Por ejemplo, el camino N09→N12 se representa como N09→N11→N12, no como una recta.
