#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qué costó una sesión de Claude Code, turno a turno — medido, no estimado.

El transcript de cada sesión guarda el gasto real de cada turno. Esta herramienta lo lee y
contesta dos preguntas que antes se respondían a ojo:

  1. ¿Cuánto pesa el ARRANQUE, y qué parte de él es documentación tuya?
     (el turno 1 es el prefijo fijo: entorno + fichero de instrucciones + memoria,
     antes de leer un solo documento del proyecto)
  2. ¿Dónde se fue la cuota: en releer, en escribir caché o en producir?

🔑 Sirve para no optimizar lo que no es el problema. En el proyecto de origen, el arranque costaba
61.101 tokens y todo el mundo daba por hecho que sobraba documentación: al medirlo, el 81% era
prefijo del entorno y los documentos propios eran el 19%.

**No toca nada: solo lee.**

Uso:
    python herramientas/medir_cuota_sesion.py            # la sesión más reciente
    python herramientas/medir_cuota_sesion.py --turnos   # además, el detalle turno a turno
    python herramientas/medir_cuota_sesion.py <fichero.jsonl>

Dónde están los transcripts: `~/.claude/projects/<proyecto>/<sesión>.jsonl`. Otros agentes guardan
un registro equivalente en otro sitio; si usas uno, apunta la herramienta a su fichero.
"""
import glob
import json
import os
import sys

# Precio relativo de cada clase de token respecto a uno de entrada normal.
# Un token producido cuesta ~50 veces uno releído: NO son la misma unidad y no se suman.
PESO = {"releer": 0.1, "escribir_cache": 1.25, "producir": 5.0}

RAIZ = os.path.expanduser("~/.claude/projects")


def transcript_mas_reciente():
    cands = glob.glob(os.path.join(RAIZ, "*", "*.jsonl"))
    if not cands:
        sys.exit("No hay transcripts en %s" % RAIZ)
    return max(cands, key=os.path.getmtime)


def leer_turnos(ruta):
    """Un turno por petición real al modelo, sin los duplicados por bloque de contenido."""
    turnos, vistos = [], set()
    with open(ruta, encoding="utf-8") as fh:
        for linea in fh:
            try:
                d = json.loads(linea)
            except ValueError:
                continue
            if d.get("type") != "assistant":
                continue
            msg = d.get("message") or {}
            uso = msg.get("usage")
            if not uso:
                continue
            # Varias líneas comparten id de mensaje (una por bloque de contenido):
            # se contaría dos y tres veces el mismo gasto.
            ident = msg.get("id") or d.get("uuid")
            if ident in vistos:
                continue
            vistos.add(ident)
            turnos.append({
                "escribir_cache": uso.get("cache_creation_input_tokens", 0),
                "releer":         uso.get("cache_read_input_tokens", 0),
                "producir":       uso.get("output_tokens", 0),
                "entrada":        uso.get("input_tokens", 0),
            })
    return turnos


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    detalle = "--turnos" in sys.argv
    ruta = args[0] if args else transcript_mas_reciente()
    turnos = leer_turnos(ruta)
    if not turnos:
        sys.exit("Sin turnos medibles en %s" % ruta)

    print("Sesión: %s   (%d turnos)\n" % (os.path.basename(ruta), len(turnos)))

    if detalle:
        print("%4s %9s %10s %8s %10s" % ("#", "escribe", "relee", "produce", "prompt"))
        for i, t in enumerate(turnos, 1):
            print("%4d %9d %10d %8d %10d"
                  % (i, t["escribir_cache"], t["releer"], t["producir"],
                     t["escribir_cache"] + t["releer"]))
        print()

    # --- El arranque -------------------------------------------------------
    t1 = turnos[0]
    prefijo = t1["escribir_cache"] + t1["releer"]
    ultimo = turnos[-1]
    print("ARRANQUE")
    print("  Prefijo fijo (turno 1, antes de leer nada) : %8d" % prefijo)
    print("     - llegó ya en caché                     : %8d" % t1["releer"])
    print("     - hubo que escribir a caché             : %8d" % t1["escribir_cache"])
    print("     ^ ESTE REPARTO ES DE CACHÉ, NO DE CONTENIDO: dice qué parte del")
    print("       prefijo estaba ya cacheada, no qué lo pone. Para saber qué lo")
    print("       pone hay que mirar el tamaño de cada pieza, no esta línea.")

    # --- Dónde se fue la cuota --------------------------------------------
    tot = dict((k, sum(t[k] for t in turnos)) for k in PESO)
    efectivo = dict((k, v * PESO[k]) for k, v in tot.items())
    total = sum(efectivo.values()) or 1
    print("\nDÓNDE SE FUE LA CUOTA (pesado por lo que cuesta cada clase de token)")
    for k in ("releer", "escribir_cache", "producir"):
        print("  %-16s %9d tokens  ->  %5.1f%%" % (k, tot[k], efectivo[k] / total * 100))

    print("\n  Prompt al final de la sesión: %d tokens."
          % (ultimo["escribir_cache"] + ultimo["releer"]))
    print("  Cada turno relee todo lo anterior: el coste de releer crece con el cuadrado")
    print("  del número de turnos. Menos turnos sigue siendo la palanca mayor.")


if __name__ == "__main__":
    main()
