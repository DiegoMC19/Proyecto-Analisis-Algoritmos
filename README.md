# Asignación de horarios estudiantiles

Proyecto de Análisis de Algoritmos. Requiere Python 3.10 o superior. Solo `graficas.py`
usa una librería externa (`pip install matplotlib`).

## Estructura

```
horarios/            paquete principal
  modelo.py          clases Seccion, Estudiante, Instancia (entradas del diseño)
  validador.py       reglas de validez de una instancia (Sección 4.2)
  archivos.py        lectura/escritura de JSON
  verificador.py     restricciones (1)-(4), función objetivo f y comparación con la esperada
  generador.py       generador de instancias aleatorias con semilla (Sección 3)
  estado.py          asignación parcial con f actualizada en O(k_e + |C_e|) por cambio
  fuerza_bruta.py    óptimo exacto por backtracking (instancias pequeñas)
  casos.py           los 6 casos hechos a mano (Tabla 2)
  algoritmo.py       algoritmo principal: voraz por prioridad + búsqueda local
datos/instancias/    archivos de instancia
datos/esperadas/     salidas esperadas (mismo nombre que la instancia)
resultados/<alg>/    salidas de cada algoritmo
tests/               pruebas unitarias
generar.py           CLI: genera instancias
crear_casos.py       CLI: escribe los casos a mano y sus salidas esperadas
fuerza_bruta.py      CLI: calcula la salida esperada óptima de instancias pequeñas
resolver.py          CLI: ejecuta el algoritmo, guarda y verifica la salida
latex.txt            entrega 1 corregida (LaTeX)
latex_final.txt      documento final completo: diseño, estrategia de datos, algoritmo y resultados (LaTeX)
GUIA_SUSTENTACION.md guía para preparar la sustentación
experimentos.py      corre los experimentos (calidad, escalabilidad, competencia) -> CSV
graficas.py          gráficas PNG/PDF y resumen.md a partir de los CSV (requiere matplotlib)
validar.py           CLI: valida instancias
verificar.py         CLI: verifica una salida
```

## Comandos

```
python -m unittest discover -s tests -t .
python generar.py -n 100 1000 5000 --semilla 42
python generar.py -n 200 --holgura 0.6        # más competencia por los cupos
python generar.py -n 4 --semilla 1 --asignaturas 5 --solicitudes 2 3 --secciones 1 3   # instancia pequeña
python crear_casos.py
python fuerza_bruta.py datos/instancias/caso*.json datos/instancias/inst_n4_s1.json
python resolver.py datos/instancias/inst_n1000_s42.json
python resolver.py datos/instancias/inst_n1000_s42.json --solo-voraz
python experimentos.py            # ~10 min; --rapido para una versión corta
python graficas.py
python validar.py datos/instancias/ejemplo.json
python verificar.py datos/instancias/ejemplo.json resultados/manual/ejemplo.json --esperada datos/esperadas/ejemplo.json
```
