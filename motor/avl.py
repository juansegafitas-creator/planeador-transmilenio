# Arbol binario de busqueda balanceado (AVL).
# Es el ABB de clase, pero despues de cada insercion o borrado revisa la altura
# de los dos lados y, si se descuadra por mas de 1, hace una rotacion.
# Asi la altura siempre queda en O(log n) y nunca se vuelve una lista.
# Las claves pueden ser textos (nombres) o tuplas (para el ranking).


class NodoAVL:
    def __init__(self, clave):
        self.clave = clave
        self.izquierda = None
        self.derecha = None
        self.altura = 1


def _altura(nodo):
    if nodo is None:
        return 0
    return nodo.altura


def _actualizar(nodo):
    a = _altura(nodo.izquierda)
    b = _altura(nodo.derecha)
    if a > b:
        nodo.altura = a + 1
    else:
        nodo.altura = b + 1


def _rotar_derecha(y):
    x = y.izquierda
    y.izquierda = x.derecha
    x.derecha = y
    _actualizar(y)
    _actualizar(x)
    return x


def _rotar_izquierda(x):
    y = x.derecha
    x.derecha = y.izquierda
    y.izquierda = x
    _actualizar(x)
    _actualizar(y)
    return y


def _balancear(nodo):
    _actualizar(nodo)
    factor = _altura(nodo.izquierda) - _altura(nodo.derecha)
    if factor > 1:
        # cargado a la izquierda
        if _altura(nodo.izquierda.izquierda) < _altura(nodo.izquierda.derecha):
            nodo.izquierda = _rotar_izquierda(nodo.izquierda)
        return _rotar_derecha(nodo)
    if factor < -1:
        # cargado a la derecha
        if _altura(nodo.derecha.derecha) < _altura(nodo.derecha.izquierda):
            nodo.derecha = _rotar_derecha(nodo.derecha)
        return _rotar_izquierda(nodo)
    return nodo


class AVL:
    """Buscar, insertar y borrar en O(log n). Listar en orden un tramo de m
    elementos en O(log n + m)."""

    def __init__(self):
        self.raiz = None
        self.cantidad = 0
        self._cambio = False

    def __len__(self):
        return self.cantidad

    # ---------- construir desde una lista ordenada ----------

    def construir(self, claves_ordenadas):
        """Arma el arbol tomando el del medio como raiz (divide y venceras). O(n)."""
        self.raiz = self._construir(claves_ordenadas, 0, len(claves_ordenadas) - 1)
        self.cantidad = len(claves_ordenadas)

    def _construir(self, lista, izquierda, derecha):
        if izquierda > derecha:
            return None
        medio = (izquierda + derecha) // 2
        nodo = NodoAVL(lista[medio])
        nodo.izquierda = self._construir(lista, izquierda, medio - 1)
        nodo.derecha = self._construir(lista, medio + 1, derecha)
        _actualizar(nodo)
        return nodo

    # ---------- buscar, insertar, borrar ----------

    def contiene(self, clave):
        nodo = self.raiz
        while nodo is not None:
            if clave == nodo.clave:
                return True
            if clave < nodo.clave:
                nodo = nodo.izquierda
            else:
                nodo = nodo.derecha
        return False

    def insertar(self, clave):
        """True si la inserto, False si ya estaba."""
        self._cambio = False
        self.raiz = self._insertar(self.raiz, clave)
        if self._cambio:
            self.cantidad += 1
        return self._cambio

    def _insertar(self, nodo, clave):
        if nodo is None:
            self._cambio = True
            return NodoAVL(clave)
        if clave < nodo.clave:
            nodo.izquierda = self._insertar(nodo.izquierda, clave)
        elif nodo.clave < clave:
            nodo.derecha = self._insertar(nodo.derecha, clave)
        else:
            return nodo
        return _balancear(nodo)

    def borrar(self, clave):
        """True si la borro, False si no estaba."""
        self._cambio = False
        self.raiz = self._borrar(self.raiz, clave)
        if self._cambio:
            self.cantidad -= 1
        return self._cambio

    def _borrar(self, nodo, clave):
        if nodo is None:
            return None
        if clave < nodo.clave:
            nodo.izquierda = self._borrar(nodo.izquierda, clave)
        elif nodo.clave < clave:
            nodo.derecha = self._borrar(nodo.derecha, clave)
        else:
            self._cambio = True
            # 0 o 1 hijo: lo reemplaza el hijo que tenga
            if nodo.izquierda is None:
                return nodo.derecha
            if nodo.derecha is None:
                return nodo.izquierda
            # 2 hijos: lo reemplaza el menor de la derecha (el sucesor)
            sucesor = nodo.derecha
            while sucesor.izquierda is not None:
                sucesor = sucesor.izquierda
            nodo.clave = sucesor.clave
            nodo.derecha = self._borrar_minimo(nodo.derecha)
        return _balancear(nodo)

    def _borrar_minimo(self, nodo):
        if nodo.izquierda is None:
            return nodo.derecha
        nodo.izquierda = self._borrar_minimo(nodo.izquierda)
        return _balancear(nodo)

    # ---------- recorridos en orden ----------

    def rango(self, desde, hasta, limite=-1):
        """Claves entre desde y hasta (incluidas), en orden. Solo baja por las
        ramas que pueden tener algo del rango. limite = -1 es sin limite."""
        salida = []
        if limite != 0:
            self._rango(self.raiz, desde, hasta, limite, salida)
        return salida

    def _rango(self, nodo, desde, hasta, limite, salida):
        if nodo is None:
            return
        if desde < nodo.clave:
            self._rango(nodo.izquierda, desde, hasta, limite, salida)
            if len(salida) == limite:
                return
        if not (nodo.clave < desde) and not (hasta < nodo.clave):
            salida.append(nodo.clave)
            if len(salida) == limite:
                return
        if nodo.clave < hasta:
            self._rango(nodo.derecha, desde, hasta, limite, salida)

    def primeros(self, k):
        """Las k claves mas pequenas, en orden. O(log n + k)."""
        salida = []
        if k > 0:
            self._primeros(self.raiz, k, salida)
        return salida

    def _primeros(self, nodo, k, salida):
        if nodo is None:
            return
        self._primeros(nodo.izquierda, k, salida)
        if len(salida) == k:
            return
        salida.append(nodo.clave)
        if len(salida) == k:
            return
        self._primeros(nodo.derecha, k, salida)

    def altura(self):
        return _altura(self.raiz)
