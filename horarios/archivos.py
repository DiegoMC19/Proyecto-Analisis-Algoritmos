"""Lectura y escritura de los archivos JSON (instancia, salida, salida esperada)."""

from __future__ import annotations

import json
from pathlib import Path

from .modelo import Instancia, instancia_desde_dict
from .validador import validar_datos


class InstanciaInvalida(Exception):
    def __init__(self, ruta, errores: list[str]):
        self.errores = errores
        detalle = "\n  - ".join(errores[:20])
        extra = f"\n  ... y {len(errores) - 20} errores más" if len(errores) > 20 else ""
        super().__init__(f"La instancia {ruta} no es válida:\n  - {detalle}{extra}")


def leer_json(ruta) -> dict:
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar_json(ruta, datos: dict, indentar: bool = True) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        if indentar:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        else:
            json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def cargar_instancia(ruta, validar: bool = True) -> Instancia:
    """Lee un archivo de instancia, lo valida y construye el modelo."""
    datos = leer_json(ruta)
    if validar:
        errores = validar_datos(datos)
        if errores:
            raise InstanciaInvalida(ruta, errores)
    return instancia_desde_dict(datos)
