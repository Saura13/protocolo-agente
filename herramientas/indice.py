# -*- coding: utf-8 -*-
u"""El índice: una base SQLite generada sobre los documentos de texto. Se genera, no se escribe.

Contesta: ¿está al día el índice de los documentos (diario, bugs, criterios, memoria)?
Toca: escribe la base SQLite del índice (.indice/), que es generada y no va a git.
Necesita: protocolo.config.json con «indice».

    python indice.py            pone el índice al día (solo relee lo que cambió)
    python indice.py --desde-cero

**El texto sigue mandando.** Los documentos son markdown: los lee una persona y git los compara.
El índice es una copia troceada y buscable, que se tira y se rehace cuando haga falta. Por eso
vive en una carpeta que git no ve, y por eso nadie lo edita.

Qué hace:
- **Trocea** cada documento por sus cabeceras (o por la expresión que declare la fuente) y guarda
  cada trozo con su fichero, su línea, su título y su fecha. Búsqueda por texto completo (FTS5,
  viene con Python), sin acentos.
- **La red**: guarda los enlaces de cada trozo. Un enlace es `[[nombre]]` (como en la memoria) o
  un **identificador** declarado (`BUG-\\d+`, por ejemplo). Así contesta «qué toca a X» aunque el
  texto viejo no lleve corchetes: un identificador nombrado ya es un enlace.
- **Quién es quién**: un trozo cuya cabecera **empieza** por un identificador es ese identificador
  (la fila del BUG-040 es el BUG-040); una nota con `name:` en su cabecera es ese nombre.

Se configura en `protocolo.config.json`, clave «indice». Ejemplo en protocolo.config.ejemplo.json.
"""
import argparse
import glob
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import cargar, exigir          # noqa: E402
from diario import fecha_de                # noqa: E402
from terreno import SinTerrenoQueMedir     # noqa: E402

VERSION = 1   # si cambia la forma de la base, se rehace sola
ENLACE = re.compile(r"\[\[([^\]\n|]{1,120})(?:\|[^\]\n]*)?\]\]")
NOMBRE_NOTA = re.compile(r"^name:\s*(.+?)\s*$", re.M)

ESQUEMA = u"""
CREATE TABLE IF NOT EXISTS ficheros (ruta TEXT PRIMARY KEY, tipo TEXT, mtime REAL, tam INTEGER);
CREATE TABLE IF NOT EXISTS trozos (
    id INTEGER PRIMARY KEY, fichero TEXT, tipo TEXT, linea INTEGER, fin INTEGER,
    titulo TEXT, clave TEXT, fecha TEXT);
CREATE INDEX IF NOT EXISTS trozos_fichero ON trozos(fichero);
CREATE INDEX IF NOT EXISTS trozos_clave ON trozos(clave);
CREATE VIRTUAL TABLE IF NOT EXISTS texto USING fts5(
    titulo, cuerpo, tokenize = "unicode61 remove_diacritics 2");
CREATE TABLE IF NOT EXISTS enlaces (desde INTEGER, hacia TEXT, como TEXT);
CREATE INDEX IF NOT EXISTS enlaces_hacia ON enlaces(hacia);
CREATE INDEX IF NOT EXISTS enlaces_desde ON enlaces(desde);
CREATE TABLE IF NOT EXISTS meta (clave TEXT PRIMARY KEY, valor TEXT);
"""


def normalizar(nombre):
    u"""Un nombre de enlace, comparable: sin mayúsculas ni espacios de más."""
    return re.sub(r"\s+", " ", nombre.strip()).lower()


class Indice(object):
    def __init__(self, raiz=None, cfg=None):
        if cfg is None:
            raiz, cfg = cargar()
        self.raiz, self.cfg = raiz, cfg
        conf = exigir(cfg, "indice", u"saber qué documentos se indexan")
        self.fuentes = exigir(conf, "fuentes", u"saber qué documentos se indexan")
        self.ids = [re.compile(p) for p in conf.get("identificadores", [])]
        self.ruta_base = os.path.join(raiz, conf.get("base", ".indice/protocolo.sqlite"))
        os.makedirs(os.path.dirname(self.ruta_base), exist_ok=True)
        self.db = sqlite3.connect(self.ruta_base)
        self.db.executescript(ESQUEMA)
        fila = self.db.execute("SELECT valor FROM meta WHERE clave='version'").fetchone()
        if not fila or fila[0] != str(VERSION):
            self.vaciar()

    # ── qué ficheros entran ──────────────────────────────────────────────────────────
    def ficheros(self):
        u"""{ruta_absoluta: fuente}. Si dos fuentes cogen el mismo fichero, gana la primera."""
        vistos = {}
        for fuente in self.fuentes:
            patron = os.path.expanduser(fuente["ruta"])
            if not os.path.isabs(patron):
                patron = os.path.join(self.raiz, patron)
            hallados = glob.glob(patron, recursive=True)
            if not hallados and not fuente.get("opcional"):
                raise SinTerrenoQueMedir(
                    u"la fuente «%s» no encuentra ningún fichero (%s). Si es a propósito, "
                    u"márcala \"opcional\": true" % (fuente.get("tipo"), fuente["ruta"]))
            for ruta in sorted(hallados):
                if os.path.isfile(ruta):
                    vistos.setdefault(os.path.normpath(ruta), fuente)
        return vistos

    def relativa(self, ruta):
        try:
            rel = os.path.relpath(ruta, self.raiz)
        except ValueError:          # otra unidad, en Windows
            return ruta
        return ruta if rel.startswith("..") else rel.replace(os.sep, "/")

    # ── al día ──────────────────────────────────────────────────────────────────────
    def vaciar(self):
        for t in ("ficheros", "trozos", "texto", "enlaces", "meta"):
            self.db.execute("DELETE FROM %s" % t)
        self.db.execute("INSERT INTO meta VALUES ('version', ?)", (str(VERSION),))
        self.db.commit()

    def al_dia(self, avisar=False):
        u"""Relee solo los ficheros que cambiaron. Devuelve cuántos releyó."""
        actuales = self.ficheros()
        guardados = {r: (m, t) for r, m, t in self.db.execute("SELECT ruta, mtime, tam FROM ficheros")}
        cambiados = 0
        for ruta in set(guardados) - set(actuales):
            self.quitar(ruta)
            cambiados += 1
        for ruta, fuente in actuales.items():
            st = os.stat(ruta)
            if guardados.get(ruta) == (st.st_mtime, st.st_size):
                continue
            if avisar:
                print(u"  indexando %s" % self.relativa(ruta), file=sys.stderr)
            self.quitar(ruta)
            self.meter(ruta, fuente, st)
            cambiados += 1
        self.db.commit()
        return cambiados

    def quitar(self, ruta):
        ids = [r[0] for r in self.db.execute("SELECT id FROM trozos WHERE fichero=?", (ruta,))]
        for i in range(0, len(ids), 500):
            lote = ids[i:i + 500]
            marcas = ",".join("?" * len(lote))
            self.db.execute("DELETE FROM texto WHERE rowid IN (%s)" % marcas, lote)
            self.db.execute("DELETE FROM enlaces WHERE desde IN (%s)" % marcas, lote)
        self.db.execute("DELETE FROM trozos WHERE fichero=?", (ruta,))
        self.db.execute("DELETE FROM ficheros WHERE ruta=?", (ruta,))

    def meter(self, ruta, fuente, st):
        with open(ruta, encoding="utf-8", errors="replace") as fh:
            lineas = fh.read().replace("\r\n", "\n").split("\n")
        tipo = fuente.get("tipo", "doc")
        for inicio, fin in self.trocear(lineas, fuente.get("corte")):
            cuerpo = "\n".join(lineas[inicio:fin])
            titulo = self.titulo(lineas, inicio, ruta)
            clave = self.clave(titulo, cuerpo, tipo, fuente)
            fecha = fecha_de(titulo) or (fecha_de(cuerpo[:400]) if tipo != "memoria" else None)
            cur = self.db.execute(
                "INSERT INTO trozos (fichero, tipo, linea, fin, titulo, clave, fecha) "
                "VALUES (?,?,?,?,?,?,?)", (ruta, tipo, inicio + 1, fin, titulo, clave, fecha))
            rid = cur.lastrowid
            self.db.execute("INSERT INTO texto (rowid, titulo, cuerpo) VALUES (?,?,?)",
                            (rid, titulo, cuerpo))
            self.db.executemany("INSERT INTO enlaces VALUES (?,?,?)",
                                [(rid, h, c) for h, c in self.enlaces(cuerpo, clave)])
        self.db.execute("INSERT INTO ficheros VALUES (?,?,?,?)", (ruta, tipo, st.st_mtime, st.st_size))

    # ── trocear y reconocer ─────────────────────────────────────────────────────────
    @staticmethod
    def trocear(lineas, corte):
        u"""[(inicio, fin)]. Sin corte, el fichero es un solo trozo (una nota de memoria)."""
        if not corte:
            return [(0, len(lineas))]
        patron = re.compile(corte)
        en_codigo = False
        cortes = [0]
        for i, l in enumerate(lineas):
            if l.startswith("```"):
                en_codigo = not en_codigo
            elif not en_codigo and i and patron.match(l):
                cortes.append(i)
        cortes.append(len(lineas))
        return [(a, b) for a, b in zip(cortes, cortes[1:]) if any(x.strip() for x in lineas[a:b])]

    @staticmethod
    def titulo(lineas, inicio, ruta):
        primera = lineas[inicio].strip()
        if primera == "---":            # nota con cabecera: su descripción es el título
            for l in lineas[inicio + 1:inicio + 15]:
                if l.startswith("description:"):
                    return l.split(":", 1)[1].strip()
            return os.path.basename(ruta)
        primera = re.sub(r"^#+\s*", "", primera)
        if primera.startswith("|"):     # fila de una tabla: su nombre y la primera celda con frase
            celdas = [c.strip() for c in primera.strip("|").split("|") if c.strip()]
            frase = [c for c in celdas[1:] if len(c) > 25][:1]
            primera = u" · ".join(celdas[:1] + frase)
        return primera[:200] or os.path.basename(ruta)

    def clave(self, titulo, cuerpo, tipo, fuente):
        if tipo == "memoria" or fuente.get("corte") is None:
            m = NOMBRE_NOTA.search(cuerpo[:600])
            if m:
                return normalizar(m.group(1))
        limpio = re.sub(r"[*_`]", "", titulo)      # «**BUG-040**» también es el BUG-040
        for p in self.ids:
            m = p.match(limpio)
            if m:
                return m.group(0).upper()
        return None

    def enlaces(self, cuerpo, propia):
        vistos = set()
        for m in ENLACE.finditer(cuerpo):
            vistos.add((normalizar(m.group(1)), "enlace"))
        for p in self.ids:
            for m in p.finditer(cuerpo):
                vistos.add((m.group(0).upper(), "nombra"))
        return sorted(v for v in vistos if v[0] != propia)


def main():
    ap = argparse.ArgumentParser(description=u"Pone al día el índice de los documentos.")
    ap.add_argument("--desde-cero", action="store_true", help=u"tirarlo y rehacerlo entero")
    a = ap.parse_args()
    try:
        ind = Indice()
        if a.desde_cero:
            ind.vaciar()
        n = ind.al_dia(avisar=True)
    except SinTerrenoQueMedir as e:
        print(u"✗ %s" % e)
        return 2
    trozos = ind.db.execute("SELECT count(*) FROM trozos").fetchone()[0]
    enlaces = ind.db.execute("SELECT count(*) FROM enlaces").fetchone()[0]
    print(u"✓ índice al día: %d ficheros releídos · %d trozos · %d enlaces · %s"
          % (n, trozos, enlaces, ind.relativa(ind.ruta_base)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
