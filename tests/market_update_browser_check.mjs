// Real Chrome against a local dashboard; preparation is fulfilled by fixtures.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {session, VIEWPORTS} from '../scripts/ui_cdp_v762.mjs';
const [base,out]=process.argv.slice(2);
fs.mkdirSync(out,{recursive:true});
await session(async page=>{
  let mock=false,submitted=false,posts=0;
  const blocked=[];
  const run={id:'radar-ui-fixture',session:'2026-10-13',universe:['PETR4','VALE3','ITUB4','WEGE3','BBAS3'],mode:'CONSULTATIVE_SANDBOX'};
  page.listeners.push(msg=>{
    if(msg.method!=='Fetch.requestPaused')return;
    const {request,requestId}=msg.params,u=new URL(request.url);
    let value;
    if(mock&&u.pathname==='/api/platform/radar-runs')value={runner:run.id};
    if(mock&&u.pathname==='/api/platform/radar-view')value={run,mutation_available:true,csrf_token:'fixture',last_closed_session:run.session,job:submitted?{id:'fixture-job',command:'prepare',status:'COMPLETED',items:run.universe.map(ticker=>({ticker,status:'PREPARED'}))}:null};
    if(mock&&u.pathname==='/api/radar/prepare'){
      assert.equal(request.method,'POST');
      assert.deepEqual(JSON.parse(request.postData),{tickers:run.universe,session:run.session,mode:'live'});
      submitted=true;posts++;value={id:'fixture-job',command:'prepare',status:'RUNNING'};
    }
    if(value){page.send('Fetch.fulfillRequest',{requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify(value)).toString('base64')});return;}
    const safe=request.method==='GET'&&u.origin===base;
    if(!safe)blocked.push(request);
    page.send(safe?'Fetch.continueRequest':'Fetch.failRequest',safe?{requestId}:{requestId,errorReason:'BlockedByClient'});
  });
  await page.send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
  for(const size of ['desktop','phone']){
    await page.viewport(VIEWPORTS[size]);
    mock=false;submitted=false;
    await page.go(base+'/');
    assert.equal(await page.eval(`document.querySelector('#hfl-market-dialog').open`),false);
    mock=true;
    await page.eval(`document.querySelector('#hfl-market-open').focus()`);await page.key('Enter');
    for(let n=0;n<30;n++){if(await page.eval(`!document.querySelector('#hfl-market-start').disabled`))break;await new Promise(r=>setTimeout(r,100));}
    assert.match(await page.eval(`document.querySelector('#hfl-market-scope').textContent`),/13\/10\/2026.*PETR4/);
    await page.click('#hfl-market-start');
    for(let n=0;n<30;n++){if(await page.eval(`!document.querySelector('#hfl-market-reload').hidden`))break;await new Promise(r=>setTimeout(r,100));}
    assert.match(await page.eval(`document.querySelector('#hfl-market-status').textContent`),/5 ativos/);
    assert.equal(await page.eval(`document.documentElement.scrollWidth<=innerWidth+1`),true);
    await page.shot(path.join(out,'market-update-'+size+'.png'),false);
    await page.key('Escape');
    assert.equal(await page.eval(`document.querySelector('#hfl-market-dialog').open`),false);
    assert.equal(await page.eval(`document.activeElement.id`),'hfl-market-open');
  }
  mock=false;
  for(const route of ['/market','/radar','/portfolio','/legacy','/legacy/paper']){
    await page.go(base+route);
    assert.equal(await page.eval(`document.querySelectorAll('#hfl-market-open').length`),1,route);
    assert.equal(await page.eval(`document.documentElement.scrollWidth<=innerWidth+1`),true,route);
  }
  assert.equal(posts,2);assert.deepEqual(blocked,[]);assert.deepEqual(page.console,[]);
  console.log('PASS: global button across modules; fixture-only prepare; desktop/phone modal, keyboard, focus, no live POST or external traffic');
});
