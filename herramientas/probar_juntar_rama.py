#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""¿Varios agentes pueden apuntar y juntar a la vez sin perder nada?

Contesta: ¿`apuntar.py` reparte letras distintas a dos carpetas a la vez, y `juntar_rama.py` suma lo que
debe sumar, regenera lo generado y frena —sin tocar nada— en todo lo demás?
Toca: solo una copia aparte, en una carpeta temporal que se borra al acabar; el repositorio de verdad no se toca.
Necesita: git.

Monta un repositorio **de juguete**, con su propia configuración, dos fichas de vías, un diario y los
avisos —no copia nada del proyecto salvo las herramientas—, y lo pasa por los casos que se vieron el 16/10/2026:

  1. dos `entrada` a la vez en dos carpetas → letras distintas;
  2. dos ramas con ficha, hoja de vías, aviso y resultado → todo en la principal y la hoja al día;
  3. choque de verdad en una ficha → frena y la rama queda como estaba;
  4. choque solo en un documento generado → lo regenera y junta;
  5. cambios sin guardar → frena;
  6. la misma letra en dos ramas → frena;
  7. un aviso marcado visto mientras otra rama añade otro → los dos bien.

Sale con código 1 si algún caso falla.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import threading

AQUI = os.path.dirname(os.path.abspath(__file__))
DOC = "docs"
# Lo que el juguete necesita de las herramientas: las del protocolo y lo que importan. Nada más viaja.
NECESARIAS = ["apuntar.py", "juntar_rama.py", "generar_vias.py", "diario.py", "config.py", "terreno.py",
              os.path.join("comun", "__init__.py"), os.path.join("comun", "git.py")]
CONFIG = u"""{
  "cierre": {"diario": "docs/diario", "rama_principal": "master"},
  "vias": {"fichas": "docs/vias", "salida": "docs/VIAS_DE_TRABAJO.md", "techo_ficha": 2000},
  "avisos": "docs/AVISOS_ENTRE_VIAS.md",
  "generados": {"docs/VIAS_DE_TRABAJO.md": "herramientas/generar_vias.py"}
}
"""
ATRIBUTOS = u"docs/diario/*.md merge=union\ndocs/AVISOS_ENTRE_VIAS.md merge=union\n"
fallos = []


def corre(cwd, *orden, **kw):
    r = subprocess.run(list(orden), cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", **kw)
    return r.returncode, r.stdout + r.stderr


def git(cwd, *args):
    return corre(cwd, "git", "-c", "core.autocrlf=false", *args)


def herramienta(cwd, nombre, *args):
    return corre(cwd, sys.executable, os.path.join("herramientas", nombre), *args)


def caso(nombre, bien, detalle=""):
    print(u"%s %s%s" % (u"✓" if bien else u"✗", nombre, u"" if bien else u"\n    " + detalle.replace("\n", "\n    ")))
    if not bien:
        fallos.append(nombre)


def editar(ruta, antes, despues):
    with open(ruta, encoding="utf-8") as fh:
        s = fh.read()
    assert antes in s, (ruta, antes)
    with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(s.replace(antes, despues, 1))


def anadir(ruta, texto):
    with open(ruta, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(texto)


def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(texto)


def montar(base):
    r = os.path.join(base, "r")
    for rel in NECESARIAS:
        destino = os.path.join(r, "herramientas", rel)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        shutil.copy(os.path.join(AQUI, rel), destino)
    escribir(os.path.join(r, "protocolo.config.json"), CONFIG)
    escribir(os.path.join(r, ".gitattributes"), ATRIBUTOS)
    escribir(os.path.join(r, DOC, "vias", "10_uno.md"), u"## Vía uno\n\nAlgo.\n")
    escribir(os.path.join(r, DOC, "vias", "20_dos.md"), u"## Vía dos\n\nAlgo.\n")
    escribir(os.path.join(r, DOC, "AVISOS_ENTRE_VIAS.md"), u"# Avisos entre vías\n")
    os.makedirs(os.path.join(r, DOC, "diario"))
    git(base, "init", "-q", "-b", "master", r)
    git(r, "config", "user.name", "prueba")
    git(r, "config", "user.email", "prueba@prueba")
    herramienta(r, "generar_vias.py")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "base")
    return r


def carpeta(r, nombre):
    ruta = os.path.join(os.path.dirname(r), nombre)
    git(r, "worktree", "add", "-q", ruta, "-b", "p" + nombre)
    return ruta


def guardar(c, msg):
    git(c, "add", "-A")
    git(c, "commit", "-qm", msg)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    base = tempfile.mkdtemp(prefix="juntar_")
    try:
        r = montar(base)
        avisos = os.path.join(DOC, "AVISOS_ENTRE_VIAS.md")
        f_ficha, v_ficha = os.path.join(DOC, "vias", "10_uno.md"), os.path.join(DOC, "vias", "20_dos.md")

        # 1 · dos entradas a la vez
        a, b = carpeta(r, "a"), carpeta(r, "b")
        salidas = {}
        hilos = [threading.Thread(target=lambda c=c: salidas.__setitem__(
            c, herramienta(c, "apuntar.py", "entrada", "--titulo", "prueba", "--frase", "x")[1])) for c in (a, b)]
        [h.start() for h in hilos]
        [h.join() for h in hilos]
        letras = [s.split()[3] if len(s.split()) > 3 else s for s in salidas.values()]
        caso(u"1 · dos entradas a la vez, letras distintas (%s)" % u" y ".join(letras),
             len(set(letras)) == 2, "\n".join(salidas.values()))

        # 2 · dos ramas que tocan de todo
        for c, ficha, letra in ((a, f_ficha, letras[list(salidas).index(a)]), (b, v_ficha, letras[list(salidas).index(b)])):
            anadir(os.path.join(c, ficha), u"Línea de %s.\n" % os.path.basename(c))
            herramienta(c, "generar_vias.py")
            herramienta(c, "apuntar.py", "aviso", "--de", "X", "--a", "Y", "--titulo", "aviso " + os.path.basename(c), "--frase", "y")
            herramienta(c, "apuntar.py", "resultado", "--letra", letra, "--frase", "hecho " + os.path.basename(c))
            guardar(c, os.path.basename(c))
        ra = herramienta(a, "juntar_rama.py", "--juntar")
        rb = herramienta(b, "juntar_rama.py", "--juntar")
        diario_r = "".join(open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(r, DOC, "diario", "*.md")))
        av = open(os.path.join(r, avisos), encoding="utf-8").read()
        al_dia = herramienta(r, "generar_vias.py", "--comprobar")[0] == 0
        bien = (ra[0] == 0 and rb[0] == 0 and "hecho a" in diario_r and "hecho b" in diario_r
                and "aviso a" in av and "aviso b" in av and al_dia and "<<<<<<<" not in diario_r + av)
        caso(u"2 · dos ramas con ficha, hoja, aviso y resultado: todo en la principal", bien, ra[1] + rb[1])

        # 3 · choque de verdad en una ficha
        e, f = carpeta(r, "e"), carpeta(r, "f")
        for c in (e, f):
            editar(os.path.join(c, f_ficha), u"Línea de a.", u"Línea cambiada por %s." % os.path.basename(c))
            herramienta(c, "generar_vias.py")
            guardar(c, os.path.basename(c))
        herramienta(e, "juntar_rama.py", "--juntar")
        antes = git(f, "rev-parse", "HEAD")[1]
        rf = herramienta(f, "juntar_rama.py", "--juntar")
        limpio = git(f, "status", "--porcelain")[1].strip() == "" and git(f, "rev-parse", "HEAD")[1] == antes
        caso(u"3 · choque en una ficha: frena y la rama queda igual", rf[0] == 1 and limpio and "A MANO" in rf[1], rf[1])

        # 4 · choque solo en la hoja generada
        g_, h = carpeta(r, "g"), carpeta(r, "h")
        for c in (g_, h):
            editar(os.path.join(c, DOC, "VIAS_DE_TRABAJO.md"), u"# ", u"# [a mano %s] " % os.path.basename(c))
            guardar(c, os.path.basename(c))
        herramienta(g_, "juntar_rama.py", "--juntar")
        rh = herramienta(h, "juntar_rama.py", "--juntar")
        caso(u"4 · choque solo en lo generado: lo regenera y junta",
             rh[0] == 0 and "regenerado" in rh[1] and herramienta(r, "generar_vias.py", "--comprobar")[0] == 0, rh[1])

        # 5 · cambios sin guardar
        anadir(os.path.join(h, v_ficha), u"sin guardar\n")
        rs = herramienta(h, "juntar_rama.py", "--juntar")
        caso(u"5 · cambios sin guardar: frena", rs[0] == 1 and "sin guardar" in rs[1], rs[1])
        git(h, "checkout", "-q", "--", v_ficha)

        # 6 · la misma letra en dos ramas
        i, j = carpeta(r, "i"), carpeta(r, "j")
        mes = sorted(glob.glob(os.path.join(r, DOC, "diario", "*.md")))[-1]
        for c in (i, j):
            anadir(os.path.join(c, os.path.relpath(mes, r)),
                   u"\n## 📅 01/01/2001 (Z) — misma letra desde %s\nalgo\n" % os.path.basename(c))
            guardar(c, os.path.basename(c))
        herramienta(i, "juntar_rama.py", "--juntar")
        antes = git(j, "rev-parse", "HEAD")[1]
        rj = herramienta(j, "juntar_rama.py", "--juntar")
        caso(u"6 · la misma letra en dos ramas: frena y no cambia nada",
             rj[0] == 1 and "2 veces" in rj[1] and git(j, "rev-parse", "HEAD")[1] == antes, rj[1])

        # 7 · visto en una rama, aviso nuevo en otra
        k, l_ = carpeta(r, "k"), carpeta(r, "l")
        lineas = open(os.path.join(k, avisos), encoding="utf-8").read().split("\n")
        n = next(x for x, t in enumerate(lineas, 1) if t.startswith(u"## ⏳") and "aviso a" in t)
        herramienta(k, "apuntar.py", "visto", "--linea", str(n))
        guardar(k, "k")
        herramienta(l_, "apuntar.py", "aviso", "--de", "L", "--a", "Y", "--titulo", "aviso l", "--frase", "z")
        guardar(l_, "l")
        herramienta(k, "juntar_rama.py", "--juntar")
        rl = herramienta(l_, "juntar_rama.py", "--juntar")
        av = open(os.path.join(r, avisos), encoding="utf-8").read()
        caso(u"7 · un aviso visto y otro nuevo a la vez: los dos bien",
             rl[0] == 0 and u"## ✅" in av and "aviso l" in av and not any(
                 t.startswith(u"## ⏳") and "aviso a" in t for t in av.split("\n")), rl[1])
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print(u"\n%s" % (u"✓ todo bien" if not fallos else u"✗ %d caso(s) fallan" % len(fallos)))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
