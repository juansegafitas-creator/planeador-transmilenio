# Convierte el GTFS de TransMilenio (zip) a los tres CSV que lee el motor.
# Fuera de motor/ se puede usar cualquier libreria; aqui usamos pandas.
#
# Uso:  python3 conversion/convertir_gtfs.py ruta/al/gtfs.zip datos/
#
# Decisiones:
# - Nombre de estacion: stop_name en mayusculas, sin tildes y sin espacios de
#   mas. Si el GTFS trae varias paradas (vagones) con el mismo nombre, quedan
#   como una sola estacion.
# - Ruta: cada ruta va en un solo sentido. Para cada route_short_name agrupamos
#   los viajes por su secuencia de paradas; cada secuencia distinta es una ruta
#   y se llama <route_short_name>-<numero>.
# - Horas: el GTFS usa horas como 25:10 para los viajes que pasan de la
#   medianoche. Les restamos 24 (25:10 -> 01:10) para que todas queden en
#   formato HH:MM de 00:00 a 23:59.
import sys
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd


def limpiar(nombre):
    nombre = unicodedata.normalize("NFKD", str(nombre))
    nombre = "".join(c for c in nombre if not unicodedata.combining(c))
    return " ".join(nombre.upper().split())


def hora_hhmm(texto):
    h, m = str(texto).strip().split(":")[:2]
    h = int(h) % 24
    return f"{h:02d}:{int(m):02d}"


def convertir(zip_gtfs, salida):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_gtfs) as z:
        leer = lambda n: pd.read_csv(z.open(n), dtype=str)
        stops = leer("stops.txt")
        routes = leer("routes.txt")
        trips = leer("trips.txt")
        stop_times = leer("stop_times.txt")

    stops["estacion"] = stops["stop_name"].map(limpiar)
    st = stop_times.merge(stops[["stop_id", "estacion"]], on="stop_id")
    st["stop_sequence"] = st["stop_sequence"].astype(int)
    st = st.sort_values(["trip_id", "stop_sequence"])
    # dos paradas seguidas con el mismo nombre (vagones de una estacion) cuentan una vez
    st = st[st["estacion"] != st.groupby("trip_id")["estacion"].shift()]

    trips = trips.merge(routes[["route_id", "route_short_name"]], on="route_id")
    secuencias = st.groupby("trip_id")["estacion"].agg(tuple).rename("secuencia")
    trips = trips.merge(secuencias, left_on="trip_id", right_index=True)

    nombres_ruta = {}
    for corto, grupo in trips.groupby("route_short_name"):
        for i, sec in enumerate(sorted(grupo["secuencia"].unique()), 1):
            nombres_ruta[(corto, sec)] = f"{corto}-{i}"
    trips["ruta"] = [nombres_ruta[(c, s)] for c, s in zip(trips["route_short_name"], trips["secuencia"])]

    # rutas.csv: una fila por parada, en orden
    filas = []
    for (corto, sec), ruta in nombres_ruta.items():
        vistos = set()
        orden = 0
        for estacion in sec:
            if estacion in vistos:
                continue
            vistos.add(estacion)
            orden += 1
            filas.append((ruta, orden, estacion))
    rutas = pd.DataFrame(filas, columns=["ruta", "orden", "estacion"]).sort_values(["ruta", "orden"])

    # horarios.csv: cada vez que un viaje de esa ruta pasa por la estacion
    hor = st.merge(trips[["trip_id", "ruta"]], on="trip_id")
    hor["hora"] = hor["departure_time"].fillna(hor["arrival_time"]).map(hora_hhmm)
    hor = hor[["ruta", "estacion", "hora"]].drop_duplicates()

    estaciones = pd.DataFrame({"nombre": sorted(rutas["estacion"].unique())})
    estaciones.to_csv(salida / "estaciones.csv", index=False)
    rutas.to_csv(salida / "rutas.csv", index=False)
    hor.to_csv(salida / "horarios.csv", index=False)
    print(len(estaciones), "estaciones,", rutas["ruta"].nunique(), "rutas,", len(hor), "horarios")


if __name__ == "__main__":
    convertir(sys.argv[1], sys.argv[2])
