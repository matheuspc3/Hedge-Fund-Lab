// Actual shared shell action: no DOM framework and no real HTTP/provider request.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function app(){
  const fields={},pending=[],timers=[];
  const el=id=>fields[id]??={disabled:false,hidden:true,textContent:'',href:'',open:false,listeners:{},
    addEventListener(k,f){this.listeners[k]=f},setAttribute(){},showModal(){this.open=true},close(){this.open=false}};
  const context=vm.createContext({document:{querySelector:()=>null,getElementById:el},window:{addEventListener(){}},
    URLSearchParams,location:{reload(){}},setTimeout:f=>(timers.push(f),timers.length),clearTimeout(){},
    fetch:(url,options={})=>new Promise(resolve=>pending.push({url,options,reply:(d,ok=true)=>resolve({ok,json:async()=>d})}))});
  vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),context);
  const take=()=>{assert.ok(pending.length);return pending.shift()};
  return {el,pending,timers,take};
}
const tick=()=>new Promise(r=>setImmediate(r));
const view={run:{id:'radar-active',session:'2026-10-13',universe:['PETR4','VALE3'],mode:'CONSULTATIVE_SANDBOX'},
  csrf_token:'token',mutation_available:true,last_closed_session:'2026-10-13',job:null};
async function open(a,d=view){
  a.el('hfl-market-open').listeners.click();
  const registry=a.take();assert.equal(registry.url,'/api/platform/radar-runs');registry.reply({runner:'radar-active'});await tick();
  const state=a.take();assert.ok(state.url.includes('run=radar-active'));state.reply(d);await tick();
}
(async()=>{
  const a=app();assert.equal(a.pending.length,0,'page load must never fetch or prepare');
  await open(a);assert.equal(a.el('hfl-market-start').disabled,false);
  assert.match(a.el('hfl-market-scope').textContent,/13\/10\/2026.*PETR4, VALE3/);
  assert.equal(a.pending.length,0,'opening panel is read-only');
  a.el('hfl-market-start').listeners.click();a.el('hfl-market-start').listeners.click();
  assert.equal(a.pending.length,1,'double click must start only one job');
  const post=a.take();assert.equal(post.url,'/api/radar/prepare');assert.equal(post.options.method,'POST');
  assert.deepEqual(JSON.parse(post.options.body),{tickers:['PETR4','VALE3'],session:'2026-10-13',mode:'live'});
  assert.equal(post.options.headers['X-HFL-Radar-Run'],'radar-active');
  assert.equal(post.options.headers['X-CSRF-Token'],'token');
  post.reply({id:'job-1',status:'RUNNING'});await tick();
  a.timers.shift()();a.take().reply({...view,job:{id:'job-1',status:'RUNNING'}});await tick();
  assert.equal(a.el('hfl-market-start').disabled,true);
  a.timers.shift()();a.take().reply({...view,job:{id:'job-1',status:'COMPLETED',items:[{ticker:'PETR4',status:'PREPARED'},{ticker:'VALE3',status:'BLOCKED'}]}});await tick();
  assert.match(a.el('hfl-market-status').textContent,/bloqueios: VALE3/);
  assert.equal(a.el('hfl-market-reload').hidden,false);
  const resumed=app();await open(resumed,{...view,job:{id:'previous-prepare',command:'prepare',status:'RUNNING'}});
  assert.equal(resumed.pending.length,0);assert.equal(resumed.el('hfl-market-start').disabled,true);
  resumed.timers.shift()();resumed.take().reply({...view,job:{id:'previous-prepare',status:'COMPLETED',items:view.run.universe.map(ticker=>({ticker,status:'PREPARED'}))}});await tick();
  assert.match(resumed.el('hfl-market-status').textContent,/2 ativos/);
  const changed=app();await open(changed,{...view,job:{id:'prepare-1',command:'prepare',status:'RUNNING'}});
  changed.timers.shift()();changed.take().reply({...view,job:{id:'paid-2',command:'run',status:'COMPLETED'}});await tick();
  assert.match(changed.el('hfl-market-status').textContent,/registro da atualização mudou/);
  const refused=app();await open(refused,{...view,mutation_available:false});
  refused.el('hfl-market-start').listeners.click();assert.equal(refused.pending.length,0);
  assert.match(refused.el('hfl-market-status').textContent,/somente para consulta/);
  const missing=app();missing.el('hfl-market-open').listeners.click();missing.take().reply({runner:null});await tick();
  assert.equal(missing.el('hfl-market-start').disabled,true);
  assert.match(missing.el('hfl-market-status').textContent,/Nenhuma execução operacional/);
  const failure=app();await open(failure);failure.el('hfl-market-start').listeners.click();
  failure.take().reply({error:'radar_busy_or_stale_lock'},false);await tick();
  assert.match(failure.el('hfl-market-status').textContent,/operação ativa/);assert.equal(failure.timers.length,0);
  console.log('PASS: explicit shared preparation, scope/CSRF, double click, resume, partial failure, changed job and read-only gates');
})().catch(e=>{console.error(e);process.exitCode=1});
