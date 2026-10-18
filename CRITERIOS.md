# Criterios

Lo que no se vuelve a razonar. Cada uno se escribe **con el caso que lo produjo**, porque una regla
sin su historia se salta a la primera prisa.

Están destilados de un proyecto real de un año. Los casos son suyos; las reglas no — por eso están
aquí.

---

## Parte 1 · Cómo se mide sin engañarse

> Esta es la parte que más veces ha evitado un desastre, y la que menos intuitiva resulta. Casi
> todos los errores caros del proyecto de origen fueron **una medida que parecía buena**.

### 1. Antes de optimizar algo, medir qué fracción del problema es

El arranque de cada sesión costaba 61.101 tokens y la intuición decía, unánimemente, que sobraba
documentación. Al medirlo: **el 81% era el prefijo del entorno** —herramientas, reglas, memoria— y
los documentos propios eran el 19%. Podar documentación atacaba un quinto del problema.

🔑 **El corolario, que es el que duele**: una medida *aproximada pero coherente* es la más difícil
de corregir, porque explica lo suficiente como para dejar de buscar.

### 2. El cero de «no había nada que medir» se imprime igual que el cero de «está limpio»

Son la misma cifra y significan lo contrario. Un medidor apuntó a una carpeta que no existía y
devolvió **cero apariciones**; se leyó como «limpio». Con la ruta correcta eran veintiséis.

El fallo no fue la ruta. Fue que la función **devolvía lista vacía cuando el directorio no existía y
seguía como si nada**.

👉 La solución en código está en [`herramientas/terreno.py`](herramientas/terreno.py): antes de
medir, se exige la raíz contra la que se mide, y si no está **se grita en vez de devolver cero**.

### 3. Una medida no vale más que su acceso

Un barrido por SSH informaba sobre 58 carpetas de artefactos. Cuarenta y cinco pertenecían a otro
usuario: el barrido **veía el 22% del parque** y presentaba el resultado como si fuera el total.

🔑 Una medida hecha desde donde no se ve todo **no avisa de que no lo ve todo**. Hay que preguntarlo
aparte: *¿desde aquí se ve el 100%?*

### 4. Un resultado unánime es un resultado sospechoso — el 100% igual que el 0%

Una sonda que dice «45 de 45 sanos» no vale nada hasta que **caza un caso malo conocido**. Un
barrido que falla en todo no es un hallazgo: es una herramienta rota.

🔑 **La regla operativa**: antes de creerte una sonda, dale de comer un caso que sabes que está mal.
Si no lo caza, lo que mide es otra cosa.

### 5. La vara y el control que la juzga no pueden caerse por lo mismo

Si el comprobante que valida tu medidor comparte con él la ruta, la conexión o la suposición que
falla, los dos mienten a la vez y en la misma dirección — que es como no tener control.

### 6. Una medida contesta su pregunta, no la tuya

Antes de usar una cifra que ya tienes, releer **qué preguntaba exactamente**. Una cifra que
«casi» responde a lo que quieres saber es peor que no tenerla.

### 7. Un reparto no dice nada hasta saber según qué eje reparte

Un medidor partía el gasto en dos columnas y se leyó como «qué lo pone». No era eso: era **cómo se
almacenó**, otro eje completamente distinto. La tabla era correcta; la lectura, no.

🔑 **Cuando un número reparte un total, preguntar según qué eje lo reparte** antes de sacar
conclusiones.

### 8. Contar apariciones no es contar cosas

Mirar siempre qué unidad cuenta la cifra: ¿ficheros, o líneas? ¿elementos, o veces que aparece un
elemento? La confusión no se nota nunca en el número — se nota en la decisión que se toma con él.

### 9. Un comentario del código no es una medida

Lo que dice la cabecera de un fichero sobre lo que hace el fichero es **una afirmación sin
verificar**, del día en que se escribió. Se comprueba corriendo el código, no leyéndolo.

### 10. Medir un defecto exige antes definirlo, o se «arregla» lo que estaba bien

Si no puedes escribir en una frase qué cuenta como defectuoso, el barrido que escribas contará otra
cosa — y la lista de «arreglados» incluirá casos que nunca estuvieron rotos.

---

## Parte 2 · Cómo se decide

### 11. Criterios generales, nunca listas de casos

Si una solución enumera nombres de ficheros, URLs o valores concretos, **está mal aunque hoy
funcione**. Funciona hasta el primer caso que nadie apuntó, y entonces falla en silencio.

🔑 **Y lo peor**: *una lista de casos puede estar equivocada entera y parecer que funciona*, porque
los casos que contiene sí pasan.

La prueba: *¿esto seguiría funcionando en el proyecto siguiente, con datos distintos?*

### 12. Un bug de criterio no se cierra arreglando los casos que se ven

Si la causa es un criterio mal escrito, arreglar los diez casos visibles deja el criterio intacto y
el bug **vuelve a nacer** con el siguiente dato que entre. Se cierra cambiando el criterio.

### 13. Si dos sitios pintan lo mismo, uno de los dos tiene que callarse

Dos lugares que muestran o calculan lo mismo **divergen**. No es una posibilidad, es cuestión de
semanas. El criterio vive en un sitio y los demás lo llaman.

Su versión en el mundo del código: cinco copias del mismo programa, y no había dos iguales. Arreglar
la fábrica no arreglaba la fábrica, porque la que corría era otra copia.

### 14. Antes de arreglar una fábrica, comprobar cuál es la que corre

Corolario del anterior, y hay que hacerlo **primero**: verificar qué versión está realmente en
ejecución antes de tocar nada. El tiempo perdido arreglando la copia equivocada no se recupera.

### 15. Una fábrica probada por partes no está probada

Un componente llevaba un día dado por «cerrado» tras probar sus piezas por separado. Cubría media
fábrica. Lo encontró **fabricar algo de verdad, de principio a fin**.

🔑 **La prueba de una fábrica es un producto terminado**, no la suma de sus piezas verdes.

### 16. Un molde no se prueba con los casos que ya tenías

Al generalizar algo, lo que era cierto «por casualidad» en los casos existentes pasa a ser falso. El
molde se prueba con **un caso nuevo**, uno que no existía cuando se escribió.

### 17. Un arreglo que no llega a la pantalla por donde se entra no está terminado

Se arregló algo y se verificó en la pantalla de desarrollo. El usuario entra por otra, y ahí seguía
roto. **La verificación se hace por donde entra el usuario**, no por donde es cómodo mirar.

### 18. Sustituir no es lo mismo que añadir: exige probar que no se pierde nada

Añadir solo puede fallar en lo nuevo. Sustituir puede romper en silencio algo que llevaba un año
funcionando, y el síntoma aparece semanas después, lejos del cambio.

### 19. Antes de leer una fuente, preguntar si se necesita

Aplica igual a un documento de 400 líneas que a una consulta cara: la pregunta *«¿me hace falta esto
para el paso que voy a dar?»* es gratis, y casi siempre la respuesta es no.

---

## Parte 3 · Cómo se opera sin romper nada

### 20. La copia de seguridad no te salva; te salva la comprobación

Una copia que nadie ha restaurado nunca es una **suposición**, no una copia. Lo que salva es haber
comprobado que se puede restaurar — y eso se comprueba antes de necesitarlo.

### 21. Una regla que depende de que alguien la teclee no es una regla

Si cumplirla exige acordarse, se incumple. Lo que no está automatizado o comprobado por un programa
es una intención.

De ahí que los mapas se generen y que las varas de medida sean código, no instrucciones.

### 22. Un valor por defecto que apunta a lo que no está es peor que ninguno

Un defecto que apunta a una ruta inexistente convierte «no configurado» en «cero resultados», que se
lee como éxito. Sin defecto, habría fallado ruidosamente en el primer intento.

### 23. Un dato guardado no puede depender de desde dónde se ejecutó quien lo guardó

Rutas relativas, directorios de trabajo, entornos: si el dato almacenado cambia según quién y desde
dónde lo escribió, lo que tienes no es un dato, es un accidente.

### 24. Comprobar antes de subir, no subir para comprobar

Parece lo mismo y no lo es: subir para comprobar deja el sistema roto durante la comprobación, y en
un entorno que alguien usa a diario, eso es su día de trabajo.

### 25. Un bug registrado describe el sistema del día en que se escribió

Un registro con cuarenta bugs abiertos no dice que haya cuarenta cosas rotas. Dice que hay cuarenta
**anotaciones**, y varias describen un sistema que ya no existe.

🔑 **Antes de ponerse con un bug antiguo, comprobar contra el sistema real que sigue estando.**

### 26. Nada se toca en el entorno real sin avisar antes

Si el sistema lo usa una persona a diario, reiniciarlo no es una operación técnica: es interrumpirle
el día. Se pregunta. Siempre. Aunque sea obvio, aunque sea rápido, aunque ya se hiciera ayer.

### 27. El código que corre fuera se cambia en un solo sitio, y se despliega en un solo sentido

Si unas cosas se arreglan en el servidor y se traen, y otras se arreglan en casa y se suben, tarde o
temprano un despliegue borra un arreglo que solo vivía allí. **Casa manda**, la otra máquina no se
parchea en sitio, y el despliegue compara tres huellas —casa, servidor y la del último despliegue—
para saber **quién** cambió cada fichero. Si cambió allí, se niega entero. Detalle en `LA_BIBLIOTECA.md` §4.

### 28. Una receta que el agente va a ejecutar solo se prueba al escribirla, no al correrla

Cada orden que escribe, seguida de su comprobación; cada dirección y cada fichero, abiertos al prepararla
**desde donde se van a usar**; y una regla de parada. Cuando una sesión se atasca siguiendo una receta,
casi siempre el fallo es de la receta, no del modelo que la sigue.

---

## Parte 4 · Sobre el propio protocolo

### 29. Lo compartible es cómo se trabaja, no con qué se trabaja

El material de un proyecto es suyo y no le sirve a nadie más. El método sí.

### 30. Dos copias del mismo texto no se mantienen

Vale para el código, para la documentación y para los ficheros de instrucciones de los agentes. Si
un texto tiene que estar en dos sitios, uno de los dos es un puntero al otro.

### 31. El coste de releer crece con el cuadrado de los turnos

Un mensaje intermedio no cuesta lo que ocupa: cuesta eso multiplicado por todos los turnos que
vengan después. De ahí que se trabaje seguido y se informe una vez.

### 32. Lo que el agente lee al arrancar es el diseño más importante del proyecto

Es lo único que sabe. Todo lo demás —lo bien documentado que esté el resto, lo ordenado que sea el
repositorio— solo cuenta si el arranque lo alcanza.

### 33. El modelo se elige al abrir la sesión, y se dice al cerrar la anterior

Cambiar de modelo a mitad no hereda la caché ni el razonamiento: se repaga el arranque entero. Por eso
cada paso planificado lleva su modelo, los pasos seguidos del mismo modelo van juntos, y la sesión que
cierra dice con cuál se abre la siguiente — al arrancar ya llega tarde.

### 34. Una sesión viva sigue costando aunque nadie le hable

Cada mensaje que recibe se paga releyendo todo su historial. Cuando el trabajo pasa a otra sesión, la
vieja se archiva en el acto, sin esperar su informe: lo que tenía que decir ya está en el diario.
