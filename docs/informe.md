# INFORME TÉCNICO DE PROYECTO
## Sistema de Gestión de Rutas Óptimas en Cusco: Enfoque Multiparadigma

**Institución:** Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)  
**Facultad:** Facultad de Ingeniería Eléctrica, Electrónica, Informática y Mecánica  
**Escuela Profesional:** Ingeniería Informática y de Sistemas  
**Asignatura:** Programación III (Semestre 2026-II)  
**Proyecto:** Primer Examen Parcial / Proyecto Práctico  
**Fecha:** Octubre de 2026  

---

## 1. Introducción y Descripción del Sistema

La optimización de rutas de distribución urbana es un desafío computacional de primer orden en la logística contemporánea, catalogado formalmente dentro de la familia de problemas NP-Hard. En ciudades históricas y de geografía compleja como **Cusco**, las restricciones urbanas (calles peatonales, pendientes pronunciadas, vías angostas y obras de mantenimiento frecuentes) impiden la aplicación ingenua de heurísticas universales.

El presente proyecto implementa el **"Sistema de Gestión de Rutas Óptimas en Cusco"**, una aplicación de escritorio modular desarrollada en Python 3.13 con interfaz gráfica en Tkinter (`ttk`) y visualización geoespacial con `tkintermapview` (con soporte de conmutación a tiles de OpenStreetMap y Google Maps, además de un mecanismo de fallback autónomo a `Canvas` vectorial 2D para operación fuera de línea).

El núcleo del sistema gestiona una flota de despacho y una cartera de pedidos distribuidos sobre un grafo de **20 nodos representativos de Cusco** (Plaza de Armas, San Blas, Coricancha, Mercado San Pedro, Santiago, Wanchaq, UNSAAC, San Sebastián, etc.) y **64 conexiones dirigidas** en el cache vial actual.

### Restricción Fundamental de Ingeniería
Los algoritmos centrales fueron implementados **a mano**. En particular, Dijkstra no delega la búsqueda en una biblioteca: `heapq` se usa únicamente como cola de prioridad. NetworkX y OSMnx se reservan para el script de desarrollo que construye el cache; no son dependencias de ejecución y la aplicación no descarga datos.

### 1.1. Modelo híbrido: lugares de interés sobre red vial

Los 20 lugares siguen siendo los vértices usados por Greedy, Held-Karp, D&C y Backtracking. Un arco dirigido entre dos lugares representa el camino más corto encontrado entre sus puntos ajustados sobre la red vial de OpenStreetMap; el peso es la suma de `length` de sus tramos en metros y su geometría es una polilínea que conserva las curvas de las calles. El cache actual tiene 64 arcos, con grado de salida entre 3 y 4; se parte de los tres vecinos más próximos por distancia de red y se añaden únicamente conexiones necesarias para mantener la conectividad fuerte.

El script `tools/construir_red_vial.py` descarga una sola vez la red `drive`, obtiene su mayor componente fuertemente conexa, ajusta los lugares y escribe `data/red_vial_cache.json`. La app carga ese JSON sin OSMnx ni Internet. Dijkstra, implementado manualmente, produce la matriz dirigida de distancias mínimas y reconstruye los caminos entre lugares. Su complejidad es $O((V+E)\log V)$ en tiempo y $O(V)$ en espacio por origen. Cuando `RESPETAR_SENTIDOS = True`, una ruta A→B puede diferir de B→A; si es `False`, el cache se simetriza con la menor longitud entre ambos sentidos.

Haversine **no es un peso de los algoritmos**: se conserva para asignar pedidos por coordenadas al lugar de interés más cercano, para la partición espacial de D&C y como distancia de comparación. Para cada arco se informa el factor de desvío `longitud de red / distancia Haversine`. En el cache actual el promedio es **1.646×**, el mínimo **1.014×** (N12→N14) y el máximo **5.854×** (N07→N01). La conexión N09→N12 no es un arco directo: la ruta por la red de interés actual es N09→N11→N12, de **1,961.56 m**.

**Limitaciones y procedencia:** ocho nodos quedaron a más de 60 m de la calle más cercana y deben revisarse con conocimiento local; sus coordenadas originales se conservaron y el cache documenta la propuesta de ajuste. El cierre interactivo bloquea la conexión entre dos lugares de interés (y su inversa), no un segmento individual de la red OSM. Los datos corresponden al snapshot descargado el 19 de octubre de 2026 y pueden quedar desactualizados. El perfil `drive` modela circulación vehicular y no contempla restricciones peatonales. Atribución de datos: © OpenStreetMap contributors (ODbL).

---

## 2. Paradigmas Algorítmicos Implementados

### 2.1. Estructuras de Datos, Ordenamiento y Búsqueda

#### A. Merge Sort (Ordenamiento por Mezcla)
- **Paradigma:** Divide y Vencerás (D&C).
- **Idea:** Divide recursivamente el arreglo por la mitad ($n/2$) hasta alcanzar arreglos unitarios, y luego los fusiona mediante dos punteros comparando los valores de clave.
- **Pseudocódigo:**
  ```text
  Función MergeSort(A):
      si longitud(A) <= 1: retornar A
      medio = longitud(A) // 2
      izq = MergeSort(A[0 .. medio-1])
      der = MergeSort(A[medio .. final])
      retornar Mezclar(izq, der)

  Función Mezclar(izq, der):
      res = []
      mientras i < len(izq) y j < len(der):
          si clave(izq[i]) <= clave(der[j]):
              res.agregar(izq[i]); i++
          sino:
              res.agregar(der[j]); j++
      concatenar elementos restantes
      retornar res
  ```
- **Derivación de Complejidad:**
  - Árbol de recursión de altura $\log_2(n)$.
  - En cada nivel de profundidad, la unión de los subarreglos recorre exactamente $n$ elementos.
  - **Tiempo:** $O(n \log n)$ en mejor, promedio y peor caso (estable).
  - **Espacio:** $O(n)$ memoria auxiliar requerida para la mezcla de subarreglos.

#### B. Quick Sort (Ordenamiento Rápido)
- **Paradigma:** Divide y Vencerás con partición in-place.
- **Idea:** Selecciona un elemento pivote mediante la heurística de mediana de tres (primero, medio y último) para evitar el peor caso cuadrático en arreglos preordenados. Particiona el arreglo ubicando elementos menores a la izquierda y mayores a la derecha.
- **Derivación de Complejidad:**
  - **Tiempo Promedio:** $O(n \log n)$, asumiendo particiones balanceadas.
  - **Peor Caso:** $O(n^2)$ cuando el pivote divide el problema en $1$ y $n-1$.
  - **Espacio:** $O(\log n)$ en la pila de llamadas de recursión.

#### C. Búsquedas
1. **Búsqueda por ID en $O(1)$:** Implementada mediante tabla hash (diccionario Python) con clave `id` del pedido. Tiempo medio de acceso $O(1)$, espacio $O(n)$.
2. **Búsqueda Binaria por ID en $O(\log n)$:** Requiere que la lista esté previamente ordenada por ID mediante QuickSort. Descarta la mitad del espacio de búsqueda en cada iteración:
   $$T(n) = T(n/2) + O(1) \implies O(\log n)$$
   Espacio auxiliar: $O(1)$ iterativo.
3. **Índice Invertido por Sector:** Mapeo `sector -> lista[Pedido]`. Construcción en $O(n)$, consulta de los pedidos de un sector en $O(1)$.

---

### 2.2. Paradigma Voraz (Greedy)

#### A. Heurística del Vecino Más Cercano (Nearest Neighbor TSP)
- **Paradigma:** Greedy (Voraz).
- **Idea:** Partiendo de la posición inicial, selecciona iterativamente el pedido pendiente con menor distancia mínima por calles, consultada en la matriz dirigida de Dijkstra. No reconsidera decisiones tomadas.
- **Pseudocódigo:**
  ```text
  Función VecinoMasCercano(nodo_inicio, pedidos):
      ruta = [nodo_inicio]
      pendientes = copia(pedidos)
      pos_actual = nodo_inicio
      mientras pendientes no esté vacío:
          mejor_p = argmin_{p in pendientes} Dijkstra(pos_actual, p.nodo_id)
          ruta.agregar(mejor_p.nodo)
          pos_actual = mejor_p.coords
          pendientes.eliminar(mejor_p)
      retornar ruta
  ```
- **Derivación de Complejidad:**
  - Iteración 1: evalúa $n$ pedidos. Iteración 2: $n-1$, ..., Iteración $n$: 1.
  - Total comparaciones: $\sum_{i=1}^n i = \frac{n(n+1)}{2} = O(n^2)$.
  - **Tiempo:** $O(n^2)$.
  - **Espacio:** $O(n)$ para la lista de ruta y conjunto de pendientes.

#### B. Asignación de Despacho de Emergencia
- **Idea:** Evalúa la distancia entre el pedido crítico (prioridad 1) y cada repartidor disponible, verificando si cuenta con capacidad de peso y volumen.
- **Complejidad:** $O(R)$ en tiempo donde $R$ es el número de repartidores ($R \le 3 \implies O(1)$ efectivo). Espacio: $O(1)$.

---

### 2.3. Paradigma Divide y Vencerás (Segmentación Espacial)

- **Idea:** Descompone recursivamente el conjunto de pedidos en cuadrantes geográficos balanceados alternando el eje de corte (latitud en profundidades pares, longitud en impares) hasta que cada clúster contenga $\le K$ pedidos. Resuelve cada clúster localmente y ensambla el recorrido global conectando los centroides más próximos.
- **Ecuación de Recurrencia:**
  $$T(n) = 2 T\left(\frac{n}{2}\right) + O(n)$$
  Donde $O(n)$ representa el costo de particionar el arreglo por la mediana en cada nivel.
- **Resolución formal por el Teorema Maestro:**
  - Forma general: $T(n) = a T(n/b) + f(n)$
  - Constantes: $a = 2$, $b = 2$, $f(n) = \Theta(n)$
  - Exponente crítico: $n^{\log_b a} = n^{\log_2 2} = n^1 = n$
  - Comparación: Como $f(n) = \Theta(n^{\log_b a}) = \Theta(n)$, aplica el **Caso 2 del Teorema Maestro**.
  - **Conclusión:** $T(n) = \Theta(n \log n)$.
  - **Espacio Auxiliar:** $O(n)$ para almacenar los subarreglos y $O(\log n)$ en la pila de llamadas.

---

### 2.4. Paradigma de Programación Dinámica (PD)

#### A. Problema de la Mochila 0/1 (Knapsack)
- **Idea:** Determina el conjunto óptimo de pedidos a cargar en el vehículo de reparto maximizando el valor económico total sin sobrepasar la capacidad $W$ en kilogramos.
- **Ecuación de Bellman:**
  $$DP[i][w] = \begin{cases} DP[i-1][w] & \text{si } w_i > w \\ \max\left(DP[i-1][w], DP[i-1][w - w_i] + v_i\right) & \text{si } w_i \le w \end{cases}$$
- **Reconstrucción:** Se realiza un recorrido hacia atrás desde $DP[N][W]$: si $DP[i][w] \ne DP[i-1][w]$, el pedido $i$ forma parte de la solución óptima y se decrementa la capacidad restante $w \leftarrow w - w_i$.
- **Complejidad:**
  - **Tiempo:** $O(N \cdot W)$ pseudo-polinomial (tabla de $(N+1) \times (W+1)$ estados).
  - **Espacio:** $O(N \cdot W)$ para almacenar la matriz completa para visualización e inspección.

#### B. Algoritmo de Held-Karp (TSP Exacto con Bitmask)
- **Idea:** Resuelve de forma matemáticamente exacta el problema del viajante sobre $N$ destinos utilizando una máscara de bits (`bitmask`) para representar el subconjunto de nodos visitados y el último nodo alcanzado.
- **Ecuación de Recurrencia:**
  $$C(mask, u) = \min_{v \notin mask} \{ \text{dist}(u, v) + C(mask \cup \{v\}, v) \}$$
  Con caso base: cuando $mask = (1 \ll N) - 1$, retorna $\text{dist}(u, 0)$ si se exige circuito cerrado.
- **Derivación de Complejidad:**
  - Número de estados posibles: $2^N$ combinaciones de máscara $\times N$ nodos terminales $= N \cdot 2^N$.
  - Costo de transición por estado: iterar sobre los $N$ posibles siguientes nodos $\implies O(N)$.
  - **Tiempo:** $O(N^2 \cdot 2^N)$.
  - **Espacio:** $O(N \cdot 2^N)$ para la tabla de memoización.
    - La matriz de costos puede ser asimétrica porque representa calles de sentido único; la recurrencia usa el costo dirigido `dist[u][v]` y no presupone simetría.
    - **Límite operativo medido:** para $N=12$ el benchmark actual registra 40.428 ms en el hardware de prueba. El costo crece exponencialmente con $N$.

---

### 2.5. Paradigma de Backtracking con Poda (Branch and Bound)

- **Idea:** Explora en profundidad (DFS) caminos simples entre un nodo origen y destino en el grafo disperso de lugares de interés; cada conexión activa representa una ruta vial y tiene un sentido.
- **Condiciones de Poda:**
  1. **Detección de Ciclos:** Mantiene un conjunto `visitados`; ningún nodo se repite en un camino simple.
  2. **Restricción de Calles Bloqueadas:** Si una arista $(u, v)$ tiene `activa == False`, no se transita.
  3. **Poda por Cota Superior (Branch and Bound):** Si el costo acumulado parcial del camino actual iguala o supera a la mejor distancia completa ya encontrada (`costo_acumulado >= mejor_distancia`), la rama se corta inmediatamente mediante `return`.
- **Derivación de Complejidad:**
  - Peor caso teórico en grafo completo: $O(V!)$.
  - En el grafo de Cusco (disperso, grado medio entre 2 y 4 con poda activa): la poda por cota reduce el espacio efectivo a una fracción mínima del árbol combinatorio.
  - **Espacio:** $O(V)$ en memoria para la pila de recursión y conjunto de visitados.

---

## 3. Resultados Empíricos de Pruebas y Benchmarks Reales

Los siguientes datos corresponden a ejecuciones directas realizadas sobre el hardware de prueba (Python 3.13 en Windows, AMD64), registradas en `benchmarks/resultados_benchmark.json`:

### 3.1. Comparación TSP: Greedy vs Held-Karp (Óptimo)

| $N$ (Entregas) | Tiempo Greedy (ms) | Tiempo Held-Karp (ms) | Distancia Greedy (m) | Distancia Óptima (m) | Gap de Ineficiencia (%) | Speedup Greedy |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **3** | 0.011 ms | 0.061 ms | 1,866.35 m | 1,866.35 m | **0.00 %** | 5.5x |
| **5** | 0.008 ms | 0.085 ms | 3,685.04 m | 3,685.04 m | **0.00 %** | 10.6x |
| **8** | 0.030 ms | 1.312 ms | 9,474.50 m | 7,608.16 m | **24.53 %** | 43.7x |
| **10** | 0.019 ms | 6.484 ms | 10,656.39 m | 8,790.04 m | **21.23 %** | 341.3x |
| **12** | 0.025 ms | 40.428 ms | 13,651.62 m | 11,785.27 m | **15.84 %** | **1,617.1x** |

**Análisis:**
- Para $N \le 5$, Greedy coincide con el óptimo en las instancias medidas; esto es un resultado empírico, no una garantía general.
- En $N=8$, Greedy recorre 1,866.34 m más que Held-Karp (gap **24.53%**). Para $N=12$, la diferencia es 1,866.35 m (**15.84%**).
- Greedy es **1,617.1 veces más rápido** que Held-Karp en la instancia de 12 destinos, evidenciando el compromiso entre calidad de solución y costo computacional.

### 3.2. Comparación de Algoritmos de Ordenamiento

| Tamaño $N$ | Merge Sort Promedio (ms) | Quick Sort Promedio (ms) |
| :---: | :---: | :---: |
| **10 pedidos** | 0.0195 ms | 0.0173 ms |
| **20 pedidos** | 0.0354 ms | 0.0320 ms |
| **30 pedidos** | 0.0555 ms | 0.0505 ms |

### 3.3. Rendimiento de Backtracking con Poda en la Red Vial de Cusco

| Ruta Evaluada | Rutas Viables | Ramas Podadas por Cota | Estados Visitados | Distancia Óptima (m) | Tiempo (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Plaza de Armas $\to$ San Pedro (N01 $\to$ N04) | 1 | **1** | 448 | 790.80 m | 0.644 ms |
| San Blas $\to$ Wanchaq (N02 $\to$ N11) | 1 | **10** | 20 | 1,778.62 m | 0.024 ms |
| Plaza de Armas $\to$ UNSAAC (N01 $\to$ N15) | 2 | **40** | 142 | 4,524.34 m | 0.370 ms |
| Santiago $\to$ San Sebastián (N05 $\to$ N19) | 7 | **269** | 955 | 9,034.33 m | 0.935 ms |

**Análisis de Poda:**
En la ruta más larga (Santiago a San Sebastián), la poda evitó explorar **269 ramas**, resolviendo un trayecto de 9 conexiones en **0.935 ms**. El grafo dirigido y los pesos son los del cache vial actual.

### 3.4. Comparación antes y después del cambio de modelo

Para las mismas ocho entregas de la corrida de referencia, el modelo anterior usaba distancias en línea recta y el nuevo usa caminos por calles. El caso de Backtracking compara la misma consulta N01→N15; los tiempos son mediciones puntuales del hardware y no una garantía:

| Métrica | Modelo anterior: línea recta | Modelo actual: red vial |
| :--- | ---: | ---: |
| Greedy, 8 destinos | 4,591.81 m | 9,474.50 m |
| Óptimo Held-Karp, 8 destinos | 4,089.09 m | 7,608.16 m |
| Backtracking N01→N15 | 3,449.22 m / 1.181 ms | 4,524.34 m / 0.370 ms |

La distancia aumenta porque el nuevo costo suma tramos transitables y contempla direcciones; no es una regresión algorítmica ni se compara como si ambos modelos midieran lo mismo.

---

## 4. Guía de Selección: ¿Cuándo usar Greedy vs PD vs Backtracking?

| Criterio | Greedy (Voraz) | Programación Dinámica (PD) | Backtracking con Poda |
| :--- | :--- | :--- | :--- |
| **Garantía de Optimalidad** | No garantiza óptimo global (heurística aproximada). | **Garantiza 100% óptimo global**. | **Garantiza 100% óptimo global**. |
| **Complejidad Temporal** | Polinomial baja ($O(n^2)$ o $O(n \log n)$). | Pseudo-polinomial o exponencial moderada ($O(n^2 2^n)$). | Exponencial / Factorial podado ($O(b^d)$). |
| **Escalabilidad** | Masiva ($N > 10,000$ pedidos). | Limitada ($N \le 14$ para TSP, $W \le 10^5$ en mochila). | Redes dispersas o caminos acotados ($V \le 50$). |
| **Manejo de Restricciones** | Muy difícil incorporar restricciones globales duras. | Excelente si se pueden codificar en el estado. | **El mejor paradigma para restricciones arbitrarias** (calles cerradas). |
| **Caso de Uso en Cusco** | Reasignación de emergencia en milisegundos o rutas preliminares rápidas. | Carga de mochila del furgón o ruta de reparto fina de pocos paquetes VIP. | Rutas de contingencia ante paros, obras o cortes de tráfico en el Centro Histórico. |

---

## 5. Casos de Prueba Verificados con Pytest

La suite automatizada cuenta actualmente con **31 pruebas** (`pytest -v`), todas aprobadas en la validación documentada:
1. `test_mochila_caso_clasico_libro`: Verifica que ante ítems con pesos [1, 2, 3] y valores [15, 10, 30] con $W=4$, la PD selecciona exactamente los ítems 1 y 3 (Valor óptimo = 45), descartando la decisión miope voraz.
2. `test_held_karp_tsp_triangulo_retorno`: Comprueba el ciclo exacto cerrado en un triángulo de 3 nodos en Cusco.
3. `test_backtracking_con_calle_bloqueada`: Confirma que al bloquear la vía principal en un grafo diamante, el algoritmo halla la vía alterna y actualiza la ruta óptima.
4. `test_particion_tamanios_menores_o_iguales_a_k`: Garantiza que la segmentación recursiva espacial conserve todos los pedidos sin duplicados ni pérdidas y respete el umbral $K$.
5. Pruebas de grafo: validan el Dijkstra manual frente a un óptimo conocido, la conectividad fuerte, la desigualdad triangular de la matriz, la geometría de extremos y la invalidación de rutas al cerrar una conexión.
6. Pruebas de Held-Karp y Greedy con costos asimétricos para confirmar que se respeta el sentido de circulación.

---

## 6. Conclusiones

1. **Separación de Responsabilidades:** La arquitectura implementada aísla completamente los modelos matemáticos y la lógica algorítmica de los componentes visuales de Tkinter, permitiendo pruebas independientes y alta mantenibilidad.
2. **Resiliencia Operativa:** La inclusión del componente de respaldo `CanvasFallback` garantiza la continuidad de la aplicación ante caídas de red o indisponibilidad de servidores de tiles geográficos.
3. **Concurrencia Segura:** La delegación de tareas computacionales intensivas (Held-Karp y Backtracking) a hilos secundarios (`threading.Thread`) previene el congelamiento de la interfaz de usuario, cumpliendo los más exigentes estándares de experiencia de usuario.

---

## 7. Instrucciones para Exportación a PDF

Para generar una versión impresa en PDF del presente informe técnico con tipografía académica mediante `pandoc` y LaTeX:

```bash
# Exportación mediante Pandoc (con motor xelatex o wkhtmltopdf)
pandoc docs/informe.md -o docs/informe.pdf --pdf-engine=xelatex -V geometry:margin=2.5cm -V fontsize=11pt
```
O bien, abrir `docs/informe.md` en VS Code o Typora y exportar mediante la opción **"Export to PDF"**.
