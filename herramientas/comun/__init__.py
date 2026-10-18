# -*- coding: utf-8 -*-
u"""El código que varias herramientas necesitan, escrito una vez.

**Por qué existe**: en el proyecto de origen, una misma función de normalizar texto estaba escrita
18 veces en 14 ficheros, y las copias no eran iguales —unas pasaban a minúsculas y otras no—. Cada
copia es un sitio donde el criterio puede quedarse atrás sin que nadie lo note. Aquí vive **una
vez**, y las diferencias que eran de verdad **se dicen con un parámetro**, en vez de esconderse en
una copia.

**Qué entra aquí** (criterio, no lista):
  * una función que aparece **igual o casi igual en dos o más herramientas** y no depende de un
    frente concreto del proyecto. Lo de un solo frente va a su propio módulo compartido.
  * cada pieza nueva entra **probada contra la copia que sustituye**: si da otro resultado, la
    diferencia se escribe en el docstring de la función.

**Qué NO puede importar esto** 🔑: las herramientas que **también corren en otra máquina**. Si el
despliegue sube un fichero suelto, `comun/` no viaja con él y allí reventaría al importar. Esas
conservan su copia hasta que el despliegue lleve `comun/` consigo.

El porqué largo, en `LA_BIBLIOTECA.md`.

    from comun import git as g        # lo que el protocolo pregunta a git (carpetas, ramas, almacén común)
"""
