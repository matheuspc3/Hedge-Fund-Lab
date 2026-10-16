// Browser-only authorization fixtures: no authorization or inference reaches the server.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {session,VIEWPORTS} from '../scripts/ui_cdp_v762.mjs';
const [base,out]=process.argv.slice(2),id='radar-2026-10-14-asof-13';
fs.mkdirSync(out,{recursive:true});
const view=await (await fetch(base+'/api/platform/radar-view?run='+id)).json();
const money=await (await fetch(base+'/api/platform/radar-budget?run='+id)).json();
// The historical source may now be completed or owned by a different server.
// A pending, writable batch exists only in these browser fixtures.
Object.assign(view,{mutation_available:true,runner:id,job:null});
Object.assign(money,{run_reserved_usd:0,other_runs_reserved_usd:6.63552,aggregate_exposure_usd:9.95328,aggregate_cap_usd:5,
  planned:{tickers:view.run.universe,calls_max:30,calls_planned:29,usd_reserved:3.31776}});
const preflight={ready:true,replay:false,session:view.run.session,identity:view.run.treatment.identity,confirmation_token:'BROWSER_FIXTURE_NOT_REAL',
  items:view.run.universe.map(ticker=>({ticker,ready:true,mode:'live',input_sha256:'fixture',estimate:{calls_max:6}})),
  usd_estimated:.14625,usd_reserved:3.31776,max_usd:3.5,global_budget_used:0,global_budget_cap:5};
await session(async page=>{
  let authorized=false,authorizations=0;
  const blocked=[];
  page.listeners.push(msg=>{
    if(msg.method!=='Fetch.requestPaused')return;
    const {request,requestId}=msg.params,u=new URL(request.url);let fixture;
    const budget={...money,authorization:{required:true,state:authorized?'VALID':'ABSENT'}};
    if(u.pathname==='/api/platform/radar-view')fixture={...view,run:{...view.run,budget}};
    if(u.pathname==='/api/platform/radar-budget')fixture=budget;
    if(u.pathname==='/api/radar/preflight')fixture=preflight;
    if(u.pathname==='/api/platform/radar-budget-authorization'){
      const body=JSON.parse(request.postData);assert.equal(body.max_aggregate_usd,10);assert.equal(body.confirm,true);assert.equal(body.budget_token,money.budget_token);
      authorized=true;authorizations++;fixture={provider_calls:0};
    }
    if(fixture){page.send('Fetch.fulfillRequest',{requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify(fixture)).toString('base64')});return;}
    const safe=request.method==='GET'&&u.origin===base;
    if(!safe)blocked.push(request);
    page.send(safe?'Fetch.continueRequest':'Fetch.failRequest',safe?{requestId}:{requestId,errorReason:'BlockedByClient'});
  });
  await page.send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
  const wait=async expr=>{for(let n=0;n<80;n++){if(await page.eval(expr))return;await new Promise(r=>setTimeout(r,100));}throw Error('timeout '+expr);};
  for(const name of ['desktop','phone']){
    authorized=false;await page.viewport(VIEWPORTS[name]);await page.go(base+'/radar?run='+id+'#analysis-workflow',2500);
    await page.eval(`document.querySelector('.technical-options').open=true;document.querySelector('#analysis-workflow').scrollIntoView()`);await wait('!document.querySelector("#preflight").disabled');
    await page.click('#preflight');await wait('!document.querySelector("#budget-review").hidden');
    assert.equal(await page.eval('document.querySelector("#budget-consent").checked'),false);
    await page.eval(`document.querySelector('#aggregate-budget').value='5';document.querySelector('#aggregate-budget').dispatchEvent(new Event('input',{bubbles:true}));`);
    await page.click('#budget-consent');assert.equal(await page.eval('document.querySelector("#budget-authorize").disabled'),true);
    await page.eval(`document.querySelector('#aggregate-budget').value='10';document.querySelector('#aggregate-budget').dispatchEvent(new Event('input',{bubbles:true}));`);
    assert.equal(await page.eval('document.querySelector("#budget-authorize").disabled'),false);
    await page.eval('document.querySelector("#budget-review").scrollIntoView({block:"center"})');
    await page.shot(path.join(out,'budget-review-fixture-'+name+'.png'));
    await page.click('#budget-authorize');await wait('document.querySelector("#budget-review").hidden&&document.querySelector("#preflight-result").textContent.includes("Preflight Radar aprovado")');
    assert.equal(await page.eval('document.querySelector("#paid").checked'),false);
    assert.equal(await page.eval('document.querySelector("#execute").disabled'),true);
    await page.click('#paid');assert.equal(await page.eval('document.querySelector("#execute").disabled'),false);
    assert.equal(await page.eval('document.documentElement.scrollWidth<=innerWidth+1'),true);
  }
  assert.equal(authorizations,2);assert.deepEqual(blocked,[]);assert.deepEqual(page.console,[]);
  console.log('PASS: editable ceiling, insufficient limit, explicit consent, fixture authorization, fresh preflight and step 3 enabled only after paid checkbox; desktop/phone; zero live writes');
});
