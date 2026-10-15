# -*- coding: utf-8 -*-
u"""El diario: dónde está, cómo se reconoce una entrada y cómo se escribe sin pisarse.

Lo usan `apuntar.py` (escribe), `consultar.py` (lee la última) y `comprobar_cierre.py` (mira que
la última tenga resultado). Vive aquí una sola vez para que los tres entiendan lo mismo por
«entrada» y por «el diario de ahora».

El diario puede declararse de dos formas en `protocolo.config.json` («cierre.diario»):

- **un fichero** (`docs/DIARIO.md`): todo en uno, como al principio;
- **una carpeta** (`docs/diario`): un fichero por mes, `AAAA-MM.md`. El de ahora es el del mes en
  curso. 🔑 *Un diario de un solo fichero crece sin techo*: a los tres meses son megas que nadie
  abre y que cualquier herramienta tiene que tragarse entera para leer la última entrada.

El formato de la cabecera también se declara («diario_formato»), con un defecto razonable.
"""
import datetime
import glob
import os
import re
import time

from terreno import SinTerrenoQueMedir

MES = re.compile(r"^(\d{4})-(\d{2})\.md$")

FORMATO = {
    # Cómo empieza una entrada. {fecha} va en dd/mm/aaaa y {letra} distingue las del mismo día.
    "cabecera": u"## 📅 {fecha} ({letra}) — {titulo}",
    "resultado": u"### RESULTADO ({dia} {letra}) — {titulo}",
    "marcador_entrada": "## ",
    "marcador_resultado": "### RESULTADO",
}

# Fechas que se reconocen en una cabecera, en cualquiera de las formas que ha usado el diario.
_FECHAS = [
    (re.compile(r"(\d{4})-(\d{2})-(\d{2})"), lambda m: (m.group(1), m.group(2), m.group(3))),
    (re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})"), lambda m: (m.group(3), m.group(2), m.group(1))),
]


def fecha_de(texto):
    u"""La primera fecha que aparece en `texto`, como 'AAAA-MM-DD', o None."""
    mejor = None
    for patron, partes in _FECHAS:
        m = patron.search(texto)
        if m and (mejor is None or m.start() < mejor[0]):
            a, mm, d = partes(m)
            mejor = (m.start(), u"%s-%02d-%02d" % (a, int(mm), int(d)))
    return mejor[1] if mejor else None


def formato(cfg):
    f = dict(FORMATO)
    f.update(cfg.get("diario_formato", {}))
    cierre = cfg.get("cierre", {})
    for clave in ("marcador_entrada", "marcador_resultado"):
        if clave in cierre:
            f[clave] = cierre[clave]
    return f


def ruta_declarada(raiz, cfg):
    rel = cfg.get("cierre", {}).get("diario")
    if not rel:
        raise SinTerrenoQueMedir(u"falta «cierre.diario» en protocolo.config.json")
    return os.path.join(raiz, rel)


def ficheros(raiz, cfg):
    u"""Los ficheros del diario, del más viejo al más nuevo."""
    ruta = ruta_declarada(raiz, cfg)
    if os.path.isfile(ruta):
        return [ruta]
    if os.path.isdir(ruta):
        meses = sorted(f for f in os.listdir(ruta) if MES.match(f))
        return [os.path.join(ruta, f) for f in meses]
    raise SinTerrenoQueMedir(u"el diario declarado no existe: %s" % ruta)


def actual(raiz, cfg, crear=False):
    u"""El fichero donde se escribe hoy. En una carpeta, el del mes en curso."""
    ruta = ruta_declarada(raiz, cfg)
    if os.path.isfile(ruta) or not (os.path.isdir(ruta) or crear):
        return ruta
    hoy = datetime.date.today()
    fichero = os.path.join(ruta, u"%04d-%02d.md" % (hoy.year, hoy.month))
    if crear and not os.path.exists(fichero):
        os.makedirs(ruta, exist_ok=True)
        try:            # «x»: si otro agente lo acaba de crear, no se le pisa lo que ya escribió
            fh = open(fichero, "x", encoding="utf-8", newline="")
        except FileExistsError:
            return fichero
        with fh:
            fh.write(u"# Diario — %04d-%02d\n\n> Una entrada por sesión, en orden. Se escribe con "
                     u"`apuntar.py`, no a mano.\n" % (hoy.year, hoy.month))
    return fichero


def entradas(lineas, fmt):
    u"""Índices de las líneas que abren una entrada (no un resultado)."""
    return [i for i, l in enumerate(lineas)
            if l.startswith(fmt["marcador_entrada"]) and not l.startswith(fmt["marcador_resultado"])]


class Cerrojo(object):
    u"""Que dos agentes no escriban el mismo fichero a la vez.

    Un fichero `.cerrojo` al lado, creado en exclusiva: el sistema garantiza que solo uno lo crea.
    Si quien lo tenía murió sin soltarlo, a los `caduca` segundos se da por abandonado — escribir
    en el diario dura milisegundos, así que uno viejo es siempre de un proceso muerto.
    """

    def __init__(self, ruta, espera=30, caduca=120):
        self.ruta = ruta + ".cerrojo"
        self.espera, self.caduca = espera, caduca

    def __enter__(self):
        limite = time.time() + self.espera
        while True:
            try:
                fd = os.open(self.ruta, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, (u"%d %s" % (os.getpid(), time.ctime())).encode("utf-8"))
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.ruta) > self.caduca:
                        os.remove(self.ruta)
                        continue
                except OSError:
                    continue
                if time.time() > limite:
                    raise SinTerrenoQueMedir(
                        u"otro agente tiene cogido %s desde hace rato; si no hay ninguno, borra "
                        u"ese fichero a mano" % self.ruta)
                time.sleep(0.2)

    def __exit__(self, *exc):
        try:
            os.remove(self.ruta)
        except OSError:
            pass


def leer(ruta):
    u"""(texto, salto) — el salto de línea que usa el fichero, para escribir con el mismo."""
    with open(ruta, "rb") as fh:
        crudo = fh.read()
    salto = "\r\n" if b"\r\n" in crudo[:20000] else "\n"
    return crudo.decode("utf-8").replace("\r\n", "\n"), salto


def escribir(ruta, texto, salto):
    u"""Escribe entero y de golpe: a un temporal y luego se cambia por el bueno."""
    tmp = ruta + ".escribiendo"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(texto.replace("\n", salto))
    os.replace(tmp, ruta)
