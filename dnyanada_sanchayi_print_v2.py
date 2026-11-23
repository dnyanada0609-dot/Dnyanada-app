#!/usr/bin/env python3
"""Replace only cumulativeFrame's print handler with isolated print document."""
from pathlib import Path
import re, base64
p=Path('www/index.html')
s=p.read_text(encoding='utf-8')
pat=r'(cumulativeFrame:")([A-Za-z0-9+/=]+)(")'
m=re.search(pat,s)
if not m: raise SystemExit('STOP: cumulativeFrame missing')
h=base64.b64decode(m.group(2)).decode('utf-8')
if not all(f'id="p{i}"' in h for i in range(1,12)): raise SystemExit('STOP: 11 pages missing')
start=h.find('function gyCumNativePrint(all){')
end=h.find('\nfunction printCurrent()',start)
if start<0 or end<0 or h.count('function gyCumNativePrint(all){')!=1: raise SystemExit('STOP: original print function not unique')
replacement=r'''function gyCumNativePrint(all){
  try { if(typeof save==='function') save(); } catch(e) {}
  const pages = Array.from(document.querySelectorAll('main .page'));
  const active = document.querySelector('main .page.active') || pages[0];
  const chosen = all ? pages : [active];
  if (!chosen.length) { alert('प्रिंटसाठी पाने सापडली नाहीत'); return; }
  // An isolated print document avoids viewer-mode CSS hiding the pages.
  const popup = window.open('', '_blank');
  if (!popup) { alert('प्रिंट विंडो उघडण्यासाठी Chrome मधील Pop-ups परवानगी द्या.'); return; }
  const css = Array.from(document.querySelectorAll('style')).map(x=>x.textContent).join('\n');
  const sheets = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(x=>x.outerHTML).join('\n');
  const htmlPages = chosen.map(p=>{
    const c=p.cloneNode(true);
    c.classList.add('active','printing');
    c.querySelectorAll('script,.rowtools,.help,.source').forEach(x=>x.remove());
    // Form controls must be converted to their current values.
    const originals=p.querySelectorAll('input,textarea,select');
    const clones=c.querySelectorAll('input,textarea,select');
    originals.forEach((o,i)=>{
      const t=clones[i]; if(!t)return;
      if(o.tagName==='SELECT') { const span=document.createElement('span');span.textContent=o.selectedOptions[0]?.textContent||'';t.replaceWith(span); }
      else if(o.tagName==='TEXTAREA'){const span=document.createElement('span');span.textContent=o.value;t.replaceWith(span);}
      else if(o.type==='checkbox'||o.type==='radio'){t.checked=o.checked;}
      else {t.setAttribute('value',o.value);}
    });
    return c.outerHTML;
  }).join('\n');
  popup.document.open();
  popup.document.write('<!doctype html><html lang="mr"><head><meta charset="utf-8"><base href="'+document.baseURI.replace(/"/g,'&quot;')+'">'+sheets+'<style>'+css+'</style><style id="gy-cum-isolated-print">'+
  '@page{size:A4 portrait;margin:7mm}html,body{height:auto!important;overflow:visible!important;background:#fff!important;margin:0!important;padding:0!important}'+
  'body>main{display:block!important;position:static!important;overflow:visible!important;height:auto!important;max-width:none!important;width:100%!important;padding:0!important;margin:0!important}'+
  'body main .page,body main .page.active,body main .page.printing,body main .page:not(.active){display:block!important;visibility:visible!important;position:relative!important;opacity:1!important;transform:none!important;overflow:visible!important;max-width:100%!important;width:100%!important;height:auto!important;min-height:0!important;box-shadow:none!important;margin:0!important;padding:0!important;break-after:page!important;page-break-after:always!important}'+
  'body main .page:last-child{break-after:auto!important;page-break-after:auto!important}'+
  '.rowtools,.help,.source,.tabs,header,#gyCumViewerNav,#gyCumDash{display:none!important}'+
  'table{max-width:100%!important}img{max-width:100%}'+
  '</style></head><body><main>'+htmlPages+'</main></body></html>');
  popup.document.close();
  const run=()=>{try{popup.focus();popup.print();}catch(e){alert('प्रिंट उघडली नाही: '+e.message);}};
  const images=Array.from(popup.document.images);
  Promise.all(images.map(im=>im.complete?Promise.resolve():new Promise(resolve=>{im.onload=resolve;im.onerror=resolve;setTimeout(resolve,3000)}))).then(()=>setTimeout(run,400));
}
'''
h=h[:start]+replacement+h[end:]
enc=base64.b64encode(h.encode()).decode()
s2=s[:m.start(2)]+enc+s[m.end(2):]
p.write_text(s2,encoding='utf-8')
print('OK: cumulative 11-page isolated print v2 installed; other modules unchanged')
