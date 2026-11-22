# Planeador de viajes TransMilenio

Proyecto final de Estructuras de Datos y Algoritmos. El motor está en Python, en la carpeta `motor/`, y lo escribimos nosotros: dentro de `motor/` solo usamos `list` como arreglo, `str`, tuplas y los módulos `csv`, `time` y `random`. No usamos diccionarios, conjuntos, `sorted`, `.sort()`, `min`/`max` sobre colecciones, `in` sobre listas, `index`, `count`, `bisect`, `heapq` ni `collections`. La app (carpeta `app/`) solo llama al motor.

## Cómo arrancar la app

```
pip install -r requirements.txt && streamlit run app/app.py
```

Otros comandos:

```
python3 demo.py              # prueba rápida de R1 a R10 en la terminal
python3 correr_tests.py      # 15 pruebas, no necesita instalar nada
python3 panel/medir.py       # mide todo en redes de 10.000 a 80.000 estaciones (R11)
```

## App desplegada

https://transmilleno7.lovable.app/

Es una versión web del front. No reimplementa nada: carga Python en el navegador con Pyodide, descarga `motor/` y los CSV de la rama `main` de este repositorio y llama a los mismos métodos del contrato (`from motor import Red, simular_fila`). La primera carga tarda unos segundos mientras baja Pyodide.

## Estructura del repositorio

```
motor/
  red.py          clase Red con el contrato completo
  tabla_hash.py   tabla hash con encadenamiento
  avl.py          árbol binario de búsqueda balanceado (AVL)
  lista_doble.py  lista doblemente enlazada para las rutas
  pila.py         pila para deshacer y rehacer
  cola.py         cola para la fila de abordaje
  fila.py         simular_fila (R10)
  viaje.py        búsqueda del viaje (R5)
  ordenar.py      merge sort y búsqueda binaria
app/app.py        front en Streamlit, incluye el panel de rendimiento
panel/            generador de redes sintéticas y script de medición
datos/            estaciones.csv, rutas.csv, horarios.csv (lo único que lee el motor)
conversion/       scripts que convierten el GTFS a los tres CSV (y coordenadas para el mapa)
tests/            pruebas
```

## Carga de la red

`Red(carpeta)` lee los tres CSV una sola vez. Cada estación entra a una tabla hash, las paradas de cada ruta se ordenan por la columna `orden` y se arma una lista doblemente enlazada por ruta, y los horarios se agrupan por la pareja ruta|estación y se ordenan. Con eso se arman los dos árboles (estaciones abiertas y ranking) desde listas ya ordenadas, tomando el elemento del medio como raíz. Costo: O(n log n) por los ordenamientos, con n = filas de los CSV.

Las horas se guardan como minutos desde las 00:00 (un entero) y se pasan a texto HH:MM solo al devolverlas. Comparar enteros es más simple y más rápido que comparar textos.

## Datos y conversión del GTFS

`conversion/convertir_gtfs.py` toma el GTFS de julio de 2021 y escribe los tres CSV de `datos/`. Lo que decidimos al convertir:

- **Horas después de medianoche (25:10).** El GTFS cuenta los viajes que pasan de las 12 de la noche como 24:xx, 25:xx, etc., porque pertenecen al día de servicio anterior. Les restamos 24 (25:10 queda 01:10) para que todas las horas estén en HH:MM de 00:00 a 23:59, que es el formato que pide el enunciado. La consecuencia es que esos buses de madrugada aparecen al principio del día: `proximo_bus(..., "00:30")` puede devolver 01:10. Lo preferimos a descartarlos, porque así no se pierde ningún bus del conteo de R6. La otra opción era dejar 25:10 tal cual, pero rompe el formato HH:MM.
- **Nombres.** En mayúsculas, sin tildes y sin espacios de más. Los vagones de una misma estación quedan como una sola estación.
- **Rutas.** Cada secuencia distinta de paradas de un `route_short_name` es una ruta de un solo sentido, llamada `<nombre>-<número>`.
- **Horarios repetidos.** Si dos viajes de la misma ruta pasan por la misma estación en el mismo minuto, la fila se guarda una sola vez (`drop_duplicates`). Así, los buses por día de R6 cuentan horarios distintos.

`conversion/coordenadas.py` saca la latitud y longitud de cada estación del mismo GTFS y escribe `datos/coordenadas.csv`. **El motor no lee ese archivo**: solo lo usa el mapa del front.

## Decisiones por requisito (R12)

En todo el documento, salvo que se diga otra cosa, n es el número de estaciones de la red.

### R1. Buscar una estación: `estado(nombre)`

Estructura: tabla hash propia con encadenamiento (`tabla_hash.py`), de nombre a la estación. El índice es `hash(nombre) % capacidad`; si dos nombres caen en la misma casilla quedan en una lista enlazada dentro de esa casilla. Cuando el factor de carga pasa de 0.75 la tabla duplica su tamaño y reacomoda los nodos, igual que el arreglo dinámico.

O grande: O(1) en promedio. La redimensión cuesta O(n) cuando pasa, pero repartida entre todas las inserciones es O(1) amortizado. Peor caso O(n) si todo colisiona en una casilla.

Alternativa descartada: arreglo ordenado con búsqueda binaria, O(log n). Como R1 es la consulta más usada, preferimos el O(1) promedio de la tabla hash.

### R2. Autocompletar: `autocompletar(prefijo, k)` y R3. Rango: `rango(desde, hasta)`

Estructura: árbol AVL (`avl.py`) que guarda solo los nombres de las estaciones abiertas. La tabla hash no sirve aquí porque no guarda ningún orden y estas dos consultas piden orden alfabético.

Algoritmo: recorrido en orden (izquierda, nodo, derecha) que solo baja por las ramas que pueden tener nombres dentro del rango. Para autocompletar usamos que todos los nombres que empiezan por el prefijo quedan, en orden alfabético, entre `prefijo` y `prefijo + "￿"` (un carácter mayor que cualquier letra), así que autocompletar es un rango que para cuando junta k nombres.

O grande: O(log n + k) para autocompletar y O(log n + m) para rango, con m = cantidad de estaciones devueltas. El log n es bajar hasta el primer nombre del rango y el k o m es recorrer los que se devuelven.

Por qué AVL y no un ABB normal: el CSV de estaciones viene en orden alfabético. Si se insertan así en un ABB normal, cada nombre queda a la derecha del anterior, el árbol se vuelve una lista y todo pasa a O(n). Lo armamos balanceado desde la lista ordenada (el del medio como raíz), y para que siga balanceado después de cerrar, reabrir o agregar estaciones usamos AVL: después de cada inserción o borrado revisa las alturas de los dos lados y, si difieren en más de 1, hace una rotación. Así la altura queda siempre en O(log n).

Por qué guardar solo las abiertas: si el árbol tuviera también las cerradas, autocompletar tendría que saltárselas, y con muchas cerradas seguidas eso puede llegar a O(n).

Alternativa descartada: arreglo ordenado con búsqueda binaria. Las consultas quedan igual de rápidas, pero cerrar o reabrir obliga a correr elementos del arreglo, que es O(n), como `insert(0)`.

### R4. Próximo bus: `proximo_bus(estacion, ruta, hora)`

Estructura: tabla hash de la pareja `"ruta|estacion"` a la lista de horas de esa ruta en esa estación, ordenada de menor a mayor.

Algoritmo: búsqueda binaria que encuentra el primer horario mayor o igual a la hora pedida (`primer_mayor_o_igual` en `ordenar.py`). Si no hay ninguno devuelve None. También devuelve None si la estación no existe, está cerrada (nadie sube ahí) o la ruta no para en ella.

O grande: O(1) para llegar a la lista + O(log m) la búsqueda, con m = número de buses de esa ruta en esa estación en el día.

Las listas se ordenan una sola vez al cargar con merge sort. Antes de ordenar revisamos en O(m) si ya vienen ordenadas, que es lo normal porque el GTFS trae los viajes en orden; en ese caso no se ordena nada (es la idea de Timsort que vimos en la Sesión 5).

Alternativas descartadas: búsqueda lineal, O(m), que con cientos de buses al día por troncal es mucho más lenta. Interpolación tampoco, porque los buses no pasan parejo: en hora pico pasan muchos más y la interpolación cae en su peor caso, O(m). Jump search es O(√m), peor que la binaria.

### R5. Planear un viaje: `viaje(origen, destino)`

No hay un algoritmo del curso que lo resuelva tal cual, así que combinamos estructuras:

1. Con la tabla hash `rutas_por_estacion` sacamos las rutas que pasan por el origen.
2. Directo: para cada una, si su tabla de paradas dice que contiene el destino, avanzamos por la lista enlazada desde el nodo del origen contando paradas hasta llegar al destino.
3. Un transbordo: para cada ruta r1 del origen avanzamos parada por parada. En cada estación abierta s miramos las rutas r2 que pasan por s y, si r2 contiene el destino más adelante, contamos las paradas de s al destino.
4. Nos quedamos con el viaje de menos paradas en total. Si empatan, gana el directo, y después el orden alfabético de las rutas.

Una estación cerrada en medio de una ruta sí cuenta como parada porque el bus pasa por ahí, pero no se puede subir, bajar ni transbordar en ella. Si el origen o el destino no existen o están cerrados, o no hay viaje, devuelve None.

Poda: si las paradas recorridas en r1 ya son tantas como el mejor viaje encontrado, se deja de avanzar por esa ruta, porque ya no puede mejorar.

O grande: O(R · L · R · L) en el peor caso, con R = rutas que pasan por una estación y L = paradas de una ruta. Ninguno de los dos depende del tamaño total de la red, por eso el tiempo no crece con n.

Alternativa considerada: BFS (búsqueda en anchura con una cola) sobre un grafo cuyos nodos son (estación, ruta), cortando en un transbordo. Encuentra lo mismo, pero hay que armar y mantener el grafo cada vez que se edita una ruta, y nuestro recorrido usa directamente las listas que ya existen.

### R6. Ranking: `ranking(k)`

Estructura: un segundo árbol AVL con claves `(-buses, nombre)` de las estaciones abiertas. Como el árbol está ordenado de menor a mayor, las primeras claves son las de más buses (por el signo menos), y en empate quedan en orden alfabético.

Buses por día de una estación: número de filas de horarios.csv de esa estación, contando solo las rutas que hoy paran en ella.

O grande: consulta O(log n + k), recorriendo en orden los primeros k. Mantenerlo al día cuesta O(log n): al cerrar se borra la clave, al reabrir se inserta, y cuando una edición de ruta cambia los buses de una estación se borra la clave vieja y se inserta la nueva.

El requisito dice que se consulta muy seguido y cambia poco. Por eso no recalculamos el ranking en cada consulta (eso sería ordenar todo, O(n log n)) sino que lo mantenemos ordenado todo el tiempo.

Alternativas descartadas: un arreglo ordenado da la consulta en O(k), pero cada cierre o reapertura corre elementos y cuesta O(n). Un heap (montículo) da O(log n) al actualizar, pero sacar el top k cuesta O(k log n) y borrar una estación cualquiera no es directo.

### R7. Editar rutas: `agregar_parada`, `quitar_parada`, `recorrido`

Estructura: cada ruta es una lista doblemente enlazada (`lista_doble.py`) con puntero a la cabeza y a la cola, más una tabla hash de nombre de parada a su nodo.

O grande:
- `agregar_parada(ruta, nueva, despues_de)`: O(1) para encontrar el nodo de `despues_de` con la tabla hash y O(1) para reconectar cuatro punteros. Si la estación cambia de buses por día, actualizar el ranking cuesta O(log n).
- `quitar_parada(ruta, estacion)`: O(1) para encontrar el nodo y reconectar a sus vecinos, más O(log n) del ranking y O(r) para quitar la ruta de la lista de rutas de esa estación (r = rutas de la estación).
- `recorrido(ruta, al_reves)`: O(L), con L = paradas de la ruta. Al derecho se avanza con `siguiente` desde la cabeza y al revés con `anterior` desde la cola. Por eso no hace falta guardar la ruta inversa.

`agregar_parada` devuelve False si la ruta no existe, si `despues_de` no está en la ruta, si la estación nueva no existe o si ya está en la ruta.

Alternativa descartada: la ruta como arreglo. Insertar o quitar en el medio corre todos los elementos de atrás, O(L), y buscar `despues_de` también es O(L). Una lista simple (solo `siguiente`) no permite recorrer al revés ni quitar un nodo sin buscar su anterior.

### R8. Cerrar y reabrir: `cerrar(nombre)`, `reabrir(nombre)`

Se marca la estación como cerrada en la tabla hash (O(1)), se borra del árbol de abiertas (O(log n)) y se borra del ranking (O(log n)). Reabrir hace lo contrario. Total O(log n). Con eso la estación desaparece sola de autocompletar, rango y ranking, y R4 y R5 revisan si está abierta antes de dejar subir, bajar o transbordar. Devuelve False si no existe o ya estaba en ese estado.

### R9. Deshacer y rehacer: `deshacer()`, `rehacer()`

Estructura: dos pilas (`pila.py`), una de cambios por deshacer y otra por rehacer. Cada cambio (cerrar, reabrir, agregar parada, quitar parada) es un objeto que sabe hacerse y deshacerse.

- Un cambio nuevo se hace, se apila en "deshacer" y la pila de "rehacer" se vacía (un cambio nuevo borra lo que había para rehacer).
- `deshacer()` saca el último cambio de "deshacer", lo deshace y lo apila en "rehacer".
- `rehacer()` hace lo contrario.
- Si la pila está vacía devuelven False.

Usamos pila porque el último cambio hecho es el primero que se deshace (LIFO), como el Ctrl+Z del ejemplo de la Sesión 6. Para que quitar una parada se pueda deshacer en el sitio exacto, la acción guarda cuál era la parada de atrás.

O grande: O(1) para sacar y meter en las pilas (la pila es una lista con el tope al final: `append` y `pop()`), más lo que cueste el cambio: O(log n) para cerrar y reabrir y O(log n) para editar rutas.

Los cambios inválidos (cerrar una estación ya cerrada, quitar una parada que no está) no se registran, porque no cambian nada.

### R10. Fila de abordaje: `simular_fila(llegadas, frecuencia, capacidad)`

1. Ordenamos a las personas por segundo de llegada con merge sort. Para que dos personas que llegan en el mismo segundo suban en el orden en que aparecen, ordenamos por la pareja (segundo, posición). La guardamos como un solo entero `segundo * P + posición`, porque comparar enteros es más rápido que comparar tuplas. Merge sort es estable y su peor caso es O(P log P) sin importar cómo vengan los datos.
2. Simulamos con una cola (`cola.py`): para cada bus, los que llegaron hasta su salida se forman al final (`enqueue`), y el bus se lleva hasta `capacidad` personas del frente (`dequeue`). Si la fila está vacía y el próximo pasajero llega mucho después, saltamos directo al primer bus después de su llegada en vez de recorrer los buses vacíos.
3. Escribimos la salida de cada persona en su posición original.

La cola no usa `deque` (es de `collections`, prohibido) ni `list.pop(0)`, que es O(n) porque corre todo el arreglo. El frente es un índice que avanza, así que `enqueue` y `dequeue` son O(1).

O grande: O(P log P), con P = número de pasajeros. Ordenar es O(P log P) y la simulación es O(P), porque cada persona entra y sale de la cola una sola vez.

Alternativas descartadas: inserción es O(P²) con datos al azar, y aquí son cientos de miles de pasajeros. Una cola hecha con `list.pop(0)` hace la simulación O(P²).

## Métodos extra para los fronts (fuera del contrato)

Además del contrato, `Red` tiene tres métodos de apoyo para que las apps no lean atributos internos del motor ni repitan lógica. No hacen parte de R1 a R10 y siguen las mismas reglas de `motor/`:

| Método | Devuelve | O grande |
| --- | --- | --- |
| `lista_rutas()` | todas las rutas en orden alfabético | O(R log R), R = rutas |
| `rutas_de(estacion)` | las rutas que paran en esa estación, en orden ([] si no existe) | O(r log r), r = rutas de la estación |
| `llegadas(ruta, hora)` | `(estacion, próximo bus o None)` para cada parada de la ruta, en orden | O(L log m), L = paradas, m = buses por parada |

`llegadas` es `proximo_bus` aplicado a todo el recorrido. El mapa la usa para ubicar los buses: si el próximo bus llega antes a una parada que a la anterior, hay un bus entre esas dos paradas.

## Panel de rendimiento (R11)

`panel/medir.py` genera redes de 10.000, 20.000, 40.000 y 80.000 estaciones con el mismo formato de los CSV (`panel/generar_red.py`), corre cada operación con las mismas consultas, toma la mediana de varias repeticiones y calcula la pendiente del tiempo contra n en escala logarítmica (0 = constante, 1 = lineal). El resultado queda en `panel/resultados.csv`. La pestaña "Panel de rendimiento" de la app lo grafica: la línea continua es lo medido y la punteada la complejidad que esperábamos, anclada en el primer tamaño.

La misma pestaña tiene el botón **Medir ahora**, que corre todas las operaciones en vivo sobre redes de 1.000, 2.000, 4.000 y 8.000 estaciones (unos segundos) y muestra las pendientes con el mismo método. Sirve para comprobar la tendencia sin esperar la medición completa.

Resultado (tiempo por operación):

| Operación | Esperada | 10.000 | 80.000 | Pendiente |
| --- | --- | --- | --- | --- |
| carga | O(n log n) | 0.78 s | 8.58 s | +1.16 |
| estado (R1) | O(1) | 0.2 µs | 0.2 µs | +0.12 |
| autocompletar (R2) | O(log n + k) | 2.3 µs | 3.1 µs | +0.16 |
| rango (R3) | O(log n + m) | 2.5 µs | 3.2 µs | +0.13 |
| proximo_bus (R4) | O(log m) | 1.8 µs | 2.0 µs | +0.05 |
| ranking (R6) | O(log n + k) | 2.2 µs | 2.4 µs | +0.03 |
| agregar/quitar parada (R7) | O(log n) | 12.1 µs | 16.2 µs | +0.14 |
| recorrido (R7) | O(L) | 1.1 µs | 0.8 µs | -0.16 |
| cerrar/reabrir (R8) | O(log n) | 9.6 µs | 17.7 µs | +0.27 |
| deshacer/rehacer (R9) | O(log n) | 9.2 µs | 12.1 µs | +0.13 |
| simular_fila (R10) | O(P log P) | 0.10 s | 1.00 s | +1.10 |

Para carga y simular_fila el tiempo es el total; para las demás es el tiempo de una operación. En simular_fila la fila crece con la red (4 pasajeros por estación).

Cómo se lee: las consultas (R1, R2, R3, R4, R6) quedan planas al pasar de 10.000 a 80.000 estaciones, que es lo que se espera de O(1) y O(log n). Las operaciones que cambian la red (R7, R8, R9) son O(log n) y suben muy poco. Las pendientes no son exactamente 0 porque en redes grandes el árbol y las tablas hash ya no caben en la memoria caché del procesador y cada salto de puntero cuesta un poco más; eso no viene del algoritmo. La carga y la fila dan pendiente un poco mayor que 1, que es lo que corresponde a O(n log n) (el log n le suma algo a la pendiente) más el costo de Python de crear millones de objetos. R5 no se mide, como dice el enunciado.

## Pruebas

`python3 correr_tests.py` corre 15 pruebas: casos borde de cada requisito (estación inexistente o cerrada, viaje imposible, deshacer sin nada que deshacer, k = 0, rango al revés, hora después del último bus), el ejemplo de R10 del enunciado, la tabla hash y el AVL contra miles de operaciones al azar, y R5, R6 y R10 comparados contra una versión de fuerza bruta.
