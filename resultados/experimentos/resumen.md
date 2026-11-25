# Resumen de experimentos

- Crecimiento empírico del tiempo (Voraz (prioridad)): ~ n^1.08
- Crecimiento empírico del tiempo (Voraz (3 criterios)): ~ n^1.09

## Calidad contra el óptimo

| n | instancias | espacio (mediana) | nodos sin cota | tiempo sin cota | nodos con cota | tiempo voraz+BT | óptimas voraz | óptimas 3 criterios | óptimas voraz+BT | brecha voraz | brecha 3 criterios | brecha voraz+BT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 30 | 2,560 | 1,412 | 0.005 s | 69 | 0.0006 s | 14 | 15 | 30 | 1.75 % | 1.52 % | 0.00 % |
| 4 | 30 | 27,216 | 8,576 | 0.022 s | 257 | 0.0011 s | 10 | 12 | 30 | 1.79 % | 1.19 % | 0.00 % |
| 5 | 30 | 296,960 | 70,559 | 0.174 s | 772 | 0.0032 s | 10 | 13 | 30 | 2.77 % | 1.96 % | 0.00 % |
| 6 | 9 | 2,654,208 | 633,242 | 1.638 s | 1,794 | 0.0067 s | 2 | 2 | 9 | 2.37 % | 2.37 % | 0.00 % |

Total: óptimo en 36/99 (voraz), 42/99 (3 criterios), 99/99 (voraz+BT); brecha máxima voraz 13.53 %, 3 criterios 13.53 %; backtracking completo en 99/99.

## Escalabilidad (promedio de las semillas)

| n | asignaturas | secciones | solicitudes | tiempo voraz | tiempo 3 criterios | inscritas | mejora por 3 criterios | mejora por backtracking | criterio ganador |
|---|---|---|---|---|---|---|---|---|---|
| 100 | 16 | 39 | 463 | 0.004 s | 0.012 s | 82.8 % | +1.16 % | +0.174 % | opciones |
| 250 | 26 | 72 | 1122 | 0.010 s | 0.031 s | 85.1 % | +0.47 % | +0.000 % | opciones |
| 500 | 43 | 115 | 2257 | 0.022 s | 0.066 s | 85.0 % | +1.43 % | +0.023 % | opciones |
| 1000 | 76 | 187 | 4503 | 0.042 s | 0.135 s | 85.8 % | +1.73 % | +0.000 % | opciones |
| 2500 | 176 | 428 | 11205 | 0.124 s | 0.385 s | 85.3 % | +1.16 % | +0.000 % | opciones |
| 5000 | 343 | 871 | 22499 | 0.280 s | 0.853 s | 85.5 % | +1.30 % | +0.000 % | opciones |

## Competencia por cupos

| holgura | inscritas 3 criterios | inscritas voraz+BT | prioridad 5 inscritas |
|---|---|---|---|
| 0.5 | 49.77 % | 49.77 % | 96.66 % |
| 0.7 | 69.76 % | 69.76 % | 96.0 % |
| 0.9 | 85.79 % | 85.79 % | 95.55 % |
| 1.1 | 92.12 % | 92.12 % | 95.33 % |
| 1.3 | 93.66 % | 93.66 % | 95.11 % |
| 1.5 | 94.01 % | 94.01 % | 95.11 % |
