"""Backtracking: encuentra la asignación óptima de instancias pequeñas.

Cada solicitud (e, a) con a ∈ R_e tiene t_a + 1 opciones: una de las t_a
secciones de a, o ninguna. El espacio completo tiene

    prod_{(e, a)} (t_a + 1)     =  (t + 1)^(n * q)  si todo es uniforme

combinaciones (Sección 5 del documento). Se recorre con backtracking: en cada
nivel se decide una solicitud y se descartan las ramas que ya violan una
restricción, porque ninguna de sus hojas puede ser válida. Esa poda no cambia
el resultado (se siguen evaluando todas las asignaciones válidas), solo evita
recorrer las inválidas.

Complejidad: O(prod (t_a + 1)) nodos en el peor caso, cada uno con costo
O(k_e + |C_e|) gracias al Estado incremental.
"""

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
