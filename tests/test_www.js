// Test strony www kursu na żywo (GitHub Pages) w przeglądarce bezgłowej.
// Od audytu stanu 15.11.2026 (C-01, C-02, C-05) wersja publiczna nie zapisuje wyniku i nie ma formularza przesyłania skanów:
// test sprawdza, że strona mówi to wprost, że wydruki zaświadczeń są plikami PDF i że nie ma przycisku ani pól przesyłania.
// Prawdziwy plik zapis.json (bez atrapy), więc test widzi to, co widzi pracownik.
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const URL=process.env.URL||'https://tomasz1961.github.io/kurs-bhp-curl/';const b=await chromium.launch();
 const pg=await b.newPage({acceptDownloads:true});const errs=[];pg.on('pageerror',e=>errs.push(String(e).slice(0,200)));
 const wyslane=[];pg.on('request',r=>{if(r.method()==='POST')wyslane.push(r.url())});
 const odp=await pg.goto(URL,{waitUntil:'load',timeout:120000});await pg.waitForTimeout(3000);const W={url:URL,http:odp?odp.status():null};
 W.wersja=(await pg.textContent('body')).match(/wersja v[\d.]+ z [\d.]+/)?.[0];
 await pg.evaluate(()=>{const t=document.getElementById('test');t.hidden=false;t.style.display='block'});
 W.ramka=await pg.textContent('#skan_www h3').catch(()=>null);
 await pg.evaluate(()=>{const d=document.createElement('p');d.id='savestatus';document.body.appendChild(d);ZASWPO({zaliczony:1,kod_osoby:'UCZ',uczestnik:'Test Automatyczny',data:'2026-11-14',rodzaj:'BHP_okresowe',punkty:8,liczba_pytan:8,procent:100,answers:'',temat:'Test BHP – pracownicy'},d)});
 for(const a of ['zbhp','zqms']){const [d]=await Promise.all([pg.waitForEvent('download',{timeout:60000}).catch(()=>null),pg.click(`#zasw_po button[data-a="${a}"]`,{force:true})]);
  if(d){const p='wynik_'+a+'.pdf';await d.saveAs(p);const t=fs.readFileSync(p);W[a]={plik:d.suggestedFilename(),bajty:t.length,pdf:t.slice(0,5).toString()==='%PDF-'}}else W[a]=null}
 W.komunikat_niezapis=(await pg.textContent('body')).includes('Wynik nie zapisuje się automatycznie');
 W.przycisk_przeslij=await pg.$$eval('button[data-a="przeslij"]',x=>x.length);
 W.pole_pliku_skanu=await pg.$$eval('#sk_plik',x=>x.length);
 W.wyslane_POST=wyslane;W.przyciski=await pg.$$eval('#skan_www button, #zasw_po button',bs=>[...new Set(bs.map(x=>x.textContent))]);W.bledy_strony=errs;
 const ok=W.http===200&&W.zbhp?.pdf&&W.zqms?.pdf&&W.komunikat_niezapis&&W.przycisk_przeslij===0&&W.pole_pliku_skanu===0&&!wyslane.length&&!errs.length;W.WYNIK=ok?'OK':'BŁĄD';
 fs.writeFileSync('wynik_testu.json',JSON.stringify(W,null,1));console.log(JSON.stringify(W,null,1));await b.close();process.exit(ok?0:1)})();
