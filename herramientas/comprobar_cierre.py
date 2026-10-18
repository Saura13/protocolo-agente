#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""¿Se puede cerrar la sesión? Comprueba la lista de cierre en vez de recordarla.

Contesta: ¿se puede cerrar la sesión: techos, diario con resultado, mapas al día, siguiente con su modelo, todo en git?
Toca: ejecuta git solo para preguntar (estado, ramas, commits); no escribe nada.
Necesita: protocolo.config.json con «cierre».

Por qué existe: la lista de comprobación estaba escrita y aun así se saltaba, porque cumplirla
dependía de acordarse justo cuando el contexto se estaba agotando — que es el peor momento para
acordarse de nada.

🔑 **Una regla que depende de que alguien la teclee no es una regla.** Lo que no comprueba un
programa es una intención.

Qué comprueba, todo mecánicamente:

  1. **Techos de líneas (y de caracteres, si se declaran)** de los documentos que se leen al arrancar. Si uno se pasó, se poda
     ANTES de cerrar: cada línea de más se paga en todas las sesiones que queden.
  2. **El diario tiene RESULTADO** en su última entrada. Sin él, la siguiente sesión no sabe si
     aquello terminó o se cortó a la mitad.
  3. **Los mapas no son más viejos que el código** que dicen mapear. Un mapa desactualizado
     apunta a líneas equivocadas, y eso es peor que no tenerlo.
  4. **Cada «siguiente» dice con qué modelo se abre** (p. ej. `[Opus]` / `[Sonnet]`), si se declara
     «cierre.siguiente». Decirlo al cerrar avisa al usuario ANTES de abrir la próxima sesión; al
     arrancar ya llega tarde, porque la sesión ya está abierta con un modelo.
  5. **No quedan cambios sin registrar** en git, y la rama no se queda sin juntar con la principal (aviso).

Lo que NO comprueba, y hay que mirar a mano: que el estado diga cuál es el siguiente paso, que el
registro de bugs refleje la realidad, y que el mensaje del commit explique el porqué. Un programa
no puede juzgar eso — pero sí puede recordarlo, y lo hace al final.

**No toca nada: solo lee.** Sale con código 1 si algo falta, para que se note al encadenarlo.

Uso:
    python herramientas/comprobar_cierre.py
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import cargar          # noqa: E402
from terreno import raiz           # noqa: E402

OK, FALLO, AVISO = "  [OK]  ", "  [FALTA]", "  [AVISO]"


def contar_lineas(ruta):
    with open(ruta, encoding="utf-8", errors="ignore") as fh:
        return sum(1 for _ in fh)


def mas_reciente(carpeta, extensiones, excluir):
    """La fecha del fichero de código modificado más recientemente bajo `carpeta`."""
    ultima = 0
    for base, dirs, ficheros in os.walk(carpeta):
        dirs[:] = [d for d in dirs if not any(x in d for x in excluir)]
        for f in ficheros:
            if f.endswith(tuple(extensiones)):
                try:
                    ultima = max(ultima, os.path.getmtime(os.path.join(base, f)))
                except OSError:
                    pass
    return ultima


def comprobar_techos(raiz_p, cierre):
    """Los documentos de arranque, contra su techo declarado."""
    fallos = []
    techos = cierre.get("techos", {})
    if not techos:
        print(AVISO, u"no hay techos declarados en «cierre.techos» — no se comprueba ninguno")
        return fallos
    for rel, techo in sorted(techos.items()):
        # Un número es un techo de líneas. Un diccionario puede llevar también caracteres:
        # 🔑 un techo de líneas solo no mide lo que se paga — 120 líneas de 20.000 caracteres
        # caben en él y cuestan como un libro.
        if not isinstance(techo, dict):
            techo = {"lineas": techo}
        ruta = os.path.join(raiz_p, rel)
        if not os.path.isfile(ruta):
            fallos.append(u"%s está declarado con techo pero no existe" % rel)
            print(FALLO, u"%s — declarado con techo, pero no existe" % rel)
            continue
        with open(ruta, encoding="utf-8", errors="ignore") as fh:
            texto = fh.read()
        medidas = {"lineas": contar_lineas(ruta), "caracteres": len(texto)}
        partes, pasado = [], False
        for unidad in ("lineas", "caracteres"):
            if unidad not in techo:
                continue
            n, t = medidas[unidad], techo[unidad]
            partes.append(u"%d/%d %s" % (n, t, u"líneas" if unidad == "lineas" else unidad))
            if n > t:
                pasado = True
                fallos.append(u"%s se pasó del techo de %s (%d > %d)" % (rel, unidad, n, t))
        if pasado:
            print(FALLO, u"%s — %s: se poda ANTES de cerrar" % (rel, u", ".join(partes)))
        else:
            print(OK, u"%s — %s" % (rel, u", ".join(partes)))
    return fallos


def comprobar_diario(raiz_p, cierre):
    fallos = []
    rel = cierre.get("diario")
    if not rel:
        print(AVISO, u"no hay diario declarado en «cierre.diario» — no se comprueba")
        return fallos
    ruta = os.path.join(raiz_p, rel)
    if os.path.isdir(ruta):
        # Diario por meses: la última entrada está en el último mes.
        meses = sorted(f for f in os.listdir(ruta) if f[:4].isdigit() and f.endswith(".md"))
        if meses:
            rel = rel.rstrip("/") + "/" + meses[-1]
            ruta = os.path.join(ruta, meses[-1])
    if not os.path.isfile(ruta):
        fallos.append(u"no existe el diario %s" % rel)
        print(FALLO, u"%s — no existe" % rel)
        return fallos

    marcador = cierre.get("marcador_resultado", "### RESULTADO")
    inicio = cierre.get("marcador_entrada", "## ")
    with open(ruta, encoding="utf-8", errors="ignore") as fh:
        lineas = fh.readlines()

    ultima = None
    for i, linea in enumerate(lineas):
        if linea.startswith(inicio) and not linea.startswith(marcador):
            ultima = i
    if ultima is None:
        fallos.append(u"el diario no tiene ninguna entrada")
        print(FALLO, u"%s — sin entradas" % rel)
        return fallos

    titulo = lineas[ultima].strip()[:70]
    if any(l.startswith(marcador) for l in lineas[ultima:]):
        print(OK, u"%s — la última entrada tiene RESULTADO" % rel)
    else:
        fallos.append(u"la última entrada del diario no tiene RESULTADO")
        print(FALLO, u"%s — la última entrada NO tiene «%s»" % (rel, marcador))
        print(u"           era: %s" % titulo)
    return fallos


def comprobar_mapas(raiz_p, cfg, cierre):
    """Un mapa más viejo que el código que mapea apunta a líneas equivocadas."""
    fallos = []
    mapas = cierre.get("mapas", [])
    if not mapas:
        print(AVISO, u"no hay mapas declarados en «cierre.mapas» — no se comprueba")
        return fallos

    zonas = [z["ruta"] for z in cfg.get("zonas", [])]
    if not zonas:
        print(AVISO, u"no hay zonas de código declaradas — no se puede fechar el código")
        return fallos
    codigo = max(mas_reciente(os.path.join(raiz_p, z), cfg["extensiones"], cfg["excluir"])
                 for z in zonas if os.path.isdir(os.path.join(raiz_p, z)))

    for rel in mapas:
        ruta = os.path.join(raiz_p, rel)
        if not os.path.isfile(ruta):
            fallos.append(u"falta el mapa %s: nunca se generó" % rel)
            print(FALLO, u"%s — no existe: generarlo" % rel)
            continue
        if os.path.getmtime(ruta) < codigo:
            fallos.append(u"%s es más viejo que el código: regenerarlo" % rel)
            print(FALLO, u"%s — más viejo que el código: REGENERAR" % rel)
        else:
            print(OK, u"%s — al día" % rel)
    return fallos


def comprobar_hoja_de_vias(raiz_p, cfg):
    """La hoja de vías, si se genera de fichas, tiene que ser la de las fichas.

    Si alguien la edita a mano, la próxima generación le borra lo escrito sin avisar; y si se
    edita una ficha sin generar, el arranque lee la versión vieja.
    """
    if "vias" not in cfg:
        return []
    try:
        import generar_vias
        ok = generar_vias.al_dia(raiz_p, cfg)
    except Exception as e:  # noqa: BLE001 — se informa, no se tumba el cierre
        print(AVISO, u"no se pudo comprobar la hoja de vías: %s" % e)
        return []
    if ok:
        print(OK, u"hoja de vías — es la de sus fichas")
        return []
    print(FALLO, u"hoja de vías — no es la de sus fichas: `python %s/generar_vias.py`"
          % cfg.get("herramientas", "herramientas"))
    return [u"la hoja de vías no está generada de sus fichas"]


def lineas_siguiente_sin_modelo(lineas, marca, palabra, etiquetas):
    u"""Las líneas que anuncian un siguiente paso sin decir con qué modelo se abre. Pura: (nº, texto)."""
    return [(i, l.strip()) for i, l in enumerate(lineas, 1)
            if marca in l and palabra.lower() in l.lower() and not any(e in l for e in etiquetas)]


def comprobar_siguiente_con_modelo(raiz_p, cierre):
    u"""Cada «siguiente» de la hoja de vías dice con qué modelo se abre la sesión que lo haga.

    El modelo se elige al ABRIR la sesión: cambiarlo a mitad no hereda la caché y se repaga el arranque.
    Por eso se dice al cerrar la anterior, no al arrancar la nueva. Opcional: sin «cierre.siguiente», no se mira.
    """
    fallos = []
    cfg = cierre.get("siguiente") or {}
    rel = cfg.get("documento")
    if not rel:
        print(AVISO, u"no hay «cierre.siguiente» declarado — no se comprueba")
        return fallos
    ruta = os.path.join(raiz_p, rel)
    if not os.path.isfile(ruta):
        fallos.append(u"no existe %s" % rel)
        print(FALLO, u"%s — no existe" % rel)
        return fallos
    etiquetas = cfg.get("etiquetas") or []
    with open(ruta, encoding="utf-8", errors="ignore") as fh:
        sin = lineas_siguiente_sin_modelo(fh.readlines(), cfg.get("marca", u"⏭️"),
                                          cfg.get("palabra", u"siguiente"), etiquetas)
    if sin:
        fallos.append(u"%d «siguiente» sin modelo en %s" % (len(sin), rel))
        print(FALLO, u"%s — %d «siguiente» sin %s:" % (rel, len(sin), u" ni ".join(etiquetas)))
        for i, texto in sin:
            print(u"           línea %d: %s" % (i, texto[:90]))
    else:
        print(OK, u"%s — cada «siguiente» dice su modelo" % rel)
    return fallos


def comprobar_git(raiz_p):
    fallos = []
    try:
        r = subprocess.run(["git", "status", "--porcelain"], cwd=raiz_p,
                           capture_output=True, text=True)
    except OSError:
        print(AVISO, u"git no está disponible — no se comprueba")
        return fallos
    if r.returncode != 0:
        print(AVISO, u"esto no es un repositorio git — no se comprueba")
        return fallos
    sucios = [l for l in r.stdout.splitlines() if l.strip()]
    if sucios:
        fallos.append(u"hay %d ficheros sin registrar en git" % len(sucios))
        print(FALLO, u"git — %d ficheros sin commit:" % len(sucios))
        for l in sucios[:10]:
            print(u"           %s" % l)
        if len(sucios) > 10:
            print(u"           … y %d más" % (len(sucios) - 10))
    else:
        print(OK, u"git — sin cambios pendientes")
    return fallos


def comprobar_rama(raiz_p, cierre):
    u"""La rama de trabajo no se queda con commits que la principal no tiene.

    Una rama cerrada y sin juntar es trabajo que la siguiente sesión no ve: arranca de la
    principal y lo rehace. Solo avisa (no es un fallo: se puede comprobar antes del commit).
    """
    principal = cierre.get("rama_principal", "master")
    def git(*args):
        return subprocess.run(["git"] + list(args), cwd=raiz_p, capture_output=True, text=True)
    try:
        actual = git("branch", "--show-current")
        if actual.returncode != 0:
            print(AVISO, u"esto no es un repositorio git — no se comprueba la rama")
            return []
        rama = actual.stdout.strip()
        if not rama:
            print(AVISO, u"HEAD suelto, sin rama — no se comprueba si está juntada con «%s»" % principal)
            return []
        if rama == principal:
            print(OK, u"estás en «%s», la rama principal" % principal)
            return []
        cuenta = git("rev-list", "--count", "%s..HEAD" % principal)
    except OSError:
        print(AVISO, u"git no está disponible — no se comprueba la rama")
        return []
    if cuenta.returncode != 0:
        print(AVISO, u"no existe la rama principal «%s» (se declara en «cierre.rama_principal»)" % principal)
        return []
    n = int(cuenta.stdout.strip() or 0)
    if n:
        print(AVISO, u"«%s» tiene %d commit(s) que «%s» no tiene — sin juntar, la próxima sesión no los ve" % (rama, n, principal))
        print(u"           tras el commit: python herramientas/juntar_rama.py --juntar (suma diario y avisos,"
              u" regenera lo generado y frena si algo se perdería)")
    else:
        print(OK, u"«%s» ya está dentro de «%s»" % (rama, principal))
    return []


def main():
    raiz_p, cfg = cargar(os.getcwd())
    raiz(raiz_p, u"la raíz del proyecto")
    cierre = cfg.get("cierre", {})

    print(u"\n¿SE PUEDE CERRAR LA SESIÓN?\n")
    fallos = []
    print(u"1. Techos de los documentos de arranque")
    fallos += comprobar_techos(raiz_p, cierre)
    fallos += comprobar_hoja_de_vias(raiz_p, cfg)
    print(u"\n2. El diario cuenta cómo acabó")
    fallos += comprobar_diario(raiz_p, cierre)
    print(u"\n3. Los mapas están al día")
    fallos += comprobar_mapas(raiz_p, cfg, cierre)
    print(u"\n4. Cada siguiente paso dice con qué modelo se abre")
    fallos += comprobar_siguiente_con_modelo(raiz_p, cierre)
    print(u"\n5. Todo registrado en git y juntado con la principal")
    fallos += comprobar_git(raiz_p)
    fallos += comprobar_rama(raiz_p, cierre)

    print(u"\n" + u"-" * 70)
    if fallos:
        print(u"NO SE CIERRA TODAVÍA — %d cosa(s) pendientes:" % len(fallos))
        for f in fallos:
            print(u"   · %s" % f)
    else:
        print(u"Lo comprobable está hecho.")

    print(u"\nY esto NO lo puede comprobar un programa — mirarlo a mano:")
    print(u"   · ¿El estado dice cuál es el SIGUIENTE PASO? (lo lee la próxima sesión, no tú)")
    print(u"   · ¿El registro de bugs refleja el estado real, no el de cuando se escribió?")
    print(u"   · ¿El mensaje del commit explica el PORQUÉ? El qué ya está en el diff.")
    print(u"   · ¿Se verificó que no se rompió nada, POR DONDE ENTRA EL USUARIO?")
    print(u"   · ¿Se ha dicho al usuario CON QUÉ MODELO abrir la próxima sesión?")
    print(u"   · ¿La próxima sesión queda PREPARADA (receta cerrada), y esta se archiva al abrirla?")

    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
