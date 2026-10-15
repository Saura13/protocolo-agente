#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera MAPA_HERRAMIENTAS.md: qué pregunta contesta cada herramienta y si toca algo al correrla.

Por qué existe: una carpeta con ochenta scripts es inútil sin un índice. El agente —y el humano—
acaban abriendo cinco para encontrar el que servía, o peor: escribiendo uno nuevo que duplica algo
que ya estaba.

**La segunda columna es la importante**: *¿esto solo mira, o cambia algo?* Antes de correr una
herramienta desconocida hay que saberlo, y leerse el script entero para averiguarlo cuesta más que
el trabajo. Aquí se deduce del código, no de lo que diga el comentario.

🔑 Un comentario del código no es una medida: dice lo que alguien creyó el día que lo escribió. El
veredicto de esta tabla sale de leer las llamadas reales del script.

**La ficha de cada herramienta**: qué contesta, qué toca y qué necesita. No se escribe aparte: sale del
docstring y del código. El docstring puede precisarla con tres líneas opcionales, cada una al principio
de su renglón:

    Contesta: ¿…?         si falta, la primera frase del docstring
    Toca: …               lo que escribe, borra o envía, dicho con sus nombres
    Necesita: …           lo que tiene que haber para correrla y el código no enseña

Lo que el código sí enseña se añade solo (red, consola remota, modelo de lenguaje, base de datos y las
otras herramientas que importa). Y se **comprueba**: si la ficha dice que no toca nada y el código
escribe, sale arriba del mapa.

⚠️ El veredicto es **conservador y aproximado**: detecta las formas habituales de escribir, borrar,
subir y ejecutar. Un script marcado como «solo lee» que haga algo raro por vías indirectas se le
escaparía. Sirve para decidir cuál abrir, no como permiso para ejecutar a ciegas.

Uso:
    python herramientas/generar_mapa_herramientas.py
"""
import ast
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import cargar, exigir          # noqa: E402
from terreno import raiz as exigir_raiz    # noqa: E402

# Cómo se reconoce que un script cambia algo. Por FORMA, no por lista de nombres de scripts.
ESCRITURA_MODULO = {
    ("os", "remove"), ("os", "unlink"), ("os", "rmdir"), ("os", "rename"), ("os", "makedirs"),
    ("shutil", "rmtree"), ("shutil", "copy"), ("shutil", "copy2"), ("shutil", "move"),
    ("subprocess", "run"), ("subprocess", "call"), ("subprocess", "Popen"),
    ("subprocess", "check_call"), ("subprocess", "check_output"),
    ("requests", "post"), ("requests", "put"), ("requests", "delete"), ("requests", "patch"),
}
MODOS_ESCRITURA = ("w", "a", "x", "+")


def toca_algo(arbol):
    u"""Devuelve la lista de motivos por los que este script NO es de solo lectura."""
    motivos = set()

    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        f = nodo.func

        # open(ruta, "w") y variantes
        if isinstance(f, ast.Name) and f.id == "open":
            modo = ""
            if len(nodo.args) > 1 and isinstance(nodo.args[1], ast.Constant):
                modo = str(nodo.args[1].value)
            for kw in nodo.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    modo = str(kw.value.value)
            if any(m in modo for m in MODOS_ESCRITURA):
                motivos.add("escribe ficheros")

        # modulo.funcion(...)
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            par = (f.value.id, f.attr)
            if par in ESCRITURA_MODULO:
                if par[0] == "subprocess":
                    motivos.add("ejecuta comandos externos")
                elif par[0] == "requests":
                    motivos.add("hace peticiones que modifican")
                elif f.attr in ("makedirs", "rename"):
                    motivos.add("crea o mueve carpetas")
                else:
                    motivos.add("borra o copia ficheros")
            # .write(...) sobre cualquier cosa
            if f.attr in ("write", "writelines", "writerow", "writerows"):
                motivos.add("escribe ficheros")
            if f.attr in ("commit", "executescript"):
                motivos.add("escribe en base de datos")
            if f.attr == "execute" and nodo.args and isinstance(nodo.args[0], ast.Constant):
                sql = str(nodo.args[0].value).lstrip().upper()
                if sql.startswith(("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE")):
                    motivos.add("escribe en base de datos")

    return sorted(motivos)


CAMPO_DE_FICHA = re.compile(r"^(Contesta|Toca|Necesita):\s*(.+?)\s*$", re.M)
DICE_QUE_NO_TOCA = re.compile(r"(?i)^(solo lee|no toca|no escribe|nada)\b")
MODELO = re.compile(r"(?i)minimax|anthropic|openai|gemini|chat/completions")
RED = {"requests", "urllib", "http", "httpx", "aiohttp", "playwright"}


def ficha_declarada(arbol):
    u"""{campo: texto} de las líneas `Contesta:` / `Toca:` / `Necesita:` del docstring."""
    doc = ast.get_docstring(arbol) or ""
    return {m.group(1).lower(): m.group(2) for m in CAMPO_DE_FICHA.finditer(doc)}


def resumen(arbol):
    u"""Qué pregunta contesta: `Contesta:` si la ficha lo dice; si no, la primera frase de la docstring."""
    declarada = ficha_declarada(arbol).get("contesta")
    if declarada:
        return declarada
    doc = ast.get_docstring(arbol) or ""
    if not doc.strip():
        return ""
    primera = doc.strip().split("\n\n")[0].replace("\n", " ").strip()
    return primera[:200] + ("…" if len(primera) > 200 else "")


def _textos_de_codigo(arbol):
    u"""Los textos que el código usa; no los docstrings, que explican y no se ejecutan."""
    docs = set()
    for n in ast.walk(arbol):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            primero = n.body[0]
            if isinstance(primero, ast.Expr) and isinstance(getattr(primero, "value", None), ast.Constant):
                docs.add(id(primero.value))
    # Tampoco los patrones (`re.compile`) ni lo que solo se compara (`t in ("ssh", …)`): describen
    # qué buscar, no lo que la herramienta hace. Si no, el propio generador «necesitaría» la consola.
    for n in ast.walk(arbol):
        if isinstance(n, ast.Compare) or (isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "compile"):
            docs.update(id(c) for c in ast.walk(n) if isinstance(c, ast.Constant))
    return [n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs]


def necesita(arbol, hermanas):
    u"""Lo que el código enseña que hace falta para correrla. Clases de dependencia, no nombres."""
    importa = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            importa.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            importa.add(n.module)
    textos = _textos_de_codigo(arbol)
    cosas = []
    if any(t in ("ssh", "scp") or t.startswith(("ssh ", "scp ")) for t in textos):
        cosas.append("consola remota")
    if any(i.split(".")[0] in RED for i in importa):
        cosas.append("red")
    if any(MODELO.search(t) for t in textos + sorted(importa)):
        cosas.append("modelo de lenguaje")
    if "sqlite3" in importa:
        cosas.append("base de datos")
    propias = sorted(i for i in importa if i.split(".")[0] in hermanas)
    if propias:
        cosas.append("usa " + ", ".join(propias))
    return cosas


def main():
    raiz, cfg = cargar(os.getcwd())
    carpeta_rel = exigir(cfg, "herramientas", u"saber qué carpeta contiene las herramientas")
    salida_dir = exigir(cfg, "salida", u"saber dónde escribir el mapa")
    carpeta = exigir_raiz(os.path.join(raiz, carpeta_rel), u"la carpeta de herramientas")
    salida = os.path.join(raiz, salida_dir, "MAPA_HERRAMIENTAS.md")

    filas, sin_documentar = [], []
    hermanas = {f[:-3] for f in os.listdir(carpeta) if f.endswith(".py")} | {
        d for d in os.listdir(carpeta) if os.path.isfile(os.path.join(carpeta, d, "__init__.py"))}
    for entrada in sorted(os.listdir(carpeta)):
        if not entrada.endswith(".py") or entrada.startswith("_"):
            continue
        completa = os.path.join(carpeta, entrada)
        try:
            with open(completa, encoding="utf-8", errors="ignore") as fh:
                arbol = ast.parse(fh.read())
        except (SyntaxError, ValueError, OSError):
            continue

        que_hace = resumen(arbol)
        motivos = toca_algo(arbol)
        if not que_hace:
            sin_documentar.append(entrada)
        ficha = ficha_declarada(arbol)
        pide = ([ficha["necesita"]] if ficha.get("necesita") else []) + necesita(arbol, hermanas)
        filas.append({
            "fichero": entrada,
            "que_hace": que_hace or "*(sin docstring — no se sabe qué hace)*",
            "efecto": ", ".join(motivos) if motivos else "**solo lee**",
            "toca_dicho": ficha.get("toca", ""),
            "necesita": "; ".join(pide) or "—",
            "contradice": bool(motivos) and bool(DICE_QUE_NO_TOCA.match(ficha.get("toca", ""))),
        })

    partes = ["# Mapa de herramientas — GENERADO AUTOMÁTICAMENTE\n"]
    partes.append(
        "> ⚠️ **No editar a mano.** Se genera leyendo el código real de `%s/`.\n>\n"
        "> Regenerar con:\n>\n"
        "> ```bash\n> python herramientas/generar_mapa_herramientas.py\n> ```\n" % carpeta_rel
    )
    partes.append(
        "\n**Generado**: %s\n\n"
        "**Para qué sirve**: encontrar la herramienta que ya contesta tu pregunta, en vez de "
        "escribir otra que haga lo mismo.\n\n"
        "**La columna «al correrla»** se deduce de las llamadas reales del script, no de sus "
        "comentarios. Es **conservadora y aproximada**: sirve para decidir cuál abrir, no como "
        "permiso para ejecutar a ciegas.\n\n---\n\n"
        % datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    solo_leen = [f for f in filas if f["efecto"] == "**solo lee**"]
    tocan = [f for f in filas if f["efecto"] != "**solo lee**"]

    contradicen = [f for f in filas if f["contradice"]]
    if contradicen:
        partes.append("## 🔶 Fichas que dicen que no tocan nada y el código sí (%d)\n\n"
                      "O la ficha está mal o el código hace algo que su autor no sabía. Las dos cosas se miran:\n\n"
                      % len(contradicen))
        for f in contradicen:
            partes.append("- `%s`: dice «%s», el código %s\n" % (f["fichero"], f["toca_dicho"], f["efecto"]))
        partes.append("\n")

    partes.append("## Solo leen — seguras de correr (%d)\n\n" % len(solo_leen))
    partes.append("| Herramienta | Qué pregunta contesta | Necesita |\n|:---|:---|:---|\n")
    for f in solo_leen:
        partes.append("| `%s` | %s | %s |\n" % (f["fichero"], f["que_hace"], f["necesita"]))

    partes.append("\n## Cambian algo — mirar antes de correr (%d)\n\n" % len(tocan))
    partes.append("| Herramienta | Qué pregunta contesta | Al correrla | Necesita |\n|:---|:---|:---|:---|\n")
    for f in tocan:
        efecto = f["efecto"] + (" — " + f["toca_dicho"] if f["toca_dicho"] else "")
        partes.append("| `%s` | %s | %s | %s |\n" % (f["fichero"], f["que_hace"], efecto, f["necesita"]))

    if sin_documentar:
        partes.append(
            "\n---\n\n## ⚠️ Sin docstring (%d)\n\n"
            "Estas no dicen qué hacen. Una herramienta sin docstring es una herramienta que "
            "alguien va a reescribir dentro de tres meses porque no supo que existía:\n\n"
            % len(sin_documentar))
        partes.append(", ".join("`%s`" % n for n in sin_documentar) + "\n")

    os.makedirs(os.path.dirname(salida), exist_ok=True)
    with open(salida, "w", encoding="utf-8") as fh:
        fh.write("".join(partes))

    print("[OK] Mapa generado: %s" % os.path.relpath(salida, raiz))
    print("     %d herramientas (%d solo leen, %d cambian algo, %d sin documentar)."
          % (len(filas), len(solo_leen), len(tocan), len(sin_documentar)))


if __name__ == "__main__":
    main()
