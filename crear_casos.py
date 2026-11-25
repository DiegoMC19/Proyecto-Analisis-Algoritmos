"""Escribe los 6 casos hechos a mano en datos/instancias y datos/esperadas."""

import sys
from pathlib import Path

from horarios.archivos import guardar_json
from horarios.casos import casos
from horarios.modelo import asignacion_a_json, instancia_desde_dict
from horarios.validador import validar_datos
from horarios.verificador import verificar


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    for caso in casos():
        nombre = f"caso{caso['numero']}.json"
        errores = validar_datos(caso["instancia"])
        if errores:
            print(f"{nombre}: instancia inválida {errores}", file=sys.stderr)
            return 1
        reporte = verificar(instancia_desde_dict(caso["instancia"]), caso["esperada"])
        if not reporte.valida:
            print(f"{nombre}: la asignación esperada no es válida", file=sys.stderr)
            return 1
        guardar_json(Path("datos/instancias") / nombre, caso["instancia"])
        guardar_json(Path("datos/esperadas") / nombre, {
            "instancia": nombre,
            "origen": "manual",
            "optimo": True,
            "descripcion": caso["descripcion"],
            "asignacion": asignacion_a_json(caso["esperada"]),
            "f": reporte.objetivo.a_dict()["f"],
        })
        print(f"{nombre}: f = {reporte.objetivo.a_dict()['f']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
