"""Ejecuta el algoritmo (voraz con varios criterios + backtracking con poda).

Uso:
    python resolver.py datos/instancias/inst_n1000_s42.json
    python resolver.py datos/instancias/*.json --solo-voraz
    python resolver.py datos/instancias/inst_n5000_s42.json --tiempo 30

Guarda la salida en resultados/<algoritmo>/<instancia>.json con el formato del
Código 2, la verifica y, si existe datos/esperadas/<instancia>.json, la compara.
"""

import argparse
import sys
from pathlib import Path

from horarios.algoritmo import resolver
from horarios.archivos import cargar_instancia, guardar_json, leer_json
from horarios.modelo import asignacion_a_json
from horarios.verificador import comparar_con_esperada, verificar


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Asignación de horarios: voraz + backtracking")
    parser.add_argument("instancias", nargs="+")
    parser.add_argument("--solo-voraz", action="store_true", help="no hacer el backtracking")
    parser.add_argument("--tiempo", type=float, default=10.0, help="segundos máximos del backtracking")
    parser.add_argument("--esperadas", default="datos/esperadas")
    args = parser.parse_args()

    nombre_alg = "voraz" if args.solo_voraz else "voraz_bt"
    todo_bien = True
    for ruta in args.instancias:
        nombre = Path(ruta).name
        inst = cargar_instancia(ruta)
        r = resolver(inst, con_backtracking=not args.solo_voraz, tiempo_max=args.tiempo)

        asignadas = {(e, inst.secciones[g].asignatura) for e, g in r.asignacion}
        no_asignadas = [{"estudiante": e.id, "asignatura": a}
                        for e in inst.estudiantes.values() for a in sorted(e.solicitudes)
                        if (e.id, a) not in asignadas]
        salida = {
            "instancia": nombre,
            "algoritmo": nombre_alg,
            "asignacion": asignacion_a_json(r.asignacion),
            "no_asignadas": no_asignadas,
            "objetivo": r.objetivo.a_dict(),
            "tiempo_ms": round(r.tiempo * 1000, 1),
        }
        guardar_json(Path("resultados") / nombre_alg / nombre, salida, indentar=len(inst.estudiantes) < 1000)

        reporte = verificar(inst, r.asignacion)
        total = len(asignadas) + len(no_asignadas)
        criterios = ", ".join(f"{c} {v:.1f}" for c, v in r.f_criterios.items())
        linea = (f"{nombre}: f = {r.objetivo.f:.3f}  |  voraz ({criterios}; gana {r.criterio})  |  "
                 f"{len(asignadas)}/{total} solicitudes inscritas  |  {r.tiempo:.2f} s")
        if r.backtracking:
            b = r.backtracking
            linea += (f"  |  backtracking: {b.nodos} nodos, "
                      + ("árbol completo (óptimo)" if b.completo else f"cortado a los {args.tiempo:g} s"))
        if not reporte.valida:
            todo_bien = False
            linea += f"  |  INVÁLIDA: {[v.a_dict() for v in reporte.violaciones[:3]]}"

        ruta_esperada = Path(args.esperadas) / nombre
        if ruta_esperada.exists():
            esperada = leer_json(ruta_esperada)
            comp = comparar_con_esperada(reporte, r.asignacion, esperada)
            if esperada.get("f") is not None:
                f_opt = esperada["f"]
                brecha = 100 * (f_opt - r.objetivo.f) / abs(f_opt) if f_opt else 0.0
                linea += f"  |  óptimo {f_opt} (brecha {brecha:.2f} %)"
            linea += "  -> correcta" if comp["correcta"] else f"  -> {comp['motivo']}"
        print(linea)
    return 0 if todo_bien else 1


if __name__ == "__main__":
    sys.exit(main())
