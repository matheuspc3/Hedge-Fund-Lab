// Cycle view states (radar-analysis.js HFLCycle): node run against the snapshots radar.js and
// wallet-manager.js send. Usage: node tests/agent_cycle_check.js dashboard/radar-analysis.js
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx=vm.createContext({document:{getElementById:()=>null},console});ctx.window=ctx;
vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);
const {nodes,summary}=ctx.HFLCycle, tickers=['PETR4','VALE3','ITUB4','WEGE3','BBAS3'];
const states=s=>Object.fromEntries(nodes(s).map(n=>[n.id,n.state]));
const analysis={wallet:'Multiagentes',target:'2026-10-21',reference:'2026-10-20',created:'2026-10-20T20:56:00-03:00',changed:false};
const run=(opinions=0,auth='ABSENT')=>({id:'r',session:'2026-10-20',universe:tickers,opinions,budget:{authorization:{required:true,state:auth}}});
const radar=x=>({run:run(),job:null,last_prepare:null,readiness:[],readonly:false,report:null,review:false,paid:false,...x});
const entry=x=>({status:'PREPARED',context:{created_at:'2026-10-21T09:00:00-03:00',wallet:{name:'Multiagentes'}},result:null,compatible:true,...x});
const plan={completed_at:'2026-10-21T09:05:00-03:00',trades:[{ticker:'VALE3'}]};
const manager=x=>({s:entry(),consult:false,preview:false,inference:false,cost:true,...x});
// 20/10: every ticker blocked by a raw KeyError; the readiness action explains it in words
const raw={last_prepare:{generated_at:'2026-10-20T20:59:18-03:00',items:tickers.map(ticker=>({ticker,status:'BLOCKED',error:"KeyError: Timestamp('2026-10-20 00:00:00')"}))}};
let list=nodes({analysis,radar:radar(raw)}), data=list.find(n=>n.id==='data');
assert.equal(data.state,'blocked');assert.ok(data.reason.includes('KeyError'));assert.equal(data.diag,true);assert.equal(data.detail,'5/5 ativos bloqueados');
assert.equal(summary(list).node.id,'data');assert.ok(!summary(nodes({analysis,radar:radar({readiness:[{ticker:'PETR4',input_state:'BLOCKED_DATA',action:'Aguarde a B3.'}]})})).text.includes('..')); // a reason ending in a period
assert.ok(summary(list).state.startsWith('Bloqueado em Dados'));
assert.equal(list.find(n=>n.id==='budget').state,'pending'); // never "done" ahead of blocked data
const gap=tickers.map(ticker=>({ticker,input_state:'BLOCKED_DATA',error:'reference_session_not_yet_published_by_b3',action:'Pregão de 20/10/2026 ainda não publicado pela B3.'}));
data=nodes({analysis,radar:radar({...raw,readiness:gap})}).find(n=>n.id==='data');
assert.equal(data.state,'blocked');assert.equal(data.reason,'Pregão de 20/10/2026 ainda não publicado pela B3.'); // words over the raw error
assert.equal(states({analysis,radar:radar()}).data,'you'); // free check waits for a click
let s=states({analysis,radar:radar({report:{ready:true},review:true})});
assert.equal(s.data,'done');assert.equal(s.budget,'you');assert.equal(s.agents,'pending'); // budget consent first
s=states({analysis,radar:radar({run:run(0,'VALID'),report:{ready:true},paid:true})});
assert.equal(s.budget,'done');assert.equal(s.agents,'you');
list=nodes({analysis,radar:radar({run:run(2,'VALID'),job:{command:'run',status:'RUNNING',started_at:'2026-10-21T08:00:00-03:00'}})});
assert.equal(list.find(n=>n.id==='agents').state,'running');assert.equal(list.find(n=>n.id==='agents').detail,'2/5 pareceres');
// Confirming the batch deliberately clears the browser's preflight and checkboxes.
// Reloading/polling must derive completed steps from verified inputs and reservations.
for(const auth of ['NOT_REQUIRED','STALE']) {
  const running=radar({run:{...run(0,auth),inputs:5,integrity:'OK',usd_reserved:3.31776},job:{command:'run',status:'RUNNING',started_at:'2026-10-22T10:32:40-03:00'}});
  list=nodes({analysis,radar:running});s=states({analysis,radar:running});
  assert.equal(s.data,'done');assert.equal(s.budget,'done');assert.equal(s.agents,'running');
  assert.equal(summary(list).node.id,'agents');assert.equal(summary(list).state,'Analistas em andamento');
  const partial=radar({...running,run:{...running.run,opinions:2},last_prepare:raw.last_prepare,job:{command:'run',status:'COMPLETED',outcome:{state:'PARTIAL',summary:'3 comitês pendentes'}}});
  s=states({analysis,radar:partial});assert.equal(s.data,'done');assert.equal(s.budget,'done');assert.equal(s.agents,'blocked');
  assert.equal(summary(nodes({analysis,radar:partial})).node.id,'agents');
}
const verified={...run(0,'VALID'),inputs:5,integrity:'OK',usd_reserved:0};
s=states({analysis,radar:radar({run:verified})});assert.equal(s.data,'done');assert.equal(s.budget,'done');
s=states({analysis,radar:radar({run:{...verified,budget:{authorization:{required:true,state:'STALE'}}}})});
assert.equal(s.data,'done');assert.equal(s.budget,'pending'); // inputs alone never prove a paid consent
s=states({analysis,radar:radar({run:verified,readiness:[{ticker:'PETR4',input_state:'INTEGRITY_ERROR',action:'Revise a integridade.'}]})});
assert.equal(s.data,'blocked');assert.equal(s.budget,'pending'); // current errors still block
s=states({analysis,radar:radar({run:run(3,'VALID'),job:{command:'run',status:'COMPLETED',outcome:{state:'PARTIAL',summary:'2 comitês pendentes'}}})});
assert.equal(s.agents,'blocked');
const done=radar({run:run(5,'VALID'),job:{command:'run',status:'COMPLETED',started_at:'2026-10-21T08:00:00-03:00',finished_at:'2026-10-21T08:04:00-03:00',outcome:{state:'COMPLETED'}}});
assert.ok(nodes({analysis,radar:done}).find(n=>n.id==='agents').time.endsWith('4 min'));
assert.equal(states({analysis,radar:done,manager:manager({inference:true})}).manager,'you'); // paid manager consent
assert.equal(states({analysis,radar:done,manager:manager({s:entry({status:'RUNNING'})})}).manager,'running');
s=states({analysis,radar:done,manager:manager({s:entry({status:'VALID_PROPOSAL',result:plan})})});
assert.equal(s.manager,'done');assert.equal(s.preview,'you');assert.equal(s.approval,'pending');
s=states({analysis,radar:done,manager:manager({s:entry({status:'VALID_PROPOSAL',result:plan}),preview:true})});
assert.equal(s.preview,'done');assert.equal(s.approval,'you'); // financial approval waits for Lucas
const order={approved_at:'2026-10-21T09:10:00-03:00',leg:'CLOSE',session:'2026-10-21'};
list=nodes({analysis,radar:done,manager:manager({s:entry({status:'PENDING_AUCTION',result:plan,order})})});
assert.equal(list.find(n=>n.id==='auction').state,'waiting');assert.equal(list.find(n=>n.id==='auction').detail,'Aguardando o leilão de fechamento de 21/10/2026');
assert.equal(summary(list).state,'Aguardando o leilão de fechamento de 21/10/2026');
const intraday={...order,leg:'INTRADAY',session:'2026-10-22'};
list=nodes({analysis,radar:done,manager:manager({s:entry({status:'PENDING_INTRADAY',result:plan,order:intraday})})});
assert.equal(list.find(n=>n.id==='auction').name,'Execução');
assert.equal(list.find(n=>n.id==='auction').detail,'Aguardando preço intradiário de 22/10/2026');
assert.ok(list.find(n=>n.id==='auction').next.includes('posterior à aprovação'));
list=nodes({analysis,radar:done,manager:manager({s:entry({status:'EXECUTED',result:plan,order:intraday,execution:{...intraday,status:'EXECUTED',executed_at:'2026-10-22T10:52:00-03:00'}})})});
assert.ok(list.every(n=>n.state==='done'));assert.ok(!list.at(-1).detail.includes('leilão'));
list=nodes({analysis:{...analysis,changed:true},radar:done,manager:manager({s:entry({status:'EXECUTED',result:plan,order,execution:{status:'EXECUTED',leg:'CLOSE',session:'2026-10-21',executed_at:'2026-10-22T08:00:00-03:00'}})})});
assert.ok(list.every(n=>n.state==='done'));assert.equal(summary(list).state,'Ciclo concluído'); // its own order changed the wallet
assert.equal(states({analysis:{...analysis,changed:true},radar:radar()}).created,'blocked'); // a changed wallet needs a new analysis
s=states({analysis,radar:done,manager:manager({s:entry({status:'VALID_PROPOSAL',result:{...plan,trades:[]}})})});
assert.deepEqual([s.preview,s.approval,s.auction],['skipped','skipped','skipped']);
assert.equal(states({analysis,radar:done,manager:manager({s:entry({status:'EXPIRED',result:plan})})}).preview,'blocked');
assert.equal(states({analysis:null,radar:done,manager:null}).manager,'skipped'); // a run without a wallet
console.log('PASS: cycle view states: blocked data in words, free check, budget/paid/manager/approval consents waiting, live analysts, auction wait, completed cycle, skips and expiry');
