# Registro de bugs

> **Síntoma → causa → solución.** Un bloque por bug, numerado, con estado.
>
> ⚠️ **La trampa de este documento**: *un bug registrado describe el sistema del día en que se
> escribió*. Cuarenta bugs abiertos no son cuarenta cosas rotas — son cuarenta **anotaciones**, y
> varias describen un sistema que ya no existe.
>
> 🔑 **Antes de ponerse con un bug antiguo, comprobar contra el sistema real que sigue estando.**
> El registro es una libreta, no un diagnóstico.

**Estados**: 🔴 abierto · 🟡 a medias · 🟢 cerrado · ⚪ ya no aplica

---

## BUG-001 🔴 \<título: el síntoma en una línea, no la causa\>

**Detectado**: \<fecha\> · **Dónde**: `<fichero o servicio>`

**Síntoma** — qué se ve, desde donde lo ve el usuario:
\<Lo observable. No la teoría.\>

**Causa** — por qué pasa:
\<La causa real, cuando se conoce. Si aún no se conoce, decir «sin diagnosticar» en vez de poner
una hipótesis con cara de hecho.\>

**Alcance** — a cuántos casos afecta, **medido**:
\<Una cifra y cómo se sacó. «Parece que a varios» no es un alcance.\>

**Solución** — qué habría que hacer:
\<Y si la solución es cambiar un criterio, decirlo: arreglar los casos visibles de un bug de
criterio lo deja vivo, y vuelve a nacer con el siguiente dato que entre.\>

**Bloqueado por**: \<otro bug, un permiso, una decisión\>

---

## BUG-002 🟢 \<título\> — CERRADO el \<fecha\>

**Qué era**: \<una línea\>
**Cómo se arregló**: \<una o dos líneas\>
**Cómo se verificó**: \<con qué se comprobó que de verdad está arreglado, y **por dónde entra el
usuario** — un arreglo verificado solo en la pantalla de desarrollo no está verificado\>
