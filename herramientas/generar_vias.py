# -*- coding: utf-8 -*-
u"""La hoja de vías se GENERA de una ficha por vía. Se edita la ficha, no la hoja.

    python generar_vias.py              escribe la hoja y dice cuánto pesa cada ficha
    python generar_vias.py --comprobar  solo mira si la hoja está al día (sale 1 si no)

Por qué: la hoja se lee entera en cada arranque, y escrita a mano engordaba sin que se notara —
un techo de líneas no lo para, porque una línea puede tener veinte mil caracteres—. Con una
ficha por vía:
- cada vía escribe **solo su ficha** (dos sesiones de vías distintas no tocan el mismo fichero);
- el peso se mide **por ficha**: se sabe cuál engorda, no solo que la hoja se pasó;
- 🔑 *lo que se genera no se desincroniza a mano*: el cierre comprueba que la hoja sea la de las fichas.

Configuración («vias» en protocolo.config.json):
    "vias": {"fichas": "docs/vias", "salida": "docs/VIAS_DE_TRABAJO.md", "techo_ficha": 2000}
Las fichas se juntan por orden de nombre (`00_cabecera.md`, `10_…`, `99_…`).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import cargar, exigir          # noqa: E402
from terreno import SinTerrenoQueMedir     # noqa: E402

AVISO = (u"<!-- GENERADO por generar_vias.py desde {fichas}/ — se edita la ficha, no este fichero -->\n")


def fichas(raiz, conf):
    carpeta = os.path.join(raiz, exigir(conf, "fichas", u"saber dónde están las fichas"))
    if not os.path.isdir(carpeta):
        raise SinTerrenoQueMedir(u"no existe la carpeta de fichas: %s" % carpeta)
    nombres = sorted(f for f in os.listdir(carpeta) if f.endswith(".md"))
    if not nombres:
        raise SinTerrenoQueMedir(u"la carpeta de fichas está vacía: %s" % carpeta)
    salida = []
    for n in nombres:
        with open(os.path.join(carpeta, n), encoding="utf-8") as fh:
            salida.append((n, fh.read().replace("\r\n", "\n").strip() + "\n"))
    return salida


def componer(raiz, cfg):
    u"""(texto_de_la_hoja, [(ficha, caracteres)], ruta_de_salida)."""
    conf = exigir(cfg, "vias", u"generar la hoja de vías")
    lista = fichas(raiz, conf)
    texto = AVISO.format(fichas=conf["fichas"]) + u"\n".join(t for _, t in lista)
    return texto, [(n, len(t)) for n, t in lista], os.path.join(raiz, exigir(conf, "salida", u"saber dónde escribir"))


def al_dia(raiz, cfg):
    u"""¿La hoja escrita es la que sale de las fichas? (para comprobar_cierre)."""
    texto, _, ruta = componer(raiz, cfg)
    if not os.path.isfile(ruta):
        return False
    with open(ruta, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n") == texto


def main():
    ap = argparse.ArgumentParser(description=u"Genera la hoja de vías desde sus fichas.")
    ap.add_argument("--comprobar", action="store_true", help=u"no escribe: dice si está al día")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        raiz, cfg = cargar()
        texto, pesos, ruta = componer(raiz, cfg)
        if a.comprobar:
            ok = al_dia(raiz, cfg)
            print(u"✓ la hoja está al día" if ok else u"✗ la hoja no es la de las fichas: generar_vias.py")
            return 0 if ok else 1
        techo = cfg["vias"].get("techo_ficha")
        for n, c in pesos:
            marca = u"  ✗ se pasa" if techo and c > techo else u""
            print(u"  %-22s %6d caracteres%s" % (n, c, marca))
        with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texto)
        print(u"✓ %s — %d caracteres, %d líneas" % (os.path.relpath(ruta, raiz), len(texto), texto.count("\n")))
        return 1 if techo and any(c > techo for _, c in pesos) else 0
    except SinTerrenoQueMedir as e:
        print(u"✗ %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
