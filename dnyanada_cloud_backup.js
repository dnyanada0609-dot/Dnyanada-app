
;(function(){
'use strict';
if(window.__dnyanadaCloudBackupInstalled)return;
window.__dnyanadaCloudBackupInstalled=true;

const MAX_BYTES=20*1024*1024;
const CHUNK_CHARS=80000;
const CHECK_MS=15000;
const QUIET_MS=20000;
const EXCLUDE=/^(firebase:|firebase_|__firebase|dnyanada_cloud_)/i;

let baseline=null;
let pendingSince=0;
let busy=false;
let lastUid=null;
let autoStatus=null;

function context(){
 if(typeof firebase==='undefined')
  throw Error('Firebase उपलब्ध नाही.');
 const app=firebase.app('dnyanada-login-gate');
 const user=app.auth().currentUser;
 if(!user)throw Error('प्रथम शिक्षक लॉगिन करा.');
 return {db:app.firestore(),uid:user.uid};
}

function dataObject(){
 const data={};
 for(let i=0;i<localStorage.length;i++){
  const k=localStorage.key(i);
  if(k&&!EXCLUDE.test(k))
   data[k]=localStorage.getItem(k);
 }
 return data;
}

function snapshot(){
 return JSON.stringify(dataObject());
}

function marker(uid){
 return 'dnyanada_cloud_backup_marker_'+uid;
}

function versionMarker(uid){
 return 'dnyanada_cloud_backup_version_'+uid;
}

function status(message){
 if(autoStatus)autoStatus.textContent=message;
}

function makePayload(){
 const data=dataObject();
 const serialized=JSON.stringify({
  schema:1,
  createdAt:new Date().toISOString(),
  data
 });
 if(new Blob([serialized]).size>MAX_BYTES)
  throw Error('डेटा 20 MB पेक्षा मोठा आहे.');
 return {
  serialized,
  count:Object.keys(data).length,
  snap:JSON.stringify(data)
 };
}

async function backup(silent=false){
 const {db,uid}=context();
 const root=db.collection('app_backups').doc(uid);
 const {serialized,count,snap}=makePayload();

 if(silent){
  const known=localStorage.getItem(versionMarker(uid));
  if(!known)
   throw Error('प्रथम एकदा स्वतः बॅकअप घ्या.');

  const remote=await root.get();
  if(!remote.exists||
     remote.data().latestVersion!==known)
   throw Error('क्लाऊडवर दुसरी आवृत्ती आहे. आपोआप बॅकअप थांबवला.');
 }

 const chunks=[];
 for(let i=0;i<serialized.length;i+=CHUNK_CHARS)
  chunks.push(serialized.slice(i,i+CHUNK_CHARS));

 if(!chunks.length)chunks.push(serialized);

 const id='b'+Date.now().toString(36)+'_'+
  Math.random().toString(36).slice(2,7);

 for(let i=0;i<chunks.length;i++){
  await root.collection('chunks')
   .doc(id+'_'+String(i).padStart(5,'0'))
   .set({
    payload:chunks[i],
    version:id,
    index:i
   });
 }

 await root.set({
  latestVersion:id,
  chunkCount:chunks.length,
  updatedAt:firebase.firestore.FieldValue.serverTimestamp(),
  schema:1
 });

 const verify=await root.get();
 if(!verify.exists||
    verify.data().latestVersion!==id)
  throw Error('क्लाऊड पुष्टी मिळाली नाही.');

 localStorage.setItem(marker(uid),snap);
 localStorage.setItem(versionMarker(uid),id);
 baseline=snap;
 pendingSince=0;

 status('☁ बॅकअप सुरक्षित झाला');

 if(!silent)
  alert('क्लाऊड बॅकअप पूर्ण. '+
   count+' स्थानिक स्टोरेज नोंदी जतन झाल्या.');
}

async function restore(){
 const {db,uid}=context();
 const root=db.collection('app_backups').doc(uid);
 const meta=await root.get();

 if(!meta.exists)
  throw Error('या खात्यासाठी क्लाऊड बॅकअप सापडला नाही.');

 const {latestVersion,chunkCount}=meta.data();

 if(!latestVersion||
    !Number.isInteger(chunkCount)||
    chunkCount<1||
    chunkCount>1000)
  throw Error('बॅकअप माहिती अवैध आहे.');

 let str='';

 for(let i=0;i<chunkCount;i++){
  const d=await root.collection('chunks')
   .doc(latestVersion+'_'+String(i).padStart(5,'0'))
   .get();

  if(!d.exists||
     typeof d.data().payload!=='string')
   throw Error('बॅकअप अपूर्ण आहे; स्थानिक डेटा बदललेला नाही.');

  str+=d.data().payload;
 }

 const parsed=JSON.parse(str);

 if(parsed.schema!==1||
    !parsed.data||
    typeof parsed.data!=='object'||
    Array.isArray(parsed.data))
  throw Error('बॅकअप स्वरूप अवैध आहे.');

 const keys=Object.keys(parsed.data);

 for(const k of keys){
  if(typeof parsed.data[k]!=='string'||
     EXCLUDE.test(k))
   throw Error('अवैध नोंद: '+k);
 }

 if(!confirm(
  'क्लाऊडमधील '+keys.length+
  ' स्थानिक स्टोरेज नोंदी आणायच्या? समान नावाच्या स्थानिक नोंदी बदलतील. आधी स्वतंत्र बॅकअप घ्या.'
 ))return;

 for(const k of keys)
  localStorage.setItem(k,parsed.data[k]);

 localStorage.setItem(marker(uid),snapshot());
 localStorage.setItem(versionMarker(uid),latestVersion);

 baseline=snapshot();
 pendingSince=0;

 alert('डेटा पुनर्संचयित झाला. बदल दिसण्यासाठी ॲप पुन्हा उघडा.');
}

async function autoCheck(){
 if(busy||!navigator.onLine)return;

 let uid;
 try{
  uid=context().uid;
 }catch(_){
  return;
 }

 const current=snapshot();

 if(uid!==lastUid){
  lastUid=uid;
  const saved=localStorage.getItem(marker(uid));

  baseline=saved===null?current:saved;
  pendingSince=0;

  if(saved===null)
   status('☁ प्रथम एकदा बॅकअप घ्या');
  else if(current===saved)
   status('☁ मागील बॅकअप जतन आहे');
  else
   status('☁ बदल आढळले; बॅकअप प्रलंबित');

  return;
 }

 if(current===baseline){
  pendingSince=0;
  return;
 }

 if(!localStorage.getItem(versionMarker(uid))){
  status('☁ प्रथम एकदा बॅकअप घ्या');
  return;
 }

 if(!pendingSince){
  pendingSince=Date.now();
  status('☁ बदल आढळले; बॅकअप प्रलंबित');
  return;
 }

 if(Date.now()-pendingSince<QUIET_MS)return;

 busy=true;

 try{
  status('☁ आपोआप बॅकअप सुरू...');
  await backup(true);
 }catch(err){
  pendingSince=Date.now();
  status('☁ बॅकअप प्रलंबित: '+err.message);
  console.warn('DNYANADA automatic backup:',err);
 }finally{
  busy=false;
 }
}

function addUI(){
 if(document.getElementById('dny-cloud-tools'))return;

 const panel=document.createElement('div');
 panel.id='dny-cloud-tools';
 panel.style.cssText=
  'position:fixed;left:50%;'+
  'bottom:calc(8px + env(safe-area-inset-bottom, 0px));'+
  'transform:translateX(-50%);'+
  'z-index:2147483000;'+
  'font:13px system-ui,sans-serif;'+
  'max-width:calc(100vw - 20px);';

 const trigger=document.createElement('button');
 trigger.type='button';
 trigger.textContent='☁ क्लाऊड बॅकअप';
 trigger.setAttribute(
  'aria-label','क्लाऊड बॅकअप पर्याय उघडा'
 );
 trigger.setAttribute('aria-expanded','false');

 trigger.style.cssText=
  'display:block;margin:auto;'+
  'background:#125b92;color:white;'+
  'border:2px solid white;'+
  'border-radius:999px;padding:9px 18px;'+
  'font:700 14px system-ui,sans-serif;'+
  'box-shadow:0 3px 12px #0005;'+
  'white-space:nowrap;cursor:pointer;';

 const popup=document.createElement('div');
 popup.hidden=true;
 popup.style.cssText=
  'position:absolute;bottom:calc(100% + 9px);'+
  'left:50%;transform:translateX(-50%);'+
  'width:270px;max-width:calc(100vw - 24px);'+
  'background:white;color:#173e68;'+
  'border:2px solid #125b92;'+
  'border-radius:12px;padding:12px;'+
  'box-shadow:0 5px 22px #0004;'+
  'text-align:center;';

 popup.innerHTML=
  '<div style="font-weight:800;margin-bottom:8px">'+
  '☁ क्लाऊड बॅकअप</div>'+
  '<button type="button" data-action="backup">'+
  'बॅकअप घ्या</button> '+
  '<button type="button" data-action="restore">'+
  'डेटा परत आणा</button>'+
  '<div id="dny-cloud-status" role="status" '+
  'style="font-size:12px;line-height:1.4;'+
  'margin-top:9px;overflow-wrap:anywhere">'+
  'स्थिती तपासत आहे...</div>';

 popup.querySelectorAll('button').forEach(btn=>{
  btn.style.cssText=
   'background:#e5f2ff;color:#124879;'+
   'border:1px solid #9cc6e9;'+
   'border-radius:8px;padding:8px 7px;'+
   'font-weight:700;cursor:pointer;';
 });

 autoStatus=popup.querySelector('#dny-cloud-status');

 trigger.addEventListener('click',()=>{
  popup.hidden=!popup.hidden;
  trigger.setAttribute(
   'aria-expanded',String(!popup.hidden)
  );
 });

 popup.addEventListener('click',async e=>{
  const action=e.target.dataset.action;
  if(!action)return;
  if(busy)return;

  status('कृपया थांबा...');
  popup.querySelectorAll('button')
   .forEach(btn=>btn.disabled=true);
  busy=true;

  try{
   if(action==='backup')
    await backup();
   else
    await restore();
  }catch(err){
   status('☁ त्रुटी: '+err.message);
   alert('क्लाऊड: '+err.message);
  }finally{
   busy=false;
   popup.querySelectorAll('button')
    .forEach(btn=>btn.disabled=false);
  }
 });

 panel.appendChild(popup);
 panel.appendChild(trigger);
 document.body.appendChild(panel);

 setInterval(autoCheck,CHECK_MS);
 window.addEventListener('online',autoCheck);
 document.addEventListener('visibilitychange',()=>{
  if(!document.hidden)autoCheck();
 });

 autoCheck();
}

if(document.readyState==='loading')
 document.addEventListener('DOMContentLoaded',addUI);
else
 addUI();

})();
     
