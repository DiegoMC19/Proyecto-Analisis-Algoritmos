"""Reglas de validez de una instancia (Sección 4.2 del documento).

Trabaja sobre el JSON leído (un dict) y no sobre el modelo, para poder
reportar todos los errores en lugar de fallar con el primero.

    1. ids únicos y referencias que existen.
    2. distancias: matriz |S| x |S|, no negativa, diagonal 0 y simétrica.
    3. franjas con día en D y bloque entre 1 y h.
    4. secciones con al menos una franja, sin repetir, y cupo entero >= 1.
    5. solicitudes sin asignaturas repetidas y prioridades entre 1 y 5.
    6. L_e ∩ N_e = ∅ y e ∉ C_e.
    7. afinidades entre -2 y 2 y pesos >= 0.
"""

from __future__ import annotations

CAMPOS_INSTANCIA = ["franjas", "pesos", "asignaturas", "profesores",
                    "salones", "distancias", "secciones", "estudiantes"]
CAMPOS_ESTUDIANTE = ["solicitudes", "no_disponibles", "libres", "companeros", "afinidad"]
TOLERANCIA = 1e-9


def es_entero(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def es_numero(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validar_datos(datos: dict) -> list[str]:
    """Devuelve la lista de errores de la instancia (vacía si es válida)."""
    if not isinstance(datos, dict):
        return ["la instancia debe ser un objeto JSON"]
    faltan = [c for c in CAMPOS_INSTANCIA if c not in datos]
    if faltan:
        return [f"falta el campo '{c}'" for c in faltan]

    errores: list[str] = []

    # --- Franjas F = D x H (regla 3) ---
    dias = datos["franjas"].get("dias") if isinstance(datos["franjas"], dict) else None
    h = datos["franjas"].get("bloques") if isinstance(datos["franjas"], dict) else None
    if not isinstance(dias, list) or not dias or len(set(map(str, dias))) != len(dias):
        errores.append("franjas.dias debe ser una lista no vacía de días sin repetir")
        dias = []
    if not es_entero(h) or h < 1:
        errores.append("franjas.bloques debe ser un entero >= 1")
        h = 0
    dias_validos = set(dias)

    def revisar_franjas(lista, contexto: str, sin_repetir: bool = False) -> set:
        """Revisa una lista de franjas y devuelve las válidas como tuplas."""
        if not isinstance(lista, list):
            errores.append(f"{contexto}: debe ser una lista de franjas")
            return set()
        validas = set()
        for f in lista:
            if not (isinstance(f, list) and len(f) == 2 and f[0] in dias_validos
                    and es_entero(f[1]) and 1 <= f[1] <= h):
                errores.append(f"{contexto}: franja inválida {f}")
                continue
            if sin_repetir and tuple(f) in validas:
                errores.append(f"{contexto}: franja repetida {f}")
            validas.add(tuple(f))
        return validas

    # --- ids únicos (regla 1) ---
    def ids_unicos(lista, nombre: str) -> set[str]:
        if not isinstance(lista, list):
            errores.append(f"{nombre} debe ser una lista")
            return set()
        vistos: set[str] = set()
        for i, x in enumerate(lista):
            if not isinstance(x, dict) or not isinstance(x.get("id"), str):
                errores.append(f"{nombre}[{i}] no tiene un id de texto")
                continue
            if x["id"] in vistos:
                errores.append(f"{nombre}: id repetido '{x['id']}'")
            vistos.add(x["id"])
        return vistos

    A = ids_unicos(datos["asignaturas"], "asignaturas")
    P = ids_unicos(datos["profesores"], "profesores")
    S = ids_unicos(datos["salones"], "salones")
    ids_unicos(datos["secciones"], "secciones")
    E = ids_unicos(datos["estudiantes"], "estudiantes")

    # Edificios: campo auxiliar, solo se revisa si viene.
    if "edificios" in datos:
        B = ids_unicos(datos["edificios"], "edificios")
        for s in datos["salones"] if isinstance(datos["salones"], list) else []:
            if isinstance(s, dict) and "edificio" in s and s["edificio"] not in B:
                errores.append(f"salon {s.get('id')}: el edificio '{s['edificio']}' no existe")

    # --- Distancias (regla 2) ---
    n_s = len(datos["salones"]) if isinstance(datos["salones"], list) else 0
    M = datos["distancias"]
    if (not isinstance(M, list) or len(M) != n_s
            or any(not isinstance(fila, list) or len(fila) != n_s for fila in M)):
        errores.append(f"distancias debe ser una matriz de {n_s} x {n_s} (una fila y columna por salón)")
    else:
        numerica = True
        for i in range(n_s):
            for j in range(n_s):
                v = M[i][j]
                if not es_numero(v) or v < 0:
                    errores.append(f"distancias[{i}][{j}] = {v} debe ser un número >= 0")
                    numerica = False
        if numerica:
            for i in range(n_s):
                if M[i][i] != 0:
                    errores.append(f"distancias[{i}][{i}] debe ser 0")
                for j in range(i + 1, n_s):
                    if abs(M[i][j] - M[j][i]) > TOLERANCIA:
                        errores.append(f"distancias no es simétrica en [{i}][{j}] y [{j}][{i}]")

    # --- Secciones (reglas 1, 3 y 4) ---
    for g in datos["secciones"] if isinstance(datos["secciones"], list) else []:
        if not isinstance(g, dict):
            continue
        ctx = f"seccion {g.get('id')}"
        for campo, existentes in (("asignatura", A), ("profesor", P), ("salon", S)):
            if g.get(campo) not in existentes:
                errores.append(f"{ctx}: {campo} '{g.get(campo)}' no existe")
        if not isinstance(g.get("franjas"), list) or not g["franjas"]:
            errores.append(f"{ctx}: debe tener al menos una franja")
        else:
            revisar_franjas(g["franjas"], ctx, sin_repetir=True)
        if not es_entero(g.get("cupo")) or g["cupo"] < 1:
            errores.append(f"{ctx}: el cupo debe ser un entero >= 1")

    # --- Estudiantes (reglas 1, 3, 5, 6 y 7) ---
    for e in datos["estudiantes"] if isinstance(datos["estudiantes"], list) else []:
        if not isinstance(e, dict):
            continue
        ctx = f"estudiante {e.get('id')}"
        faltan = [c for c in CAMPOS_ESTUDIANTE if c not in e]
        if faltan:
            errores.append(f"{ctx}: faltan los campos {faltan}")
            continue

        # Solicitudes: R_e y pi_e (regla 5)
        if not isinstance(e["solicitudes"], list):
            errores.append(f"{ctx}: solicitudes debe ser una lista")
        else:
            pedidas = set()
            for s in e["solicitudes"]:
                if not isinstance(s, dict):
                    errores.append(f"{ctx}: solicitud inválida {s}")
                    continue
                a = s.get("asignatura")
                if a not in A:
                    errores.append(f"{ctx}: la asignatura '{a}' no existe")
                elif a in pedidas:
                    errores.append(f"{ctx}: pide dos veces la asignatura '{a}'")
                pedidas.add(a)
                if not es_entero(s.get("prioridad")) or not 1 <= s["prioridad"] <= 5:
                    errores.append(f"{ctx}: la prioridad de '{a}' debe ser un entero entre 1 y 5")

        # N_e y L_e (reglas 3 y 6)
        N = revisar_franjas(e["no_disponibles"], f"{ctx} (no_disponibles)")
        L = revisar_franjas(e["libres"], f"{ctx} (libres)")
        if N & L:
            errores.append(f"{ctx}: franjas en libres y no_disponibles a la vez {sorted(N & L)}")

        # C_e (reglas 1 y 6)
        if not isinstance(e["companeros"], list):
            errores.append(f"{ctx}: companeros debe ser una lista")
        else:
            for c in e["companeros"]:
                if c == e.get("id"):
                    errores.append(f"{ctx}: no puede ser compañero de sí mismo")
                elif c not in E:
                    errores.append(f"{ctx}: el compañero '{c}' no existe")

        # phi_e (reglas 1 y 7)
        if not isinstance(e["afinidad"], dict):
            errores.append(f"{ctx}: afinidad debe ser un objeto {{profesor: valor}}")
        else:
            for p, v in e["afinidad"].items():
                if p not in P:
                    errores.append(f"{ctx}: el profesor '{p}' de la afinidad no existe")
                if not es_entero(v) or not -2 <= v <= 2:
                    errores.append(f"{ctx}: la afinidad con '{p}' debe ser un entero entre -2 y 2")

    # --- Pesos (regla 7) ---
    pesos = datos["pesos"]
    for i in range(1, 6):
        w = pesos.get(f"w{i}") if isinstance(pesos, dict) else None
        if not es_numero(w) or w < 0:
            errores.append(f"pesos.w{i} debe ser un número >= 0")

    return errores
