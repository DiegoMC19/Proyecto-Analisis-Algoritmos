# Guía para la sustentación

La sustentación es **individual**: cada uno debe poder explicar cualquier parte del proyecto.
Esta guía corresponde a la versión final: **voraz con 3 criterios + backtracking con poda**
(ya no hay búsqueda local).

---

## 1. El proyecto en un minuto

> Asignamos estudiantes a secciones de las asignaturas que piden. Hay cuatro restricciones
> duras: solo lo que pidió, sin cruces ni asignaturas repetidas, sin clases en franjas que no
> puede, y sin pasar el cupo. Se maximiza f, que suma prioridad, afinidad con el profesor y
> compañeros, y resta franjas libres ocupadas y distancia caminada.
>
> El problema es NP-difícil (se reduce desde conjunto independiente máximo). Por eso usamos
> dos técnicas vistas en clase para problemas NP-completos:
> 1. un **voraz** que se corre con tres criterios de orden y se queda con el mejor;
> 2. un **backtracking con poda** que parte de esa solución, poda por restricciones y por
>    una cota, y tiene tiempo límite. Si recorre todo el árbol, da el óptimo.
>
> En 99 instancias pequeñas el backtracking con poda da siempre el óptimo, cientos de veces
> más rápido que sin cota. El voraz resuelve 5000 estudiantes en menos de un segundo. En
> instancias grandes el backtracking ya casi no mejora al voraz, que es lo esperable en un
> problema NP-difícil.

---

## 2. Números que hay que saber

| Qué | Valor |
|---|---|
| Pruebas automáticas | **55**, todas pasan |
| Óptimos en 99 instancias pequeñas | voraz (prioridad) 36 · voraz 3 criterios **42** · + backtracking **99** |
| Brecha promedio contra el óptimo | 2,13 % → **1,63 %** con 3 criterios → **0 %** con backtracking |
| Brecha máxima de los voraces | 13,5 % |
| Backtracking con 6 estudiantes (mediana) | sin cota **633 242 nodos, 1,6 s** · con poda **1794 nodos, 7 ms** |
| Peor caso de las 99 instancias | sin cota 15,6 s · con poda 0,11 s |
| Voraz con 5000 estudiantes | 1 criterio 0,28 s · 3 criterios **0,85 s** |
| Crecimiento del voraz | ≈ n^1,08 y n^1,09, consistente con O(n log n) |
| Mejora de 3 criterios sobre prioridad (instancias grandes) | entre 0,5 % y 1,7 %; siempre ganó **opciones** |
| Backtracking en instancias grandes (10 s) | unos 2 millones de nodos; mejoró en **2 de 18**, máximo +0,5 % |
| Solicitudes inscritas (holgura 0,9) | ≈ 85 % |
| Solicitudes de prioridad 5 inscritas | **> 95 %** en todos los niveles de competencia |

---

## 3. Mapa del código

| Archivo | Qué hace |
|---|---|
| `horarios/modelo.py` | Clases `Seccion`, `Estudiante`, `Instancia`. Cada campo es un símbolo de la formalización. |
| `horarios/validador.py` | Las 7 reglas de validez de una instancia. |
| `horarios/verificador.py` | Restricciones (1)–(4) y f desde cero. No comparte código con el algoritmo. |
| `horarios/generador.py` | Instancias aleatorias con semilla; cupos = demanda × holgura. |
| `horarios/estado.py` | Asignación con f incremental: cada cambio cuesta O(k_e + \|C_e\|). |
| `horarios/fuerza_bruta.py` | Backtracking **exacto sin cota**: la salida esperada de referencia. |
| `horarios/casos.py` | Los 6 casos hechos a mano. |
| `horarios/algoritmo.py` | **El algoritmo:** `ordenar`, `voraz`, `voraz_criterios`, `cota`, `backtracking`, `resolver`. |

---

## 4. El algoritmo, paso a paso

### Fase 1: voraz con 3 criterios
El voraz (`voraz`) recorre las solicitudes (e, a) en un orden y a cada una le da la sección
válida con mayor **ganancia** Δf, si es positiva. Nunca se devuelve.

El resultado depende mucho del orden, así que se corre con tres órdenes (`ordenar`) y se queda
con la mejor f (`voraz_criterios`):

| Criterio | Orden | Idea |
|---|---|---|
| **Prioridad** | mayor π primero; empate: asignatura con menos secciones | atender primero lo que más se necesita |
| **Escasez** | menor Σ cupos / número de solicitudes de la asignatura; empate: mayor π | repartir primero los cupos más disputados |
| **Opciones** | asignatura con menos secciones primero; empate: mayor π | lo que no tiene alternativa se ubica antes de que le ocupen las franjas |

**Relación con clase:** es como **selección de actividades**, donde se prueban varios criterios
voraces y ninguno es siempre el mejor.

**Ejemplo de memoria (por qué un solo criterio falla):**
- El estudiante pide A (prioridad 5) y B (prioridad 4).
- A tiene secciones el lunes y el martes; B solo el martes.
- Tiene afinidad +2 con el profesor de A del martes.
- **Prioridad** pone A el martes (gana 50 + 4) y ya no puede tomar B: **f = 54**.
- **Opciones** ubica primero B (una sola sección) y luego A el lunes: **f = 90**, el óptimo.

### Fase 2: backtracking con poda (`backtracking`)
Es el mismo árbol de decisiones que el exacto: un nivel por solicitud y, como ramas, cada
sección de la asignatura o "ninguna". Igual que el **coloreado de grafos** visto en clase.

Cuatro ideas:
1. **Punto de partida:** la mejor asignación conocida X\* empieza siendo la del voraz. Por eso
   el resultado **nunca es peor que el voraz**, y la cota poda desde el principio.
2. **Orden de las ramas:** las secciones se prueban de mayor a menor ganancia y "ninguna" al
   final, para encontrar soluciones buenas temprano.
3. **Dos podas:**
   - **Por restricciones:** solo se baja por secciones válidas (como `EsValido` en el coloreado).
   - **Por cota:** si f(X) + U(i) ≤ f(X\*), la rama se descarta.
4. **Tiempo límite** (10 s por defecto): si se acaba, devuelve la mejor encontrada. Si recorre
   todo el árbol antes, la respuesta es el **óptimo**.

### La cota, que es lo que más van a preguntar
Para cada solicitud (e, a) se calcula lo **máximo** que podría sumar a f:

  u(e, a) = w₁·π_e(a) + w₂·max(0, mejor afinidad de e con los profesores de a) + w₃·(|C_e| + |{e' : e ∈ C_e'}|)

y U(i) es la suma de u desde la solicitud i hasta el final.

**¿Por qué es una cota válida (nunca subestima)?**
- Toma la prioridad completa, la mejor afinidad posible (o 0 si todas son negativas) y como
  si todos sus amigos, en las dos direcciones, quedaran en su sección.
- **Ignora f₄ y f₅**, que solo restan.
- Cada vez que dos amigos quedan juntos, eso se le cuenta al que entra después, y su u ya lo
  incluye.

Entonces, si ni sumando el máximo posible de lo que falta se supera a X\*, ninguna hoja de esa
rama puede superarlo, y podarla **no pierde el óptimo**.

**¿Es ramificación y poda (branch and bound)?** Sí, la poda por cota es justamente esa idea.
Lo presentamos como backtracking con poda porque se implementa igual que el backtracking de
clase, más una cota.

---

## 5. Complejidad

- **Voraz con un criterio:** O(Q log Q + Q·t·τ), donde Q es el número de solicitudes, t el
  número de secciones por asignatura y τ = O(q + c) el costo de evaluar una ganancia con el
  estado incremental.
- **Con 3 criterios:** 3 veces lo mismo, así que el mismo orden. Como q ≤ 6, t ≤ 4 y c no
  crecen con n, Q = O(n) y el voraz es **O(n log n)**. Se midió n^1,09.
- **Backtracking con poda:** en el peor caso O((t+1)^Q · t·(τ + log t)), **exponencial**. La cota
  y el buen punto de partida **no cambian el peor caso**, solo reducen lo que se explora en la
  práctica. Por eso lleva tiempo límite.
- **Backtracking exacto sin cota:** O((t+1)^Q · τ). Recurrencia T(i) ≤ (t+1)·T(i+1).

---

## 6. Preguntas probables y respuestas

**¿Por qué es NP-difícil?**
Por reducción desde **conjunto independiente máximo**. Se toma un solo estudiante que pide todo
con prioridad 1, w₁ = 1 y los demás pesos en 0, así que f = |X|. Por cada vértice hay una
asignatura con una sola sección; por cada arista, un bloque que comparten las secciones de sus
dos extremos; y cada vértice tiene además un bloque propio, para que ninguna sección quede sin
franjas (F_g ≠ ∅). Así, dos secciones se cruzan si y solo si hay arista, y una asignación válida
es un conjunto independiente. Además está en NP porque el verificador revisa una solución en
tiempo polinomial.

**¿Por qué quitaron la búsqueda local?**
Porque el curso pide aplicar las técnicas vistas para problemas NP-completos: voraz,
aproximación y backtracking. Usamos dos de ellas.

**¿Su algoritmo es de aproximación?**
No. Un algoritmo de aproximación **garantiza** una cota (por ejemplo, "a lo sumo el doble del
óptimo"). El voraz no la garantiza (llegó a quedar 13,5 % por debajo), y el backtracking cortado
por tiempo tampoco. Lo que hicimos fue **medir** la brecha.

**¿Por qué tres criterios y no uno?**
Porque ningún orden es siempre el mejor, como en selección de actividades. Correr tres cuesta
solo una constante (×3), y bajó la brecha de 2,13 % a 1,63 %.

**¿Por qué el backtracking no mejora en instancias grandes?**
Con 5000 estudiantes hay unas 22 000 solicitudes y el árbol tiene del orden de (t+1)^22000
hojas. En 10 s visita unos 2 millones de nodos, una fracción ínfima, y casi todos cerca de las
últimas decisiones del recorrido. Es el compromiso calidad/tiempo típico de un problema
NP-difícil; para esas instancias la solución útil es la del voraz.

**¿Cómo saben que el backtracking con poda da el óptimo?**
Por el razonamiento de la cota (sección 4), y lo comprobamos: en las 99 instancias pequeñas da
el mismo f que el backtracking exacto sin cota, y hay pruebas automáticas que lo verifican.

**¿Por qué arrancar con la solución del voraz?**
Por dos razones: el resultado nunca es peor que el voraz, y con un X\* bueno desde el principio
la cota descarta muchas ramas de entrada.

**¿Por qué probar primero las secciones con más ganancia?**
Para llegar pronto a hojas buenas: así X\* mejora rápido y la cota poda más.

**¿Qué es el estado incremental?**
Recalcular f cuesta O(|X|). El `Estado` guarda f₁…f₅ y los actualiza al inscribir o retirar en
O(k_e + |C_e|):
- Δf₁ = π_e(a_g), Δf₂ = φ_e(p_g);
- Δf₃ = amigos de e en la sección más los estudiantes de la sección que tienen a e de amigo;
- Δf₄ = |L_e ∩ F_g|;
- Δf₅ = la distancia con cada otra clase de e que vaya seguida.

**¿Por qué no usaron programación dinámica?**
No hay subestructura óptima independiente: lo que se decide para un estudiante afecta a otros
(cupos, compañeros).

**¿Qué estructuras de datos usaron?**
Las franjas son conjuntos (el cruce es una intersección), estudiantes y secciones están en
diccionarios por id (búsqueda en O(1)), δ es una matriz y los compañeros, una lista de
adyacencia.

**¿Cómo validan que las salidas son correctas?**
Con un verificador independiente del algoritmo, los 6 casos a mano con respuesta única y la
comparación contra el óptimo del backtracking exacto en instancias pequeñas.

**¿Qué cambió respecto a la entrega 1?**
La formalización no cambió. Cambió el caso 4 (tenía dos óptimos), los cupos ahora dependen de la
demanda, las solicitudes del semestre, y el método exacto se implementó como backtracking.

**¿Qué mejorarían?**
Una mejor cota (por ejemplo, contando el cupo restante) para podar más; aceptar empeorar
temporalmente (recocido simulado); o comparar contra un solver de programación entera en
instancias medianas.

---

## 7. Demo en vivo

```
python -m unittest discover -s tests -t .
```
"55 pruebas: validez, restricciones, casos a mano, backtracking contra el exacto, f incremental."

```
python fuerza_bruta.py datos/instancias/inst_n6_s1.json
python resolver.py datos/instancias/inst_n6_s1.json
```
"El exacto sin cota recorre 4,2 millones de nodos en unos 10 s. El nuestro llega al mismo
óptimo, f = 514, con 3143 nodos en centésimas de segundo."

```
python resolver.py datos/instancias/inst_n1000_s42.json --solo-voraz
python resolver.py datos/instancias/inst_n1000_s42.json --tiempo 5
```
"Se ven los tres criterios y cuál gana (opciones). El backtracking se corta a los 5 s sin
recorrer todo el árbol, como explicamos."

```
python verificar.py datos/instancias/inst_n1000_s42.json resultados/voraz_bt/inst_n1000_s42.json
```
"El verificador confirma que la salida es válida y que la f reportada coincide."

---

## 8. Lista de chequeo

- [ ] Correr las pruebas en el computador de la sustentación.
- [ ] Ensayar la demo de la sección 7.
- [ ] Poder escribir la fórmula de la cota y explicar por qué es válida.
- [ ] Poder dibujar el ejemplo f = 54 contra 90 y decir qué criterio acierta.
- [ ] Repasar la reducción desde conjunto independiente.
- [ ] Leer `horarios/algoritmo.py` completo (son unas 200 líneas).
