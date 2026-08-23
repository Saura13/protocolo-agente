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
cinco pasos y ni uno más:

1. **Leer solo el desvío.** Un documento corto (`VIAS_DE_TRABAJO.md`) que dice qué frentes hay
   abiertos, a qué documento ir en cada uno y cuál es el siguiente paso. Nada más.
2. **Preguntar por qué frente se va**, si el usuario no lo ha dicho. No se elige por cuenta propia:
   la elección depende del tiempo que tenga ese día y de qué le aprieta más, y eso no se adivina.
3. **Leer solo la sección del paso que toca.** No el documento entero. El desvío ya ha dicho cuál
   es la sección. 🔑 *Lo que el desvío ya te ha dicho no se vuelve a pagar.*
4. **Comprobar que el sistema responde** con un solo comando.
5. **Responder en menos de 15 líneas** — dónde estamos, siguiente paso, qué está bloqueado — y
   **esperar el visto bueno antes de tocar nada**.

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

---

## 2 · Un solo asunto por sesión

**El problema**: se arregla algo, se ve otra cosa de paso, se tira del hilo, y a las tres horas hay
cuatro cambios a medias, ninguno registrado, y el contexto agotado.

**La regla**: un asunto por sesión. Si el arreglo resulta pequeño, se sigue con el siguiente. Si es
grande o se complica: **registrar, cerrar, y empezar con contexto limpio**.

Tener varios frentes abiertos no autoriza a saltar de uno a otro dentro de la misma sesión.

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

## 5 · El cierre — la lista de comprobación

**No se cierra la sesión hasta que estas seis están hechas:**

1. ¿**Diario** actualizado con el resultado?
2. ¿El **estado** dice cuál es el siguiente paso? (lo lee la siguiente sesión, no tú)
3. ¿El **registro de bugs** refleja el nuevo estado?
4. ¿**Mapa de código regenerado**, si se movió o añadió alguna función?
5. ¿**Commit** hecho, con mensaje que explique **el porqué**?
6. ¿**Verificado** que no se rompió nada?

Y decirlo explícitamente cuando esté: *«esto está registrado, puedes cerrar y retomamos con contexto
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
