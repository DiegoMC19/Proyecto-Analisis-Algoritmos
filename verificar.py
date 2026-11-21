"""Verifica la salida de un algoritmo contra su instancia.

Uso:
    python verificar.py INSTANCIA SALIDA [--esperada ESPERADA] [--reporte REPORTE]

Ejemplo:
    python verificar.py datos/instancias/ejemplo.json resultados/manual/ejemplo.json --esperada datos/esperadas/ejemplo.json

Termina con código 0 si la salida es válida (y correcta, si se da --esperada) y 1 si no.
"""

import argparse
import json
import sys
from pathlib import Path

from horarios.archivos import InstanciaInvalida, cargar_instancia, guardar_json, leer_json
from horarios.modelo import asignacion_desde_json
from horarios.verificador import comparar_con_esperada, reporte_a_dict, verificar


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Verificador de asignaciones de horarios")
    parser.add_argument("instancia", help="archivo de instancia (JSON)")
    parser.add_argument("salida", help="archivo de salida del algoritmo (JSON)")
    parser.add_argument("--esperada", help="archivo de salida esperada (JSON)")
    parser.add_argument("--reporte", help="ruta donde guardar el reporte (JSON)")
    args = parser.parse_args()

    try:
        inst = cargar_instancia(args.instancia)
    except InstanciaInvalida as error:
        print(error, file=sys.stderr)
        return 1

    salida = leer_json(args.salida)
    asignacion = asignacion_desde_json(salida["asignacion"])
    reporte = verificar(inst, asignacion)

    comparacion = None
    if args.esperada:
        comparacion = comparar_con_esperada(reporte, asignacion, leer_json(args.esperada))

    resultado = reporte_a_dict(Path(args.instancia).name, reporte, salida.get("objetivo"), comparacion)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if args.reporte:
        guardar_json(args.reporte, resultado)

    ok = reporte.valida and (comparacion is None or comparacion["correcta"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
