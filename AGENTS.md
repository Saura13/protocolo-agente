# Mapa de trabajo — <NOMBRE DEL PROYECTO>

> **Este fichero se carga solo al abrir cada sesión.** Es el mapa inviolable.
> Es corto a propósito: **cada línea de aquí se paga en todas las sesiones, para siempre.**
> No añadir nada que solo haga falta a veces — eso va a los documentos enlazados.
>
> 🎯 **Techo: 200 líneas.** Si se pasa, se poda antes de trabajar.

---

## 🔑 Orden rápida: «retomamos \<proyecto\>»

Cuando el usuario escriba eso, hacer **exactamente esto y nada más**:

1. Leer `VIAS_DE_TRABAJO.md` (qué frentes hay abiertos). Es corto **y tiene que seguir siéndolo**:
   es un desvío a cada vía, no un registro.
2. **Saber por qué vía se va.** Si el usuario la dijo, esa. **Si no la dijo, preguntárselo** —
   depende de su prioridad y del tiempo que tenga ese día, y eso no se adivina.
3. Del documento de esa vía, leer **solo la sección del paso que toca** — `VIAS_DE_TRABAJO.md` ya
   ha dicho cuál es —, **no el documento entero**. Y del diario, la última entrada **desde su
   `### RESULTADO`**; solo si esa entrada no tiene RESULTADO (sesión cortada a medias) se lee
   entera. 🔑 *Lo que la vía ya te ha dicho no se vuelve a pagar.*
4. Comprobar que el sistema responde: `<comando de vida: un ping, un docker ps, un curl>`
5. Responder en **menos de 15 líneas**: dónde estamos, cuál es el siguiente paso, qué está
   bloqueado. Y **esperar el visto bueno** antes de tocar nada.

No leer nada más en ese arranque. Nada de auditorías, planes ni código: eso se abre **después**, y
solo lo que pida la tarea concreta.

⛔ **No leer el documento de la otra vía.** Abrir 400 líneas para trabajar en otro frente se paga
entero y no aporta nada.

---

## ⛔ Reglas inviolables

1. **Un solo asunto por sesión.** Si el arreglo es pequeño, se sigue con el siguiente. Si es grande
   o se complica: registrar, cerrar, y empezar con contexto limpio.
2. **Criterios generales, nunca listas de casos.** Si una solución enumera nombres de ficheros,
   URLs o valores concretos, está mal aunque funcione hoy. Una lista de casos puede estar
   equivocada **entera** y parecer que funciona.
3. **Registrar al empezar, no al terminar.** La entrada del diario se escribe **antes** de trabajar.
   Si la sesión se agota a mitad, la siguiente encuentra la intención.
4. **Nada se toca en \<el entorno real\> sin avisar antes.** \<Por qué: quién lo usa y para qué.\>
5. **\<La regla de seguridad propia del proyecto.\>** \<Ej.: el repositorio es local porque hay
   credenciales dentro de ficheros de código; no sube a ningún remoto hasta rotarlas.\>
6. **\<Quién es el usuario y cómo hablarle.\>** \<Ej.: no es desarrollador: lenguaje claro, sin
   jerga, y avisar del riesgo antes de proponer un cambio.\>

---

## 📉 Economía de contexto — qué abrir y qué no

👉 **La cuota no se estima, se lee**: `python herramientas/medir_cuota_sesion.py` saca del registro
de la sesión qué costó el arranque y dónde se fue el gasto. **Solo lee, no toca nada.**

🔑 **Antes de podar, medir qué fracción del problema son los documentos.** Suele ser menos de lo que
parece: el prefijo del entorno (herramientas, reglas, memoria) puede ser la mayor parte, y contra
eso podar documentación no hace nada.

**Nunca abrir enteros** (envenenan el contexto sin aportar):

| Ruta | Por qué |
|:---|:---|
| `<carpeta de material en bruto>` | Entrada, no código |
| `<carpeta de salida / artefactos>` | Producto ya fabricado |
| `<archivo histórico / scripts desechables>` | Solo si se busca algo histórico concreto |
| `**/node_modules/`, `**/venv/` | Dependencias |
| `**/*_output.txt` | Salidas de pruebas manuales |

**Ficheros grandes: leer por trozos, nunca enteros.**

👉 **Consultar primero `MAPA_CODIGO.md`**: dice en qué líneas exactas vive cada función y cada ruta
de la API. Se va directo con lectura por `offset/limit`, sin buscar antes.

| Fichero | Líneas |
|:---|---:|
| `<el fichero más grande>` | `<n>` |

El mapa **se genera, no se escribe**. Si el código cambió, regenerarlo antes de fiarse:

```bash
python herramientas/generar_mapa_codigo.py
```

**Regenerarlo siempre que se muevan o añadan funciones**, y desde luego antes de cerrar sesión.
⛔ **Nunca editarlo a mano**: un índice mantenido a mano acaba apuntando a líneas equivocadas, y un
índice que miente es peor que ninguno.

**Qué abrir según la tarea:**

| Si la tarea es… | Abrir | Nota |
|:---|:---|:---|
| `<tipo de tarea frecuente>` | `<documento>` + `<rango de código>` | |
| Un bug conocido | `REGISTRO_BUGS.md` + el rango citado en el bug | |
| Planificar | `<el plan vigente>` | |
| Saber qué corre dónde | `ESTADO_ACTUAL.md` | |

---

## 🔄 Protocolo de sesión

**Mientras se trabaja — sin partes por el camino.** Se encadena el trabajo y se da **un** informe al
final. Sí se interrumpe para **una decisión del usuario**, **un riesgo antes de correrlo** o **un
hallazgo que cambia el plan**. 🔑 *El coste de releer crece con el cuadrado de los turnos*: un parte
de situación no cuesta lo que ocupa, sino eso multiplicado por todos los turnos que vengan después.

**Al empezar un trabajo:**
1. Anotar la intención en `DIARIO.md` (2-3 líneas: qué y por qué).
2. Confirmar el objetivo con el usuario antes de tocar código.

**Al terminar, antes de cerrar** — primero se corre, y luego se mira lo que el programa
no puede juzgar:

```bash
python herramientas/comprobar_cierre.py
```

1. ¿Diario actualizado con el **resultado**?
2. ¿`ESTADO_ACTUAL.md` dice cuál es el siguiente paso?
3. ¿`REGISTRO_BUGS.md` refleja el nuevo estado del bug **que se traía**?
4. ¿Y **lo roto que apareció de paso**, anotado ahí como 🔴 sin diagnosticar?
5. ¿**Mapa de código regenerado**, si se movió o añadió alguna función?
6. ¿Commit hecho, con mensaje que explique **el porqué**?
7. ¿Verificado que no se rompió nada?

Si algo de esto falta, **no se cierra la sesión todavía**.
🔑 *Una regla que depende de que alguien la teclee no es una regla*: los puntos 1, 5 y 6 los
comprueba `comprobar_cierre.py`; los demás hay que mirarlos. La tabla de qué se actualiza y
dónde se apunta está en `PROTOCOLO_SESION.md` §5.

**Cuándo pedir que se cierre la sesión**: cuando el asunto esté terminado y registrado, o cuando se
vea que va a alargarse. Decirlo explícitamente: *«esto está registrado, puedes cerrar y retomamos
con contexto limpio»*.

---

## 🗺️ Dónde vive cada cosa

| Documento | Para qué |
|:---|:---|
| `VIAS_DE_TRABAJO.md` | **El desvío**: qué frentes hay abiertos y el siguiente paso de cada uno. Se lee **entero** al arrancar. ⛔ Techo de 120 líneas |
| `ESTADO_ACTUAL.md` | **Dónde estamos.** Qué corre, qué se está haciendo, qué sigue. ⛔ Techo de 400 líneas |
| `DIARIO.md` | **Qué pasó.** Una entrada por sesión, con su INTENCIÓN y su RESULTADO |
| `REGISTRO_BUGS.md` | **Qué está roto.** Síntoma → causa → solución |
| `CRITERIOS.md` | **Lo que no se vuelve a razonar.** Lo que sobrevive a este proyecto |
| `MAPA_CODIGO.md` | **Dónde está cada cosa.** Función → líneas exactas. **Generado** |
| `MAPA_HERRAMIENTAS.md` | **Qué pregunta contesta cada herramienta** y si toca algo al correrla. **Generado** |

Detalle de la función de cada uno: `LOS_DOCUMENTOS.md`.

---

## 🖥️ El sistema en una tabla

\<Dónde corre esto realmente. **Si no es en la máquina del agente, decirlo aquí** y decir cómo se
llega.\>

| Servicio | Puerto | Qué hace |
|:---|:---|:---|
| `<nombre>` | `<puerto>` | `<qué hace>` |

⛔ **\<La trampa de medición propia del proyecto.\>** \<Ej.: lo que se mida sobre los artefactos se
mide DENTRO del contenedor, nunca desde el host: la mayoría de las carpetas pertenecen a otro
usuario y una medida desde fuera vería una fracción **sin avisar de que es una fracción**.\>

**\<Qué es el producto y qué es la herramienta.\>** \<Ej.: el producto son los libros, no el
compilador que los fabrica. Un libro mal maquetado es un defecto de producto, no un detalle
interno.\>

---

## 🪜 Las fases del proyecto

**Marcan qué es trabajo y qué es distracción.**

| | Fase | Estado |
|:---:|:---|:---|
| 1 | `<qué significa que esté terminada>` | ⬅️ **Aquí estamos** |
| 2 | `<qué significa que esté terminada>` | Sin planificar |

⛔ **No se empieza una fase hasta que la anterior está perfecta.** Nada de adelantar trabajo de la
fase 2 «ya que estamos por aquí»: eso es lo que ramifica los problemas y deja las dos a medias. Si
algo solo sirve a una fase posterior, **va a la cola sin discutirlo**.
