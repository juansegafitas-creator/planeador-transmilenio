# Demo rapido del motor con la red real: python3 demo.py
from motor import Red, simular_fila

red = Red("datos")
print("R1 estado('PORTAL NORTE') ->", red.estado("PORTAL NORTE"))
print("R1 estado('CALLE 80')     ->", red.estado("CALLE 80"))
print("R2 autocompletar('CAL', 5) ->", red.autocompletar("CAL", 5))
print("R3 rango('CALLE 26', 'CALLE 80') ->", red.rango("CALLE 26", "CALLE 80"))
print("R4 proximo_bus('UNIVERSIDADES', '1-1', '10:00') ->", red.proximo_bus("UNIVERSIDADES", "1-1", "10:00"))
print("R5 viaje('PORTAL NORTE', 'PORTAL SUR') ->", red.viaje("PORTAL NORTE", "PORTAL SUR"))
print("R6 ranking(3) ->", red.ranking(3))
print("R7 recorrido('1-1') ->", red.recorrido("1-1"))
print("R7 quitar_parada('1-1', 'RECINTO FERIAL') ->", red.quitar_parada("1-1", "RECINTO FERIAL"), red.recorrido("1-1"))
print("R9 deshacer() ->", red.deshacer(), red.recorrido("1-1"))
print("R8 cerrar('CALLE 45') ->", red.cerrar("CALLE 45"), red.estado("CALLE 45"))
print("R9 deshacer() ->", red.deshacer(), red.estado("CALLE 45"))
print("R10 simular_fila([30, 5, 5, 70], 60, 2) ->", simular_fila([30, 5, 5, 70], 60, 2))
