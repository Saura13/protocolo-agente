#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""Juntar la rama de esta sesión con la principal, sin perder nada de nadie.

Contesta: ¿se puede llevar a la principal lo de esta rama, y qué chocaría? Con `--juntar`, lo lleva.
Toca: sin `--juntar`, solo lee. Con `--juntar`: escribe en git (une la principal en esta rama, hace el
commit de la unión y adelanta la principal); nunca sube a un remoto.
Necesita: git, y que esta carpeta sea una carpeta de trabajo del repositorio.

    python _herramientas/juntar_rama.py            # qué pasaría (solo mira)
    python _herramientas/juntar_rama.py --juntar   # hacerlo

Por qué existe (16/10/2026): dos sesiones trabajaron a la vez en sus carpetas y, al juntar, chocó el
diario —las dos habían cogido la letra «B»— y se resolvió a mano. 🔑 *Una sesión que cierra en su rama
no ha cerrado*: si nadie junta la rama, la siguiente arranca desde antes. Y juntar a mano, con prisa al
final de una sesión, es justo cuando se pierde algo. Esto lo hace siempre igual:

1. **Lo que no está guardado no se junta**: si hay cambios sin commit, para y los enseña.
2. **Primero la principal entra en la rama**, aquí, donde un choque no estorba a nadie.
   - El diario y los avisos se suman solos (`.gitattributes`, `merge=union`): no chocan.
   - Los documentos **generados** (`generados` en `protocolo.config.json`) no se arreglan a mano: se
     vuelven a generar con su programa.
   - **Cualquier otro choque**: se deshace la unión entera (`git merge --abort`) y se dice qué fichero es.
     No se elige un lado a ciegas: es lo que pierde trabajo.
3. **Se comprueba lo que la suma puede estropear**: una misma fecha y letra dos veces en el diario, un
   aviso que sale a la vez pendiente y visto, marcas de choque olvidadas. Si hay algo, no se adelanta la
   principal.
4. **La principal solo avanza hacia delante** (`--ff-only`): si alguien la movió mientras tanto, git se
   niega y se vuelve a correr. En su carpeta, los cambios sin guardar de otro no se tocan.
"""
import argparse
import os
import re
import subprocess
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diario                               # noqa: E402
from comun import git as g                  # noqa: E402
from config import cargar                   # noqa: E402
from terreno import SinTerrenoQueMedir      # noqa: E402

MARCAS = re.compile(r"^(<<<<<<<|>>>>>>>) ", re.M)


def sin_guardar(raiz):
    r = g.git(raiz, "status", "--porcelain")
    lineas = [l for l in (r.stdout.splitlines() if r else []) if l.strip()]
    return [l for l in lineas if not l.startswith("??")], [l[3:] for l in lineas if l.startswith("??")]


def adelanto(raiz, de, sobre):
    r = g.git(raiz, "rev-list", "--count", "%s..%s" % (sobre, de))
    return int(r.stdout.strip()) if r and r.returncode == 0 else 0


def choques_previstos(raiz, rama, principal):
    u"""Qué ficheros chocarían, sin tocar nada (git merge-tree)."""
    r = g.git(raiz, "merge-tree", "--write-tree", "--name-only", "--no-messages", rama, principal)
    if r is None or r.returncode == 0:
        return []
    return [l.strip() for l in r.stdout.splitlines()[1:] if l.strip()]


# La cabecera de una entrada, en cualquiera de sus formas: «## 📅 15/10/2026 (N) — …» o «## 15/10/2026 N …».
CABECERA = re.compile(r"^## .*?(\d{1,2}/\d{1,2}/\d{4})\s*\(?([A-Z]{1,2})\)?(?:\s|$)", re.M)


def repetidas(texto):
    u"""{(fecha, letra): veces} de las entradas que salen más de una vez en `texto`."""
    return {k: n for k, n in Counter(CABECERA.findall(texto or "")).items() if n > 1}


def repetidas_nuevas(raiz, cfg, principal, antes):
    u"""[(fichero, fecha, letra, veces)] repetidas tras la suma que no lo estaban ya en una de las dos.

    Las que ya venían repetidas (el diario las tenía de antes del 16/10) no frenan: no las causó esta unión.
    """
    malas = []
    for ruta in diario.ficheros(raiz, cfg):
        rel = os.path.relpath(ruta, raiz)
        ya = set(antes.get(rel, {})) | set(repetidas(g.contenido_en(raiz, principal, rel)))
        for k, n in repetidas(diario.leer(ruta)[0]).items():
            if k not in ya:
                malas.append((rel, k[0], k[1], n))
    return malas


def avisos_dobles(raiz, cfg):
    u"""Avisos que salen a la vez ⏳ y ✅: una rama lo marcó visto y la suma conservó los dos."""
    rel = cfg.get("avisos")
    ruta = os.path.join(raiz, rel) if rel else None
    if not ruta or not os.path.isfile(ruta):
        return []
    lineas = diario.leer(ruta)[0].splitlines()
    pend = set(l[len(u"## ⏳"):] for l in lineas if l.startswith(u"## ⏳"))
    return [l for l in lineas if l.startswith(u"## ✅") and l[len(u"## ✅"):] in pend]


def marcas_olvidadas(raiz, ficheros):
    malas = []
    for rel in ficheros:
        ruta = os.path.join(raiz, rel)
        try:
            with open(ruta, encoding="utf-8", errors="replace") as fh:
                if MARCAS.search(fh.read()):
                    malas.append(rel)
        except (OSError, IsADirectoryError):
            pass
    return malas


def regenerar(raiz, rel, programa):
    r = subprocess.run([sys.executable, os.path.join(raiz, programa)], cwd=raiz,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SinTerrenoQueMedir(u"%s no se pudo regenerar con %s:\n%s" % (rel, programa, r.stdout + r.stderr))
    g.git(raiz, "add", "--", rel)


def carpeta_de(raiz, rama):
    for ruta, r in g.carpetas(raiz):
        if r == rama:
            return ruta
    return None


def main():
    ap = argparse.ArgumentParser(description=u"Juntar esta rama con la principal sin perder nada.")
    ap.add_argument("--juntar", action="store_true", help=u"hacerlo (sin esto, solo dice qué pasaría)")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        raiz, cfg = cargar()
        return juntar(raiz, cfg, a.juntar)
    except SinTerrenoQueMedir as e:
        print(u"✗ %s" % e)
        return 2


def juntar(raiz, cfg, de_verdad):
    principal = cfg.get("cierre", {}).get("rama_principal", "master")
    generados = cfg.get("generados", {})
    rama = g.rama_actual(raiz)
    if not rama:
        raise SinTerrenoQueMedir(u"esta carpeta no está en ninguna rama (HEAD suelto) o no es git")
    if rama == principal:
        print(u"✓ estás en «%s», la principal: no hay nada que juntar" % principal)
        return 0
    if not g.existe_rama(raiz, principal):
        raise SinTerrenoQueMedir(u"no existe la rama principal «%s» («cierre.rama_principal»)" % principal)

    cambios, nuevos = sin_guardar(raiz)
    if cambios:
        print(u"✗ hay cambios sin guardar; lo que no está en un commit no se junta:")
        for l in cambios:
            print(u"     " + l)
        return 1
    if nuevos:
        print(u"⚠ ficheros que git no ve (no viajan a la principal): %s" % ", ".join(nuevos[:8])
              + (u" …" if len(nuevos) > 8 else u""))

    mios, suyos = adelanto(raiz, rama, principal), adelanto(raiz, principal, rama)
    print(u"«%s»: %d commit(s) que «%s» no tiene; «%s» trae %d que esta rama no tiene"
          % (rama, mios, principal, principal, suyos))
    if mios == 0:
        print(u"✓ nada que llevar: esta rama ya está dentro de «%s»" % principal)
        return 0

    previstos = choques_previstos(raiz, rama, principal) if suyos else []
    a_mano = [f for f in previstos if f not in generados]
    for f in previstos:
        print(u"   choca %s — %s" % (f, u"se regenera con " + generados[f] if f in generados else u"⛔ A MANO"))
    if not de_verdad:
        if a_mano:
            print(u"✗ no se puede juntar solo: %d fichero(s) chocan y no son generados" % len(a_mano))
            return 1
        print(u"→ se puede juntar: python _herramientas/juntar_rama.py --juntar")
        return 0
    if a_mano:
        print(u"✗ no se junta: esos ficheros hay que resolverlos a mano, en esta rama, antes")
        return 1

    if suyos:
        antes = {os.path.relpath(f, raiz): repetidas(diario.leer(f)[0]) for f in diario.ficheros(raiz, cfg)}
        r = g.git(raiz, "merge", "--no-ff", "--no-commit", principal)
        chocan = g.git(raiz, "diff", "--name-only", "--diff-filter=U").stdout.split()
        raros = [f for f in chocan if f not in generados]
        if raros:
            g.git(raiz, "merge", "--abort")
            print(u"✗ chocó lo que no se esperaba (%s); unión deshecha, nada cambiado" % ", ".join(raros))
            return 1
        for f in chocan:
            g.git(raiz, "checkout", "--ours", "--", f)
            regenerar(raiz, f, generados[f])
            print(u"   ✓ %s regenerado" % f)
        tocados = g.git(raiz, "diff", "--cached", "--name-only").stdout.split()
        problemas = [u"marcas de choque en " + f for f in marcas_olvidadas(raiz, tocados)]
        problemas += [u"entrada %s (%s) %d veces en %s" % (fe, le, n, fi)
                      for fi, fe, le, n in repetidas_nuevas(raiz, cfg, principal, antes)]
        problemas += [u"aviso pendiente y visto a la vez: %s" % l for l in avisos_dobles(raiz, cfg)]
        if problemas:
            g.git(raiz, "merge", "--abort")
            print(u"✗ la suma estropearía algo; unión deshecha, nada cambiado:")
            for p in problemas:
                print(u"     " + p)
            print(u"  una letra repetida: en esta rama, cambia la de TU entrada (y su RESULTADO) por una libre"
                  u" —la que dé `apuntar.py entrada`, mirando todas las carpetas— y vuelve a correr esto")
            return 1
        r = g.git(raiz, "commit", "--no-edit")
        if r is None or r.returncode != 0:
            raise SinTerrenoQueMedir(u"no se pudo hacer el commit de la unión:\n" + (r.stdout + r.stderr if r else ""))
        print(u"✓ «%s» unida en «%s»" % (principal, rama))

    donde = carpeta_de(raiz, principal)
    if donde:
        r = g.git(donde, "merge", "--ff-only", rama)
    else:                               # la principal no está sacada en ninguna carpeta
        r = g.git(raiz, "fetch", ".", "%s:%s" % (rama, principal))
    if r is None or r.returncode != 0:
        print(u"✗ «%s» no avanzó (¿alguien la movió, o choca con lo que hay sin guardar en %s?):\n%s"
              % (principal, donde or u"ninguna carpeta", (r.stdout + r.stderr) if r else u""))
        print(u"  vuelve a correr esto: lo ya unido en la rama no se pierde")
        return 1
    print(u"✓ «%s» adelantada hasta «%s»%s" % (principal, rama, u" (en %s)" % donde if donde else u""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
