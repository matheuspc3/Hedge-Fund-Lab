"""Exercise the actual workflow script with delayed, out-of-order GET replies."""

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_preflight_consent_and_selection_races():
    script = r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const fields={},pending=[],posts=[],symbols=['PETR4','VALE3','ITUB4','WEGE3','BBAS3'];
function element(id){return fields[id]??={value:'',checked:false,disabled:false,hidden:false,textContent:'',innerHTML:'',listeners:{},addEventListener(k,f){this.listeners[k]=f},querySelectorAll(){return symbols.map(value=>({value}))},close(){this.open=false},showModal(){this.open=true}}}
element('workflow-mode').value='CONSULTATIVE_SANDBOX';element('workflow-budget').value='0.25';
const document={getElementById:element,querySelectorAll:()=>Object.values(fields)};
function fetch(url,options){return new Promise(resolve=>{const req={url,options,reply:(data,ok=true)=>resolve({ok,json:async()=>data})};pending.push(req);if(options?.method==='POST')posts.push(req)})}
function take(part){const i=pending.findIndex(r=>r.url.includes(part));assert.ok(i>=0,'missing '+part);return pending.splice(i,1)[0]}
const tick=()=>new Promise(r=>setImmediate(r));
// A script that stalls on a never-resolved request must fail, not exit silently.
let done=false;process.on('exit',()=>{if(!done)process.exitCode=1});
const ctx=vm.createContext({document,fetch,URLSearchParams,location:{search:''},history:{replaceState(){}},window:{dispatchEvent(){}},CustomEvent:class{},crypto:{randomUUID:()=> 'a'.repeat(32)},setTimeout,clearTimeout,console});
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);
const fire=(id,event)=>element(id).listeners[event]();
const selection={mode:'SYNTHETIC_DEMO',session:'2026-10-09',selected:symbols,missing:[],items:symbols.map(ticker=>({ticker,status:'ELIGIBLE'})),radar_cost_preview:{calls_max:0,usd_reserved:'0'},global_pm_cost_preview:{usd_reserved_ceiling:'0'}};
const detail={id:'v7-'+'b'.repeat(32),native_state:'AWAITING_PREFLIGHT',state:'PREPARED',mode:'SYNTHETIC_DEMO',valuation_session:'2026-10-09',portfolio:{equity:'100000',cash:{available:'100000'},initial_capital:'100000'},opinions:Object.fromEntries(symbols.map(t=>[t,{}])),created_at:'2026-10-11T20:00:00Z',expires_at:'2026-10-12T20:00:00Z',context_sha256:'c'.repeat(64)};
const preflight={ready:true,state:'READY',paid:false,confirmation_token:'token',context_sha256:'c'.repeat(64),expires_at:detail.expires_at,errors:[],max_usd:'0.25'};
(async()=>{
 take('/api/forward/status').reply({csrf_token:'csrf'});await tick();
 take('/api/radar/status').reply({last_closed_session:'2026-10-09'});await tick();
 take('/api/platform/jobs').reply({jobs:[],global_records:[]});await tick();
 take('/api/global-pm/selection').reply(selection);await tick();
 // A loaded record brings its actual mode/session/selection into the form.
 element('workflow-record').value=detail.id;let loading=fire('workflow-record','change');
 take('/api/platform/global?id=').reply(detail);await loading;
 assert.equal(element('workflow-mode').value,'SYNTHETIC_DEMO');
 assert.equal(element('workflow-session').value,'2026-10-09');
 // V7.6.2 (HFL-UX-001): HFL-MULTIASSET-GLOBAL-PM-V1 is closed for new inferences in the
 // panel. Before V7.6.2 this test drove preflight -> run -> confirmation -> prepare; those
 // triggers must now do nothing and send nothing, while consultation and offline recovery stay.
 fire('workflow-preflight','click');await tick();
 assert.equal(pending.filter(r=>r.url.includes('global-preflight')).length,0);
 assert.equal(element('workflow-preflight').disabled,true);assert.equal(element('workflow-run').disabled,true);
 fire('workflow-run','click');assert.notEqual(element('workflow-confirm').open,true);
 element('workflow-paid').checked=true;fire('workflow-authorize','click');
 element('workflow-hypothetical').checked=element('workflow-fixture').checked=true;
 fire('workflow-prepare','click');fire('workflow-prepare','click');await tick();
 assert.equal(pending.filter(r=>r.url.includes('/selection')).length,0);
 assert.equal(posts.length,0);
 // A selection switch still wins over a delayed record lookup.
 element('workflow-record').value=detail.id;loading=fire('workflow-record','change');let old=take('/global?id=');
 element('workflow-mode').value='CONSULTATIVE_SANDBOX';fire('workflow-mode','change');old.reply(detail);await loading;
 assert.equal(element('workflow-preflight').disabled,true);assert.equal(element('workflow-mode').value,'CONSULTATIVE_SANDBOX');
 // Offline recovery of an existing record remains available and is the only POST.
 element('workflow-record').value=detail.id;loading=fire('workflow-record','change');take('/global?id=').reply(detail);await loading;
 assert.equal(element('workflow-replay').disabled,false);fire('workflow-replay','click');await tick();
 assert.equal(posts.length,1);assert.ok(posts[0].url.endsWith('/api/platform/global-replay'));
 done=true;console.log('closed V1 triggers, selection race and offline recovery check: PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
"""
    result = subprocess.run(
        [
            shutil.which("node") or "node",
            "-e",
            script,
            str(ROOT / "dashboard/global-workflow.js"),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
