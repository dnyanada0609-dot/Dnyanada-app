from pathlib import Path
import re,base64,sys
p=Path('www/index.html');s=p.read_text(encoding='utf-8')
marker='DNY_CCE_NOTES_UNIFY_20261123'
if marker in s:
 print('Notes fix already installed');sys.exit(0)
m=re.search(r'(cceFrame:")([A-Za-z0-9+/=]+)(")',s)
if not m:raise SystemExit('CCE base64 frame missing; no changes')
h=base64.b64decode(m.group(2)).decode('utf-8')
old="function hydrate(){state.draft=(saved()[key()]||[]).map(x=>({subject:cat(x.subject)||x.subject,text:x.text})).filter(x=>subjects.includes(x.subject));}"
new="""function hydrate(){
 // DNY_CCE_NOTES_UNIFY_20261123: read the teacher/student scoped record.
 let entries=[];
 try{const sk=dnyNotesStorageKey(),rk=dnyNotesRecordKey(state.roll,state.term);
  if(sk&&rk){const db=JSON.parse(localStorage.getItem(sk)||'{}');entries=db[rk]||[];}
 }catch(e){console.warn('Scoped notes read',e)}
 state.draft=(Array.isArray(entries)?entries:[]).map(x=>({subject:cat(x.subject)||x.subject,text:x.text})).filter(x=>subjects.includes(x.subject));
}"""
old2="function store(){let data=saved();data[key()]=state.draft.map(x=>({subject:x.subject,text:x.text}));localStorage.setItem('gyanadaCCEDescriptiveNotes',JSON.stringify(data));try{if(typeof loadChosenNotes==='function')loadChosenNotes();if(typeof renderChosenNotes==='function')renderChosenNotes();}catch(_){} }"
new2="""function store(){
 // Write only the verified teacher's student-specific record; do not overwrite legacy data.
 const sk=dnyNotesStorageKey(),rk=dnyNotesRecordKey(state.roll,state.term);
 if(!sk||!rk){alert('शिक्षक लॉगिन किंवा विद्यार्थी माहिती उपलब्ध नाही. नोंदी सेव्ह झालेल्या नाहीत.');return false;}
 try{const db=JSON.parse(localStorage.getItem(sk)||'{}');
  db[rk]=state.draft.map(x=>({subject:x.subject,text:x.text}));
  localStorage.setItem(sk,JSON.stringify(db));
  if(typeof loadChosenNotes==='function')loadChosenNotes();
  if(typeof renderChosenNotes==='function')renderChosenNotes();
  if(typeof syncProgressNoteFields==='function')syncProgressNoteFields();
  return true;
 }catch(e){alert('नोंदी सेव्ह झाल्या नाहीत: '+e.message);return false;}
}"""
old3="function save(){store();let e=$('gyNWStatus');if(e)e.textContent='निवडलेल्या नोंदी यशस्वीपणे जतन झाल्या.';}"
new3="function save(){if(!store())return;let e=$('gyNWStatus');if(e)e.textContent='निवडलेल्या नोंदी यशस्वीपणे जतन झाल्या.';}"
old4='<button class="gyNWBack" id="gyNWAnother">विषयांच्या यादीकडे या</button>'
old5="$('gyNWBackSubjects').onclick=subjectView;$('gyNWAnother').onclick=subjectView;"
new5="$('gyNWBackSubjects').onclick=subjectView;"
for a,b in [(old,new),(old2,new2),(old3,new3),(old4,''),(old5,new5)]:
 if h.count(a)!=1:raise SystemExit('Expected unique CCE anchor not found: '+a[:65]+'; no changes')
 h=h.replace(a,b,1)
enc=base64.b64encode(h.encode()).decode()
s=s[:m.start(2)]+enc+s[m.end(2):]
p.write_text(s,encoding='utf-8')
print('CCE descriptive notes unified with teacher-scoped progress notes; extra button removed; legacy data preserved')
