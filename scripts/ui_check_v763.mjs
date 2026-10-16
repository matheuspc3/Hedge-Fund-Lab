// Real Chrome interactions, backed by recorded API data. Fetch interception blocks
// ALL writes and external requests before transport; only explicit local fixtures succeed.
// node scripts/ui_check_v763.mjs <base> <report.json> [<screenshots>]
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {session, VIEWPORTS} from './ui_cdp_v762.mjs';

const [base, out, shots] = process.argv.slice(2);
const RUN='radar-2026-10-09-recovery-01';
const results=[], blocked=[], mocked=[], exceptions=[], transfers=[];
let fixture=null;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const report=()=>fs.writeFileSync(out,JSON.stringify({passed:results.filter(r=>r.ok).length,failed:results.filter(r=>!r.ok).length,results,blocked,mocked,exceptions},null,2)+'\n');
fs.mkdirSync(path.dirname(out),{recursive:true}); if(shots)fs.mkdirSync(shots,{recursive:true});
try {
  await session(async page=>{
    page.listeners.push(msg=>{
      if(['Network.loadingFailed','Network.loadingFinished','Network.responseReceived'].includes(msg.method))transfers.push({event:msg.method,...msg.params});
      if(msg.method!=='Fetch.requestPaused')return;
      const {requestId,request}=msg.params, u=new URL(request.url);
      // ponytail: fulfill the 16 MB legacy export byte-for-byte to avoid local
      // Chrome TCP resets; much larger exports need a dedicated static test server.
      if(request.method==='GET' && u.origin===base && u.pathname==='/data.json') {
        const bytes=fs.readFileSync(new URL('../dashboard/data.json',import.meta.url));
        mocked.push({method:'GET',path:'/data.json',source:'LOCAL_UNALTERED_EXPORT',bytes:bytes.length});
        page.send('Fetch.fulfillRequest',{requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:bytes.toString('base64')});
        return;
      }
      const mock=fixture?.(u,request);
      if(mock) {
        mocked.push({method:request.method,path:u.pathname});
        page.send('Fetch.fulfillRequest',{requestId,responseCode:mock.status||200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify(mock.body)).toString('base64')});
      } else if(request.method!=='GET' || u.origin!==base) {
        blocked.push({method:request.method,url:request.url});page.send('Fetch.failRequest',{requestId,errorReason:'BlockedByClient'});
      } else page.send('Fetch.continueRequest',{requestId});
    });
    const check=async(name,expression)=>{
      const value=await page.eval(expression);results.push({name,ok:!!value});assert.ok(value,name);
    };
    const wait=async expression=>{
      for(let i=0;i<600;i++){if(await page.eval(`Boolean(${expression})`))return;await sleep(50);}
      throw Error('wait_timeout: '+expression+'; '+JSON.stringify(await page.eval(`({url:location.href,error:document.querySelector('#error-message')?.textContent,loaded:typeof STATE==='undefined'?null:!!STATE.data})`))+'; network='+JSON.stringify(transfers.filter(t=>t.response?.url?.includes('/data.json')||t.event==='Network.loadingFailed'||t.encodedDataLength>1000000)));
    };
    const select=async(selector,value)=>{
      // Native select is focused and operated by keyboard; no script changes its value.
      const index=await page.eval(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.focus();return [...e.options].findIndex(o=>o.value===${JSON.stringify(value)})})()`);
      assert.ok(index>=0,selector+':'+value);
      await page.key('Home'); for(let i=0;i<index;i++)await page.key('ArrowDown'); await page.key('Enter');
      await wait(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(value)}`);
    };
    const shot=async(name,full=true)=>{if(shots){if(full)await page.eval('window.scrollTo(0,0)');await page.shot(path.join(shots,name+'.png'),full);}};
    await page.viewport(VIEWPORTS.desktop);
    // Verify the large static export before installing Fetch fixtures; no API URL
    // can be reached in this read-only legacy segment.
    await page.send('Network.setBlockedURLs',{urls:['*/api/*','*googleapis*','*generativelanguage*']});
    await page.send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
    await page.go(base+'/legacy',5000);
    await wait(`window.Chart && Chart.getChart('chart-portfolio-equity')`);
    await check('legacy:charts_still_render',`Chart.getChart('chart-portfolio-equity').data.datasets.length>0`);
    await page.click('button[data-tab=analise]');
    await wait(`Chart.getChart('chart-rsi')`);
    await check('legacy:indicator_charts_preserved',`Chart.getChart('chart-price').data.datasets.length>0 && Chart.getChart('chart-rsi').data.datasets.length>0 && Chart.getChart('chart-macd').data.datasets.length>0`);
    await page.send('Network.setBlockedURLs',{urls:[]});
    await page.go(base+'/');
    await page.click('a[href^="/market"]');
    await wait(`document.querySelectorAll('#market-assets [data-asset]').length===5`);
    await check('market:real_universe_and_history',`document.querySelector('#market-coverage').textContent.includes('2026-10-09') && document.body.textContent.includes('Não há cotações em tempo real')`);
    await shot('market-desktop');
    await select('#market-asset','PETR4');
    await wait(`!document.querySelector('#market-room').hidden`);
    await check('market:asset_detail',`document.querySelector('#market-detail').textContent.includes('PETR4') && location.search.includes('asset=PETR4')`);
    await page.click('#market-detail .market-indicators summary');
    await check('market:indicators_expand_and_units',`document.querySelector('.market-indicators').open && document.querySelector('.market-indicators').textContent.includes('Fechamento / média de 50 sessões')`);
    await shot('petr4-detail');
    await page.click('#market-to-radar');
    await wait(`document.querySelector('#radar-run')?.value===${JSON.stringify(RUN)} && !document.querySelector('#room').hidden`);
    await check('navigation:market_to_radar_preserves_selection',`location.search.includes('asset=PETR4') && location.search.includes(${JSON.stringify(RUN)})`);
    await page.click('#close-room');
    await check('radar:return_focus',`document.activeElement.id==='results-title'`);
    await check('radar:five_rows',`document.querySelectorAll('#results tr').length===5`);
    await shot('radar-desktop');
    await select('#filter-signal','VENDA');
    await check('filters:sell',`document.querySelectorAll('#results tr').length===1 && document.querySelector('#results').textContent.includes('VALE3')`);
    await page.click('#clear-filters');
    await select('#filter-final','COMPRA');
    await check('filters:buy',`document.querySelectorAll('#results tr').length===2 && !document.querySelector('#results').textContent.includes('BBAS3')`);
    await page.click('#clear-filters');
    await select('#filter-final','MANTER');
    await check('filters:hold',`document.querySelectorAll('#results tr').length===2 && document.querySelector('#results').textContent.includes('WEGE3') && document.querySelector('#results').textContent.includes('BBAS3')`);
    await select('#filter-risk','VETADO');
    await check('filters:deterministic_veto',`document.querySelectorAll('#results tr').length===1 && document.querySelector('#results').textContent.includes('COMPRA') && document.querySelector('#results').textContent.includes('MANTER')`);
    await page.click('#results [data-detail]');
    await wait(`!document.querySelector('#room').hidden`);
    await check('bbas3:correct_risk_source',`document.querySelector('#room .market-risk').textContent.includes('nenhum parecer LLM de Risk') && document.querySelector('#room .market-risk').textContent.includes('54,48%') && document.querySelector('#room').textContent.includes('COMPRA: 5')`);
    await shot('bbas3-detail');
    await page.click('#room .market-vote > summary');
    await check('committee:expand_real_evidence',`document.querySelector('#room .market-vote').open && document.querySelector('#room .market-vote').textContent.includes('CLOSE_')`);
    await shot('committee-expanded',false);
    await page.click('#room .market-risk [data-help="veto"]');
    await check('help:open',`!document.querySelector('#ds-help-popover').hidden`);
    await shot('contextual-help',false);
    await page.key('Escape');
    await check('help:escape_and_focus',`document.querySelector('#ds-help-popover').hidden && document.activeElement.dataset.help==='veto'`);
    await page.click('#room .market-evidence > summary');
    await page.send('Browser.grantPermissions',{origin:base,permissions:['clipboardReadWrite','clipboardSanitizedWrite']});
    await page.click('#room .ds-copy');
    await check('copy:execution_id',`navigator.clipboard.readText().then(t=>t===${JSON.stringify(RUN)})`);
    await page.click('#close-room'); await page.click('#clear-filters');
    await select('#filter-signal','VENDA'); await select('#filter-risk','VETADO');
    await check('filters:empty',`document.querySelector('#results .ds-empty').textContent.includes('Nenhuma análise')`);
    await shot('empty-state');
    await page.send('Page.reload'); await wait(`document.querySelector('#results .ds-empty')!==null`);
    await check('reload:run_and_filters',`location.search.includes(${JSON.stringify(RUN)}) && document.querySelector('#filter-signal').value==='VENDA' && document.querySelector('#filter-risk').value==='VETADO'`);
    await page.click('#clear-filters');
    await select('#radar-run','radar-2026-10-09-original');
    await wait(`document.querySelector('#run-card').dataset.state==='INCIDENT_PRESERVED'`);
    await page.click('#radar-audit > summary');
    await check('history:incident_not_valid',`document.querySelector('#run-card').textContent.includes('INCIDENT_') && !document.querySelector('#results').textContent.includes('APROVADO')`);
    await select('#radar-run',RUN);await wait(`document.querySelector('#run-card').dataset.state==='COMPLETED'`);
    await select('#compare-a','PETR4|2026-10-09');await select('#compare-b','VALE3|2026-10-09');await page.click('#compare');
    await check('comparison:two_assets',`document.querySelectorAll('#comparison .comparison-card').length===2`);
    await page.click('#radar-to-global');await wait(`document.querySelector('#workflow-record')!==null`);
    await check('navigation:radar_to_portfolio',`location.search.includes(${JSON.stringify(RUN)}) && location.search.includes('tickers=') && !document.querySelector('#workflow-run')`);

    // The component uses local test values labelled as fixtures. No provider data invented.
    await page.go(base+'/market?run='+RUN);
    await wait(`document.querySelectorAll('#market-assets [data-asset]').length===5`);
    const cost={ready:true,operation:'Fixture local · comitês',treatment:'TEST_ONLY',context:'LOCAL_FIXTURE',run:'fixture-run',source:'LOCAL_TEST_FIXTURE',confirmationToken:'fixture-token',callsMax:6,estimatedUsd:0.02,reservedUsd:0.2,remainingUsd:1};
    const openCost=async data=>{await page.eval(`window.costResult=null;window.HFL.confirmCost(${JSON.stringify(data)}).then(v=>window.costResult=v);true`);};
    await openCost(cost);
    await check('component:missing_data_has_no_market_fallback',`!HFLMarket.detail({ticker:'LOCAL_FIXTURE',session:'2026-10-09',status:'NONE'},'fixture').includes('B3 COTAHIST')`);
    await check('cost:disabled_and_facts',`document.querySelector('#hfl-cost-confirm').disabled && document.querySelector('#hfl-cost-dialog').textContent.includes('USD 0.200000')`);
    await page.click('#hfl-cost-dialog details summary');
    await check('cost:review_details',`document.querySelector('#hfl-cost-dialog details').open`);
    await page.key('Escape');
    await check('cost:escape_cancels',`window.costResult===false && !document.querySelector('#hfl-cost-dialog').open`);
    await openCost(cost);await page.click('#hfl-cost-dialog button[value=cancel]');
    await check('cost:cancel',`window.costResult===false`);
    await openCost(cost);await page.click('#hfl-cost-consent');await page.click('#hfl-cost-confirm');
    await check('cost:explicit_confirmation',`window.costResult===true`);
    await check('cost:reject_missing_or_expired',`Promise.all([window.HFL.confirmCost({...${JSON.stringify(cost)},reservedUsd:null}).then(()=>false,()=>true),window.HFL.confirmCost({...${JSON.stringify(cost)},validUntil:'2000-01-01T00:00:00Z'}).then(()=>false,()=>true)]).then(v=>v.every(Boolean))`);

    // Existing paid button integration: local preflight/run fixtures only. The real
    // server never receives these POSTs, even when the dialog is confirmed.
    const view=await (await fetch(base+'/api/platform/radar-view?run='+RUN)).json();
    view.network_isolation=true; view.mutation_available=true; view.run.usd_reserved=0;
    const preflight={ready:true,identity:view.identity,session:view.run.session,replay:false,max_usd:3.32,usd_estimated:0.1,usd_reserved:0.2,global_budget_used:0,global_budget_cap:5,confirmation_token:'LOCAL_FIXTURE_TOKEN',items:view.run.universe.map(ticker=>({ticker,ready:true,mode:'live',input_sha256:'LOCAL_FIXTURE_INPUT',estimate:{calls_max:6}}))};
    let paidRequests=[];
    fixture=(u,r)=>u.pathname==='/api/platform/radar-view' ? {body:view} : u.pathname==='/api/radar/preflight' ? {body:preflight} : u.pathname==='/api/radar/run' ? (paidRequests.push(JSON.parse(r.postData)),{body:{status:'LOCAL_MOCK_ONLY'}}) : null;
    await page.go(base+'/radar?run='+RUN);await wait(`document.querySelectorAll('#radar-assets [data-asset]').length===5`);
    await page.click('.market-operations > summary');await page.click('#preflight');await wait(`!document.querySelector('#confirmation').hidden`);
    await page.click('#paid');await page.click('#execute');await wait(`document.querySelector('#hfl-cost-dialog')?.open`);
    await page.key('Escape');assert.equal(paidRequests.length,0);
    await check('paid:cancel_keeps_authorization_unsent',`!document.querySelector('#hfl-cost-dialog').open`);
    await page.click('#execute');await page.click('#hfl-cost-consent');await page.click('#hfl-cost-confirm');
    await wait(`document.querySelector('#confirmation').hidden`);
    assert.equal(paidRequests.length,1);
    assert.deepEqual(paidRequests[0],{tickers:view.run.universe,session:view.run.session,max_usd:3.32,replay:false,confirmation_token:'LOCAL_FIXTURE_TOKEN',authorize_paid:true,confirm:true});
    results.push({name:'paid:unchanged_payload_intercepted_before_transport',ok:true});
    await page.click('#preflight');await wait(`!document.querySelector('#confirmation').hidden`);await page.click('#paid');await page.click('#execute');
    await page.eval(`document.querySelector('#budget').dispatchEvent(new Event('change',{bubbles:true}))`);
    await page.click('#hfl-cost-consent');await page.click('#hfl-cost-confirm');
    await wait(`!document.querySelector('#error').hidden`);
    assert.equal(paidRequests.length,1);
    results.push({name:'paid:stale_context_refused_before_transport',ok:true});
    fixture=null;

    for(const [name,v] of Object.entries(VIEWPORTS)) {
      await page.viewport(v);
      for(const route of ['/market','/radar']) {
        await page.go(base+route+'?run='+RUN);
        await wait(`document.querySelectorAll('[data-asset]').length===5`);
        await check('reflow:'+route+':'+name,`document.documentElement.scrollWidth<=innerWidth+1`);
      }
    }
    await page.click('.hfl-menu');
    await check('mobile:menu',`document.querySelector('.hfl-menu').getAttribute('aria-expanded')==='true'`);
    await page.key('Escape');
    await check('mobile:escape_restores_focus',`document.activeElement.classList.contains('hfl-menu') && document.activeElement.getAttribute('aria-expanded')==='false'`);
    await shot('radar-mobile');
    await page.click('#radar-overview [data-help]');
    await check('mobile:popover_bounds',`(()=>{const r=document.querySelector('#ds-help-popover').getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.bottom<=innerHeight})()`);
    await page.key('Escape');
    // Browser page zoom equivalent: halve CSS viewport while retaining the desktop raster.
    await page.viewport({width:720,height:450,mobile:false});
    await page.send('Emulation.setDeviceMetricsOverride',{width:720,height:450,deviceScaleFactor:2,mobile:false});
    await check('zoom:200_percent_reflow',`document.documentElement.scrollWidth<=innerWidth+1`);

    fixture=u=>u.pathname==='/api/platform/radar-view' ? {body:{run:{id:RUN,universe:[],session:'2026-10-09',classification:'OFFICIAL',state:'COMPLETED',source:'LOCAL_TEST_EMPTY'},items:[]}} : null;
    await page.go(base+'/market?run='+RUN);await wait(`document.querySelector('#market-assets .ds-empty')!==null`);
    await check('market:empty_api_fixture',`document.querySelector('#market-assets').textContent.includes('Nenhum ativo')`);
    fixture=u=>u.pathname==='/api/platform/radar-runs' ? {status:503,body:{error:'registry_unavailable'}} : null;
    await page.go(base+'/market');await wait(`!document.querySelector('#market-error').hidden`);
    await check('market:error_fixture_no_fallback',`document.querySelectorAll('[data-asset]').length===0`);
    await page.go(base+'/radar');await wait(`!document.querySelector('#error').hidden`);
    await check('radar:error_fixture_blocks_operations',`document.querySelector('#prepare').disabled && document.querySelector('#preflight').disabled && document.querySelectorAll('[data-asset]').length===0`);
    fixture=null;
    await page.viewport(VIEWPORTS.desktop);
    for(const route of ['/market/','/market.html','/radar/','/radar.html']) {
      await page.go(base+route);await check('route:'+route,`document.querySelectorAll('[aria-label="Navegação principal"]').length===1`);
    }
    exceptions.push(...page.console);
    results.push({name:'network:no_unexpected_writes_or_external_calls',ok:blocked.length===0});
    results.push({name:'browser:no_javascript_exceptions',ok:exceptions.length===0});
    assert.equal(blocked.length,0);assert.equal(exceptions.length,0);
  });
} catch(e) {results.push({name:'runner',ok:false,error:e.stack});process.exitCode=1;}
finally {report();console.log(JSON.stringify({passed:results.filter(r=>r.ok).length,failed:results.filter(r=>!r.ok).length,blocked}));}
