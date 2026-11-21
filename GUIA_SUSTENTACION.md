# Guía para la sustentación

La sustentación es **individual**: cada uno debe poder explicar cualquier parte del proyecto,
no solo la que escribió. Esta guía resume lo que hay que saber, una demo en vivo y las
preguntas más probables con sus respuestas.

---

## 1. El proyecto en dos minutos

> Asignamos estudiantes a secciones de las asignaturas que piden, respetando cuatro
> restricciones duras (solo lo que pidió, sin cruces ni asignaturas repetidas, sin clases en
> franjas que no puede, sin pasar el cupo) y maximizando una función con cinco criterios:
> prioridad, afinidad con el profesor, compañeros, franjas libres y distancia entre salones.
>
> El problema es NP-difícil (se reduce desde conjunto independiente máximo), así que el
> óptimo solo se puede calcular en instancias muy pequeñas. Para eso hicimos una fuerza
> bruta con backtracking que usamos como referencia.
>
> Nuestro algoritmo tiene dos fases: un **voraz** que inscribe las solicitudes de mayor a
> menor prioridad en la sección que más sube f, y una **búsqueda local** con cuatro
> movimientos (insertar, cambiar, expulsar, intercambiar) que corrige los errores del voraz.
>
> En 99 instancias pequeñas llega al óptimo en 72 y queda en promedio a 0,77 % de él.
> Resuelve 5000 estudiantes en menos de un minuto, y todas sus salidas pasan el verificador.

---

## 2. Números que hay que saber

| Qué | Valor |
|---|---|
| Pruebas automáticas | 53, todas pasan |
| Calidad (99 instancias, n = 3 a 6) | voraz óptimo en 36, voraz+BL en **72** |
| Brecha promedio contra el óptimo | voraz 2,13 % → voraz+BL **0,77 %** |
| Instancias con brecha ≤ 1 % | 83 de 99 |
| Mejora de la BL sobre el voraz (instancias grandes) | ≈ 3,5 % en f, ≈ 3 puntos más de solicitudes inscritas |
| Tiempo con 5000 estudiantes | voraz 0,24 s, voraz+BL ≈ 52 s |
| Crecimiento empírico del tiempo | voraz ≈ n^1,10, voraz+BL ≈ n^1,56 |
| Fuerza bruta | se multiplica ≈ ×10 por estudiante; mediana n = 6 ≈ 1,3 s (n = 8 serían minutos, n = 10 horas) |
| Solicitudes de prioridad 5 inscritas | > 97 % en todos los niveles de competencia |
| Pasadas de la búsqueda local | entre 7 y 15; siempre terminó en óptimo local |

---

## 3. Mapa del código

| Archivo | Qué hace | Lo que hay que saber explicar |
|---|---|---|
| `horarios/modelo.py` | Clases `Seccion`, `Estudiante`, `Instancia` | Cada campo es un símbolo de la formalización (a_g, π_e, N_e…). La afinidad es dispersa: si no aparece, vale 0. |
| `horarios/validador.py` | Las 7 reglas de validez de una instancia | Trabaja sobre el JSON crudo para reportar todos los errores a la vez. |
| `horarios/verificador.py` | Restricciones (1)–(4) y f desde cero | Es independiente del algoritmo: así comprobamos que el algoritmo no hace trampa. |
| `horarios/generador.py` | Instancias aleatorias con semilla | Misma semilla = misma instancia. Cupos según la demanda × holgura. |
| `horarios/estado.py` | Asignación con f incremental | Cada cambio cuesta O(k_e + \|C_e\|) en vez de O(\|X\|). |
| `horarios/fuerza_bruta.py` | Óptimo exacto por backtracking | La poda solo quita ramas inválidas, no cambia el resultado. |
| `horarios/casos.py` | Los 6 casos hechos a mano | Cada uno prueba un criterio y tiene una única respuesta. |
| `horarios/algoritmo.py` | Voraz + búsqueda local | Los cuatro movimientos y por qué termina. |
| `experimentos.py`, `graficas.py` | Experimentos y gráficas | Qué mide cada experimento. |

---

## 4. Demo en vivo (5 minutos)

Ejecutar en este orden desde la carpeta del proyecto:

```
python -m unittest discover -s tests -t .
```
"Estas son las 53 pruebas: reglas de validez, restricciones, casos a mano, la fuerza bruta
contra un recorrido ingenuo y la f incremental contra la f desde cero."

```
python resolver.py datos/instancias/caso6.json
```
"Caso de la distancia: queda en la sección del mismo edificio. f = 79,6, igual al óptimo."

```
python fuerza_bruta.py datos/instancias/inst_n6_s1.json
python resolver.py datos/instancias/inst_n6_s1.json
```
"La fuerza bruta recorre 4 millones de nodos en varios segundos; el algoritmo llega al
mismo óptimo, f = 514, en milisegundos."

```
python generar.py -n 1000 --semilla 7
python resolver.py datos/instancias/inst_n1000_s7.json --solo-voraz
python resolver.py datos/instancias/inst_n1000_s7.json
```
"Generamos una instancia nueva en vivo. El voraz tarda centésimas de segundo; la búsqueda
local sube f cerca de 3,5 % en unos segundos."

```
python verificar.py datos/instancias/inst_n1000_s7.json resultados/voraz_bl/inst_n1000_s7.json
```
"El verificador, que no comparte código con el algoritmo, confirma que la salida es válida
y que la f reportada coincide."

Tener abiertas las gráficas de `resultados/experimentos/` (sobre todo `tiempo_vs_n.png` y
`fuerza_bruta_vs_algoritmo.png`).

---

## 5. Preguntas probables y respuestas

### Sobre el problema

**¿Por qué el problema es difícil? ¿Es NP-difícil?**
Sí. Se reduce desde **conjunto independiente máximo**: por cada vértice se crea una
asignatura con una sola sección, por cada arista una franja que comparten las secciones de
sus dos extremos, y un solo estudiante que pide todo con prioridad 1 y w1 = 1 (los demás
pesos en 0). Dos secciones se cruzan si y solo si hay arista, así que una asignación válida
es un conjunto independiente y f = |X|. Encontrar el máximo es NP-difícil, entonces nuestro
problema también. Además está en NP porque el verificador revisa una solución en tiempo
polinomial.

**¿Con qué problemas vistos en clase se relaciona?**
Con **coloreo de grafos**: asignar secciones sin cruces se parece a colorear un grafo de
conflictos. Con **mochila**: los cupos son capacidades y la prioridad es el valor. Y con los
**voraces**: nuestro voraz es como el de mochila por densidad, que es rápido pero no siempre
óptimo.

**¿Por qué w1 es el peso más grande?**
Porque lo más importante para un estudiante es poder cursar lo que necesita. Con w1 = 10 y
prioridades de 1 a 5, inscribir una solicitud vale entre 10 y 50, mucho más que la afinidad
(±4), un compañero (1) o una franja libre (1).

### Sobre el algoritmo

**¿Por qué el voraz va por prioridad?**
Porque w1 domina f. Inscribir primero lo prioritario asegura que esas solicitudes tomen los
cupos y horarios antes que las de baja prioridad. Entre prioridades iguales van primero las
asignaturas con menos secciones, porque tienen menos alternativas.

**Den un ejemplo en el que el voraz falle.**
Un estudiante pide A (prioridad 5) y B (prioridad 4). A tiene secciones el lunes y el martes;
B solo el martes. El estudiante tiene afinidad 2 con el profesor de A del martes. El voraz
pone A el martes (ganancia 54) y ya no puede tomar B: f = 54. El óptimo es A el lunes y B el
martes: f = 90. La búsqueda local lo corrige con el movimiento de **expulsar**: B entra
sacando a A del martes, y A se reubica el lunes.

**¿Qué hace cada movimiento de la búsqueda local?**
- **Insertar:** una solicitud pendiente toma un cupo que quedó libre.
- **Cambiar:** un estudiante pasa a una sección mejor de la misma asignatura, o la suelta si
  eso sube f.
- **Expulsar:** una solicitud pendiente entra a una sección sacando lo que estorba (sus
  propias clases que se cruzan, o a otro estudiante si está llena) y luego intenta reubicar lo
  que salió. Si f no mejora, se deshace todo.
- **Intercambiar:** dos estudiantes de dos secciones llenas de la misma asignatura cambian de
  lugar. Lo agregamos al comparar contra la fuerza bruta: en n = 5 y n = 6 faltaba justo eso.

**¿Por qué la búsqueda local termina?**
Cada movimiento aceptado aumenta f estrictamente, y hay un número finito de asignaciones, así
que no puede repetir una asignación ni ciclar. Además hay un límite de pasadas (100) y de
tiempo. En los experimentos siempre paró por llegar a un óptimo local (de 7 a 15 pasadas).

**¿Qué es un óptimo local? ¿Por qué no siempre llega al óptimo global?**
Una asignación en la que ninguno de los cuatro movimientos mejora f. El óptimo global puede
necesitar varios cambios a la vez (por ejemplo, una cadena de intercambios entre tres
estudiantes de dos asignaturas distintas), que ningún movimiento individual hace. Eso pasa en
`inst_n4_s1`, donde quedamos a 0,72 %. Se podría escapar con recocido simulado o búsqueda
tabú, que aceptan empeorar temporalmente.

**¿Por qué en la expulsión solo prueban 3 candidatos?**
Probar a todos los estudiantes de la sección multiplica el tiempo por el cupo (≈ 20). Se
prueban primero los que tienen otra sección libre a donde ir (sacarlos casi no cuesta nada) y
luego los de menor prioridad. En las instancias pequeñas la calidad no cambió y en la de 5000
el resultado bajó solo 0,08 %, mientras que el tiempo bajó de 205 s a unos 40–50 s. Es una
decisión heurística consciente.

**¿Qué es la clase `Sucios`?**
Después de la primera pasada solo se revisan las asignaturas y estudiantes que cambiaron,
porque un movimiento sobre algo que no cambió da el mismo resultado que antes. Cuando una
pasada parcial no encuentra nada, se hace una completa para confirmar el óptimo local.

### Sobre la eficiencia

**¿Qué es el estado incremental y por qué importa?**
Recalcular f desde cero cuesta O(|X|). La fuerza bruta y la búsqueda local agregan y quitan
pares millones de veces, así que el `Estado` guarda f₁…f₅ y los actualiza al inscribir o
retirar:
- Δf₁ = π_e(a_g), Δf₂ = φ_e(p_g)
- Δf₃ = amigos de e en la sección + estudiantes de la sección que tienen a e como amigo
- Δf₄ = |L_e ∩ F_g| (exacto porque F_g no se cruza con sus otras clases)
- Δf₅ = distancia con cada otra clase de e, por las veces que van seguidas

Así cada cambio cuesta O(k_e + |C_e|). Una prueba hace 1500 operaciones al azar y comprueba
que la f incremental es igual a la recalculada.

**¿Cuál es la complejidad del algoritmo?**
- Voraz: O(Q log Q + Q·t·τ), con Q solicitudes, t secciones por asignatura y τ = O(q + c)
  el costo de evaluar un par. Como q, t y c no crecen con n, es **O(n log n)**.
- Búsqueda local: una pasada completa es O(n log n). El número de pasadas no tiene una cota
  polinomial demostrable, por eso se limita a L pasadas: O(L · n log n).
- Fuerza bruta: O((t+1)^Q · τ), **exponencial**.

**¿Por qué el tiempo medido de la búsqueda local crece como n^1,56 y no como n log n?**
Porque el número de movimientos aceptados crece con n, y cada uno obliga a volver a revisar
lo que tocó en las pasadas siguientes. Sigue siendo polinomial y muy lejos de la fuerza
bruta. El voraz sí coincide con la teoría (n^1,10 ≈ n log n).

**¿Cómo midieron el exponente?**
Ajustando una recta a log(tiempo) contra log(n) con mínimos cuadrados. La pendiente es el
exponente b de tiempo ≈ a·n^b.

### Sobre la fuerza bruta

**¿Cómo funciona la fuerza bruta?**
Backtracking: decide una solicitud por nivel (ninguna sección o una de las de su asignatura).
Si inscribir viola una restricción, no baja por esa rama. Al llegar a una hoja compara f con
la mejor encontrada.

**¿La poda no hace que se pierda el óptimo?**
No. Solo poda ramas que ya son inválidas, y ninguna asignación válida puede tener una parte
inválida. Además una prueba la compara contra un recorrido ingenuo con `itertools.product` de
todas las (t+1)^(n·q) combinaciones, en 8 instancias distintas.

**¿Hasta dónde llega?**
Hasta unos 6 estudiantes. El espacio crece de 2560 combinaciones (n = 3) a 2,6 millones
(n = 6), y el tiempo se multiplica por cerca de 10 con cada estudiante: con 8 serían
minutos y con 10, horas.

### Sobre los datos y la validación

**¿Por qué generan los datos en vez de usar datos reales?**
Los amigos y la afinidad con profesores son datos personales y no son públicos. El generador
es reproducible (misma semilla, misma instancia) y permite controlar la dificultad.

**¿Cómo saben que el algoritmo da respuestas correctas?**
Tres niveles:
1. El **verificador** revisa toda salida con un código independiente del algoritmo.
2. Los **6 casos a mano** tienen una respuesta conocida y única.
3. Las **instancias pequeñas** se comparan contra el óptimo de la fuerza bruta.

**¿Qué cambiaron respecto a la entrega 1?**
- El caso 4 tenía dos óptimos; le agregamos una franja libre para que fuera único.
- Los cupos se calculan según la demanda × holgura; con un rango fijo, en instancias grandes
  casi nadie quedaba inscrito.
- Los estudiantes piden más asignaturas de su semestre y conocen sobre todo a los profesores
  de sus asignaturas, para que f₃ y f₂ influyan.
- El reporte del verificador trae campos extra para depurar.

**¿Por qué con holgura 1,5 no se inscribe el 100 %?**
Porque hay solicitudes imposibles: asignaturas cuyas únicas secciones se cruzan entre sí o con
las franjas no disponibles del estudiante.

**¿Qué mejorarían?**
- Recocido simulado o búsqueda tabú para escapar de óptimos locales.
- Comparar contra un modelo de programación entera con un solver (por ejemplo, OR-Tools) en
  instancias medianas, donde la fuerza bruta ya no alcanza.
- Paralelizar las pasadas o reescribir las partes críticas en un lenguaje compilado.

---

## 6. Puntos débiles (y cómo responder si los mencionan)

- **No garantiza el óptimo.** Es esperable: el problema es NP-difícil. Lo medimos: 72 de 99
  óptimas y brecha promedio de 0,77 %.
- **La búsqueda local tarda ≈ 50 s con 5000 estudiantes.** Es Python puro, en un hilo. El voraz
  solo tarda 0,24 s y ya da una solución válida; la búsqueda local es opcional y tiene límite
  de tiempo.
- **Brecha máxima de 10,4 %** en una instancia pequeña. Es un óptimo local que necesita varios
  cambios simultáneos; en instancias pequeñas una brecha porcentual grande puede ser una sola
  solicitud de diferencia.
- **Los datos son sintéticos.** Es por privacidad; el generador imita la realidad
  (popularidad, semestres, trabajo, preferencias) y es reproducible.

---

## 7. Lista de chequeo antes de la sustentación

- [ ] Clonar el repositorio y correr las pruebas en el computador que van a usar.
- [ ] Tener `matplotlib` instalado y las gráficas abiertas.
- [ ] Ensayar la demo de la sección 4 (que los comandos funcionen y los tiempos sean similares).
- [ ] Repasar la reducción desde conjunto independiente (sección 5).
- [ ] Poder dibujar en el tablero el ejemplo donde el voraz falla.
- [ ] Saber de memoria la tabla de la sección 2.
- [ ] Leer `horarios/algoritmo.py` completo al menos una vez: el docstring de arriba resume todo.
