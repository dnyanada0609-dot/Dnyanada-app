;(function(){
'use strict';
if(window.__dnyanadaCloudBackupInstalled)return;
window.__dnyanadaCloudBackupInstalled=true;
const MAX_BYTES=20*1024*1024, CHUNK_CHARS=80000;
function getDb(){
  const app = firebase.app('dnyanada-login-gate');
  const auth = app.auth();
  const u = auth.currentUser;
  if (!u) throw Error('प्रथम शिक्षक लॉगिन करा.');
  return {db: app.firestore(), uid: u.uid};
}
function collect(){
 const data={};
 for(let i=0;i<localStorage.length;i++){
  const k=localStorage.key(i);
  if(!k || /^(firebase:|firebase_|__firebase|dnyanada_cloud_)/i.test(k))continue;
  data[k]=localStorage.getItem(k);
 }
 const serialized=JSON.stringify({schema:1,createdAt:new Date().toISOString(),data});
 if(new Blob([serialized]).size>MAX_BYTES)throw Error('डेटा 20 MB पेक्षा मोठा आहे.');
 return serialized;
}
async function backup(silent=false){
 const {db,uid}=getDb();
 const str=collect(),chunks=[];
 for(let i=0;i<str.length;i+=CHUNK_CHARS)chunks.push(str.slice(i,i+CHUNK_CHARS));
 const id='b'+Date.now().toString(36);
 const root=db.collection('app_backups').doc(uid);
 for(let i=0;i<chunks.length;i++){
  await root.collection('chunks').doc(id+'_'+String(i).padStart(5,'0')).set({payload:chunks[i],version:id,index:i});
 }
 await root.set({latestVersion:id,chunkCount:chunks.length,updatedAt:firebase.firestore.FieldValue.serverTimestamp(),schema:1});
 if(!silent)alert('क्लाउड बॅकअप पूर्ण. '+Object.keys(JSON.parse(str).data).length+' स्थानिक नोंदी जतन झाल्या.');
}
async function restore(){
 const {db,uid}=getDb(),root=db.collection('app_backups').doc(uid);
 const meta=await root.get();
 if(!meta.exists)throw Error('या खात्यासाठी क्लाउड बॅकअप सापडला नाही.');
 const {latestVersion,chunkCount}=meta.data();
 if(!latestVersion||!Number.isInteger(chunkCount)||chunkCount<1||chunkCount>1000)throw Error('बॅकअप माहिती अवैध आहे.');
 let str='';
 for(let i=0;i<chunkCount;i++){
  const d=await root.collection('chunks').doc(latestVersion+'_'+String(i).padStart(5,'0')).get();
  if(!d.exists||typeof d.data().payload!=='string')throw Error('बॅकअप अपूर्ण आहे; स्थानिक डेटा बदललेला नाही.');
  str+=d.data().payload;
 }
 const parsed=JSON.parse(str);
 if(parsed.schema!==1||!parsed.data||typeof parsed.data!=='object'||Array.isArray(parsed.data))throw Error('बॅकअप स्वरूप अवैध आहे.');
 const keys=Object.keys(parsed.data);
 if(!confirm('क्लाउडमधील '+keys.length+' नोंदी या मोबाईलवर आणायच्या? एकाच नावाच्या स्थानिक नोंदी बदलतील. आधी स्थानिक बॅकअप घ्या.'))return;
 for(const k of keys){if(typeof parsed.data[k]!=='string')throw Error('अवैध नोंद: '+k);}
 for(const k of keys)localStorage.setItem(k,parsed.data[k]);
 alert('डेटा पुनर्संचयित झाला. बदल दिसण्यासाठी अ‍ॅप पुन्हा उघडा.');
}
const CHECK_MS=15000, QUIET_MS=20000;
let baseline=null,pendingSince=0,busy=false,lastUid=null,lastUploaded=null,autoStatus=null;
function snapshot(){
 const data={};
 for(let i=0;i<localStorage.length;i++){
  const k=localStorage.key(i);
  if(k&&!/^(firebase:|firebase_|__firebase|dnyanada_cloud_)/i.test(k))data[k]=localStorage.getItem(k);
 }
 return JSON.stringify(data);
}
async function autoCheck(){
 if(busy||!navigator.onLine||typeof firebase==='undefined')return;
 let uid;
 try{uid=getDb().uid;}catch(_){return;}
 if(uid!==lastUid){lastUid=uid;baseline=snapshot();pendingSince=0;lastUploaded=null;return;}
 const current=snapshot();
 if(baseline===null){baseline=current;return;}
 if(current===baseline){pendingSince=0;return;}
 if(!pendingSince){pendingSince=Date.now();return;}
 if(Date.now()-pendingSince<QUIET_MS)return;
 if(current===lastUploaded){baseline=current;pendingSince=0;return;}
 busy=true;
 try{
  if(autoStatus)autoStatus.textContent='☁ आपोआप बॅकअप सुरू...';
  await backup(true);
  lastUploaded=current;baseline=current;pendingSince=0;
  if(autoStatus)autoStatus.textContent='☁ बॅकअप सुरक्षित झाला';
 }catch(err){
  pendingSince=Date.now();
  if(autoStatus)autoStatus.textContent='☁ बॅकअप प्रलंबित';
  console.warn('DNYANADA automatic backup:',err);
 }finally{busy=false;}
}
function startAutoBackup(){
 if(window.__dnyanadaAutoBackupStarted)return;
 window.__dnyanadaAutoBackupStarted=true;
 setInterval(autoCheck,CHECK_MS);
 window.addEventListener('online',autoCheck);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)autoCheck();});
 autoCheck();
}
function addUI(){
 if(document.getElementById('dny-cloud-tools'))return;
 const panel=document.createElement('div');
 panel.id='dny-cloud-tools';
 panel.style.cssText='position:fixed;bottom:10px;right:10px;z-index:2147483000;background:white;border:2px solid #135a8a;border-radius:10px;padding:8px;font:13px sans-serif;box-shadow:0 3px 12px #0003';
 panel.innerHTML='<div style="font-weight:bold;margin-bottom:6px">☁ क्लाउड बॅकअप (चाचणी)</div><button type="button" data-action="backup">बॅकअप घ्या</button> <button type="button" data-action="restore">डेटा परत आणा</button><div id="dny-cloud-status" style="font-size:11px;margin-top:4px"></div>';
 panel.addEventListener('click',async e=>{
  const a=e.target.dataset.action;if(!a)return;
  const status=panel.querySelector('#dny-cloud-status');status.textContent='कृपया थांबा...';
  panel.querySelectorAll('button').forEach(b=>b.disabled=true);
  try{await (a==='backup'?backup():restore());status.textContent='पूर्ण';baseline=snapshot();pendingSince=0;if(a==='backup')lastUploaded=baseline;}
  catch(err){status.textContent='त्रुटी';alert('क्लाउड: '+err.message);}
  finally{panel.querySelectorAll('button').forEach(b=>b.disabled=false);}
 });
 document.body.appendChild(panel);
 autoStatus=panel.querySelector('#dny-cloud-status');
 startAutoBackup();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',addUI);else addUI();
})();
