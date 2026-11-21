"""Algoritmo de asignación: voraz por prioridad + búsqueda local.

Fase 1 - Voraz
    Se ordenan todas las solicitudes (e, a) de mayor a menor prioridad pi_e(a)
    (w1 es el peso más grande, así que lo más importante es inscribir lo
    prioritario). Cada solicitud toma la sección válida con mayor ganancia en
    f, si esa ganancia es positiva. La ganancia ya incluye afinidad, amigos
    inscritos antes, franjas libres y distancia a las otras clases de e.

    Costo: O(Q log Q) para ordenar y O(Q * t * (k + c)) para decidir, con
    Q = número de solicitudes, t = secciones por asignatura, k = clases por
    estudiante y c = compañeros por estudiante. Es casi lineal en Q.

Fase 2 - Búsqueda local (mejor la primera mejora, por pasadas)
    El voraz no se devuelve: si un estudiante de prioridad baja tomó un cupo o
    un horario que después necesitaba otro, se queda así. La búsqueda local
    corrige eso con tres movimientos, y solo acepta un cambio si f aumenta:

    A. Insertar:  una solicitud pendiente toma una sección que quedó libre.
    B. Cambiar:   un estudiante pasa a otra sección de la misma asignatura
                  (o la suelta, si eso sube f).
    C. Expulsar:  una solicitud pendiente (e, a) entra a la sección g de a
                  sacando lo que estorba: las clases de e que se cruzan con g
                  y, si g está llena, a un estudiante e2 de g (se prueban los
                  3 más prometedores). Después se intenta reubicar lo que
                  salió en otras secciones. Si f no mejoró, se deshace todo.
    D. Intercambiar: dos estudiantes de dos secciones llenas de la misma
                  asignatura cambian de sección entre sí (ninguno de los
                  dos podría moverse solo porque no hay cupo). El cambio en f
                  se calcula con una fórmula directa, sin modificar nada.

    Se repiten pasadas hasta que una pasada completa no encuentra ninguna
    mejora (óptimo local) o hasta el límite de pasadas o de tiempo. Después
    de la primera pasada solo se revisan las asignaturas y estudiantes que
    cambiaron (clase Sucios).

    Costo de una pasada completa, con P solicitudes pendientes, t secciones
    por asignatura y c el cupo de una sección:
        A: O(P * t)    B: O(|X| * t)    C: O(P * t * 3)    D: O(m * t^2 * c^2)
    Cada pasada mejora f estrictamente, así que la búsqueda siempre termina.

La f de cada paso se lleva con el Estado incremental (O(k + c) por cambio).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .estado import Estado
from .modelo import Asignacion, Instancia
from .verificador import Objetivo, calcular_objetivo

EPS = 1e-9


# ----------------------------------------------------------------------------
# Transacciones: permiten probar un movimiento y deshacerlo
# ----------------------------------------------------------------------------

class Transaccion:
    def __init__(self, estado: Estado):
        self.estado = estado
        self.f_inicial = estado.f
        self.ops: list[tuple[str, str, str]] = []

    def inscribir(self, e: str, g: str) -> None:
        self.estado.inscribir(e, g)
        self.ops.append(("+", e, g))

    def retirar(self, e: str, g: str) -> None:
        self.estado.retirar(e, g)
        self.ops.append(("-", e, g))

    def ubicar(self, e: str, a: str) -> None:
        """Inscribe a e en la mejor sección válida de a, si mejora f."""
        g = mejor_seccion(self.estado, e, a)
        if g is not None:
            self.inscribir(e, g)

    def mejora(self) -> bool:
        return self.estado.f > self.f_inicial + EPS

    def deshacer(self) -> None:
        for op, e, g in reversed(self.ops):
            if op == "+":
                self.estado.retirar(e, g)
            else:
                self.estado.inscribir(e, g)
        self.ops.clear()


def mejor_seccion(estado: Estado, e: str, a: str, minimo: float = EPS) -> str | None:
    """Sección válida de a con mayor ganancia para e (None si ninguna supera `minimo`)."""
    mejor, mejor_ganancia = None, minimo
    for g in estado.inst.secciones_por_asignatura[a]:
        if estado.puede_inscribir(e, g):
            ganancia = estado.ganancia(e, g)
            if ganancia > mejor_ganancia:
                mejor, mejor_ganancia = g, ganancia
    return mejor


def pendientes(estado: Estado) -> list[tuple[str, str]]:
    """Solicitudes sin sección, de mayor a menor prioridad."""
    inst = estado.inst
    lista = [(e.id, a) for e in inst.estudiantes.values() for a in e.solicitudes
             if a not in estado.asignatura_de[e.id]]
    lista.sort(key=lambda s: (-inst.estudiantes[s[0]].prioridad(s[1]), s[0], s[1]))
    return lista


# ----------------------------------------------------------------------------
# Fase 1: voraz
# ----------------------------------------------------------------------------

def voraz(inst: Instancia) -> Estado:
    estado = Estado(inst)
    solicitudes = [(e.id, a) for e in inst.estudiantes.values() for a in e.solicitudes]
    # Mayor prioridad primero; entre iguales, la asignatura con menos secciones (menos opciones).
    solicitudes.sort(key=lambda s: (-inst.estudiantes[s[0]].prioridad(s[1]),
                                    len(inst.secciones_por_asignatura[s[1]]), s[0], s[1]))
    for e, a in solicitudes:
        g = mejor_seccion(estado, e, a)
        if g is not None:
            estado.inscribir(e, g)
    return estado


# ----------------------------------------------------------------------------
# Fase 2: búsqueda local
# ----------------------------------------------------------------------------

@dataclass
class EstadisticasBusqueda:
    pasadas: int = 0
    insertar: int = 0
    cambiar: int = 0
    expulsar: int = 0
    intercambiar: int = 0
    optimo_local: bool = False
    f_por_pasada: list[float] = field(default_factory=list)


class Sucios:
    """Qué cambió desde la pasada anterior, para no volver a revisar lo que sigue igual.

    Un movimiento sobre la asignatura a solo puede dar un resultado distinto
    al de la pasada anterior si cambió alguna sección de a o alguno de sus
    estudiantes. Por eso, después de la primera pasada, solo se revisan esas
    asignaturas y estudiantes. Cuando una pasada así no encuentra nada, se
    hace una pasada completa para confirmar que es un óptimo local.
    """

    def __init__(self, estado: Estado):
        self.estado = estado
        self.e: set[str] = set()
        self.g: set[str] = set()
        self.completa = True
        self.rev_e: set[str] = set()
        self.rev_a: set[str] = set()

    def marcar(self, ops) -> None:
        for _, e, g in ops:
            self.e.add(e)
            self.g.add(g)

    def iniciar_pasada(self, completa: bool) -> None:
        inst = self.estado.inst
        self.completa = completa
        self.rev_e = self.e
        self.rev_a = {inst.secciones[g].asignatura for g in self.g}
        for e in self.e:
            for g in self.estado.secciones_de[e]:
                self.rev_a.add(inst.secciones[g].asignatura)
        self.e, self.g = set(), set()

    def revisar(self, e: str | None, a: str) -> bool:
        return self.completa or a in self.rev_a or (e is not None and e in self.rev_e)


def _mov_insertar(estado: Estado, s: Sucios) -> int:
    hechos = 0
    for e, a in pendientes(estado):
        g = mejor_seccion(estado, e, a)
        if g is not None:
            estado.inscribir(e, g)
            s.marcar([("+", e, g)])
            hechos += 1
    return hechos


def _mov_cambiar(estado: Estado, s: Sucios) -> int:
    hechos = 0
    inst = estado.inst
    for e in inst.estudiantes:
        for g in list(estado.secciones_de[e]):
            a = inst.secciones[g].asignatura
            if not s.revisar(e, a):
                continue
            t = Transaccion(estado)
            t.retirar(e, g)
            actual = estado.ganancia(e, g)            # lo que aporta quedarse en g
            if actual <= EPS:
                # Soltarla ya sube f (o no cambia); probar otra sección o dejarla.
                t.ubicar(e, a)
            else:
                nueva = mejor_seccion(estado, e, a, minimo=actual + EPS)
                if nueva is not None:
                    t.inscribir(e, nueva)
            if t.mejora():
                s.marcar(t.ops)
                hechos += 1
            else:
                t.deshacer()
    return hechos


def _mov_expulsar(estado: Estado, s: Sucios, limite_tiempo: float) -> int:
    hechos = 0
    inst = estado.inst
    for e, a in pendientes(estado):
        if time.perf_counter() > limite_tiempo:
            break
        if a in estado.asignatura_de[e] or not s.revisar(e, a):   # ya se inscribió, o nada cambió
            continue
        est = inst.estudiantes[e]
        for g in inst.secciones_por_asignatura[a]:
            sec = inst.secciones[g]
            if sec.franjas & est.no_disponibles:
                continue
            conflictos = [g2 for g2 in estado.secciones_de[e] if inst.secciones[g2].franjas & sec.franjas]
            llena = len(estado.inscritos[g]) >= sec.cupo
            candidatos = _candidatos_expulsion(estado, g, a) if llena else [None]
            exito = False
            for e2 in candidatos:
                t = Transaccion(estado)
                for g2 in conflictos:
                    t.retirar(e, g2)
                if e2 is not None:
                    t.retirar(e2, g)
                if not estado.puede_inscribir(e, g):
                    t.deshacer()
                    continue
                t.inscribir(e, g)
                if e2 is not None:
                    t.ubicar(e2, a)                       # reubicar al expulsado
                for g2 in conflictos:
                    t.ubicar(e, inst.secciones[g2].asignatura)   # reubicar lo que e soltó
                if t.mejora():
                    s.marcar(t.ops)
                    hechos += 1
                    exito = True
                    break
                t.deshacer()
            if exito:
                break
    return hechos


CANDIDATOS_EXPULSION = 3


def _candidatos_expulsion(estado: Estado, g: str, a: str) -> list[str]:
    """Los estudiantes de g que más conviene probar sacar (a lo sumo CANDIDATOS_EXPULSION).

    Primero los que tienen otra sección libre de a a donde moverse (sacarlos
    casi no cuesta nada) y, entre ellos, los de menor prioridad pi_e2(a).
    Probar a todos los de la sección multiplica el tiempo por el cupo (~20)
    y casi nunca encuentra algo que estos no encuentren.
    """
    inst = estado.inst
    otras = [g2 for g2 in inst.secciones_por_asignatura[a]
             if g2 != g and len(estado.inscritos[g2]) < inst.secciones[g2].cupo]

    def clave(e2):
        tiene_alternativa = any(_puede_tras_soltar(estado, e2, g, g2) for g2 in otras)
        return (not tiene_alternativa, inst.estudiantes[e2].prioridad(a), e2)

    return sorted(estado.inscritos[g], key=clave)[:CANDIDATOS_EXPULSION]


def _puede_tras_soltar(estado: Estado, e: str, soltar: str, tomar: str) -> bool:
    """¿e podría tomar `tomar` si suelta `soltar`? (sin mirar el cupo de `tomar`)"""
    inst = estado.inst
    F = inst.secciones[tomar].franjas
    return not (F & (estado.ocupadas[e] - inst.secciones[soltar].franjas)) and not (F & inst.estudiantes[e].no_disponibles)


def delta_intercambio(estado: Estado, e1: str, g1: str, e2: str, g2: str) -> float:
    """Cambio exacto de f si e1 (en g1) y e2 (en g2) intercambian de sección.

    Se calcula sin modificar la asignación, en O(k + |C_e|):
      f1 no cambia (es la misma asignatura).
      f2, f4: diferencia de afinidad y de franjas libres ocupadas.
      f3: amigos en la sección nueva menos amigos en la vieja; e1 y e2 nunca
          quedan juntos, así que si son amigos entre sí no se cuentan.
      f5: distancias con las demás clases de cada uno, antes y después.
    """
    inst, w = estado.inst, estado.w
    E1, E2 = inst.estudiantes[e1], inst.estudiantes[e2]
    S1, S2 = inst.secciones[g1], inst.secciones[g2]
    I1, I2 = estado.inscritos[g1], estado.inscritos[g2]

    def amigos_en(e, est, I):
        return len(est.companeros & I) + len(estado.seguidores[e] & I)

    entre_ellos = (e2 in E1.companeros) + (e1 in E2.companeros)
    d2 = (E1.afinidad_con(S2.profesor) - E1.afinidad_con(S1.profesor)
          + E2.afinidad_con(S1.profesor) - E2.afinidad_con(S2.profesor))
    d3 = (amigos_en(e1, E1, I2) - entre_ellos + amigos_en(e2, E2, I1) - entre_ellos
          - amigos_en(e1, E1, I1) - amigos_en(e2, E2, I2))
    d4 = (len(E1.libres & S2.franjas) - len(E1.libres & S1.franjas)
          + len(E2.libres & S1.franjas) - len(E2.libres & S2.franjas))
    d5 = _cambio_f5(estado, e1, g1, g2) + _cambio_f5(estado, e2, g2, g1)
    return w[2] * d2 + w[3] * d3 - w[4] * d4 - w[5] * d5


def _cambio_f5(estado: Estado, e: str, viejo: str, nuevo: str) -> float:
    inst = estado.inst
    sv, sn = inst.secciones[viejo].salon, inst.secciones[nuevo].salon
    total = 0.0
    for g in estado.secciones_de[e]:
        if g == viejo:
            continue
        s = inst.secciones[g].salon
        total += (inst.distancia(sn, s) * (estado.seguidas(nuevo, g) + estado.seguidas(g, nuevo))
                  - inst.distancia(sv, s) * (estado.seguidas(viejo, g) + estado.seguidas(g, viejo)))
    return total


def _mov_intercambiar(estado: Estado, s: Sucios, limite_tiempo: float) -> int:
    hechos = 0
    inst = estado.inst
    for a, secs in inst.secciones_por_asignatura.items():
        if time.perf_counter() > limite_tiempo:
            break
        if not s.revisar(None, a):
            continue
        for i, g1 in enumerate(secs):
            for g2 in secs[i + 1:]:
                # Solo hace falta intercambiar si ninguno de los dos puede moverse solo (ambas llenas).
                if (len(estado.inscritos[g1]) < inst.secciones[g1].cupo
                        or len(estado.inscritos[g2]) < inst.secciones[g2].cupo):
                    continue
                for e1 in sorted(estado.inscritos[g1]):
                    if not _puede_tras_soltar(estado, e1, g1, g2):
                        continue
                    for e2 in sorted(estado.inscritos[g2]):
                        if e1 == e2 or not _puede_tras_soltar(estado, e2, g2, g1):
                            continue
                        if delta_intercambio(estado, e1, g1, e2, g2) > EPS:
                            estado.retirar(e1, g1)
                            estado.retirar(e2, g2)
                            estado.inscribir(e1, g2)
                            estado.inscribir(e2, g1)
                            s.marcar([("", e1, g1), ("", e2, g2)])
                            hechos += 1
                            break          # e1 ya cambió de sección; seguir con el siguiente
    return hechos


def busqueda_local(estado: Estado, max_pasadas: int = 100, tiempo_max: float = 60.0) -> EstadisticasBusqueda:
    stats = EstadisticasBusqueda()
    limite = time.perf_counter() + tiempo_max
    sucios = Sucios(estado)
    completa = True
    stats.f_por_pasada.append(estado.f)
    while stats.pasadas < max_pasadas and time.perf_counter() < limite:
        stats.pasadas += 1
        sucios.iniciar_pasada(completa)
        i = _mov_insertar(estado, sucios)
        c = _mov_cambiar(estado, sucios)
        x = _mov_expulsar(estado, sucios, limite)
        s = _mov_intercambiar(estado, sucios, limite)
        stats.insertar += i
        stats.cambiar += c
        stats.expulsar += x
        stats.intercambiar += s
        stats.f_por_pasada.append(estado.f)
        if i + c + x + s > 0:
            completa = False
        elif completa:
            stats.optimo_local = True     # una pasada completa sin mejoras: óptimo local
            break
        else:
            completa = True               # confirmar con una pasada completa
    return stats


# ----------------------------------------------------------------------------
# Algoritmo completo
# ----------------------------------------------------------------------------

@dataclass
class Resultado:
    asignacion: Asignacion
    objetivo: Objetivo
    f_voraz: float
    tiempo_voraz: float
    tiempo_busqueda: float
    busqueda: EstadisticasBusqueda | None

    @property
    def tiempo(self) -> float:
        return self.tiempo_voraz + self.tiempo_busqueda


def resolver(inst: Instancia, con_busqueda: bool = True, max_pasadas: int = 100,
             tiempo_max: float = 60.0) -> Resultado:
    t0 = time.perf_counter()
    estado = voraz(inst)
    t1 = time.perf_counter()
    f_voraz = estado.f
    stats = busqueda_local(estado, max_pasadas, tiempo_max) if con_busqueda else None
    t2 = time.perf_counter()
    x = estado.asignacion()
    return Resultado(
        asignacion=x,
        objetivo=calcular_objetivo(inst, x),     # f recalculada desde cero (sin error acumulado)
        f_voraz=f_voraz,
        tiempo_voraz=t1 - t0,
        tiempo_busqueda=t2 - t1,
        busqueda=stats,
    )
