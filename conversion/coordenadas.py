# Saca las coordenadas de cada estacion del GTFS para el mapa del front.
# El motor NO lee este archivo: solo lee estaciones.csv, rutas.csv y horarios.csv.
#
# Uso:  python3 conversion/coordenadas.py ruta/al/gtfs.zip datos/
# Escribe datos/coordenadas.csv con columnas nombre,lat,lon.
#
# Una estacion puede tener varias paradas en el GTFS (vagones, accesos). Usamos
# el promedio de sus coordenadas, con el mismo nombre limpio que usa
# convertir_gtfs.py para que coincida con estaciones.csv.
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convertir_gtfs import limpiar  # noqa: E402


def coordenadas(zip_gtfs, carpeta):
    carpeta = Path(carpeta)
    with zipfile.ZipFile(zip_gtfs) as z:
        stops = pd.read_csv(z.open("stops.txt"), dtype=str)
    stops["nombre"] = stops["stop_name"].map(limpiar)
    stops["lat"] = stops["stop_lat"].astype(float)
    stops["lon"] = stops["stop_lon"].astype(float)
    promedio = stops.groupby("nombre")[["lat", "lon"]].mean().round(6)

    estaciones = pd.read_csv(carpeta / "estaciones.csv", dtype=str)["nombre"]
    salida = promedio.reindex(estaciones).reset_index()
    faltan = salida[salida["lat"].isna()]["nombre"].tolist()
    salida.dropna().to_csv(carpeta / "coordenadas.csv", index=False)
    print(len(salida) - len(faltan), "estaciones con coordenadas")
    if faltan:
        print("sin coordenadas:", ", ".join(faltan))


if __name__ == "__main__":
    coordenadas(sys.argv[1], sys.argv[2])
