from pathlib import Path
import base64, html, re, json
p=Path('www/index.html'); g=Path('dnyanada_login_gate.js'); c=Path('dnyanada_cloud_backup.js')
s=p.read_text(); gate=g.read_text(); cloud=c.read_text()
def replace(s,a,b):
    if s.count(a)!=1: raise SystemExit('STOP: unexpected source: '+a[:90])
    return s.replace(a,b,1)
# Only modify the embedded lesson module; keep all other modules and cloud logic unchanged.
def view_only_books(source):
    pattern = r'(\blessonFrame:\s*")([A-Za-z0-9+/=]+)(")'
    matches=list(re.finditer(pattern,source))
    if len(matches)!=1: raise SystemExit('STOP: lesson module missing or duplicated')
    m=matches[0]
    lesson=base64.b64decode(m[2],validate=True).decode('utf-8')
    section_pattern=r'<section id="lessonsTab" class="tabpage hide">.*?</section>'
    sections=list(re.finditer(section_pattern,lesson,flags=re.S))
    if len(sections)!=1 or 'id="bookFiles"' not in sections[0][0]:
        raise SystemExit('STOP: unexpected book library layout')
    new_section='''<section id="lessonsTab" class="tabpage hide"><div class="panel"><h2>📚 माझी पाठ्यपुस्तके</h2><p class="hint">इयत्ता पहिली ते आठवीची पाठ्यपुस्तके अधिकृत ई-बालभारती संकेतस्थळावर पाहता येतील. खालील बटण दाबून तेथे इयत्ता, माध्यम आणि विषय निवडा.</p><div class="toolbar"><a class="btn" href="https://ebooks.ebalbharati.in/ebook.aspx" target="_blank" rel="noopener noreferrer">📖 ई-बालभारती पाठ्यपुस्तके पाहा</a></div><p class="hint">पुस्तक पाहण्यासाठी इंटरनेट आवश्यक आहे. या ॲपमध्ये पुस्तक अपलोड, डाउनलोड किंवा जतन करण्याची स्वतंत्र सुविधा नाही.</p></div></section>'''
    lesson=replace(lesson,sections[0][0],new_section)
    start='// पुस्तक डायरी: PDF/EPUB फाइल्स IndexedDB मध्ये साठवते'
    end="const multiKey='gyanada_multi_class_plans_v1';"
    if lesson.count(start)!=1 or lesson.count(end)!=1: raise SystemExit('STOP: unexpected book library script')
    a=lesson.index(start); b=lesson.index(end)
    if a>=b: raise SystemExit('STOP: invalid book library script boundaries')
    old=lesson[a:b]
    if 'function openBookDB()' not in old or 'function deleteBook(id)' not in old or "getElementById('bookFiles')" not in old:
        raise SystemExit('STOP: book library script not recognized')
    lesson=lesson[:a]+'// Textbooks are viewed at the official source; no local library writes or deletion.\n'+lesson[b:]
    lesson=replace(lesson,"document.getElementById('librarySubject').innerHTML=subjectOptions('मराठी');",'')
    lesson=replace(lesson,'renderOutcomeOverview();renderBookShelf();','renderOutcomeOverview();')
    for token in ('bookFiles','librarySubject','libraryGrade','renderBookShelf','openBookDB','downloadBook(','deleteBook(','storeBooks('):
        if token in lesson: raise SystemExit('STOP: obsolete book reference: '+token)
    encoded_lesson=base64.b64encode(lesson.encode('utf-8')).decode('ascii')
    return source[:m.start(2)]+encoded_lesson+source[m.end(2):]

# Replace the outdated local-only cloud warning in the student module only.
def update_student_cloud_message(source):
    pattern=r'(\bclassFrame:\s*")([A-Za-z0-9+/=]+)(")'
    matches=list(re.finditer(pattern,source))
    if len(matches)!=1: raise SystemExit('STOP: class module missing or duplicated')
    m=matches[0]
    module=base64.b64decode(m[2],validate=True).decode('utf-8')
    old='डेटा या डिव्हाइसच्या ब्राउझरमध्ये जतन झाला. खऱ्या क्लाउड जतनासाठी क्लाउड खाते/सर्व्हर जोडणे आवश्यक आहे.'
    new='माहिती या उपकरणात जतन झाली आहे. क्लाऊड बॅकअपची स्थिती मुख्य डॅशबोर्डवरील क्लाऊड बटणात तपासा.'
    module=replace(module,old,new)
    return source[:m.start(2)]+base64.b64encode(module.encode('utf-8')).decode('ascii')+source[m.end(2):]

s=update_student_cloud_message(s)
print('Student cloud notice updated; local save feedback installed in app frames')

s=view_only_books(s)
print('Lesson textbook view-only patch applied; existing stored books not deleted')

s=replace(s,gate,'')
s=replace(s,'<script src="/dnyanada_cloud_backup.js"></script>','')
# The application runs in a fresh document only after account approval.
boot=r'''<script>(function(){
const host=top.__dnAccount;
if(!host)throw Error('Account not approved');
(function(){
'use strict';
// Track only explicit local-save actions in this application document.
let pending=null, noticeTimer=0;
const base=host.store;
function record(fn,check){
 const op=pending;
 try{const result=fn();if(op){if(check&&!check())op.failed=true;else op.writes++;}return result;}
 catch(error){if(op)op.failed=true;throw error;}
}
const store=new Proxy(base,{
 get(target,key){
  if(key==='setItem')return (k,v)=>{const name=String(k),value=String(v);return record(()=>target.setItem(name,value),()=>target.getItem(name)===value);};
  return Reflect.get(target,key);
 },
 set(target,key,value){return record(()=>Reflect.set(target,key,value),()=>target.getItem(String(key))===String(value));}
});
Object.defineProperty(window,'localStorage',{get:()=>store,configurable:false});
function display(ok,message){
 if(!document.body)return;
 let el=document.getElementById('dn-save-notice-v1');
 if(!el){
  el=document.createElement('div');el.id='dn-save-notice-v1';el.setAttribute('aria-live','polite');el.setAttribute('role','status');
  el.style.cssText='position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:2147483646;max-width:calc(100% - 32px);width:max-content;box-sizing:border-box;padding:12px 16px;background:white;border:2px solid;border-radius:10px;box-shadow:0 2px 12px #0003;text-align:center;font:700 15px/1.5 system-ui,sans-serif;pointer-events:none';
  document.body.appendChild(el);
  const css=document.createElement('style');css.textContent='@media print{#dn-save-notice-v1{display:none!important}}';document.head.appendChild(css);
 }
 el.style.color=ok?'#12652f':'#b91c1c';el.style.borderColor=el.style.color;el.textContent=message;el.hidden=false;
 clearTimeout(noticeTimer);noticeTimer=setTimeout(()=>{el.hidden=true;},ok?4500:6500);
}
function isSave(el){
 if(!el)return false;
 const t=(el.textContent||el.value||'').trim()+' '+(el.getAttribute('aria-label')||'');
 const code=el.getAttribute('onclick')||'';
 if(/प्रिंट|\bPDF\b|\bJSON\b|डाउनलोड|डाऊनलोड|निर्यात|उघडा|परत आणा|क्लाऊड|क्लाउड|डिलीट|हटवा|clear|export|download|print|restore/i.test(t+' '+code))return false;
 return /(?:सेव[्ह]*|जतन|साठव)\s*(?:करा|करून|$)|\bsave\b/i.test(t)||el.id==='saveStudentBtn'||/\b(?:saveStudent|saveGR)\s*\(/.test(code);
}
function begin(){
 if(pending)return;
 const op={writes:0,failed:false,validation:false};pending=op;
 // A macrotask runs after click/submit handlers, including nested synchronous saves.
 setTimeout(()=>{
  if(pending!==op)return;pending=null;
  if(op.failed)display(false,'✗ माहिती पूर्णपणे जतन झाल्याची पुष्टी मिळाली नाही. पुन्हा तपासा.');
  else if(op.validation||!op.writes)display(false,'! माहिती जतन झाल्याची पुष्टी मिळाली नाही. आवश्यक माहिती व सूचना तपासा.');
  else display(true,'✓ माहिती या उपकरणात यशस्वीपणे जतन झाली आहे.');
 },0);
}
window.addEventListener('click',e=>{const el=e.target?.closest?.('button,input[type="submit"],input[type="button"],a,[role="button"]');if(el&&!el.disabled&&isSave(el))begin();},true);
window.addEventListener('submit',e=>{if(isSave(e.submitter))begin();},true);
window.addEventListener('invalid',()=>{if(pending)pending.validation=true;},true);
window.addEventListener('error',()=>{if(pending)pending.failed=true;});
const oldAlert=window.alert.bind(window);
window.alert=function(message){if(pending&&/कृपया|प्रथम|आधी|अडचण|त्रुटी|अयशस्वी|(?:जतन|सेव[्ह]*)[^.\n]{0,45}(?:नाही|शकली नाही|शकले नाही)|(?:निवडा|भरा)\s*\.?$/.test(String(message)))pending.validation=true;return oldAlert(message);};
})();
const db=window.indexedDB;
if(db){for(const name of ['open','deleteDatabase']){const original=db[name].bind(db);Object.defineProperty(db,name,{value:(key,...args)=>original(host.prefix+String(key),...args)});}}
const desc=Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype,'srcdoc');
Object.defineProperty(HTMLIFrameElement.prototype,'srcdoc',{...desc,set(value){desc.set.call(this,host.inject(String(value)));}});
})();</script>'''
def inject(s):
    m=re.search(r'<head\b[^>]*>',s,re.I)
    if not m: raise SystemExit('STOP: missing head')
    return s[:m.end()]+boot+s[m.end():]
def static(m):
    content=inject(html.unescape(m[3]))
    if re.search(r'id=["\']supportFrame["\']',m[1]):
        content=replace(content,'</main>','<section class="section"><h2>जुना स्थानिक डेटा</h2><button class="action secondary" onclick="top.__dnAccount.recover()">जुना स्थानिक डेटा परत मिळवा</button></section></main>')
    return m[1]+m[2]+html.escape(content,quote=True)+m[2]
s=re.sub(r'(<iframe\b[^>]*?\bsrcdoc\s*=\s*)([\"\'])(.*?)\2',static,s,flags=re.I|re.S)
s=inject(s)
encoded=base64.b64encode(s.encode()).decode()
# Keep Firebase storage in the shell untouched. Expose only a UID-scoped facade to app code.
controller=r'''<script>
(function(){
const raw=window.localStorage; let account=null, frame=null;
const boot=BOOT;
function inject(s){if(s.includes('const host=top.__dnAccount;'))return s;const m=/<head\b[^>]*>/i.exec(s);return m?s.slice(0,m.index+m[0].length)+boot+s.slice(m.index+m[0].length):boot+s;}
function close(){document.getElementById('dn-legacy-recovery')?.remove();if(frame){frame.remove();frame=null;}account=null;}
Object.defineProperty(window,'__dnAccount',{get:()=>account});
window.__dnClose=close;
window.__dnOpen=function(uid){
 if(account?.uid===uid)return;
 close();const prefix='dn_uid_v1:'+encodeURIComponent(uid)+':';
 const keys=()=>Array.from({length:raw.length},(_,i)=>raw.key(i)).filter(k=>k&&k.startsWith(prefix)).map(k=>k.slice(prefix.length));
 const valid=()=>{if(account?.uid!==uid)throw Error('Account closed');};
 const methods={getItem(k){valid();return raw.getItem(prefix+String(k));},setItem(k,v){valid();raw.setItem(prefix+String(k),String(v));},removeItem(k){valid();raw.removeItem(prefix+String(k));},key(i){valid();return keys()[i]??null;},clear(){valid();for(const k of keys())raw.removeItem(prefix+k);}};
 const store=new Proxy(methods,{get(t,k){if(k==='length'){valid();return keys().length;}if(k in t)return t[k];return typeof k==='string'?t.getItem(k)??undefined:undefined;},set(t,k,v){t.setItem(k,v);return true;},deleteProperty(t,k){t.removeItem(k);return true;},ownKeys(){valid();return keys();},getOwnPropertyDescriptor(t,k){return {configurable:true,enumerable:true,value:t.getItem(k),writable:true};}});
 account={uid,prefix,store,inject};
 const oldButton=document.getElementById('dn-legacy-recovery');if(oldButton)oldButton.remove();
 const legacyKeys=()=>Array.from({length:raw.length},(_,i)=>raw.key(i)).filter(k=>k&&!/^(firebase:|firebase_|__firebase|dnyanada_cloud_|dn_uid_v1:|dn_legacy_)/i.test(k));
 const recovery=document.createElement('button');recovery.id='dn-legacy-recovery';recovery.textContent='जुना स्थानिक डेटा परत मिळवा';recovery.style.cssText='position:fixed;bottom:65px;right:8px;z-index:2147483000;background:#fff;color:#125b92;border:1px solid #125b92;border-radius:8px;padding:8px';
 recovery.onclick=()=>{
  try{
   valid();if(document.documentElement.classList.contains('dnyanada-login-locked'))throw Error('प्रथम लॉगिन करा.');
   if(raw.getItem('dn_legacy_claim_v1'))throw Error('या ब्राउझरमधील जुना डेटा आधीच एका खात्यास जोडला आहे.');
   const old=legacyKeys();if(!old.length)throw Error('जुन्या स्थानिक नोंदी सापडल्या नाहीत.');
   if(keys().some(k=>old.includes(k)))throw Error('या खात्यात समान नोंदी आहेत. डेटा बदललेला नाही.');
   const user=firebase.app('dnyanada-login-gate').auth().currentUser;
   if(user?.uid!==uid)throw Error('खाते बदलले आहे.');
   if(!confirm('खाते: '+user.email+'\nजुन्या '+old.length+' स्टोरेज नोंदी सापडल्या. या मोबाईलवरील सर्व जुन्या नोंदी फक्त याच खात्याच्या आहेत याची खात्री असल्यासच पुढे जा. मिश्र डेटा असल्यास रद्द करा.'))return;
   if(prompt('मालकी निश्चित करण्यासाठी या खात्याचा ईमेल पुन्हा लिहा.')!==user.email)return;
   const copied=[];try{for(const k of old){valid();store.setItem(k,raw.getItem(k));copied.push(k);}raw.setItem('dn_legacy_claim_v1',uid);}catch(e){for(const k of copied)store.removeItem(k);throw e;}
   alert('जुन्या स्थानिक नोंदी कॉपी झाल्या. मूळ नोंदी हटवलेल्या नाहीत. ॲप पुन्हा उघडत आहे.');location.reload();
  }catch(e){alert(e.message);}
 };
 account.recover=()=>recovery.onclick();

 frame=document.createElement('iframe');frame.id='dn-app';frame.style.cssText='position:fixed;inset:0;width:100%;height:100%;border:0';
 const bytes=Uint8Array.from(atob(document.getElementById('dn-payload').textContent),x=>x.charCodeAt(0));
 frame.srcdoc=new TextDecoder().decode(bytes);document.body.prepend(frame);
};
})();
</script>'''.replace('BOOT',json.dumps(boot).replace('</','<\\/'))
gate=replace(gate,'approvedUid = user.uid;','window.__dnOpen(user.uid);\n    approvedUid = user.uid;')
gate=gate.replace('approvedUid = null;','approvedUid = null; window.__dnClose();')
# Avoid touching the declaration.
gate=gate.replace('let approvedUid = null; window.__dnClose();','let approvedUid = null;')
gate=replace(gate,'const ticket = ++sequence;','const ticket = ++sequence;\n    if(window.__dnAccount && window.__dnAccount.uid !== user?.uid) window.__dnClose();')
cloud=cloud.replace('localStorage','window.__dnAccount.store')
cloud=replace(cloud,"if(!user)throw Error('प्रथम शिक्षक लॉगिन करा.');","if(!user || window.__dnAccount?.uid!==user.uid || document.documentElement.classList.contains('dnyanada-login-locked'))throw Error('प्रथम शिक्षक लॉगिन करा.');")
# Do not trust legacy cloud data or overwrite its pointer.
cloud=replace(cloud,"const {serialized,count,snap}=makePayload();","const {serialized,count,snap}=makePayload();\n  const existing=await root.get();\n  if(existing.exists && existing.data().schema!==2)throw Error('जुना बॅकअप सुरक्षित ठेवला आहे. पडताळणी आवश्यक.');")
cloud=cloud.replace('schema:1','schema:2').replace('parsed.schema !== 1','parsed.schema !== 2')
cloud=replace(cloud,'const info = meta.data() || {};',"const info = meta.data() || {};\n   if(info.schema!==2)throw Error('जुना बॅकअप पडताळणीशिवाय परत आणता येणार नाही.');")
cloud=replace(cloud,'const previous = {};',"if(context().uid!==uid)throw Error('खाते बदलले आहे.');\n   const previous = Object.create(null);")
cloud=replace(cloud,'const data={};','const data=Object.create(null);')
cloud=replace(cloud,'await root.set({',"if(context().uid!==uid)throw Error('खाते बदलले आहे.');\n  await root.set({")
cloud=replace(cloud,'window.__dnAccount.store.setItem(marker(uid),snap);',"if(context().uid!==uid)throw Error('खाते बदलले आहे.');\n  window.__dnAccount.store.setItem(marker(uid),snap);")
cloud=replace(cloud,"'बदल पाहण्यासाठी ॲप पुन्हा उघडा.'","'बदल पाहण्यासाठी ॲप पुन्हा उघडत आहे.'")
cloud=replace(cloud,'keys.length + \' नोंदी पुनर्संचयित झाल्या.\\n\' +','keys.length + \' नोंदी पुनर्संचयित झाल्या.\\n\' +')
# Prevent accidental writes from stale UI after restore by reloading.
cloud=replace(cloud,"'बदल पाहण्यासाठी ॲप पुन्हा उघडत आहे.'\n  );","'बदल पाहण्यासाठी ॲप पुन्हा उघडत आहे.'\n  );\n  location.reload();")
# Gate is a separate shell, not the application document.
output='<!doctype html><html lang="mr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DNYANADA</title></head><body><script type="application/octet-stream" id="dn-payload">'+encoded+'</script>'+controller+'<script>'+gate+'</script><script src="/dnyanada_cloud_backup.js"></script></body></html>'
# Cloud diagnostics and server-confirmed reads; retain legacy backup protection.
cloud=cloud.replace('await root.get()', "await root.get({source:'server'})")
cloud=replace(cloud,".doc(chunkId)\n      .get();", ".doc(chunkId)\n      .get({source:'server'});")
cloud=replace(cloud,'const {serialized,count,snap}=makePayload();',"const {serialized,count,snap}=makePayload();\n  if(!count)throw Error('स्थानिक नोंदी रिकाम्या आहेत. बॅकअप थांबवला.');")
cloud=replace(cloud,'const keys = Object.keys(parsed.data);',"const keys = Object.keys(parsed.data);\n   if(!keys.length)throw Error('क्लाऊड बॅकअप रिकामा आहे. स्थानिक डेटा बदललेला नाही.');")
cloud=replace(cloud,'baseline = snapshot();\n  pendingSince = 0;',"baseline = snapshot();\n   for(const key of keys){if(window.__dnAccount.store.getItem(key)!==parsed.data[key])throw Error('स्थानिक पडताळणी अयशस्वी.');}\n   pendingSince = 0;")
# Keep legacy root metadata intact; publish scoped metadata separately in the same UID document.
cloud=replace(cloud,"const existing=await root.get({source:'server'});\n  if(existing.exists && existing.data().schema!==2)throw Error('जुना बॅकअप सुरक्षित ठेवला आहे. पडताळणी आवश्यक.');", "")
cloud=replace(cloud,'remote.data().latestVersion!==known','scopedMeta(remote).latestVersion!==known')
cloud=replace(cloud,'verify.data().latestVersion!==id','scopedMeta(verify).latestVersion!==id')
cloud=replace(cloud,'const info = meta.data() || {};','const info = scopedMeta(meta);')
cloud=replace(cloud,'await root.set({','await root.set({ scopedBackupV2: {')
cloud=replace(cloud,'schema:2\n });','schema:2\n } }, {merge:true});')
cloud=replace(cloud,'function context(){', "function scopedMeta(doc){ const d=doc.exists?(doc.data()||{}):{}; return d.scopedBackupV2 || (d.schema===2?d:{}); }\nfunction context(){")
# Version the external script using its final content, not a fixed release number.
import hashlib
version = hashlib.sha256(cloud.encode('utf-8')).hexdigest()[:20]
if 'जुना बॅकअप सुरक्षित ठेवला आहे. पडताळणी आवश्यक.' in cloud:
    raise SystemExit('STOP: obsolete backup guard remains')
if 'scopedBackupV2' not in cloud:
    raise SystemExit('STOP: scoped backup metadata missing')
output = replace(output, '<script src="/dnyanada_cloud_backup.js"></script>', '<script src="/dnyanada_cloud_backup.js?v='+version+'"></script>')
p.write_text(output);c.write_text(cloud)
print('Cloud script content version:', version)
print('Account isolation candidate built; browser testing required')
