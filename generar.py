"""Genera instancias aleatorias y las guarda en datos/instancias.

Uso:
    python generar.py -n 100 1000 5000 --semilla 42
    python generar.py -n 200 --holgura 0.6 --asignaturas 15

Cada instancia se valida antes de guardarse. El nombre del archivo incluye el
número de estudiantes y la semilla: inst_n<estudiantes>_s<semilla>.json
"""

import argparse
import sys
import time
from pathlib import Path

from horarios.archivos import guardar_json
from horarios.generador import Parametros, generar, nombre_instancia
from horarios.validador import validar_datos


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    defecto = Parametros()
    parser = argparse.ArgumentParser(description="Generador de instancias de horarios")
    parser.add_argument("-n", "--estudiantes", type=int, nargs="+", default=[defecto.estudiantes],
                        help="número de estudiantes (se pueden dar varios)")
    parser.add_argument("--semilla", type=int, default=defecto.semilla)
    parser.add_argument("--asignaturas", type=int, help="por defecto n // 15 + 10")
    parser.add_argument("--profesores", type=int, help="por defecto secciones / 3")
    parser.add_argument("--salones", type=int, help="por defecto secciones / 8")
    parser.add_argument("--edificios", type=int, help="por defecto salones / 8")
    parser.add_argument("--solicitudes", type=int, nargs=2, default=list(defecto.solicitudes_por_estudiante),
                        metavar=("MIN", "MAX"), help="asignaturas que pide cada estudiante")
    parser.add_argument("--secciones", type=int, nargs=2, default=list(defecto.secciones_por_asignatura),
                        metavar=("MIN", "MAX"), help="secciones de cada asignatura")
    parser.add_argument("--dias", type=int, default=defecto.dias)
    parser.add_argument("--bloques", type=int, default=defecto.bloques)
    parser.add_argument("--holgura", type=float, default=defecto.holgura,
                        help="cupo total / demanda; menor que 1 = más competencia")
    parser.add_argument("--popularidad", type=float, default=defecto.popularidad,
                        help="exponente de Zipf; 0 = todas las asignaturas igual de populares")
    parser.add_argument("--pesos", type=float, nargs=5, default=list(defecto.pesos),
                        metavar=("W1", "W2", "W3", "W4", "W5"))
    parser.add_argument("--carpeta", default="datos/instancias")
    args = parser.parse_args()

    for n in args.estudiantes:
        p = Parametros(
            estudiantes=n, semilla=args.semilla, asignaturas=args.asignaturas,
            profesores=args.profesores, salones=args.salones, edificios=args.edificios,
            solicitudes_por_estudiante=tuple(args.solicitudes),
            secciones_por_asignatura=tuple(args.secciones),
            dias=args.dias, bloques=args.bloques, holgura=args.holgura,
            popularidad=args.popularidad, pesos=tuple(args.pesos),
        )
        t0 = time.perf_counter()
        datos = generar(p)
        t = time.perf_counter() - t0

        errores = validar_datos(datos)
        if errores:
            print(f"La instancia generada no es válida (error del generador): {errores[:5]}", file=sys.stderr)
            return 1

        ruta = Path(args.carpeta) / nombre_instancia(p)
        # Las instancias grandes se guardan sin sangría para que el archivo pese menos.
        guardar_json(ruta, datos, indentar=n < 1000)
        solicitudes = sum(len(e["solicitudes"]) for e in datos["estudiantes"])
        cupos = sum(g["cupo"] for g in datos["secciones"])
        print(f"{ruta}: {n} estudiantes, {len(datos['asignaturas'])} asignaturas, "
              f"{len(datos['secciones'])} secciones, {len(datos['salones'])} salones, "
              f"{len(datos['profesores'])} profesores, {solicitudes} solicitudes, "
              f"{cupos} cupos ({t:.2f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
