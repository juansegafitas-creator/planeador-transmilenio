# R10: fila de abordaje en hora pico.
from .cola import Cola
from .ordenar import merge_sort


def simular_fila(llegadas, frecuencia, capacidad):
    """llegadas: segundos en que llega cada persona (en cualquier orden).
    Los buses salen en frecuencia, 2*frecuencia, ... con cupo capacidad y la
    gente sube en orden de llegada. Devuelve, en el mismo orden de llegadas,
    el segundo en que salio el bus de cada persona.

    1. Ordeno las llegadas con merge sort (estable: si dos llegan al mismo
       segundo sube primero la que aparece antes). O(P log P).
    2. Simulo con una cola: llegan los que tengan tiempo <= salida del bus, y
       el bus saca hasta capacidad del frente. Cada persona entra y sale de la
       cola una sola vez: O(P).
    Total O(P log P), P = numero de pasajeros."""
    p = len(llegadas)
    salida = [None] * p
    if p == 0 or frecuencia <= 0 or capacidad <= 0:
        return salida

    # Para ordenar por segundo y, en empate, por posicion original, junto las dos
    # cosas en un solo entero: segundo * p + posicion. Comparar enteros es mas
    # rapido que comparar tuplas. Si llegan segundos con decimales uso tuplas.
    enteros = True
    for t in llegadas:
        if type(t) is not int:
            enteros = False
            break
    claves = [None] * p
    i = 0
    while i < p:
        if enteros:
            claves[i] = llegadas[i] * p + i
        else:
            claves[i] = (llegadas[i], i)
        i += 1
    claves = merge_sort(claves)
    pares = [None] * p
    i = 0
    while i < p:
        c = claves[i]
        if enteros:
            pares[i] = (c // p, c % p)
        else:
            pares[i] = c
        i += 1

    fila = Cola()
    siguiente = 0       # proxima persona (en orden de llegada) que no ha llegado
    bus = frecuencia    # segundo en que sale el proximo bus
    atendidos = 0
    while atendidos < p:
        if fila.vacia() and pares[siguiente][0] > bus:
            # nadie esperando: salto directo al primer bus despues de la llegada
            # (sin recorrer los buses vacios uno por uno)
            t = pares[siguiente][0]
            bus = ((t + frecuencia - 1) // frecuencia) * frecuencia
        # todos los que llegaron hasta la salida del bus se forman
        while siguiente < p and pares[siguiente][0] <= bus:
            fila.enqueue(pares[siguiente][1])
            siguiente += 1
        # el bus se lleva hasta capacidad personas del frente
        cupo = capacidad
        while cupo > 0 and not fila.vacia():
            salida[fila.dequeue()] = bus
            atendidos += 1
            cupo -= 1
        bus += frecuencia
    return salida
