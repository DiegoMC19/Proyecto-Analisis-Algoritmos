# Resumen de experimentos

- Crecimiento empírico del tiempo (Voraz): ~ n^1.10
- Crecimiento empírico del tiempo (Voraz + búsqueda local): ~ n^1.56

## Calidad contra el óptimo

| n | instancias | espacio (mediana) | nodos FB (mediana) | tiempo FB (mediana) | óptimas voraz | óptimas voraz+BL | brecha voraz | brecha voraz+BL |
|---|---|---|---|---|---|---|---|---|
| 3 | 30 | 2,560 | 1,412 | 0.003 s | 14 | 23 | 1.75 % | 0.73 % |
| 4 | 30 | 27,216 | 8,576 | 0.017 s | 10 | 21 | 1.79 % | 0.68 % |
| 5 | 30 | 296,960 | 70,559 | 0.139 s | 10 | 22 | 2.77 % | 0.91 % |
| 6 | 9 | 2,654,208 | 633,242 | 1.346 s | 2 | 6 | 2.37 % | 0.77 % |

Total: voraz óptimo en 36/99, voraz+BL en 72/99; brecha máxima voraz 13.53 %, voraz+BL 10.39 %.

## Escalabilidad (promedio de las semillas)

| n | asignaturas | secciones | solicitudes | tiempo voraz | tiempo voraz+BL | inscritas voraz | inscritas voraz+BL | mejora de f por BL |
|---|---|---|---|---|---|---|---|---|
| 100 | 16 | 39 | 463 | 0.003 s | 0.13 s | 81.1 % | 83.7 % | +3.23 % |
| 250 | 26 | 72 | 1122 | 0.009 s | 0.44 s | 84.0 % | 86.7 % | +3.26 % |
| 500 | 43 | 115 | 2257 | 0.018 s | 1.20 s | 83.2 % | 86.5 % | +3.90 % |
| 1000 | 76 | 187 | 4503 | 0.040 s | 3.64 s | 83.5 % | 86.2 % | +3.62 % |
| 2500 | 176 | 428 | 11205 | 0.100 s | 18.18 s | 83.5 % | 86.2 % | +3.29 % |
| 5000 | 343 | 871 | 22499 | 0.239 s | 51.60 s | 83.2 % | 86.2 % | +3.48 % |

## Competencia por cupos

| holgura | inscritas voraz | inscritas voraz+BL | prioridad 5 inscritas (voraz+BL) |
|---|---|---|---|
| 0.5 | 49.77 % | 49.77 % | 97.44 % |
| 0.7 | 69.53 % | 69.62 % | 97.44 % |
| 0.9 | 83.61 % | 86.06 % | 97.44 % |
| 1.1 | 89.61 % | 93.34 % | 97.44 % |
| 1.3 | 91.09 % | 94.24 % | 97.44 % |
| 1.5 | 91.33 % | 94.42 % | 97.44 % |
