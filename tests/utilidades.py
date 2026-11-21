import copy
from pathlib import Path

from horarios.archivos import leer_json

RAIZ = Path(__file__).resolve().parent.parent
RUTA_EJEMPLO = RAIZ / "datos" / "instancias" / "ejemplo.json"
_EJEMPLO = leer_json(RUTA_EJEMPLO)


def ejemplo() -> dict:
    """Copia del JSON de la instancia de ejemplo (Código 1), para modificarla en cada prueba."""
    return copy.deepcopy(_EJEMPLO)


def estudiante(datos: dict, id_: str) -> dict:
    return next(e for e in datos["estudiantes"] if e["id"] == id_)


def seccion(datos: dict, id_: str) -> dict:
    return next(g for g in datos["secciones"] if g["id"] == id_)
