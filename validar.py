"""Valida uno o varios archivos de instancia.

Uso: python validar.py INSTANCIA [INSTANCIA ...]
"""

import sys

from horarios.archivos import leer_json
from horarios.validador import validar_datos


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    todo_bien = True
    for ruta in sys.argv[1:]:
        errores = validar_datos(leer_json(ruta))
        if errores:
            todo_bien = False
            print(f"{ruta}: {len(errores)} error(es)")
            for e in errores:
                print(f"  - {e}")
        else:
            print(f"{ruta}: válida")
    return 0 if todo_bien else 1


if __name__ == "__main__":
    sys.exit(main())
