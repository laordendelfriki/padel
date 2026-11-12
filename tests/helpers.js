// Utilidades para las pruebas automáticas del juego (Playwright + Chromium sin GPU).
const {chromium}=require('playwright');
const {spawn}=require('child_process');
const path=require('path');
const net=require('net');
const ROOT=path.resolve(__dirname,'..');

function threePath(){
  if(process.env.THREE_JS)return process.env.THREE_JS;
  try{return require.resolve('three/build/three.min.js');}catch(e){}
  throw new Error('Falta Three.js: define THREE_JS=/ruta/three.min.js o instala "three"');
}
function freePort(){return new Promise(res=>{const s=net.createServer();s.listen(0,()=>{const p=s.address().port;s.close(()=>res(p));});});}
let SERVER=null,PORT=0;
async function server(){
  if(SERVER)return PORT;PORT=await freePort();
  SERVER=spawn('python3',['-m','http.server',String(PORT)],{cwd:ROOT,stdio:'ignore'});
  for(let i=0;i<50;i++){const ok=await new Promise(r=>{const c=net.connect(PORT,'127.0.0.1',()=>{c.end();r(true);});c.on('error',()=>r(false));});if(ok)break;await new Promise(r=>setTimeout(r,100));}
  return PORT;
}
// opts.opt / opts.car: valores para localStorage antes de cargar; opts.viewport
async function openGame(opts={}){
  const port=await server();
  const browser=await chromium.launch({args:['--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
  const page=await browser.newPage({viewport:opts.viewport||{width:960,height:540}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route(/three\.min\.js/,r=>r.fulfill({path:threePath(),contentType:'application/javascript'}));
  await page.route(/fonts\.(googleapis|gstatic)|gstatic\.com|peerjs/,r=>r.abort());
  await page.addInitScript(([o,c])=>{try{if(o)localStorage.setItem('padel_opt',JSON.stringify(o));if(c)localStorage.setItem('padel_car',typeof c==='string'?c:JSON.stringify(c));}catch(e){}},[opts.opt||null,opts.car||null]);
  await page.goto(`http://127.0.0.1:${port}/index.html`);
  await page.waitForFunction(()=>window.__padel,null,{timeout:20000});
  if(opts.wait3d!==false&&!(opts.opt&&opts.opt.gfx==='2d'))await page.waitForFunction(()=>window.__padel.G3&&(window.__padel.G3.on||window.__padel.G3.failed),null,{timeout:30000}).catch(()=>{});
  return {browser,page,errors};
}
const results=[];
function test(name,fn){results.push({name,fn});}
async function run(){
  const only=process.argv[2];let ok=0,fail=0;
  for(const t of results){if(only&&!t.name.includes(only))continue;
    try{await t.fn();ok++;console.log('✓',t.name);}catch(e){fail++;console.log('✗',t.name,'\n   ',(e&&e.message||e).split('\n')[0]);}}
  console.log(`\n${ok} ok, ${fail} fallan`);if(SERVER)SERVER.kill();process.exit(fail?1:0);
}
function assert(c,msg){if(!c)throw new Error(msg||'assert');}
module.exports={openGame,test,run,assert};
