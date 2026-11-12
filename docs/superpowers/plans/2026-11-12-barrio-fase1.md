# Barrio – Fase 1: Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Barrio 3D en miniatura donde el jugador de carrera camina hasta donde tocas y entra en los edificios; la estación, la tienda de pádel y el club ya funcionan con lo que existe hoy.

**Architecture:** Todo en `index.html`, sección nueva `/* ============ BARRIO ============ */` antes de `/* ---------- cámara de televisión`. El barrio es una escena Three.js propia (`BAR.scene`) dibujada con el **mismo** `G3.R`; `render3D()` la pinta en lugar del estadio mientras `BAR.on`. El jugador es `mkHuman3`/`mkPlayer3` animado con `pose3` (paso de partido) a velocidad de paseo. Las acciones de compra y entrenador se sacan del manejador de la pantalla de carrera a una función común `carAct`.

**Tech Stack:** HTML/JS sin compilar, Three.js 0.160 (CDN), pruebas con Playwright (Chromium ya instalado) en scripts Node.

**Spec:** `docs/superpowers/specs/2026-11-12-barrio-carrera-design.md`

## Global Constraints
- Un solo `index.html` (+ `players/`); sin dependencias nuevas en tiempo de ejecución.
- Nunca crear otro `WebGLRenderer` ni otro contexto WebGL: usar `G3.R`.
- No tocar `pose3`, `armPose`, `updateFacing`, `applyPoseHum`, `updPlayer3` (golpes como los quiere Xavi).
- Lo nuevo que se guarde va dentro de `CAR` con valores por defecto en `carMigrate`.
- Textos de la interfaz en español.
- Llegar a un torneo desde el barrio: como mucho 2 toques (botón fijo "🏆 Torneos").
- Niveles de gráficos: `OPT.gfx` `'2d'` → barrio como lista de lugares; `'3dl'` → muñeco ligero; resto → realista.

## Review Focus
1. Empezar un partido de torneo desde el barrio: la escena del barrio se libera y el partido se ve con el estadio normal (prueba en Task 4).
2. Tocar otro sitio mientras el jugador camina: cambia de ruta sin atascarse (prueba en Task 3).
3. Partida de carrera guardada antes de esta versión: entra al barrio sin errores (prueba en Task 1).
4. Gráficos en 2D: el barrio sale como lista y los lugares funcionan (prueba en Task 3).
5. Entrar y salir del barrio varias veces no acumula memoria gráfica (prueba en Task 3).

---

### Task 1: Pruebas automáticas y acciones de carrera reutilizables

**Files:**
- Create: `tests/helpers.js`, `tests/barrio.test.js`
- Modify: `index.html` (manejador de clics de la pantalla de carrera, alrededor de `a==='buy'`/`a==='coach'`; `window.__padel` al final)

**Interfaces:**
- Produces: `carAct(act:string, el:HTMLElement|{dataset:object}) -> void` (ejecuta `buy`, `equip`, `coach`, `plus`… exactamente como hoy y llama a `saveCar()`/`buildCar()` como hoy). `window.__padel` expone además `CAR` (getter), `carAct`, `newCar`, `BAR` (getter, Task 2+).
- Produces (tests): `openGame(opts?) -> {browser,page}` en `tests/helpers.js`: arranca `python3 -m http.server` en un puerto libre, abre Chromium con `--enable-unsafe-swiftshader --ignore-gpu-blocklist`, sirve Three.js desde `process.env.THREE_JS` (o `require.resolve('three/build/three.min.js')`) y corta fuentes/PeerJS/Firebase; `opts.opt` pre-carga `localStorage.padel_opt`, `opts.car` pre-carga `padel_car`.

- [ ] **Step 1: Prueba que falla** `tests/barrio.test.js` → `test('carAct buy descuenta dinero y equipa')`: crea carrera (`__padel.newCar` con el jugador por defecto), pone `CAR.money=1000`, `carAct('buy',{dataset:{id:'voltj'}})` → `CAR.money===400 && CAR.rk==='voltj' && CAR.owned.includes('voltj')`. Y `test('carrera antigua sin campos nuevos carga')`: pre-carga un `padel_car` sin `home/furn/wardrobe` (copiar uno generado por `newCar` y borrar esos campos) → abrir Carrera no lanza `pageerror`.
- [ ] **Step 2:** `node tests/barrio.test.js` → FAIL (`carAct is not a function`).
- [ ] **Step 3:** Sacar el cuerpo del manejador actual a `carAct(act, el)`; el manejador queda `carAct(t.dataset.act, t)`. Exponer en `window.__padel`.
- [ ] **Step 4:** `node tests/barrio.test.js` → PASS (2/2).
- [ ] **Step 5:** Commit `Pruebas de barrio y acciones de carrera reutilizables`.

### Task 2: Escena del barrio y caminos

**Files:**
- Modify: `index.html` (sección BARRIO nueva)
- Test: `tests/barrio.test.js`

**Interfaces:**
- Produces: `BAR = {on:false, scene:null, cam:null, P:null, nodes:[], edges:[], blds:[], path:[], pos:{x,z}, dest:null}`.
- Produces: `BAR_BLDS` — constante con los 7 edificios: `{id, n, door:[x,z], box:[x0,z0,x1,z1], col}` con ids `casa, inmo, muebles, ropa, padel, club, estacion` y nombres `Tu casa, Inmobiliaria, Muebles, Ropa, La Orden del Friki – Pádel, Club, Estación`. Barrio de 60 × 40 m centrado en el origen, plaza con fuente en el centro.
- Produces: `buildBarrio3() -> THREE.Scene` (suelo, calles, plaza, fuente, edificios con rótulo de `cTex`, árboles con `InstancedMesh`, bancos, farolas, una pista de pádel en el club, sol con sombras, cielo de día) y rellena `BAR.nodes/edges` (red de puntos de paso por las calles, incluido un nodo en cada puerta).
- Produces: `barrioPath(from:{x,z}, to:{x,z}) -> Array<{x,z}>` — une `from` y `to` al nodo más cercano y devuelve la ruta más corta (Dijkstra) por la red; nunca cruza el `box` de un edificio.
- Produces: `disposeBarrio3() -> void` — libera geometrías, materiales y texturas de `BAR.scene` y del jugador del barrio.

- [ ] **Step 1: Prueba que falla** `test('hay ruta de la plaza a cada puerta y no cruza edificios')`: para cada `b` de `BAR_BLDS`, `p=barrioPath({x:0,z:0},{x:b.door[0],z:b.door[1]})` → `p.length>=2`, último punto a <0,3 m de la puerta, y ningún segmento de `p` (muestreado cada 0,2 m) cae dentro de un `box` ajeno (permitido entrar 0,3 m en el propio).
- [ ] **Step 2:** Ejecutar → FAIL.
- [ ] **Step 3:** Implementar `BAR_BLDS`, red de nodos, `barrioPath`, `buildBarrio3`, `disposeBarrio3`.
- [ ] **Step 4:** Ejecutar → PASS.
- [ ] **Step 5:** Commit `Barrio: escena 3D y caminos`.

### Task 3: Pantalla del barrio, caminar tocando y entrar

**Files:**
- Modify: `index.html` (HTML: `<div id="barrio" class="screen">` con capa de botones; CSS; `render3D`; eventos de toque)
- Test: `tests/barrio.test.js`

**Interfaces:**
- Consumes: Task 2.
- Produces: `barrioEnter() -> void` (requiere `CAR`; si `want3D()&&G3.on` construye la escena si no existe, crea el jugador con `CHARS[CAR.me]`, `BAR.on=true`; si no, muestra la lista de lugares `#barList`), `barrioLeave() -> void` (`BAR.on=false`, `disposeBarrio3()`), `barrioGo(id:string) -> void` (calcula ruta a la puerta y camina), `barrioOpen(id:string) -> void` (Task 4 la completa; aquí: `estacion` → `buildCar();showScreen('car')`, resto → aviso "Próximamente"), `barrioTick(dt:number) -> void` (avanza 1,6 m/s por `BAR.path`, orienta al jugador, anima con `pose3(C,{gait,mv:[0,v,v],time,seed:0})`; al llegar a una puerta llama `barrioOpen`).
- Toque/clic sobre el lienzo con `BAR.on`: rayo contra edificios (→ `barrioGo(id)`) o suelo (→ caminar a ese punto). Arrastrar >8 px mueve la cámara; al soltar vuelve sola.
- `render3D()`: si `BAR.on`, actualiza cámara (diagonal desde arriba, sigue al jugador) y `G3.R.render(BAR.scene,BAR.cam)`; no pinta el estadio ni la capa 2D de partido.
- Capa fija: botones `🏆 Torneos` (→ `barrioOpen('estacion')`) y `📋 Carrera` (→ `buildCar();showScreen('car')`), nombre del lugar al que vas.

- [ ] **Step 1: Pruebas que fallan**
  - `test('tocar la estación lleva andando y abre la carrera')`: `barrioEnter()`, `barrioGo('estacion')`, esperar ≤15 s → pantalla `car` visible; la posición recorrió la ruta (distancia final a la puerta <0,4 m).
  - `test('cambiar de destino a mitad de camino')`: `barrioGo('club')`, a los 0,5 s `barrioGo('estacion')` → termina en la estación.
  - `test('entrar y salir 3 veces no acumula memoria')`: guardar `G3.R.info.memory.geometries` tras el primer `barrioLeave()`; tras 3 ciclos más, diferencia ≤ 5.
  - `test('gráficos 2D: lista de lugares')`: `openGame({opt:{gfx:'2d'}})`, `barrioEnter()` → `#barList` visible con 7 botones; pulsar Estación → pantalla `car`.
- [ ] **Step 2:** Ejecutar → FAIL.
- [ ] **Step 3:** Implementar pantalla, CSS, `barrioEnter/Leave/Go/Open/Tick`, toques y la rama de `render3D`; llamar `barrioTick` desde `frame()` cuando `BAR.on`.
- [ ] **Step 4:** Ejecutar → PASS. Captura en móvil horizontal (844×390) y revisarla.
- [ ] **Step 5:** Commit `Barrio: caminar tocando y entrar en los sitios`.

### Task 4: Lugares de la fase 1 y el barrio como inicio de la carrera

**Files:**
- Modify: `index.html` (`barrioOpen`; navegación `data-go="car"`; vuelta de torneo en `showBracket`/`afterUserMatch` para `kind==='car'`; botón "🏘️ Barrio" en la pantalla de carrera; `newMatch` llama `barrioLeave()`)
- Test: `tests/barrio.test.js`

**Interfaces:**
- Consumes: `carAct` (Task 1), `barrioEnter/Leave/Open` (Task 3).
- Produces: `barPanel(html:string) -> void` (panel modal dentro de `#barrio`, botón cerrar), `carHome() -> void` (si hay `CAR` → `barrioEnter()`, si no → `buildCar();showScreen('car')`).
- `padel` → panel con las palas de `RACKETS` (precio, mejoras, Comprar/Equipar con `data-act` y `carAct`), título "La Orden del Friki – Pádel".
- `club` → panel con "🏋️ Sesión con entrenador" (`carAct('coach')`, mismo precio `coachPrice()`) y "🎯 Entrenar" (el entrenamiento de siempre con `CAR.me` como jugador).
- `casa`, `inmo`, `muebles`, `ropa` → panel "Próximamente" con una frase de lo que habrá.
- Menú `Carrera` con `CAR` existente → `carHome()`; tras un torneo de carrera, el botón de vuelta va a `carHome()`.

- [ ] **Step 1: Pruebas que fallan**
  - `test('tienda de pádel compra y equipa')`: `CAR.money=1000`, `barrioOpen('padel')`, clic en Comprar de `voltj` → `CAR.rk==='voltj'`, dinero 400.
  - `test('club: sesión con entrenador')`: dinero suficiente, clic → `CAR.sp` +1 y dinero −`coachPrice()` previo.
  - `test('del barrio al partido: el barrio se libera')`: `barrioEnter()`, jugar el primer partido del torneo (`carNext` + `playUserMatch('car')`) → `BAR.on===false`, `BAR.scene===null`, y `render3D` dibuja el estadio (`G3.R.info.render.triangles>0` con `S` activo).
  - `test('menú Carrera abre el barrio')`: con `CAR`, clic en `[data-go=car]` → `#barrio` visible.
- [ ] **Step 2:** Ejecutar → FAIL.
- [ ] **Step 3:** Implementar paneles, `carHome`, cambios de navegación y `barrioLeave()` en `newMatch`.
- [ ] **Step 4:** Ejecutar todas las pruebas → PASS; partido completo de torneo jugado por bots sin `pageerror`.
- [ ] **Step 5:** Commit `Barrio: tienda de pádel, club y barrio como inicio de la carrera`.

---

## Fases siguientes (planes propios cuando toque)
- **Fase 2 – Ropa**: catálogo, probador con el jugador realista, armario; `CAR.wardrobe`, `CAR.outfit`; ropa propia fuera de torneos y del patrocinador en torneos.
- **Fase 3 – Casa**: inmobiliaria (piso gratis, apartamento 15.000 €, casa 60.000 €, ático 200.000 €), interior 3D, tienda de muebles (~30, de 50 € a 5.000 €), modo decorar en cuadrícula con giro, paredes y suelo, vitrina de trofeos y palas.
- **Fase 4 – Vida**: partidos abiertos (100–400 €, sin ranking, máx. 2 por semana), 3–4 vecinos, accesorios de pádel.
