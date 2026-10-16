// Exercise the actual page script with Python read-model values, not JS prices.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const views=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
function app(search){
  const fields={},pending=[];
  function el(id){return fields[id]??={value:'',textContent:'',innerHTML:'',hidden:true,
    listeners:{},parentElement:{hidden:false},replaceChildren(){this.textContent='';this.innerHTML='';},
    addEventListener(k,f){this.listeners[k]=f},setAttribute(){},contains(){return false}};}
  const document={getElementById:el,documentElement:{},querySelectorAll:()=>[]};
  const window={addEventListener(){}};
  class Chart{destroy(){}}
  const ctx=vm.createContext({document,window,Chart,URLSearchParams,AbortController,
    getComputedStyle:()=>({getPropertyValue:()=> '#a1edcb'}),location:{search,hash:'',replace(){}},
    history:{replaceState(){}},fetch:(url)=>new Promise(resolve=>pending.push({url,
      reply:(data,ok=true)=>resolve({ok,json:async()=>data})})),console});
  vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);
  return {fields,pending,el};
}
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
  const normal=app('');assert.equal(normal.pending.length,0,'default page must not load synthetic or H2 data');
  normal.el('home-laboratory').open=true;
  normal.el('home-laboratory').listeners.toggle();
  assert.equal(normal.pending.length,1);
  assert.equal(normal.pending[0].url,'/api/platform/overview');
  normal.pending.shift().reply({observed_at:'2026-10-14T12:00:00-03:00',global_records:[],jobs:{available:true,data:[]}});await tick();
  assert.ok(!normal.el('home-state').innerHTML.includes('PETR4'));
  assert.equal(normal.pending.length,0);
  const missing=app('?demo=1');missing.pending.shift().reply({available:false,message:'Missing export'});await tick();
  assert.match(missing.el('pilot-wallet').innerHTML,/Indisponível/);
  assert.equal(missing.el('pilot-content').hidden,true);
  const a=app('?demo=1');assert.equal(a.pending.length,1);assert.ok(a.pending[0].url.startsWith('/api/portfolio/pilot?'));
  a.pending.shift().reply(views[0]);await tick();
  assert.equal(a.el('pilot-content').hidden,false);
  const initial=a.el('pilot-equity').textContent;
  a.el('pilot-wallet').value=views[1].wallet;a.el('pilot-wallet').listeners.change();
  const old=a.pending.shift();
  a.el('pilot-period').value='month';a.el('pilot-period').listeners.change();
  a.pending.shift().reply(views[1]);await tick();
  const current=a.el('pilot-equity').textContent;assert.notEqual(current,initial);
  old.reply(views[0]);await tick();assert.equal(a.el('pilot-equity').textContent,current);
  assert.match(a.el('pilot-variation').textContent,/Histórico insuficiente/);
  a.el('pilot-session').value='2026-11-03';a.el('pilot-session').listeners.change();
  assert.equal(a.el('pilot-content').hidden,true);assert.equal(a.el('pilot-equity').textContent,'');
  a.pending.shift().reply({},false);await tick();
  assert.equal(a.el('pilot-error').hidden,false);assert.equal(a.el('pilot-content').hidden,true);
  assert.equal(a.el('pilot-equity').textContent,'');
  console.log('default opt-in, stale reply, period selection and error clearing: PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
