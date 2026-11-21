# Genera una red sintetica con el formato de los tres CSV (fuera de motor/).
# Uso: python3 panel/generar_red.py 10000 carpeta_salida
import random
import sys
from pathlib import Path


def generar(n, carpeta, semilla=1):
    rnd = random.Random(semilla)
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    nombres = ["EST " + str(i).zfill(6) for i in range(n)]
    rnd.shuffle(nombres)
    (carpeta / "estaciones.csv").write_text("nombre\n" + "\n".join(nombres) + "\n")

    n_rutas = max(1, n // 4)
    rutas = []
    with open(carpeta / "rutas.csv", "w") as f:
        f.write("ruta,orden,estacion\n")
        for r in range(n_rutas):
            nombre = "R" + str(r)
            paradas = rnd.sample(nombres, rnd.randint(5, 20))
            rutas.append((nombre, paradas))
            for i, e in enumerate(paradas, 1):
                f.write(f"{nombre},{i},{e}\n")
    with open(carpeta / "horarios.csv", "w") as f:
        f.write("ruta,estacion,hora\n")
        for nombre, paradas in rutas:
            salida = rnd.randint(300, 420)
            for viaje in range(rnd.randint(4, 12)):
                t = salida + viaje * rnd.randint(10, 30)
                for e in paradas:
                    t += rnd.randint(1, 4)
                    if t < 24 * 60:
                        f.write(f"{nombre},{e},{t // 60:02d}:{t % 60:02d}\n")
    return nombres, rutas


if __name__ == "__main__":
    generar(int(sys.argv[1]), sys.argv[2])
