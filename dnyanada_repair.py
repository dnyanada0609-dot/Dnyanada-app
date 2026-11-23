from pathlib import Path
p=Path("www/index.html")
s=p.read_text(encoding="utf-8")
old="""if(id==='cceFrame'){loadApp('classFrame');setTimeout(()=>{try{document.getElementById('classFrame').contentWindow.postMessage({type:'GYANADA_REQUEST_STUDENT_DATA'},'*')}catch(e){}},400)}"""
new="""if(id==='cceFrame'){
  loadApp('classFrame');
  const cf=document.getElementById('classFrame'),cc=document.getElementById('cceFrame');
  const request=()=>{try{cf.contentWindow.postMessage({type:'GYANADA_REQUEST_STUDENT_DATA'},'*')}catch(e){}};
  const deliver=()=>{try{if(gyanadaLatestStudentMessage)cc.contentWindow.postMessage(gyanadaLatestStudentMessage,'*');else request()}catch(e){}};
  if(cf.dataset.loaded==='1')request();
  cf.addEventListener('load',request,{once:true});
  cc.addEventListener('load',deliver,{once:true});
  setTimeout(request,350);setTimeout(deliver,900);
}"""
if s.count(old)!=1:
    raise SystemExit("CCE navigation anchor changed; no modification applied.")
s=s.replace(old,new)
# The student relay must only accept messages from the real student master frame.
old2="""if(!m||m.type!=='GYANADA_STUDENT_DATA')return;gyanadaLatestStudentMessage=m;gyanadaForwardStudentData(m)"""
new2="""if(!m||m.type!=='GYANADA_STUDENT_DATA'||ev.source!==document.getElementById('classFrame').contentWindow)return;gyanadaLatestStudentMessage=m;gyanadaForwardStudentData(m)"""
if s.count(old2)!=1:
    raise SystemExit("Student relay anchor changed; no modification applied.")
s=s.replace(old2,new2)
# Preserve the existing print architecture; add a reload-safe request on CCE iframe load.
anchor="""let gyanadaLatestTeacherProfile=null;"""
extra="""document.getElementById('cceFrame').addEventListener('load',function(){
  const cf=document.getElementById('classFrame');
  try{cf.contentWindow.postMessage({type:'GYANADA_REQUEST_STUDENT_DATA'},'*')}catch(e){}
  setTimeout(()=>{try{if(gyanadaLatestStudentMessage)this.contentWindow.postMessage(gyanadaLatestStudentMessage,'*')}catch(e){}},250);
});
"""
if s.count(anchor)!=1: raise SystemExit("Teacher relay anchor changed; no modification applied.")
s=s.replace(anchor,extra+anchor)
p.write_text(s,encoding="utf-8")
print("CCE navigation and student relay repaired; other modules untouched.")
