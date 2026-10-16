// DP-23: current data in GET-only mode. Financial CRUD has its isolated browser check.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {session,VIEWPORTS} from '../scripts/ui_cdp_v762.mjs';
const [base,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
const catalog=await(await fetch(base+'/api/portfolio/manual')).json();
const wallet=catalog.wallets.find(w=>w.strategy==='MULTIAGENT')||catalog.wallets[0];
assert.ok(wallet);
await session(async page=>{
 const blocked=[];
 page.listeners.push(m=>{if(m.method!=='Fetch.requestPaused')return;const {request,requestId}=m.params;
  const safe=request.method==='GET'&&new URL(request.url).origin===base;if(!safe)blocked.push(request.url);
  page.send(safe?'Fetch.continueRequest':'Fetch.failRequest',safe?{requestId}:{requestId,errorReason:'BlockedByClient'});
 });
 await page.send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
 for(const size of ['desktop','phone']){
  await page.viewport(VIEWPORTS[size]);
  for(const [name,route] of [['wallet','/'],['operations','/operations'],['agents','/radar'],['data','/data'],['comparison','/comparison']]){
   await page.go(base+route+'?wallet='+wallet.id);
   assert.equal(await page.eval(`document.querySelector('#product-wallet').value`),wallet.id);
   assert.equal(await page.eval(`document.documentElement.scrollWidth<=innerWidth+1`),true,size+' '+route);
   assert.equal(await page.eval(`document.querySelectorAll('.hfl-primary a').length`),5);
   assert.equal(await page.eval(`Array.from(document.querySelectorAll('.hfl-primary a')).every(a=>new URL(a.href).searchParams.get('wallet')===${JSON.stringify(wallet.id)})`),true);
   if(name==='agents'){
    assert.equal(await page.eval(`document.body.dataset.agentStage`),'setup');
    assert.equal(await page.eval(`document.querySelector('[data-agent-screen="workflow"]').hidden`),true);
    await page.click('[data-agent-stage="workflow"]');
    assert.equal(await page.eval(`document.querySelector('[data-agent-screen="workflow"]').hidden`),false);
    await page.click('[data-agent-stage="results"]');
    assert.equal(await page.eval(`document.querySelector('#analysis-results').hidden`),false);
    await page.click('[data-agent-stage="setup"]');
   }
   if(name==='operations'){
    await page.eval(`document.querySelector('#product-sell').focus()`);await page.key('Enter');
    assert.equal(await page.eval(`document.querySelector('#trade-form').elements.namedItem('side').value`),'SELL');
    await page.click('#product-buy');
   }
   await page.eval('window.scrollTo(0,0)');await page.shot(out+'/'+size+'-'+name+'.png',size==='desktop');
  }
  await page.go(base+'/legacy/paper?wallet=h2%3Aai');
  assert.equal(await page.eval(`document.querySelector('#product-wallet').disabled`),true);
  assert.equal(await page.eval(`new URLSearchParams(location.search).get('wallet')`),'h2:ai');
 }
 assert.deepEqual(blocked,[]);assert.deepEqual(page.console,[]);
 console.log('PASS: five areas, shared wallet links, visible analysis stages, buy/sell keyboard, independent Legacy context; desktop/phone; GET-only');
});
