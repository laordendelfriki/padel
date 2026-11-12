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

module.exports={withCar};
if(require.main===module)run();
