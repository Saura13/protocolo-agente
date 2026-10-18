# -*- coding: utf-8 -*-
u"""¿Vigila `comprobar_cierre.py` cada mapa contra SU código, y sin que le engañen las fechas en disco?

Contesta: ¿cada mapa se compara solo con el código que declara, lo excluido no cuenta, una carpeta nueva con la marca entra sola, y una carpeta de trabajo recién creada no da rojos falsos?
Toca: solo una copia aparte, en una carpeta temporal que se borra al acabar; el repositorio de verdad no se toca.
Necesita: git.

Monta su propio repositorio de juguete, con su configuración, y repite cinco casos. Sale 1 si alguno falla.

    python herramientas/probar_cierre_mapas.py
"""
import io, json, os, re, shutil, subprocess, sys, tempfile, time

HERR = os.path.dirname(os.path.abspath(__file__))
t = tempfile.mkdtemp(prefix="mapas_")
os.chdir(t)
os.makedirs("herramientas")
for f in os.listdir(HERR):
    if f.endswith(".py"):
        shutil.copy(os.path.join(HERR, f), "herramientas")
if os.path.isdir(os.path.join(HERR, "comun")):
    shutil.copytree(os.path.join(HERR, "comun"), "herramientas/comun")
def w(p, s=""):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(s)
def git(*a):
    subprocess.run(["git"] + list(a), check=True, capture_output=True)
def cierre():
    r = subprocess.run([sys.executable, "herramientas/comprobar_cierre.py"], capture_output=True, text=True, encoding="utf-8")
    out = r.stdout
    return re.search(r"3\. Los mapas.*?(?=\n\d\. )", out, re.S).group(0)

w("src/a.py", "x=1\n"); w("herramientas_mias/h.py", "'''h'''\n"); w("herramientas_mias/_usados/viejo.py", "")
w("fab1/MARCA", ""); w("fab1/f.py", ""); w("deep/fab2/MARCA", "")
for m in ("MAPA_CODIGO", "MAPA_HERR", "MAPA_FAB", "MAPA_FUERA", "MAPA_ROTO"):
    w("docs/%s.md" % m, "mapa\n")
cfg = {"zonas": [{"titulo": "src", "ruta": "src"}], "extensiones": [".py"], "excluir": ["__pycache__"],
       "cierre": {"mapas": ["docs/MAPA_CODIGO.md",
                            {"mapa": "docs/MAPA_HERR.md", "codigo": ["herramientas_mias"], "excluir": ["_*"]},
                            {"mapa": "docs/MAPA_FAB.md", "codigo": ["*/MARCA", "*/*/MARCA"]},
                            {"mapa": "docs/MAPA_FUERA.md", "codigo": [], "por_que": "vive en otra máquina"},
                            {"mapa": "docs/MAPA_ROTO.md", "codigo": ["no_existe"]}]}}
w("protocolo.config.json", json.dumps(cfg))
git("init", "-q", "-b", "master"); git("config", "user.name", "p"); git("config", "user.email", "p@p")
git("add", "-A"); git("commit", "-qm", "todo junto")
r = cierre(); print(r)
assert r.count("[OK]") == 3 and "no se vigila: vive en otra máquina" in r and "no_existe" in r

# 1. Las fechas en disco no mandan: todo el código «nuevo» en disco, pero guardado → sigue al día
time.sleep(1.1)
for p in ("src/a.py", "herramientas_mias/h.py", "fab1/f.py"):
    os.utime(p, None)
r = cierre(); assert "MAPA_CODIGO.md — al día" in r and "MAPA_FAB.md — al día" in r, r
print("✓ 1 · tocar la fecha de un fichero guardado no pone rojo (carpeta de trabajo nueva)")

# 2. Un cambio sin guardar en lo que mapea → rojo; en lo excluido (_usados) → no
time.sleep(1.1); w("herramientas_mias/_usados/viejo.py", "cambio\n")
r = cierre(); assert "MAPA_HERR.md — al día" in r, r
w("herramientas_mias/h.py", "'''h2'''\n")
r = cierre(); assert "MAPA_HERR.md — más viejo" in r and "MAPA_CODIGO.md — al día" in r, r
print("✓ 2 · cada mapa solo mira lo suyo, y lo excluido no cuenta")

# 3. Regenerar el mapa (sin guardar) lo pone al día; commit del código después del mapa → rojo
time.sleep(1.1); w("docs/MAPA_HERR.md", "mapa nuevo\n")
r = cierre(); assert "MAPA_HERR.md — al día" in r, r
git("add", "docs/MAPA_HERR.md"); git("commit", "-qm", "mapa")
time.sleep(1.1); git("add", "herramientas_mias/h.py"); git("commit", "-qm", "codigo despues")
r = cierre(); assert "MAPA_HERR.md — más viejo" in r, r
print("✓ 3 · regenerar pone al día; un commit de código posterior al mapa pone rojo")

# 4. Una carpeta nueva con la marca entra sola
time.sleep(1.1); w("nueva/MARCA", ""); w("nueva/g.py", "")
r = cierre(); assert "MAPA_FAB.md — más viejo que su código (3 carpetas)" in r, r
print("✓ 4 · la carpeta que nace con la marca queda vigilada sin tocar la configuración")

# 5. Sin git: la fecha en disco, como antes
shutil.rmtree(".git", onerror=lambda f, p, e: (os.chmod(p, 0o700), f(p)))
r = cierre(); assert "MAPA_CODIGO.md" in r, r
print("✓ 5 · sin git, la fecha en disco (lo de siempre)")
os.chdir(HERR)
shutil.rmtree(t, ignore_errors=True)
print("\n✓ todo bien")
