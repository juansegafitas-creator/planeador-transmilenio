# Corre todas las pruebas sin instalar nada (no necesita pytest).
# Uso: python3 correr_tests.py
import pathlib
import tempfile
import traceback

from tests import test_motor

pasaron = 0
total = 0
for nombre in dir(test_motor):
    if not nombre.startswith("test_"):
        continue
    total += 1
    funcion = getattr(test_motor, nombre)
    try:
        if funcion.__code__.co_argcount == 1:
            funcion(pathlib.Path(tempfile.mkdtemp()))
        else:
            funcion()
        print("OK     ", nombre)
        pasaron += 1
    except Exception:
        print("FALLO  ", nombre)
        traceback.print_exc()

print()
print(pasaron, "de", total, "pruebas pasaron")
