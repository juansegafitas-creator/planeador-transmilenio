import csv

from .tabla_hash import TablaHash
from .avl import AVL
from .ordenar import merge_sort, primer_mayor_o_igual
from .lista_doble import ListaDoble
from .pila import Pila
from .viaje import buscar_viaje


class Estacion:
    def __init__(self, nombre):
        self.nombre = nombre
        self.abierta = True
        self.buses = 0  # cuantas veces pasa un bus por aqui en el dia


def _a_minutos(hora):
    if len(hora) == 5 and hora[2] == ":":
        return int(hora[0:2]) * 60 + int(hora[3:5])
    partes = hora.strip().split(":")
    return int(partes[0]) * 60 + int(partes[1])


def _a_texto(minutos):
    h = minutos // 60
    m = minutos % 60
    return str(h).zfill(2) + ":" + str(m).zfill(2)


def _archivo(carpeta, nombre):
    if carpeta.endswith("/") or carpeta.endswith("\\"):
        return carpeta + nombre
    return carpeta + "/" + nombre


class Red:
    """La red de TransMilenio cargada desde estaciones.csv, rutas.csv y horarios.csv."""

    def __init__(self, carpeta):
        self.estaciones = TablaHash()          # nombre -> Estacion           (R1)
        self.abiertas = AVL()                  # nombres abiertos, en orden   (R2, R3)
        self.rutas = TablaHash()               # ruta -> ListaDoble           (R7)
        self.rutas_por_estacion = TablaHash()  # nombre -> list de rutas      (R5)
        self.horarios = TablaHash()            # "ruta|estacion" -> minutos ordenados (R4)
        self.top = AVL()                       # (-buses, nombre) de las abiertas (R6)
        self.por_deshacer = Pila()             # (R9)
        self.por_rehacer = Pila()

        self._cargar_estaciones(_archivo(carpeta, "estaciones.csv"))
        self._cargar_rutas(_archivo(carpeta, "rutas.csv"))
        self._cargar_horarios(_archivo(carpeta, "horarios.csv"))
        self._armar_arboles()

    # ======================= carga =======================

    def _crear_estacion(self, nombre):
        est = Estacion(nombre)
        self.estaciones.set(nombre, est)
        return est

    def _cargar_estaciones(self, archivo):
        with open(archivo, newline="", encoding="utf-8") as f:
            lector = csv.reader(f)
            next(lector, None)  # encabezado
            for fila in lector:
                if len(fila) == 0:
                    continue
                nombre = fila[0].strip()
                if nombre != "" and not self.estaciones.contiene(nombre):
                    self._crear_estacion(nombre)

    def _cargar_rutas(self, archivo):
        # junto las paradas de cada ruta como (orden, estacion) y despues las ordeno
        paradas = TablaHash()
        nombres_rutas = []
        with open(archivo, newline="", encoding="utf-8") as f:
            lector = csv.reader(f)
            next(lector, None)
            for fila in lector:
                if len(fila) < 3:
                    continue
                ruta = fila[0].strip()
                estacion = fila[2].strip()
                lista = paradas.get(ruta)
                if lista is None:
                    lista = []
                    paradas.set(ruta, lista)
                    nombres_rutas.append(ruta)
                lista.append((int(fila[1]), estacion))

        for ruta in nombres_rutas:
            orden = merge_sort(paradas.get(ruta))  # O(L) si ya viene ordenada
            lista = ListaDoble()
            for par in orden:
                estacion = par[1]
                if lista.contiene(estacion):
                    continue
                if not self.estaciones.contiene(estacion):
                    self._crear_estacion(estacion)
                lista.agregar_al_final(estacion)
                self._agregar_ruta_a_estacion(estacion, ruta)
            self.rutas.set(ruta, lista)

    def _cargar_horarios(self, archivo):
        # una lista de minutos por cada pareja ruta|estacion
        grupos = []  # (lista, ruta, estacion) en el orden en que aparecen
        horarios = self.horarios
        with open(archivo, newline="", encoding="utf-8") as f:
            lector = csv.reader(f)
            next(lector, None)
            for fila in lector:
                if len(fila) < 3:
                    continue
                clave = fila[0] + "|" + fila[1]
                lista = horarios.get(clave)
                if lista is None:
                    lista = []
                    horarios.set(clave, lista)
                    grupos.append((lista, fila[0], fila[1]))
                hora = fila[2]
                if len(hora) == 5 and hora[2] == ":":
                    lista.append(int(hora[0:2]) * 60 + int(hora[3:5]))
                else:
                    lista.append(_a_minutos(hora))

        for grupo in grupos:
            lista = grupo[0]
            # si ya viene ordenada merge_sort la devuelve en O(m); si no, O(m log m)
            ordenada = merge_sort(lista)
            lista[:] = ordenada
            ruta_lista = self.rutas.get(grupo[1])
            # solo cuenta si la ruta de verdad para en esa estacion
            if ruta_lista is not None and ruta_lista.contiene(grupo[2]):
                self.estaciones.get(grupo[2]).buses += len(lista)

    def _armar_arboles(self):
        nombres = merge_sort(self.estaciones.claves())
        self.abiertas.construir(nombres)
        claves = []
        for est in self.estaciones.valores():
            claves.append((-est.buses, est.nombre))
        self.top.construir(merge_sort(claves))

    # ================== ayudas internas ==================

    def _agregar_ruta_a_estacion(self, estacion, ruta):
        lista = self.rutas_por_estacion.get(estacion)
        if lista is None:
            lista = []
            self.rutas_por_estacion.set(estacion, lista)
        lista.append(ruta)

    def _quitar_ruta_de_estacion(self, estacion, ruta):
        # list.remove esta prohibido: armo la lista sin esa ruta. O(r), r = rutas de la estacion
        nueva = []
        for r in self.rutas_por_estacion.get(estacion):
            if r != ruta:
                nueva.append(r)
        self.rutas_por_estacion.set(estacion, nueva)

    def _cambiar_buses(self, est, cambio):
        """Mantiene el ranking al dia: saca la clave vieja e inserta la nueva. O(log n)."""
        if cambio == 0:
            return
        if est.abierta:
            self.top.borrar((-est.buses, est.nombre))
        est.buses += cambio
        if est.abierta:
            self.top.insertar((-est.buses, est.nombre))

    def _buses_de(self, ruta, estacion):
        lista = self.horarios.get(ruta + "|" + estacion)
        if lista is None:
            return 0
        return len(lista)

    def _ejecutar(self, accion):
        """Hace la accion, la apila para deshacer y borra lo que habia para rehacer."""
        accion.hacer()
        self.por_deshacer.push(accion)
        self.por_rehacer = Pila()

    # ======================= R1 =======================

    def estado(self, nombre):
        """"ABIERTA", "CERRADA" o "NO EXISTE". O(1) promedio (tabla hash)."""
        est = self.estaciones.get(nombre)
        if est is None:
            return "NO EXISTE"
        if est.abierta:
            return "ABIERTA"
        return "CERRADA"

    # ===================== R2 y R3 =====================

    def autocompletar(self, prefijo, k):
        """Hasta k abiertas que empiezan por prefijo, en orden alfabetico.
        Todas estan entre prefijo y prefijo + un caracter mayor que cualquier
        letra, asi que es un rango con limite k. O(log n + k)."""
        if k <= 0:
            return []
        return self.abiertas.rango(prefijo, prefijo + "￿", k)

    def rango(self, desde, hasta):
        """Abiertas entre desde y hasta (inclusive), en orden. O(log n + m)."""
        if hasta < desde:
            return []
        return self.abiertas.rango(desde, hasta)

    # ======================= R4 =======================

    def proximo_bus(self, estacion, ruta, hora):
        """Hora HH:MM del siguiente bus de esa ruta en esa estacion, o None.
        Busqueda binaria en los horarios de esa ruta en esa estacion: O(log m)."""
        est = self.estaciones.get(estacion)
        if est is None or not est.abierta:
            return None
        lista_ruta = self.rutas.get(ruta)
        if lista_ruta is None or not lista_ruta.contiene(estacion):
            return None
        horas = self.horarios.get(ruta + "|" + estacion)
        if horas is None:
            return None
        pos = primer_mayor_o_igual(horas, _a_minutos(hora))
        if pos == len(horas):
            return None
        return _a_texto(horas[pos])

    # ======================= R5 =======================

    def viaje(self, origen, destino):
        """Lista de tramos (ruta, sube_en, baja_en), o None si no hay viaje."""
        return buscar_viaje(self, origen, destino)

    # ======================= R6 =======================

    def ranking(self, k):
        """(nombre, buses_por_dia) de las k abiertas con mas buses, de mayor a menor.
        El arbol esta ordenado por (-buses, nombre): los primeros k son el top
        (y en empate van en orden alfabetico). O(log n + k)."""
        salida = []
        for clave in self.top.primeros(k):
            salida.append((clave[1], -clave[0]))
        return salida

    # ======================= R7 =======================

    def agregar_parada(self, ruta, nueva, despues_de):
        lista = self.rutas.get(ruta)
        if lista is None or not lista.contiene(despues_de):
            return False
        if not self.estaciones.contiene(nueva) or lista.contiene(nueva):
            return False
        self._ejecutar(AccionAgregar(self, ruta, nueva, despues_de))
        return True

    def quitar_parada(self, ruta, estacion):
        lista = self.rutas.get(ruta)
        if lista is None or not lista.contiene(estacion):
            return False
        self._ejecutar(AccionQuitar(self, ruta, estacion))
        return True

    def recorrido(self, ruta, al_reves=False):
        lista = self.rutas.get(ruta)
        if lista is None:
            return []
        return lista.recorrido(al_reves)

    def _agregar(self, ruta, nueva, despues_de):
        self.rutas.get(ruta).insertar_despues(despues_de, nueva)
        self._agregar_ruta_a_estacion(nueva, ruta)
        self._cambiar_buses(self.estaciones.get(nueva), self._buses_de(ruta, nueva))

    def _quitar(self, ruta, estacion):
        anterior = self.rutas.get(ruta).quitar(estacion)
        self._quitar_ruta_de_estacion(estacion, ruta)
        self._cambiar_buses(self.estaciones.get(estacion), -self._buses_de(ruta, estacion))
        return anterior

    # ======================= R8 =======================

    def cerrar(self, nombre):
        est = self.estaciones.get(nombre)
        if est is None or not est.abierta:
            return False
        self._ejecutar(AccionCerrar(self, nombre))
        return True

    def reabrir(self, nombre):
        est = self.estaciones.get(nombre)
        if est is None or est.abierta:
            return False
        self._ejecutar(AccionReabrir(self, nombre))
        return True

    def _cerrar(self, nombre):
        est = self.estaciones.get(nombre)
        est.abierta = False
        self.abiertas.borrar(nombre)                # O(log n)
        self.top.borrar((-est.buses, nombre))       # O(log n)

    def _reabrir(self, nombre):
        est = self.estaciones.get(nombre)
        est.abierta = True
        self.abiertas.insertar(nombre)
        self.top.insertar((-est.buses, nombre))

    # ======================= R9 =======================

    def deshacer(self):
        if self.por_deshacer.vacia():
            return False
        accion = self.por_deshacer.pop()
        accion.deshacer()
        self.por_rehacer.push(accion)
        return True

    def rehacer(self):
        if self.por_rehacer.vacia():
            return False
        accion = self.por_rehacer.pop()
        accion.hacer()
        self.por_deshacer.push(accion)
        return True


# ============ acciones para deshacer / rehacer (R9) ============
# Cada cambio sabe hacerse y deshacerse. Las pilas guardan estas acciones.

class AccionCerrar:
    def __init__(self, red, nombre):
        self.red = red
        self.nombre = nombre

    def hacer(self):
        self.red._cerrar(self.nombre)

    def deshacer(self):
        self.red._reabrir(self.nombre)


class AccionReabrir:
    def __init__(self, red, nombre):
        self.red = red
        self.nombre = nombre

    def hacer(self):
        self.red._reabrir(self.nombre)

    def deshacer(self):
        self.red._cerrar(self.nombre)


class AccionAgregar:
    def __init__(self, red, ruta, nueva, despues_de):
        self.red = red
        self.ruta = ruta
        self.nueva = nueva
        self.despues_de = despues_de

    def hacer(self):
        self.red._agregar(self.ruta, self.nueva, self.despues_de)

    def deshacer(self):
        self.red._quitar(self.ruta, self.nueva)


class AccionQuitar:
    def __init__(self, red, ruta, estacion):
        self.red = red
        self.ruta = ruta
        self.estacion = estacion
        self.anterior = None  # la parada de atras, para volver a ponerla en su sitio

    def hacer(self):
        self.anterior = self.red._quitar(self.ruta, self.estacion)

    def deshacer(self):
        self.red._agregar(self.ruta, self.estacion, self.anterior)
