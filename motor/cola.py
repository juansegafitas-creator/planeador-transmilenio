# Cola (FIFO) de la Sesion 6.
# deque esta prohibido (es de collections) y list.pop(0) es O(n) porque corre
# todo el arreglo. Aqui el frente es un indice que avanza: enqueue es un
# append al final y dequeue solo mueve el indice. Las dos son O(1).


class Cola:
    def __init__(self):
        self.datos = []
        self.frente = 0

    def enqueue(self, x):
        self.datos.append(x)

    def dequeue(self):
        x = self.datos[self.frente]
        self.frente += 1
        return x

    def ver_frente(self):
        return self.datos[self.frente]

    def vacia(self):
        return self.frente == len(self.datos)

    def __len__(self):
        return len(self.datos) - self.frente
