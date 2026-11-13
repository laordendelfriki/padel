# El barrio: vida fuera de la pista en el modo carrera

## Intención y por qué
Xavi quiere que la carrera dé **la sensación de poder hacer cosas aparte de jugar partidos**: vivir en un barrio relajado con todo a mano, comprarse una casa o un apartamento y amueblarla, comprar ropa y material de pádel. Los partidos siguen siendo el centro; el barrio es lo que hay entre torneo y torneo y lo que hace que tu jugador "tenga una vida".

## Objetivos
- Un **barrio pequeño en 3D** (maqueta vista desde arriba en diagonal) donde tu jugador realista **camina hasta donde tocas** y entra en los sitios.
- **Tu casa**: empiezas en un piso de alquiler; con el dinero de los torneos compras apartamento o casa; **amueblas y decoras** colocando muebles en una cuadrícula.
- **Tienda de ropa**: compras camisetas, pantalones, zapatillas, gorras y cintas; tu jugador las lleva puestas.
- **Tienda de pádel** (con la estética de La Orden del Friki): las palas que ya existen y accesorios.
- **Club**: entrenador (lo que ya hay), entrenamiento y **partidos abiertos** sueltos.
- **Salida a torneos**: un edificio que lleva al calendario de siempre.

## No objetivos
- **Casa, muebles, ropa y accesorios son solo estéticos** (decisión de Xavi). No dan estadísticas ni energía. Las **palas** siguen siendo lo único que mejora el juego, como ahora.
- No hay andar libre con joystick (eso sería la opción A; solo si la C no convence).
- No hay multijugador ni otros jugadores reales en el barrio.
- No se usan marcas reales; todas inventadas, salvo La Orden del Friki.

## Anti-objetivos (sería un fracaso aunque funcione)
- Que el barrio **estorbe** para ir a jugar: llegar a un torneo nunca puede costar más de un par de toques.
- Que vaya **pesado en el móvil** o que rompa el partido (el barrio no puede dejar memoria ocupada al jugar).
- Que se **pierdan las partidas guardadas** de carrera que ya existen.
- Que sea una forma de **ganar dinero infinito** que vacíe de sentido los torneos.

## Restricciones
- Todo vive en `index.html` (+ carpeta `players/`), Three.js 0.160 por CDN, web para móvil y PC, instalable.
- Guardado en `localStorage` (`padel_car`) y sincronizado con Google (Firebase) como ya está: lo nuevo va **dentro de `CAR`** para que se guarde y sincronice solo.
- Los tres niveles de gráficos existentes: *3D realistas*, *3D ligeros* (muñeco de antes) y *2D clásicos*.
- Los golpes y movimientos de partido **no se tocan** (Xavi los quiere como están).
- Hay un límite de contextos WebGL por página: el barrio usa **el mismo renderizador** (`G3.R`), nunca uno nuevo.

## Enfoques considerados
| | Cómo es | A favor | En contra |
|---|---|---|---|
| A | Barrio 3D andando con joystick, interiores 3D | Lo más inmersivo | Mucho trabajo, pesado en móvil, joystick incómodo por calles |
| B | Mapa dibujado, tocas edificios y se abren pantallas | Rápido y ligero | No se siente que paseas: es otro menú |
| **C (elegido)** | **Maqueta 3D desde arriba; tocas y el jugador va andando solo; casa en 3D con muebles en cuadrícula** | Sensación de vivir en el barrio, cómodo con el dedo, reutiliza el motor y los jugadores realistas | Más trabajo que B |

Xavi eligió **C**; si al verla no convence, se prueba **A**.

## Diseño

### Entrada y salida
- En la pantalla de carrera aparece **"🏘️ Ir al barrio"**. El barrio es el sitio principal de la carrera, pero **nada se pierde**: la pantalla de carrera actual sigue existiendo y se abre desde el edificio de torneos o desde un botón fijo en la esquina.
- Al terminar un torneo vuelves al barrio.
- Botón fijo **"🏆 Torneos"** en la esquina del barrio: llegar a jugar es siempre un toque.

### El barrio (escena 3D)
- Unos **60 × 40 m**, de día, luz cálida, calles peatonales, una plaza con fuente, árboles, bancos y farolas. Estilo maqueta: edificios sencillos de formas limpias con colores vivos y rótulos.
- Edificios (cada uno con su rótulo y su puerta):
  1. **Tu casa** (cambia de aspecto según la vivienda que tengas).
  2. **Inmobiliaria** (comprar viviendas).
  3. **Muebles** (tienda de decoración).
  4. **Ropa** (tienda de moda deportiva).
  5. **Tienda de pádel – La Orden del Friki** (palas y accesorios; escaparate con cartas y figuras).
  6. **Club** con una pista de pádel visible (entrenar, entrenador, partidos abiertos).
  7. **Estación** (torneos: abre el calendario de siempre).
- **Moverse**: tocas el suelo o un edificio → el jugador va andando por las calles (red de puntos de paso; nada de atravesar edificios) → al llegar a una puerta se abre ese sitio. Se puede tocar otro sitio a mitad de camino.
- **Cámara**: fija en diagonal desde arriba, sigue suavemente al jugador; se puede arrastrar para mirar el barrio y vuelve sola.
- **Vecinos**: 3 o 4 personas paseando o sentadas en bancos, para que el barrio tenga vida.
- **Animación de andar**: la que ya usa el jugador al correr en partido, a velocidad de paseo.

### Tu casa
- **Viviendas** (se compran en la inmobiliaria; las que compras son tuyas para siempre y puedes elegir en cuál vives):
  | Vivienda | Precio | Suelo (casillas de 0,5 m) |
  |---|---|---|
  | Piso de alquiler | gratis (la de partida) | 8 × 8 |
  | Apartamento | 15.000 € | 12 × 10 |
  | Casa con jardín | 60.000 € | 16 × 12 |
  | Ático de lujo | 200.000 € | 20 × 14 |
- Dentro: una habitación 3D vista desde arriba en diagonal, con ventana y puerta. Tu jugador aparece dentro y pasea.
- **Modo decorar**: abres tu inventario de muebles, eliges uno, tocas una casilla del suelo (o de pared, para cuadros) para colocarlo, un botón para **girarlo 90°**, tocas uno ya puesto para **moverlo o guardarlo**. No se pueden solapar.
- **Pintura y suelo**: eliges color de paredes y tipo de suelo (gratis o muy baratos).
- **Vitrina de trofeos** automática con los títulos que has ganado y **soporte de pared** con las palas que tienes: decoración que cuenta tu carrera.

### Tienda de muebles
- Unos **30 muebles** hechos con formas sencillas en 3D: sofá, cama, mesa, sillas, mesita, televisión, estantería, lámpara, planta, alfombra, cuadros, consola de videojuegos, estantería de cartas y figuras (guiño friki), mesa de ping-pong, bicicleta estática, etc.
- Precios de **50 € a 5.000 €**. Puedes comprar varias unidades del mismo.
- Cada mueble se ve girando en 3D antes de comprarlo.

### Tienda de ropa
- Camisetas (varios colores y estampados), pantalones, zapatillas, gorras y cintas, muñequeras. Precios de **30 € a 400 €**.
- **Probador**: ves a tu jugador realista con la prenda antes de comprar (como el creador de jugador).
- **Armario**: lo comprado se guarda; te cambias en la tienda o en casa.

### Tienda de pádel (La Orden del Friki)
- Las **palas que ya existen** (`RACKETS`): se compran y equipan aquí, con sus mejoras de siempre.
- **Accesorios estéticos**: color de grip/overgrip, muñequeras, paletero (se ve en tu casa), bolas de colores para la vitrina, etc.

### Club
- **Entrenador**: la sesión de mejora que ya existe.
- **Entrenamiento**: los ejercicios con máquina que ya existen, gratis.
- **Partidos abiertos**: partido rápido contra una pareja amateur de tu nivel, con tu compañero actual. Premio pequeño (100–400 € según tu nivel), **sin puntos de ranking** y **como máximo 2 por semana de calendario** (para que no se convierta en una fábrica de dinero).

### Guardado
- Todo nuevo dentro de `CAR`, con valores por defecto en `carMigrate` para que las partidas antiguas sigan funcionando:
  - `CAR.home = {owned:['piso'], cur:'piso', layouts:{piso:[{id,x,z,rot}]}, wall:{piso:'#...'}, floor:{piso:'madera'}}`
  - `CAR.furn = {sofa:2, ...}` (inventario sin colocar)
  - `CAR.wardrobe = [ids de prendas]`, `CAR.outfit = {shirt,shorts,shoes,head,band}`
  - `CAR.acc = [ids de accesorios]`
  - `CAR.openWeek = {week, n}` (partidos abiertos jugados esta semana)

### Rendimiento
- El barrio es **otra escena** del mismo renderizador; se construye al entrar y se libera al salir (y al empezar un partido).
- Edificios y muebles con pocas formas, árboles instanciados, sombras solo del sol, como mucho **5 personas** realistas a la vez.
- *3D ligeros*: el barrio usa el muñeco de antes. *2D clásicos*: el barrio se muestra como una lista de lugares (sin 3D) y las tiendas funcionan igual.

### Fases de construcción
1. **Barrio** con todos los edificios, caminar tocando y entrar; estación, tienda de pádel (palas) y club (entrenador y entrenamiento) conectados a lo que ya existe.
2. **Tienda de ropa** con probador y armario.
3. **Casa**: inmobiliaria, interior 3D, tienda de muebles y modo decorar, vitrina de trofeos.
4. **Partidos abiertos**, vecinos y detalles.

Cada fase se publica por separado para que Xavi la pruebe.

## Decisiones tomadas por mí (Xavi puede cambiarlas)
- Precios de viviendas, muebles y ropa de la tabla de arriba, pensados para que la casa cara sea un objetivo de temporadas.
- Partidos abiertos: máximo 2 por semana, sin ranking, premio pequeño.
- La pantalla de carrera actual se mantiene accesible.
- Vecinos con 3–4 personas.

## Decidido con Xavi (aprobó las propuestas)
- **Ropa en torneos**: si tienes patrocinador de ropa/zapatillas, en los torneos llevas su equipación (como ahora, con su pequeño extra). En el barrio, en casa y en partidos abiertos llevas tu ropa comprada. Sin patrocinador, llevas siempre la tuya.
- **El barrio es el sitio principal de la carrera**: al entrar en la carrera apareces en el barrio. La pantalla de carrera actual sigue accesible desde la estación y desde un botón fijo; ir a un torneo es siempre un toque.

Estado: **aprobado** por Xavi el 12/11/2026.

## Lo que queda a criterio de quien construya
- El aspecto exacto de cada edificio y la distribución del barrio dentro de lo descrito.
- El catálogo concreto de muebles, prendas y accesorios, y el ajuste fino de precios.
- Cómo se calculan los caminos (red de puntos de paso u otra forma sencilla).

## Cambio a la opción A (13/11/2026)
Tras probar la C, Xavi pidió el estilo NBA 2K / The Grounds: **joystick en tercera persona** por el barrio, **entrar dentro** de cada sitio al estilo GTA y un **club con pistas** donde entras y juegas. Además, en el barrio tu jugador va **de calle, sin pala**. Se construyó todo de una vez:
- Fuera: joystick (o WASD), cámara detrás que sigue al jugador, arrastrar para girar la cámara, choques con edificios y fuente, botón de acción junto a cada puerta.
- Dentro: interiores 3D de La Orden del Friki – Pádel (palas y accesorios), Ropa (calle y equipaciones de juego, probador/armario), Muebles, Inmobiliaria (4 viviendas), Tu casa (huecos para muebles, vitrina de trofeos y palas en la pared) y Club (recepción, pista 1 de partidos abiertos, pista 2 de entrenamiento).
- Partidos abiertos: máx. 2 por semana, premio 100–400 € si ganas, sin ranking; al terminar vuelves al club.
- La equipación de juego comprada se usa en los partidos cuando no hay patrocinador de ropa.
