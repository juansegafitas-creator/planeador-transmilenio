# Tabla hash con encadenamiento, como la de la practica de Tablas Hash.
# Reemplaza al dict, que esta prohibido dentro de motor/.


class NodoHash:
    """Un par clave-valor dentro de la cadena de una casilla."""

    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.siguiente = None


class TablaHash:
    """Tabla hash con encadenamiento (cada casilla es una lista enlazada).
    get, set y delete son O(1) en promedio; set es O(1) amortizado por la redimension."""

    def __init__(self, capacidad=16):
        self.capacidad = capacidad
        self.casillas = [None] * capacidad
        self.cantidad = 0

    def _indice(self, clave):
        # hash(clave) % tamaño: siempre cae dentro del arreglo
        return hash(clave) % self.capacidad

    def set(self, clave, valor):
        """Guarda el valor. Si la clave ya estaba, lo reemplaza."""
        i = hash(clave) % self.capacidad
        nodo = self.casillas[i]
        while nodo is not None:
            if nodo.clave == clave:
                nodo.valor = valor
                return
            nodo = nodo.siguiente

        # no estaba: va al inicio de la cadena, O(1) como agregar_al_inicio
        nuevo = NodoHash(clave, valor)
        nuevo.siguiente = self.casillas[i]
        self.casillas[i] = nuevo
        self.cantidad += 1

        # factor de carga: si pasa de 0.75 duplico, igual que el arreglo dinamico
        if self.cantidad / self.capacidad > 0.75:
            self._redimensionar()

    def get(self, clave):
        """Devuelve el valor de la clave, o None si no esta."""
        nodo = self.casillas[hash(clave) % self.capacidad]
        while nodo is not None:
            if nodo.clave == clave:
                return nodo.valor
            nodo = nodo.siguiente
        return None

    def contiene(self, clave):
        nodo = self.casillas[hash(clave) % self.capacidad]
        while nodo is not None:
            if nodo.clave == clave:
                return True
            nodo = nodo.siguiente
        return False

    def delete(self, clave):
        """Quita la clave reconectando la cadena. Devuelve True si la quito."""
        i = hash(clave) % self.capacidad
        anterior = None
        nodo = self.casillas[i]
        while nodo is not None:
            if nodo.clave == clave:
                if anterior is None:
                    self.casillas[i] = nodo.siguiente
                else:
                    anterior.siguiente = nodo.siguiente
                self.cantidad -= 1
                return True
            anterior = nodo
            nodo = nodo.siguiente
        return False

    def _redimensionar(self):
        # tabla del doble de tamaño y reacomodo todo: O(n) esta vez, O(1) amortizado.
        # No creo nodos nuevos: muevo los mismos nodos a su nueva casilla.
        viejas = self.casillas
        self.capacidad = self.capacidad * 2
        capacidad = self.capacidad
        casillas = [None] * capacidad
        for nodo in viejas:
            while nodo is not None:
                siguiente = nodo.siguiente
                i = hash(nodo.clave) % capacidad
                nodo.siguiente = casillas[i]
                casillas[i] = nodo
                nodo = siguiente
        self.casillas = casillas

    def claves(self):
        salida = []
        for nodo in self.casillas:
            while nodo is not None:
                salida.append(nodo.clave)
                nodo = nodo.siguiente
        return salida

    def valores(self):
        salida = []
        for nodo in self.casillas:
            while nodo is not None:
                salida.append(nodo.valor)
                nodo = nodo.siguiente
        return salida

    def __len__(self):
        return self.cantidad
