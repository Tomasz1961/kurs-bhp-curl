// Test strony www kursu na żywo (GitHub Pages) w przeglądarce bezgłowej – sprawdza ZACHOWANIE, nie tekst.
// Wersja publiczna (audyt stanu 15.11.2026, C-01/C-02/C-05) nie zapisuje wyniku. Test przechodzi prawdziwą ścieżką zapisu
// strony: saveResult → ZAPISWWW (pobiera zapis.json) → ZASWPO, z prawdziwym zapis.json z serwera. Każde żądanie POST jest
// blokowane przed wysłaniem i liczone. Wynik OK tylko, gdy: ścieżka zapisu skończyła się stanem „bez zapisu” (element .niezapis
// w polu statusu), nie pojawiło się pole PIN ani kodu osoby, nie było żadnego POST, oba zaświadczenia pobierają się jako PDF,
// w żadnej zakładce i sekcji (także wywołanej adresem) nie widać pola przesyłania pliku ani PIN-u, nie ma przycisku przesyłania skanu
// i nie ma błędów skryptu.
// TRYB=negatywny: zapis.json zostaje podmieniony na poprawny adres aplikacji zapisu (jak po ponownym włączeniu zapisu);
// test MUSI wtedy dać BŁĄD (sprawdza to krok w Actions).
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const URL=process.env.URL||'https://tomasz1961.github.io/kurs-bhp-curl/';const NEG=process.env.TRYB==='negatywny';
 const b=await chromium.launch();const pg=await b.newPage({acceptDownloads:true});const errs=[];pg.on('pageerror',e=>errs.push(String(e).slice(0,200)));
 const posty=[];await pg.route('**/*',r=>{if(r.request().method()==='POST'){posty.push(r.request().url());return r.abort()}return r.continue()});
 if(NEG)await pg.route('**/zapis.json',r=>r.fulfill({body:JSON.stringify({url:'https://script.google.com/macros/s/TEST_NEGATYWNY/exec'}),contentType:'application/json'}));
 const odp=await pg.goto(URL,{waitUntil:'load',timeout:120000});await pg.waitForTimeout(3000);const W={url:URL,tryb:NEG?'negatywny':'zwykły',http:odp?odp.status():null};
 W.wersja=(await pg.textContent('body')).match(/wersja v[\d.]+ z [\d.]+/)?.[0];
 await pg.evaluate(()=>{const t=document.getElementById('test');t.hidden=false;t.style.display='block'});
 W.sciezka_zapisu=await pg.evaluate(()=>typeof saveResult==='function'&&typeof window.ZAPISWWW==='function');
 await pg.evaluate(()=>{let d=document.getElementById('savestatus');if(!d){d=document.createElement('p');d.id='savestatus';document.body.appendChild(d)}d.innerHTML='';
  window.__zapisGotowy=false;window.__zapis=saveResult({zaliczony:1,kod_osoby:'UCZ',uczestnik:'Test Automatyczny',data:'2026-11-14',rodzaj:'BHP_okresowe',punkty:8,liczba_pytan:8,procent:100,answers:'',temat:'Test BHP – pracownicy'})});
 // czekamy na koniec operacji zapisu (albo na formularz PIN, który ją wstrzymuje), nie na stały czas
 await pg.evaluate(()=>{window.__zapis.then(()=>{window.__zapisGotowy=true},()=>{window.__zapisGotowy=true})});
 await pg.waitForFunction(()=>window.__zapisGotowy||document.getElementById('zw_ok'),null,{timeout:30000});
 W.stan_bez_zapisu=await pg.$$eval('#savestatus .niezapis',x=>x.length);
 // gdyby strona poprosiła o kod i PIN, test je wpisuje, żeby sprawdzić, czy wynik poszedłby żądaniem POST (blokowanym wyżej)
 if(await pg.$('#zw_ok')){W.formularz_pin_wypelniony=true;await pg.fill('#zw_kod','TS');await pg.fill('#zw_pin','000000');await pg.click('#zw_ok');await pg.waitForFunction(()=>window.__zapisGotowy,null,{timeout:30000}).catch(()=>{W.zapis_bez_konca=true})}
 W.pola_pin_lub_kodu=await pg.$$eval('#zw_pin, #zw_kod, #sk_pin, #sk_kod, input[type=password]',x=>x.filter(e=>!e.closest('[hidden]')&&e.type!=='hidden').length);
 for(const a of ['zbhp','zqms']){const [d]=await Promise.all([pg.waitForEvent('download',{timeout:NEG?8000:60000}).catch(()=>null),pg.click(`#zasw_po button[data-a="${a}"]`,{force:true,timeout:10000}).catch(()=>null)]);
  if(d){const p='wynik_'+(NEG?'negatywny_':'')+a+'.pdf';await d.saveAs(p);const t=fs.readFileSync(p);W[a]={plik:d.suggestedFilename(),bajty:t.length,pdf:t.slice(0,5).toString()==='%PDF-'}}else W[a]=null}
 W.przycisk_przeslij=await pg.$$eval('button[data-a="przeslij"]',x=>x.length);
 // pola przesyłania pliku i PIN-u, które odwiedzający może zobaczyć: każda zakładka z menu i każda sekcja strony (także usunięte z menu) wywołana adresem
 const zakladki=await pg.$$eval('#nav a[href^="#"], main section[id]',x=>x.map(a=>a.tagName==='A'?a.getAttribute('href'):'#'+a.id));W.zakladki_sprawdzone=0;W.widoczne_pola_przesylania=[];
 for(const z of [...new Set(zakladki)]){await pg.evaluate(h=>{location.hash=h},z);await pg.waitForTimeout(150);W.zakladki_sprawdzone++;
  const w=await pg.$$eval('input[type=file], #zw_pin, #sk_pin, input[type=password]',x=>x.filter(e=>e.type!=='hidden'&&e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden').map(e=>e.id||e.name||e.type));
  for(const i of w)W.widoczne_pola_przesylania.push(z+':'+i)}
 W.pole_pliku_skanu=W.widoczne_pola_przesylania.length;
 W.zadania_POST=posty;W.bledy_strony=errs;
 const ok=W.http===200&&W.sciezka_zapisu&&W.stan_bez_zapisu===1&&W.pola_pin_lub_kodu===0&&!W.formularz_pin_wypelniony&&!posty.length&&W.zbhp?.pdf&&W.zqms?.pdf&&W.przycisk_przeslij===0&&W.pole_pliku_skanu===0&&!errs.length;
 W.WYNIK=ok?'OK':'BŁĄD';fs.writeFileSync(NEG?'wynik_testu_negatywnego.json':'wynik_testu.json',JSON.stringify(W,null,1));console.log(JSON.stringify(W,null,1));await b.close();process.exit(ok?0:1)})();
