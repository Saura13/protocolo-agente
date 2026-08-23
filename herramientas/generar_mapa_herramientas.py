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

⚠️ El veredicto es **conservador y aproximado**: detecta las formas habituales de escribir, borrar,
subir y ejecutar. Un script marcado como «solo lee» que haga algo raro por vías indirectas se le
escaparía. Sirve para decidir cuál abrir, no como permiso para ejecutar a ciegas.

Uso:
    python herramientas/generar_mapa_herramientas.py
"""
import ast
import os
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


def resumen(arbol):
    u"""La primera frase de la docstring: qué pregunta contesta esta herramienta."""
    doc = ast.get_docstring(arbol) or ""
    if not doc.strip():
        return ""
    primera = doc.strip().split("\n\n")[0].replace("\n", " ").strip()
    return primera[:200] + ("…" if len(primera) > 200 else "")


def main():
    raiz, cfg = cargar(os.getcwd())
    carpeta_rel = exigir(cfg, "herramientas", u"saber qué carpeta contiene las herramientas")
    salida_dir = exigir(cfg, "salida", u"saber dónde escribir el mapa")
    carpeta = exigir_raiz(os.path.join(raiz, carpeta_rel), u"la carpeta de herramientas")
    salida = os.path.join(raiz, salida_dir, "MAPA_HERRAMIENTAS.md")

    filas, sin_documentar = [], []
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
        filas.append({
            "fichero": entrada,
            "que_hace": que_hace or "*(sin docstring — no se sabe qué hace)*",
            "efecto": ", ".join(motivos) if motivos else "**solo lee**",
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

    partes.append("## Solo leen — seguras de correr (%d)\n\n" % len(solo_leen))
    partes.append("| Herramienta | Qué pregunta contesta |\n|:---|:---|\n")
    for f in solo_leen:
        partes.append("| `%s` | %s |\n" % (f["fichero"], f["que_hace"]))

    partes.append("\n## Cambian algo — mirar antes de correr (%d)\n\n" % len(tocan))
    partes.append("| Herramienta | Qué pregunta contesta | Al correrla |\n|:---|:---|:---|\n")
    for f in tocan:
        partes.append("| `%s` | %s | %s |\n" % (f["fichero"], f["que_hace"], f["efecto"]))

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
