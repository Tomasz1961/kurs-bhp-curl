// Test strony Start (krok 11zz9, TS 16.11.2026 20:12 „jak się otworzy, są nazwiska”; dec. 148) i braku list braków (krok 11zz10, dec. 153).
// ZACHOWANIE: 1) pierwsze dwa ekrany Start (1366×800 i 390×844) nie zawierają żadnego nazwiska z listy osób kursu;
// 2) pierwszy nagłówek treści to „Czym jest CURL…”, a wybór szkolenia jest pod nim; 3) „Rozpocznij szkolenie” przenosi do szkolenia
// krok po kroku (#szkwstepne / #szkokresowe), nie do testu; 4) stan z nazwiskami jest tylko w bloku „Stan szkoleń w zespole” na końcu;
// 5) na żadnej zakładce nie ma „Braki w rejestrze” ani „brak karty – do uzupełnienia”; 6) brak błędów skryptu.
// Użycie: node test_start_tresc.js <kurs.html> <kurs_admin_dane.json?>
// Uwaga Copilota do PR #16: dane osób ładowane jak w kursie – atrapa claude.use (właściciel, baza z kurs_admin/dane z pliku),
// nazwiska do sprawdzenia z tych danych; test wymaga niepustej listy nazwisk i ich obecności w bloku „Stan szkoleń w zespole”.
const {chromium}=require('playwright');const fs=require('fs');const [K,AD]=process.argv.slice(2);
if(!AD||!fs.existsSync(AD)){console.error('brak pliku danych prowadzącego (kurs_admin_dane.json)');process.exit(2)}
const DANE=JSON.parse(fs.readFileSync(AD,'utf8'));const PD=typeof DANE['prac-data']==='string'?JSON.parse(DANE['prac-data']):DANE['prac-data'];
const NAZW=(PD&&PD.ludzie||[]).map(x=>x.n).filter(Boolean);
function atrapa(D0){const D={'kurs_admin/dane':D0};
  const snap=(p,v)=>({id:p.split('/').pop(),exists:v!==undefined,data:()=>v,metadata:{}});
  const dref=p=>({id:p.split('/').pop(),path:p,get:async()=>snap(p,D[p]),set:async v=>{D[p]=v},update:async v=>{Object.assign(D[p]||(D[p]={}),v)},delete:async()=>{delete D[p]},collection:c=>cref(p+'/'+c),onSnapshot:n=>{dref(p).get().then(n);return()=>{}}});
  let nr=0;const cref=c=>({id:c,path:c,doc:id=>dref(c+'/'+(id||('a'+(++nr)))),add:async v=>{const r=dref(c+'/a'+(++nr));await r.set(v);return r},get:async()=>({docs:[],size:0,empty:true,forEach:()=>{},docChanges:()=>[]}),onSnapshot:n=>{cref(c).get().then(n);return()=>{}}});
  const db={collection:cref,doc:dref};
  const user={isOwner:async()=>true,canEdit:async()=>true,can:async()=>true,id:async()=>'u_test',me:async()=>({id:'u_test',name:'tomasz stuczynski',isMe:true}),profiles:async ids=>({}),search:async q=>[]};
  window.claude={use:async n=>n==='db'?db:n==='user'?user:null}}
(async()=>{const b=await chromium.launch();const W={bledy:[],nazwisk_w_danych:NAZW.length};const fail=m=>W.bledy.push(m);
 if(NAZW.length<5)fail('za mało nazwisk w danych prowadzącego: '+NAZW.length);
 for(const vp of [{width:1366,height:800},{width:390,height:844}]){
  const p=await b.newPage({viewport:vp});const pe=[];p.on('pageerror',e=>pe.push(String(e).slice(0,140)));
  await p.addInitScript({content:`(${atrapa.toString()})(${JSON.stringify(DANE)});`});
  await p.goto('file://'+require('path').resolve(K)+'#start');await p.waitForTimeout(4500);
  const r=await p.evaluate(([vh,names])=>{
   const st=document.getElementById('start');const top=st.getBoundingClientRect().top+scrollY;
   // widoczne węzły tekstowe z położeniem (także w elementach mających dzieci, np. <span class="nazwisko">…<span class="data">) – uwaga Copilota do PR #17
   const tw=document.createTreeWalker(st,NodeFilter.SHOW_TEXT);const vt=[];let tn;
   while((tn=tw.nextNode())){if(!tn.textContent.trim()||!tn.parentElement||tn.parentElement.offsetParent===null)continue;
    const rg=document.createRange();rg.selectNodeContents(tn);const q=[...rg.getClientRects()].find(x=>x.height>0);
    if(q&&q.top+scrollY-top<2*vh)vt.push(tn.parentElement.textContent)}
   const vis=vt.join(' ');
   const h=[...st.querySelectorAll('h3')].filter(x=>x.offsetParent!==null).map(x=>x.textContent.trim());
   const zesp=document.getElementById('sto_zespol');
   return {nazwiskaWidoczne:names.filter(n=>vis.includes(n)),h3:h.slice(0,3),wStanie:zesp?zesp.querySelectorAll('li').length:-1,
     nazwiskWZespole:zesp?names.filter(n=>zesp.textContent.includes(n)).length:0,
     osobWKursie:(typeof PEOPLE!=='undefined'?PEOPLE:[]).length,
     stanWKartach:document.querySelectorAll('.wsz-karta .wsz-stan').length,przyciski:[...st.querySelectorAll('[data-sto-start]')].map(x=>x.dataset.stoStart)}},[vp.height,NAZW]);
  W[vp.width]=r;
  if(r.osobWKursie<5)fail(vp.width+': dane osób nie wczytane do kursu (PEOPLE: '+r.osobWKursie+') – test nic by nie sprawdził');
  if(!r.nazwiskWZespole)fail(vp.width+': w bloku „Stan szkoleń w zespole” nie ma nazwisk z danych – test nic by nie sprawdził');
  if(r.nazwiskaWidoczne.length)fail(vp.width+': nazwiska na pierwszych ekranach: '+r.nazwiskaWidoczne.length);
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
