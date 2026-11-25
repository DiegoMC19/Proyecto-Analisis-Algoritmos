"""Experimentos para la sustentación.

    1. Calidad:        instancias pequeñas (n = 3..6) con óptimo por el
                       backtracking exacto (fuerza_bruta). Brecha del voraz con
                       un criterio, del voraz con varios criterios y del voraz
                       + backtracking con poda.
    2. Escalabilidad:  n = 100 ... 5000 con varias semillas. Tiempo, f y
                       solicitudes inscritas.
    3. Competencia:    n = 1000 variando la holgura (cupos / demanda).

Todas las salidas se verifican con el verificador antes de guardarlas.
Los resultados quedan en resultados/experimentos/*.csv y las gráficas se
generan con graficas.py.

Uso:
    python experimentos.py            # todo (~10 minutos)
    python experimentos.py --rapido   # versión corta para probar
    python experimentos.py --solo escalabilidad
"""

import argparse
import csv
import sys
import time
from pathlib import Path

from horarios.algoritmo import resolver, voraz
from horarios.fuerza_bruta import InstanciaMuyGrande, fuerza_bruta
from horarios.generador import Parametros, generar
from horarios.modelo import instancia_desde_dict
from horarios.verificador import verificar

CARPETA = Path("resultados/experimentos")
PEQUENA = dict(asignaturas=5, solicitudes_por_estudiante=(2, 3), secciones_por_asignatura=(1, 3), holgura=0.7)
LIMITE_BT = 10.0      # segundos de backtracking en las instancias grandes


def guardar_csv(nombre: str, filas: list[dict]) -> None:
    CARPETA.mkdir(parents=True, exist_ok=True)
    with open(CARPETA / nombre, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(f"  -> {CARPETA / nombre} ({len(filas)} filas)")


def comprobar(inst, asignacion) -> None:
    reporte = verificar(inst, asignacion)
    if not reporte.valida:
        raise AssertionError(f"salida inválida: {[v.a_dict() for v in reporte.violaciones[:3]]}")


def correr(inst, con_backtracking: bool, tiempo_max: float):
    r = resolver(inst, con_backtracking=con_backtracking, tiempo_max=tiempo_max)
    comprobar(inst, r.asignacion)
    return r


def brecha(optimo: float, f: float) -> float:
    return 100 * (optimo - f) / abs(optimo) if optimo else 0.0


def mejora(base: float, f: float) -> float:
    return 100 * (f - base) / abs(base) if base else 0.0


# ----------------------------------------------------------------------------

def experimento_calidad(rapido: bool) -> None:
    print("1. Calidad contra el óptimo")
    plan = {3: 30, 4: 30, 5: 30, 6: 10} if not rapido else {3: 5, 4: 5, 5: 3}
    filas = []
    for n, semillas in plan.items():
        for s in range(1, semillas + 1):
            inst = instancia_desde_dict(generar(Parametros(estudiantes=n, semilla=s, **PEQUENA)))
            try:
                fb = fuerza_bruta(inst, limite=60_000_000)
            except InstanciaMuyGrande:
                continue
            t = time.perf_counter()
            v1 = voraz(inst, "prioridad")
            t_v1 = time.perf_counter() - t
            comprobar(inst, v1.asignacion())
            r = correr(inst, True, 60.0)
            opt = fb.objetivo.f
            filas.append({
                "n": n, "semilla": s, "espacio": fb.espacio, "nodos": fb.nodos,
                "tiempo_fb": round(fb.tiempo, 5), "f_optimo": round(opt, 4),
                "f_voraz": round(v1.f, 4), "tiempo_voraz": round(t_v1, 6),
                "f_vc": round(r.f_voraz, 4), "criterio": r.criterio, "tiempo_vc": round(r.tiempo_voraz, 6),
                "f_bt": round(r.objetivo.f, 4), "tiempo_bt": round(r.tiempo, 6),
                "nodos_bt": r.backtracking.nodos, "completo_bt": r.backtracking.completo,
                "brecha_voraz": round(brecha(opt, v1.f), 4),
                "brecha_vc": round(brecha(opt, r.f_voraz), 4),
                "brecha_bt": round(brecha(opt, r.objetivo.f), 4),
            })
        print(f"  n = {n}: {sum(1 for f in filas if f['n'] == n)} instancias")
    guardar_csv("calidad.csv", filas)


def experimento_escalabilidad(rapido: bool) -> None:
    print(f"2. Escalabilidad (backtracking con límite de {LIMITE_BT:g} s)")
    tamanos = [100, 250, 500, 1000, 2500, 5000] if not rapido else [100, 250, 500]
    semillas = [1, 2, 3] if not rapido else [1]
    limite = LIMITE_BT if not rapido else 1.0
    filas = []
    for n in tamanos:
        for s in semillas:
            inst = instancia_desde_dict(generar(Parametros(estudiantes=n, semilla=s)))
            solicitudes = sum(len(e.solicitudes) for e in inst.estudiantes.values())
            t = time.perf_counter()
            v1 = voraz(inst, "prioridad")
            t_v1 = time.perf_counter() - t
            r = correr(inst, True, limite)
            filas.append({
                "n": n, "semilla": s, "asignaturas": len(inst.asignaturas), "secciones": len(inst.secciones),
                "solicitudes": solicitudes,
                "f_voraz": round(v1.f, 3), "tiempo_voraz": round(t_v1, 4),
                "f_vc": round(r.f_voraz, 3), "criterio": r.criterio, "tiempo_vc": round(r.tiempo_voraz, 4),
                "f_bt": round(r.objetivo.f, 3), "tiempo_bt": round(r.tiempo, 4),
                "inscritas_vc": len(voraz(inst, r.criterio).asignacion()),
                "inscritas_bt": len(r.asignacion),
                "nodos_bt": r.backtracking.nodos, "completo_bt": r.backtracking.completo,
                "mejora_vc_pct": round(mejora(v1.f, r.f_voraz), 3),
                "mejora_bt_pct": round(mejora(r.f_voraz, r.objetivo.f), 3),
            })
            print(f"  n = {n}, semilla {s}: voraz {r.tiempo_voraz:.2f} s (gana {r.criterio}, "
                  f"+{filas[-1]['mejora_vc_pct']} %), backtracking +{filas[-1]['mejora_bt_pct']} %")
    guardar_csv("escalabilidad.csv", filas)


def experimento_competencia(rapido: bool) -> None:
    print("3. Competencia por los cupos (holgura)")
    holguras = [0.5, 0.7, 0.9, 1.1, 1.3, 1.5] if not rapido else [0.5, 1.0, 1.5]
    n = 1000 if not rapido else 200
    limite = LIMITE_BT if not rapido else 1.0
    filas = []
    for h in holguras:
        inst = instancia_desde_dict(generar(Parametros(estudiantes=n, semilla=1, holgura=h)))
        solicitudes = [(e.id, a, p) for e in inst.estudiantes.values() for a, p in e.solicitudes.items()]
        prioritarias = {(e, a) for e, a, p in solicitudes if p == 5}
        fila = {"holgura": h, "n": n, "solicitudes": len(solicitudes)}
        r = correr(inst, True, limite)
        for nombre, asignacion, f in (("vc", voraz(inst, r.criterio).asignacion(), r.f_voraz),
                                      ("bt", r.asignacion, r.objetivo.f)):
            inscritas = {(e, inst.secciones[g].asignatura) for e, g in asignacion}
            fila[f"pct_inscritas_{nombre}"] = round(100 * len(inscritas) / len(solicitudes), 2)
            fila[f"pct_prioridad5_{nombre}"] = round(100 * len(inscritas & prioritarias) / len(prioritarias), 2)
            fila[f"f_{nombre}"] = round(f, 3)
        filas.append(fila)
        print(f"  holgura {h}: inscritas {fila['pct_inscritas_vc']} % -> {fila['pct_inscritas_bt']} %")
    guardar_csv("competencia.csv", filas)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Experimentos del proyecto")
    parser.add_argument("--rapido", action="store_true")
    parser.add_argument("--solo", choices=["calidad", "escalabilidad", "competencia"])
    args = parser.parse_args()
    t0 = time.perf_counter()
    experimentos = {"calidad": experimento_calidad, "escalabilidad": experimento_escalabilidad,
                    "competencia": experimento_competencia}
    for nombre, fn in experimentos.items():
        if args.solo in (None, nombre):
            fn(args.rapido)
    print(f"Listo en {time.perf_counter() - t0:.0f} s. Gráficas: python graficas.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
