# Las herramientas: una biblioteca con sus estantes

> Copia este fichero como `LEEME.md` dentro de tu carpeta de herramientas. El porqué de cada regla
> está en `LA_BIBLIOTECA.md` del protocolo.

**Los nombres no se mueven**: cada herramienta se cita por su nombre en el diario y en los bugs, así
que lo que se aparta va a un estante, no se renombra.

| Estante | Qué va ahí | Regla |
|:---|:---|:---|
| `herramientas/` | Las herramientas que se vuelven a correr | Cada una con su **ficha** en el docstring (`Contesta:` / `Toca:` / `Necesita:`). `MAPA_HERRAMIENTAS.md` la recoge y la comprueba contra el código |
| `comun/` | El código que estaba copiado en varias | Se reutiliza antes de crear. Cada pieza, probada contra la copia que sustituye. **Lo que corre también en otra máquina no la importa** |
| `datos/` | Lo que las herramientas leen o escriben (decisiones, juicios, volcados) | No son herramientas: el mapa no las mira |
| `_usados/AAAA-MM/` | Guiones de un solo uso, ya corridos, y sus restos | Se guardan como constancia. **No se corren desde ahí**: sus rutas eran las de su día |
| `<copia>/` | Copia local del código que corre en otra máquina | Se cambia **aquí** y se despliega con un programa que compara huellas. Allí no se parchea |

**Antes de crear una herramienta**: `python herramientas/consultar.py <palabras>` y `MAPA_HERRAMIENTAS.md`.
Si ya hay una que contesta, se usa o se amplía.
