# -*- coding: utf-8 -*-
u"""Escribir en el diario y dejar avisos, con su formato y sin que dos agentes se pisen.

    python apuntar.py entrada  --titulo "Vía A: BUG-040" --modelo Opus --texto intencion.md
    python apuntar.py resultado --letra N --titulo "✅ hecho" --texto resultado.md
    python apuntar.py aviso    --de F --a G --titulo "cambia el formato del libro" --texto aviso.md
    python apuntar.py visto    --linea 42        (el aviso de esa línea pasa de ⏳ a ✅)

El texto va en un fichero (o `-` para leerlo de la entrada estándar), o corto con --frase.
🔑 *En fichero y no en la línea de órdenes*: las comillas invertidas y las barras se las come el
terminal por el camino.

Lo que resuelve:
- **La letra del día la da el diario, no el agente.** Dos sesiones que abren a la vez ya no
  eligen las dos la «N»: bajo el cerrojo se mira cuál es la siguiente libre y se reserva.
  🔑 *Y el diario son todas sus copias*: cada sesión trabaja en su carpeta (worktree) y solo ve
  la suya, así que el 16/10 dos sesiones cogieron las dos la «B». La letra se elige mirando el
  diario de **todas** las carpetas y el de la rama principal, bajo un cerrojo que vive en el
  almacén común de git, el único sitio que todas ven.
- **El resultado va a SU entrada**, no al final del fichero: si otra sesión apuntó después, el
  resultado no queda colgando debajo de la entrada ajena.
- **Nadie escribe a medias**: el fichero se escribe entero a un temporal y luego se cambia.
"""
import argparse
import datetime
import os
import re
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diario                               # noqa: E402
from comun import git as g                  # noqa: E402
from config import cargar                   # noqa: E402
from terreno import SinTerrenoQueMedir      # noqa: E402


def hoy():
    return datetime.date.today().strftime("%d/%m/%Y")


def leer_texto(a):
    if a.frase:
        return a.frase.strip()
    if not a.texto:
        raise SinTerrenoQueMedir(u"falta el texto: --texto FICHERO, --texto - o --frase")
    if a.texto == "-":
        return sys.stdin.read().strip()
    with open(a.texto, encoding="utf-8") as fh:
        return fh.read().strip()


def letras():
    u"""A, B, … Z, AA, AB, … — sin techo."""
    n = 1
    while True:
        for t in _combinaciones(n):
            yield t
        n += 1


def _combinaciones(n):
    if n == 1:
        for c in string.ascii_uppercase:
            yield c
        return
    for p in _combinaciones(n - 1):
        for c in string.ascii_uppercase:
            yield p + c


def letras_del_dia(textos, fecha):
    u"""Las letras ya usadas `fecha` en cualquier forma de cabecera: «15/10/2026 (N)» o «15/10/2026 N»."""
    patron = re.compile(r"^## .*?%s\s*\(?([A-Z]{1,2})\)?(?:\s|$)" % re.escape(fecha), re.M)
    usadas = set()
    for t in textos:
        usadas.update(patron.findall(t))
    return usadas


def copias_ajenas(raiz, cfg, ruta):
    u"""El mismo fichero del diario en las OTRAS carpetas de trabajo y en la rama principal."""
    rel = os.path.relpath(ruta, raiz)
    textos = []
    for carpeta, _ in g.carpetas(raiz):
        if os.path.normcase(carpeta) == os.path.normcase(os.path.normpath(raiz)):
            continue
        otra = os.path.join(carpeta, rel)
        if os.path.isfile(otra):
            textos.append(diario.leer(otra)[0])
    principal = cfg.get("cierre", {}).get("rama_principal", "master")
    guardado = g.contenido_en(raiz, principal, rel)
    if guardado:
        textos.append(guardado)
    return textos


class CerrojoComun(object):
    u"""El cerrojo del diario para todas las carpetas a la vez (en el almacén común de git)."""

    def __init__(self, raiz):
        comun = g.almacen_comun(raiz)
        self.c = diario.Cerrojo(os.path.join(comun, "protocolo-diario")) if comun else None

    def __enter__(self):
        if self.c:
            self.c.__enter__()
        return self

    def __exit__(self, *exc):
        if self.c:
            self.c.__exit__(*exc)


def entrada(raiz, cfg, a):
    fmt = diario.formato(cfg)
    ruta = diario.actual(raiz, cfg, crear=True)
    cuerpo = leer_texto(a)
    fecha = hoy()
    with CerrojoComun(raiz), diario.Cerrojo(ruta):
        texto, salto = diario.leer(ruta)
        usadas = letras_del_dia([texto] + copias_ajenas(raiz, cfg, ruta), fecha)
        letra = next(l for l in letras() if l not in usadas)
        titulo = a.titulo + (u" (%s)" % a.modelo if a.modelo else u"")
        cabecera = fmt["cabecera"].format(fecha=fecha, letra=letra, titulo=titulo)
        nuevo = texto.rstrip("\n") + u"\n\n" + cabecera + u"\n" + cuerpo + u"\n"
        diario.escribir(ruta, nuevo, salto)
    print(u"✓ entrada %s %s en %s" % (fecha, letra, os.path.relpath(ruta, raiz)))
    print(u"  para el resultado: python apuntar.py resultado --letra %s ..." % letra)
    return 0


def resultado(raiz, cfg, a):
    fmt = diario.formato(cfg)
    fecha = a.fecha or hoy()
    cuerpo = leer_texto(a)
    cab = re.compile(r"^## .*?%s\s*\(?%s\)?(?:\s|$)" % (re.escape(fecha), re.escape(a.letra)))
    for ruta in reversed(diario.ficheros(raiz, cfg)):
        with diario.Cerrojo(ruta):
            texto, salto = diario.leer(ruta)
            lineas = texto.split("\n")
            ini = next((i for i in range(len(lineas) - 1, -1, -1) if cab.match(lineas[i])), None)
            if ini is None:
                continue
            fin = next((j for j in range(ini + 1, len(lineas))
                        if lineas[j].startswith(fmt["marcador_entrada"])
                        and not lineas[j].startswith(fmt["marcador_resultado"])), len(lineas))
            while fin > ini + 1 and not lineas[fin - 1].strip():
                fin -= 1
            ya = any(l.startswith(fmt["marcador_resultado"]) for l in lineas[ini:fin])
            if ya:
                bloque = [cuerpo]                       # se añade al resultado que ya hay
            else:
                d, m, _ = fecha.split("/")
                bloque = [fmt["resultado"].format(dia="%s/%s" % (d, m), letra=a.letra,
                                                  titulo=a.titulo or u""), cuerpo]
            lineas[fin:fin] = bloque
            diario.escribir(ruta, "\n".join(lineas), salto)
            print(u"✓ resultado %s en la entrada %s %s (%s:%d)"
                  % (u"añadido" if ya else u"escrito", fecha, a.letra,
                     os.path.relpath(ruta, raiz), ini + 1))
            return 0
    raise SinTerrenoQueMedir(u"no hay ninguna entrada %s %s en el diario" % (fecha, a.letra))


def aviso(raiz, cfg, a):
    rel = cfg.get("avisos")
    if not rel:
        raise SinTerrenoQueMedir(u"falta «avisos» en protocolo.config.json (dónde se dejan)")
    ruta = os.path.join(raiz, rel)
    try:                # «x»: solo lo crea el primero; si ya existe, no se toca
        with open(ruta, "x", encoding="utf-8", newline="") as fh:
            fh.write(u"# Avisos entre vías\n\n> Lo que una vía decide y cambia a otra. Se escriben con "
                     u"`apuntar.py aviso` y se leen al abrir la vía de destino con "
                     u"`consultar.py --avisos X`. ⏳ pendiente · ✅ visto.\n")
    except FileExistsError:
        pass
    cuerpo = leer_texto(a)
    with diario.Cerrojo(ruta):
        texto, salto = diario.leer(ruta)
        cab = u"## ⏳ %s · de %s a %s — %s" % (hoy(), a.de, a.a, a.titulo)
        diario.escribir(ruta, texto.rstrip("\n") + u"\n\n" + cab + u"\n" + cuerpo + u"\n", salto)
    print(u"✓ aviso de %s a %s en %s" % (a.de, a.a, rel))
    return 0


def visto(raiz, cfg, a):
    ruta = os.path.join(raiz, cfg.get("avisos", ""))
    with diario.Cerrojo(ruta):
        texto, salto = diario.leer(ruta)
        lineas = texto.split("\n")
        i = a.linea - 1
        if not (0 <= i < len(lineas)) or not lineas[i].startswith(u"## ⏳"):
            raise SinTerrenoQueMedir(u"la línea %d no es un aviso pendiente" % a.linea)
        lineas[i] = lineas[i].replace(u"## ⏳", u"## ✅", 1)
        diario.escribir(ruta, "\n".join(lineas), salto)
    print(u"✓ visto: %s" % lineas[i])
    return 0


def main():
    ap = argparse.ArgumentParser(description=u"Escribir en el diario y dejar avisos.")
    sub = ap.add_subparsers(dest="que", required=True)

    def con_texto(p):
        p.add_argument("--texto", help=u"fichero con el texto, o - para la entrada estándar")
        p.add_argument("--frase", help=u"texto corto, sin comillas raras")

    p = sub.add_parser("entrada", help=u"abrir la entrada de esta sesión (la intención)")
    p.add_argument("--titulo", required=True)
    p.add_argument("--modelo")
    con_texto(p)
    p = sub.add_parser("resultado", help=u"cerrar la entrada con su resultado")
    p.add_argument("--letra", required=True)
    p.add_argument("--fecha", help=u"dd/mm/aaaa; por defecto hoy")
    p.add_argument("--titulo", default="")
    con_texto(p)
    p = sub.add_parser("aviso", help=u"dejar un aviso para otra vía")
    p.add_argument("--de", required=True)
    p.add_argument("--a", required=True)
    p.add_argument("--titulo", required=True)
    con_texto(p)
    p = sub.add_parser("visto", help=u"marcar un aviso como visto")
    p.add_argument("--linea", type=int, required=True)

    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        raiz, cfg = cargar()
        return {"entrada": entrada, "resultado": resultado, "aviso": aviso,
                "visto": visto}[a.que](raiz, cfg, a)
    except SinTerrenoQueMedir as e:
        print(u"✗ %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
