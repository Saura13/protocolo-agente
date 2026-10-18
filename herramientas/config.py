# -*- coding: utf-8 -*-
u"""Dónde está cada cosa en ESTE proyecto — declarado una vez, en un fichero.

Contesta: ¿dónde está cada cosa en este proyecto (protocolo.config.json)?
Toca: nada (solo lee).

Las herramientas de este protocolo no llevan dentro ninguna ruta del proyecto. La razón es la
regla de fondo: *criterios generales, nunca listas de casos*. Una herramienta con rutas cableadas
sirve a un proyecto y estorba en el siguiente.

El fichero se llama `protocolo.config.json` y vive en la raíz del proyecto. Hay un ejemplo
comentado en `protocolo.config.ejemplo.json`.

🔑 Si falta el fichero o falta una clave, esto **grita**. No usa un valor por defecto: un defecto
que apunta a lo que no está convierte «sin configurar» en «cero resultados», y eso se lee como
éxito.
"""
import json
import os

from terreno import SinTerrenoQueMedir

NOMBRE = "protocolo.config.json"

# Valores que sí tienen un defecto razonable, porque no dependen del proyecto sino del oficio.
DEFECTOS = {
    "umbral_detalle": 150,
    "extensiones": [".py", ".html", ".js"],
    "excluir": ["node_modules", "__pycache__", "venv", ".git", ".venv", "dist", "build"],
}


def raiz_proyecto(desde=None):
    u"""Sube desde `desde` hasta encontrar el fichero de configuración."""
    actual = os.path.abspath(desde or os.path.dirname(os.path.abspath(__file__)))
    while True:
        if os.path.isfile(os.path.join(actual, NOMBRE)):
            return actual
        padre = os.path.dirname(actual)
        if padre == actual:
            raise SinTerrenoQueMedir(
                u"no se encuentra %s subiendo desde %s\n"
                u"  Cópialo de herramientas/protocolo.config.ejemplo.json a la raíz del "
                u"proyecto y rellénalo." % (NOMBRE, desde or "las herramientas"))
        actual = padre


def cargar(desde=None):
    u"""Devuelve (raiz_del_proyecto, configuración) o revienta diciendo qué falta."""
    raiz = raiz_proyecto(desde)
    ruta = os.path.join(raiz, NOMBRE)
    try:
        with open(ruta, encoding="utf-8") as fh:
            cfg = json.load(fh)
    except ValueError as e:
        raise SinTerrenoQueMedir(u"%s no es JSON válido: %s" % (ruta, e))

    for clave, valor in DEFECTOS.items():
        cfg.setdefault(clave, valor)
    return raiz, cfg


def exigir(cfg, clave, para_que):
    u"""Una clave obligatoria. Si no está, se dice para qué hacía falta."""
    if clave not in cfg or cfg[clave] in (None, "", [], {}):
        raise SinTerrenoQueMedir(
            u"falta «%s» en %s — hace falta para %s" % (clave, NOMBRE, para_que))
    return cfg[clave]
