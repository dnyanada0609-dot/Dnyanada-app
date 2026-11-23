from pathlib import Path
import re,base64
p=Path('www/index.html')
s=p.read_text(encoding='utf-8')
match=re.search(r'(cceFrame:")([A-Za-z0-9+/=]+)(")',s)
if not match: raise SystemExit('CCE module not found; stopped safely')
html=base64.b64decode(match.group(2)).decode('utf-8')
anchor='let chosenDescriptiveNotes = {};'
if html.count(anchor)!=1: raise SystemExit('CCE descriptive module changed; stopped safely')
guard=r"""
// DNYANADA: descriptive notes are partitioned by authenticated teacher and student identity.
// Old unscoped data remains untouched for supervised recovery.
let dnyTeacherUid='';
const dnyLegacyNotesKey='gyanadaCCEDescriptiveNotes';
function dnyNotesStorageKey(){
 if(!dnyTeacherUid)return null;
 return 'dny_notes_v2_'+dnyTeacherUid;
}
function dnyStudentIdentity(roll){
 const st=roster[Number(roll)-1];
 if(!st||!String(st.name||'').trim())return '';
 const grade=String(document.getElementById('setupClass')?.value||'');
 const year=String(document.getElementById('setupYear')?.value||'');
 return encodeURIComponent(JSON.stringify([grade,year,Number(roll),String(st.name).trim().toLowerCase()]));
}
function dnyNotesRecordKey(roll,term){
 const id=dnyStudentIdentity(roll);
 return id?id+'_'+String(term):'';
}
function dnyNotesAccessReady(){
 if(dnyTeacherUid)return true;
 const st=document.getElementById('notesStatus');
 if(st)st.textContent='शिक्षक खाते पडताळणी सुरू आहे; नोंदी अजून सेव्ह करू नका.';
 return false;
}
window.addEventListener('message',e=>{
 if(e.source!==parent||e.data?.type!=='DNY_AUTH_CONTEXT')return;
 const uid=String(e.data.uid||'');
 if(!/^[a-zA-Z0-9_-]{6,128}$/.test(uid))return;
 if(dnyTeacherUid!==uid){
  dnyTeacherUid=uid;
  chosenDescriptiveNotes={};
  try{loadChosenNotes();renderChosenNotes();syncProgressNoteFields()}catch(_){}
 }
});
try{parent.postMessage({type:'DNY_AUTH_CONTEXT_REQUEST'},'*')}catch(_){}
"""
html=html.replace(anchor,guard+'\n'+anchor)
html=html.replace("return roll?`${roll}_${term}`:'';","return roll?dnyNotesRecordKey(roll,term):'';")
# Replace the two direct storage reads and two writes in the chosen notes implementation only
start=html.index('function loadChosenNotes(){')
end=html.index('function updateNotesHeader(){',start)
html=html[:start]+"""function loadChosenNotes(){
 chosenDescriptiveNotes={};
 const storageKey=dnyNotesStorageKey();if(!storageKey)return;
 try{const value=JSON.parse(localStorage.getItem(storageKey)||'{}');
  if(value&&typeof value==='object'&&!Array.isArray(value))chosenDescriptiveNotes=value;
 }catch(e){chosenDescriptiveNotes={}}
}
"""+html[end:]
start=html.index('function saveChosenNotes(silent=false)')
end=html.index('function notesForProgress(roll,term)',start)
html=html[:start]+"""function saveChosenNotes(silent=false){
 const storageKey=dnyNotesStorageKey();if(!storageKey){dnyNotesAccessReady();return false}
 try{
  localStorage.setItem(storageKey,JSON.stringify(chosenDescriptiveNotes));
  try{syncProgressNoteFields()}catch(e){}
  const st=document.getElementById('notesStatus');
  if(st)st.textContent='नोंदी शिक्षक व विद्यार्थीनिहाय सुरक्षित सेव्ह झाल्या.';
  return true;
 }catch(e){if(!silent)alert('नोंदी सेव्ह झाल्या नाहीत: '+e.message);return false}
}
"""+html[end:]
# Update progress reader, removing fallback to stale legacy keys
start=html.index('function notesForProgress(roll,term)')
end=html.index('loadRoster();loadWorkdays();buildRows();',start)
part=html[start:end]
part=part.replace("let all={};try{all=JSON.parse(localStorage.getItem('gyanadaCCEDescriptiveNotes')||'{}')}catch(e){}",
                  "let all={};try{const k=dnyNotesStorageKey();if(k)all=JSON.parse(localStorage.getItem(k)||'{}')}catch(e){}")
part=part.replace("const list=all[`${roll}_${t}`]||all[String(roll)+(t===2?'_2':'')]||[];",
                  "const list=all[dnyNotesRecordKey(roll,t)]||[];")
html=html[:start]+part+html[end:]
# Guard writes before user auth and ensure only valid selected student
html=html.replace("if(!chosenDescriptiveNotes[key])chosenDescriptiveNotes[key]=[];",
                  "if(!dnyNotesAccessReady()||!key)return;if(!chosenDescriptiveNotes[key])chosenDescriptiveNotes[key]=[];")
encoded=base64.b64encode(html.encode('utf-8')).decode('ascii')
s=s[:match.start(2)]+encoded+s[match.end(2):]
# Parent sends authenticated UID on CCE frame load and request, never on unverified login
inject=r"""
<script id="dny-auth-context-relay">
(function(){
 function deliver(){
  try{
   const a=window.firebase?.app('dnyanada-login-gate')?.auth();
   const uid=a?.currentUser?.uid;
   const frame=document.getElementById('cceFrame');
   if(uid&&frame?.contentWindow)frame.contentWindow.postMessage({type:'DNY_AUTH_CONTEXT',uid},'*');
  }catch(e){}
 }
 window.addEventListener('message',function(e){
  if(e.data?.type==='DNY_AUTH_CONTEXT_REQUEST'&&e.source===document.getElementById('cceFrame')?.contentWindow)deliver();
 });
 document.addEventListener('DOMContentLoaded',()=>{
  const f=document.getElementById('cceFrame');
  if(f)f.addEventListener('load',()=>setTimeout(deliver,150));
 });
})();
</script>
"""
pos=s.lower().rfind('</body>')
if pos<0:raise SystemExit('Missing body')
s=s[:pos]+inject+s[pos:]
p.write_text(s,encoding='utf-8')
print('CCE descriptive account isolation installed; legacy data retained.')
