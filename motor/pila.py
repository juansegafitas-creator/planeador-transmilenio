# Pila (LIFO) de la Sesion 6, con el tope al final de la lista:
# push = append y pop = pop(), las dos O(1).


class Pila:
    def __init__(self):
        self.datos = []

    def push(self, x):
        self.datos.append(x)

    def pop(self):
        return self.datos.pop()

    def peek(self):
        return self.datos[len(self.datos) - 1]

    def vacia(self):
        return len(self.datos) == 0

    def __len__(self):
        return len(self.datos)
