# Agent Protocol

**A method for running a long project with an AI agent without it losing the thread between
sessions.**

*[🇪🇸 Léelo en castellano](README.es.md) — the protocol documents themselves are in Spanish.
See [Language](#language) below.*

It is not a library and not a tool. It is **six documents and nine programs** that solve one
concrete problem: when a project runs for months, every session starts blind. You explain
everything again, you pay for the whole context, and the agent still makes decisions that
contradict last week's.

This protocol was written while working, not in the abstract. It came out of a real year-long
project, and every rule here exists because something broke first.

---

## The problem, in one sentence

> An agent has no memory between sessions. All it knows is what it reads at startup.
> **So what it reads at startup is the most important design decision in the project.**

Three decisions follow from that, and they govern everything else:

1. **Startup is a budget, not a greeting.** Every line the agent reads at the start is paid for in
   **every** session, forever. A 400-line document opened "just in case" costs more than the work
   it was meant to enable.
2. **Each document has one job and only one.** What is open, where we are, what happened, what is
   broken, what we learned. The moment two documents say the same thing, one of them is lying —
   and you don't know which.
3. **Maps are generated, not written.** A hand-maintained index points at the wrong lines as soon
   as someone moves a function. An index that lies is worse than no index.

---

## What is here

| File | What it solves |
|:---|:---|
| **[`AGENTS.md`](AGENTS.md)** | The startup-map template. **The central piece**: what the agent reads when it opens each session |
| **[`CLAUDE.md`](CLAUDE.md)** | A one-line pointer to `AGENTS.md`, because Claude Code does not read `AGENTS.md` natively |
| **[`PROTOCOLO_SESION.md`](PROTOCOLO_SESION.md)** | How a session is opened, run and closed. The checklist before closing |
| **[`LOS_DOCUMENTOS.md`](LOS_DOCUMENTOS.md)** | The fixed job of each document, its line ceiling, and what does *not* go in it |
| **[`CRITERIOS.md`](CRITERIOS.md)** | The lessons that outlive the project. Above all: how to measure something without fooling yourself |
| **[`herramientas/`](herramientas/)** | The programs: three generate maps, one measures what a session costs, one **checks that you are allowed to close**, and four that **let you ask the documents instead of reading them** (`indice.py`, `consultar.py`, `apuntar.py`, `generar_vias.py`) |
| **[`plantillas/`](plantillas/)** | The empty documents, ready to copy |

---

## Getting started

```bash
git clone <this-repository> && cd protocolo-agente
```

1. Copy `AGENTS.md`, `CLAUDE.md` and the `plantillas/` folder into the root of your project.
2. Fill in the `<placeholders>` in `AGENTS.md`. There are deliberately few.
3. Copy `herramientas/` and create your `protocolo.config.json` (there is an example inside).
4. Generate the first code map:

```bash
python herramientas/generar_mapa_codigo.py
```

5. Before closing the session, check that you can:

```bash
python herramientas/comprobar_cierre.py
```

6. And measure what it cost:

```bash
python herramientas/medir_cuota_sesion.py
```

7. Once the documents grow, stop reading them whole. Build the index and ask it:

```bash
python herramientas/indice.py                       # generates the SQLite index (no dependencies)
python herramientas/consultar.py "what touches X"   # ten chunks with file:line
python herramientas/apuntar.py                      # writes diary entries and notices, under lock
python herramientas/generar_vias.py                 # builds the tracks sheet from one card per track
```

Everything is configured in `protocolo.config.json` (`indice`, `vias`, `avisos`, character ceilings in `cierre`).

8. **Before writing a new tool, ask whether one already exists** (`consultar.py` and `MAPA_HERRAMIENTAS.md`).
   Every tool carries its **card** in the docstring — `Contesta:` / `Toca:` / `Necesita:` (answers / touches /
   needs), one line each — and `generar_mapa_herramientas.py` collects it, adds what the code shows (network,
   remote shell, language model, database, which other tools it imports) and **flags a card that says
   "read-only" when the code writes**. What gets set aside goes to a shelf without being renamed:
   `_usados/AAAA-MM/` (one-off scripts), `datos/` (data) and `comun/` (shared code) — details in `AGENTS.md`.

That last number is the one that orders everything else. **Before optimising anything, measure what
fraction of the problem it is.** In the project this came from, startup cost 61,101 tokens and
intuition said there was too much documentation — but once measured, **81% was environment
configuration** and the project's own documents were 19%. Pruning documents would have attacked one
fifth of the problem.

---

## Which agents this works with

The content lives in **`AGENTS.md`**, the open standard that since December 2025 is governed by the
Linux Foundation's Agentic AI Foundation and is read by more than thirty agents: OpenAI Codex,
GitHub Copilot, Cursor, Gemini CLI, Google Antigravity, OpenCode, Zed, Windsurf, Aider, Jules,
Devin.

**Claude Code is the exception**: it does not read `AGENTS.md` natively. That is why this repository
ships a `CLAUDE.md` that **does not duplicate the content** — it imports it in one line.

> ⚠️ **Do not copy the same text into several files.** It is the obvious temptation and it rots on
> its own: three weeks later no two copies match and nobody knows which one is authoritative. The
> content lives in `AGENTS.md`; everything else points at it.

---

## Language

The five protocol documents are **written in Spanish**, and this README is the English entry point.
That is a deliberate choice rather than an oversight:

- The documents you are reading here are read **once, by a person**. They cost the agent nothing.
- The files that are actually loaded into every session — `AGENTS.md` and `plantillas/` — are where
  language costs tokens, and they are the ones worth translating first.
- Translating everything would mean two full copies of the same rules, which is precisely the
  failure this repository warns against in the box above.

**If you want an English `AGENTS.md` and templates, open an issue.** That is the translation that
pays for itself, and it will be done properly — with one version declared authoritative — rather
than by duplicating the lot.

---

## Licence

MIT. Use it, cut it up, change it.
