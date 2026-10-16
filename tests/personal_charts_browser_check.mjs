// APP-03 actual cached history; every POST and external request blocked.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {session,VIEWPORTS} from '../scripts/ui_cdp_v762.mjs';
const [base,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
const wallet='manual-5be40ea8853a476e94b799b6d45389ed';
const catalog=await(await fetch(base+'/api/portfolio/manual')).json();
const other=catalog.wallets.find(w=>w.id!==wallet);
await session(async page=>{
 const blocked=[];let collects=0;
 page.listeners.push(m=>{
  if(m.method!=='Fetch.requestPaused')return;
  const {request,requestId}=m.params;
  // Intraday collection would reach Yahoo: answer it locally and read only the archive.
  if(request.method==='POST'&&request.url===base+'/api/portfolio/stock-history/intraday/refresh'){
   collects++;
   return page.send('Fetch.fulfillRequest',{requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify({identity:'HFL-STOCK-INTRADAY-YAHOO-V1',refresh_errors:{}})).toString('base64')});
  }
  const safe=request.method==='GET'&&new URL(request.url).origin===base;
  if(!safe)blocked.push(request.url);
  page.send(safe?'Fetch.continueRequest':'Fetch.failRequest',safe?{requestId}:{requestId,errorReason:'BlockedByClient'});
 });
 await page.send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
 for(const size of ['desktop','phone']){
  await page.viewport(VIEWPORTS[size]);await page.go(base+'/?wallet='+wallet);
  for(let i=0;i<150;i++){
   if(await page.eval(`Boolean(window.Chart?.getChart('personal-stock-chart') && Chart.getChart('personal-equity-chart'))`))break;
   await new Promise(r=>setTimeout(r,100));
  }
  assert.equal(await page.eval(`document.querySelector('#personal-chart-error').hidden`),true);
  assert.equal(await page.eval(`document.querySelector('#personal-stock-error').hidden`),true);
  assert.match(await page.eval(`document.querySelector('#personal-metrics').textContent`),/99.831,60/);
  // Later sessions without a B3 mark stay null; the curve grows with the calendar.
  const nav=await page.eval(`Chart.getChart('personal-equity-chart').data.datasets[0].data`);
  assert.deepEqual(nav.slice(0,2),[100000,99835.33]);assert.ok(nav.length>2&&nav.slice(2).every(v=>v==null));
  if(!await page.eval(`Boolean(Chart.getChart('personal-stock-chart'))`)){console.log(size,await page.eval(`({note:document.querySelector('#personal-stock-note').textContent,error:document.querySelector('#personal-stock-error').textContent})`),page.console,blocked);await page.shot(out+'/failure.png',true);throw Error('stock chart missing');}
  assert.equal(await page.eval(`Chart.getChart('personal-stock-chart').data.datasets[0].label`),'PETR4');
  await page.click('[data-stock-period="max"]');
  assert.ok(await page.eval(`Chart.getChart('personal-stock-chart').data.labels.length>6000`));
  assert.equal(await page.eval(`Chart.getChart('personal-stock-chart').data.labels[0]`),'03/01/2000');
  assert.equal(await page.eval(`Chart.getChart('personal-stock-chart').data.datasets[0].spanGaps`),false);
  const until=async(expr,what)=>{for(let i=0;i<100;i++){if(await page.eval(expr))return;await new Promise(r=>setTimeout(r,100));}throw Error(what+' never happened: '+await page.eval(`document.querySelector('#personal-stock-note').textContent`));};
  await page.click('[data-stock-period="5d"]');
  await until(`Chart.getChart('personal-stock-chart')?.data.labels.length>300`,'5D intraday');
  assert.match(await page.eval(`document.querySelector('#personal-stock-note').textContent`),/intradiário · barras de 5 min/);
  await page.eval(`document.querySelector('#personal-stock-from').value='2026-10-15';document.querySelector('#personal-stock-to').value='2026-10-15';`);
  await page.click('#personal-stock-range button[type="submit"]');
  await until(`Chart.getChart('personal-stock-chart')?.data.labels.length>400`,'one-day 1m');
  assert.match(await page.eval(`Chart.getChart('personal-stock-chart').data.labels.join(',')`),/^10:0\d,(\d\d:\d\d,)+\d\d:\d\d$/);
  assert.match(await page.eval(`document.querySelector('#personal-stock-note').textContent`),/barras de 1 min/);
  await page.click('[data-stock-period="5d"]');
  await until(`Chart.getChart('personal-stock-chart')?.data.labels.length>300`,'5D again');
  await page.click('#personal-stock-assets input[value="VALE3"]');
  await until(`Chart.getChart('personal-stock-chart')?.data.datasets.length===2`,'second asset');
  assert.equal(await page.eval(`document.activeElement.value`),'VALE3');
  await page.click('[data-stock-period="1mo"]');
  await until(`/barras de 1 hora/.test(document.querySelector('#personal-stock-note').textContent)&&Boolean(Chart.getChart('personal-stock-chart'))`,'1M hourly');
  await page.eval(`document.querySelector('#personal-stock-mode').value='change';document.querySelector('#personal-stock-mode').dispatchEvent(new Event('change',{bubbles:true}));`);
  assert.equal(await page.eval(`Chart.getChart('personal-stock-chart').data.datasets.every(s=>s.data[0]===0)`),true);
  await page.eval(`document.querySelector('#personal-stock-mode').value='price';document.querySelector('#personal-stock-mode').dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('#personal-stock-from').value='2026-10-05';document.querySelector('#personal-stock-to').value='2026-10-14';`);
  await page.click('#personal-stock-range button[type="submit"]');
  await until(`/barras de 15 min/.test(document.querySelector('#personal-stock-note').textContent)&&Boolean(Chart.getChart('personal-stock-chart'))`,'8 sessions at 15m');
  const expected=await page.eval(`(()=>{const c=Chart.getChart('personal-stock-chart');return c.data.datasets.map(s=>((s.data.at(-2)/s.data[1]-1)*100).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'%');})()`);
  await page.eval(`document.querySelector('#personal-stock-chart').scrollIntoView({block:'center'});`);
  const p=await page.eval(`(()=>{const c=Chart.getChart('personal-stock-chart'),r=c.canvas.getBoundingClientRect();return {x:r.x+c.scales.x.getPixelForValue(1),z:r.x+c.scales.x.getPixelForValue(c.data.labels.length-2),y:r.y+(c.chartArea.top+c.chartArea.bottom)/2};})()`);
  if(size==='desktop'){
   await page.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x,y:p.y});
   await page.send('Input.dispatchMouseEvent',{type:'mousePressed',x:p.x,y:p.y,button:'left',buttons:1,clickCount:1});
   await page.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.z,y:p.y,button:'left',buttons:1});
   await page.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:p.z,y:p.y,button:'left',clickCount:1});
  }else{
   await page.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:p.x,y:p.y}]});
   await page.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:p.z,y:p.y}]});
   await page.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  }
  assert.match(await page.eval(`document.querySelector('#personal-stock-interval').textContent`),/Intervalo selecionado/);
  const summary=await page.eval(`document.querySelector('#personal-stock-summary').textContent`);
  for(const change of expected)assert.ok(summary.includes(change),summary+' lacks '+change);
  assert.equal(await page.eval(`document.documentElement.scrollWidth<=innerWidth+1`),true);
  await page.shot(out+'/'+size+'-stock-explorer.png',true);
  await page.click('#personal-stock-clear');
  assert.match(await page.eval(`document.querySelector('#personal-stock-interval').textContent`),/Período exibido/);
  await page.click('#personal-stock-details summary');
  assert.match(await page.eval(`document.querySelector('#personal-stock-table').textContent`),/05\/10\/2026/);
  await page.click('#personal-stock-all');
  await until(`Chart.getChart('personal-stock-chart')?.data.datasets.length===5`,'all assets');
  assert.equal(await page.eval(`Chart.getChart('personal-stock-chart').data.datasets.length`),5);
  assert.equal(await page.eval(`document.querySelector('#personal-stock-from').value`),'2026-10-05');
  assert.equal(await page.eval(`document.querySelector('#personal-stock-to').value`),'2026-10-14');
  await page.go(base+'/?wallet='+other.id);
  for(let i=0;i<150;i++){
   if(await page.eval(`Boolean(window.Chart?.getChart('personal-equity-chart'))`))break;
   await new Promise(r=>setTimeout(r,100));
  }
  assert.equal(await page.eval(`Chart.getChart('personal-equity-chart').data.datasets[0].label`),other.name);
 }
 assert.deepEqual(blocked,[]);assert.deepEqual(page.console,[]);assert.ok(collects>=2,'intraday collection on load');
 console.log('PASS: max history from 2000, intraday 1m/5m/15m/1h from the local archive, presets, custom dates, action selection, normalization, mouse/touch interval percentages, tables, wallet switch, NAV preservation, desktop/phone; GET only.');
});
