// obchód propozycji etapu 2 (BHP w jednym oknie): node obchod2.js <url_powloki> <katalog_zrzutow> [ekrany...]
// powłoka testowa podaje treść w ramce (jak strona /pelny/ po zalogowaniu) i WWW_RAMA.strona z jawnych kopii stron części zarządzania BHP
const {chromium}=require('playwright');const [url,out,...ekr]=process.argv.slice(2);
const EKR=[{n:'telefon',w:390,h:844},{n:'laptop',w:1366,h:768}];
const S=ekr.length?ekr:['','#szkolenie','#wiedza','#bhp','#bhp/mapa','#bhp/srodki','#bhp/ludzie','#bhp/ludzie/strona','#bhp/szkolenia','#bhp/dokumenty','#sprawy','#bhp/index/terminy','#alerty','#konto'];
(async()=>{const b=await chromium.launch();
for(const e of EKR){const c=await b.newContext({viewport:{width:e.w,height:e.h},deviceScaleFactor:1});const p=await c.newPage();const bl=[];p.on('pageerror',x=>bl.push(x.message));
 await p.goto(url);await p.waitForTimeout(3000);const fr=p.frames().find(f=>/tresc\.html/.test(f.url()));
 fr.on&&0;p.on('framenavigated',()=>{});
 for(const s of S){if(s)await fr.evaluate(h=>{location.hash=h},s);await p.waitForTimeout(/^#bhp\/(?!ludzie$)/.test(s)?3000:800);
  const m=await fr.evaluate(()=>({hash:location.hash,t:(document.getElementById('rama_tytul')||{}).textContent,w:document.documentElement.scrollWidth,h:document.documentElement.scrollHeight,
   nav:[...document.querySelectorAll('#rama_dol a')].filter(a=>a.offsetParent).map(a=>a.innerText.replace(/\s+/g,' ').trim()+(a.classList.contains('akt')?'*':'')),
   ramka:(document.querySelector('.bhp-ramka')||{}).offsetHeight||0,
   ukryte:(()=>{const f=document.querySelector('.bhp-ramka');if(!f||!f.contentDocument)return null;const d=f.contentDocument;const n=d.querySelector('nav.pasek'),g=d.querySelector('body>div[style*="sticky"]');return [n&&getComputedStyle(n).display,g&&getComputedStyle(g).display,d.documentElement.scrollWidth]})()}));
  console.log(e.n,JSON.stringify(s),JSON.stringify(m));
  await p.screenshot({path:`${out}/${e.n}_${(s||'start').replace(/[^a-z0-9]/gi,'_')}.png`})}
 if(bl.length)console.log('BŁĘDY',bl.slice(0,5));await c.close()}
await b.close()})();
