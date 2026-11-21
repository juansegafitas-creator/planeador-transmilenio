# Ordenamiento y busqueda propios (sorted, .sort() y bisect estan prohibidos).


def esta_ordenada(lista):
    """True si ya viene ordenada. O(n): un solo recorrido."""
    i = 1
    while i < len(lista):
        if lista[i] < lista[i - 1]:
            return False
        i += 1
    return True


def merge_sort(lista):
    """Devuelve una lista nueva ordenada. O(n log n) y estable.
    Es el merge sort de clase hecho de abajo hacia arriba (sin recursion):
    primero mezcla pedazos de 1, luego de 2, de 4... hasta tener todo.
    Si la lista ya viene ordenada la devuelve en O(n) (la idea de Timsort).
    Para ordenar por un criterio se ordenan tuplas (criterio, dato)."""
    n = len(lista)
    a = lista[:]
    if n < 2 or esta_ordenada(a):
        return a
    b = [None] * n
    ancho = 1
    while ancho < n:
        inicio = 0
        while inicio < n:
            medio = inicio + ancho
            if medio > n:
                medio = n
            fin = inicio + 2 * ancho
            if fin > n:
                fin = n
            # mezclar a[inicio:medio] con a[medio:fin] dentro de b
            i = inicio
            j = medio
            k = inicio
            while i < medio and j < fin:
                if a[j] < a[i]:
                    b[k] = a[j]
                    j += 1
                else:
                    # en empate pasa primero el de la izquierda: estable
                    b[k] = a[i]
                    i += 1
                k += 1
            while i < medio:
                b[k] = a[i]
                i += 1
                k += 1
            while j < fin:
                b[k] = a[j]
                j += 1
                k += 1
            inicio = fin
        a, b = b, a
        ancho = ancho * 2
    return a


def primer_mayor_o_igual(lista, objetivo):
    """Busqueda binaria (izquierda, derecha, medio) sobre una lista ordenada.
    Devuelve la posicion del primer elemento >= objetivo, o len(lista) si no hay.
    O(log n)."""
    izquierda = 0
    derecha = len(lista)
    while izquierda < derecha:
        medio = (izquierda + derecha) // 2
        if lista[medio] < objetivo:
            izquierda = medio + 1
        else:
            derecha = medio
    return izquierda
