# R11: corre cada operacion sobre redes de 10.000, 20.000, 40.000 y 80.000
# estaciones (el mismo metodo del Taller 1: duplicar n y mirar que pasa).
# Guarda panel/resultados.csv, que es lo que grafica la app.
# Uso: python3 panel/medir.py
import csv
import math
import random
import statistics
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "panel"))
from motor import Red, simular_fila  # noqa: E402
from generar_red import generar     # noqa: E402

TAMANOS = [10000, 20000, 40000, 80000]
REPETICIONES = 7
CONSULTAS = 300

# complejidad esperada y pendiente esperada en escala log-log
ESPERADO = {
    "carga": ("O(n log n)", 1.0),
    "estado (R1)": ("O(1)", 0.0),
    "autocompletar (R2)": ("O(log n + k)", 0.0),
    "rango (R3)": ("O(log n + m)", 0.0),
    "proximo_bus (R4)": ("O(log m)", 0.0),
    "ranking (R6)": ("O(log n + k)", 0.0),
    "agregar/quitar parada (R7)": ("O(log n)", 0.0),
    "recorrido (R7)": ("O(L)", 0.0),
    "cerrar/reabrir (R8)": ("O(log n)", 0.0),
    "deshacer/rehacer (R9)": ("O(log n)", 0.0),
    "simular_fila (R10)": ("O(P log P)", 1.0),
}


def mediana(funcion, veces=REPETICIONES):
    tiempos = []
    for _ in range(veces):
        inicio = time.perf_counter()
        funcion()
        tiempos.append(time.perf_counter() - inicio)
    return statistics.median(tiempos)


def medir_red(n):
    carpeta = tempfile.mkdtemp()
    nombres, rutas = generar(n, carpeta)
    rnd = random.Random(3)
    t_carga = mediana(lambda: Red(carpeta), 3)
    red = Red(carpeta)

    ests = [rnd.choice(nombres) for _ in range(CONSULTAS)]
    prefijos = [e[:8] for e in ests]
    pares_rango = []
    for e in ests:
        pares_rango.append((e, e[:-1] + "9"))
    buses = []
    for _ in range(CONSULTAS):
        ruta, paradas = rnd.choice(rutas)
        buses.append((rnd.choice(paradas), ruta, "07:00"))
    ediciones = []
    for _ in range(CONSULTAS):
        ruta, paradas = rnd.choice(rutas)
        ediciones.append((ruta, paradas[0]))

    def r7():
        for ruta, parada in ediciones:
            red.quitar_parada(ruta, parada)
            red.deshacer()

    def r8():
        for e in ests:
            red.cerrar(e)
            red.reabrir(e)

    def r9():
        for e in ests:
            red.cerrar(e)
        for _ in ests:
            red.deshacer()
        for _ in ests:
            red.rehacer()
        for _ in ests:
            red.deshacer()

    # la fila crece con la red: n * 4 pasajeros
    llegadas = [rnd.randint(0, 3 * 3600) for _ in range(n * 4)]

    return {
        "carga": t_carga,
        "estado (R1)": mediana(lambda: [red.estado(e) for e in ests]) / CONSULTAS,
        "autocompletar (R2)": mediana(lambda: [red.autocompletar(p, 5) for p in prefijos]) / CONSULTAS,
        "rango (R3)": mediana(lambda: [red.rango(a, b) for a, b in pares_rango]) / CONSULTAS,
        "proximo_bus (R4)": mediana(lambda: [red.proximo_bus(*b) for b in buses]) / CONSULTAS,
        "ranking (R6)": mediana(lambda: [red.ranking(10) for _ in range(CONSULTAS)]) / CONSULTAS,
        "agregar/quitar parada (R7)": mediana(r7) / (2 * CONSULTAS),
        "recorrido (R7)": mediana(lambda: [red.recorrido(r) for r, _ in ediciones]) / CONSULTAS,
        "cerrar/reabrir (R8)": mediana(r8) / (2 * CONSULTAS),
        "deshacer/rehacer (R9)": mediana(r9) / (4 * CONSULTAS),
        "simular_fila (R10)": mediana(lambda: simular_fila(llegadas, 60, 80), 3),
    }


def pendiente(xs, ys):
    """Pendiente de log(tiempo) contra log(n): 0 = constante, 1 = lineal."""
    lx = [math.log(x) for x in xs]
    ly = [math.log(y) for y in ys]
    mx = sum(lx) / len(lx)
    my = sum(ly) / len(ly)
    num = sum((a - mx) * (b - my) for a, b in zip(lx, ly))
    den = sum((a - mx) ** 2 for a in lx)
    return num / den


if __name__ == "__main__":
    resultados = {}
    for n in TAMANOS:
        print("midiendo n =", n, "...", flush=True)
        resultados[n] = medir_red(n)

    filas = []
    print()
    print(f"{'operacion':30} {'esperada':14} " + " ".join(f"{n:>10}" for n in TAMANOS) + "  pendiente")
    for op, (comp, esperada) in ESPERADO.items():
        ys = [resultados[n][op] for n in TAMANOS]
        m = pendiente(TAMANOS, ys)
        print(f"{op:30} {comp:14} " + " ".join(f"{y * 1e6:>8.1f}us" for y in ys) + f"  {m:+.2f}")
        for n, y in zip(TAMANOS, ys):
            filas.append([op, comp, esperada, n, y, round(m, 3)])

    with open(RAIZ / "panel" / "resultados.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["operacion", "complejidad", "pendiente_esperada", "n", "segundos", "pendiente_medida"])
        w.writerows(filas)
    print("\nguardado en panel/resultados.csv")
