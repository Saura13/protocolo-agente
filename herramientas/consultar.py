# -*- coding: utf-8 -*-
u"""Preguntarle a la casa en vez de rebuscar en ella. Solo lee, no toca nada.

Contesta: ¿qué trozos de los documentos hablan de X, qué toca a X y qué avisos tiene una vía?
Toca: nada (solo lee; si el índice está viejo, lo pone al día con indice.py).
Necesita: protocolo.config.json con «indice».

    python consultar.py palabras sueltas      los 10 trozos que mejor casan, con fichero:línea
    python consultar.py --toca BUG-040        qué es, a qué enlaza y quién lo nombra
    python consultar.py --toca nombre-de-nota lo mismo con una nota de memoria o un [[enlace]]
    python consultar.py --ultima              la última entrada del diario, desde su RESULTADO
    python consultar.py --avisos G            los avisos que otras vías han dejado para la G

Filtros: --tipo diario|bug|criterio|memoria|doc  ·  --desde AAAA-MM-DD  ·  --por-fecha  ·  -n 20

🔑 **Diez líneas con su enlace en vez de abrir megas.** Lo que devuelve es dónde mirar: el trozo
se lee después con `Read offset/limit` en la línea que dice, y solo si hace falta.

El índice se pone al día solo antes de contestar (relee únicamente lo que cambió).
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diario                               # noqa: E402
from indice import Indice, normalizar      # noqa: E402
from terreno import SinTerrenoQueMedir     # noqa: E402

PALABRA = re.compile(r"\w+", re.U)
AVISO = re.compile(r"^## ⏳ (?P<fecha>\S+) · de (?P<de>.+?) a (?P<a>.+?) — (?P<titulo>.*)$")


def expresion(texto, prefijo=False, o=False):
    u"""Lo que escribe una persona, convertido en una consulta FTS5 que no revienta.

    Cada palabra va entre comillas: así «BUG-040» o «sí/no» no se leen como operadores."""
    palabras = [p for p in PALABRA.findall(texto) if len(p) > 1]
    if prefijo:
        partes = [u'"%s"*' % p[:6] if len(p) > 6 else u'"%s"' % p for p in palabras]
    else:
        partes = [u'"%s"' % p for p in palabras]
    return (u" OR " if o else u" ").join(partes)


def buscar(ind, texto, a):
    filtros, params = [], []
    if a.tipo:
        filtros.append("t.tipo = ?")
        params.append(a.tipo)
    if a.desde:
        filtros.append("t.fecha >= ?")
        params.append(a.desde)
    donde = (" AND " + " AND ".join(filtros)) if filtros else ""
    orden = "t.fecha DESC, rank" if a.por_fecha else "rank"
    sql = (u"SELECT t.id, t.fichero, t.linea, t.tipo, t.fecha, t.titulo, "
           u"snippet(texto, 1, '«', '»', '…', 16) FROM texto JOIN trozos t ON t.id = texto.rowid "
           u"WHERE texto MATCH ? %s ORDER BY %s LIMIT ?" % (donde, orden))
    # Primero todas las palabras tal cual; si sale poco, raíces y cualquiera de ellas.
    for prefijo, o in ((False, False), (True, False), (True, True)):
        consulta = expresion(texto, prefijo, o)
        if not consulta:
            return [], ""
        filas = ind.db.execute(sql, [consulta] + params + [a.n]).fetchall()
        if len(filas) >= min(3, a.n):
            break
    return filas, consulta


def linea(ind, fichero, n, tipo, fecha, titulo):
    return u"[%s] %s:%d%s · %s" % (tipo, ind.relativa(fichero), n,
                                   (u" · " + fecha) if fecha else u"",
                                   titulo.replace("**", "")[:110])


def mostrar_busqueda(ind, texto, a):
    filas, consulta = buscar(ind, texto, a)
    if not filas:
        print(u"(nada para «%s»)" % texto)
        return 1
    for _id, fichero, n, tipo, fecha, titulo, trozo in filas:
        print(linea(ind, fichero, n, tipo, fecha, titulo))
        trozo = re.sub(r"\s+", " ", trozo).strip()
        if trozo:
            print(u"      %s" % trozo[:220])
    if " OR " in consulta or "*" in consulta:
        print(u"(ampliado a: %s)" % consulta)
    return 0


def mostrar_toca(ind, nombre, a):
    clave_id = nombre.upper()
    clave_nombre = normalizar(nombre)
    claves = (clave_id, clave_nombre)
    es = ind.db.execute(
        "SELECT id, fichero, linea, tipo, fecha, titulo FROM trozos WHERE clave IN (?,?) "
        "ORDER BY fecha", claves).fetchall()
    if es:
        print(u"ES:")
        for _id, f, n, tipo, fecha, titulo in es[:a.n]:
            print(u"  " + linea(ind, f, n, tipo, fecha, titulo))
        propios = [e[0] for e in es]
        marcas = ",".join("?" * len(propios))
        sale = ind.db.execute(
            "SELECT DISTINCT hacia FROM enlaces WHERE desde IN (%s) ORDER BY hacia" % marcas,
            propios).fetchall()
        if sale:
            print(u"ENLAZA A: " + u", ".join(h for (h,) in sale[:40])
                  + (u" (+%d)" % (len(sale) - 40) if len(sale) > 40 else u""))
    llegan = ind.db.execute(
        "SELECT DISTINCT t.id, t.fichero, t.linea, t.tipo, t.fecha, t.titulo FROM enlaces e "
        "JOIN trozos t ON t.id = e.desde WHERE e.hacia IN (?,?) "
        + ("AND t.tipo = ? " if a.tipo else "") +
        "ORDER BY t.fecha DESC", claves + ((a.tipo,) if a.tipo else ())).fetchall()
    if llegan:
        print(u"LO NOMBRAN (%d, lo más nuevo primero):" % len(llegan))
        for _id, f, n, tipo, fecha, titulo in llegan[:a.n]:
            print(u"  " + linea(ind, f, n, tipo, fecha, titulo))
        if len(llegan) > a.n:
            print(u"  … y %d más (-n para ver más, --tipo para filtrar)" % (len(llegan) - a.n))
    if not es and not llegan:
        print(u"(nadie es ni nombra «%s»)" % nombre)
        return 1
    return 0


def mostrar_ultima(raiz, cfg):
    fmt = diario.formato(cfg)
    ruta = diario.ficheros(raiz, cfg)[-1]
    texto, _ = diario.leer(ruta)
    lineas = texto.split("\n")
    entradas = diario.entradas(lineas, fmt)
    if not entradas:
        print(u"(el diario %s no tiene entradas)" % ruta)
        return 1
    ini = entradas[-1]
    cuerpo = lineas[ini:]
    res = [i for i, l in enumerate(cuerpo) if l.startswith(fmt["marcador_resultado"])]
    print(u"%s:%d" % (os.path.relpath(ruta, raiz).replace(os.sep, "/"), ini + 1))
    if res:
        print(cuerpo[0])
        print(u"…")
        cuerpo = cuerpo[res[0]:]
    else:
        print(u"(sin RESULTADO: la sesión se cortó a medias; va entera)")
    print("\n".join(cuerpo).rstrip())
    return 0


def mostrar_avisos(raiz, cfg, via):
    rel = cfg.get("avisos")
    if not rel:
        print(u"(no hay «avisos» declarado en protocolo.config.json)")
        return 1
    ruta = os.path.join(raiz, rel)
    if not os.path.isfile(ruta):
        print(u"(sin avisos: %s no existe todavía)" % rel)
        return 0
    texto, _ = diario.leer(ruta)
    lineas = texto.split("\n")
    via_n = normalizar(via)
    hallados = 0
    for i, l in enumerate(lineas):
        m = AVISO.match(l)
        if not m:
            continue
        destino = [normalizar(x) for x in re.split(r"\s*(?:,|\by\b)\s*", m.group("a")) if x.strip()]
        if via_n not in destino and "todas" not in destino:
            continue
        hallados += 1
        print(u"%s:%d · %s · de %s — %s" % (rel, i + 1, m.group("fecha"), m.group("de"), m.group("titulo")))
        for c in lineas[i + 1:]:
            if c.startswith("## "):
                break
            if c.strip():
                print(u"      " + c.strip())
    if not hallados:
        print(u"(ningún aviso pendiente para %s)" % via)
    return 0


def main():
    ap = argparse.ArgumentParser(description=u"Preguntarle a la casa. Solo lee.")
    ap.add_argument("texto", nargs="*", help=u"lo que se busca, en palabras sueltas")
    ap.add_argument("--toca", metavar="X", help=u"un identificador o un nombre de nota")
    ap.add_argument("--ultima", action="store_true", help=u"la última entrada del diario")
    ap.add_argument("--avisos", metavar="VIA", help=u"los avisos pendientes para esa vía")
    ap.add_argument("--tipo")
    ap.add_argument("--desde", metavar="AAAA-MM-DD")
    ap.add_argument("--por-fecha", action="store_true", help=u"lo más nuevo primero")
    ap.add_argument("-n", type=int, default=10)
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        if a.ultima or a.avisos:
            from config import cargar
            raiz, cfg = cargar()
            return mostrar_ultima(raiz, cfg) if a.ultima else mostrar_avisos(raiz, cfg, a.avisos)
        ind = Indice()
        ind.al_dia()
        if a.toca:
            return mostrar_toca(ind, a.toca, a)
        if not a.texto:
            ap.print_help()
            return 2
        return mostrar_busqueda(ind, u" ".join(a.texto), a)
    except SinTerrenoQueMedir as e:
        print(u"✗ %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
