// Renderuje każdą zakładkę kursu (tryb prowadzącego z paczki ZIP) i zapisuje widoczny tekst do JSON.
// Także: (a) każdy wybór z list rozwijanych w zakładce (np. Teczka – każda osoba): klucz "<zakładka>#<lista>=<wartość>";
//        (b) każdy wydruk z przycisków „Drukuj…/Wydruk…” (printNow przechwycony, okno druku nie otwiera się): klucz "<zakładka>~druk<n>".
// Użycie: node render_zakladki.js <plik html> <wyjście json>
const {chromium}=require('playwright');const fs=require('fs');(async()=>{const b=await chromium.launch();const p=await b.newPage();const bledy=[];p.on('pageerror',e=>bledy.push(String(e.message).slice(0,200)));
p.on('dialog',d=>d.dismiss().catch(()=>{}));
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(4000);
// druk: przechwycenie po poprawkach strony (zawinięcie window.print – strona sama poprawia wydruk przed drukiem); okno druku się nie otwiera
await p.evaluate(()=>{window.__druki=[];const op=window.print;window.print=function(){try{op.apply(window,arguments)}catch(e){}
  const pa=document.getElementById('printarea');window.__druki.push('<div>'+(pa?pa.innerHTML:'')+'</div>')};
  window.open=function(){return {document:{write:h=>window.__druki.push(String(h||'')),close(){}},close(){},focus(){},print(){}}}});
const ids=await p.evaluate(()=>[...document.querySelectorAll('section[id]')].map(s=>s.id));
const out={_nawigacja:await p.evaluate(()=>[...document.querySelectorAll('nav a, nav button')].map(a=>a.innerText.trim()).filter(Boolean).join('\n')),
 _poczatek:await p.evaluate(()=>location.hash+'\n'+document.body.innerText.slice(0,1500))};
const txt=i=>p.evaluate(i=>{const s=document.getElementById(i);s.querySelectorAll('details').forEach(d=>d.open=true);if(getComputedStyle(s).display==='none'||!s.getClientRects().length)return '';return s.innerText},i);
for(const id of ids){await p.evaluate(i=>location.hash='#'+i,id);await p.waitForTimeout(400);
 out[id]=await txt(id);
 if(!out[id])continue;
 // (a) listy rozwijane
 const sel=await p.evaluate(i=>[...document.getElementById(i).querySelectorAll('select')].map((s,n)=>({n,id:s.id||('lista'+n),v:[...s.options].map(o=>o.value).slice(0,80)})),id);
 for(const s of sel){for(const v of s.v){await p.evaluate(([i,n,v])=>{const s=document.getElementById(i).querySelectorAll('select')[n];if(!s)return;s.value=v;s.dispatchEvent(new Event('change',{bubbles:true}));s.dispatchEvent(new Event('input',{bubbles:true}))},[id,s.n,v]);
   await p.waitForTimeout(120);out[id+'#'+s.id+'='+v]=await txt(id)}}
 // (b) wydruki
 const nb=await p.evaluate(i=>[...document.getElementById(i).querySelectorAll('button')].filter(b=>/drukuj|wydruk/i.test(b.innerText)&&b.offsetParent).length,id);
 for(let k=0;k<nb;k++){await p.evaluate(()=>window.__druki=[]);
   await p.evaluate(([i,k])=>{const b=[...document.getElementById(i).querySelectorAll('button')].filter(b=>/drukuj|wydruk/i.test(b.innerText)&&b.offsetParent)[k];try{b&&b.click()}catch(e){}},[id,k]);
   await p.waitForTimeout(300);
   const d=await p.evaluate(()=>window.__druki.map(h=>{const t=document.createElement('div');t.innerHTML=h.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/gi,' ');return t.innerText||t.textContent}).join('\n'));
   if(d)out[id+'~druk'+k]=d}}
out._bledy_strony=bledy.join('\n');fs.writeFileSync(process.argv[3],JSON.stringify(out));console.log('zakładek',ids.length);await b.close()})()
