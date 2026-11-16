// Test strony Start (krok 11zz9, TS 16.11.2026 20:12 „jak się otworzy, są nazwiska”; dec. 148) i braku list braków (krok 11zz10, dec. 153).
// ZACHOWANIE: 1) pierwsze dwa ekrany Start (1366×800 i 390×844) nie zawierają żadnego nazwiska z listy osób kursu;
// 2) pierwszy nagłówek treści to „Czym jest CURL…”, a wybór szkolenia jest pod nim; 3) „Rozpocznij szkolenie” przenosi do szkolenia
// krok po kroku (#szkwstepne / #szkokresowe), nie do testu; 4) stan z nazwiskami jest tylko w bloku „Stan szkoleń w zespole” na końcu;
// 5) na żadnej zakładce nie ma „Braki w rejestrze” ani „brak karty – do uzupełnienia”; 6) brak błędów skryptu.
// Użycie: node test_start_tresc.js <kurs.html> <kurs_admin_dane.json?>
const {chromium}=require('playwright');const fs=require('fs');const [K,AD]=process.argv.slice(2);
(async()=>{const b=await chromium.launch();const W={bledy:[]};const fail=m=>W.bledy.push(m);
 for(const vp of [{width:1366,height:800},{width:390,height:844}]){
  const p=await b.newPage({viewport:vp});const pe=[];p.on('pageerror',e=>pe.push(String(e).slice(0,140)));
  await p.goto('file://'+require('path').resolve(K));await p.waitForTimeout(3500);
  if(AD&&fs.existsSync(AD)){const d=JSON.parse(fs.readFileSync(AD,'utf8'));await p.evaluate(d=>{try{window.__ADMIN_TEST__=d}catch(e){}},d)}
  const r=await p.evaluate(vh=>{const names=(window.PEOPLE||[]).map(x=>x[1]).filter(n=>n&&!/Uczestnik/.test(n));
   const st=document.getElementById('start');const top=st.getBoundingClientRect().top+scrollY;
   const vis=[...st.querySelectorAll('*')].filter(e=>{const q=e.getBoundingClientRect();return e.children.length===0&&q.height>0&&q.top+scrollY-top<2*vh&&e.offsetParent!==null}).map(e=>e.textContent).join(' ');
   const h=[...st.querySelectorAll('h3')].filter(x=>x.offsetParent!==null).map(x=>x.textContent.trim());
   const zesp=document.getElementById('sto_zespol');
   return {nazwiskaWidoczne:names.filter(n=>vis.includes(n)),h3:h.slice(0,3),wStanie:zesp?zesp.querySelectorAll('li').length:-1,
     stanWKartach:document.querySelectorAll('.wsz-karta .wsz-stan').length,przyciski:[...st.querySelectorAll('[data-sto-start]')].map(x=>x.dataset.stoStart)}},vp.height);
  W[vp.width]=r;
  if(r.nazwiskaWidoczne.length)fail(vp.width+': nazwiska na pierwszych ekranach: '+r.nazwiskaWidoczne.join(', '));
  if(!/^Czym jest CURL/.test(r.h3[0]||''))fail(vp.width+': pierwszy nagłówek nie jest opisem CURL: '+r.h3[0]);
  if(r.h3[1]!=='Wybierz swoje szkolenie')fail(vp.width+': wybór szkolenia nie jest drugi');
  if(r.stanWKartach)fail('stan z nazwiskami w kartach szkoleń');
  if(r.przyciski.join()!=='#szkwstepne,#szkokresowe,#szkokresowe')fail('przyciski Start: '+r.przyciski.join());
  if(vp.width===1366){await p.click('[data-sto-start="#szkwstepne"]');await p.waitForTimeout(500);
   const hs=await p.evaluate(()=>location.hash);W.po_kliknieciu=hs;if(hs!=='#szkwstepne')fail('„Rozpocznij szkolenie” nie prowadzi do szkolenia wstępnego');
   const ids=await p.$$eval('main section[id]',a=>a.map(x=>x.id));const zle=[];
   for(const id of ids){await p.evaluate(i=>location.hash='#'+i,id);await p.waitForTimeout(150);
     const t=await p.$eval('#'+id,s=>s.innerText);if(/Braki w rejestrze|brak karty – do uzupełnienia/.test(t))zle.push(id)}
   W.braki=zle;if(zle.length)fail('listy braków na zakładkach: '+zle.join())}
  if(pe.length)fail(vp.width+': błędy skryptu '+pe.join(' | '));await p.close()}
 W.WYNIK=W.bledy.length?'BŁĄD':'OK';console.log(JSON.stringify(W,null,1));await b.close();process.exit(W.bledy.length?1:0)})();
