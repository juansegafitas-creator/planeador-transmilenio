# Pruebas del motor. Aqui (fuera de motor/) si se puede usar dict, sorted, etc.
# para comparar contra una version de fuerza bruta.
import random
import pathlib

from motor import Red, simular_fila
from motor.tabla_hash import TablaHash
from motor.avl import AVL
from motor.ordenar import merge_sort, primer_mayor_o_igual

CARPETA = str(pathlib.Path(__file__).resolve().parent.parent / "datos")


def red_chiquita(tmp_path):
    (tmp_path / "estaciones.csv").write_text(
        "nombre\nA\nB\nC\nD\nE\nF\nCALLE 26\nCALLE 45\nCALLE 72\n")
    (tmp_path / "rutas.csv").write_text(
        "ruta,orden,estacion\n"
        "R1,1,A\nR1,2,B\nR1,3,C\nR1,4,D\n"
        "R2,1,C\nR2,2,E\nR2,3,F\n"
        "R3,2,F\nR3,1,A\n"          # desordenada a proposito
        "R4,1,CALLE 26\nR4,2,CALLE 45\nR4,3,CALLE 72\n")
    (tmp_path / "horarios.csv").write_text(
        "ruta,estacion,hora\n"
        "R1,A,06:10\nR1,A,06:00\nR1,A,07:30\nR1,B,06:05\n"
        "R2,C,08:00\nR2,E,08:05\nR3,A,05:00\nR3,F,05:30\n")
    return Red(str(tmp_path))


# ---------------- estructuras ----------------

def test_tabla_hash():
    t = TablaHash(capacidad=1)
    real = {}
    for i in range(5000):
        c = "K" + str(random.randint(0, 800))
        if random.random() < 0.3:
            assert t.delete(c) == (c in real)
            real.pop(c, None)
        else:
            t.set(c, i)
            real[c] = i
    assert len(t) == len(real)
    for c in real:
        assert t.get(c) == real[c]
    assert sorted(t.claves()) == sorted(real)


def test_avl_contra_lista():
    a = AVL()
    real = set()
    for _ in range(4000):
        x = random.randint(0, 500)
        if random.random() < 0.5:
            assert a.insertar(x) == (x not in real)
            real.add(x)
        else:
            assert a.borrar(x) == (x in real)
            real.discard(x)
    s = sorted(real)
    assert a.rango(-1, 10 ** 9) == s
    assert a.rango(100, 300) == [x for x in s if 100 <= x <= 300]
    assert a.primeros(7) == s[:7]
    assert a.altura() <= 1.45 * (len(s) + 2).bit_length()


def test_avl_insertando_en_orden_no_se_degenera():
    a = AVL()
    for i in range(1 << 14):
        a.insertar(i)
    assert a.altura() <= 16


def test_merge_sort_y_binaria():
    for _ in range(50):
        l = [random.randint(0, 50) for _ in range(random.randint(0, 200))]
        assert merge_sort(l) == sorted(l)
        x = random.randint(-1, 52)
        s = sorted(l)
        assert primer_mayor_o_igual(s, x) == len([v for v in s if v < x])
    pares = [(1, "b"), (0, "z"), (1, "a")]
    assert merge_sort(pares) == [(0, "z"), (1, "a"), (1, "b")]


# ---------------- contrato con la red chiquita ----------------

def test_r1_estado(tmp_path):
    red = red_chiquita(tmp_path)
    assert red.estado("A") == "ABIERTA"
    assert red.estado("NADA") == "NO EXISTE"
    red.cerrar("A")
    assert red.estado("A") == "CERRADA"


def test_r2_r3(tmp_path):
    red = red_chiquita(tmp_path)
    assert red.autocompletar("CAL", 10) == ["CALLE 26", "CALLE 45", "CALLE 72"]
    assert red.autocompletar("CAL", 2) == ["CALLE 26", "CALLE 45"]
    assert red.autocompletar("CAL", 0) == []
    assert red.autocompletar("ZZ", 3) == []
    assert red.rango("CALLE 26", "CALLE 80") == ["CALLE 26", "CALLE 45", "CALLE 72"]
    assert red.rango("B", "D") == ["B", "C", "CALLE 26", "CALLE 45", "CALLE 72", "D"]
    assert red.rango("D", "B") == []
    red.cerrar("CALLE 45")
    assert red.autocompletar("CAL", 10) == ["CALLE 26", "CALLE 72"]
    assert red.rango("CALLE 26", "CALLE 72") == ["CALLE 26", "CALLE 72"]


def test_r4_proximo_bus(tmp_path):
    red = red_chiquita(tmp_path)
    assert red.proximo_bus("A", "R1", "05:00") == "06:00"
    assert red.proximo_bus("A", "R1", "06:00") == "06:00"
    assert red.proximo_bus("A", "R1", "06:01") == "06:10"
    assert red.proximo_bus("A", "R1", "07:31") is None
    assert red.proximo_bus("A", "R2", "05:00") is None     # R2 no para en A
    assert red.proximo_bus("NADA", "R1", "05:00") is None
    assert red.proximo_bus("A", "NADA", "05:00") is None
    red.cerrar("A")
    assert red.proximo_bus("A", "R1", "05:00") is None


def test_r5_viaje(tmp_path):
    red = red_chiquita(tmp_path)
    assert red.viaje("A", "C") == [("R1", "A", "C")]
    assert red.viaje("A", "F") == [("R3", "A", "F")]           # directo de 1 parada
    assert red.viaje("B", "F") == [("R1", "B", "C"), ("R2", "C", "F")]
    assert red.viaje("C", "A") is None                          # las rutas van en un solo sentido
    assert red.viaje("A", "NADA") is None
    assert red.viaje("A", "A") is None
    red.cerrar("C")                                             # no se puede transbordar en C
    assert red.viaje("B", "F") is None
    assert red.viaje("A", "D") == [("R1", "A", "D")]            # pero el bus si pasa por C


def test_r6_ranking(tmp_path):
    red = red_chiquita(tmp_path)
    assert red.ranking(2) == [("A", 4), ("B", 1)]
    assert red.ranking(0) == []
    assert len(red.ranking(100)) == 9
    red.cerrar("A")
    assert red.ranking(1) == [("B", 1)]
    red.reabrir("A")
    red.quitar_parada("R1", "A")                                # A pierde los 3 buses de R1
    assert red.ranking(2) == [("A", 1), ("B", 1)]


def test_r7_rutas(tmp_path):
    red = red_chiquita(tmp_path)
    assert red.recorrido("R3") == ["A", "F"]
    assert red.recorrido("R1", al_reves=True) == ["D", "C", "B", "A"]
    assert red.recorrido("NADA") == []
    assert red.agregar_parada("R1", "E", "B")
    assert red.recorrido("R1") == ["A", "B", "E", "C", "D"]
    assert red.agregar_parada("R1", "F", "D")                   # al final
    assert red.recorrido("R1", True) == ["F", "D", "C", "E", "B", "A"]
    assert not red.agregar_parada("R1", "E", "A")               # ya esta
    assert not red.agregar_parada("R1", "NADA", "A")
    assert not red.agregar_parada("R1", "CALLE 26", "NADA")
    assert not red.agregar_parada("NADA", "A", "B")
    assert red.quitar_parada("R1", "A")                         # la primera
    assert red.recorrido("R1") == ["B", "E", "C", "D", "F"]
    assert not red.quitar_parada("R1", "A")
    assert red.viaje("B", "F") == [("R1", "B", "E"), ("R2", "E", "F")]  # 2 paradas, mejor que el directo de 4
    assert red.viaje("B", "D") == [("R1", "B", "D")]


def test_r8_r9(tmp_path):
    red = red_chiquita(tmp_path)
    assert not red.deshacer() and not red.rehacer()
    assert red.cerrar("A") and not red.cerrar("A") and not red.cerrar("NADA")
    assert not red.reabrir("B")
    red.quitar_parada("R1", "B")
    red.agregar_parada("R2", "A", "E")
    assert red.recorrido("R2") == ["C", "E", "A", "F"]
    assert red.deshacer()
    assert red.recorrido("R2") == ["C", "E", "F"]
    assert red.deshacer()
    assert red.recorrido("R1") == ["A", "B", "C", "D"]
    assert red.deshacer()
    assert red.estado("A") == "ABIERTA"
    assert not red.deshacer()
    assert red.rehacer()
    assert red.estado("A") == "CERRADA"
    assert red.cerrar("B")                                      # cambio nuevo: borra el rehacer
    assert not red.rehacer()


def test_r10_fila():
    assert simular_fila([30, 5, 5, 70], 60, 2) == [120, 60, 60, 120]
    assert simular_fila([], 60, 2) == []
    assert simular_fila([60], 60, 1) == [60]
    assert simular_fila([61], 60, 1) == [120]
    assert simular_fila([0, 0, 0], 10, 1) == [10, 20, 30]
    assert simular_fila([1000000], 60, 5) == [1000020]


def test_r10_contra_fuerza_bruta():
    for _ in range(200):
        n = random.randint(1, 40)
        lleg = [random.randint(0, 300) for _ in range(n)]
        f = random.randint(1, 50)
        c = random.randint(1, 4)
        orden = sorted(range(n), key=lambda i: (lleg[i], i))
        esperado = [None] * n
        t = f
        pos = 0
        while pos < n:
            sube = 0
            while pos < n and sube < c and lleg[orden[pos]] <= t:
                esperado[orden[pos]] = t
                pos += 1
                sube += 1
            t += f
        assert simular_fila(lleg, f, c) == esperado


# ---------------- red real contra fuerza bruta ----------------

def _viaje_fuerza_bruta(red, rutas, o, d):
    """Menor numero de paradas con directo o un transbordo (solo cuenta paradas)."""
    if o == d or red.estado(o) != "ABIERTA" or red.estado(d) != "ABIERTA":
        return None
    mejor = None
    for r1, l1 in rutas.items():
        if o not in l1:
            continue
        i = l1.index(o)
        if d in l1[i + 1:]:
            p = l1.index(d) - i
            mejor = p if mejor is None else min(mejor, p)
        for j in range(i + 1, len(l1)):
            s = l1[j]
            if s == d or red.estado(s) != "ABIERTA":
                continue
            for r2, l2 in rutas.items():
                if r2 == r1 or s not in l2 or d not in l2:
                    continue
                a, b = l2.index(s), l2.index(d)
                if b > a:
                    p = (j - i) + (b - a)
                    mejor = p if mejor is None else min(mejor, p)
    return mejor


def _paradas(red, viaje):
    total = 0
    for ruta, sube, baja in viaje:
        l = red.recorrido(ruta)
        assert l.index(baja) > l.index(sube)
        total += l.index(baja) - l.index(sube)
    return total


def test_red_real_viajes_y_ranking():
    red = Red(CARPETA)
    nombres = red.rango("", "￿")
    assert len(nombres) == 147 and nombres == sorted(nombres)
    random.seed(7)
    for s in random.sample(nombres, 10):
        red.cerrar(s)
    rutas = {r: red.recorrido(r) for r in {t for n in nombres for t in (red.rutas_por_estacion.get(n) or [])}}
    for _ in range(300):
        o, d = random.choice(nombres), random.choice(nombres)
        v = red.viaje(o, d)
        esperado = _viaje_fuerza_bruta(red, rutas, o, d)
        if esperado is None:
            assert v is None
        else:
            assert v is not None and _paradas(red, v) == esperado
            assert v[0][1] == o and v[-1][2] == d
            if len(v) == 2:
                assert v[0][2] == v[1][1] and red.estado(v[0][2]) == "ABIERTA"
    # ranking contra fuerza bruta
    abiertas = [n for n in nombres if red.estado(n) == "ABIERTA"]
    cuenta = {n: red.estaciones.get(n).buses for n in abiertas}
    esperado = sorted(cuenta.items(), key=lambda x: (-x[1], x[0]))[:15]
    assert red.ranking(15) == esperado


def test_metodos_para_el_front(tmp_path):
    # lista_rutas, rutas_de y llegadas: apoyo para las apps, fuera del contrato
    red = red_chiquita(tmp_path)
    assert red.lista_rutas() == ["R1", "R2", "R3", "R4"]
    assert red.rutas_de("A") == ["R1", "R3"]
    assert red.rutas_de("C") == ["R1", "R2"]
    assert red.rutas_de("NADA") == []
    assert red.llegadas("R1", "06:01") == [("A", "06:10"), ("B", "06:05"), ("C", None), ("D", None)]
    assert red.llegadas("NADA", "06:00") == []
    red.quitar_parada("R1", "C")
    assert red.rutas_de("C") == ["R2"]
