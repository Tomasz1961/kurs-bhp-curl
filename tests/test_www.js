// Test strony www aplikacji CURL w przeglądarce bezgłowej – sprawdza ZACHOWANIE, nie tekst.
// Od 19.11.2026 (polecenie TS 09:20, dec. 193) strona publiczna to „O aplikacji”: bez treści szkoleń, bez testu, bez zapisu wyniku,
// bez pól PIN-u, hasła i przesyłania pliku; z przyciskami logowania do /pracownik/ i /pelny/. Strony /pracownik/ i /pelny/ są
// zaszyfrowane: otwierają się formularzem hasła strony, a w ich źródle nie ma jawnej treści szkoleń.
// Każde żądanie POST jest blokowane przed wysłaniem i liczone. Wynik OK tylko, gdy:
//  P1 strona publiczna odpowiada 200, nie ma sekcji szkoleń ani testu, nie ma funkcji zapisu wyniku, nie pobiera zapis.json;
//  P2 na stronie publicznej nie ma żadnego pola formularza (PIN, hasło, plik) i nie ma żadnego POST;
//  P3 są odnośniki do pracownik/ i pelny/, a obie strony odpowiadają 200, pokazują pole hasła strony i nie mają jawnej treści szkoleń;
//  P4 brak błędów skryptu.
// URL: adres strony (domyślnie GitHub Pages); w prośbie o scalenie test idzie na lokalnym serwerze z plikami gałęzi.
// TRYB=negatywny: strona publiczna dostaje dopisaną sekcję testu z polem PIN, pobranie zapis.json i formularz POST (jak dawna strona
// z zapisem wyniku); test MUSI wtedy dać BŁĄD (sprawdza to krok w Actions).
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const URL=process.env.URL||'https://tomasz1961.github.io/kurs-bhp-curl/';const NEG=process.env.TRYB==='negatywny';
 const b=await chromium.launch();const pg=await b.newPage();const errs=[];pg.on('pageerror',e=>errs.push(String(e).slice(0,200)));
 const posty=[],zapisy=[];
 await pg.route('**/*',async r=>{const q=r.request();if(q.method()==='POST'){posty.push(q.url());return r.abort()}
  if(/\/zapis\.json(\?|$)/.test(q.url()))zapisy.push(q.url());
  if(NEG&&q.resourceType()==='document'&&q.url().replace(/index\.html$/,'')===URL){const o=await r.fetch();let t=await o.text();
   t=t.replace('</main>','<section id="test"><input id="zw_pin" type="password"><input type="file"><form id="negf" method="post" action="https://script.google.com/macros/s/TEST_NEGATYWNY/exec"><input name="x" value="1"></form></section>'
    +'<script>window.saveResult=function(){};fetch("zapis.json").catch(()=>{});document.getElementById("negf").submit()</script></main>');
   return r.fulfill({response:o,body:t,headers:{...o.headers(),'content-type':'text/html; charset=utf-8'}})}
  return r.continue()});
 const W={url:URL,tryb:NEG?'negatywny':'zwykły'};
 const odp=await pg.goto(URL,{waitUntil:'load',timeout:120000});await pg.waitForTimeout(2500);W.http=odp?odp.status():null;
 // P1
 W.sekcje_szkolen=await pg.$$eval('section#test, section#m1, section#szkwstepne, main section',x=>x.length);
 W.funkcja_zapisu=await pg.evaluate(()=>typeof window.saveResult==='function'||typeof window.ZAPISWWW==='function');
 W.pobrania_zapis_json=zapisy.length;
 // P2
 W.pola_formularza=await pg.$$eval('input, textarea, select',x=>x.filter(e=>e.type!=='hidden').map(e=>e.id||e.name||e.type));
 // P3
 const hrefy=await pg.$$eval('a[href]',a=>a.map(x=>x.getAttribute('href')));
 W.przyciski_logowania={pracownik:hrefy.some(h=>/^(\.\/)?pracownik\/?$/.test(h)),pelny:hrefy.some(h=>/^(\.\/)?pelny\/?$/.test(h))};
 W.strony_logowania={};
 for(const s of ['pracownik/','pelny/']){const p2=await b.newPage();p2.on('pageerror',e=>errs.push(s+': '+String(e).slice(0,200)));
  await p2.route('**/*',r=>{if(r.request().method()==='POST'){posty.push(r.request().url());return r.abort()}return r.continue()});
  const u=new globalThis.URL(s,URL).href;const o=await p2.goto(u,{waitUntil:'load',timeout:120000}).catch(()=>null);await p2.waitForTimeout(1000);
  const zr=await p2.request.get(u).then(x=>x.text()).catch(()=>'');
  W.strony_logowania[s]={http:o?o.status():null,pole_hasla:!!(await p2.$('#h')),jawna_tresc:/<section\b[^>]*\bid="(test|m1|szkwstepne)"/.test(zr)};await p2.close()}
 W.zadania_POST=posty;W.bledy_strony=errs;
 const L=Object.values(W.strony_logowania);
 const ok=W.http===200&&W.sekcje_szkolen===0&&!W.funkcja_zapisu&&W.pobrania_zapis_json===0&&W.pola_formularza.length===0&&!posty.length
  &&W.przyciski_logowania.pracownik&&W.przyciski_logowania.pelny&&L.length===2&&L.every(x=>x.http===200&&x.pole_hasla&&!x.jawna_tresc)&&!errs.length;
 W.WYNIK=ok?'OK':'BŁĄD';fs.writeFileSync(NEG?'wynik_testu_negatywnego.json':'wynik_testu.json',JSON.stringify(W,null,1));console.log(JSON.stringify(W,null,1));await b.close();process.exit(ok?0:1)})();
