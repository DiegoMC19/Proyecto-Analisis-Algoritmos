"""Generador de instancias aleatorias. Con la misma semilla se obtiene la misma instancia."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import asdict, dataclass, replace

VERSION = "1.0"
DIAS_SEMANA = ["LU", "MA", "MI", "JU", "VI", "SA"]


@dataclass
class Parametros:
    estudiantes: int = 100
    semilla: int = 42
    # Tamaño (None = se calcula a partir de los demás valores)
    asignaturas: int | None = None        # estudiantes // 15 + 10
    profesores: int | None = None         # ceil(secciones / 3)
    salones: int | None = None            # ceil(secciones / 8)
    edificios: int | None = None          # ceil(salones / 8)
    secciones_por_asignatura: tuple[int, int] = (1, 4)
    solicitudes_por_estudiante: tuple[int, int] = (3, 6)
    # Semana
    dias: int = 5
    bloques: int = 12                     # por ejemplo, de 7:00 a 19:00 en bloques de 1 hora
    # Dificultad
    holgura: float = 0.9                  # cupo total / demanda de cada asignatura
    popularidad: float = 0.8              # exponente de Zipf (0 = todas igual de populares)
    # Campus
    lado_campus: float = 500.0            # metros
    distancia_interna: float = 20.0       # metros entre dos salones del mismo edificio
    # Estudiantes
    semestres: int = 10
    max_companeros: int = 4
    prob_companero_mismo_semestre: float = 0.8
    profesores_conocidos: tuple[int, int] = (2, 8)
    prob_profesor_de_sus_asignaturas: float = 0.7
    prob_trabaja: float = 0.15
    prob_preferencia_libre: float = 0.5
    # Función objetivo
    pesos: tuple[float, float, float, float, float] = (10, 2, 1, 1, 0.01)


def _ids(prefijo: str, n: int, minimo: int = 2) -> list[str]:
    ancho = max(minimo, len(str(n)))
    return [f"{prefijo}{i:0{ancho}d}" for i in range(1, n + 1)]


def generar(p: Parametros) -> dict:
    """Genera una instancia con el formato del archivo de instancia (Código 1)."""
    if p.dias < 1 or p.dias > len(DIAS_SEMANA):
        raise ValueError(f"dias debe estar entre 1 y {len(DIAS_SEMANA)}")
    if p.bloques < 2:
        raise ValueError("se necesitan al menos 2 bloques por día")

    rng = random.Random(p.semilla)
    D = DIAS_SEMANA[:p.dias]
    h = p.bloques
    orden_dia = {d: i for i, d in enumerate(D)}

    def ordenar(franjas) -> list[list]:
        return [[d, b] for d, b in sorted(franjas, key=lambda f: (orden_dia[f[0]], f[1]))]

    # 1. Asignaturas y número de secciones
    m = p.asignaturas or p.estudiantes // 15 + 10
    A = _ids("A", m)
    semestre_asig = {a: rng.randint(1, p.semestres) for a in A}
    n_secciones = {a: rng.randint(*p.secciones_por_asignatura) for a in A}
    k = sum(n_secciones.values())

    n_salones = p.salones or max(2, math.ceil(k / 8))
    n_edificios = p.edificios or max(2, math.ceil(n_salones / 8))
    n_profesores = p.profesores or max(2, math.ceil(k / 3))
    p = replace(p, asignaturas=m, salones=n_salones, edificios=n_edificios, profesores=n_profesores)

    # 2. Edificios, salones y distancias
    B = _ids("B", n_edificios, minimo=1)
    coords = {b: (round(rng.uniform(0, p.lado_campus), 1), round(rng.uniform(0, p.lado_campus), 1)) for b in B}
    S = _ids("S", n_salones)
    # Los primeros salones cubren todos los edificios; el resto se reparte al azar.
    edificio_de = {s: (B[i] if i < len(B) else rng.choice(B)) for i, s in enumerate(S)}

    distancias = []
    for s1 in S:
        fila = []
        for s2 in S:
            if s1 == s2:
                fila.append(0.0)
            elif edificio_de[s1] == edificio_de[s2]:
                fila.append(p.distancia_interna)
            else:
                fila.append(round(math.dist(coords[edificio_de[s1]], coords[edificio_de[s2]]), 1))
        distancias.append(fila)

    # 3. Horarios: salón y profesor libres en las franjas de cada sección
    P = _ids("P", n_profesores)
    if len(D) >= 3:
        grupos_dias = [(D[i], D[i + 2]) for i in range(len(D) - 2)]   # LU-MI, MA-JU, MI-VI
    else:
        grupos_dias = [(d,) for d in D]
    patrones = [frozenset((d, b + j) for d in grupo for j in (0, 1))
                for grupo in grupos_dias for b in range(1, h, 2)]       # bloques 1-2, 3-4, ...

    ocupado_salon = {s: set() for s in S}
    ocupado_prof = {q: set() for q in P}
    G = iter(_ids("G", k, minimo=3))
    secciones = []
    for a in A:
        usados = set()
        for _ in range(n_secciones[a]):
            candidatos = patrones[:]
            rng.shuffle(candidatos)
            # Primero los horarios que no usa otra sección de la misma asignatura.
            candidatos.sort(key=lambda pat: pat in usados)
            for pat in candidatos:
                salones_libres = [s for s in S if not ocupado_salon[s] & pat]
                profes_libres = [q for q in P if not ocupado_prof[q] & pat]
                if salones_libres and profes_libres:
                    s, q = rng.choice(salones_libres), rng.choice(profes_libres)
                    ocupado_salon[s] |= pat
                    ocupado_prof[q] |= pat
                    usados.add(pat)
                    secciones.append({"id": next(G), "asignatura": a, "profesor": q, "salon": s,
                                      "franjas": ordenar(pat), "cupo": None})
                    break
            else:
                raise ValueError("No hay salones o profesores libres para todas las secciones; "
                                 "aumente 'salones' o 'profesores'.")

    secciones_de_asig = defaultdict(list)
    for g in secciones:
        secciones_de_asig[g["asignatura"]].append(g)

    # 4. Estudiantes y solicitudes
    n = p.estudiantes
    E = _ids("E", n, minimo=4)
    semestre_est = {e: rng.randint(1, p.semestres) for e in E}

    rangos = list(range(m))
    rng.shuffle(rangos)
    popularidad = {a: 1 / (r + 1) ** p.popularidad for a, r in zip(A, rangos)}

    solicitudes = {}
    demanda = dict.fromkeys(A, 0)
    for e in E:
        q = min(rng.randint(*p.solicitudes_por_estudiante), m)
        # Elegir q asignaturas al azar según su popularidad, sin repetir.
        llaves = {}
        for a in A:
            w = popularidad[a] * (4 if semestre_asig[a] == semestre_est[e] else 1)
            llaves[a] = rng.random() ** (1 / w)
        elegidas = sorted(A, key=llaves.__getitem__, reverse=True)[:q]
        solicitudes[e] = [{"asignatura": a, "prioridad": rng.randint(1, 5)} for a in elegidas]
        for a in elegidas:
            demanda[a] += 1

    # 5. Cupos según la demanda
    for a in A:
        base = demanda[a] / n_secciones[a] * p.holgura
        for g in secciones_de_asig[a]:
            g["cupo"] = max(1, round(base * rng.uniform(0.8, 1.2)))

    # 6. Compañeros
    por_semestre = defaultdict(list)
    for e in E:
        por_semestre[semestre_est[e]].append(e)
    companeros = {e: set() for e in E}
    for e in E:
        for _ in range(rng.randint(0, p.max_companeros)):
            grupo = por_semestre[semestre_est[e]] if rng.random() < p.prob_companero_mismo_semestre else E
            c = rng.choice(grupo)
            if c != e:
                companeros[e].add(c)
                companeros[c].add(e)

    # 7. Afinidad con los profesores
    reputacion = {q: rng.uniform(-2, 2) for q in P}
    afinidad = {}
    for e in E:
        relevantes = sorted({g["profesor"] for s in solicitudes[e] for g in secciones_de_asig[s["asignatura"]]})
        conocidos = {}
        for _ in range(rng.randint(*p.profesores_conocidos)):
            grupo = relevantes if relevantes and rng.random() < p.prob_profesor_de_sus_asignaturas else P
            q = rng.choice(grupo)
            if q not in conocidos:
                conocidos[q] = max(-2, min(2, round(reputacion[q] + rng.gauss(0, 0.8))))
        afinidad[e] = {q: v for q, v in sorted(conocidos.items()) if v != 0}

    # 8. Franjas no disponibles y franjas que se prefieren libres
    mitad = h // 2
    mananas = {(d, b) for d in D for b in range(1, mitad + 1)}
    tardes = {(d, b) for d in D for b in range(mitad + 1, h + 1)}
    preferencias = [
        {(D[-1], b) for b in range(1, h + 1)},            # último día libre (viernes libre)
        tardes,                                           # tardes libres
        {(d, b) for d in D for b in (1, 2)},              # no madrugar
        {(d, b) for d in D for b in (mitad, mitad + 1)},  # hora de almuerzo libre
    ]

    estudiantes = []
    for e in E:
        N = rng.choice([mananas, tardes]) if rng.random() < p.prob_trabaja else set()
        L = (rng.choice(preferencias) - N) if rng.random() < p.prob_preferencia_libre else set()
        estudiantes.append({
            "id": e,
            "semestre": semestre_est[e],
            "solicitudes": solicitudes[e],
            "no_disponibles": ordenar(N),
            "libres": ordenar(L),
            "companeros": sorted(companeros[e]),
            "afinidad": afinidad[e],
        })

    return {
        "meta": {"version": VERSION, "semilla": p.semilla, "parametros": asdict(p)},
        "franjas": {"dias": D, "bloques": h},
        "pesos": {f"w{i}": w for i, w in enumerate(p.pesos, start=1)},
        "asignaturas": [{"id": a, "semestre": semestre_asig[a]} for a in A],
        "profesores": [{"id": q} for q in P],
        "edificios": [{"id": b, "x": coords[b][0], "y": coords[b][1]} for b in B],
        "salones": [{"id": s, "edificio": edificio_de[s]} for s in S],
        "distancias": distancias,
        "secciones": secciones,
        "estudiantes": estudiantes,
    }


def nombre_instancia(p: Parametros) -> str:
    return f"inst_n{p.estudiantes}_s{p.semilla}.json"
