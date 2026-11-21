"""Verificador de asignaciones.

Revisa que una asignación X cumpla las restricciones del documento

    (1) a_g ∈ R_e                               (solo asignaturas pedidas)
    (2) a_g != a_g'  y  F_g ∩ F_g' = ∅           (sin repetir asignatura ni cruces)
    (3) F_g ∩ N_e = ∅                            (disponibilidad)
    (4) |{e | (e, g) ∈ X}| <= c_g               (cupo)

y calcula por su cuenta la función objetivo

    f(X) = w1 f1 + w2 f2 + w3 f3 - w4 f4 - w5 f5.

Además de (1)-(4) se reportan errores de "formato": pares que nombran un
estudiante o una sección que no existen, o pares repetidos.

Complejidad: con |X| pares, k_e secciones por estudiante y |F_g| franjas por
sección, la verificación cuesta O(|X| + sum_e k_e^2 * max|F_g|), que en la
práctica es lineal en |X| porque k_e y |F_g| son pequeños (<= 6 y <= 8).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .modelo import Asignacion, Instancia

TOLERANCIA = 1e-6


@dataclass
class Violacion:
    restriccion: int | str      # 1, 2, 3, 4 o "formato"
    detalle: str
    estudiante: str | None = None
    seccion: str | None = None

    def a_dict(self) -> dict:
        d = {"restriccion": self.restriccion}
        if self.estudiante is not None:
            d["estudiante"] = self.estudiante
        if self.seccion is not None:
            d["seccion"] = self.seccion
        d["detalle"] = self.detalle
        return d


@dataclass
class Objetivo:
    f1: float = 0.0
    f2: float = 0.0
    f3: float = 0.0
    f4: float = 0.0
    f5: float = 0.0
    f: float = 0.0

    def a_dict(self, decimales: int = 6) -> dict:
        def r(x):
            x = round(x, decimales)
            return int(x) if x == int(x) else x
        return {k: r(v) for k, v in vars(self).items()}


@dataclass
class Reporte:
    valida: bool
    violaciones: list[Violacion] = field(default_factory=list)
    objetivo: Objetivo = field(default_factory=Objetivo)


# ----------------------------------------------------------------------------
# Agrupación de X
# ----------------------------------------------------------------------------

def _agrupar(inst: Instancia, asignacion: Asignacion, violaciones: list[Violacion] | None):
    """Devuelve G_X(e) para cada estudiante y los inscritos de cada sección.

    Los pares con ids inexistentes o repetidos se descartan (y se reportan
    como violaciones de formato si se pasa la lista `violaciones`).
    """
    secciones_de: dict[str, list[str]] = defaultdict(list)   # G_X(e)
    inscritos: dict[str, set[str]] = defaultdict(set)         # {e | (e, g) ∈ X}
    vistos: set[tuple[str, str]] = set()

    def reportar(detalle, e, g):
        if violaciones is not None:
            violaciones.append(Violacion("formato", detalle, e, g))

    for e, g in asignacion:
        if e not in inst.estudiantes:
            reportar(f"el estudiante '{e}' no existe", e, g)
        elif g not in inst.secciones:
            reportar(f"la sección '{g}' no existe", e, g)
        elif (e, g) in vistos:
            reportar("par (estudiante, sección) repetido", e, g)
        else:
            vistos.add((e, g))
            secciones_de[e].append(g)
            inscritos[g].add(e)
    return secciones_de, inscritos


# ----------------------------------------------------------------------------
# Función objetivo
# ----------------------------------------------------------------------------

def _objetivo(inst: Instancia, secciones_de, inscritos) -> Objetivo:
    o = Objetivo()
    for e_id, gs in secciones_de.items():
        e = inst.estudiantes[e_id]
        secs = [inst.secciones[g] for g in gs]
        ocupadas = set()                                   # O_X(e)
        for g in secs:
            o.f1 += e.prioridad(g.asignatura)              # pi_e(a_g)
            o.f2 += e.afinidad_con(g.profesor)             # phi_e(p_g)
            o.f3 += len(e.companeros & inscritos[g.id])    # e' ∈ C_e en la misma sección
            ocupadas |= g.franjas
        o.f4 += len(e.libres & ocupadas)                   # |L_e ∩ O_X(e)|
        # f5: pares ordenados g != g' con una clase de g en (d, b) y una de g' en (d, b+1)
        for g in secs:
            for g2 in secs:
                if g is g2:
                    continue
                seguidas = sum(1 for d, b in g.franjas if (d, b + 1) in g2.franjas)
                if seguidas:
                    o.f5 += inst.distancia(g.salon, g2.salon) * seguidas
    o.f = (inst.peso(1) * o.f1 + inst.peso(2) * o.f2 + inst.peso(3) * o.f3
           - inst.peso(4) * o.f4 - inst.peso(5) * o.f5)
    return o


def calcular_objetivo(inst: Instancia, asignacion: Asignacion) -> Objetivo:
    """f1, ..., f5 y f de la asignación (ignora pares con ids inexistentes)."""
    secciones_de, inscritos = _agrupar(inst, asignacion, None)
    return _objetivo(inst, secciones_de, inscritos)


# ----------------------------------------------------------------------------
# Restricciones
# ----------------------------------------------------------------------------

def verificar(inst: Instancia, asignacion: Asignacion) -> Reporte:
    """Revisa las restricciones (1)-(4) y recalcula f."""
    violaciones: list[Violacion] = []
    secciones_de, inscritos = _agrupar(inst, asignacion, violaciones)

    for e_id, gs in secciones_de.items():
        e = inst.estudiantes[e_id]
        secs = [inst.secciones[g] for g in gs]
        for i, g in enumerate(secs):
            # (1) solo asignaturas pedidas
            if g.asignatura not in e.solicitudes:
                violaciones.append(Violacion(
                    1, f"no pidió la asignatura {g.asignatura}", e_id, g.id))
            # (3) no tiene clase cuando no puede asistir
            choque = g.franjas & e.no_disponibles
            if choque:
                violaciones.append(Violacion(
                    3, f"tiene clase en franjas no disponibles {sorted(choque)}", e_id, g.id))
            # (2) no repite asignatura ni tiene cruces (cada par una sola vez)
            for g2 in secs[i + 1:]:
                if g.asignatura == g2.asignatura:
                    violaciones.append(Violacion(
                        2, f"inscrito dos veces en {g.asignatura} ({g.id} y {g2.id})", e_id, g.id))
                cruce = g.franjas & g2.franjas
                if cruce:
                    violaciones.append(Violacion(
                        2, f"{g.id} y {g2.id} se cruzan en {sorted(cruce)}", e_id, g.id))

    # (4) cupo
    for g_id, alumnos in inscritos.items():
        cupo = inst.secciones[g_id].cupo
        if len(alumnos) > cupo:
            violaciones.append(Violacion(
                4, f"{len(alumnos)} inscritos, cupo {cupo}", seccion=g_id))

    return Reporte(
        valida=not violaciones,
        violaciones=violaciones,
        objetivo=_objetivo(inst, secciones_de, inscritos),
    )


# ----------------------------------------------------------------------------
# Comparación con la salida esperada
# ----------------------------------------------------------------------------

def comparar_con_esperada(reporte: Reporte, asignacion: Asignacion, esperada: dict) -> dict:
    """Compara una salida ya verificada con su salida esperada (Sección 4.4).

    Es correcta si es válida y su f coincide con la esperada (tolerancia 1e-6).
    En los casos hechos a mano ("origen": "manual") también se compara la
    asignación exacta. Si no se conoce el óptimo, solo cuenta la validez.
    """
    if not reporte.valida:
        return {"correcta": False, "motivo": "la salida no cumple las restricciones"}

    f_esperada = esperada.get("f")
    if not esperada.get("optimo") or f_esperada is None:
        return {"correcta": True, "motivo": "no se conoce el óptimo; solo se revisó que sea válida"}

    f = reporte.objetivo.f
    if f < f_esperada - TOLERANCIA:
        return {"correcta": False, "motivo": f"f = {f:.6f} es menor que el óptimo {f_esperada}"}
    if f > f_esperada + TOLERANCIA:
        return {"correcta": False,
                "motivo": f"f = {f:.6f} es mayor que el 'óptimo' {f_esperada}: revisar la salida esperada"}

    if esperada.get("origen") == "manual" and esperada.get("asignacion") is not None:
        esperado = {(p["estudiante"], p["seccion"]) for p in esperada["asignacion"]}
        if set(asignacion) != esperado:
            return {"correcta": False, "motivo": "f coincide pero la asignación no es la esperada"}

    return {"correcta": True, "motivo": "válida y con el valor óptimo"}


def reporte_a_dict(nombre_instancia: str, reporte: Reporte, objetivo_reportado: dict | None = None,
                   comparacion: dict | None = None) -> dict:
    """Arma el JSON del reporte del verificador con el formato del Código 4."""
    d = {
        "instancia": nombre_instancia,
        "valida": reporte.valida,
        "violaciones": [v.a_dict() for v in reporte.violaciones],
        "f_recalculada": reporte.objetivo.a_dict()["f"],
        "objetivo_recalculado": reporte.objetivo.a_dict(),
    }
    if objetivo_reportado is not None and "f" in objetivo_reportado:
        d["coincide_objetivo"] = abs(objetivo_reportado["f"] - reporte.objetivo.f) <= TOLERANCIA * max(1.0, abs(reporte.objetivo.f))
    if comparacion is not None:
        d["comparacion_esperada"] = comparacion
    return d
