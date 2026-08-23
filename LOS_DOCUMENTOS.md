# Los documentos: qué función tiene cada uno

> **La regla que gobierna este fichero**: cada documento contesta **una** pregunta y solo una.
> En cuanto dos documentos contestan la misma, uno de los dos miente — y no sabes cuál.

El síntoma de que esto se ha roto siempre es el mismo: alguien pregunta «¿dónde apunto esto?» y hay
dos respuestas razonables. Cuando pasa, la respuesta correcta casi nunca es crear un documento
nuevo; es que uno de los dos se ha salido de su función.

---

## El cuadro completo

| Documento | Contesta | Techo | Se lee… |
|:---|:---|---:|:---|
| `AGENTS.md` | **Cómo se trabaja aquí** | 200 | Solo, en cada sesión |
| `VIAS_DE_TRABAJO.md` | **Qué frentes hay abiertos** | 120 | Entero, en cada arranque |
| `ESTADO_ACTUAL.md` | **Dónde estamos** | 400 | Cuando toca esa vía |
| `DIARIO.md` | **Qué pasó** | — | Solo la última entrada |
| `REGISTRO_BUGS.md` | **Qué está roto** | — | Solo el bug que toca |
| `CRITERIOS.md` | **Qué no se vuelve a razonar** | — | Cuando reaparece la duda |
| `MAPA_CODIGO.md` | **Dónde está cada cosa** | — | Se consulta, no se lee |
| `MAPA_HERRAMIENTAS.md` | **Qué herramienta contesta qué** | — | Se consulta, no se lee |

---

## `VIAS_DE_TRABAJO.md` — el desvío

**Es un desvío, no un plan y no un registro.** Dice qué frentes hay abiertos, **a qué documento ir**
en cada uno, **qué NO abrir**, y cuál es el siguiente paso. Nada más.

Se lee **entero en cada arranque**, así que cada línea de más se paga en todas las sesiones.

⛔ **Aquí no se cuenta lo que pasó.** Lo que pasó es el diario; lo que está roto es el registro de
bugs; lo que se aprendió son los criterios.

🔑 **Si una entrada de este fichero empieza a narrar una sesión, está en el sitio equivocado.** Es
la señal de alarma más fiable que existe, y aparece sola cada pocas semanas.

Estructura por frente:

```markdown
## FRENTE A — <nombre>

| | |
|:---|:---|
| **Qué es** | <una línea> |
| **Documento que manda** | `<fichero>` — y si algo se contradice, gana él |
| **Además, según la tarea** | `<fichero>` (para qué) |
| ⛔ **No abrir** | `<fichero del otro frente>` — se paga entero para nada |

**En qué punto está**: <dos o tres líneas>.

**⏭️ Siguiente paso**: <uno solo, concreto>.
```

Ese **«documento que manda»** resuelve por adelantado la discusión de qué fuente gana cuando dos se
contradicen. Sin esa línea, el agente elige la que leyó última.

---

## `ESTADO_ACTUAL.md` — dónde estamos

Qué corre, qué se está haciendo, qué sigue. **Presente y futuro inmediato, nunca pasado.**

⛔ Techo de 400 líneas: si se pasa, **se poda antes de trabajar**, no «cuando haya un rato». Un
estado que ha crecido hasta las 700 líneas ya no se lee: se hojea, que es otra cosa.

La pregunta para podar: *¿esto sigue siendo verdad hoy, y hace falta para decidir el siguiente
paso?* Si es historia, va al diario. Si es una lección, va a los criterios. Si ya no es verdad, se
borra.

---

## `DIARIO.md` — qué pasó

Una entrada por sesión, siempre con dos partes: la **INTENCIÓN** (escrita antes de trabajar) y el
**RESULTADO** (escrito al terminar, debajo, sin borrar la intención).

Crece sin límite y **no pasa nada**, porque nunca se lee entero: el arranque lee la última entrada
desde su `### RESULTADO`.

Ese marcador hace un trabajo doble que conviene entender: si la última entrada **no lo tiene**,
significa que la sesión se cortó a la mitad — y entonces sí se lee entera, porque hay trabajo a
medias que nadie ha contado.

---

## `REGISTRO_BUGS.md` — qué está roto

Síntoma → causa → solución, un bloque por bug, numerados y con estado.

⚠️ **La trampa de este documento**, y cuesta cara: *un bug registrado describe el sistema del día en
que se escribió*. Un registro con cuarenta bugs abiertos no significa que haya cuarenta cosas rotas
— significa que hay cuarenta **anotaciones**, y varias describen un sistema que ya no existe.

🔑 **Antes de ponerse con un bug antiguo, comprobar contra el sistema real que sigue estando.** El
registro es una libreta, no un diagnóstico.

---

## `CRITERIOS.md` — lo que no se vuelve a razonar

Aquí va lo que **sobrevive al proyecto**: cómo se mide, cómo se decide, cómo se opera. No los casos,
sino la regla que los generó.

La prueba para saber si algo pertenece aquí: **¿seguiría siendo verdad en el proyecto siguiente?**
Si la respuesta es no, es un bug o una nota de estado, no un criterio.

Cada criterio se escribe con **el caso que lo produjo**. Una regla sin su historia se salta a la
primera prisa, porque nadie recuerda qué se rompió sin ella.

---

## Los mapas — generados, jamás escritos

`MAPA_CODIGO.md` y `MAPA_HERRAMIENTAS.md` **los produce un programa** leyendo el código real.

**El motivo, y es de los caros**: un índice mantenido a mano en la cabecera de un fichero apuntaba a
líneas equivocadas, porque nadie lo actualizaba al mover el código. El agente leía el rango que el
índice decía, encontraba otra cosa, y trabajaba sobre suposiciones.

> ⛔ **Editar un mapa a mano es reintroducir exactamente ese fallo.** Cada mapa lleva el aviso
> escrito dentro de sí mismo, en la primera línea, porque el que lo va a editar a mano no va a
> venir a leer este documento.

Se regeneran **siempre que se muevan o añadan funciones**, y desde luego antes de cerrar sesión.

---

## Cómo se sabe que esto se está pudriendo

Tres señales, por orden de aparición:

1. **El desvío narra sesiones.** Aparece un párrafo contando lo que se hizo el martes. Va al diario.
2. **El estado tiene historia.** Frases en pasado que ya no afectan al siguiente paso. Van al diario.
3. **Dos documentos se contradicen** y hay que abrir los dos para saber cuál vale. Falta la línea de
   «documento que manda», o sobra uno de los dos.

Ninguna se arregla añadiendo un documento nuevo.
