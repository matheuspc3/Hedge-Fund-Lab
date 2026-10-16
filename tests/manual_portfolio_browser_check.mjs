// Real UI -> HTTP -> isolated SQLite -> home, no mocked financial responses.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {session,VIEWPORTS} from '../scripts/ui_cdp_v762.mjs';

const [base,out]=process.argv.slice(2);
fs.mkdirSync(out,{recursive:true});
await session(async page=>{
  const blocked=[];
  page.listeners.push(msg=>{
    if(msg.method!=='Fetch.requestPaused')return;
    const {request,requestId}=msg.params,u=new URL(request.url);
    const safe=u.origin===base&&(request.method==='GET'||
      (!process.argv.includes('--current')&&request.method==='POST'&&['/api/portfolio/manual/preview','/api/portfolio/manual/confirm'].includes(u.pathname)));
    if(!safe)blocked.push(request);
    page.send(safe?'Fetch.continueRequest':'Fetch.failRequest',safe?{requestId}:{requestId,errorReason:'BlockedByClient'});
  });
  await page.send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
  const wait=async expression=>{
    for(let i=0;i<100;i++){
      if(await page.eval(expression))return;
      await new Promise(r=>setTimeout(r,100));
    }
    throw Error('Timeout: '+expression+' '+await page.eval('document.querySelector("#personal-error").textContent'));
  };
  const ready=()=>wait('document.querySelector("#personal-portfolios").getAttribute("aria-busy")==="false"');
  if(process.argv.includes('--current')){
    const d=await (await fetch(base+'/api/portfolio/manual')).json();
    const group=d.wallets.filter(w=>w.comparison_group==='manual-initial-20261014');
    assert.equal(group.length,2);
    const expected={PETR4:'351',VALE3:'297',ITUB4:'402',WEGE3:'393',BBAS3:'824'};
    for(const name of ['desktop','phone']){
      await page.viewport(VIEWPORTS[name]);
      for(const w of group){
        assert.equal(w.nature,'SIMULATION');assert.equal(w.cash,'177.44');assert.equal(w.trades.length,5);
        assert.deepEqual(Object.fromEntries(w.positions.map(p=>[p.ticker,p.quantity])),expected);
        await page.go(base+'/?wallet='+w.id);await ready();
        assert.equal(await page.eval('document.querySelector("#personal-name").textContent'),w.name);
        assert.match(await page.eval('document.querySelector("#personal-nature").textContent'),/13\/10\/2026/);
        assert.match(await page.eval('document.querySelector("#personal-nature").textContent'),/custos de entrada zero/);
        assert.match(await page.eval('document.querySelector("#personal-metrics").textContent'),/177,44/);
        assert.equal(await page.eval('document.querySelectorAll("#personal-positions tbody tr").length'),5);
        assert.match(await page.eval('document.querySelector("#personal-pilot").textContent'),/Base inicial comum cadastrada/);
        assert.equal(await page.eval('document.querySelector("#personal-error").hidden'),true);
        assert.equal(await page.eval('document.documentElement.scrollWidth<=innerWidth+1'),true);
        await page.eval('scrollTo(0,0)');await page.shot(path.join(out,'initial-'+w.strategy+'-'+name+'.png'),true);
      }
    }
    await page.go(base+'/?wallet=manual-5f60dc15a6384f97bf1197d85fc16096');await ready();
    assert.equal(await page.eval('document.querySelectorAll("#personal-wallet option").length'),2);
    assert.match(await page.eval('document.querySelector("#personal-status").textContent'),/Carteira anterior indisponível/);
    assert.equal(await page.eval('document.querySelector("#personal-error").hidden'),true);
    assert.deepEqual(blocked,[]);assert.deepEqual(page.console,[]);
    assert.equal(page.requests.some(r=>r.method!=='GET'),false);
    console.log('PASS: current Buy & Hold/Multiagentes, same five positions, reference/costs/cash, archived link recovery, desktop/phone; GET only');return;
  }
  if(process.argv.includes('--resume')){
    const d=await (await fetch(base+'/api/portfolio/manual')).json();
    assert.equal(d.wallets.length,2);
    for(const w of d.wallets){
      assert.equal(w.cash,'821.00');assert.equal(w.trades.length,3);assert.equal(w.audit.length,4);
      await page.go(base+'/?wallet='+w.id);await ready();
      assert.equal(await page.eval('document.querySelector("#personal-name").textContent'),w.name);
      assert.match(await page.eval('document.querySelector("#personal-metrics").textContent'),/821,00/);
    }
    assert.deepEqual(blocked,[]);assert.deepEqual(page.console,[]);
    console.log('PASS: restarted server, same catalog, balances, history and home in a fresh browser');return;
  }
  const fill=async(form,values)=>{
    await page.eval(`(()=>{const f=document.querySelector(${JSON.stringify(form)});for(const [k,v] of Object.entries(${JSON.stringify(values)})){const e=f.elements.namedItem(k);e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));}})()`);
  };
  const register=async values=>{
    await fill('#trade-form',values);
    await page.click('#trade-form button[type=submit]'); await ready();
    assert.equal(await page.eval('document.querySelector("#personal-preview").hidden'),false);
    assert.equal(await page.eval('document.activeElement.id'),'personal-confirm');
    await page.key('Enter'); await ready();
    assert.equal(await page.eval('document.querySelector("#personal-preview").hidden'),true);
    assert.equal(await page.eval('document.querySelector("#personal-error").hidden'),true);
  };
  const ids=[];
  for(const name of ['desktop','phone']){
    await page.viewport(VIEWPORTS[name]); await page.go(base+'/wallets/new'); await ready();
    if(name==='desktop'){
      assert.equal(await page.eval('!document.querySelector("#personal-create").hidden'),true);
      assert.equal(await page.eval('document.querySelector("#personal-detail").hidden'),true);
      await page.shot(path.join(out,'empty-desktop.png'));
    }
    await fill('#wallet-form',{name:'Carteira '+name,nature:name==='desktop'?'EXTERNAL':'SIMULATION',capital:'1000',start_date:'2020-01-01'});
    await page.click('#wallet-form button[type=submit]'); await wait('location.pathname==="/operations"'); await ready();
    assert.equal(await page.eval('document.querySelector("#personal-name").textContent'),'Carteira '+name);
    ids.push(await page.eval('document.querySelector("#personal-wallet").value'));
    await register({ticker:'PETR4',side:'BUY',quantity:'10',price:'20',costs:'2',economic_date:'2020-01-02'});
    assert.match(await page.eval('document.querySelector("#personal-metrics").textContent'),/798,00/);
    assert.match(await page.eval('document.querySelector("#personal-positions").textContent'),/20,2/);
    await register({side:'SELL',quantity:'4',price:'30',costs:'1',economic_date:'2020-01-04'});
    assert.match(await page.eval('document.querySelector("#personal-metrics").textContent'),/917,00/);
    await register({side:'BUY',quantity:'10',price:'10',costs:'0',economic_date:'2020-01-01'});
    assert.match(await page.eval('document.querySelector("#personal-metrics").textContent'),/817,00/);
    await page.click('#personal-trades [data-correct]');
    await fill('#trade-form',{quantity:'4',price:'31',costs:'1',reason:'Corrigir preço da venda'});
    await page.click('#trade-form button[type=submit]'); await ready();
    await page.click('#personal-confirm'); await ready();
    assert.match(await page.eval('document.querySelector("#personal-metrics").textContent'),/821,00/);
    await fill('#trade-form',{side:'SELL',quantity:'999'});
    await page.click('#trade-form button[type=submit]'); await ready();
    assert.equal(await page.eval('document.querySelector("#trade-form [name=quantity]").getAttribute("aria-invalid")'),'true');
    assert.equal(await page.eval('document.activeElement.name'),'quantity');
    assert.equal(await page.eval('document.querySelector("#personal-preview").hidden'),true);
    await page.shot(path.join(out,'error-'+name+'.png'));
    await page.click('#personal-refresh'); await ready();
    assert.equal(await page.eval('document.documentElement.scrollWidth<=innerWidth+1'),true,name+' overflow');
    await page.eval('scrollTo(0,0)'); await page.shot(path.join(out,'portfolio-'+name+'.png'),true);
    const url=await page.eval('location.href'); await page.go(url); await ready();
    assert.match(await page.eval('document.querySelector("#personal-metrics").textContent'),/821,00/);
    assert.match(await page.eval('document.querySelector("#personal-prices").textContent'),/Preços de referência ausentes/);
    assert.equal(await page.eval('document.querySelector("#home-portfolio").hidden'),true);
    assert.equal(await page.eval('document.querySelectorAll("#personal-portfolios canvas").length'),0);
    // Original and corrected entry remain available in the audit table.
    assert.match(await page.eval('document.querySelector("#personal-audit").textContent'),/Corrigido/);
    assert.match(await page.eval('document.querySelector("#personal-audit").textContent'),/30,00/);
    assert.match(await page.eval('document.querySelector("#personal-audit").textContent'),/31,00/);
  }
  await page.go(base+'/?wallet='+ids[0]);await ready();
  assert.equal(await page.eval('document.querySelectorAll("#personal-wallet option").length'),2);
  await page.go(base+'/?demo=1');
  assert.equal(await page.eval('document.querySelector("#personal-portfolios").hidden'),true);
  assert.equal(await page.eval('document.querySelector("#pilot-demo").hidden'),false);
  await page.go(base+'/portfolio');
  assert.match(await page.eval('document.querySelector("h1").textContent'),/Propostas e demonstrações/);
  await page.go(base+'/legacy');
  assert.match(await page.eval('document.body.innerText'),/somente consulta/i);
  await page.go(base+'/#audit');await page.go(base+'/#wallets');
  await wait('location.pathname==="/legacy/paper"');
  assert.equal(await page.eval('location.hash'),'#carteiras');
  assert.deepEqual(blocked,[]);assert.deepEqual(page.console,[]);
  console.log('PASS: real creation/buy/partial sell/history/correction/error/reload/selection, desktop+phone+keyboard, no external traffic or other writes');
});
