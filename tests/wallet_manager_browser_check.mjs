// Full browser → HTTP API → isolated SQLite flow; fake provider in the test server.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {session,VIEWPORTS} from '../scripts/ui_cdp_v762.mjs';
const [base,run,wallet,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
await session(async page=>{
 await page.viewport(VIEWPORTS.desktop);
 await page.go(base+'/radar?'+new URLSearchParams({run,wallet})+'#analysis-results');
 assert.equal(await page.eval(`document.querySelector('#wallet-manager').hidden`),false);
 await page.eval(`document.querySelector('#manager-cost').value='0.10';document.querySelector('#manager-cost').dispatchEvent(new Event('input',{bubbles:true}));`);
 await page.click('#manager-prepare');
 for(let i=0;i<100;i++){
  if(await page.eval(`!document.querySelector('#manager-inference').hidden`))break;
  await new Promise(r=>setTimeout(r,100));
 }
 assert.equal(await page.eval(`document.querySelector('#manager-run').disabled`),true);
 assert.equal(await page.eval(`document.querySelector('#manager-estimate').textContent.includes('Uma chamada')`),true);
 await page.click('#manager-paid');await page.click('#manager-run');
 for(let i=0;i<100;i++){
  if(await page.eval(`!document.querySelector('#manager-result').hidden`))break;
  await new Promise(r=>setTimeout(r,100));
 }
 assert.equal(await page.eval(`document.querySelector('#manager-result').hidden`),false);
 assert.equal(await page.eval(`document.querySelector('#manager-plan').textContent.includes('redução parcial')`),true);
 assert.equal(await page.eval(`document.querySelector('#manager-price-note').textContent.includes('Não é cotação ao vivo')`),true);
 assert.equal(await page.eval(`document.querySelector('#manager-plan').textContent.includes('Vender 4 ações')`),true);
 await page.click('#manager-preview');
 for(let i=0;i<100;i++){
  if(await page.eval(`!document.querySelector('#manager-preview-box').hidden`))break;
  await new Promise(r=>setTimeout(r,100));
 }
 assert.equal(await page.eval(`document.querySelector('#manager-apply').disabled`),true);
 await page.eval(`document.querySelector('#manager-financial').focus()`);await page.key(' ');
 assert.equal(await page.eval(`document.querySelector('#manager-apply').disabled`),false);
 await page.click('#manager-apply');
 for(let i=0;i<100;i++){
  if(await page.eval(`document.querySelector('#manager-receipt').textContent.includes('Cesta registrada')`))break;
  await new Promise(r=>setTimeout(r,100));
 }
 assert.equal(await page.eval(`document.querySelector('#manager-receipt').textContent.includes('Cesta registrada')`),true);
 await page.shot(out+'/manager-desktop.png',true);
 await page.viewport(VIEWPORTS.phone);
 await page.go(base+'/radar?'+new URLSearchParams({run,wallet})+'#analysis-results');
 assert.equal(await page.eval(`document.querySelector('#manager-receipt').textContent.includes('Cesta registrada')`),true);
 assert.equal(await page.eval(`document.querySelector('#manager-approval').hidden`),true);
 assert.equal(await page.eval(`document.documentElement.scrollWidth <= innerWidth + 1`),true);
 await page.shot(out+'/manager-phone.png',true);
 await page.go(base+'/operations?'+new URLSearchParams({wallet}));
 assert.equal(await page.eval(`document.querySelectorAll('#personal-trades tbody tr').length`),3);
 assert.equal(await page.eval(`document.querySelector('#personal-trades').textContent.includes('Venda')`),true);
 assert.deepEqual(page.console,[]);
 console.log('PASS: prepare, separate paid consent, fake durable inference, partial sizing, financial preview/keyboard consent, atomic record, reload/history; desktop/phone');
});
