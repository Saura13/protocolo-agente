# El protocolo de sesión

Cómo se abre, se lleva y se cierra una sesión de trabajo con un agente.

> Todo lo de aquí existe porque lo contrario falló primero. Cada regla lleva escrito **qué se
> rompía sin ella**, porque una regla sin su motivo se salta a la primera prisa.

---

## 1 · El arranque

**El problema**: el agente no recuerda nada. Cada sesión empieza de cero, y la tentación es
volcarle todo el proyecto «para que se sitúe». Eso cuesta la mitad de la sesión antes de escribir
una línea de código.

**La solución**: una orden corta y fija — *«retomamos \<proyecto\>»* — que dispara **exactamente**
seis pasos y ni uno más:

1. **Leer solo el desvío.** Un documento corto (`VIAS_DE_TRABAJO.md`) que dice qué frentes hay
   abiertos, a qué documento ir en cada uno y cuál es el siguiente paso. Nada más.
2. **Preguntar por qué frente se va**, si el usuario no lo ha dicho. No se elige por cuenta propia:
   la elección depende del tiempo que tenga ese día y de qué le aprieta más, y eso no se adivina.
3. **Leer solo la sección del paso que toca.** No el documento entero. El desvío ya ha dicho cuál
   es la sección. 🔑 *Lo que el desvío ya te ha dicho no se vuelve a pagar.*
4. **Comprobar que el sistema responde** con un solo comando.
5. **Mirar si hay otra sesión viva.** Si la hay, cada una se pone un nombre propio y se avisan antes
   de tocar lo común (§9).
6. **Responder en menos de 15 líneas** — dónde estamos, siguiente paso, qué está bloqueado, qué otra
   sesión hay viva y **con qué modelo va ese paso** (§8) — y **esperar el visto bueno antes de tocar
   nada**.

⛔ **Lo que NO se hace al arrancar**: abrir auditorías, planes, código «por si acaso», ni el
documento del frente por el que hoy no se va.

### El techo de líneas no es estético

Cada documento que se lee al arrancar tiene un **techo de líneas escrito dentro**, y cuando se pasa
**se poda antes de trabajar**, no después. El motivo es aritmético: un documento de arranque no se
paga una vez, se paga en **todas** las sesiones que queden de proyecto.

| Documento | Techo | Por qué ese |
|:---|---:|:---|
| El mapa (`AGENTS.md`) | 200 | Se carga solo, siempre, en todas las sesiones |
| El desvío (`VIAS_DE_TRABAJO.md`) | 120 | Se lee entero en cada arranque |
| El estado (`ESTADO_ACTUAL.md`) | 400 | Se lee cuando toca, no siempre |
| El diario, los bugs, los criterios | *sin techo* | Se leen **por trozos**, nunca enteros |

Un techo de líneas solo no para una línea de veinte mil caracteres: en `protocolo.config.json` un techo puede
llevar también **caracteres** (`{ "lineas": 120, "caracteres": 16000 }`). Y el diario puede ser una carpeta con
un fichero por mes, para que ni siquiera él crezca sin límite.

---

## 2 · Un solo asunto por sesión

**El problema**: se arregla algo, se ve otra cosa de paso, se tira del hilo, y a las tres horas hay
cuatro cambios a medias, ninguno registrado, y el contexto agotado.

**La regla**: un asunto por sesión. Si el arreglo resulta pequeño, se sigue con el siguiente. Si es
grande o se complica: **registrar, cerrar, y empezar con contexto limpio**.

Tener varios frentes abiertos no autoriza a saltar de uno a otro dentro de la misma sesión.

### El hallazgo que no es de hoy

La regla de arriba dice **no tires del hilo**. Le falta la otra mitad: **dónde se deja el hilo.**
Una regla que te prohíbe perseguir algo sin decirte dónde apuntarlo se incumple sola — si no hay
sitio, o lo persigues y pierdes la sesión, o lo pierdes a secas.

**Cuando aparece algo roto que no es el asunto de hoy**: se anota en `REGISTRO_BUGS.md` como 🔴,
dos líneas, con **el síntoma y la fecha, y sin diagnosticar**. No se busca la causa: buscarla ya es
tirar del hilo. Y se sigue con lo de hoy.

🔑 **Anotar no es aplazar; perseguir sí es abandonar lo de hoy.**

⚠️ **La excepción**: si lo que ha aparecido **hace inútil el trabajo de hoy**, no es un hallazgo al
margen — es un hallazgo que cambia el plan, y se dice en el momento (§4).

---

## 3 · Registrar al empezar, no al terminar

**El problema, medido**: las sesiones se agotaban justo antes de escribir el resultado. La siguiente
partía de un mapa falso — creía terminado lo que estaba a medias.

**La regla**: la entrada del diario se escribe **antes** de trabajar. Dos o tres líneas:

```markdown
## <fecha> · Sesión <n> — INTENCIÓN: <qué se va a hacer>

**Lo dijo el usuario**: «<sus palabras, literales>».
**Por qué ahora**: <qué lo hace el siguiente paso>.
**Qué se va a tocar**: <ficheros o zonas>.
```

Y al terminar se **añade** debajo, sin borrar la intención:

```markdown
### RESULTADO — <el titular en una línea>
```

Así, si la sesión se corta a la mitad, la siguiente encuentra la intención y sabe dónde se quedó.
Y ese `### RESULTADO` es además lo que el arranque busca: si la última entrada lo tiene, se lee solo
desde ahí; si no lo tiene, significa **sesión cortada** y hay que leerla entera.

---

## 4 · Mientras se trabaja: sin partes por el camino

**El problema**: los partes de situación cada pocos minutos parecen inofensivos y no lo son.

🔑 **El coste de releer crece con el cuadrado de los turnos.** Un mensaje intermedio no cuesta lo
que ocupa: cuesta eso **multiplicado por todos los turnos que vengan después**, porque cada turno
posterior vuelve a arrastrar la conversación entera.

**La regla**: se encadena el trabajo y se da **un** informe al final. Se interrumpe solo por:

- una **decisión** que le corresponde al usuario,
- un **riesgo** que hay que avisar **antes** de correrlo,
- un **hallazgo que cambia el plan**.

---

## 5 · El cierre — qué se actualiza y dónde se apunta

**Lo primero: correrlo, no recordarlo.**

```bash
python herramientas/comprobar_cierre.py
```

🔑 *Una regla que depende de que alguien la teclee no es una regla.* La lista de abajo estaba
escrita y aun así se saltaba, porque cumplirla exigía acordarse **justo cuando el contexto se está
agotando** — el peor momento posible para acordarse de nada.

### La tabla del cierre

| Qué se actualiza | Dónde se apunta | Quién lo comprueba |
|:---|:---|:---|
| **Cómo acabó** el trabajo | `DIARIO.md`, bajo `### RESULTADO` en la entrada de hoy | ✅ el programa |
| **Cuál es el siguiente paso** | `ESTADO_ACTUAL.md` | 👤 a mano |
| **En qué quedó el bug** que se traía | `REGISTRO_BUGS.md` | 👤 a mano |
| **Lo roto que apareció de paso** | `REGISTRO_BUGS.md`, como 🔴 sin diagnosticar | 👤 a mano |
| **Qué frente queda abierto** | `VIAS_DE_TRABAJO.md`, si cambió | 👤 a mano |
| **La lección**, si vale fuera del caso | `CRITERIOS.md` | 👤 a mano |
| **Dónde vive ahora cada función** | Regenerar `MAPA_CODIGO.md` | ✅ el programa |
| **Los techos de línea** | Podar el documento que se pasó | ✅ el programa |
| **Con qué modelo se abre la siguiente** | El `⏭️ siguiente` de la vía lleva `[Opus]` / `[Sonnet]` (§8) | ✅ el programa |
| **Todo lo anterior, junto** | Un commit que explique el porqué, y la rama juntada | ✅ el programa (que exista) |
| **La siguiente sesión, preparada** | Una receta cerrada, lista para abrir (§10) | 👤 a mano |

**Qué comprueba el programa**: techos de líneas (y de caracteres) de los documentos de arranque · que
la última entrada del diario tenga `### RESULTADO` · que ningún mapa sea más viejo que **el código que
él declara mapear** (con fechas de git, no de disco) · si llevas la hoja de vías generada, que esté al día · que cada «siguiente» diga con qué modelo
se abre · que no queden cambios sin registrar en git, y que la rama no se quede sin juntar (aviso).
Sale con código 1 si algo falta.

**Y los programas que ahorran leer**: `apuntar.py` escribe la entrada del diario y los avisos entre vías con su
formato y bajo cerrojo (así dos sesiones a la vez no se pisan, y la fecha no se la inventa el agente);
`consultar.py` contesta «qué toca a X» desde el índice que genera `indice.py`; `generar_vias.py` arma
`VIAS_DE_TRABAJO.md` a partir de una ficha por vía; `juntar_rama.py --juntar` lleva la rama de la sesión a la
principal sin perder nada —el diario y los avisos se suman (`plantillas/gitattributes`), lo generado se regenera y
cualquier otro choque frena sin tocar nada—. Todo se declara en `protocolo.config.json`.

**Qué no puede comprobar, y por eso lo recuerda al final**: si el siguiente paso está de verdad
escrito, si el registro de bugs refleja la realidad de hoy, si el mensaje del commit explica el
porqué, si la verificación se hizo **por donde entra el usuario**, si se le ha dicho **con qué modelo
abrir la próxima** y si esa próxima **queda preparada**.

### Y decirlo

Cuando esté, decirlo explícitamente: *«esto está registrado, puedes cerrar y retomamos con contexto
limpio»*. El usuario no tiene por qué adivinar cuándo es seguro cerrar.

---

## 6 · Los commits

El mensaje **explica el porqué, no el qué**. El «qué» ya está en el diff; el «porqué» se pierde para
siempre si no se escribe.

Mal: `arreglar bug del botón`
Bien: `Un identificador solo significa algo dentro del catálogo que lo emitió`

El segundo se entiende dentro de un año sin abrir el código.

### Un aviso práctico si trabajas en Windows

Los mensajes multilínea se pasan con un *here-document* de **Bash**:

```bash
git commit -F- <<'EOF'
El título del commit

El cuerpo, explicando el porqué.
EOF
```

⚠️ El equivalente de PowerShell (`@'…'@`) rompe el título del commit. Si el shell por defecto es
PowerShell, hay que invocar Bash explícitamente.

---

## 7 · Cuándo se para

Se le dice al usuario que cierre **cuando el asunto está terminado y registrado**, o **cuando se ve
que va a alargarse**. Seguir con el contexto medio lleno produce trabajo peor y más caro que
retomarlo limpio cinco minutos después.

---

## 8 · Qué modelo para qué paso

**El problema**: hay un modelo que juzga mejor y cuesta más (en el proyecto de origen, Opus) y otro que
ejecuta casi igual de bien por bastante menos (Sonnet). Usar el caro para todo derrocha cuota; usar el
barato para todo acaba en decisiones mal tomadas. Y cambiar de modelo **a mitad de sesión** no sale gratis:
el nuevo no hereda la caché ni el razonamiento, así que **se repaga el arranque entero**.

🔑 **El modelo se elige al abrir la sesión, nunca a mitad.** Si el paso cambia de tipo, se cierra y se
abre otra.

| **Modelo que ejecuta** — tarea cerrada: se sabe qué debe salir | **Modelo que juzga** — hay que decidir |
|:---|:---|
| Aplicar un cambio ya decidido (el «qué» está escrito en el diario o en el bug) | Si el producto está bien hecho |
| Correr herramientas de mapas o de cierre y leer lo que dicen | Qué va dónde; si un material sirve |
| Medir, contar, rastrear registros | Diagnosticar un bug nuevo y diseñar su arreglo |
| Commits, y cerrar con el resultado ya claro | Criterios, especificaciones, lo que va a `CRITERIOS.md` |
| | Tocar el entorno real con riesgo |

En la duda, el que juzga: un error de juicio cuesta más que los tokens.

**Cómo se planifica con eso:**

1. **Cada paso de un plan lleva su etiqueta**, `[Opus]` o `[Sonnet]` (o las que uses tú). Un paso que
   mezcla juicio y ejecución **se parte en dos**.
2. **Los pasos seguidos del mismo modelo van en la misma sesión.** Cambiar de etiqueta es cambiar de sesión.
3. **El `⏭️ siguiente` de cada vía lleva la etiqueta** del paso que nombra. `comprobar_cierre.py` lo exige
   (`cierre.siguiente` en la configuración).
4. **Se dice al cerrar, no al arrancar.** La última línea al usuario dice *«la próxima, en Sonnet»*. Al
   arrancar ya llega tarde: la sesión está abierta con un modelo.
5. **Un ayudante barato a mano, sin cerrar sesión.** En una sesión cara, lo cerrado y de salida pesada
   (medir, rastrear, correr una herramienta de solo lectura) puede ir a un **subagente del modelo barato,
   de solo lectura**, que devuelve un resumen corto. ⚠️ Cada subagente arranca en frío y eso es lo que más
   cuota come: solo compensa si **la entrada cabe en pocas líneas y la salida bruta sería pesada**. Para
   algo pequeño sale más caro. Y al revés: si en una sesión barata aparece un juicio que no estaba en el
   plan, **no se decide** ahí; se anota como pendiente `[Opus]` y se sigue con lo cerrado.

---

## 9 · Varias sesiones a la vez

**El problema**: con varios frentes abiertos, lo natural es tener dos o tres sesiones vivas, cada una en
su carpeta de trabajo (un *worktree* de git) y su rama. Y entonces dos cogen la misma letra del día en el
diario, un aviso de una vía llega a la sesión equivocada, o una reinicia el servidor mientras la otra
estaba midiendo en él.

**Lo que lo resuelve sin pensar** (está en las herramientas):

- `apuntar.py` reparte **la letra del día** mirando el diario de **todas** las carpetas de trabajo y de la
  rama principal, bajo un cerrojo en el almacén común de git: dos sesiones nunca cogen la misma.
- El diario y los avisos **se suman** al juntar (`plantillas/gitattributes`, `merge=union`).
- `juntar_rama.py --juntar` lleva la rama a la principal **siempre igual**: regenera lo generado y frena
  **sin tocar nada** si algo se fuera a perder.

**Lo que hay que hacer a mano:**

1. **Al arrancar, mirar si hay otra sesión viva.** Lo no archivado es lo vivo.
2. **Si la hay, nombre propio en cada una** («Vía A · tema»). Dos sesiones de la misma vía, nombres
   distintos: un mensaje dirigido a «la de la vía G» llegó a la G equivocada.
3. **Antes de tocar lo común, avisar a la otra y esperar su respuesta.** Lo común es: el entorno real
   (subir, reiniciar, compilar, entrar a medir) y los documentos compartidos (estado, hoja de vías,
   registro de bugs). Leer o tocar solo lo de la propia vía no se avisa.
4. **Nunca `git add -A`.** Se añade lo propio, por nombre: lo demás puede ser de otra sesión.
5. **Lo que una vía decide y cambia a otra** se deja como aviso (`apuntar.py aviso`), y la otra lo ve al
   abrir (`consultar.py --avisos X`). Si dos vías dependen mucho una de otra, un documento de enlace
   (`ENLACE_X_Y.md`) que **se lee entero al abrir cualquiera de las dos**.

---

## 10 · La siguiente sesión, preparada

**El problema**: una sesión acaba con «lo siguiente es arreglar X». La próxima tiene que redescubrir qué
era X, dónde estaba, qué se había descartado y cómo se comprueba. Y si la próxima la hace el modelo
barato, lo redescubre peor.

**La regla**: la sesión que cierra **deja la siguiente como una receta cerrada**, lista para abrir.

**Una receta está lista cuando:**

- **Dice qué hacer, con qué modelo y qué NO hacer.**
- **Todo lo que da por bueno se ha comprobado al prepararla, desde donde se va a usar**: cada dirección
  abierta y con su texto, cada fichero existe, cada orden que escribe tiene su ensayo en seco hecho.
- **Cada orden que escribe va seguida de su comprobación**: qué mirar y qué cuenta como bien. *«Creo que
  todo correcto»* no es una medida.
- **Dice contra qué se contrasta cada cifra.** Sin eso, el modelo barato mide bien y concluye de más:
  presenta un número sorprendente sin abrirlo contra otra fuente.
- **Dice cuánto tarda cada orden larga y qué imprime**, para que una espera no parezca un cuelgue.
- **Lleva su regla de parada**: si una orden sale distinto de lo esperado, el agente **no improvisa un
  arreglo** ni abre un frente que la receta no trae. Anota qué orden, qué salió y qué esperaba, y cierra
  con un `⏭️ [Opus]`.

**Y se deja preparada después del commit** (la nueva parte de él). Si el entorno permite dejarla como
tarea lista para arrancar, mejor que como texto. ⛔ **En cuanto la nueva arranca, la vieja se archiva**,
sin esperar su informe ni seguir cruzando mensajes: una sesión larga viva **relee todo su historial en
cada turno**, y cada mensaje que recibe se paga entero.
