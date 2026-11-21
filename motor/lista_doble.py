# Lista doblemente enlazada para el recorrido de una ruta (R7).
# Cada nodo apunta al anterior y al siguiente, asi que se recorre en los dos
# sentidos. Ademas una tabla hash nombre -> nodo deja encontrar cualquier
# parada en O(1) sin recorrer la lista.
from .tabla_hash import TablaHash


class NodoRuta:
    def __init__(self, nombre):
        self.nombre = nombre
        self.anterior = None
        self.siguiente = None


class ListaDoble:
    def __init__(self):
        self.cabeza = None
        self.cola = None          # el tail de clase
        self.nodos = TablaHash()  # nombre -> nodo
        self.cantidad = 0

    def __len__(self):
        return self.cantidad

    def contiene(self, nombre):
        return self.nodos.contiene(nombre)

    def nodo(self, nombre):
        return self.nodos.get(nombre)

    def agregar_al_final(self, nombre):
        """O(1) gracias al puntero cola."""
        nuevo = NodoRuta(nombre)
        if self.cola is None:
            self.cabeza = nuevo
            self.cola = nuevo
        else:
            nuevo.anterior = self.cola
            self.cola.siguiente = nuevo
            self.cola = nuevo
        self.nodos.set(nombre, nuevo)
        self.cantidad += 1

    def insertar_despues(self, despues_de, nombre):
        """Mete nombre justo despues de despues_de. Si despues_de es None lo
        mete al inicio. O(1): se reconectan 4 punteros."""
        nuevo = NodoRuta(nombre)
        if despues_de is None:
            nuevo.siguiente = self.cabeza
            if self.cabeza is not None:
                self.cabeza.anterior = nuevo
            self.cabeza = nuevo
            if self.cola is None:
                self.cola = nuevo
        else:
            ref = self.nodos.get(despues_de)
            nuevo.anterior = ref
            nuevo.siguiente = ref.siguiente
            if ref.siguiente is not None:
                ref.siguiente.anterior = nuevo
            else:
                self.cola = nuevo
            ref.siguiente = nuevo
        self.nodos.set(nombre, nuevo)
        self.cantidad += 1

    def quitar(self, nombre):
        """Saca la parada reconectando a sus vecinos. O(1).
        Devuelve el nombre de la parada de atras (None si era la primera),
        que es lo que se necesita para deshacer."""
        nodo = self.nodos.get(nombre)
        anterior = nodo.anterior
        if anterior is not None:
            anterior.siguiente = nodo.siguiente
        else:
            self.cabeza = nodo.siguiente
        if nodo.siguiente is not None:
            nodo.siguiente.anterior = anterior
        else:
            self.cola = anterior
        self.nodos.delete(nombre)
        self.cantidad -= 1
        if anterior is None:
            return None
        return anterior.nombre

    def recorrido(self, al_reves=False):
        """Nombres en orden, o al reves usando los punteros anterior. O(L)."""
        salida = []
        if al_reves:
            nodo = self.cola
            while nodo is not None:
                salida.append(nodo.nombre)
                nodo = nodo.anterior
        else:
            nodo = self.cabeza
            while nodo is not None:
                salida.append(nodo.nombre)
                nodo = nodo.siguiente
        return salida
