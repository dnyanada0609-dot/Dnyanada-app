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

# Student form only: separate required fields from optional information.
# Keep existing Aadhaar values in historical records, but do not display or accept
# a new number in this form. Printed class lists retain a blank column.
def student_minimal_form(source):
    matches=list(re.finditer(r'(\bclassFrame:\s*")([A-Za-z0-9+/=]+)(")',source))
    if len(matches)!=1: raise SystemExit('STOP: class module missing or duplicated')
    m=matches[0]
    h=base64.b64decode(m[2],validate=True).decode('utf-8')
    h=replace(h,'<h3>हजेरीसाठी आवश्यक मुख्य माहिती</h3>','<h3>मुख्य विद्यार्थी माहिती</h3>')
    h=replace(h,'<label>जनरल रजिस्टर नंबर</label>','<label>जनरल रजिस्टर नंबर (ऐच्छिक)</label>')
    h=replace(h,'<input id="birth" type="date"></div><div class="field"><label>मूळ जात *</label>', '<input id="birth" type="date" required></div></div><h3>अतिरिक्त विद्यार्थी माहिती — सर्व ऐच्छिक</h3><p class="small">शाळेच्या अधिकृत परवानगीने शैक्षणिक कामासाठी आवश्यक असल्यासच अतिरिक्त माहिती भरा. अतिरिक्त माहिती रिकामी ठेवूनही विद्यार्थी जतन करता येईल.</p><div class="formgrid"><div class="field"><label>मूळ जात (ऐच्छिक)</label>')
    h=replace(h,'<h3>अतिरिक्त विद्यार्थी माहिती</h3><div class="formgrid">','<div class="formgrid">')
    h=replace(h,'<select id="studentClass">','<select id="studentClass" required>')
    h=replace(h,'<select id="gender">','<select id="gender" required>')
    h=replace(h,'<input id="aadhaar" inputmode="numeric" maxlength="12" placeholder="१२ अंकी क्रमांक">','<textarea id="aadhaar" rows="2" readonly aria-label="आधार क्रमांक प्रिंटनंतर हाताने लिहा" placeholder="प्रिंट काढल्यानंतर आधार कार्ड क्रमांक हाताने लिहावा."></textarea><p class="small" style="color:#125b92;margin:4px 0">आवश्यक असल्यास प्रिंट काढल्यानंतर आधार कार्ड क्रमांक हाताने लिहावा. या बॉक्समध्ये क्रमांक भरता येणार नाही.</p>')
    for field in ('bpl','disability','meal'):
        h=replace(h,f'<select id="{field}">',f'<select id="{field}"><option value="">निवड ऐच्छिक</option>')
    h=replace(h,"const s={id:editId||('s'+Date.now()+Math.random().toString(16).slice(2,6)),name,", "if(!gender.value){alert('कृपया लिंग निवडा.');return}if(!birth.value){alert('कृपया जन्मतारीख निवडा.');return}const s={id:editId||('s'+Date.now()+Math.random().toString(16).slice(2,6)),name,")
    h=replace(h,'aadhaar:aadhaar.value.trim()',"aadhaar:editId?(data.students.find(x=>x.id===editId)?.aadhaar||''):''")
    h=replace(h,"aadhaar.value=s.aadhaar||'';","aadhaar.value='';")
    h=replace(h,"bpl.value='नाही';disability.value='नाही';meal.value='होय';","bpl.value='';disability.value='';meal.value='';")
    h=replace(h,"bpl:s.bpl||'नाही',disability:s.disability||'नाही'","bpl:s.bpl??'नाही',disability:s.disability??'नाही'")
    h=replace(h,"bpl.value=s.bpl||'नाही';disability.value=s.disability||'नाही';","bpl.value=s.bpl??'नाही';disability.value=s.disability??'नाही';")
    h=replace(h,"meal.value=s.meal||'होय';","meal.value=s.meal??'होय';")
    # Keep the previous default for older records with no meal field; new explicit
    # blank selections are not counted as confirmed meal beneficiaries.
    if h.count("String(s.meal||'होय')")!=2: raise SystemExit('STOP: unexpected meal counters')
    h=h.replace("String(s.meal||'होय')","String(s.meal??'होय')")
    h=replace(h,"<td>${esc(s.aadhaar||'')}</td><td>${esc(s.bpl||'नाही')}</td><td>${esc(s.disability||'नाही')}</td>","<td></td><td>${esc(s.bpl??'नाही')}</td><td>${esc(s.disability??'नाही')}</td>")
    h=replace(h,"['aadhaar','आधार क्रमांक']","['aadhaar','आधार क्रमांक (हस्तलिखित)']")
    h=replace(h,"'विद्यार्थ्याचा पत्ता','आधार क्रमांक','बीपीएल'","'विद्यार्थ्याचा पत्ता','आधार क्रमांक (हस्तलिखित)','बीपीएल'")
    h=replace(h,"const val=(st,k)=>k==='calculatedAge'?","const val=(st,k)=>k==='aadhaar'?'':k==='calculatedAge'?")
    h=replace(h,"if(k.startsWith('blank')) return 22;","if(k.startsWith('blank')) return 22;\n  if(k==='aadhaar') return 22;")
    h=replace(h,"<h2>विद्यार्थी माहिती यादी</h2><table>${colgroup}","<h2>विद्यार्थी माहिती यादी</h2>${keys.includes('aadhaar')?'<p style=\"font-size:11px\">आवश्यक असल्यास प्रिंट काढल्यानंतर आधार कार्ड क्रमांक हाताने लिहावा.</p>':''}<table>${colgroup}")
    h=replace(h,'हजेरी टॅबमध्ये नाव, लिंग, जन्मतारीख, मूळ जात आणि जात प्रवर्ग ही मुख्य माहितीच दिसेल. अतिरिक्त माहिती येथेच राहील.','मुख्य माहिती भरून विद्यार्थी जतन करा. जात व प्रवर्ग भरले असल्यास संबंधित अहवालात वापरले जातील. अतिरिक्त माहिती ऐच्छिक आहे.')
    return source[:m.start(2)]+base64.b64encode(h.encode('utf-8')).decode('ascii')+source[m.end(2):]

s=update_student_cloud_message(s)
s=student_minimal_form(s)
# Target only the three embedded modules. Preserve record identifiers and all other code.
def patch_requested_modules(source):
    def module(name, transform):
        nonlocal source
        ms=list(re.finditer(r'(\b'+name+r':\s*")([A-Za-z0-9+/=]+)(")',source))
        if len(ms)!=1: raise SystemExit('STOP: module missing/duplicated: '+name)
        m=ms[0]; old=base64.b64decode(m[2],validate=True).decode('utf-8'); new=transform(old)
        source=source[:m.start(2)]+base64.b64encode(new.encode()).decode()+source[m.end(2):]
    def append_script(h,script):
        pos=h.lower().rfind('</body>')
        if pos<0: raise SystemExit('STOP: module body missing')
        return h[:pos]+script+h[pos:]
    def cumulative(h):
        # Keep contenteditable attributes in the original index-based record schema;
        # inert prevents user interaction without shifting any saved field indices.
        h=replace(h,'<td contenteditable="true">विद्यार्थी आधार कार्ड संकेतांक</td><td contenteditable="true"></td>', '<td contenteditable="true" inert data-dn-aadhaar-label>विद्यार्थी आधार कार्ड संकेतांक</td><td contenteditable="true" inert data-dn-aadhaar-lock aria-label="प्रिंट काढल्यानंतर आधार कार्ड क्रमांक हाताने लिहावा"></td>')
        h=replace(h,"'विद्यार्थी आधार कार्ड संकेतांक':s.aadhaar", "'विद्यार्थी आधार कार्ड संकेतांक':''")
        # Clean before synchronous exports and saves; old stored snapshots are not bulk deleted.
        for anchor in ('function collect(){','function saveHtml(){','function save(){if(!selected||restoring)return;','function capture(){','function gyCumNativePrint(all){'):
            # print function may be modified by existing workflow; other guards still apply.
            if anchor=='function gyCumNativePrint(all){' and h.count(anchor)==0: continue
            h=replace(h,anchor,anchor+'window.dnCumAadhaarBlank?.();')
        h=append_script(h,'''<style> #p3 [data-dn-aadhaar-lock]{min-height:28px;cursor:default;}@media screen{#p3 [data-dn-aadhaar-lock]:empty::after{content:"प्रिंट काढल्यानंतर आधार कार्ड क्रमांक हाताने लिहावा.";font-size:12px;color:#125b92;font-weight:600}}@media print{#p3 [data-dn-aadhaar-lock]::after{content:none!important}}</style><script id="dn-cum-aadhaar-handwritten">(function(){
function blank(){const row=document.querySelector('#p3 #body3 tr');if(!row||row.cells.length<2)return;const a=row.cells[0],b=row.cells[1];if(!a.hasAttribute('data-dn-aadhaar-label')){a.setAttribute('data-dn-aadhaar-label','');a.setAttribute('inert','')}if(a.textContent!=='विद्यार्थी आधार कार्ड संकेतांक')a.textContent='विद्यार्थी आधार कार्ड संकेतांक';if(!b.hasAttribute('data-dn-aadhaar-lock')){b.setAttribute('data-dn-aadhaar-lock','');b.setAttribute('inert','');b.setAttribute('aria-label','प्रिंट काढल्यानंतर आधार कार्ड क्रमांक हाताने लिहावा')}if(b.textContent||b.children.length)b.replaceChildren();}
window.dnCumAadhaarBlank=blank;blank();const p=document.getElementById('p3');if(p)new MutationObserver(blank).observe(p,{childList:true,characterData:true,subtree:true});document.addEventListener('beforeinput',e=>{if(e.target.closest?.('[data-dn-aadhaar-lock],[data-dn-aadhaar-label]'))e.preventDefault()},true);window.addEventListener('beforeprint',blank);
})();</script>''')
        return h
    def hpc(h):
        h=replace(h,"${input('आधार आयडी')}",'''<div class="field"><label>आधार आयडी :</label><input data-key="आधार आयडी" readonly aria-label="प्रिंट काढल्यानंतर आधार कार्ड क्रमांक हाताने लिहावा" placeholder="प्रिंट काढल्यानंतर आधार कार्ड क्रमांक हाताने लिहावा."></div>${input('तालुका')}${input('जिल्हा')}''')
        h=replace(h,'let gyHpcTeacherProfile=null;',"let gyHpcTeacherProfile=null;try{gyHpcTeacherProfile=JSON.parse(localStorage.getItem('gyanadaTeacherProfile')||'null')}catch(e){}")
        h=replace(h,"const p=gyHpcTeacherProfile;if(!p)return;","try{const saved=JSON.parse(localStorage.getItem('gyanadaTeacherProfile')||'null');if(saved)gyHpcTeacherProfile=saved}catch(e){}const p=gyHpcTeacherProfile;if(!p)return;")
        h=replace(h,"Object.entries(fields).forEach(([key,value])=>{if(value)hpcSetField(key,value)});", "Object.entries(fields).forEach(([key,value])=>{if(value!==undefined&&value!==null&&value!==''){const el=Array.from(document.querySelectorAll('#pages [data-key]')).find(e=>e.dataset.key===key);if(el)el.value=String(value)}});")
        # Block old values at all loading/saving paths, including print preview.
        h=replace(h,"function save(notify){let data={};", "function save(notify){const aad=document.querySelector('[data-key=\"आधार आयडी\"]');if(aad)aad.value='';let data={};")
        h=replace(h,"let v=data[el.dataset.key];if(v===undefined)return;", "let v=el.dataset.key==='आधार आयडी'?'':data[el.dataset.key];if(v===undefined)return;")
        h=replace(h,"let v=data[el.dataset.key];if(el.type==='checkbox'||el.type==='radio')", "let v=el.dataset.key==='आधार आयडी'?'':data[el.dataset.key];if(el.type==='checkbox'||el.type==='radio')")
        h=replace(h,"function hpcSetField(key,value){", "function hpcSetField(key,value){if(key==='आधार आयडी')return;")
        h=replace(h,"function hpcCreateCover(){", "function hpcCreateCover(){gyHpcApplyTeacher();")
        # Use the current teacher profile on the print-only cover, never a stale cover fallback.
        h=replace(h,"value.textContent=hpcCoverValue(keys)||localStorage.getItem(storeKey)||'';", "const profileKeys={'शाळेचे नाव':'schoolName','UDISE कोड':'udise','तालुका':'taluka','जिल्हा':'district'};const profileKey=profileKeys[label];value.textContent=profileKey&&gyHpcTeacherProfile&&Object.prototype.hasOwnProperty.call(gyHpcTeacherProfile,profileKey)?String(gyHpcTeacherProfile[profileKey]??''):(hpcCoverValue(keys)||localStorage.getItem(storeKey)||'');")
        h=replace(h,"hpcApplyMaster(linkedStudents[i]);calcAttendance()}","hpcApplyMaster(linkedStudents[i]);gyHpcApplyTeacher();calcAttendance()}")
        h=append_script(h,'''<style>@media print{input[data-key="आधार आयडी"]::placeholder{color:transparent!important}}</style><script>document.addEventListener('DOMContentLoaded',()=>{gyHpcApplyTeacher()});</script>''')
        # Print clones use input values or placeholders? ensure no placeholder copied in preview.
        h=replace(h,"const orig=originals[j];if(!orig)return;", "const orig=originals[j];if(!orig)return;if(orig.dataset.key==='आधार आयडी'){el.value='';el.removeAttribute('placeholder');el.removeAttribute('value');return;}")
        return h
    def cce(h):
        # Only the progress-report display label; preserve all ten grade slots.
        pattern=r'(const contents=\[")([A-Za-z0-9+/=]+)(","[A-Za-z0-9+/=]+",")([A-Za-z0-9+/=]+)("\];)'
        matches=list(re.finditer(pattern,h))
        if len(matches)!=1: raise SystemExit('STOP: progress embedded source missing or duplicated')
        m=matches[0]
        pr=base64.b64decode(m[4],validate=True).decode('utf-8')
        pr=replace(pr,"const subjects=['मराठी','हिंदी','इंग्रजी','गणित','परिसर अभ्यास','विज्ञान'", "const subjects=['मराठी','हिंदी','इंग्रजी','गणित','परिसर अभ्यास/ विज्ञान','विज्ञान'")
        return h[:m.start(4)]+base64.b64encode(pr.encode()).decode()+h[m.end(4):]
    module('cumulativeFrame',cumulative)
    module('hpcFrame',hpc)
    module('cceFrame',cce)
    return source

s=patch_requested_modules(s)
print('Requested cumulative/HPC handwritten Aadhaar, HPC profile and progress-report display label applied')

print("Student required/optional form and handwritten Aadhaar column applied")
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

# Retention: manage only successfully committed new versions, not historical unknown chunks.
# Root transaction coordinates concurrent devices; legacy metadata is never replaced.
retention_js = r"""
const KEEP_BACKUPS=3;
const CLEANUP_BATCH=8;
const CLEANUP_LIMIT=320;
const MAX_RETIRED=64;
const RETENTION_AGE=10*60*1000;
function retentionEntry(value){
 if(!value || typeof value.latestVersion!=='string' || !/^[br][a-z0-9_]{1,90}$/.test(value.latestVersion) || !Number.isSafeInteger(value.chunkCount) || value.chunkCount<1 || value.chunkCount>1000)return null;
 return {latestVersion:value.latestVersion,chunkCount:value.chunkCount,managed:value.managed===true && /^r[a-f0-9]{32}$/.test(value.latestVersion)};
}
function retentionState(doc){
 const data=doc.exists?(doc.data()||{}):{};
 const raw=data.scopedRetentionV1||{};
 const history=Array.isArray(raw.history)?raw.history.map(retentionEntry).filter(Boolean).slice(0,KEEP_BACKUPS):[];
 const retired=Array.isArray(raw.retired)?raw.retired.slice(0,MAX_RETIRED).filter(x=>{
  const e=retentionEntry(x);
  return e && e.managed && Number.isSafeInteger(x.nextIndex) && x.nextIndex>=0 && x.nextIndex<e.chunkCount && Number.isFinite(x.retiredAt);
 }).map(x=>({...retentionEntry(x),nextIndex:x.nextIndex,retiredAt:x.retiredAt})):[];
 return {data,history,retired};
}
function chunkRef(root,id,index){return root.collection('chunks').doc(id+'_'+String(index).padStart(5,'0'));}
function verifyUid(uid){if(context().uid!==uid)throw Error('खाते बदलले आहे.');}
function newBackupId(){return 'r'+Array.from(crypto.getRandomValues(new Uint8Array(16)),x=>x.toString(16).padStart(2,'0')).join('');}
async function publishRetained(db,root,uid,id,count,expected){
 await db.runTransaction(async tx=>{
  verifyUid(uid);
  const doc=await tx.get(root);
  verifyUid(uid);
  const current=scopedMeta(doc);
  if((current.latestVersion||null)!==expected)throw Error('क्लाऊडवर दुसरी आवृत्ती आली. कृपया डेटा परत आणून पुन्हा प्रयत्न करा.');
  const state=retentionState(doc);
  const previous=retentionEntry(current);
  // Older clients might still write an untracked backup; never delete such a version.
  const prior=previous && state.history.find(x=>x.latestVersion===previous.latestVersion);
  const list=[{latestVersion:id,chunkCount:count,managed:true},...(previous?[prior||previous]:[]),...state.history];
  const seen=new Set();
  const unique=list.filter(x=>{if(seen.has(x.latestVersion))return false;seen.add(x.latestVersion);return true;});
  const history=unique.slice(0,KEEP_BACKUPS);
  const protectedIds=new Set([...history.map(x=>x.latestVersion),state.data.latestVersion]);
  const retired=state.retired.filter(x=>!protectedIds.has(x.latestVersion));
  for(const e of unique.slice(KEEP_BACKUPS)){
   if(e.managed && !protectedIds.has(e.latestVersion) && !retired.some(x=>x.latestVersion===e.latestVersion) && retired.length<MAX_RETIRED){
    retired.push({...e,nextIndex:0,retiredAt:Date.now()});
   }
  }
  // Atomic metadata update: the published pointer and retention state agree.
  tx.set(root,{scopedBackupV2:{latestVersion:id,chunkCount:count,updatedAt:firebase.firestore.FieldValue.serverTimestamp(),schema:2},scopedRetentionV1:{history,retired}}, {merge:true});
 });
}
async function cleanupRetained(db,root,uid){
 let deleted=0;
 while(deleted<CLEANUP_LIMIT){
  verifyUid(uid);
  const n=await db.runTransaction(async tx=>{
   verifyUid(uid);
   const doc=await tx.get(root);
   verifyUid(uid);
   if(!doc.exists)return 0;
   const state=retentionState(doc);
   const current=scopedMeta(doc);
   if(!retentionEntry(current))return 0;
   const protectedIds=new Set([current.latestVersion,state.data.latestVersion,...state.history.map(x=>x.latestVersion)]);
   // Grace period protects normal in-flight restore. Only previously committed managed IDs are eligible.
   const candidate=state.retired.find(x=>!protectedIds.has(x.latestVersion) && Date.now()-x.retiredAt>=RETENTION_AGE);
   if(!candidate)return 0;
   const end=Math.min(candidate.chunkCount,candidate.nextIndex+CLEANUP_BATCH,candidate.nextIndex+CLEANUP_LIMIT-deleted);
   for(let i=candidate.nextIndex;i<end;i++)tx.delete(chunkRef(root,candidate.latestVersion,i));
   const retired=state.retired.flatMap(x=>x.latestVersion!==candidate.latestVersion?[x]:(end<x.chunkCount?[{...x,nextIndex:end}]:[]));
   tx.set(root,{scopedRetentionV1:{history:state.history,retired}}, {merge:true});
   return end-candidate.nextIndex;
  });
  if(!n)break;
  deleted+=n;
 }
 return deleted;
}
"""
cloud=replace(cloud,'async function backup(silent=false){',retention_js+'\nasync function backup(silent=false){')
# Keep old manual behavior, but refuse to overwrite a version that changed during upload.
start=cloud.index(' if(silent){',cloud.index('async function backup(silent=false){'))
end=cloud.index(' const chunks=[];',start)
cloud=cloud[:start]+r""" const remote=await root.get({source:'server'});
 verifyUid(uid);
 const expected=scopedMeta(remote).latestVersion||null;
 if(silent){
  const known=window.__dnAccount.store.getItem(versionMarker(uid));
  if(!known)throw Error('प्रथम एकदा स्वतः बॅकअप घ्या.');
  if(!remote.exists||expected!==known)throw Error('क्लाऊडवर दुसरी आवृत्ती आहे. आपोआप बॅकअप थांबवला.');
 }

"""+cloud[end:]
start=cloud.index(" const id='b'",cloud.index('async function backup(silent=false){'))
end=cloud.index(" const verify=await root.get({source:'server'});",start)
cloud=cloud[:start]+r""" const id=newBackupId();
 for(let i=0;i<chunks.length;i++){
  verifyUid(uid);
  await chunkRef(root,id,i).set({payload:chunks[i],version:id,index:i});
 }
 // All writes must be acknowledged, then every chunk read back from the server.
 for(let i=0;i<chunks.length;i++){
  verifyUid(uid);
  const check=await chunkRef(root,id,i).get({source:'server'});
  const d=check.exists?check.data():null;
  if(!d || d.version!==id || d.index!==i || d.payload!==chunks[i])throw Error('बॅकअप भागाची क्लाऊड पडताळणी अयशस्वी. जुना बॅकअप कायम आहे.');
 }
 verifyUid(uid);
 await publishRetained(db,root,uid,id,chunks.length,expected);

"""+cloud[end:]
cloud=replace(cloud,"   count+' स्थानिक स्टोरेज नोंदी जतन झाल्या.');\n}","   count+' स्थानिक स्टोरेज नोंदी जतन झाल्या.');\n // Cleanup is separate from backup success; failure never rolls back a valid backup.\n try{await cleanupRetained(db,root,uid);}catch(error){console.warn('DNYANADA retention deferred:',error);}\n}")
# A restore which raced with publication must retry rather than write stale local state.
cloud=replace(cloud,'  const previous = Object.create(null);',"  const latest=await root.get({source:'server'});\n   verifyUid(uid);\n   if(scopedMeta(latest).latestVersion!==version)throw Error('क्लाऊडवर नवीन बॅकअप आला आहे. कृपया डेटा परत आणा पुन्हा दाबा.');\n   const previous = Object.create(null);")

# Version the external script using its final content, not a fixed release number.
import hashlib
version = hashlib.sha256(cloud.encode('utf-8')).hexdigest()[:20]
if 'जुना बॅकअप सुरक्षित ठेवला आहे. पडताळणी आवश्यक.' in cloud:
    raise SystemExit('STOP: obsolete backup guard remains')
if 'scopedBackupV2' not in cloud:
    raise SystemExit('STOP: scoped backup metadata missing')
output = replace(output, '<script src="/dnyanada_cloud_backup.js"></script>', '<script src="/dnyanada_cloud_backup.js?v='+version+'"></script>')
# Dashboard-only information links; no changes to account, app modules or cloud script.
policy_js = '(function(){\n\'use strict\';\nconst pages={\n terms:{title:\'ॲप वापराच्या अटी\',body:`<p>ज्ञानदा Smart Teacher App हे शिक्षकांच्या शालेय नोंदी व दैनंदिन कामकाजासाठी सहाय्यक साधन आहे.</p>\n<h3>१. सदस्यत्व व खाते</h3><p>सध्याचे वार्षिक सदस्यत्व शुल्क ₹२२२ आहे. शैक्षणिक वर्षाचा सामान्य कालावधी १ जून ते ३१ मे आहे; आपल्या खात्यात दर्शविलेली सक्रियता व अंतिम तारीख लागू राहील. शुल्क, नूतनीकरण किंवा परताव्याबाबत पैसे भरण्यापूर्वी अधिकृत प्रशासकाशी खात्री करा. खाते निष्क्रिय किंवा सदस्यत्व संपल्यास ऑनलाइन प्रवेश बंद होऊ शकतो.</p>\n<h3>२. अधिकृत वापर</h3><p>आपले लॉगिन व पासवर्ड गोपनीय ठेवा. दुसऱ्या व्यक्तीचे खाते वापरू नका किंवा अनधिकृत प्रवेश करू नका. शाळेच्या परवानगीने आणि आवश्यक तेवढीच विद्यार्थी माहिती नोंदवा. तयार केलेले निकाल, दाखले, अहवाल व प्रिंट अधिकृत वापरापूर्वी तपासण्याची जबाबदारी शिक्षकाची आहे.</p>\n<h3>३. बॅकअप व डेटा परत आणणे</h3><p>नोंदी प्रथम उपकरणात जतन होतात. इंटरनेट, सक्रिय सदस्यत्व आणि क्लाऊडची उपलब्धता असल्यास बॅकअप होतो. ॲप बंद करण्यापूर्वी महत्त्वाच्या बदलांचा बॅकअप यशस्वी झाल्याची पुष्टी तपासा. नवीन उपकरणावर अद्ययावत माहिती नसल्यास डेटा परत आणा. एकाच खात्यात दोन उपकरणांवर वेगवेगळे बदल केल्यास थेट बॅकअप किंवा Restore करू नका; आधी नोंदी तपासा व सहाय्यता घ्या. स्वतंत्र अधिकृत प्रतीही सुरक्षित ठेवा.</p>\n<h3>४. सेवा व मर्यादा</h3><p>इंटरनेट, ब्राउझर, उपकरण, Firebase कोटा किंवा तांत्रिक अडचणींमुळे सेवा तात्पुरती प्रभावित होऊ शकते. बाह्य पाठ्यपुस्तक संकेतस्थळांच्या उपलब्धतेवर त्यांचे स्वतःचे नियम लागू होतात. ॲप हे अधिकृत शासकीय नोंदवहीचे पर्यायी साधन असल्याचा दावा करत नाही.</p>\n<h3>५. सहाय्यता व बदल</h3><p>तांत्रिक समस्या, सदस्यत्व किंवा अटींविषयी प्रश्न असल्यास ॲपमधील तांत्रिक सहाय्यता विभागातून अधिकृत प्रशासकाशी संपर्क साधा. अटींमध्ये बदल झाल्यास अद्ययावत मजकूर येथे उपलब्ध केला जाईल.</p>`},\n privacy:{title:\'गोपनीयता धोरण\',body:`<p>ज्ञानदा Smart Teacher App मध्ये शालेय नोंदींच्या व्यवस्थापनासाठी आवश्यक माहिती हाताळली जाते. अनावश्यक वैयक्तिक माहिती भरू नका.</p>\n<h3>१. कोणती माहिती हाताळली जाते?</h3><p>शिक्षकाचे नाव, ईमेल, ऐच्छिक मोबाईल क्रमांक, खाते व सदस्यत्व माहिती; शिक्षकाने भरलेली विद्यार्थी नावे, जन्मतारीख, संपर्क, फोटो, उपस्थिती, गुण, शैक्षणिक नोंदी, शाळा व इतर संबंधित नोंदी. काही टॅबमध्ये भरल्यास प्रवर्ग, आरोग्य किंवा इतर संवेदनशील माहितीही असू शकते. पासवर्डची पडताळणी Firebase Authentication द्वारे होते.</p>\n<h3>२. माहितीचा उद्देश</h3><p>शिक्षकाचा प्रवेश, सदस्यत्व व्यवस्थापन, शालेय नोंदी, अहवाल, प्रिंट, बॅकअप, पुनर्प्राप्ती आणि तांत्रिक सहाय्यता यासाठी माहिती वापरली जाते. विद्यार्थी माहिती जाहिरात किंवा असंबंधित कामासाठी भरू नये.</p>\n<h3>३. माहिती कुठे जतन होते?</h3><p>नोंदी उपकरणाच्या ब्राउझरमधील स्थानिक स्टोरेजमध्ये राहू शकतात. क्लाऊड बॅकअप Firebase Cloud Firestore मध्ये खात्याच्या स्वतंत्र UID नुसार जतन होतो. लॉगिन व होस्टिंगसाठी Google Firebase सेवा वापरली जाते. संबंधित सेवांबद्दल <a href="https://firebase.google.com/support/privacy" target="_blank" rel="noopener noreferrer">Firebase गोपनीयता माहिती</a> पहा. बाह्य पाठ्यपुस्तक संकेतस्थळांना त्यांच्या स्वतंत्र धोरणांचा आधार असतो.</p>\n<h3>४. सुरक्षा व प्रवेश</h3><p>लॉगिन, खातेवार स्टोरेज आणि Firebase प्रवेश नियम वापरले जातात. अधिकृत प्रशासकाला खाते व सदस्यत्व व्यवस्थापनासाठी आवश्यक प्रवेश असतो. कोणतीही प्रणाली पूर्णपणे त्रुटीमुक्त नसते. सामायिक उपकरणावर काम झाल्यावर लॉगआउट करा आणि पासवर्ड शेअर करू नका. ब्राउझर डेटा हटवण्यापूर्वी यशस्वी बॅकअप तपासा.</p>\n<h3>५. विद्यार्थ्यांची गोपनीयता</h3><p>विद्यार्थ्यांची माहिती नोंदवण्यापूर्वी शाळेची अधिकृत परवानगी व लागू असलेली पालक/पालकप्रतिनिधीची संमती किंवा इतर आवश्यक आधार सुनिश्चित करा. आवश्यक तेवढीच माहिती वापरा. संवेदनशील नोंदी किंवा विद्यार्थी अहवाल अनधिकृत व्यक्तींना पाठवू नका.</p>\n<h3>६. जतन कालावधी व हटवण्याची विनंती</h3><p>स्थानिक नोंदी ब्राउझरमध्ये आणि क्लाऊड नोंदी संबंधित खात्यात राहू शकतात. नवीन बॅकअप व्यवस्थेत नवीनतम तीन व्यवस्थापित आवृत्त्या ठेवण्याचे नियोजन आहे; पात्र जुन्या आवृत्त्या पडताळणीनंतर हटवल्या जाऊ शकतात. पूर्वीच्या प्रती वेगळ्या राहू शकतात. खाते निष्क्रिय केल्याने माहिती आपोआप हटत नाही. माहिती पाहणे, दुरुस्ती, हटवणे किंवा खाते बंद करण्याच्या विनंतीसाठी तांत्रिक सहाय्यता विभागातून अधिकृत प्रशासकाशी संपर्क साधा. विनंतीची ओळख, शाळेची अधिकृतता व लागू नोंद-जतन आवश्यकता तपासल्या जातील.</p>\n<h3>७. गोपनीयतेसंबंधी संपर्क</h3><p>माहितीच्या वापराबद्दल प्रश्न किंवा सुरक्षा समस्या असल्यास ॲपमधील तांत्रिक सहाय्यता विभाग वापरा. या धोरणातील अद्ययावत माहिती येथे उपलब्ध केली जाईल.</p>`}\n};\nfunction install(){\n if(document.getElementById(\'dn-policy-links\'))return;\n const css=document.createElement(\'style\');css.id=\'dn-policy-style\';css.textContent=`\n #dn-policy-links{position:fixed;bottom:calc(8px + env(safe-area-inset-bottom,0px));left:0;right:0;z-index:2147483001;pointer-events:none;display:flex;justify-content:space-between;align-items:center;padding:0 8px;box-sizing:border-box;min-height:40px}\n #dn-policy-links[hidden]{display:none!important}\n #dn-policy-links button{pointer-events:auto;background:#fff;color:#125b92;border:1px solid #125b92;border-radius:999px;max-width:var(--dn-policy-width,90px);min-height:36px;padding:5px 8px;box-sizing:border-box;font:700 12px/1.25 system-ui,sans-serif;cursor:pointer;overflow-wrap:normal;white-space:normal;box-shadow:0 1px 5px #0002}\n #dn-policy-dialog{box-sizing:border-box;width:min(94vw,620px);max-width:94vw;max-height:86vh;max-height:86dvh;border:1px solid #125b92;border-radius:14px;padding:0;background:#fff;color:#173047;font:15px/1.65 system-ui,sans-serif;overflow:auto;z-index:2147483646}\n #dn-policy-dialog::backdrop{background:#0008}\n #dn-policy-dialog header{position:sticky;top:0;background:#125b92;color:white;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:10px 14px;z-index:1}\n #dn-policy-dialog h2{font-size:18px;margin:0;color:white}\n #dn-policy-dialog header button{background:#fff;color:#125b92;border:0;border-radius:8px;min-width:38px;min-height:38px;font-size:24px;cursor:pointer}\n #dn-policy-content{padding:12px 16px 20px;overflow-wrap:anywhere}\n #dn-policy-content h3{font-size:16px;color:#125b92;margin:16px 0 5px}\n #dn-policy-content p{margin:0 0 10px}\n html.dnyanada-login-locked #dn-policy-links{display:none!important}\n @media print{#dn-policy-links,#dn-policy-dialog{display:none!important}}\n `;document.head.appendChild(css);\n const links=document.createElement(\'div\');links.id=\'dn-policy-links\';links.hidden=true;\n const dialog=document.createElement(\'dialog\');dialog.id=\'dn-policy-dialog\';dialog.setAttribute(\'aria-labelledby\',\'dn-policy-heading\');\n dialog.innerHTML=\'<header><h2 id="dn-policy-heading"></h2><button type="button" aria-label="बंद करा">×</button></header><div id="dn-policy-content"></div>\';\n dialog.querySelector(\'button\').addEventListener(\'click\',()=>dialog.close());\n for(const [key,label] of [[\'terms\',\'वापराच्या अटी\'],[\'privacy\',\'गोपनीयता धोरण\']]){\n  const b=document.createElement(\'button\');b.type=\'button\';b.textContent=label;b.addEventListener(\'click\',()=>{\n   if(links.hidden)return;\n   dialog.querySelector(\'h2\').textContent=pages[key].title;\n   dialog.querySelector(\'#dn-policy-content\').innerHTML=pages[key].body;\n   if(!dialog.open)dialog.showModal();dialog.scrollTop=0;\n  });links.appendChild(b);\n }\n document.body.append(links,dialog);\n let frame=null,observedBody=null;const bodyObserver=new MutationObserver(refresh);\n function refresh(){\n  const next=document.getElementById(\'dn-app\');\n  if(next!==frame){if(frame)frame.removeEventListener(\'load\',refresh);frame=next;if(frame)frame.addEventListener(\'load\',refresh);}\n  let body=null;try{body=frame?.contentDocument?.body||null;}catch(_){}\n  if(body!==observedBody){bodyObserver.disconnect();observedBody=body;if(body)bodyObserver.observe(body,{attributes:true,attributeFilter:[\'class\']});}\n  const cloud=document.querySelector(\'#dny-cloud-tools > button\');\n  const r=cloud?.getBoundingClientRect();\n  const available=r?Math.floor(Math.min(r.left,innerWidth-r.right)-16):0;\n  const dashboard=!!body&&!!body.querySelector(\'.dashboard-home\')&&!body.classList.contains(\'app-open\');\n  const visible=dashboard&&!!window.__dnAccount&&!document.documentElement.classList.contains(\'dnyanada-login-locked\')&&available>=44;\n  links.style.setProperty(\'--dn-policy-width\',Math.max(44,Math.min(115,available))+\'px\');\n  links.hidden=!visible;if(!visible&&dialog.open)dialog.close();\n }\n new MutationObserver(refresh).observe(document.body,{childList:true});\n new MutationObserver(refresh).observe(document.documentElement,{attributes:true,attributeFilter:[\'class\']});\n window.addEventListener(\'resize\',refresh);refresh();\n}\nif(document.readyState===\'loading\')document.addEventListener(\'DOMContentLoaded\',install);else install();\n})();\n'
assert output.endswith('</body></html>')
output=output[:-len('</body></html>')]+'<script id="dn-policy-script">'+policy_js+'</script></body></html>'
p.write_text(output);c.write_text(cloud)
print('Cloud script content version:', version)
print('Account isolation candidate built; browser testing required')
