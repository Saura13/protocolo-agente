#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera MAPA_CODIGO.md leyendo el código real.

Por qué existe: un índice escrito a mano en la cabecera de un fichero apuntaba a líneas
equivocadas, porque nadie lo actualizaba al mover el código. El agente leía el rango que el
índice decía, encontraba otra cosa y trabajaba sobre suposiciones.

🔑 Un mapa que se genera no puede quedar desactualizado. Uno escrito a mano miente en cuanto
alguien mueve una función, y un índice que miente es peor que no tener índice.

Para qué sirve el mapa: abrir **solo el rango que hace falta** en vez del fichero entero. Con un
fichero de 1.800 líneas, esa es la diferencia entre gastarse el contexto o no.

Uso:
    python herramientas/generar_mapa_codigo.py

Configuración: `protocolo.config.json` en la raíz del proyecto (ver el ejemplo al lado).
"""
import ast
import os
import re
import sys
import warnings
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import cargar, exigir            # noqa: E402
from terreno import raiz as exigir_raiz      # noqa: E402

# Algunos ficheros tienen escapes irregulares en cadenas. Avisan al parsearlos y no aporta nada.
warnings.filterwarnings("ignore", category=SyntaxWarning)


def contar_lineas(ruta):
    try:
        with open(ruta, encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def simbolos_python(ruta):
    """Funciones, clases y rutas HTTP con su rango exacto de líneas (leído con `ast`)."""
    try:
        with open(ruta, encoding="utf-8", errors="ignore") as f:
            arbol = ast.parse(f.read())
    except (SyntaxError, ValueError):
        return []

    encontrados = []
    for nodo in arbol.body:  # solo nivel superior: el detalle interno sobra en un mapa
        if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue

        # Decoradores de ruta: sirve para Flask, FastAPI y cualquier cosa con la misma forma.
        ruta_http = ""
        for deco in getattr(nodo, "decorator_list", []):
            if not isinstance(deco, ast.Call):
                continue
            nombre_deco = getattr(deco.func, "attr", "")
            if nombre_deco in ("get", "post", "put", "delete", "patch", "route", "api_route"):
                if deco.args and isinstance(deco.args[0], ast.Constant):
                    metodo = "ANY" if nombre_deco in ("route", "api_route") else nombre_deco.upper()
                    ruta_http = "`%s %s`" % (metodo, deco.args[0].value)

        encontrados.append({
            "nombre": nodo.name,
            "tipo": "clase" if isinstance(nodo, ast.ClassDef) else "función",
            "inicio": nodo.lineno,
            "fin": getattr(nodo, "end_lineno", nodo.lineno),
            "ruta_http": ruta_http,
        })
    return encontrados


PATRON_JS = re.compile(
    r"^\s*(?:async\s+)?function\s+(\w+)\s*\(|"
    r"^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:function|\()",
)


def simbolos_js(ruta):
    """Funciones JavaScript dentro de un .html o .js, con rango APROXIMADO."""
    try:
        with open(ruta, encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()
    except OSError:
        return []

    crudos = [{"nombre": m.group(1) or m.group(2), "inicio": i}
              for i, linea in enumerate(lineas, 1)
              for m in [PATRON_JS.match(linea)] if m]

    # El final de cada función se aproxima al inicio de la siguiente.
    for j, s in enumerate(crudos):
        s["fin"] = crudos[j + 1]["inicio"] - 1 if j + 1 < len(crudos) else len(lineas)
        s["tipo"] = "función JS"
        s["ruta_http"] = ""
    return crudos


def analizar(ruta_abs, ruta_rel):
    simbolos = simbolos_python(ruta_abs) if ruta_abs.endswith(".py") else simbolos_js(ruta_abs)
    return {"ruta": ruta_rel, "lineas": contar_lineas(ruta_abs), "simbolos": simbolos}


def recoger(raiz, subruta, cfg):
    # El mapa declara sus zonas: si una zona declarada no está, el mapa saldría corto y sin
    # decirlo — que es exactamente el fallo que este generador existe para no repetir.
    base = exigir_raiz(os.path.join(raiz, subruta), u"la zona de código %s" % subruta)
    excluir = tuple(cfg["excluir"])
    exts = tuple(cfg["extensiones"])

    def excluido(p):
        return any(x in p for x in excluir)

    ficheros = []
    # La carpeta de la zona y, un nivel más abajo, las subcarpetas donde suele vivir el frontend.
    carpetas = [base] + [os.path.join(base, d) for d in ("static", "templates", "public")
                         if os.path.isdir(os.path.join(base, d))]
    for carpeta in carpetas:
        for entrada in sorted(os.listdir(carpeta)):
            completa = os.path.join(carpeta, entrada)
            if not os.path.isfile(completa) or excluido(completa):
                continue
            if not entrada.endswith(exts):
                continue
            rel = os.path.relpath(completa, raiz).replace("\\", "/")
            ficheros.append(analizar(completa, rel))
    return ficheros


def main():
    raiz, cfg = cargar(os.getcwd())
    zonas = exigir(cfg, "zonas", u"saber qué carpetas contienen el código que importa")
    salida_dir = exigir(cfg, "salida", u"saber dónde escribir el mapa")
    umbral = cfg["umbral_detalle"]
    salida = os.path.join(raiz, salida_dir, "MAPA_CODIGO.md")

    vistos = set()
    partes = ["# Mapa de código — GENERADO AUTOMÁTICAMENTE\n"]
    partes.append(
        "> ⚠️ **No editar a mano.** Este fichero se genera leyendo el código real.\n"
        "> Cualquier cambio manual se perderá, y volvería a crear el problema que este\n"
        "> generador existe para evitar: un índice que miente.\n>\n"
        "> Regenerar con:\n>\n"
        "> ```bash\n> python herramientas/generar_mapa_codigo.py\n> ```\n"
    )
    partes.append(
        "\n**Generado**: %s\n\n"
        "**Para qué sirve**: abrir solo el rango que hace falta en vez del fichero entero.\n"
        "Leer con `offset`/`limit` sobre los rangos de abajo.\n\n"
        "**Precisión**: en Python los rangos son exactos (se leen con `ast`). En HTML/JavaScript "
        "son **aproximados**: el final de cada función se estima con el inicio de la siguiente, y "
        "alguna constante puede aparecer como si fuera una función. Sirven como puntos de "
        "referencia, no como límites exactos.\n\n---\n" % datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    for zona in zonas:
        titulo, subruta = zona["titulo"], zona["ruta"]
        ficheros = [f for f in recoger(raiz, subruta, cfg) if f["ruta"] not in vistos]
        if not ficheros:
            continue
        for f in ficheros:
            vistos.add(f["ruta"])

        partes.append("\n## %s\n" % titulo)
        grandes = [f for f in ficheros if f["lineas"] >= umbral]
        pequenos = [f for f in ficheros if f["lineas"] < umbral]

        for f in grandes:
            partes.append("\n### `%s` — %s líneas\n" % (f["ruta"], f["lineas"]))
            if not f["simbolos"]:
                partes.append("\n*(sin símbolos de nivel superior detectados)*\n")
                continue
            partes.append("\n| Líneas | Qué es | Nombre | Ruta HTTP |\n|:---|:---|:---|:---|\n")
            for s in f["simbolos"]:
                partes.append("| `%s-%s` | %s | `%s` | %s |\n"
                              % (s["inicio"], s["fin"], s["tipo"], s["nombre"], s["ruta_http"]))

        if pequenos:
            partes.append("\n**Ficheros pequeños** (menos de %d líneas, se abren enteros sin "
                          "problema): " % umbral)
            partes.append(", ".join("`%s` (%d)" % (os.path.basename(f["ruta"]), f["lineas"])
                                    for f in pequenos))
            partes.append("\n")

    os.makedirs(os.path.dirname(salida), exist_ok=True)
    with open(salida, "w", encoding="utf-8") as f:
        f.write("".join(partes))

    print("[OK] Mapa generado: %s" % os.path.relpath(salida, raiz))
    print("     %d ficheros mapeados." % len(vistos))


if __name__ == "__main__":
    main()
