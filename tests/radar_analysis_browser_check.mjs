// Real Chrome UI; fixture-only writes, no market collection or paid inference.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {session, VIEWPORTS} from '../scripts/ui_cdp_v762.mjs';
const [base,out]=process.argv.slice(2);
fs.mkdirSync(out,{recursive:true});
const live=await (await fetch(base+'/api/platform/radar-analysis')).json();
const wallets=[
  {id:'fixture-empty',name:'Carteira vazia',nature_label:'Simulada',cash:100000,positions:[],revision:'empty-r1'},
  {id:'fixture-held',name:'Carteira escolhida',nature_label:'Simulada',cash:1000,positions:[{ticker:'PETR4',quantity:10}],revision:'held-r1'}
];
const options={...live,wallets,history:[{run:live.selected,wallet:wallets[1].id,target_date:'2026-10-15',reference_session:'2026-10-14',created_at:'2026-10-15T01:00:00-03:00',classification:'SAME_DAY_ANALYSIS'}]};
await session(async page=>{
  const submitted=[],blocked=[];
  page.listeners.push(msg=>{
    if(msg.method!=='Fetch.requestPaused')return;
    const {request,requestId}=msg.params,u=new URL(request.url);
    let value;
    if(u.origin===base&&u.pathname==='/api/platform/radar-analysis'){
      if(request.method==='POST'){
        const body=JSON.parse(request.postData);submitted.push(body);
        value={run:live.selected};
      }else value=u.search?{context:{wallet:wallets[1],target_date:'2026-10-15',reference_session:'2026-10-14',created_at:'2026-10-15T01:00:00-03:00',classification:'SAME_DAY_ANALYSIS'},wallet_changed:false}:options;
    }
    if(value){page.send('Fetch.fulfillRequest',{requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify(value)).toString('base64')});return;}
    const safe=request.method==='GET'&&u.origin===base;
    if(!safe)blocked.push(request);
    page.send(safe?'Fetch.continueRequest':'Fetch.failRequest',safe?{requestId}:{requestId,errorReason:'BlockedByClient'});
  });
  await page.send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
  await page.go(base+'/');
  assert.match(await page.eval(`document.querySelector('#personal-analysis').getAttribute('href')`),/^\/radar\?wallet=manual-/);
  for(const size of ['desktop','phone']){
    await page.viewport(VIEWPORTS[size]);
    await page.go(base+'/radar?wallet=fixture-held#new-analysis');
    assert.equal(await page.eval(`document.querySelector('#new-analysis').open`),true);
    assert.equal(await page.eval(`document.activeElement.id`),'analysis-target');
    assert.equal(await page.eval(`document.querySelector('#analysis-wallet').value`),'fixture-held');
    assert.equal(await page.eval(`document.querySelector('#analysis-tickers').value`),'PETR4');
    assert.equal(await page.eval(`document.querySelector('#analysis-target').value`),live.target_date);
    assert.equal(await page.eval(`document.querySelector('#analysis-reference').value`),live.reference_session);
    assert.match(await page.eval(`document.querySelector('#analysis-history').textContent`),/15\/10\/2026/);
    assert.equal(await page.eval(`document.querySelector('#radar-to-global').hidden`),true);
    assert.equal(await page.eval(`document.querySelector('#analysis-return').getAttribute('href')`),'/?wallet=fixture-held');
    await page.eval(`document.querySelector('#analysis-wallet').value='fixture-empty';document.querySelector('#analysis-wallet').dispatchEvent(new Event('change'))`);
    assert.equal(await page.eval(`document.querySelector('#analysis-tickers').value`),live.examples.join(', '));
    await page.eval(`document.querySelector('#analysis-wallet').value='fixture-held';document.querySelector('#analysis-wallet').dispatchEvent(new Event('change'));document.querySelector('#analysis-target').value='2026-10-15';document.querySelector('#analysis-target').dispatchEvent(new Event('change'))`);
    assert.equal(await page.eval(`document.documentElement.scrollWidth<=innerWidth+1`),true);
    await page.eval(`document.querySelector('#new-analysis').scrollIntoView({block:'start'})`);
    await page.shot(path.join(out,'radar-analysis-'+size+'.png'),false);
    await page.eval(`document.querySelector('#analysis-create').focus()`);await page.key('Enter');
    for(let n=0;n<30;n++){if(submitted.length===(size==='desktop'?1:2))break;await new Promise(r=>setTimeout(r,100));}
    const body=submitted.at(-1);
    assert.equal(body.wallet,'fixture-held');assert.equal(body.wallet_revision,'held-r1');
    assert.equal(body.target_date,'2026-10-15');assert.equal(body.reference_session,'2026-10-14');
    assert.deepEqual(body.tickers,['PETR4']);assert.equal(body.confirm,true);
    assert.match(body.command_id,/^[a-f0-9]{32}$/);
  }
  assert.equal(submitted.length,2);assert.notEqual(submitted[0].command_id,submitted[1].command_id);
  assert.deepEqual(blocked,[]);assert.deepEqual(page.console,[]);
  console.log('PASS: desktop/phone; wallet, empty wallet, target/reference, history, keyboard, focus, no overflow; fixture-only POSTs, no external traffic');
});
