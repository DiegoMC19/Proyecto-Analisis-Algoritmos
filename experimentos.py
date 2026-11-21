"""Experimentos para la sustentación.

    1. Calidad:        instancias pequeñas (n = 3..6) con óptimo por fuerza bruta.
                       Brecha del voraz y del voraz + búsqueda local contra el óptimo,
                       y tiempo de la fuerza bruta contra el del algoritmo.
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

from horarios.algoritmo import resolver
from horarios.fuerza_bruta import InstanciaMuyGrande, fuerza_bruta
from horarios.generador import Parametros, generar
from horarios.modelo import instancia_desde_dict
from horarios.verificador import verificar

CARPETA = Path("resultados/experimentos")
PEQUENA = dict(asignaturas=5, solicitudes_por_estudiante=(2, 3), secciones_por_asignatura=(1, 3), holgura=0.7)


def guardar_csv(nombre: str, filas: list[dict]) -> None:
    CARPETA.mkdir(parents=True, exist_ok=True)
    with open(CARPETA / nombre, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(f"  -> {CARPETA / nombre} ({len(filas)} filas)")


def correr(inst, con_busqueda: bool, tiempo_max: float = 600.0):
    r = resolver(inst, con_busqueda=con_busqueda, tiempo_max=tiempo_max)
    reporte = verificar(inst, r.asignacion)
    if not reporte.valida:
        raise AssertionError(f"salida inválida: {[v.a_dict() for v in reporte.violaciones[:3]]}")
    return r


def brecha(optimo: float, f: float) -> float:
    return 100 * (optimo - f) / abs(optimo) if optimo else 0.0


# ----------------------------------------------------------------------------

def experimento_calidad(rapido: bool) -> None:
    print("1. Calidad contra el óptimo (fuerza bruta)")
    plan = {3: 30, 4: 30, 5: 30, 6: 10} if not rapido else {3: 5, 4: 5, 5: 3}
    filas = []
    for n, semillas in plan.items():
        for s in range(1, semillas + 1):
            inst = instancia_desde_dict(generar(Parametros(estudiantes=n, semilla=s, **PEQUENA)))
            try:
                fb = fuerza_bruta(inst, limite=60_000_000)
            except InstanciaMuyGrande:
                continue
            rv, rb = correr(inst, False), correr(inst, True)
            opt = fb.objetivo.f
            filas.append({
                "n": n, "semilla": s, "espacio": fb.espacio, "nodos": fb.nodos,
                "tiempo_fb": round(fb.tiempo, 5), "f_optimo": round(opt, 4),
                "f_voraz": round(rv.objetivo.f, 4), "tiempo_voraz": round(rv.tiempo, 6),
                "f_bl": round(rb.objetivo.f, 4), "tiempo_bl": round(rb.tiempo, 6),
                "brecha_voraz": round(brecha(opt, rv.objetivo.f), 4),
                "brecha_bl": round(brecha(opt, rb.objetivo.f), 4),
            })
        print(f"  n = {n}: {sum(1 for f in filas if f['n'] == n)} instancias")
    guardar_csv("calidad.csv", filas)


def experimento_escalabilidad(rapido: bool) -> None:
    print("2. Escalabilidad")
    tamanos = [100, 250, 500, 1000, 2500, 5000] if not rapido else [100, 250, 500]
    semillas = [1, 2, 3] if not rapido else [1]
    filas = []
    for n in tamanos:
        for s in semillas:
            datos = generar(Parametros(estudiantes=n, semilla=s))
            inst = instancia_desde_dict(datos)
            solicitudes = sum(len(e.solicitudes) for e in inst.estudiantes.values())
            rv, rb = correr(inst, False), correr(inst, True)
            filas.append({
                "n": n, "semilla": s, "asignaturas": len(inst.asignaturas), "secciones": len(inst.secciones),
                "solicitudes": solicitudes,
                "f_voraz": round(rv.objetivo.f, 3), "tiempo_voraz": round(rv.tiempo, 4),
                "inscritas_voraz": len(rv.asignacion),
                "f_bl": round(rb.objetivo.f, 3), "tiempo_bl": round(rb.tiempo, 4),
                "inscritas_bl": len(rb.asignacion),
                "pasadas": rb.busqueda.pasadas, "optimo_local": rb.busqueda.optimo_local,
                "mejora_bl_pct": round(100 * (rb.objetivo.f - rv.objetivo.f) / abs(rv.objetivo.f), 3),
            })
            print(f"  n = {n}, semilla {s}: voraz {rv.tiempo:.2f} s, voraz+BL {rb.tiempo:.2f} s, "
                  f"mejora {filas[-1]['mejora_bl_pct']} %")
    guardar_csv("escalabilidad.csv", filas)


def experimento_competencia(rapido: bool) -> None:
    print("3. Competencia por los cupos (holgura)")
    holguras = [0.5, 0.7, 0.9, 1.1, 1.3, 1.5] if not rapido else [0.5, 1.0, 1.5]
    n = 1000 if not rapido else 200
    filas = []
    for h in holguras:
        inst = instancia_desde_dict(generar(Parametros(estudiantes=n, semilla=1, holgura=h)))
        solicitudes = [(e.id, a, p) for e in inst.estudiantes.values() for a, p in e.solicitudes.items()]
        prioritarias = {(e, a) for e, a, p in solicitudes if p == 5}
        fila = {"holgura": h, "n": n, "solicitudes": len(solicitudes)}
        for nombre, bl in (("voraz", False), ("bl", True)):
            r = correr(inst, bl)
            inscritas = {(e, inst.secciones[g].asignatura) for e, g in r.asignacion}
            fila[f"pct_inscritas_{nombre}"] = round(100 * len(inscritas) / len(solicitudes), 2)
            fila[f"pct_prioridad5_{nombre}"] = round(100 * len(inscritas & prioritarias) / len(prioritarias), 2)
            fila[f"f_{nombre}"] = round(r.objetivo.f, 3)
            fila[f"tiempo_{nombre}"] = round(r.tiempo, 3)
        filas.append(fila)
        print(f"  holgura {h}: inscritas {fila['pct_inscritas_voraz']} % -> {fila['pct_inscritas_bl']} %")
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
