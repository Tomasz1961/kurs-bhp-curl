// Renderuje każdą zakładkę kursu (tryb prowadzącego z paczki ZIP) i zapisuje widoczny tekst do JSON.
// Użycie: node render_zakladki.js <plik html> <wyjście json>
const {chromium}=require('playwright');const fs=require('fs');(async()=>{const b=await chromium.launch();const p=await b.newPage();const bledy=[];p.on('pageerror',e=>bledy.push(String(e.message).slice(0,200)));
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(4000);
const ids=await p.evaluate(()=>[...document.querySelectorAll('section[id]')].map(s=>s.id));
const out={_nawigacja:await p.evaluate(()=>[...document.querySelectorAll('nav a, nav button')].map(a=>a.innerText.trim()).filter(Boolean).join('\n')),
 _poczatek:await p.evaluate(()=>location.hash+'\n'+document.body.innerText.slice(0,1500))};
for(const id of ids){await p.evaluate(i=>location.hash='#'+i,id);await p.waitForTimeout(400);
 out[id]=await p.evaluate(i=>{const s=document.getElementById(i);s.querySelectorAll('details').forEach(d=>d.open=true);if(getComputedStyle(s).display==='none'||!s.getClientRects().length)return '';return s.innerText},id)}
out._bledy_strony=bledy.join('\n');fs.writeFileSync(process.argv[3],JSON.stringify(out));console.log('zakładek',ids.length);await b.close()})()
