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

module.exports={withCar};
if(require.main===module)run();
