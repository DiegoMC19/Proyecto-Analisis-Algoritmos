"""Backtracking exacto sin cota: calcula el óptimo de instancias pequeñas."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

from .estado import Estado
from .modelo import Asignacion, Instancia
from .verificador import Objetivo, calcular_objetivo

LIMITE_POR_DEFECTO = 10_000_000
EPS = 1e-9


class InstanciaMuyGrande(Exception):
    pass


@dataclass
class ResultadoFuerzaBruta:
    asignacion: Asignacion
    objetivo: Objetivo
    espacio: int          # prod (t_a + 1): tamaño del espacio completo
    nodos: int            # nodos visitados por el backtracking
    hojas: int            # asignaciones válidas completas evaluadas
    tiempo: float         # segundos


def solicitudes_de(inst: Instancia) -> list[tuple[str, str]]:
    return [(e.id, a) for e in inst.estudiantes.values() for a in sorted(e.solicitudes)]


def tamano_espacio(inst: Instancia) -> int:
    return math.prod(len(inst.secciones_por_asignatura[a]) + 1 for _, a in solicitudes_de(inst))


def fuerza_bruta(inst: Instancia, limite: int = LIMITE_POR_DEFECTO) -> ResultadoFuerzaBruta:
    solicitudes = solicitudes_de(inst)
    espacio = tamano_espacio(inst)
    if espacio > limite:
        raise InstanciaMuyGrande(f"el espacio tiene {espacio:,} combinaciones (límite {limite:,})")

    estado = Estado(inst)
    secs = inst.secciones_por_asignatura
    mejor_f = -math.inf
    mejor: Asignacion = []
    nodos = hojas = 0
    inicio = time.perf_counter()

    def explorar(i: int) -> None:
        nonlocal mejor_f, mejor, nodos, hojas
        nodos += 1
        if i == len(solicitudes):
            hojas += 1
            if estado.f > mejor_f + EPS:
                mejor_f = estado.f
                mejor = estado.asignacion()
            return
        e, a = solicitudes[i]
        explorar(i + 1)                         # opción: no inscribir la solicitud
        for g in secs[a]:                       # opción: cada sección de a
            if estado.puede_inscribir(e, g):
                estado.inscribir(e, g)
                explorar(i + 1)
                estado.retirar(e, g)

    explorar(0)
    return ResultadoFuerzaBruta(
        asignacion=mejor,
        objetivo=calcular_objetivo(inst, mejor),
        espacio=espacio,
        nodos=nodos,
        hojas=hojas,
        tiempo=time.perf_counter() - inicio,
    )
