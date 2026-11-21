;(function(){
'use strict';
if(window.__dnySafeRestoreInstalled)return;
window.__dnySafeRestoreInstalled=true;
const LIMIT=20*1024*1024;
async function safeRestore(){
 const app=firebase.app('dnyanada-login-gate');
 const user=app.auth().currentUser;
 if(!user)throw Error('प्रथम शिक्षक लॉगिन करा.');
 const root=app.firestore().collection('app_backups').doc(user.uid);
 const snap=await root.get();
 if(!snap.exists)throw Error('क्लाउड बॅकअप सापडला नाही.');
 const meta=snap.data();
 const version=meta.latestVersion,count=meta.chunkCount;
 if(typeof version!=='string'||!/^b[a-z0-9]+$/.test(version)||
 !Number.isInteger(count)||count<1||count>1000)
 throw Error('बॅकअप माहिती अवैध आहे.');
 let raw='';
 for(let i=0;i<count;i++){
  const doc=await root.collection('chunks')
   .doc(version+'_'+String(i).padStart(5,'0')).get();
  if(!doc.exists)throw Error('बॅकअप अपूर्ण आहे.');
  const part=doc.data();
  if(part.version!==version||part.index!==i||
     typeof part.payload!=='string')
   throw Error('बॅकअपचा भाग अवैध आहे.');
  raw+=part.payload;
  if(raw.length>LIMIT)throw Error('बॅकअप आकार मर्यादेपेक्षा मोठा आहे.');
 }
 const parsed=JSON.parse(raw);
 if(parsed.schema!==1||!parsed.data||
    Object.getPrototypeOf(parsed.data)!==Object.prototype)
 throw Error('बॅकअप स्वरूप अवैध आहे.');
 const entries=Object.entries(parsed.data);
 for(const [key,value] of entries){
  if(typeof value!=='string'||!key||
   /^(firebase:|firebase_|__firebase|dnyanada_cloud_)/i.test(key))
   throw Error('बॅकअपमधील नोंद अवैध आहे.');
 }
 const before={};
 for(let i=0;i<localStorage.length;i++){
  const key=localStorage.key(i);
  before[key]=localStorage.getItem(key);
 }
 const snapshot=JSON.stringify(before);
 if(new Blob([snapshot]).size>LIMIT)
 throw Error('स्थानिक डेटाची सुरक्षित प्रत तयार करता येत नाही.');
 if(!confirm('क्लाउडमधील '+entries.length+
 ' नोंदी आणायच्या? समान नावाच्या स्थानिक नोंदी बदलतील.'))return;
 const changed=[];
 try{
  for(const [key,value] of entries){
   changed.push(key);
   localStorage.setItem(key,value);
  }
 }catch(err){
  let rollbackError=null;
  for(const key of changed){
   try{
    if(Object.prototype.hasOwnProperty.call(before,key))
     localStorage.setItem(key,before[key]);
    else localStorage.removeItem(key);
   }catch(e){rollbackError=e;}
  }
  if(rollbackError)throw Error(
   'Restore अयशस्वी; काही स्थानिक नोंदी पूर्ववत करता आल्या नाहीत.');
  throw Error('Restore अयशस्वी; स्थानिक नोंदी पूर्ववत केल्या.');
 }
 alert('Restore पूर्ण. '+entries.length+
 ' नोंदी आणल्या. बदल दिसण्यासाठी अ‍ॅप पुन्हा उघडा.');
}
document.addEventListener('click',async function(e){
 const button=e.target.closest&&e.target.closest(
  '#dny-cloud-tools button[data-action="restore"]');
 if(!button)return;
 e.preventDefault();
 e.stopImmediatePropagation();
 const panel=document.getElementById('dny-cloud-tools');
 const buttons=panel.querySelectorAll('button');
 buttons.forEach(b=>b.disabled=true);
 try{await safeRestore();}
 catch(err){alert('सुरक्षित Restore: '+err.message);}
 finally{buttons.forEach(b=>b.disabled=false);}
},true);
})();
