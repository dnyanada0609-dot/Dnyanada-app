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
    return m[1]+m[2]+html.escape(inject(html.unescape(m[3])),quote=True)+m[2]
s=re.sub(r'(<iframe\b[^>]*?\bsrcdoc\s*=\s*)([\"\'])(.*?)\2',static,s,flags=re.I|re.S)
s=inject(s)
encoded=base64.b64encode(s.encode()).decode()
# Keep Firebase storage in the shell untouched. Expose only a UID-scoped facade to app code.
controller=r'''<script>
(function(){
const raw=window.localStorage; let account=null, frame=null;
const boot=BOOT;
function inject(s){if(s.includes('const host=top.__dnAccount;'))return s;const m=/<head\b[^>]*>/i.exec(s);return m?s.slice(0,m.index+m[0].length)+boot+s.slice(m.index+m[0].length):boot+s;}
function close(){if(frame){frame.remove();frame=null;}account=null;}
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
p.write_text(output);c.write_text(cloud)
print('Account isolation candidate built; browser testing required')
