from pathlib import Path
import base64, html, re, json
p=Path('www/index.html'); g=Path('dnyanada_login_gate.js'); c=Path('dnyanada_cloud_backup.js')
s=p.read_text(); gate=g.read_text(); cloud=c.read_text()
def replace(s,a,b):
    if s.count(a)!=1: raise SystemExit('STOP: unexpected source: '+a[:90])
    return s.replace(a,b,1)
s=replace(s,gate,'')
s=replace(s,'<script src="/dnyanada_cloud_backup.js"></script>','')
# The application runs in a fresh document only after account approval.
boot='''<script>(function(){
const host=top.__dnAccount;
if(!host)throw Error('Account not approved');
const store=host.store;
Object.defineProperty(window,'localStorage',{get:()=>store,configurable:false});
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
p.write_text(output);c.write_text(cloud)
print('Account isolation candidate built; browser testing required')
