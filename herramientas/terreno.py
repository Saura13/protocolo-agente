# -*- coding: utf-8 -*-
u"""Contra qué se va a medir se comprueba AQUÍ, y en ningún otro sitio.

**Qué problema resuelve**: un medidor apuntaba por defecto a una carpeta que no existía y
devolvió **«0 apariciones»**. Se leyó como «está limpio». Con la ruta correcta, el mismo comando
dio 26. El fallo no fue la ruta: fue que la función **devolvía lista vacía cuando el directorio
no existía y seguía como si nada**.

🔑 **El cero de «no hay nada que medir» y el cero de «está limpio» se imprimen igual.** Son la
misma cifra y significan lo contrario. La cifra que desmentía el resultado estaba disponible desde
el principio y nadie la miró antes de dar la medida por buena.

**Por qué es un módulo y no un `if` en cada herramienta**: porque un criterio copiado en ocho
sitios es un criterio con ocho sitios donde puede quedarse atrás. El criterio vive en **un** sitio
y las demás lo llaman.

**Qué se exige y qué NO** — la frontera importa:

* Se exige la **raíz** contra la que se mide: la carpeta de artefactos, el directorio de salida,
  el de fuentes. Si no está, la medida entera no significa nada.
* **No** se exige cada elemento de dentro. Que un elemento concreto no tenga cierta pieza es una
  **medida legítima** —«ese no la tiene»—, no un error. Convertirlo en excepción rompería los
  barridos, que existen precisamente para encontrar los incompletos.

**Y cuando grita, dice dónde mirar** sin llevar dentro ninguna ruta conocida: sube por la ruta
pedida hasta el primer ancestro que sí existe y enseña qué hay dentro. Quien lea el error corrige
sin adivinar, y el módulo no envejece cuando cambie el despliegue.

    from terreno import raiz, cosecha, SinTerrenoQueMedir

    raiz(args.carpeta, u"la carpeta de artefactos publicados")
    ficheros = cosecha(os.path.join(dir_datos, "*.md"), u"los documentos del lote")
"""
import os


class SinTerrenoQueMedir(Exception):
    u"""No hay contra qué medir. Se grita: no se devuelve cero."""


def _listar(ruta, tope=12):
    try:
        dentro = sorted(os.listdir(ruta))
    except OSError as e:
        return u"no se puede leer (%s)" % e
    if not dentro:
        return u"está vacío"
    visto = u", ".join(d.decode("utf-8", "replace") if isinstance(d, bytes) else d
                       for d in dentro[:tope])
    return visto + (u" … y %d más" % (len(dentro) - tope) if len(dentro) > tope else u"")


def donde_se_corta(ruta):
    u"""El primer ancestro de `ruta` que sí existe, y qué hay dentro.

    Es lo que convierte «no existe» en algo accionable: casi siempre el error está en un solo
    tramo de la ruta, y el contenido del ancestro enseña cuál era el tramo bueno.
    """
    actual = os.path.abspath(ruta)
    while True:
        padre = os.path.dirname(actual)
        if padre == actual:            # se llegó a la raíz del sistema
            return actual, _listar(actual)
        if os.path.isdir(padre):
            return padre, _listar(padre)
        actual = padre


def raiz(ruta, que, exigir_contenido=True):
    u"""Comprueba la raíz contra la que se va a medir. Devuelve la ruta o revienta.

    `que` es para el humano que lea el error: qué se esperaba encontrar ahí.
    `exigir_contenido=False` sirve para una raíz que puede estar legítimamente vacía (una caché
    recién creada, una carpeta de salida antes del primer volcado).
    """
    if not ruta:
        raise SinTerrenoQueMedir(u"no se ha dicho dónde está %s" % que)
    if not os.path.exists(ruta):
        corte, dentro = donde_se_corta(ruta)
        raise SinTerrenoQueMedir(
            u"no existe %s: %s\n  lo último que sí existe es %s, y dentro hay: %s"
            % (que, ruta, corte, dentro))
    if not os.path.isdir(ruta):
        raise SinTerrenoQueMedir(u"%s no es una carpeta: %s" % (que, ruta))
    if exigir_contenido and not os.listdir(ruta):
        raise SinTerrenoQueMedir(
            u"%s está vacía: %s — no hay nada que medir, que no es lo mismo que estar limpio"
            % (que, ruta))
    return ruta


def cosecha(patron, que, minimo=1):
    u"""El `glob` que no se conforma con no encontrar nada.

    Un patrón que no casa devuelve `[]` sin distinguir «la carpeta no está» de «la carpeta está
    y no tiene ninguno». Aquí se distingue: primero se exige la carpeta del patrón, y solo
    después se juzga la cosecha.
    """
    import glob as _glob
    carpeta = os.path.dirname(patron) or "."
    raiz(carpeta, u"la carpeta donde buscar %s" % que)
    encontrados = sorted(_glob.glob(patron))
    if len(encontrados) < minimo:
        raise SinTerrenoQueMedir(
            u"no hay %s en %s (se esperaban al menos %d, hay %d)\n  dentro hay: %s"
            % (que, carpeta, minimo, len(encontrados), _listar(carpeta)))
    return encontrados


# --- Que el grito se lea, sin repetir un try/except en cada herramienta -------------------
# Todas las que usan esto son órdenes de línea de comandos, y un traceback de doce líneas
# esconde justo lo que hay que leer. Se instala un manejador que SOLO toca esta excepción y
# delega el resto: sale con código 2, para que quien encadene la orden note que falló.
import sys as _sys

_hook_previo = _sys.excepthook


def _gritar(clase, valor, traza):
    if not issubclass(clase, SinTerrenoQueMedir):
        return _hook_previo(clase, valor, traza)
    _sys.stderr.write(os.linesep)
    _sys.stderr.write(u"NO HAY NADA QUE MEDIR - lo que salga debajo no es una medida" + os.linesep)
    _sys.stderr.write(u"   %s" % valor + os.linesep)
    _sys.exit(2)


_sys.excepthook = _gritar
