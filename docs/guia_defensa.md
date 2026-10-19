# GUÍA DE DEFENSA ORAL Y SUSTENTACIÓN ANTE JURADO
## Proyecto: Sistema de Gestión de Rutas Óptimas en Cusco (Programación III - UNSAAC)
**Objetivo:** Maximizar los 8 puntos de la rúbrica de sustentación oral mediante dominio conceptual, explicación línea por línea y resolución de preguntas trampa.

---

## 1. Guion de Demostración en Vivo (Demo de 5 Minutos)

| Minuto | Pestaña / Vista | Acción a Realizar | Explicación Verbal al Jurado |
| :---: | :---: | :--- | :--- |
| **0:00 - 0:45** | `🗺️ Red Vial Cusco` | Mostrar el mapa con los 20 lugares y 64 arcos dirigidos del cache. Hacer clic en una conexión para pintarla de rojo (bloqueada). | *"Buenos días, docentes. Los 20 lugares son los vértices; cada arco representa una polilínea por calles de OpenStreetMap y pesa la longitud real de red en metros. La app conserva el control de cierres y el fallback offline."* |
| **0:45 - 1:30** | `📦 Pedidos` | Mostrar la tabla con 30 pedidos. Cambiar el criterio a 'Prioridad' y ejecutar **Merge Sort**; luego por 'Valor' con **Quick Sort**. Buscar un ID con Búsqueda Binaria. | *"Implementamos Merge Sort y Quick Sort a mano en O(n log n). La búsqueda por ID se resuelve en O(1) con hash y en O(log n) mediante búsqueda binaria manual sobre la lista ordenada."* |
| **1:30 - 2:00** | `⚡ Greedy` | Partir de Plaza de Armas con 8 pedidos y presionar 'Calcular Ruta Voraz'. Luego asignar un pedido de emergencia. | *"El algoritmo voraz elige en cada parada el destino pendiente de menor distancia por calles, consultando la matriz de Dijkstra, en O(n²). La asignación urgente evalúa en O(R) la distancia y capacidad del repartidor."* |
| **2:00 - 2:30** | `➗ Divide & Vence` | Modo "Una zona por repartidor" → 'Segmentar'. Mostrar las 3 zonas de colores. | *"Partimos la ciudad por la mediana alternando latitud y longitud hasta tener una zona por repartidor, en Θ(n log n · log R). Cada repartidor resuelve con Held-Karp la ruta óptima de su zona: el equipo recorre 30.2 km frente a 43.4 km de un solo repartidor voraz."* |
| **2:30 - 3:30** | `🧠 Prog. Dinámica` | Subpestaña Mochila: elegir la bicicleta (15 kg), calcular y mostrar la matriz $DP[i][w]$ y la comparación con el voraz. Pasar a Held-Karp y ejecutar $N=10$. | *"En Mochila 0/1 aplicamos la recurrencia en O(N·W), con W en décimas de kg, y reconstruimos el subconjunto óptimo. En Held-Karp usamos bitmask con memoización en O(n² 2ⁿ) para el recorrido exacto; corre en un hilo de fondo y la ventana no se congela."* |
| **3:30 - 4:15** | `🔍 Backtracking` | Botón "Caso del enunciado: San Blas → Wanchaq", poda desactivada → 'Buscar rutas' (27 rutas). Luego "Cerrar tramo de la óptima" (la calle queda en rojo, la nueva ruta en azul). Activar la poda y repetir. | *"Sin poda enumeramos TODAS las rutas simples, como pide el enunciado: 27, y la más corta mide 1,778.6 m. Al cerrar N02–N08 quedan 25 y la mejor pasa por Lucrepata. Con poda obtenemos la misma óptima visitando 20 estados en vez de 146."* |
| **4:15 - 5:00** | `📊 Comparación Big-O` | Mostrar las curvas de tiempo y calidad de ruta con gráficos reales de Matplotlib. | *"Con 12 destinos, Greedy tardó 0.017 ms y Held-Karp 22.2 ms; la ruta voraz llegó a ser 24.5% más larga que la óptima (con n = 8). La conclusión: PD hasta unas 12-14 paradas, Greedy para muchas paradas o emergencias, Backtracking cuando hay restricciones y se quieren todas las alternativas."* |

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
- **Cómo funciona:** Particiona el conjunto 2D alternando latitud (niveles pares) y longitud (niveles impares) cortando por la mediana. Dos modos: (1) `particionar_en_r_zonas` crea exactamente R zonas (una por repartidor), cortando en proporción ⌊r/2⌋ : ⌈r/2⌉, y cada repartidor resuelve su zona con Held-Karp; (2) `particionar_pedidos_dyv` crea zonas de ≤ K pedidos que un solo repartidor recorre eligiendo de forma voraz la zona más cercana.
- Haversine solo determina la partición espacial; el orden y las conexiones entre pedidos se valoran con distancias por calles.
- **Líneas Clave:** `if profundidad % 2 == 0: quick_sort(pedidos, key=lambda p: p.lat)` y la división recursiva `particionar_pedidos_dyv(sub_izq) + particionar_pedidos_dyv(sub_der)`.
- **Complejidad:** el trabajo no recursivo es ORDENAR con Quick Sort, así que $T(n) = 2T(n/2) + \Theta(n \log n) \implies \Theta(n \log^2 n)$ (caso 2 extendido del Teorema Maestro). Con R zonas: $\Theta(n \log n \log R)$. La ruta por zonas de K con un solo repartidor cuesta $O(n^2/K)$ por la elección voraz entre zonas.

### D. Programación Dinámica: Mochila 0/1 (`core/prog_dinamica.py`)
- **Cómo funciona:** Llena la tabla `dp[i][w]` de abajo hacia arriba considerando si incluye o no el ítem $i-1$. Luego hace backtrace desde `dp[n][w_max]`. Los pesos se expresan en décimas de kg (`escala=10`), redondeando los pesos HACIA ARRIBA y la capacidad hacia abajo: así la carga nunca supera la capacidad real. (La versión anterior redondeaba al kg más cercano y llegó a cargar 5.2 kg con capacidad de 5 kg.)
- **Líneas Clave:**
  ```python
  opcion_sin_tomar = dp[i - 1][w]
  opcion_tomando = dp[i - 1][w - w_i] + v_i
  dp[i][w] = max(opcion_sin_tomar, opcion_tomando)
  ```
  Y la reconstrucción: `if dp[i][w_restante] != dp[i - 1][w_restante]: ... w_restante -= pesos[i-1]`.
- **Complejidad:** $O(N \cdot W)$ tiempo y espacio, con W = capacidad en décimas de kg (25 kg → 250 columnas).

### E. Programación Dinámica: Held-Karp TSP (`core/prog_dinamica.py`)
- **Cómo funciona:** Utiliza una máscara de bits `mask` (donde el bit $k$ encendido significa que el nodo $k$ fue visitado) y el último nodo $u$. Memoiza `memo[mask][u]`.
- La matriz de costos es dirigida y puede ser asimétrica. Cada transición usa el costo de red de $u$ hacia $v$; no se infiere el costo inverso.
- **Líneas Clave:**
  - Verificación de bit: `if not (mask & (1 << v)):` (el nodo $v$ no ha sido visitado).
  - Transición y memoización: `nueva_mascara = mask | (1 << v); costo = dist[u][v] + _resolver_dp(nueva_mascara, v)`.
- **Complejidad:** $O(N^2 \cdot 2^N)$ tiempo, $O(N \cdot 2^N)$ espacio.

### F. Backtracking (`core/backtracking.py`)
- **Cómo funciona:** DFS de caminos simples: solo avanza a vecinos por calles abiertas (`obtener_vecinos_activos`) y no visitados. Al volver, deshace la elección (`camino.pop(); visitados.remove(v)`). Con `usar_poda=False` enumera TODAS las rutas; con `usar_poda=True` corta una rama si su costo acumulado ya es $\ge$ que la mejor ruta encontrada.
- **Líneas Clave:**
  - La poda: `if usar_poda and costo_acumulado >= mejor_distancia: contador_podas += 1; return`.
  - Al llegar al destino se guarda `list(camino)` (una COPIA: si se guardara `camino`, los `pop()` posteriores la vaciarían).
  - El paso de retroceso: `camino.append(v); _dfs(...); camino.pop(); visitados.remove(v)`.
- **Complejidad:** $O(b^d)$ con grado medio b y caminos de largo d; peor caso (grafo completo) $O(V \cdot V!)$. La poda NO cambia la cota del peor caso, solo reduce los estados visitados en la práctica (42%-86% en nuestros 4 pares).
- **¿Por qué la poda no pierde la óptima?** Los pesos son no negativos: extender una rama solo puede aumentar su costo. Si ya iguala o supera la mejor ruta completa, ninguna continuación puede ser más corta.

---

## 3. Banco de Preguntas Trampa del Docente y Respuestas Modelo

### Pregunta 1: "¿Por qué en Quick Sort tu peor caso es $O(n^2)$ y cómo lo mitigaste?"
> **Respuesta:** *"El peor caso ocurre cuando el pivote elegido es consistentemente el elemento extremo (mínimo o máximo), lo que genera particiones totalmente desbalanceadas de tamaño 1 y $n-1$, produciendo la sumatoria aritmética $n + (n-1) + \dots + 1 = O(n^2)$. Para mitigar esto, implementé en `_particion` la técnica de **mediana de tres**, que compara el primer, medio y último elemento y usa su mediana como pivote, evitando este escenario en listas preordenadas o inversas."*

### Pregunta 2: "¿Por qué el algoritmo de la Mochila 0/1 es pseudo-polinomial y no polinomial?"
> **Respuesta:** *"Su complejidad temporal es $O(N \cdot W)$, donde $N$ es la cantidad de pedidos y $W$ es la capacidad de la mochila. Aunque parece polinomial, $W$ es un valor numérico cuya longitud de entrada en bits es $k = \log_2(W)$. Por tanto, en términos del tamaño de la entrada en bits, la complejidad es $O(N \cdot 2^k)$, que es exponencial. Si aumentamos la capacidad numérica añadiendo ceros, el tiempo crece exponencialmente."*

### Pregunta 3: "¿En qué se diferencia el subproblema de Held-Karp del enfoque de fuerza bruta permutacional?"
> **Respuesta:** *"La fuerza bruta evalúa todas las permutaciones de los nodos, lo que toma $O(n!)$ tiempo. Held-Karp reconoce la **subestructura óptima y solapamiento de subproblemas**: para un conjunto dado de ciudades visitadas, no importa en qué orden específico se visitaron internamente, solo importa qué ciudades se visitaron (la máscara de bits) y en cuál estamos parados actualmente ($u$). Al memoizar el estado `(mask, u)`, reduce la complejidad de $O(n!)$ a $O(n^2 2^n)$."*

### Pregunta 4: "¿Cuánto cuesta tu partición de Divide y Vencerás? ¿Qué caso del Teorema Maestro aplica?"
> **Respuesta:** *"En cada nivel ordenamos los pedidos con Quick Sort para cortar por la mediana, así que el trabajo no recursivo es $f(n)=\Theta(n \log n)$, no $\Theta(n)$. La recurrencia es $T(n) = 2T(n/2) + \Theta(n \log n)$, con $a=b=2$ y $n^{\log_b a}=n$. Como $f(n)=\Theta(n \log^1 n)$, aplica la forma extendida del caso 2: $T(n)=\Theta(n \log^2 n)$. Si en vez de ordenar usáramos Quickselect para hallar la mediana en $O(n)$, tendríamos el caso 2 clásico y $\Theta(n \log n)$."*

### Pregunta 5: "¿Por qué en Backtracking no usas Dijkstra si solo quieres la ruta más corta?"
> **Respuesta:** *"Dijkstra es un algoritmo voraz con cola de prioridad diseñado para encontrar únicamente **una** ruta más corta. El requerimiento de nuestro sistema exige **explorar e inventariar todas las rutas simples alternativas** ante eventualidades y permitir la inspección interactiva por parte del usuario, además de soportar restricciones arbitrarias como calles cortadas dinámicamente. Por eso, sin poda, Backtracking lista todas las rutas (27 de San Blas a Wanchaq). Ojo: con la poda activada ya NO se tiene el catálogo completo, solo las rutas que fueron mejorando la cota; por eso la poda es opcional en la interfaz. Si solo quisiéramos la ruta más corta, Dijkstra sería lo eficiente, y de hecho lo usamos para la matriz de distancias."*

### Pregunta 6: "¿Qué garantiza que tu interfaz gráfica no se cuelgue al ejecutar algoritmos pesados?"
> **Respuesta:** *"Held-Karp, Backtracking y el benchmark se ejecutan en un hilo de trabajo (`gui/hilos.py`). Tkinter NO es seguro entre hilos: un hilo secundario no debe tocar widgets ni llamar a `after()`. Por eso el hilo solo deja su resultado en una `queue.Queue`, y el hilo principal revisa esa cola cada 50 ms con `after()` y actualiza la interfaz. Además, `report_callback_exception` en `app.py` captura cualquier error de un botón y lo muestra en una ventana, sin cerrar la aplicación. Hay una prueba automática, `tools/prueba_gui.py`, que pulsa todas las funciones."*

### Pregunta 7: "¿Cómo garantizas que la aplicación funcione si el docente apaga el Wi-Fi durante la sustentación?"
> **Respuesta:** *"Al iniciar, la app intenta conectarse al servidor de tiles (1.5 s máximo). Si no hay conexión, usa `CanvasFallback`, un lienzo 2D de Tkinter que proyecta latitud y longitud a píxeles y dibuja los mismos nodos, calles y rutas; también permite cerrar calles con un clic. Los algoritmos nunca usan Internet: la red vial está en `data/red_vial_cache.json`. Si el Wi-Fi se corta con la app ya abierta, el mapa con tiles deja de cargar fondo, pero las rutas se siguen dibujando. Para forzar el modo sin conexión: variable de entorno `RUTAS_OFFLINE=1`."*

### Pregunta 8: "¿Por qué no se usan todos los nodos de la red OSM como vértices de Held-Karp y Backtracking?"
> **Respuesta:** *"La red vial contiene miles de nodos y haría impracticables los algoritmos combinatorios. Usamos una arquitectura híbrida: mantenemos como vértices los 20 lugares de interés y precalculamos para cada conexión seleccionada el camino vial más corto, su longitud y su polilínea. Conservamos así costos realistas con un grafo pequeño y disperso."*

### Pregunta 9: "¿Cómo calculan el costo si las calles son de un solo sentido?"
> **Respuesta:** *"El constructor descarga una red dirigida con `network_type=drive` y busca caminos respetando sus arcos. Dijkstra calcula costos A→B; el trayecto inverso se calcula independientemente y puede tener longitud distinta o no existir. Held-Karp también consume la matriz asimétrica."*

### Pregunta 10: "¿Qué significa el factor de desvío y qué limitaciones tienen estos datos?"
> **Respuesta:** *"Es la longitud de la conexión por calles dividida entre Haversine entre sus extremos. Cuantifica cuánto difiere el recorrido vial de la línea recta, pero no es un factor universal de congestión. Los datos son una descarga puntual; algunos lugares requieren validar su ajuste a la calle, los cierres afectan conexiones completas del grafo de interés y el perfil `drive` no modela recorridos peatonales."*

### Pregunta 11: "¿Por qué tu mochila da 4.2 kg con capacidad 5 kg? ¿No debería llenarla?"
> **Respuesta:** *"La PD maximiza el VALOR, no el peso. Con los 15 primeros pedidos y 5 kg, la mejor combinación que cabe es PED-002 + PED-010 (4.2 kg, S/. 560). Además, los pesos se redondean hacia arriba a décimas de kg para no exceder nunca la capacidad real."*

### Pregunta 12: "¿Cuándo es mejor Greedy frente a PD o Backtracking?" (está en la rúbrica del informe)
> **Respuesta:** *"Greedy: muchas paradas o respuesta inmediata (emergencias), aceptando rutas hasta 24.5% más largas. PD: pocas paradas (hasta 12-14 en Held-Karp) o cuando la tabla es manejable (mochila: menos de 1 ms con capacidades reales); da el óptimo. Backtracking: cuando hay restricciones duras (calles cerradas) y queremos todas las alternativas; es exponencial, así que solo en grafos pequeños o con poda."*
