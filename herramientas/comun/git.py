# -*- coding: utf-8 -*-
u"""Lo que el protocolo pregunta a git, escrito una vez (16/10/2026).

**Por qué existe**: varios agentes trabajan a la vez, cada uno en **su carpeta** (un *worktree*
de git) y su rama. Lo que cada uno ve en disco es solo lo suyo; lo que tienen **en común** es el
almacén de git (`git rev-parse --git-common-dir`) y la lista de carpetas (`git worktree list`).
Quien tenga que coordinarse con los demás —repartir la letra del día, juntar una rama— pregunta
aquí, no a su carpeta.

Sin git, o fuera de un repositorio, todo devuelve vacío o None: quien llama sigue como antes.
"""
import os
import subprocess


def git(raiz, *args, **kw):
    u"""Corre `git -C raiz args…` y devuelve el resultado (sin lanzar si falla)."""
    try:
        return subprocess.run(["git", "-C", raiz] + list(args), capture_output=True,
                              text=True, encoding="utf-8", errors="replace", **kw)
    except OSError:
        return None


def _salida(r):
    return r.stdout.strip() if r is not None and r.returncode == 0 else None


def almacen_comun(raiz):
    u"""La carpeta que comparten todas las carpetas de trabajo del repositorio, o None."""
    s = _salida(git(raiz, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return os.path.normpath(s) if s else None


def rama_actual(raiz):
    return _salida(git(raiz, "branch", "--show-current")) or None


def carpetas(raiz):
    u"""[(ruta, rama o None)] de cada carpeta de trabajo del repositorio, la principal incluida."""
    s = _salida(git(raiz, "worktree", "list", "--porcelain"))
    if not s:
        return []
    salida, ruta, rama = [], None, None
    for linea in s.splitlines() + [""]:
        if linea.startswith("worktree "):
            ruta, rama = os.path.normpath(linea[9:]), None
        elif linea.startswith("branch refs/heads/"):
            rama = linea[len("branch refs/heads/"):]
        elif not linea.strip() and ruta:
            salida.append((ruta, rama))
            ruta = None
    return salida


def contenido_en(raiz, rama, rel):
    u"""El texto de `rel` tal como está guardado en `rama`, o None si no existe allí."""
    return _salida(git(raiz, "show", "%s:%s" % (rama, rel.replace(os.sep, "/"))))


def existe_rama(raiz, rama):
    r = git(raiz, "rev-parse", "--verify", "--quiet", "refs/heads/" + rama)
    return r is not None and r.returncode == 0
