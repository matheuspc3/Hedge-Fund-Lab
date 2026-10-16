// Real headless Chrome, existing CDP client. Transport allows local GETs only.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {session, VIEWPORTS} from './ui_cdp_v762.mjs';
const [base,out,shots]=process.argv.slice(2),results=[],blocked=[],exceptions=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
fs.mkdirSync(path.dirname(out),{recursive:true});if(shots)fs.mkdirSync(shots,{recursive:true});
let mock=null;
try{
  await session(async page=>{
    page.listeners.push(msg=>{
      if(msg.method!=='Fetch.requestPaused')return;
      const {request,requestId}=msg.params,u=new URL(request.url),fixture=mock?.(u);
      if(fixture)page.send('Fetch.fulfillRequest',{requestId,responseCode:fixture.status||200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify(fixture.body)).toString('base64')});
      else if(request.method!=='GET'||u.origin!==base){blocked.push(request);page.send('Fetch.failRequest',{requestId,errorReason:'BlockedByClient'});}
      else page.send('Fetch.continueRequest',{requestId});
    });
    await page.send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
    const check=async(name,expr)=>{const ok=!!await page.eval(expr);results.push({name,ok});assert.ok(ok,name);};
    const wait=async expr=>{for(let n=0;n<250;n++){if(await page.eval(`(()=>{try{return Boolean(${expr})}catch{return false}})()`))return;await sleep(100);}throw Error('wait_timeout: '+expr);};
    const ready=()=>wait(`!document.querySelector('#monitor-content').hidden&&document.querySelector('#monitoring').getAttribute('aria-busy')==='false'`);
    const shot=async name=>{if(shots){await page.eval('window.scrollTo(0,0)');await page.shot(path.join(shots,name+'.png'),true);}};
    const selectSession=async value=>{
      const index=await page.eval(`(()=>{const e=document.querySelector('#monitor-session');e.focus();return [...e.options].findIndex(o=>o.value===${JSON.stringify(value)})})()`);
      assert.ok(index>=0);await page.key('Home');for(let i=0;i<index;i++)await page.key('ArrowDown');await page.key('Enter');await ready();
    };
    await page.viewport(VIEWPORTS.desktop);await page.go(base+'/portfolio#visao-geral',3000);await ready();
    await check('official:cash_compact_no_doughnut',`document.querySelector('#monitor-composition').hidden&&!Chart.getChart('monitor-composition')&&document.querySelector('#monitor-summary').textContent.includes('100.000,00')`);
    await check('official:no_positions_and_no_performance_curve',`document.querySelectorAll('#monitor-positions tbody tr').length===0&&document.querySelector('#monitor-curve').hidden`);
    await check('identity:multiasset_selector_excludes_h2',`[...document.querySelectorAll('#monitor-wallet option')].every(o=>!o.value.startsWith('h2:'))&&!document.querySelector('#monitor-demo').checked`);
    await check('identity:explicit_cross_line_link',`document.querySelector('a[href^="/paper?wallet="]').textContent.includes('linha experimental H2')`);
    await shot('official-all-cash');
    await page.eval(`document.querySelector('#monitor-demo').focus()`);await page.key(' ');await ready();
    await wait(`document.querySelector('#monitor-identity').textContent.includes('SYNTHETIC_TEST')`);
    await check('demo:explicit_selection_keyboard_and_identity',`document.querySelector('#monitor-demo').checked&&location.search.includes('demo=1')&&document.querySelector('#monitor-identity').textContent.includes('HFL-MULTIASSET-PAPER-LEDGER-V1')`);
    await check('demo:qualified_summary',`document.querySelector('#monitor-summary').textContent.includes('100.168,28')&&document.querySelector('#monitor-summary').textContent.includes('91.708,28')`);
    await check('demo:last_mark_and_reconciliation',`document.querySelector('#monitor-status').textContent.includes('2026-04-24')&&document.querySelector('#monitor-status').textContent.includes('RECONCILED')`);
    await check('demo:origin_and_official_execution_disabled',`document.querySelector('#monitor-identity').textContent.includes('SQLite temporário')&&document.querySelector('#monitor-identity').textContent.includes('Execução oficial desabilitada')`);
    await shot('synthetic-overview');
    await page.click('a[href="#posicoes"]');
    await check('demo:two_positions_and_five_sessions',`document.querySelectorAll('#monitor-positions tbody tr').length===2&&Chart.getChart('monitor-curve').data.labels.length===5`);
    await check('demo:prices_are_observed_points',`Chart.getChart('monitor-curve').data.datasets[0].showLine===false&&document.querySelector('#monitor-curve-table').textContent.includes('2026-04-17')`);
    await shot('synthetic-positions-history');
    await page.click('a[href="#evidencias"]');
    await check('demo:three_trades_and_settlements',`document.querySelectorAll('#monitor-trades tbody tr').length===3&&document.querySelector('#monitor-trades').textContent.includes('2026-04-22')&&document.querySelector('#monitor-trades').textContent.includes('2026-04-24')`);
    await check('demo:timeline_first_page',`document.querySelectorAll('#monitor-timeline tbody tr').length===10&&document.querySelector('#monitor-page-label').textContent.includes('1–10 de 27')&&document.querySelector('#monitor-prev').disabled`);
    await page.click('#monitor-next');await wait(`document.querySelector('#monitor-page-label').textContent.includes('11–20 de 27')`);
    await check('demo:timeline_second_page',`document.querySelector('#monitor-timeline').textContent.includes('SETTLEMENT_RECORDED')&&!document.querySelector('#monitor-prev').disabled`);
    await shot('synthetic-operations-timeline');
    await page.click('#monitor-prev');await wait(`document.querySelector('#monitor-page-label').textContent.includes('1–10 de 27')`);
    await page.click('a[href="#posicoes"]');await selectSession('2026-04-17');
    await wait(`location.search.includes('session=2026-04-17')`);
    await check('session:historical_holdings_and_pending_settlement',`document.querySelector('#monitor-positions tbody tr').textContent.includes('100')&&document.querySelector('#monitor-future').textContent.includes('2026-04-22')&&document.querySelector('#monitor-curve').hidden`);
    await check('session:single_point_not_performance',`document.querySelector('#monitor-curve-note').textContent.includes('Histórico insuficiente')`);
    await page.send('Page.reload');await ready();
    await check('session:reload_preserves_date_and_equity',`document.querySelector('#monitor-session').value==='2026-04-17'&&document.querySelector('#monitor-summary').textContent.includes('99.990,00')`);
    await selectSession('2026-04-22');await ready();
    await check('session:receivable_and_reduced_position',`document.querySelector('#monitor-secondary').textContent.includes('1.718,28')&&document.querySelector('#monitor-positions tbody tr').textContent.includes('60')`);
    await shot('synthetic-session-receivable');
    await selectSession('');await ready();
    await page.click('a[href="#visao-geral"]');
    await page.click('#monitor-summary [data-help="patrimonio"]');
    await check('help:contextual_open',`!document.querySelector('#ds-help-popover').hidden`);await page.key('Escape');
    await check('help:escape_returns_focus',`document.querySelector('#ds-help-popover').hidden&&document.activeElement.dataset.help==='patrimonio'`);
    await page.click('a[href="#global-workflow"]');
    await check('decisions:v1_rejected_v2_valid_preserved',`document.querySelector('#decision-list').textContent.includes('REJECTED_BY_VALIDATOR')&&document.querySelector('#decision-list').textContent.includes('VALID_PROPOSAL')`);
    await page.go(base+'/portfolio?wallet=h2%3Aai#posicoes',2200);await ready();
    await check('deep_link:h2_migrates_identity_to_paper',`location.pathname==='/paper'&&new URLSearchParams(location.search).get('wallet')==='h2:ai'&&document.querySelectorAll('#monitor-wallet option').length===5`);
    await shot('h2-separate-line');
    for(const [name,v] of Object.entries(VIEWPORTS)){
      await page.viewport(v);await page.go(base+'/portfolio?demo=1&wallet=synthetic-v765#posicoes',2500);await ready();
      await check('layout:'+name,`document.documentElement.scrollWidth<=innerWidth+1&&document.querySelector('#monitor-wallet').getBoundingClientRect().width<=innerWidth`);
      if(name==='phone')await shot('synthetic-mobile');
    }
    await page.viewport({width:720,height:450,mobile:false});
    await check('layout:200_percent_equivalent_reflow',`document.documentElement.scrollWidth<=innerWidth+1`);
    await shot('synthetic-reflow-200');await page.viewport(VIEWPORTS.desktop);
    mock=u=>u.pathname==='/api/portfolio/ledger'&&u.searchParams.has('wallet')?{status:400,body:{error:'synthetic_read_error_fixture'}}:null;
    await page.click('#monitor-refresh');await wait(`!document.querySelector('#monitor-error').hidden`);
    await check('error:stale_state_hidden',`document.querySelector('#monitor-content').hidden&&document.querySelector('#monitor-error').getAttribute('role')==='alert'`);await shot('ledger-read-error');
    mock=null;await page.click('#monitor-refresh');await ready();
    await check('error:read_retry_recovers',`document.querySelector('#monitor-error').hidden`);
    mock=u=>u.pathname==='/api/portfolio/ledger'&&!u.searchParams.has('wallet')?{body:{wallets:[],read_only:true}}:null;
    await page.go(base+'/portfolio?demo=1#visao-geral',2000);
    await wait(`document.querySelector('#monitor-identity').textContent.includes('Nenhuma carteira disponível')`);
    await check('empty:no_fixture_promoted_to_official',`document.querySelector('#monitor-content').hidden`);await shot('ledger-empty');mock=null;
    await check('transport:no_writes_or_external_calls',`${blocked.length}===0`);
    exceptions.push(...page.console);assert.deepEqual(page.console,[]);
  });
}catch(e){exceptions.push(e.stack);process.exitCode=1;}
finally{fs.writeFileSync(out,JSON.stringify({passed:results.filter(r=>r.ok).length,failed:results.filter(r=>!r.ok).length,results,blocked,exceptions},null,2)+'\n');console.log(JSON.stringify({passed:results.filter(r=>r.ok).length,failed:results.filter(r=>!r.ok).length,exceptions}));}
