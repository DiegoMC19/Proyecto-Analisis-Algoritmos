"""Los 6 casos de prueba hechos a mano."""

from __future__ import annotations

from .generador import VERSION

DIAS = ["LU", "MA", "MI", "JU", "VI"]
PESOS = {"w1": 10, "w2": 2, "w3": 1, "w4": 1, "w5": 0.01}


def _franjas(*pares):
    return [[d, b] for d, b in pares]


def _seccion(id_, asignatura, profesor, salon, franjas, cupo=5):
    return {"id": id_, "asignatura": asignatura, "profesor": profesor, "salon": salon,
            "franjas": franjas, "cupo": cupo}


def _estudiante(id_, solicitudes: dict, no_disponibles=(), libres=(), companeros=(), afinidad=None):
    return {"id": id_,
            "solicitudes": [{"asignatura": a, "prioridad": p} for a, p in solicitudes.items()],
            "no_disponibles": list(no_disponibles), "libres": list(libres),
            "companeros": list(companeros), "afinidad": afinidad or {}}


def _instancia(numero, asignaturas, profesores, salones, distancias, secciones, estudiantes,
               edificios=None):
    d = {
        "meta": {"version": VERSION, "caso": numero},
        "franjas": {"dias": DIAS, "bloques": 6},
        "pesos": PESOS,
        "asignaturas": [{"id": a} for a in asignaturas],
        "profesores": [{"id": p} for p in profesores],
    }
    if edificios:
        d["edificios"] = edificios
        d["salones"] = [{"id": s, "edificio": b} for s, b in salones]
    else:
        d["salones"] = [{"id": s} for s in salones]
    d.update({"distancias": distancias, "secciones": secciones, "estudiantes": estudiantes})
    return d


LU12 = _franjas(("LU", 1), ("LU", 2))


def casos() -> list[dict]:
    """Lista de casos: {numero, descripcion, instancia, esperada}."""
    return [
        {
            "numero": 1,
            "descripcion": "Dos asignaturas cuyas únicas secciones se cruzan, con prioridades 4 y 2: "
                           "solo queda inscrito en la de prioridad 4.",
            "instancia": _instancia(
                1, ["A01", "A02"], ["P01", "P02"], ["S01", "S02"], [[0, 20], [20, 0]],
                [_seccion("G001", "A01", "P01", "S01", LU12),
                 _seccion("G002", "A02", "P02", "S02", _franjas(("LU", 2), ("LU", 3)))],
                [_estudiante("E0001", {"A01": 4, "A02": 2})]),
            "esperada": [("E0001", "G001")],
        },
        {
            "numero": 2,
            "descripcion": "Una sección con cupo 1 que piden dos estudiantes con prioridades 5 y 2: "
                           "el cupo queda para el de prioridad 5.",
            "instancia": _instancia(
                2, ["A01"], ["P01"], ["S01"], [[0]],
                [_seccion("G001", "A01", "P01", "S01", LU12, cupo=1)],
                [_estudiante("E0001", {"A01": 5}), _estudiante("E0002", {"A01": 2})]),
            "esperada": [("E0001", "G001")],
        },
        {
            "numero": 3,
            "descripcion": "La única sección de la asignatura es en una franja en la que el estudiante "
                           "no puede: no se inscribe.",
            "instancia": _instancia(
                3, ["A01"], ["P01"], ["S01"], [[0]],
                [_seccion("G001", "A01", "P01", "S01", LU12)],
                [_estudiante("E0001", {"A01": 3}, no_disponibles=_franjas(("LU", 1)))]),
            "esperada": [],
        },
        {
            "numero": 4,
            "descripcion": "Dos amigos piden la misma asignatura y hay dos secciones iguales salvo el "
                           "horario. E0001 quiere el martes libre, así que prefiere G001; a E0002 le da "
                           "igual, pero por su amigo queda también en G001.",
            "instancia": _instancia(
                4, ["A01"], ["P01"], ["S01"], [[0]],
                [_seccion("G001", "A01", "P01", "S01", LU12),
                 _seccion("G002", "A01", "P01", "S01", _franjas(("MA", 1), ("MA", 2)))],
                [_estudiante("E0001", {"A01": 3}, libres=_franjas(("MA", 1), ("MA", 2)),
                             companeros=["E0002"]),
                 _estudiante("E0002", {"A01": 3}, companeros=["E0001"])]),
            "esperada": [("E0001", "G001"), ("E0002", "G001")],
        },
        {
            "numero": 5,
            "descripcion": "Dos secciones iguales de la misma asignatura salvo el profesor, con afinidad "
                           "2 y -2: queda en la de afinidad 2.",
            "instancia": _instancia(
                5, ["A01"], ["P01", "P02"], ["S01", "S02"], [[0, 20], [20, 0]],
                [_seccion("G001", "A01", "P01", "S01", LU12),
                 _seccion("G002", "A01", "P02", "S02", LU12)],
                [_estudiante("E0001", {"A01": 3}, afinidad={"P01": 2, "P02": -2})]),
            "esperada": [("E0001", "G001")],
        },
        {
            "numero": 6,
            "descripcion": "Después de una clase en el edificio B1, la siguiente asignatura tiene una "
                           "sección en B1 y otra en B2 a la misma hora: queda en la de B1.",
            "instancia": _instancia(
                6, ["A01", "A02"], ["P01", "P02", "P03"],
                [("S01", "B1"), ("S02", "B1"), ("S03", "B2")],
                [[0, 20, 300], [20, 0, 300], [300, 300, 0]],
                [_seccion("G001", "A01", "P01", "S01", _franjas(("LU", 1), ("LU", 2), ("MI", 1), ("MI", 2))),
                 _seccion("G002", "A02", "P02", "S02", _franjas(("LU", 3), ("LU", 4), ("MI", 3), ("MI", 4))),
                 _seccion("G003", "A02", "P03", "S03", _franjas(("LU", 3), ("LU", 4), ("MI", 3), ("MI", 4)))],
                [_estudiante("E0001", {"A01": 5, "A02": 3})],
                edificios=[{"id": "B1", "x": 0.0, "y": 0.0}, {"id": "B2", "x": 300.0, "y": 0.0}]),
            "esperada": [("E0001", "G001"), ("E0001", "G002")],
        },
    ]
