// Test strony www kursu na żywo (GitHub Pages) w przeglądarce bezgłowej. Adres aplikacji zapisu (/exec) jest podstawiony atrapą,
// dopóki aplikacja Apps Script nie jest wdrożona; po wdrożeniu atrapa obejmuje tylko wysyłkę skanu (bez zapisów w rejestrze).
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const URL=process.env.URL||'https://tomasz1961.github.io/kurs-bhp-curl/';const b=await chromium.launch();
 const pg=await b.newPage({acceptDownloads:true});const errs=[];pg.on('pageerror',e=>errs.push(String(e).slice(0,200)));let posted=null;
 await pg.route('**/zapis.json',r=>r.fulfill({body:JSON.stringify({url:'https://script.google.com/macros/s/ATRAPA_testu/exec'}),contentType:'application/json'}));
 await pg.route('https://script.google.com/**',r=>{posted=JSON.parse(r.request().postData());r.fulfill({body:JSON.stringify({ok:true,plik:'ATRAPA.pdf',sha256:'0123456789abcdef'}),contentType:'application/json'})});
 const odp=await pg.goto(URL,{waitUntil:'load',timeout:120000});await pg.waitForTimeout(3000);const W={url:URL,http:odp.status()};
 W.wersja=(await pg.textContent('body')).match(/wersja v[\d.]+ z [\d.]+/)?.[0];
 await pg.evaluate(()=>{const t=document.getElementById('test');t.hidden=false;t.style.display='block'});
 W.ramka=await pg.textContent('#skan_www h3');
 await pg.evaluate(()=>{const d=document.createElement('p');d.id='savestatus';document.body.appendChild(d);ZASWPO({zaliczony:1,kod_osoby:'UCZ',uczestnik:'Test Automatyczny',data:'2026-11-14',rodzaj:'BHP_okresowe',punkty:8,liczba_pytan:8,procent:100,answers:'',temat:'Test BHP – pracownicy'},d)});
 for(const a of ['zbhp','zqms']){const [d]=await Promise.all([pg.waitForEvent('download',{timeout:60000}).catch(()=>null),pg.click(`#zasw_po button[data-a="${a}"]`,{force:true})]);
  if(d){const p='wynik_'+a+'.pdf';await d.saveAs(p);const t=fs.readFileSync(p);W[a]={plik:d.suggestedFilename(),bajty:t.length,pdf:t.slice(0,5).toString()==='%PDF-'}}else W[a]=null}
 await pg.click('#zasw_po button[data-a="przeslij"]',{force:true});await pg.fill('#sk_kod','TS');await pg.fill('#sk_pin','TEST01');
 fs.writeFileSync('skan.pdf','%PDF-1.4\n%test\n');await pg.setInputFiles('#sk_plik','skan.pdf');await pg.click('#sk_wyslij',{force:true});await pg.waitForTimeout(1500);
 W.przeslij=await pg.textContent('#sk_st');W.wyslano=posted&&{typ:posted.typ,kod:posted.kod_osoby,pin_skrot_dl:posted.pin_skrot.length,mime:posted.mime};
 W.przyciski=await pg.$$eval('#skan_www button, #zasw_po button',bs=>[...new Set(bs.map(x=>x.textContent))]);W.bledy_strony=errs;
 const ok=W.http===200&&W.ramka&&W.zbhp?.pdf&&W.zqms?.pdf&&W.wyslano?.typ==='skan'&&!errs.length;W.WYNIK=ok?'OK':'BŁĄD';
 fs.writeFileSync('wynik_testu.json',JSON.stringify(W,null,1));console.log(JSON.stringify(W,null,1));await b.close();process.exit(ok?0:1)})();
