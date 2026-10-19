+# GUÍA DE DEFENSA ORAL Y SUSTENTACIÓN ANTE JURADO
## Proyecto: Sistema de Gestión de Rutas Óptimas en Cusco (Programación III - UNSAAC)
**Objetivo:** Maximizar los 8 puntos de la rúbrica de sustentación oral mediante dominio conceptual, explicación línea por línea y resolución de preguntas trampa.

---

## 1. Guion de Demostración en Vivo (Demo de 5 Minutos)

| Minuto | Pestaña / Vista | Acción a Realizar | Explicación Verbal al Jurado |
| :---: | :---: | :--- | :--- |
| **0:00 - 0:45** | `🗺️ Red Vial Cusco` | Mostrar el mapa con los 20 lugares y 64 arcos dirigidos del cache. Hacer clic en una conexión para pintarla de rojo (bloqueada). | *"Buenos días, docentes. Los 20 lugares son los vértices; cada arco representa una polilínea por calles de OpenStreetMap y pesa la longitud real de red en metros. La app conserva el control de cierres y el fallback offline."* |
| **0:45 - 1:30** | `📦 Pedidos` | Mostrar la tabla con 30 pedidos. Cambiar el criterio a 'Prioridad' y ejecutar **Merge Sort**; luego por 'Valor' con **Quick Sort**. Buscar un ID con Búsqueda Binaria. | *"Implementamos Merge Sort y Quick Sort a mano en O(n log n). La búsqueda por ID se resuelve en O(1) con hash y en O(log n) mediante búsqueda binaria manual sobre la lista ordenada."* |
| **1:30 - 2:30** | `⚡ Greedy` | Partir de Plaza de Armas con 8 pedidos y presionar 'Calcular Ruta Voraz'. Luego asignar un pedido de emergencia. | *"El algoritmo voraz elige en cada parada el destino pendiente de menor distancia por calles, consultando la matriz de Dijkstra, en O(n²). La asignación urgente evalúa en O(R) la distancia y capacidad del repartidor."* |
| **2:30 - 3:30** | `🧠 Prog. Dinámica` | Subpestaña Mochila: calcular carga con 25 kg y mostrar la matriz $DP[i][w]$. Pasar a Held-Karp y ejecutar $N=10$. | *"En Mochila 0/1 aplicamos la ecuación de Bellman en O(N·W) reconstruyendo el subconjunto óptimo. En Held-Karp usamos bitmask con memoización en O(n² 2ⁿ) para hallar el TSP matemáticamente exacto, sin congelar la GUI gracias a multihilo."* |
| **3:30 - 4:15** | `🔍 Backtracking` | Elegir San Blas $\to$ Wanchaq. Presionar 'Explorar'. Bloquear una conexión en el mapa y observar la ruta alternativa. | *"Backtracking explora caminos simples en el grafo dirigido de lugares. La poda Branch and Bound compara costos acumulados en metros de red; los cierres desactivan la conexión en ambos sentidos cuando existe su inversa."* |
| **4:15 - 5:00** | `📊 Comparación Big-O` | Mostrar las curvas de tiempo y calidad de ruta con gráficos reales de Matplotlib. | *"En la corrida actual para 12 destinos, Greedy tardó 0.025 ms y Held-Karp 40.428 ms; el óptimo ahorró 15.84% de distancia. Son mediciones sobre calles y el compromiso es calidad frente a costo exponencial."* |

---

### El modelo de datos y sus límites

- `tools/construir_red_vial.py` descarga y procesa la red vial offline. La GUI solo lee `data/red_vial_cache.json`; OSMnx y NetworkX son dependencias de desarrollo, no de ejecución.
- El cache actual tiene 20 nodos y 64 arcos dirigidos, ponderados por longitud OSM. Dijkstra manual precalcula la matriz de distancias mínimas; por eso A→B no tiene que costar lo mismo que B→A.
- La línea recta se conserva como métrica de comparación: el factor de desvío de un arco es longitud por calles / Haversine. El promedio del cache actual es 1.646×.
- El cache es un snapshot de OSM del 19 de octubre de 2026. Ocho lugares quedaron a más de 60 m del nodo vial ajustado más cercano; sus posiciones originales no se cambiaron. Confirma manualmente los snaps listados en `data/red_vial_cache.json`.
- El cierre de la GUI actúa sobre la conexión entre dos lugares de interés, no sobre un tramo OSM aislado. El perfil `drive` representa circulación vehicular, no restricciones peatonales. Atribución: © OpenStreetMap contributors (ODbL).

## 2. Explicación Módulo por Módulo y Líneas Clave

### A. Merge Sort y Quick Sort (`core/estructuras.py`)
- **Cómo funciona:**
  - `merge_sort`: Parte recursivamente por la mitad (`medio = n // 2`) y en `_mezclar` compara los elementos apuntados por los punteros `i` y `j`.
  - `quick_sort`: Utiliza partición de Lomuto con pivote seleccionado por mediana de tres (`_particion`), colocando menores a la izquierda y mayores a la derecha.
- **Líneas Clave a señalar:**
  - En `merge_sort`: La llamada recursiva `izquierda = merge_sort(lista[:medio])` y la combinación `_mezclar(izquierda, derecha)`.
  - En `quick_sort`: El bucle de partición `for j in range(bajo, alto): if val_j <= val_pivote: i += 1; arr[i], arr[j] = arr[j], arr[i]`.
- **Complejidad:** Merge Sort: $O(n \log n)$ tiempo, $O(n)$ espacio. Quick Sort: $O(n \log n)$ promedio, $O(\log n)$ espacio de pila.

### B. Algoritmo Greedy - Vecino Cercano (`core/greedy.py`)
- **Cómo funciona:** Desde el nodo actual, consulta para cada pedido pendiente la distancia mínima por calles desde la matriz dirigida calculada con Dijkstra y extrae el mínimo con `pendientes.pop(mejor_idx)`.
- **Líneas Clave:** El bucle de búsqueda compara el costo de red entre los identificadores de nodo; al avanzar, actualiza el nodo actual, no una coordenada euclidiana.
- **Complejidad:** $\sum_{i=1}^n i = O(n^2)$ tiempo, $O(n)$ espacio.

### C. Divide y Vencerás (`core/divide_venceras.py`)
- **Cómo funciona:** Particiona el conjunto 2D alternando latitud (niveles pares) y longitud (niveles impares) cortando por la mediana. Al llegar a $\le K$ pedidos, resuelve la zona y luego enlaza centroides.
- Haversine solo determina la partición espacial; el orden y las conexiones entre pedidos se valoran con distancias por calles.
- **Líneas Clave:** `if profundidad % 2 == 0: quick_sort(pedidos, key=lambda p: p.lat)` y la división recursiva `particionar_pedidos_dyv(sub_izq) + particionar_pedidos_dyv(sub_der)`.
- **Complejidad:** $T(n) = 2T(n/2) + O(n) \implies O(n \log n)$ por Teorema Maestro Caso 2.

### D. Programación Dinámica: Mochila 0/1 (`core/prog_dinamica.py`)
- **Cómo funciona:** Llena la tabla `dp[i][w]` de abajo hacia arriba considerando si incluye o no el ítem $i-1$. Luego hace backtrace desde `dp[n][w_max]`.
- **Líneas Clave:**
  ```python
  opcion_sin_tomar = dp[i - 1][w]
  opcion_tomando = dp[i - 1][w - w_i] + v_i
  dp[i][w] = max(opcion_sin_tomar, opcion_tomando)
  ```
  Y la reconstrucción: `if dp[i][w_restante] != dp[i - 1][w_restante]: ... w_restante -= pesos[i-1]`.
- **Complejidad:** $O(N \cdot W)$ tiempo y espacio.

### E. Programación Dinámica: Held-Karp TSP (`core/prog_dinamica.py`)
- **Cómo funciona:** Utiliza una máscara de bits `mask` (donde el bit $k$ encendido significa que el nodo $k$ fue visitado) y el último nodo $u$. Memoiza `memo[mask][u]`.
- La matriz de costos es dirigida y puede ser asimétrica. Cada transición usa el costo de red de $u$ hacia $v$; no se infiere el costo inverso.
- **Líneas Clave:**
  - Verificación de bit: `if not (mask & (1 << v)):` (el nodo $v$ no ha sido visitado).
  - Transición y memoización: `nueva_mascara = mask | (1 << v); costo = dist[u][v] + _resolver_dp(nueva_mascara, v)`.
- **Complejidad:** $O(N^2 \cdot 2^N)$ tiempo, $O(N \cdot 2^N)$ espacio.

### F. Backtracking con Poda (`core/backtracking.py`)
- **Cómo funciona:** DFS exhaustivo de caminos simples. Si el costo acumulado ya es $\ge$ que la mejor ruta encontrada hasta el momento, se detiene (`return`). Al volver, deshace la elección (`camino.pop(); visitados.remove(v)`).
- **Líneas Clave:**
  - La poda: `if costo_acumulado >= mejor_distancia: contador_podas += 1; return`.
  - El paso de retroceso: `camino.append(v); _dfs(...); camino.pop(); visitados.remove(v)`.
- **Complejidad:** $O(V!)$ en el peor caso teórico; acotado drásticamente a $O(b^d)$ con poda Branch and Bound.

---

## 3. Banco de Preguntas Trampa del Docente y Respuestas Modelo

### Pregunta 1: "¿Por qué en Quick Sort tu peor caso es $O(n^2)$ y cómo lo mitigaste?"
> **Respuesta:** *"El peor caso ocurre cuando el pivote elegido es consistentemente el elemento extremo (mínimo o máximo), lo que genera particiones totalmente desbalanceadas de tamaño 1 y $n-1$, produciendo la sumatoria aritmética $n + (n-1) + \dots + 1 = O(n^2)$. Para mitigar esto, implementé en `_particion` la técnica de **mediana de tres**, que compara el primer, medio y último elemento y usa su mediana como pivote, evitando este escenario en listas preordenadas o inversas."*

### Pregunta 2: "¿Por qué el algoritmo de la Mochila 0/1 es pseudo-polinomial y no polinomial?"
> **Respuesta:** *"Su complejidad temporal es $O(N \cdot W)$, donde $N$ es la cantidad de pedidos y $W$ es la capacidad de la mochila. Aunque parece polinomial, $W$ es un valor numérico cuya longitud de entrada en bits es $k = \log_2(W)$. Por tanto, en términos del tamaño de la entrada en bits, la complejidad es $O(N \cdot 2^k)$, que es exponencial. Si aumentamos la capacidad numérica añadiendo ceros, el tiempo crece exponencialmente."*

### Pregunta 3: "¿En qué se diferencia el subproblema de Held-Karp del enfoque de fuerza bruta permutacional?"
> **Respuesta:** *"La fuerza bruta evalúa todas las permutaciones de los nodos, lo que toma $O(n!)$ tiempo. Held-Karp reconoce la **subestructura óptima y solapamiento de subproblemas**: para un conjunto dado de ciudades visitadas, no importa en qué orden específico se visitaron internamente, solo importa qué ciudades se visitaron (la máscara de bits) y en cuál estamos parados actualmente ($u$). Al memoizar el estado `(mask, u)`, reduce la complejidad de $O(n!)$ a $O(n^2 2^n)$."*

### Pregunta 4: "¿Por qué tu Teorema Maestro en Divide y Vencerás cae en el Caso 2?"
> **Respuesta:** *"Nuestra recurrencia es $T(n) = 2T(n/2) + O(n)$. Identificamos $a=2$, $b=2$, y la función de división y mezcla $f(n) = O(n)$. Calculamos $n^{\log_b a} = n^{\log_2 2} = n^1 = n$. Como $f(n)$ es asintóticamente del mismo orden que $n^{\log_b a}$, es decir $f(n) = \Theta(n^{\log_b a})$, se cumple estrictamente la condición del Caso 2 del Teorema Maestro, cuya solución es $T(n) = \Theta(n^{\log_b a} \log n) = \Theta(n \log n)$."*

### Pregunta 5: "¿Por qué en Backtracking no usas Dijkstra si solo quieres la ruta más corta?"
> **Respuesta:** *"Dijkstra es un algoritmo voraz con cola de prioridad diseñado para encontrar únicamente **una** ruta más corta. El requerimiento de nuestro sistema exige **explorar e inventariar todas las rutas simples alternativas** ante eventualidades y permitir la inspección interactiva por parte del usuario, además de soportar restricciones arbitrarias como calles cortadas dinámicamente. Backtracking con poda Branch & Bound encuentra la ruta óptima mientras mantiene el catálogo completo de rutas de contingencia viables."*

### Pregunta 6: "¿Qué garantiza que tu interfaz gráfica no se cuelgue al ejecutar algoritmos pesados?"
> **Respuesta:** *"La arquitectura utiliza concurrencia mediante `threading.Thread(daemon=True)`. Los algoritmos combinatorios intensivos como Held-Karp ($N=12$) y Backtracking se despachan en un hilo de trabajo independiente, mientras el hilo principal de Tkinter continúa despachando eventos de la interfaz y animando la barra de progreso. La actualización final de los widgets se programa mediante el método `after()` para garantizar el acceso hilo-seguro (*thread-safe*) a los elementos de Tkinter."*

### Pregunta 7: "¿Cómo garantizas que la aplicación funcione si el docente apaga el Wi-Fi durante la sustentación?"
> **Respuesta:** *"Implementamos una arquitectura resiliente con el widget `CanvasFallback`. Si `tkintermapview` no puede conectarse a los servidores de tiles de OpenStreetMap, el sistema conmuta automáticamente y sin romperse a un lienzo 2D nativo de Tkinter (`tk.Canvas`), que normaliza matemáticamente las coordenadas geográficas de Cusco a píxeles y permite interactuar con los mismos nodos, aristas y rutas."*

### Pregunta 8: "¿Por qué no se usan todos los nodos de la red OSM como vértices de Held-Karp y Backtracking?"
> **Respuesta:** *"La red vial contiene miles de nodos y haría impracticables los algoritmos combinatorios. Usamos una arquitectura híbrida: mantenemos como vértices los 20 lugares de interés y precalculamos para cada conexión seleccionada el camino vial más corto, su longitud y su polilínea. Conservamos así costos realistas con un grafo pequeño y disperso."*

### Pregunta 9: "¿Cómo calculan el costo si las calles son de un solo sentido?"
> **Respuesta:** *"El constructor descarga una red dirigida con `network_type=drive` y busca caminos respetando sus arcos. Dijkstra calcula costos A→B; el trayecto inverso se calcula independientemente y puede tener longitud distinta o no existir. Held-Karp también consume la matriz asimétrica."*

### Pregunta 10: "¿Qué significa el factor de desvío y qué limitaciones tienen estos datos?"
> **Respuesta:** *"Es la longitud de la conexión por calles dividida entre Haversine entre sus extremos. Cuantifica cuánto difiere el recorrido vial de la línea recta, pero no es un factor universal de congestión. Los datos son una descarga puntual; algunos lugares requieren validar su ajuste a la calle, los cierres afectan conexiones completas del grafo de interés y el perfil `drive` no modela recorridos peatonales."*
