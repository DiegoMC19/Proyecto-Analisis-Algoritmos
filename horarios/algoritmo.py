"""Algoritmo de asignación: voraz con tres criterios + backtracking con poda.

1. El voraz se corre con tres órdenes (prioridad, escasez, opciones) y se queda con el mejor.
2. El backtracking parte de esa solución, poda por restricciones y por una cota, y tiene
   tiempo límite. Si alcanza a recorrer todo el árbol, la respuesta es la óptima.
"""

from __future__ import annotations

import math
import sys
import time
from dataclasses import dataclass

from .estado import Estado
from .modelo import Asignacion, Instancia
from .verificador import Objetivo, calcular_objetivo

EPS = 1e-9


def mejor_seccion(estado: Estado, e: str, a: str) -> tuple[str | None, float]:
    """Sección válida de a con mayor ganancia para e (None si ninguna es positiva)."""
    mejor, mejor_ganancia = None, EPS
    for g in estado.inst.secciones_por_asignatura[a]:
        if estado.puede_inscribir(e, g):
            ganancia = estado.ganancia(e, g)
            if ganancia > mejor_ganancia:
                mejor, mejor_ganancia = g, ganancia
    return mejor, mejor_ganancia


# Fase 1: voraz con varios criterios

def _escasez(inst: Instancia) -> dict[str, float]:
    """Cupo total de cada asignatura dividido entre las solicitudes que tiene."""
    demanda = {a: 0 for a in inst.asignaturas}
    for e in inst.estudiantes.values():
        for a in e.solicitudes:
            demanda[a] += 1
    return {a: sum(inst.secciones[g].cupo for g in gs) / demanda[a] if demanda[a] else math.inf
            for a, gs in inst.secciones_por_asignatura.items()}


def ordenar(inst: Instancia, criterio: str) -> list[tuple[str, str]]:
    """Solicitudes (e, a) ordenadas según el criterio."""
    solicitudes = [(e.id, a) for e in inst.estudiantes.values() for a in e.solicitudes]
    secs = inst.secciones_por_asignatura
    pi = lambda s: inst.estudiantes[s[0]].prioridad(s[1])
    if criterio == "prioridad":
        clave = lambda s: (-pi(s), len(secs[s[1]]), s)
    elif criterio == "escasez":
        esc = _escasez(inst)
        clave = lambda s: (esc[s[1]], -pi(s), s)
    elif criterio == "opciones":
        clave = lambda s: (len(secs[s[1]]), -pi(s), s)
    else:
        raise ValueError(f"criterio desconocido: {criterio}")
    return sorted(solicitudes, key=clave)


CRITERIOS = ("prioridad", "escasez", "opciones")


def voraz(inst: Instancia, criterio: str = "prioridad") -> Estado:
    estado = Estado(inst)
    for e, a in ordenar(inst, criterio):
        g, _ = mejor_seccion(estado, e, a)
        if g is not None:
            estado.inscribir(e, g)
    return estado


def voraz_criterios(inst: Instancia, criterios=CRITERIOS) -> tuple[Estado, str, dict[str, float]]:
    """Corre el voraz con cada criterio y devuelve el mejor resultado."""
    mejor, mejor_criterio, valores = None, None, {}
    for c in criterios:
        estado = voraz(inst, c)
        valores[c] = estado.f
        if mejor is None or estado.f > mejor.f + EPS:
            mejor, mejor_criterio = estado, c
    return mejor, mejor_criterio, valores


# Fase 2: backtracking con poda

@dataclass
class ResultadoBacktracking:
    asignacion: Asignacion
    f: float
    completo: bool        # True si recorrió todo el árbol (la asignación es óptima)
    nodos: int            # nodos visitados


def cota(inst: Instancia, estado: Estado, e_id: str, a: str) -> float:
    """Lo máximo que puede sumar la solicitud (e, a) a f, ignorando lo que resta."""
    e = inst.estudiantes[e_id]
    afinidad = max((e.afinidad_con(inst.secciones[g].profesor) for g in inst.secciones_por_asignatura[a]),
                   default=0)
    amigos = len(e.companeros) + len(estado.seguidores[e_id])
    return max(0.0, estado.w[1] * e.prioridad(a) + estado.w[2] * max(0, afinidad) + estado.w[3] * amigos)


def backtracking(inst: Instancia, inicial: Asignacion | None = None,
                 tiempo_max: float = 10.0) -> ResultadoBacktracking:
    solicitudes = ordenar(inst, "prioridad")
    estado = Estado(inst)
    # U[i] = suma de las cotas de las solicitudes i, i+1, ..., final
    U = [0.0] * (len(solicitudes) + 1)
    for i in range(len(solicitudes) - 1, -1, -1):
        U[i] = U[i + 1] + cota(inst, estado, *solicitudes[i])

    mejor = list(inicial or [])
    mejor_f = calcular_objetivo(inst, mejor).f if mejor else 0.0
    nodos = 0
    corte = False
    fin = time.perf_counter() + tiempo_max
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 2 * len(solicitudes) + 1000))

    def explorar(i: int) -> None:
        nonlocal mejor, mejor_f, nodos, corte
        nodos += 1
        if estado.f > mejor_f + EPS:
            mejor, mejor_f = estado.asignacion(), estado.f
        if i == len(solicitudes) or estado.f + U[i] <= mejor_f + EPS:
            return                                           # hoja o poda por cota
        if corte or time.perf_counter() > fin:
            corte = True
            return
        e, a = solicitudes[i]
        opciones = [(estado.ganancia(e, g), g) for g in inst.secciones_por_asignatura[a]
                    if estado.puede_inscribir(e, g)]          # poda por restricciones
        opciones.sort(reverse=True)
        for _, g in opciones:
            estado.inscribir(e, g)
            explorar(i + 1)
            estado.retirar(e, g)
        explorar(i + 1)                                      # opción "ninguna"

    explorar(0)
    return ResultadoBacktracking(mejor, mejor_f, not corte, nodos)


# Algoritmo completo

@dataclass
class Resultado:
    asignacion: Asignacion
    objetivo: Objetivo
    f_voraz: float                  # f del mejor criterio voraz
    criterio: str                   # criterio voraz que ganó
    f_criterios: dict[str, float]   # f de cada criterio voraz
    tiempo_voraz: float
    tiempo_backtracking: float
    backtracking: ResultadoBacktracking | None

    @property
    def tiempo(self) -> float:
        return self.tiempo_voraz + self.tiempo_backtracking


def resolver(inst: Instancia, con_backtracking: bool = True, tiempo_max: float = 10.0,
             criterios=CRITERIOS) -> Resultado:
    t0 = time.perf_counter()
    estado, criterio, valores = voraz_criterios(inst, criterios)
    x = estado.asignacion()
    t1 = time.perf_counter()
    bt = backtracking(inst, x, tiempo_max) if con_backtracking else None
    t2 = time.perf_counter()
    if bt is not None:
        x = bt.asignacion
    return Resultado(
        asignacion=x,
        objetivo=calcular_objetivo(inst, x),     # f recalculada desde cero
        f_voraz=estado.f,
        criterio=criterio,
        f_criterios=valores,
        tiempo_voraz=t1 - t0,
        tiempo_backtracking=t2 - t1,
        backtracking=bt,
    )
