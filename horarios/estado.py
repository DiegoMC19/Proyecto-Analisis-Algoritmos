"""Asignación parcial con la función objetivo mantenida de forma incremental.

La fuerza bruta y los algoritmos agregan y quitan pares (e, g) muchas veces.
Recalcular f desde cero cuesta O(|X|) cada vez; aquí cada cambio cuesta
O(k_e + |C_e| + |F_g|), con k_e el número de secciones que ya tiene e.

Cambio en cada criterio al inscribir a e en g (si la inscripción es válida):
    f1 += pi_e(a_g)
    f2 += phi_e(p_g)
    f3 += |C_e ∩ inscritos(g)| + |{e' ∈ inscritos(g) : e ∈ C_e'}|
    f4 += |L_e ∩ F_g|            (F_g no se cruza con las otras clases de e)
    f5 += sum_{g' ∈ G_X(e)} delta(s_g, s_g') * (seguidas(g, g') + seguidas(g', g))

Las fórmulas suponen que la asignación siempre es válida, por eso solo se
debe llamar a inscribir() cuando puede_inscribir() es verdadero.
"""

from __future__ import annotations

from .modelo import Asignacion, Instancia


class Estado:
    def __init__(self, inst: Instancia):
        self.inst = inst
        self.w = [0.0] + [inst.peso(i) for i in range(1, 6)]           # w[1..5]
        self.secciones_de: dict[str, list[str]] = {e: [] for e in inst.estudiantes}   # G_X(e)
        self.inscritos: dict[str, set[str]] = {g: set() for g in inst.secciones}
        self.asignatura_de: dict[str, dict[str, str]] = {e: {} for e in inst.estudiantes}  # e -> {a: g}
        self.ocupadas: dict[str, set] = {e: set() for e in inst.estudiantes}           # O_X(e)
        # seguidores[e] = {e' : e ∈ C_e'} (aristas al revés), para f3
        self.seguidores: dict[str, set[str]] = {e: set() for e in inst.estudiantes}
        for e in inst.estudiantes.values():
            for c in e.companeros:
                self.seguidores[c].add(e.id)
        self._seguidas: dict[tuple[str, str], int] = {}
        self.f_parcial = [0.0] * 6                                      # f1..f5 en f_parcial[1..5]

    # ------------------------------------------------------------------
    @property
    def f(self) -> float:
        w, c = self.w, self.f_parcial
        return w[1] * c[1] + w[2] * c[2] + w[3] * c[3] - w[4] * c[4] - w[5] * c[5]

    def asignacion(self) -> Asignacion:
        return [(e, g) for e, gs in self.secciones_de.items() for g in gs]

    def seguidas(self, g: str, g2: str) -> int:
        """|{(d, b) ∈ F_g : (d, b+1) ∈ F_g'}|, guardado en caché."""
        clave = (g, g2)
        if clave not in self._seguidas:
            F2 = self.inst.secciones[g2].franjas
            self._seguidas[clave] = sum(1 for d, b in self.inst.secciones[g].franjas if (d, b + 1) in F2)
        return self._seguidas[clave]

    # ------------------------------------------------------------------
    def puede_inscribir(self, e_id: str, g_id: str) -> bool:
        """¿Agregar (e, g) mantiene las restricciones (1)-(4)?"""
        e = self.inst.estudiantes[e_id]
        g = self.inst.secciones[g_id]
        return (g.asignatura in e.solicitudes                         # (1)
                and g.asignatura not in self.asignatura_de[e_id]      # (2) no repetir asignatura
                and not (g.franjas & self.ocupadas[e_id])             # (2) sin cruces
                and not (g.franjas & e.no_disponibles)                # (3)
                and len(self.inscritos[g_id]) < g.cupo)               # (4)

    def cambio(self, e_id: str, g_id: str) -> list[float]:
        """Cambio de [_, f1, f2, f3, f4, f5] si se inscribe e en g (e todavía no está en g)."""
        e = self.inst.estudiantes[e_id]
        g = self.inst.secciones[g_id]
        alumnos = self.inscritos[g_id]
        d5 = 0.0
        for g2 in self.secciones_de[e_id]:
            veces = self.seguidas(g_id, g2) + self.seguidas(g2, g_id)
            if veces:
                d5 += self.inst.distancia(g.salon, self.inst.secciones[g2].salon) * veces
        return [0.0,
                e.prioridad(g.asignatura),
                e.afinidad_con(g.profesor),
                len(e.companeros & alumnos) + len(self.seguidores[e_id] & alumnos),
                len(e.libres & g.franjas),
                d5]

    def ganancia(self, e_id: str, g_id: str) -> float:
        """Cuánto aumenta f si se inscribe e en g."""
        c, w = self.cambio(e_id, g_id), self.w
        return w[1] * c[1] + w[2] * c[2] + w[3] * c[3] - w[4] * c[4] - w[5] * c[5]

    def inscribir(self, e_id: str, g_id: str) -> None:
        c = self.cambio(e_id, g_id)
        for i in range(1, 6):
            self.f_parcial[i] += c[i]
        g = self.inst.secciones[g_id]
        self.secciones_de[e_id].append(g_id)
        self.inscritos[g_id].add(e_id)
        self.asignatura_de[e_id][g.asignatura] = g_id
        self.ocupadas[e_id] |= g.franjas

    def retirar(self, e_id: str, g_id: str) -> None:
        g = self.inst.secciones[g_id]
        self.secciones_de[e_id].remove(g_id)
        self.inscritos[g_id].discard(e_id)
        del self.asignatura_de[e_id][g.asignatura]
        self.ocupadas[e_id] -= g.franjas
        c = self.cambio(e_id, g_id)          # lo que aportaba (calculado ya sin el par)
        for i in range(1, 6):
            self.f_parcial[i] -= c[i]
