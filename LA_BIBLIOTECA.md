# La biblioteca de herramientas

Cómo se ordenan los programas que el agente escribe y vuelve a usar, para que **no se escriban dos
veces** y para que **ninguno se corra a ciegas**.

> Todo lo de aquí existe porque lo contrario falló primero. Cada regla lleva escrito **qué se
> rompía sin ella**.

---

## 1 · El problema

Un proyecto largo con un agente acumula programas sin darse cuenta: uno para medir, otro para
comprobar, otro para arreglar algo una vez. En el proyecto del que sale este protocolo llegaron a
**más de doscientos cincuenta** en una sola carpeta. Y pasaron tres cosas:

1. **Se escribían otra vez.** Abrir cinco para encontrar el que servía costaba más que escribir uno
   nuevo, así que se escribía uno nuevo. Una misma función de normalizar texto llegó a estar
   **copiada 18 veces en 14 ficheros**, y las copias no eran iguales: unas pasaban a minúsculas y
   otras no. El mismo texto daba resultados distintos según qué herramienta lo mirara.
2. **Se corrían sin saber qué tocaban.** Antes de correr una herramienta desconocida hay que saber si
   **solo mira o cambia algo**. Leerse el script entero para averiguarlo cuesta más que el trabajo.
3. **Lo de un solo uso se mezclaba con lo que vale.** Un guion que se corrió una vez para mover unos
   ficheros, con las rutas de aquel día, quedaba al lado de las herramientas buenas. Correrlo un mes
   después era romper algo.

🔑 **Una carpeta de programas sin índice no es una biblioteca: es un trastero.** Y en un trastero se
compra otra vez lo que ya tenías.

---

## 2 · Las cuatro reglas

### Regla 1 · Antes de crear una herramienta, se pregunta si ya existe

```bash
python herramientas/consultar.py "lo que quiero saber"
```

y se mira `MAPA_HERRAMIENTAS.md`. Si ya hay una que contesta, **se usa o se amplía**. Solo si no hay
ninguna se escribe una nueva.

Es la regla que corta el problema 1 de raíz, y por eso va la primera: cuesta un segundo y evita la
copia número diecinueve.

### Regla 2 · Cada herramienta lleva su ficha

La ficha va **en el docstring** del programa, no en un documento aparte (un documento aparte se
desincroniza solo). Son tres líneas, cada una al principio de su renglón:

```python
"""Qué costó una sesión, turno a turno — medido, no estimado.

Contesta: ¿cuánto pesó el arranque y dónde se fue la cuota de la sesión?
Toca: nada (solo lee).
Necesita: el registro de la sesión (~/.claude/projects/<proyecto>/<sesión>.jsonl).
"""
```

| Línea | Qué dice | Si falta |
|:---|:---|:---|
| `Contesta:` | La pregunta que responde, **como pregunta** | Se usa la primera frase del docstring |
| `Toca:` | Lo que escribe, borra o envía, **con sus nombres** | El mapa lo deduce del código |
| `Necesita:` | Lo que tiene que haber para correrla y el código no enseña | Se omite |

`generar_mapa_herramientas.py` recoge las fichas en `MAPA_HERRAMIENTAS.md` y **añade lo que el código
enseña**: si usa la red, una consola remota, un modelo de lenguaje, una base de datos, y qué otras
herramientas importa.

🔑 **Y la comprueba**: si la ficha dice «solo lee» y el código escribe, sale **arriba del mapa**, en
rojo. *Un comentario del código no es una medida*: dice lo que alguien creyó el día que lo escribió.

### Regla 3 · Los nombres no se mueven

Cada herramienta se cita por su nombre en el diario, en los bugs, en los criterios. Renombrarla o
moverla de carpeta **rompe todas esas citas** sin avisar: el diario de hace un mes dirá «se corrió
`medir_x.py`» y ese fichero ya no existirá.

Así que lo que se aparta **va a un estante, no se renombra**.

### Regla 4 · Lo repetido se escribe una vez

Cuando la misma función aparece en dos o más herramientas, pasa a `comun/` y las herramientas la
importan. **Cada copia es un sitio donde el criterio puede quedarse atrás sin que nadie lo note.**

Si las copias no eran iguales, la diferencia **que era de verdad** se convierte en un parámetro. La
que no lo era se descarta. Y la pieza nueva se prueba **contra la copia que sustituye**: si da otro
resultado, se escribe en su docstring por qué.

---

## 3 · Los estantes

| Estante | Qué va ahí | Regla |
|:---|:---|:---|
| `herramientas/` | Las herramientas que se vuelven a correr | Cada una con su ficha. Las recoge el mapa |
| `herramientas/comun/` | El código que estaba copiado en varias | Se reutiliza antes de crear. Probado contra la copia que sustituye |
| `herramientas/datos/` | Lo que las herramientas leen o escriben: decisiones, juicios, volcados | No son herramientas: el mapa no las mira |
| `herramientas/_usados/AAAA-MM/` | Guiones de un solo uso, ya corridos, y sus restos | Se guardan como constancia. **No se corren desde ahí**: sus rutas eran las de su día |
| `herramientas/<copia>/` | Copia local del código que corre en otra máquina | Ver §4 |

Una plantilla del `LEEME.md` que explica los estantes dentro de tu propia carpeta está en
[`plantillas/HERRAMIENTAS_LEEME.md`](plantillas/HERRAMIENTAS_LEEME.md).

### Qué entra en `comun/` (criterio, no lista)

- Una función que aparece **igual o casi igual en dos o más herramientas** y no depende de un frente
  concreto del proyecto. Lo de un solo frente va a su propio módulo compartido, no aquí.
- ⛔ **No la importan las herramientas que también corren en otra máquina.** Si el despliegue sube un
  fichero suelto, `comun/` no viaja con él y allí reventaría al importar. Esas conservan su copia
  hasta que el despliegue lleve `comun/` consigo.

---

## 4 · El código que corre en otra máquina

El caso más caro de todos. Parte del código puede correr **fuera** del repositorio: en un servidor, en
un contenedor. Y entonces hay dos copias, y la tentación de arreglar «allí mismo, que es un momento».

**Lo que pasó**: unas partes se cambiaban en el servidor y se traían a casa; otras se cambiaban en casa
y se subían. **Dos sentidos es como se pierden arreglos**: uno vivió solo en el servidor durante días,
y el siguiente despliegue desde casa lo habría borrado sin que nadie lo notara.

**La regla**: **un solo sentido — casa manda — y una sola forma de desplegar**, la misma para todo lo
que corre fuera.

- El código se **cambia en casa**, con su git, su mapa y sus pruebas.
- Se **despliega** con un programa, nunca copiando a mano.
- La otra máquina **no se parchea en sitio**.

🔑 **Cómo sabe el despliegue quién cambió qué.** Comparar casa con el servidor dice que son
distintos, no quién se movió. Por eso cada despliegue deja en casa la **huella** (un MD5) de cada
fichero tal como quedó allí. Con tres huellas —casa, servidor y la del último despliegue— cada
fichero es una sola cosa:

| Casa | Servidor | Quiere decir | Se hace |
|:-:|:-:|:---|:---|
| = servidor | | Igual | Nada |
| ≠ | = la del último despliegue | Cambió en casa | **Se sube** |
| Está | No está, ni lo estuvo | Nuevo en casa | **Se sube** |
| No está | = la del último despliegue | Casa lo quitó | **Se aparta** a respaldos, nunca se borra |
| | ≠ la del último despliegue | **Cambió en el servidor** | ⛔ **Se niega el despliegue entero** |

Si se niega, el cambio del servidor se mira y se trae a casa (o se deshace allí) **antes** de desplegar.

**El ritual al escribir**, por orden: volver a medir justo antes (si algo cambió desde el ensayo, no
sigue) → subir a un temporal **fuera** del código → comprobar allí la huella y que compila → copiar lo
que va a cambiar a una carpeta de respaldo con fecha, con su manifiesto y su orden de restaurar → y
solo entonces moverlo a su sitio. Sin opciones, el programa **solo ensaya**: dice qué haría.

---

## 5 · Una guía por cada operación que se repite

Cuando una operación se hace a menudo y tiene varias maneras (lanzar una tanda, rehacer un producto,
desplegar), **cada manera acaba documentada en un sitio distinto**: un trozo en el diario, otro en un
bug, otro en la memoria del agente. Y cada sesión la redescubre.

**La regla**: una guía por operación, `GUIA_<OPERACIÓN>.md`, con siempre las mismas partes:

1. **La idea en cuatro líneas.**
2. **Qué va a cada manera**: cuándo se usa cada camino.
3. **Qué orden usar según el caso.**
4. **Qué pasa dentro**, lo justo para entender un fallo.
5. **Cómo se sabe si salió bien**: la comprobación, con lo que cuenta como bien.
6. **Lo que no hace el agente** (lo que lanza el usuario).
7. **Si algo falla.**

La guía apunta a las herramientas por su nombre; **no copia su código ni su uso** (eso ya está en su
ficha).

---

## 6 · Cómo se sabe que la biblioteca se está pudriendo

1. **Aparece una herramienta que hace lo mismo que otra.** No se preguntó antes de crear.
2. **El mapa marca en rojo una ficha que miente.** Se arregla la ficha, o el código.
3. **Un guion de un solo uso sigue en el estante principal.** Va a `_usados/AAAA-MM/`.
4. **Algo se arregló en la otra máquina y no en casa.** El próximo despliegue se negará: se trae a
   casa antes de seguir.
