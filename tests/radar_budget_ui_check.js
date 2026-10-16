const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const fields={},requests=[];
function el(id){return fields[id]??={id,value:'',checked:false,disabled:false,hidden:false,innerHTML:'',textContent:'',dataset:{},listeners:{},classList:{toggle(){}},
  addEventListener(k,f){this.listeners[k]=f},querySelectorAll(){return []},closest(){return el(id+'-label')},replaceChildren(){this.innerHTML=''},focus(){},scrollIntoView(){}};}
const tick=()=>new Promise(r=>setImmediate(r));
let authorized=false,authorizeReply, readinessItems=[], currentJob=null;
const tickers=['PETR4','VALE3','ITUB4','WEGE3','BBAS3'];
const money=()=>({runs:[],other_runs_reserved_usd:6.63552,run_reserved_usd:0,aggregate_exposure_usd:9.95328,aggregate_cap_usd:5,
  budget_token:'a'.repeat(64),planned:{tickers,calls_max:30,calls_planned:29,usd_reserved:3.31776},authorization:{required:true,state:authorized?'VALID':'ABSENT'}});
const run=()=>({id:'radar-current',session:'2026-10-13',universe:tickers,mode:'CONSULTATIVE_SANDBOX',state:'INPUTS_READY',reasons:[],treatment:{},budget:money(),budget_usd:3.5});
const view=()=>({run:run(),items:[],universe:tickers,examples:[],last_closed_session:'2026-10-13',csrf_token:'csrf',network_isolation:true,mutation_available:true,job:currentJob});
const preflight={ready:true,session:'2026-10-13',identity:'RADAR',confirmation_token:'sealed',items:tickers.map(ticker=>({ticker,ready:true,mode:'live',input_sha256:'hash',estimate:{calls_max:6}})),usd_estimated:.14625,usd_reserved:3.31776,max_usd:3.5,global_budget_used:0,global_budget_cap:5};
async function fetch(url,options={}){
  requests.push({url,options});let value;
  if(url.includes('radar-runs'))value={selected:'radar-current',runs:[run()]};
  else if(url.includes('radar-view'))value=view();
  else if(url.includes('radar-readiness'))value={items:readinessItems,summary:'inputs',run:'radar-current',session:'2026-10-13'};
  else if(url==='/api/platform/radar-budget-authorization')return new Promise(resolve=>{authorizeReply=()=>{authorized=true;resolve({ok:true,json:async()=>({provider_calls:0})})}});
  else if(url.includes('radar-budget'))value=money();
  else if(url==='/api/radar/preflight')value=preflight;
  else if(url==='/api/radar/prepare'){currentJob={id:'fixture',command:'prepare',status:'COMPLETED'};value={id:'fixture',status:'RUNNING'};}
  else throw Error('Unexpected endpoint '+url);
  return {ok:true,json:async()=>value};
}
let confirmations=0;
const ctx=vm.createContext({document:{getElementById:el},fetch,URLSearchParams,AbortController,location:{search:'',hash:''},history:{replaceState(){}},setTimeout,clearTimeout,setInterval(){},clearInterval(){},console});
ctx.window=ctx;ctx.addEventListener=()=>{};ctx.dispatchEvent=()=>{};ctx.PopStateEvent=class{};
ctx.HFL={confirmCost:async()=>{confirmations++;return false}};
vm.runInContext(fs.readFileSync(path.join(path.dirname(process.argv[2]),'market-ui.js'),'utf8'),ctx);
vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);
(async()=>{
  await tick();await tick();assert.equal(requests.some(r=>r.options.method==='POST'),false);
  await el('preflight').listeners.click();
  assert.equal(el('budget-review').hidden,false);assert.match(el('preflight-result').innerHTML,/revisão de orçamento pendente/);
  assert.equal(el('aggregate-budget').value,'');assert.equal(el('budget-consent').checked,false);
  el('paid').checked=true;el('paid').listeners.change();assert.equal(el('execute').disabled,true);
  el('aggregate-budget').value='5';el('aggregate-budget').listeners.input();el('budget-consent').checked=true;el('budget-consent').listeners.input();
  assert.equal(el('budget-authorize').disabled,true);
  el('aggregate-budget').value='10';el('aggregate-budget').listeners.input();
  assert.equal(el('budget-authorize').disabled,false);
  const first=el('budget-authorize').listeners.click();await tick();
  el('budget-authorize').listeners.click();await tick();
  const posts=requests.filter(r=>r.url.endsWith('radar-budget-authorization'));
  assert.equal(posts.length,1);assert.deepEqual(JSON.parse(posts[0].options.body),{run:'radar-current',budget_token:'a'.repeat(64),max_aggregate_usd:10,confirm:true});
  assert.equal(posts[0].options.headers['X-CSRF-Token'],'csrf');assert.equal(posts[0].options.headers['X-HFL-Radar-Run'],'radar-current');
  authorizeReply();await first;
  assert.equal(el('budget-review').hidden,true);assert.equal(el('paid').checked,false);assert.equal(el('execute').disabled,true);
  el('paid').checked=true;el('paid').listeners.change();assert.equal(el('execute').disabled,false);
  await el('execute').listeners.click();assert.equal(confirmations,1);
  assert.equal(requests.some(r=>r.url==='/api/radar/run'),false,'authorization alone and canceled paid confirmation never execute agents');
  el('budget').listeners.change();assert.equal(el('confirmation').hidden,true);
  el('paid').checked=true;el('paid').listeners.change();assert.equal(el('execute').disabled,true);
  preflight.ready=false;
  preflight.items=tickers.map(ticker=>({ticker,ready:false,error:'[Errno 2] No such file: input.json'}));
  readinessItems=tickers.map(ticker=>({ticker,input_state:'BLOCKED_DATA',error:'ValueError: no adjustment factor around 2026-10-14 <unsafe>',action:'Fator de ajuste Yahoo indisponível; aguarde a fonte.'}));
  await el('preflight').listeners.click();
  assert.match(el('preflight-result').innerHTML,/no adjustment factor around 2026-10-14/);
  assert.match(el('preflight-result').innerHTML,/Yahoo indisponível/);
  assert.ok(!el('preflight-result').innerHTML.includes('No such file'));
  assert.ok(el('input-check').innerHTML.includes('&lt;unsafe&gt;'));
  assert.ok(!el('preflight-result').innerHTML.includes('<unsafe>'));
  readinessItems=tickers.map(ticker=>({ticker,input_state:'PREPARING',action:'Aguarde o preparo.'}));
  const checks=requests.filter(r=>r.url==='/api/radar/preflight').length;
  await el('preflight').listeners.click();
  assert.equal(requests.filter(r=>r.url==='/api/radar/preflight').length,checks);
  assert.match(el('preflight-result').textContent,/Preparação em andamento/);
  assert.equal(el('confirmation').hidden,true);
  readinessItems=tickers.map(ticker=>({ticker,input_state:'BLOCKED_DATA',error:'no adjustment factor',action:'Aguardar dados.'}));
  await el('guided-check').listeners.click();
  const prepares=requests.filter(r=>r.url==='/api/radar/prepare');
  assert.equal(prepares.length,1);
  assert.deepEqual(JSON.parse(prepares[0].options.body),{tickers,session:'2026-10-13',mode:'live'});
  assert.equal(prepares[0].options.headers['X-HFL-Radar-Run'],'radar-current');
  assert.match(el('guided-status').textContent,/dados ainda não estão prontos/);
  assert.equal(requests.some(r=>r.url==='/api/radar/run'),false);
  console.log('PASS: budget review in UI, insufficient ceiling, explicit consent, double click, fresh preflight and separate paid confirmation');
})().catch(e=>{console.error(e);process.exitCode=1});
