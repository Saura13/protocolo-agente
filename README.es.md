# Protocolo de agente

**Un método para llevar un proyecto largo con un agente de IA sin que se pierda entre sesiones.**

*[🇬🇧 Read it in English](README.md)*

No es una librería ni una herramienta. Son **seis documentos y nueve programas** que resuelven un
problema concreto: cuando un proyecto dura meses, cada sesión con el agente empieza a ciegas. Se le
vuelve a explicar todo, se le paga el contexto entero, y aun así toma decisiones que contradicen las
de la semana pasada.

Este protocolo se escribió trabajando, no en abstracto. Nació de un proyecto real de un año, y cada
regla de aquí existe porque algo se rompió antes.

---

## El problema, en una frase

> Un agente no tiene memoria entre sesiones. Lo único que sabe es lo que lee al arrancar.
> **Así que lo que lee al arrancar es el diseño más importante del proyecto.**

De ahí salen las tres decisiones que gobiernan todo lo demás:

1. **El arranque es un presupuesto, no un saludo.** Cada línea que el agente lee al empezar se paga
   en **todas** las sesiones, para siempre. Un documento de 400 líneas que se abre "por si acaso"
   cuesta más que el trabajo que iba a hacer.
2. **Cada documento tiene una función y solo una.** Qué hay abierto, dónde estamos, qué pasó, qué
   está roto, qué se aprendió. En cuanto dos documentos cuentan lo mismo, uno de los dos miente —
   y no sabes cuál.
3. **Los mapas se generan, no se escriben.** Un índice mantenido a mano apunta a líneas equivocadas
   en cuanto alguien mueve una función. Un índice que miente es peor que no tener índice.

---

## Qué hay aquí

| Fichero | Qué resuelve |
|:---|:---|
| **[`AGENTS.md`](AGENTS.md)** | La plantilla del mapa de arranque. **Es la pieza central**: lo que el agente lee al abrir cada sesión |
| **[`CLAUDE.md`](CLAUDE.md)** | Un puntero de una línea a `AGENTS.md`, porque Claude Code no lee `AGENTS.md` de forma nativa |
| **[`PROTOCOLO_SESION.md`](PROTOCOLO_SESION.md)** | Cómo se abre, se lleva y se cierra una sesión. La lista de comprobación antes de cerrar |
| **[`LOS_DOCUMENTOS.md`](LOS_DOCUMENTOS.md)** | Qué función fija tiene cada documento, su techo de líneas y qué NO va en él |
| **[`CRITERIOS.md`](CRITERIOS.md)** | Las lecciones que sobreviven al proyecto. Sobre todo: cómo se mide algo sin engañarse |
| **[`herramientas/`](herramientas/)** | Los programas: tres generan mapas, uno mide lo que cuesta cada sesión, otro **comprueba que se puede cerrar** y cuatro **dejan preguntar a los documentos en vez de leerlos enteros** (`indice.py`, `consultar.py`, `apuntar.py`, `generar_vias.py`) |
| **[`plantillas/`](plantillas/)** | Los documentos vacíos, listos para copiar |

---

## Empezar

```bash
git clone <este-repositorio> && cd protocolo-agente
```

1. Copia `AGENTS.md`, `CLAUDE.md` y la carpeta `plantillas/` a la raíz de tu proyecto.
2. Rellena los `<marcadores>` de `AGENTS.md`. Son pocos a propósito.
3. Copia `herramientas/` y crea tu `protocolo.config.json` (hay un ejemplo dentro).
4. Genera el primer mapa de código:

```bash
python herramientas/generar_mapa_codigo.py
```

5. Antes de cerrar la sesión, comprueba que se puede:

```bash
python herramientas/comprobar_cierre.py
```

6. Y mide lo que costó:

```bash
python herramientas/medir_cuota_sesion.py
```

7. Cuando los documentos crezcan, deja de leerlos enteros. Genera el índice y pregúntale:

```bash
python herramientas/indice.py                       # genera el índice SQLite (sin dependencias)
python herramientas/consultar.py "qué toca a X"     # diez trozos con fichero:línea
python herramientas/apuntar.py                      # escribe diario y avisos, bajo cerrojo
python herramientas/generar_vias.py                 # genera la hoja de vías desde una ficha por vía
```

Todo se configura en `protocolo.config.json` (`indice`, `vias`, `avisos`, techos en caracteres en `cierre`).

8. **Antes de escribir una herramienta nueva, pregunta si ya existe** (`consultar.py` y `MAPA_HERRAMIENTAS.md`).
   Cada herramienta lleva su **ficha** en el docstring —`Contesta:` / `Toca:` / `Necesita:`, una línea cada una— y
   `generar_mapa_herramientas.py` la recoge, añade lo que el código enseña (red, consola remota, modelo de
   lenguaje, base de datos, qué otras importa) y **avisa si la ficha dice «solo lee» y el código escribe**. Lo que
   se aparta va a un estante sin renombrarlo: `_usados/AAAA-MM/`, `datos/` y `comun/` (detalle en `AGENTS.md`).

Ese último número es el que ordena todo lo demás. **Antes de optimizar nada, mide qué fracción del
problema es.** En el proyecto de origen, el arranque costaba 61.101 tokens y la intuición decía que
sobraba documentación — pero al medirlo, **el 81% era configuración del entorno** y los documentos
propios eran el 19%. Podar documentos habría atacado un quinto del problema.

---

## Sobre qué agentes funciona

El contenido vive en **`AGENTS.md`**, el estándar abierto que desde diciembre de 2025 gobierna la
Agentic AI Foundation de la Linux Foundation y que leen más de treinta agentes: OpenAI Codex, GitHub
Copilot, Cursor, Gemini CLI, Google Antigravity, OpenCode, Zed, Windsurf, Aider, Jules, Devin.

**Claude Code es la excepción**: no lee `AGENTS.md` de forma nativa. Por eso este repositorio
incluye un `CLAUDE.md` que **no duplica el contenido**, solo lo importa con una línea.

> ⚠️ **No copies el mismo texto en varios ficheros.** Es la tentación obvia y se pudre sola: a las
> tres semanas no hay dos copias iguales y nadie sabe cuál manda. El contenido va en `AGENTS.md`;
> todo lo demás apunta a él.

---

## Licencia

MIT. Úsalo, córtalo y cámbialo.
