"""Calcula el óptimo de instancias pequeñas con el backtracking exacto y lo guarda como salida esperada.

Uso: python fuerza_bruta.py INSTANCIA [INSTANCIA ...] [--limite N]
"""

import argparse
import sys
from pathlib import Path

from horarios.archivos import cargar_instancia, guardar_json, leer_json
from horarios.fuerza_bruta import LIMITE_POR_DEFECTO, InstanciaMuyGrande, fuerza_bruta
from horarios.modelo import asignacion_a_json
from horarios.verificador import comparar_con_esperada, verificar


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Backtracking exacto para instancias pequeñas")
    parser.add_argument("instancias", nargs="+")
    parser.add_argument("--limite", type=float, default=LIMITE_POR_DEFECTO,
                        help="máximo de combinaciones del espacio completo")
    parser.add_argument("--carpeta", default="datos/esperadas")
    args = parser.parse_args()

    todo_bien = True
    for ruta in args.instancias:
        nombre = Path(ruta).name
        inst = cargar_instancia(ruta)
        try:
            r = fuerza_bruta(inst, limite=int(args.limite))
        except InstanciaMuyGrande as error:
            print(f"{nombre}: se salta, {error}")
            continue

        resumen = (f"{nombre}: f* = {r.objetivo.a_dict()['f']}  |  espacio {r.espacio:,}, "
                   f"nodos {r.nodos:,}, hojas válidas {r.hojas:,}, {r.tiempo:.2f} s")
        destino = Path(args.carpeta) / nombre
        if destino.exists() and leer_json(destino).get("origen") == "manual":
            esperada = leer_json(destino)
            comp = comparar_con_esperada(verificar(inst, r.asignacion), r.asignacion, esperada)
            estado = "coincide con el caso a mano" if comp["correcta"] else f"NO coincide: {comp['motivo']}"
            todo_bien &= comp["correcta"]
            print(f"{resumen}  ->  {estado}")
            continue

        guardar_json(destino, {
            "instancia": nombre,
            "origen": "backtracking",
            "optimo": True,
            "asignacion": asignacion_a_json(r.asignacion),
            "f": r.objetivo.a_dict()["f"],
            "estadisticas": {"espacio": r.espacio, "nodos": r.nodos, "hojas": r.hojas,
                             "tiempo_s": round(r.tiempo, 4)},
        })
        print(f"{resumen}  ->  {destino}")
    return 0 if todo_bien else 1


if __name__ == "__main__":
    sys.exit(main())
