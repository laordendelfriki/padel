// Pruebas del barrio del modo carrera. Uso: THREE_JS=/ruta/three.min.js node tests/barrio.test.js [filtro]
const {openGame,test,run,assert}=require('./helpers');

async function withCar(opts,fn){const g=await openGame(opts);try{await g.page.evaluate(()=>{if(!window.__padel.CAR)window.__padel.newCar();});await fn(g);assert(!g.errors.length,'errores en la página: '+g.errors.join(' | '));}finally{await g.browser.close();}}

test('carAct buy descuenta dinero y equipa',async()=>withCar({},async({page})=>{
  const r=await page.evaluate(()=>{const P=window.__padel;P.CAR.money=1000;P.carAct('buy',{dataset:{id:'voltj'}});return {m:P.CAR.money,rk:P.CAR.rk,own:P.CAR.owned.includes('voltj')};});
  assert(r.m===400&&r.rk==='voltj'&&r.own,'resultado '+JSON.stringify(r));
}));

test('carrera antigua sin campos nuevos carga',async()=>{
  // genera una carrera, quita los campos nuevos y la carga de cero
  const g=await openGame({});let saved;
  try{saved=await g.page.evaluate(()=>{const P=window.__padel;P.newCar();const c=JSON.parse(JSON.stringify(P.CAR));for(const k of ['home','furn','wardrobe','outfit','acc','openWeek'])delete c[k];return c;});}finally{await g.browser.close();}
  const h=await openGame({car:saved});
  try{await h.page.evaluate(()=>document.querySelector('[data-go=car]').click());await h.page.waitForTimeout(800);assert(!h.errors.length,'errores: '+h.errors.join(' | '));}
  finally{await h.browser.close();}
});

test('hay ruta de la plaza a cada puerta y no cruza edificios',async()=>withCar({},async({page})=>{
  const bad=await page.evaluate(()=>{const P=window.__padel,out=[];
    const inside=(b,x,z,m)=>x>b.box[0]+m&&x<b.box[2]-m&&z>b.box[1]+m&&z<b.box[3]-m;
    for(const b of P.BAR_BLDS){const p=P.barrioPath({x:0,z:0},{x:b.door[0],z:b.door[1]});
      if(!p||p.length<2){out.push(b.id+': sin ruta');continue;}
      const e=p[p.length-1];if(Math.hypot(e.x-b.door[0],e.z-b.door[1])>0.3)out.push(b.id+': no llega a la puerta');
      for(let i=1;i<p.length;i++){const a=p[i-1],c=p[i],n=Math.ceil(Math.hypot(c.x-a.x,c.z-a.z)/0.2);
        for(let k=0;k<=n;k++){const x=a.x+(c.x-a.x)*k/n,z=a.z+(c.z-a.z)*k/n;for(const o of P.BAR_BLDS)if(inside(o,x,z,o===b?0.3:0)){out.push(b.id+': cruza '+o.id);k=n+1;break;}}}}
    return out;});
  assert(!bad.length,bad.join('; '));
}));

const visible=(page,sel)=>page.evaluate(s=>{const e=document.querySelector(s);return !!e&&e.classList.contains('on');},sel);

test('tocar la estación lleva andando y abre la carrera',async()=>withCar({},async({page})=>{
  await page.evaluate(()=>{window.__padel.barrioEnter();window.__padel.barrioGo('estacion');});
  await page.waitForFunction(()=>document.querySelector('#car').classList.contains('on'),null,{timeout:20000});
  const d=await page.evaluate(()=>{const B=window.__padel.BAR,b=window.__padel.BAR_BLDS.find(x=>x.id==='estacion');return Math.hypot(B.pos.x-b.door[0],B.pos.z-b.door[1]);});
  assert(d<0.4,'no llegó a la puerta: '+d);
}));

test('cambiar de destino a mitad de camino',async()=>withCar({},async({page})=>{
  await page.evaluate(()=>{window.__padel.barrioEnter();window.__padel.barrioGo('club');});
  await page.waitForTimeout(500);
  await page.evaluate(()=>window.__padel.barrioGo('estacion'));
  await page.waitForFunction(()=>document.querySelector('#car').classList.contains('on'),null,{timeout:25000});
  const d=await page.evaluate(()=>{const B=window.__padel.BAR,b=window.__padel.BAR_BLDS.find(x=>x.id==='estacion');return Math.hypot(B.pos.x-b.door[0],B.pos.z-b.door[1]);});
  assert(d<0.4,'terminó lejos de la estación: '+d);
}));

test('entrar y salir 3 veces no acumula memoria',async()=>withCar({},async({page})=>{
  const n=await page.evaluate(async()=>{const P=window.__padel,w=ms=>new Promise(r=>setTimeout(r,ms));
    P.barrioEnter();await w(400);P.barrioLeave();await w(200);const g0=P.G3.R.info.memory.geometries;
    for(let i=0;i<3;i++){P.barrioEnter();await w(400);P.barrioLeave();await w(200);}return P.G3.R.info.memory.geometries-g0;});
  assert(n<=5,'geometrías de más: '+n);
}));

test('gráficos 2D: lista de lugares',async()=>withCar({opt:{gfx:'2d'}},async({page})=>{
  await page.evaluate(()=>window.__padel.barrioEnter());
  const n=await page.evaluate(()=>{const l=document.querySelector('#barList');return l&&getComputedStyle(l).display!=='none'?l.querySelectorAll('button').length:0;});
  assert(n===7,'botones en la lista: '+n);
  await page.evaluate(()=>[...document.querySelectorAll('#barList button')].find(b=>b.dataset.id==='estacion').click());
  await page.waitForTimeout(300);assert(await visible(page,'#car'),'no abrió la carrera');
}));

test('tienda de pádel compra y equipa',async()=>withCar({},async({page})=>{
  await page.evaluate(()=>{const P=window.__padel;P.CAR.money=1000;P.barrioEnter();P.barrioOpen('padel');});
  await page.evaluate(()=>document.querySelector('#barPanel [data-act=buy][data-id=voltj]').click());
  const r=await page.evaluate(()=>({m:window.__padel.CAR.money,rk:window.__padel.CAR.rk}));
  assert(r.rk==='voltj'&&r.m===400,'resultado '+JSON.stringify(r));
}));

test('club: sesión con entrenador',async()=>withCar({},async({page})=>{
  const r=await page.evaluate(()=>{const P=window.__padel;P.CAR.money=100000;const sp=P.CAR.sp,m=P.CAR.money;P.barrioEnter();P.barrioOpen('club');
    const pr=P.coachPrice();document.querySelector('#barPanel [data-act=coach]').click();return {dsp:P.CAR.sp-sp,dm:m-P.CAR.money,pr};});
  assert(r.dsp===1&&r.dm===r.pr,'resultado '+JSON.stringify(r));
}));

test('del barrio al partido: el barrio se libera',async()=>withCar({},async({page})=>{
  await page.evaluate(()=>{window.__padel.barrioEnter();});await page.waitForTimeout(800);
  await page.evaluate(()=>{const P=window.__padel;P.carNext();P.playUserMatch('car');});
  await page.waitForTimeout(2500);
  const r=await page.evaluate(()=>{const P=window.__padel;return {on:P.BAR.on,scene:!!P.BAR.scene,S:!!P.S,tri:P.G3.R.info.render.triangles};});
  assert(!r.on&&!r.scene&&r.S&&r.tri>0,'resultado '+JSON.stringify(r));
}));

test('menú Carrera abre el barrio',async()=>withCar({},async({page})=>{
  await page.evaluate(()=>document.querySelector('[data-go=car]').click());await page.waitForTimeout(500);
  assert(await visible(page,'#barrio'),'no se abrió el barrio');
}));

test('comprar ropa de calle cambia la ropa del jugador del barrio',async()=>withCar({},async({page})=>{
  await page.evaluate(()=>{const P=window.__padel;P.CAR.money=1000;P.barrioEnter();});await page.waitForTimeout(600);
  const before=await page.evaluate(()=>window.__padel.BAR.P.sigB);
  await page.evaluate(()=>{window.__padel.barrioOpen('ropa');document.querySelector('#barPanel [data-x=cloth][data-id=tee_roja]').click();});
  await page.waitForTimeout(800);
  const r=await page.evaluate(()=>{const P=window.__padel;return {shirt:P.streetChar().shirt,rk:P.streetChar().noRk,sig:P.BAR.P.sigB,m:P.CAR.money};});
  assert(r.shirt==='#c1121f'&&r.rk&&r.sig!==before&&r.m===960,'resultado '+JSON.stringify(r));
}));

test('joystick: camina y no atraviesa edificios',async()=>withCar({},async({page})=>{
  const r=await page.evaluate(async()=>{const P=window.__padel,B=P.BAR,w=ms=>new Promise(r=>setTimeout(r,ms));P.barrioEnter();await w(300);
    // de frente hacia la tienda de pádel (al sur): la cámara mira hacia el norte, así que "abajo" en el joystick va al sur
    B.pos={x:2,z:4.6};B.camYaw=0;B.joy={x:0,y:1};await w(4000);B.joy={x:0,y:0};
    const b=P.BAR_BLDS.find(x=>x.id==='padel');return {z:B.pos.z,box0:b.box[1]};});
  assert(r.z>5&&r.z<r.box0,'posición '+JSON.stringify(r));
}));

test('entrar en la tienda de pádel, comprar y salir',async()=>withCar({},async({page})=>{
  const r=await page.evaluate(async()=>{const P=window.__padel,B=P.BAR,w=ms=>new Promise(r=>setTimeout(r,ms));P.CAR.money=1000;P.barrioEnter();await w(300);
    P.enterPlace('padel');const inside=B.mode;const st=B.inD.stations.find(s=>s.act==='panel:padel');B.pos={x:st.x,z:st.z};await w(400);
    const btn=document.querySelector('#barAct');const shown=btn.style.display!=='none';btn.click();
    document.querySelector('#barPanel [data-act=buy][data-id=voltj]').click();P.exitPlace();return {inside,shown,rk:P.CAR.rk,out:B.mode};});
  assert(r.inside==='padel'&&r.shown&&r.rk==='voltj'&&r.out==='out','resultado '+JSON.stringify(r));
}));

test('club: pista 1 empieza un partido abierto y se vuelve al club',async()=>withCar({},async({page})=>{
  await page.evaluate(async()=>{const P=window.__padel,B=P.BAR;P.barrioEnter();await new Promise(r=>setTimeout(r,300));P.enterPlace('club');P.barAction('open');});
  await page.waitForTimeout(800);
  const a=await page.evaluate(()=>{const P=window.__padel;return {open:P.S&&P.S.open,left:P.openLeft(),bar:P.BAR.on};});
  assert(a.open&&a.left===1&&!a.bar,'al empezar '+JSON.stringify(a));
  const r=await page.evaluate(async()=>{const P=window.__padel;const m0=P.CAR.money;P.S.over={winner:0};P.showEnd();const paid=P.CAR.money-m0;P.quitToMenu();await new Promise(r=>setTimeout(r,500));return {paid,prize:P.openPrize(),mode:P.BAR.mode,bar:P.BAR.on};});
  assert(r.paid===r.prize&&r.mode==='club'&&r.bar,'al terminar '+JSON.stringify(r));
}));

test('máximo 2 partidos abiertos por semana',async()=>withCar({},async({page})=>{
  const r=await page.evaluate(()=>{const P=window.__padel;P.CAR.openWeek={key:P.CAR.season+'-'+P.CAR.week,n:2};P.barrioEnter();P.enterPlace('club');P.barAction('open');return {S:!!P.S};});
  assert(!r.S,'empezó un tercer partido');
}));

test('comprar casa, comprar sofá y colocarlo',async()=>withCar({},async({page})=>{
  const r=await page.evaluate(async()=>{const P=window.__padel,w=ms=>new Promise(r=>setTimeout(r,ms));P.CAR.money=20000;P.barrioEnter();await w(200);
    P.barrioOpen('inmo');document.querySelector('#barPanel [data-x=home][data-id=apart]').click();
    P.barrioOpen('muebles');document.querySelector('#barPanel [data-x=furn][data-id=sofa]').click();
    P.enterPlace('casa');const n0=P.BAR.inD.scene.children.length;
    P.barrioOpen('casa');const sel=document.querySelector('#barPanel select[data-i="0"]');sel.value='sofa';sel.dispatchEvent(new Event('change',{bubbles:true}));
    return {cur:P.CAR.home.cur,m:P.CAR.money,slot:P.CAR.home.slots.apart&&P.CAR.home.slots.apart[0],more:P.BAR.inD.scene.children.length>n0,solids:P.BAR.inD.solids.length};});
  assert(r.cur==='apart'&&r.m===20000-15000-450&&r.slot==='sofa'&&r.more,'resultado '+JSON.stringify(r));
}));

module.exports={withCar};
if(require.main===module)run();
