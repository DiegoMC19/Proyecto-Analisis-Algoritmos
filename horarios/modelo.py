"""Modelo de datos del problema.

Cada clase corresponde a un elemento de las entradas del diseño:

    Franja      (d, b) in F = D x H
    Seccion     g = <a_g, p_g, s_g, F_g, c_g>
    Estudiante  e = <R_e, pi_e, N_e, L_e, C_e, phi_e>
    Instancia   todas las entradas juntas (F, A, P, S, delta, G, E, w)

Una asignación X es una lista de pares (id_estudiante, id_seccion).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Una franja es el par (día, bloque), por ejemplo ("LU", 1).
Franja = tuple[str, int]

# Una asignación X ⊆ E x G es una lista de pares (estudiante, sección).
Asignacion = list[tuple[str, str]]


@dataclass(frozen=True)
class Seccion:
    id: str
    asignatura: str               # a_g
    profesor: str                 # p_g
    salon: str                    # s_g
    franjas: frozenset[Franja]    # F_g
    cupo: int                     # c_g


@dataclass(frozen=True, eq=False)
class Estudiante:
    id: str
    solicitudes: dict[str, int]          # R_e (llaves) y pi_e (valores)
    no_disponibles: frozenset[Franja]    # N_e
    libres: frozenset[Franja]            # L_e
    companeros: frozenset[str]           # C_e
    afinidad: dict[str, int]             # phi_e, dispersa (lo que no está vale 0)
    semestre: int | None = None          # campo auxiliar, el algoritmo no lo usa

    def prioridad(self, asignatura: str) -> int:
        """pi_e(a). Vale 0 si la asignatura no está en R_e."""
        return self.solicitudes.get(asignatura, 0)

    def afinidad_con(self, profesor: str) -> int:
        """phi_e(p). Vale 0 si el profesor no aparece en el archivo."""
        return self.afinidad.get(profesor, 0)


@dataclass(eq=False)
class Instancia:
    dias: list[str]                       # D
    bloques: int                          # h, con H = {1, ..., h}
    pesos: dict[str, float]               # w1, ..., w5
    asignaturas: list[str]                # A
    profesores: list[str]                 # P
    salones: list[str]                    # S, en el orden de la matriz de distancias
    distancias: list[list[float]]         # delta
    secciones: dict[str, Seccion]         # G, por id
    estudiantes: dict[str, Estudiante]    # E, por id
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._indice_salon = {s: i for i, s in enumerate(self.salones)}
        # Índice auxiliar: secciones de cada asignatura (lo usará el algoritmo).
        self.secciones_por_asignatura: dict[str, list[str]] = {a: [] for a in self.asignaturas}
        for g in self.secciones.values():
            self.secciones_por_asignatura[g.asignatura].append(g.id)

    def distancia(self, s1: str, s2: str) -> float:
        """delta(s1, s2), consultada en O(1)."""
        return self.distancias[self._indice_salon[s1]][self._indice_salon[s2]]

    def peso(self, i: int) -> float:
        return self.pesos[f"w{i}"]


def _franjas(lista) -> frozenset[Franja]:
    return frozenset((d, b) for d, b in lista)


def instancia_desde_dict(datos: dict) -> Instancia:
    """Construye la instancia a partir del JSON ya leído.

    Supone que los datos ya pasaron por el validador.
    """
    secciones = {
        g["id"]: Seccion(
            id=g["id"],
            asignatura=g["asignatura"],
            profesor=g["profesor"],
            salon=g["salon"],
            franjas=_franjas(g["franjas"]),
            cupo=g["cupo"],
        )
        for g in datos["secciones"]
    }
    estudiantes = {
        e["id"]: Estudiante(
            id=e["id"],
            solicitudes={s["asignatura"]: s["prioridad"] for s in e["solicitudes"]},
            no_disponibles=_franjas(e["no_disponibles"]),
            libres=_franjas(e["libres"]),
            companeros=frozenset(e["companeros"]),
            afinidad=dict(e["afinidad"]),
            semestre=e.get("semestre"),
        )
        for e in datos["estudiantes"]
    }
    return Instancia(
        dias=list(datos["franjas"]["dias"]),
        bloques=datos["franjas"]["bloques"],
        pesos={f"w{i}": float(datos["pesos"][f"w{i}"]) for i in range(1, 6)},
        asignaturas=[a["id"] for a in datos["asignaturas"]],
        profesores=[p["id"] for p in datos["profesores"]],
        salones=[s["id"] for s in datos["salones"]],
        distancias=[[float(v) for v in fila] for fila in datos["distancias"]],
        secciones=secciones,
        estudiantes=estudiantes,
        meta=datos.get("meta", {}),
    )


def asignacion_desde_json(lista: list[dict]) -> Asignacion:
    """Convierte [{"estudiante": e, "seccion": g}, ...] en [(e, g), ...]."""
    return [(par["estudiante"], par["seccion"]) for par in lista]


def asignacion_a_json(asignacion: Asignacion) -> list[dict]:
    return [{"estudiante": e, "seccion": g} for e, g in asignacion]
