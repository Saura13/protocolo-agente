#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera MAPA_SERVIDOR.md leyendo el código real de una máquina remota.

Contesta: ¿en qué líneas vive cada función del código que corre en otra máquina?
Toca: trae una copia temporal por scp (se borra al acabar) y escribe MAPA_SERVIDOR.md; en la máquina remota no escribe nada.
Necesita: acceso por scp sin contraseña y «remoto» en protocolo.config.json.

Por qué existe: cuando parte del código vive fuera del repositorio —en un servidor, en un
contenedor—, no aparece en el mapa local. Cada sesión que lo tocaba volvía a localizar a mano en
qué línea está cada función. Ese es el mayor gasto recurrente de contexto que tiene un proyecto
con código remoto, y este mapa lo elimina.

**Seguridad**: el mapa es solo *función → líneas*. No contiene código ni secretos. Por eso sirve
aunque el código remoto tenga credenciales dentro: eso impide *versionarlo*, no *mapearlo*. Los
ficheros se traen a una carpeta temporal fuera del repositorio y se borran al terminar; al
repositorio entra únicamente el .md.

Uso:
    python herramientas/generar_mapa_servidor.py            # descarga y mapea
    python herramientas/generar_mapa_servidor.py <carpeta>  # mapea una copia ya traída

Reutiliza el parseo de generar_mapa_codigo.py: un solo sitio decide cómo se leen los rangos.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=SyntaxWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import cargar, exigir                              # noqa: E402
from generar_mapa_codigo import contar_lineas, simbolos_python  # noqa: E402


def descargar(destino, host, ruta_remota):
    """Trae los .py del servidor.

    `-O` fuerza el protocolo antiguo de scp: sin él, en Windows aparece un aviso de
    'suspect path' al expandir el comodín del directorio remoto.
    """
    subprocess.run(["scp", "-O", "-q", "%s:%s/*.py" % (host, ruta_remota), destino + "/"],
                   check=True)


def recoger(carpeta, ruta_remota, prefijos_desechables, umbral):
    ficheros = []
    for entrada in sorted(os.listdir(carpeta)):
        if not entrada.endswith(".py"):
            continue
        # Criterio por PREFIJO, no lista de nombres: cualquier script nuevo de usar y tirar
        # queda excluido solo, sin tocar este fichero.
        if prefijos_desechables and entrada.startswith(tuple(prefijos_desechables)):
            continue
        completa = os.path.join(carpeta, entrada)
        ficheros.append({
            "ruta": "%s/%s" % (ruta_remota, entrada),
            "lineas": contar_lineas(completa),
            "simbolos": simbolos_python(completa),
        })
    return ficheros


def main():
    raiz, cfg = cargar(os.getcwd())
    remoto = exigir(cfg, "remoto", u"saber qué máquina y qué carpeta mapear")
    host = exigir(remoto, "host", u"conectarse por scp (formato usuario@maquina)")
    ruta_remota = exigir(remoto, "ruta", u"saber qué carpeta del servidor se mapea")
    prefijos = remoto.get("prefijos_desechables", [])
    salida_dir = exigir(cfg, "salida", u"saber dónde escribir el mapa")
    umbral = cfg["umbral_detalle"]
    salida = os.path.join(raiz, salida_dir, "MAPA_SERVIDOR.md")

    carpeta_dada = sys.argv[1] if len(sys.argv) > 1 else None
    temporal = None
    if carpeta_dada:
        carpeta = carpeta_dada
    else:
        temporal = tempfile.mkdtemp(prefix="mapa_servidor_")
        descargar(temporal, host, ruta_remota)
        carpeta = temporal

    try:
        ficheros = recoger(carpeta, ruta_remota, prefijos, umbral)
    finally:
        if temporal:
            shutil.rmtree(temporal, ignore_errors=True)

    partes = ["# Mapa del código del servidor — GENERADO AUTOMÁTICAMENTE\n"]
    partes.append(
        "> ⚠️ **No editar a mano.** Se genera leyendo el código real de `%s/`.\n"
        "> No contiene código ni credenciales: solo nombre de función y sus líneas.\n>\n"
        "> Regenerar (descarga fresca incluida) con:\n>\n"
        "> ```bash\n> python herramientas/generar_mapa_servidor.py\n> ```\n" % ruta_remota
    )
    partes.append(
        "\n**Generado**: %s — leído de `%s`.\n\n"
        "**Para qué sirve**: ir directo al rango exacto (`ssh … sed -n 'A,Bp'`) en vez de buscar "
        "la función a ciegas en ficheros de más de mil líneas.\n\n"
        "**Precisión**: rangos exactos, leídos con `ast`.%s\n\n---\n"
        % (datetime.now().strftime("%d/%m/%Y %H:%M"), host,
           (" Los ficheros de usar y tirar (prefijos %s) se omiten a propósito."
            % ", ".join("`%s`" % p for p in prefijos)) if prefijos else "")
    )

    grandes = [f for f in ficheros if f["lineas"] >= umbral]
    pequenos = [f for f in ficheros if f["lineas"] < umbral]

    for f in grandes:
        partes.append("\n## `%s` — %s líneas\n" % (f["ruta"], f["lineas"]))
        if not f["simbolos"]:
            partes.append("\n*(sin símbolos de nivel superior detectados)*\n")
            continue
        partes.append("\n| Líneas | Qué es | Nombre | Ruta HTTP |\n|:---|:---|:---|:---|\n")
        for s in f["simbolos"]:
            partes.append("| `%s-%s` | %s | `%s` | %s |\n"
                          % (s["inicio"], s["fin"], s["tipo"], s["nombre"], s["ruta_http"]))

    if pequenos:
        partes.append("\n## Ficheros pequeños (menos de %d líneas)\n\nSe abren enteros sin "
                      "problema: " % umbral)
        partes.append(", ".join("`%s` (%d)" % (os.path.basename(f["ruta"]), f["lineas"])
                                for f in pequenos))
        partes.append("\n")

    os.makedirs(os.path.dirname(salida), exist_ok=True)
    with open(salida, "w", encoding="utf-8") as fh:
        fh.write("".join(partes))

    print("[OK] Mapa generado: %s" % os.path.relpath(salida, raiz))
    print("     %d ficheros mapeados (%d con detalle)." % (len(ficheros), len(grandes)))


if __name__ == "__main__":
    main()
