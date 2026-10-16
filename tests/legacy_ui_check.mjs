// Run against scripts/serve_dashboard_keyless.py; reuse the existing Chrome client.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {session, VIEWPORTS} from '../scripts/ui_cdp_v762.mjs';

const [base, out] = process.argv.slice(2);
fs.mkdirSync(out, {recursive:true});
await session(async page => {
  const blocked=[];
  page.listeners.push(msg => {
    if(msg.method!=='Fetch.requestPaused')return;
    const {request,requestId}=msg.params;
    const safe=request.method==='GET' && new URL(request.url).origin===base;
    if(!safe)blocked.push(request);
    page.send(safe?'Fetch.continueRequest':'Fetch.failRequest',safe?{requestId}:{requestId,errorReason:'BlockedByClient'});
  });
  await page.send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
  for(const name of ['desktop','phone']) {
    await page.viewport(VIEWPORTS[name]);
    for(const route of ['/', '/#audit', '/legacy', '/legacy/paper?wallet=h2%3Aai#acompanhamento', '/legacy/h2#provisional/audit', '/legacy/backtests']) {
      const before=page.requests.length;
      await page.go(base+route,2500);
      assert.equal(await page.eval('document.documentElement.scrollWidth<=innerWidth+1'),true,route+' overflow');
      assert.equal(await page.eval(`document.querySelectorAll('.hfl-primary a').length`),4);
      assert.equal(await page.eval(`!!document.querySelector('.hfl-archive a[href="/legacy"]')`),true);
      if(route.startsWith('/legacy')) {
        assert.equal(await page.eval(`document.querySelector('.hfl-archive a').getAttribute('aria-current')`),'true');
        assert.equal(await page.eval(`document.body.innerText.includes('documentação do TCC')`),true);
      } else {
        assert.equal(page.requests.slice(before).some(r=>/\/api\/(forward|h2)\//.test(r.url)),false,'home depends on H2');
        assert.equal(await page.eval(`!!document.querySelector('#attention-next,#platform-wallets')`),false);
      }
      if(route.includes('/paper')) {
        assert.equal(await page.eval(`document.querySelectorAll('#monitor-wallet option').length`),5);
        assert.equal(await page.eval(`document.querySelectorAll('#prepare,#execute,#sup-form,[data-action="approve"],[data-action="cancel"]').length`),0);
        assert.equal(await page.eval(`document.querySelector('#monitor-content').hidden`),false);
      }
      if(route==='/' || route==='/legacy')await page.shot(path.join(out,(route==='/'?'home':'legacy')+'-'+name+'.png'),true);
    }
    await page.go(base+'/legacy');
    if(name==='phone') {
      await page.eval(`document.querySelector('.hfl-menu').focus()`);
      await page.key('Enter');
      assert.equal(await page.eval(`document.querySelector('.hfl-menu').getAttribute('aria-expanded')`),'true');
      await page.key('Escape');
      assert.equal(await page.eval(`document.activeElement.className`),'hfl-menu');
    }
  }
  for(const route of ['/paper?wallet=h2%3Aai#supervisao','/h2?source=demo#provisional/audit','/index.html?old=1#portfolio']) {
    await page.go(base+route);
    assert.equal(await page.eval('location.pathname+location.search+location.hash'),route);
  }
  await page.go(base+'/?keep=1#wallets');
  assert.equal(await page.eval('location.pathname'),'/legacy/paper');
  assert.equal(await page.eval('new URLSearchParams(location.search).get("keep")'),'1');
  assert.equal(await page.eval('location.hash'),'#carteiras');
  assert.deepEqual(blocked,[]);
  assert.deepEqual(page.console,[]);
  console.log('PASS: Legacy routes, aliases/query/fragments, read-only controls, home without H2, desktop/phone and keyboard menu');
});
