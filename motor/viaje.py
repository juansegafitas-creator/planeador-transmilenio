# R5: viaje directo o con un solo transbordo que recorra menos paradas.
# No hay un algoritmo de clase que lo haga tal cual: se combinan la tabla hash
# (rutas que paran en cada estacion, y nodo de cada parada dentro de su ruta)
# con la lista doblemente enlazada de cada ruta (avanzar parada por parada).


def _contar_hasta(nodo, destino):
    """Avanza por la ruta desde nodo hasta destino.
    Devuelve cuantas paradas recorrio, o -1 si destino no esta mas adelante."""
    pasos = 0
    actual = nodo.siguiente
    while actual is not None:
        pasos += 1
        if actual.nombre == destino:
            return pasos
        actual = actual.siguiente
    return -1


def _es_mejor(paradas, tramos, clave, mejor):
    # gana menos paradas; en empate menos tramos (el directo); despues el
    # orden alfabetico de las rutas para que el resultado no dependa del azar
    if mejor is None:
        return True
    if paradas != mejor[0]:
        return paradas < mejor[0]
    if tramos != mejor[1]:
        return tramos < mejor[1]
    return clave < mejor[2]


def buscar_viaje(red, origen, destino):
    est_o = red.estaciones.get(origen)
    est_d = red.estaciones.get(destino)
    if est_o is None or est_d is None or not est_o.abierta or not est_d.abierta:
        return None
    if origen == destino:
        return None

    rutas_origen = red.rutas_por_estacion.get(origen)
    if rutas_origen is None:
        return None

    # mejor = (paradas, tramos, clave_desempate, lista_de_tramos)
    mejor = None

    for r1 in rutas_origen:
        lista1 = red.rutas.get(r1)
        nodo_o = lista1.nodo(origen)

        # directo
        if lista1.contiene(destino):
            p = _contar_hasta(nodo_o, destino)
            if p != -1 and _es_mejor(p, 1, (r1,), mejor):
                mejor = (p, 1, (r1,), [(r1, origen, destino)])

        # un transbordo en una estacion s mas adelante en r1
        p1 = 0
        s = nodo_o.siguiente
        while s is not None:
            p1 += 1
            if mejor is not None and p1 >= mejor[0]:
                break  # ya no puede mejorar: todavia falta al menos una parada
            nombre_s = s.nombre
            if nombre_s == destino:
                break  # llegar aqui ya es el directo
            est_s = red.estaciones.get(nombre_s)
            if est_s.abierta:
                rutas_s = red.rutas_por_estacion.get(nombre_s)
                for r2 in rutas_s:
                    if r2 == r1:
                        continue
                    lista2 = red.rutas.get(r2)
                    if not lista2.contiene(destino):
                        continue
                    p2 = _contar_hasta(lista2.nodo(nombre_s), destino)
                    if p2 == -1:
                        continue
                    total = p1 + p2
                    if _es_mejor(total, 2, (r1, r2), mejor):
                        mejor = (total, 2, (r1, r2),
                                 [(r1, origen, nombre_s), (r2, nombre_s, destino)])
            s = s.siguiente

    if mejor is None:
        return None
    return mejor[3]
