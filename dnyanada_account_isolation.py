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
        # Change presentation only. Keep subject keys, marks, slots and grade bridges intact.
        label_hits=[0,0,0,0,0]
        def report_labels(doc):
            pairs=(
                ('<td class="subject-name" rowspan="2">${s.name}</td>',
                 '<td class="subject-name" rowspan="2">${s.name===\'परिसर अभ्यास\'?\'परिसर अभ्यास/विज्ञान\':s.name}</td>'),
                ('<th colspan="4">परिसर अभ्यास</th>',
                 '<th colspan="4">परिसर अभ्यास/विज्ञान</th>'),
                ('cell(escapeAttr(s.name),',
                 "cell(escapeAttr(s.name==='परिसर अभ्यास'?'परिसर अभ्यास/विज्ञान':s.name),"),
                ("td(sub.name,'rowspan=", 
                 "td(sub.name==='परिसर अभ्यास'?'परिसर अभ्यास/विज्ञान':sub.name,'rowspan="),
                ("td(sub.name,'excel-subject-cell')",
                 "td(sub.name==='परिसर अभ्यास'?'परिसर अभ्यास/विज्ञान':sub.name,'excel-subject-cell')"),
            )
            # The live build may omit an older renderer, or have several copies.
            # Only replace these exact display expressions, never the subject key.
            for i,(old,new) in enumerate(pairs):
                count=doc.count(old)
                label_hits[i]+=count
                if count:
                    doc=doc.replace(old,new)
            return doc
        # The embedded marks/notes documents share the same CCE display templates.
        pattern=r'(const contents=\[")([A-Za-z0-9+/=]+)(",")([A-Za-z0-9+/=]+)(",")([A-Za-z0-9+/=]+)("\];)'
        matches=list(re.finditer(pattern,h))
        if len(matches)!=1: raise SystemExit('STOP: CCE embedded sources missing or duplicated')
        m=matches[0]
        parts=[base64.b64decode(m[i],validate=True).decode('utf-8') for i in (2,4,6)]
        parts[0]=report_labels(parts[0])
        parts[1]=report_labels(parts[1])
        # Preserve the already requested progress-report change exactly as before.
        parts[2]=replace(parts[2],"const subjects=['मराठी','हिंदी','इंग्रजी','गणित','परिसर अभ्यास','विज्ञान'", "const subjects=['मराठी','हिंदी','इंग्रजी','गणित','परिसर अभ्यास/ विज्ञान','विज्ञान'")
        enc=[base64.b64encode(x.encode()).decode() for x in parts]
        h=h[:m.start()]+m[1]+enc[0]+m[3]+enc[1]+m[5]+enc[2]+m[7]+h[m.end():]
        h=report_labels(h)
        if not label_hits[0] or not label_hits[1] or not sum(label_hits[2:]):
            raise SystemExit('STOP: one CCE report has no recognized display template: '+str(label_hits))
        print('CCE display label replacements (marks, consolidated, review variants):',label_hits)
        return h
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
# CCE stable student notes patch — after the existing verified account isolation build.
from pathlib import Path
import base64, re, hashlib, json

# Apply only after dnyanada_account_isolation.py. No Firebase calls or data writes at build time.
EXPECTED={
 'cceFrame':'caf921ba731fb5333fb4f77ace10570129f4d58fc72bccf093fe3e77377b88a8',
 'classFrame':'abe2b3016eab11e289b281bcf3a9d2d54be9a19222733492f1aa525cbab2a025',
}
MARK='DN_CCE_STABLE_NOTES_20261126'
STORE='dnCCEStudentNotesV3'

def once(s,a,b):
    if s.count(a)!=1: raise SystemExit('STOP: CCE anchor mismatch: '+a[:100])
    return s.replace(a,b,1)

def block(s,a,b,new):
    if s.count(a)!=1: raise SystemExit('STOP: CCE block start: '+a)
    start=s.index(a); end=s.index(b,start+len(a))
    return s[:start]+new+'\n'+s[end:]

CORE=r'''// DN_CCE_STABLE_NOTES_20261126 — account-scoped, stable student IDs, academic year and term.
const dnNoteKey='dnCCEStudentNotesV3';
function dnNotesAccess(){if(!top.__dnAccount?.uid)throw Error('शिक्षक खाते पडताळणी आवश्यक आहे.');return localStorage;}
function dnNotesMaster(){try{const raw=dnNotesAccess().getItem('independentStudentManager_v1');if(!raw)return [];const data=JSON.parse(raw);return Array.isArray(data.students)?data.students.filter(x=>x&&typeof x.id==='string'&&x.id&&String(x.name||'').trim()):[]}catch(e){return []}}
function dnNotesById(id){const matches=dnNotesMaster().filter(s=>s.id===id);return matches.length===1?matches[0]:null;}
function dnNotesYear(){return String(document.getElementById('setupYear')?.value||'2026-27').trim();}
function dnNotesRecordKey(id,term,year=dnNotesYear()){return JSON.stringify([String(id),String(year),Number(term)===2?2:1]);}
function dnNotesDb(){const raw=dnNotesAccess().getItem(dnNoteKey);if(!raw)return {version:3,records:{},claims:{}};const d=JSON.parse(raw);if(!d||d.version!==3||!d.records||typeof d.records!=='object'||Array.isArray(d.records)||!d.claims||typeof d.claims!=='object'||Array.isArray(d.claims))throw Error('वर्णनात्मक नोंदींची रचना अवैध आहे.');return d;}
function dnNotesRead(id,term,year=dnNotesYear()){if(!dnNotesById(id))return [];try{const rows=dnNotesDb().records[dnNotesRecordKey(id,term,year)];return Array.isArray(rows)?rows:[]}catch(e){console.warn('CCE notes read',e);return []}}
function dnNotesWrite(id,term,year,rows){if(!dnNotesById(id)||year!==dnNotesYear())throw Error('विद्यार्थी किंवा शैक्षणिक वर्ष बदलले आहे. पुन्हा निवडा.');const d=dnNotesDb();d.records[dnNotesRecordKey(id,term,year)]=rows.map(x=>({subject:String(x.subject||''),text:String(x.text||'')}));dnNotesAccess().setItem(dnNoteKey,JSON.stringify(d));}
function dnNotesOldRosterId(roll){const st=roster[Number(roll)-1];if(!st||!String(st.name||'').trim())return '';const grade=String(document.getElementById('gyResultClass')?.value||document.getElementById('setupClass')?.value||'');const found=dnNotesMaster().filter(x=>String(x.name||'').trim()===String(st.name).trim()&&(!grade||gyGrade(x.className||x.class||x.grade)===grade));return found.length===1?found[0].id:'';}
function dnNotesProgressId(roll){const id=window.dnCCEProgressStudentId;if(id)return dnNotesById(id)?id:'';return dnNotesOldRosterId(roll);}
function dnNotesRefresh(){try{if(typeof syncProgressNoteFields==='function')syncProgressNoteFields();if(typeof window.gySyncProgressGradesAndNotes==='function')window.gySyncProgressGradesAndNotes();}catch(e){console.warn('CCE notes refresh',e)}}
// Legacy roll-number data is never assigned automatically. Explicit, one-time recovery per legacy record.
function dnNotesRecover(id,term,year){
 const student=dnNotesById(id);if(!student||year!==dnNotesYear())throw Error('विद्यार्थी पुन्हा निवडा.');
 const d=dnNotesDb(), target=dnNotesRecordKey(id,term,year);if(Object.prototype.hasOwnProperty.call(d.records,target))throw Error('या विद्यार्थी-सत्राच्या नवीन नोंदी आहेत. जुन्या नोंदी आपोआप मिसळणार नाहीत.');
 const raw=dnNotesAccess().getItem('gyanadaCCEDescriptiveNotes');if(!raw)throw Error('या खात्यात जुनी अनुक्रमांकानुसार नोंद उपलब्ध नाही.');
 const old=JSON.parse(raw);const roll=prompt('जुना अनुक्रमांक लिहा. विद्यार्थी यादी बदलली असल्यास जुना क्रमांक वेगळा असू शकतो.');if(roll===null)return false;if(!/^\d{1,6}$/.test(roll.trim())||Number(roll)<1)throw Error('योग्य जुना अनुक्रमांक लिहा.');
 const canonical=String(Number(roll))+'_'+(Number(term)===2?2:1);const rows=old[canonical]||(Number(term)===1?old[String(Number(roll))]:null);
 if(!Array.isArray(rows)||!rows.length)throw Error('या जुन्या अनुक्रमांक व सत्रासाठी नोंदी नाहीत.');
 if(Object.prototype.hasOwnProperty.call(d.claims,canonical))throw Error('या जुन्या नोंदींचा वापर आधीच झाला आहे.');
 const clean=rows.filter(x=>x&&String(x.text||x.note||'').trim()).map(x=>({subject:String(x.subject||x.category||x.group||''),text:String(x.text||x.note||'')}));if(!clean.length)throw Error('जुन्या नोंदी रिकाम्या आहेत.');
 if(!confirm('निवडलेला विद्यार्थी: '+student.name+'\nसत्र: '+term+'\nजुन्या नोंदी:\n'+clean.map(x=>x.subject+': '+x.text).join('\n')+'\n\nया सर्व नोंदी याच विद्यार्थ्याच्या असल्याची खात्री आहे का? खात्री नसेल तर रद्द करा.'))return false;
 if(!dnNotesById(id)||year!==dnNotesYear())throw Error('विद्यार्थी किंवा वर्ष बदलले.');
 const latest=dnNotesDb();if(Object.prototype.hasOwnProperty.call(latest.records,target)||Object.prototype.hasOwnProperty.call(latest.claims,canonical))throw Error('नोंदी बदलल्या आहेत. पुन्हा तपासा.');
 latest.records[target]=clean;latest.claims[canonical]=target;dnNotesAccess().setItem(dnNoteKey,JSON.stringify(latest));return true;
}
'''

DELETE=r'''// DN_CCE_STABLE_NOTES_20261126 — remove only the deleted student's stable records.
function dnCCEDeleteStudentNotes(id){
 try{
  if(!top.__dnAccount?.uid)throw Error('Account not approved');
  const key='dnCCEStudentNotesV3',raw=localStorage.getItem(key);if(!raw)return;
  const d=JSON.parse(raw);if(!d||d.version!==3||!d.records||typeof d.records!=='object'||Array.isArray(d.records))throw Error('Invalid notes data');
  let changed=false;for(const k of Object.keys(d.records)){let parts;try{parts=JSON.parse(k)}catch(e){continue}if(Array.isArray(parts)&&parts[0]===String(id)){delete d.records[k];changed=true}}
  // Keep legacy recovery claims to prevent reassigning a deleted student's old notes.
  if(changed)localStorage.setItem(key,JSON.stringify(d));
 }catch(e){console.warn('CCE notes cleanup:',e);alert('विद्यार्थी यादीतून काढला आहे. वर्णनात्मक नोंदींची स्वच्छता पूर्ण झाली नाही; त्या प्रगतीपत्रकात वापरल्या जाणार नाहीत.');}
}
'''

def patch_class(h):
    h=once(h,'function deleteStudent(id){',DELETE+'\nfunction deleteStudent(id){')
    h=once(h,'data.students=data.students.filter(s=>s.id!==id);\n persist();renderStudents();','data.students=data.students.filter(s=>s.id!==id);\n persist();if(st)dnCCEDeleteStudentNotes(id);renderStudents();')
    return h

def patch_cce(h):
    h=once(h,'let chosenDescriptiveNotes = {};',CORE+'\nlet chosenDescriptiveNotes = {};')
    h=block(h,'function notesStudentKey(){','function updateNotesHeader(){',r'''function notesStudentKey(){const id=dnNotesOldRosterId(document.getElementById('noteStudent')?.value);return id?dnNotesRecordKey(id,document.getElementById('noteTerm')?.value||1):'';}
function loadChosenNotes(){chosenDescriptiveNotes={};try{const key=notesStudentKey();if(key){const [id,year,term]=JSON.parse(key);chosenDescriptiveNotes[key]=dnNotesRead(id,term,year);}}catch(e){console.warn(e)}}''')
    h=once(h,'(chosenDescriptiveNotes[`${roll}_${term}`]||[])','dnNotesRead(dnNotesOldRosterId(roll),term)')
    h=block(h,'function saveChosenNotes(silent=false){','function notesForProgress(roll,term){',r'''function saveChosenNotes(silent=false){try{const key=notesStudentKey();if(!key)throw Error('विद्यार्थी निवडा.');const [id,year,term]=JSON.parse(key);dnNotesWrite(id,term,year,chosenDescriptiveNotes[key]||[]);dnNotesRefresh();const status=document.getElementById('notesStatus');if(status)status.textContent='वर्णनात्मक नोंदी जतन झाल्या.';return true}catch(e){if(!silent)alert(e.message);return false}}''')
    h=once(h,'function notesForProgress(roll,term){','function notesForProgress(roll,term,studentId){')
    h=once(h," let all={};try{all=JSON.parse(localStorage.getItem('gyanadaCCEDescriptiveNotes')||'{}')}catch(e){}\n const norm=",' const norm=')
    h=once(h,"const list=all[String(roll)+'_'+t]||(t===1?all[String(roll)]:null)||[];","const list=dnNotesRead(studentId===undefined?dnNotesOldRosterId(roll):studentId,t);")
    # Result roster: keep original marks behavior; pass the master ID separately for notes.
    h=once(h,"const tr=document.createElement('tr');tr.className='gy-roster-row';","const tr=document.createElement('tr');tr.className='gy-roster-row';tr.dataset.dnStudentId=String(st.id||'');")
    h=once(h,'gySelectRosterStudent(name,kind,target);','window.dnCCEProgressStudentId=String(st.id||\'\');gySelectRosterStudent(name,kind,target);')
    h=once(h,"const notes=typeof notesForProgress==='function'?notesForProgress(roll,term):{};","const notes=typeof notesForProgress==='function'?notesForProgress(roll,term,dnNotesProgressId(roll)):{};")
    h=once(h,"const student=roster[roll-1];\n  const values={};","const student=roster[roll-1];\n  const master=dnNotesById(dnNotesProgressId(roll));if(!master)return null;\n  const values={};")
    h=once(h,"values.student=String(student.name||'').trim();values.roll=String(roll);","values.student=String(master.name||'').trim();values.roll=String(roll);")
    h=once(h,"return {type:'GY_PROGRESS_FILL_V30',key:String(roll)+'|'+values.student,values};","return {type:'GY_PROGRESS_FILL_V30',key:dnNotesRecordKey(master.id,1),values};")
    h=once(h,"if(e.data?.type==='GY_PROGRESS_READY_V30')schedule()","if(e.source===get(frameId)?.contentWindow&&e.data?.type==='GY_PROGRESS_READY_V30')schedule()")
    h=once(h,'window.gySyncProgressGradesAndNotes=schedule;','window.gySyncProgressGradesAndNotes=function(){send();schedule()};')
    # Select actual row rather than first occurrence of the same name.
    h=once(h,'function select(name){\n  var row=Array.from(document.querySelectorAll(\'#studentRoster tr\')).find(function(r){return r.querySelector(\'.gy-student-heading strong\')?.textContent.trim()===name});',"function select(name,id){\n  var row=Array.from(document.querySelectorAll('#studentRoster tr')).find(function(r){return r.dataset.dnStudentId===id});")
    h=once(h,'function refresh(name,printing){\n  if(!select(name))return;','function refresh(name,printing,id){\n  if(!dnNotesById(id)||!select(name,id))return;')
    h=once(h,"function preview(name){refresh(name,false)}\n function download(name){refresh(name,true)}","function preview(name,id){refresh(name,false,id)}\n function download(name,id){refresh(name,true,id)}")
    h=once(h,'view.onclick=function(){preview(name)};','view.onclick=function(){preview(name,row.dataset.dnStudentId)};')
    h=once(h,'dl.onclick=function(){download(name)};','dl.onclick=function(){download(name,row.dataset.dnStudentId)};')
    h=once(h,"window.dispatchEvent(new Event('change'));\n   if(printing)","window.gySyncProgressGradesAndNotes?.();\n   if(printing)")
    # Main visible descriptive notebook.
    h=once(h,"const state={roll:0,subject:'',view:'roster',draft:[],term:'1'};","const state={roll:0,id:'',year:'',subject:'',view:'roster',draft:[],term:'1'};")
    h=block(h,'function records(){\n const base=','function getClass(st){',"function records(){return dnNotesMaster();}")
    h=block(h,"function saved(){try{return JSON.parse(localStorage.getItem('gyanadaCCEDescriptiveNotes')||'{}')}catch(_){return {}}}","function root(){return $('gyNotesWorkflow');}",r'''function hydrate(){state.draft=dnNotesRead(state.id,state.term,state.year).map(x=>({subject:cat(x.subject)||x.subject,text:x.text})).filter(x=>subjects.includes(x.subject));}
function store(){try{dnNotesWrite(state.id,state.term,state.year,state.draft);dnNotesRefresh();return true;}catch(e){alert('नोंदी जतन झाल्या नाहीत: '+e.message);return false;}}''')
    h=once(h,"function title(){return esc(records()[state.roll-1]?.name||'');}","function title(){return esc(dnNotesById(state.id)?.name||'');}")
    h=once(h,"function rosterView(){state.view='roster';","function rosterView(){state.view='roster';state.id='';state.draft=[];")
    h=once(h,"data-roll=\"'+x.roll+'\">वर्णनात्मक नोंदी","data-roll=\"'+x.roll+'\" data-student-id=\"'+esc(x.st.id)+'\">वर्णनात्मक नोंदी")
    h=once(h,"state.roll=+b.dataset.roll;state.term=$('gyNWTerm').value;hydrate();subjectView()","state.roll=+b.dataset.roll;state.id=b.dataset.studentId;state.year=dnNotesYear();state.term=$('gyNWTerm').value;if(!dnNotesById(state.id)){rosterView();return;}hydrate();subjectView()")
    h=once(h,'const student=records()[state.roll-1]||{};','const student=dnNotesById(state.id);if(!student){alert(\'विद्यार्थी यादीत नाही.\');rosterView();return;}')
    # one save button; optional explicit send and manual legacy recovery, no auto assignment.
    old='<button class="gyNWPrimary" id="gyNWSave">विद्यार्थ्याच्या नोंदी जतन करा</button>'
    new='<button class="gyNWPrimary" id="gyNWSave">सेव्ह करा</button><button class="gyNWPrimary" id="gyNWSend">प्रगतीपत्रकात पाठवा</button>'
    if h.count(old)!=2: raise SystemExit('STOP: notebook save buttons')
    h=h.replace(old,new)
    h=once(h,'<button class="gyNWBack" id="gyNWAnother">विषयांच्या यादीकडे या</button>','')
    h=once(h,"$('gyNWBackSubjects').onclick=subjectView;$('gyNWAnother').onclick=subjectView;","$('gyNWBackSubjects').onclick=subjectView;")
    h=once(h,"$('gyNWBackRoster').onclick=rosterView;root().querySelectorAll('[data-sub]')", "$('gyNWBackRoster').onclick=rosterView;const recovery=document.createElement('button');recovery.type='button';recovery.className='gyNWBack';recovery.textContent='जुन्या नोंदी तपासून आणा';recovery.onclick=()=>{try{if(dnNotesRecover(state.id,state.term,state.year)){hydrate();subjectView();dnNotesRefresh();}}catch(e){alert(e.message)}};root().appendChild(recovery);root().querySelectorAll('[data-sub]')")
    old="$('gyNWSave').onclick=save;"
    if h.count(old)!=2: raise SystemExit('STOP: notebook save handlers')
    h=h.replace(old,"$('gyNWSave').onclick=save;$('gyNWSend').onclick=sendToProgress;")
    h=once(h,"function save(){store();let e=$('gyNWStatus');if(e)e.textContent='निवडलेल्या नोंदी यशस्वीपणे जतन झाल्या.';}",r'''function save(){if(!store())return;let e=$('gyNWStatus');if(e)e.textContent='निवडलेल्या नोंदी यशस्वीपणे जतन झाल्या.';}
function sendToProgress(){if(!store())return;let e=$('gyNWStatus');if(e)e.textContent='नोंदी जतन झाल्या. या विद्यार्थ्याचे प्रगतीपत्रक उघडल्यावर नोंदी आपोआप दिसतील.';}
window.addEventListener('message',e=>{if(e.source!==parent||e.data?.type!=='GYANADA_STUDENT_DATA'||!root())return;if(state.view==='roster'||!dnNotesById(state.id))rosterView();});''')
    # Old competing progress renderer must use the same canonical reader, not roll-only storage.
    h=once(h,"const KEY='gyanadaCCEDescriptiveNotes', $=id=>document.getElementById(id);","const KEY=dnNoteKey, $=id=>document.getElementById(id);")
    a=h.index('function read(roll,term){',h.index('id="gy-progress-descriptive-sync-unified-20261117"'))
    b=h.index('function sync(){',a)
    h=h[:a]+"function read(roll,term){return notesForProgress(roll,term);}\n"+h[b:]
    h=once(h,"const oldSet=Storage.prototype.setItem;\nStorage.prototype.setItem=function(key,value){const result=oldSet.apply(this,arguments);if(key===KEY)schedule();return result};",'// Scoped storage saves call dnNotesRefresh explicitly.')
    # Refresh and hide an invalid current preview on student-list changes; no fallback to legacy roster.
    # This source has no final body tag; the last literal </body> is inside a print template.
    if not h.rstrip().endswith('</script>'):raise SystemExit('STOP: unexpected CCE document ending')
    h=h+r'''
<script id="dn-cce-stable-notes-refresh">(function(){
function refresh(){const id=window.dnCCEProgressStudentId;if(id&&!dnNotesById(id)){const f=document.getElementById('gyEmbedded2');if(f){f.style.display='none';try{for(const el of f.contentDocument.querySelectorAll('#approvedProgress [data-field]'))el.value='';}catch(e){}}const heading=document.getElementById('gyProgressPreviewHeading');if(heading)heading.hidden=true;}dnNotesRefresh();}
window.addEventListener('message',e=>{if(e.source===parent&&e.data?.type==='GYANADA_STUDENT_DATA')refresh();});
window.addEventListener('pageshow',refresh);
})();</script>'''
    return h

def patch_module(name,h):
    if MARK in h:return h
    if hashlib.sha256(h.encode()).hexdigest()!=EXPECTED[name]:raise SystemExit('STOP: source has changed; review '+name)
    return patch_cce(h) if name=='cceFrame' else patch_class(h)

def patch_shell(s):
    matches=list(re.finditer(r'(<script\b[^>]*\bid="dn-payload"[^>]*>)([A-Za-z0-9+/=]+)(</script>)',s))
    if len(matches)!=1:raise SystemExit('STOP: account isolation shell missing')
    m=matches[0];payload=base64.b64decode(m[2],validate=True).decode()
    for name in EXPECTED:
        ms=list(re.finditer(r'(\b'+name+r':\s*")([A-Za-z0-9+/=]+)(")',payload))
        if len(ms)!=1:raise SystemExit('STOP: module missing or duplicated: '+name)
        x=ms[0];old=base64.b64decode(x[2],validate=True).decode();new=patch_module(name,old)
        payload=payload[:x.start(2)]+base64.b64encode(new.encode()).decode()+payload[x.end(2):]
    return s[:m.start(2)]+base64.b64encode(payload.encode()).decode()+s[m.end(2):]


output=patch_shell(output)

# CCE + cumulative consolidated repair, appended to the existing account-isolation build.
DN_FINAL_HASHES={
 'cceFrame':'f80f6a5c61c236f93ab5b99f261f545d1155a09e35f6e59c29f9d7164ddad401',
 'classFrame':'b04d1a905eba4bf23ac2d5f891b0dd600e3baf486a01d0e705361eb93313d6a8',
 'cumulativeFrame':'826cfa5d9d08c6dc2e1959e129364acf326c2246a4f3e661c88167da028ab3eb',
}
DN_FINAL_MARK='DN_CCE_CUM_ID_20261126_V1'
DN_COMMON=r'''// DN_CCE_CUM_ID_20261126_V1 — scoped account storage only; no external calls.
const dnMarkKey='dnCCEStudentMarksV2';
const dnLegacyMarkKey='gyanadaCCEStudentScopedMarksV1';
function dnMarkReadJson(k,def){if(!top.__dnAccount?.uid)throw Error('शिक्षक खाते पडताळणी आवश्यक आहे.');const raw=localStorage.getItem(k);return raw===null?def:JSON.parse(raw);}
function dnMarkMaster(){const m=dnMarkReadJson('independentStudentManager_v1',{});return {students:Array.isArray(m.students)?m.students:[],deletedStudents:Array.isArray(m.deletedStudents)?m.deletedStudents:[]};}
function dnMarkNorm(v){return String(v??'').normalize('NFC').trim().replace(/\s+/g,' ');}
function dnMarkGrade(v){const s=dnMarkNorm(v), names=['पहिली','दुसरी','तिसरी','चौथी','पाचवी','सहावी','सातवी','आठवी'];for(let i=0;i<8;i++)if(s.includes(names[i]))return String(i+1);const m=s.replace(/[०-९]/g,d=>String('०१२३४५६७८९'.indexOf(d))).match(/(?:^|[^0-9])([1-8])(?:$|[^0-9])/);return m?m[1]:'';}
function dnMarkClass(st){return dnMarkGrade(st?.className||st?.class||st?.grade||st?.standard||st?.std);}
function dnMarkStudent(id){const matches=dnMarkMaster().students.filter(s=>s&&typeof s.id==='string'&&s.id===String(id));return matches.length===1?matches[0]:null;}
function dnMarkYear(){const field=document.getElementById('setupYear');const saved=dnMarkReadJson('gyanadaCCESchoolInfo',{});return dnMarkNorm(field?.value||saved.year||'2026-27');}
function dnMarkTerm(t){return Number(t)===2?2:1;}
function dnMarkRecordKey(id,g,y,t){return JSON.stringify([String(id),String(g),String(y),dnMarkTerm(t)]);}
function dnMarkDb(){const d=dnMarkReadJson(dnMarkKey,{version:2,records:{},claims:{},legacyYear:null});if(!d||d.version!==2||!d.records||typeof d.records!=='object'||Array.isArray(d.records)||!d.claims||typeof d.claims!=='object'||Array.isArray(d.claims))throw Error('गुणांच्या नोंदींची रचना अवैध आहे.');return d;}
function dnMarkPutDb(d){localStorage.setItem(dnMarkKey,JSON.stringify(d));}
function dnMarkClean(a){return Array.from({length:198},(_,i)=>{const v=String(a?.[i]??'').trim().replace(/[०-९]/g,d=>String('०१२३४५६७८९'.indexOf(d)));return /^(?:\d+(?:\.\d+)?)?$/.test(v)?v:'';});}
function dnMarkMigrate(d){
 const old=dnMarkReadJson(dnLegacyMarkKey,{}),m=dnMarkMaster();if(!old||typeof old!=='object'||Array.isArray(old))return false;
 let changed=false;
 if(!d.legacyYear){const y=dnMarkNorm(dnMarkReadJson('gyanadaCCESchoolInfo',{}).year);if(!y)return false;d.legacyYear=y;changed=true;}
 for(const [key,values] of Object.entries(old)){
  if(Object.prototype.hasOwnProperty.call(d.claims,key)||!Array.isArray(values))continue;
  let p;try{p=JSON.parse(key)}catch(e){continue}if(!Array.isArray(p)||p.length!==3||!['1','2'].includes(String(p[2])))continue;
  const [g0,n,t]=p,g=dnMarkGrade(g0),name=dnMarkNorm(n);if(!g||!name)continue;
  const match=m.students.filter(s=>s?.id&&dnMarkClass(s)===g&&dnMarkNorm(s.name)===name);
  // A deleted student may have been replaced with an identical name; never guess ownership.
  const deleted=m.deletedStudents.some(s=>dnMarkNorm(s?.name)===name&&(!dnMarkClass(s)||dnMarkClass(s)===g));
  if(deleted){d.claims[key]={blocked:true};changed=true;continue;}
  if(match.length!==1)continue;
  const target=dnMarkRecordKey(match[0].id,g,d.legacyYear,t);
  if(!Object.prototype.hasOwnProperty.call(d.records,target))d.records[target]=dnMarkClean(values);
  d.claims[key]={id:String(match[0].id),target};changed=true;
 }
 // Older summary snapshots are eligible only if they contain an explicit matching class and name.
 // Never infer student identity from an old roll number. Preserve the old stores unchanged.
 const rollRecords=dnMarkReadJson('gyanadaCCEAllStudentMarks',{});
 for(const [oldKey,r] of Object.entries(rollRecords||{})){
  const claim='roll:'+oldKey;if(Object.prototype.hasOwnProperty.call(d.claims,claim)||!Array.isArray(r?.marks))continue;
  const g=dnMarkGrade(r.gradeClass||r.className||r.class),n=dnMarkNorm(r.name),t=Number(r.term||(/_2$/.test(oldKey)?2:1));
  if(!g||!n||![1,2].includes(t))continue;
  const match=m.students.filter(s=>s?.id&&dnMarkClass(s)===g&&dnMarkNorm(s.name)===n);
  if(m.deletedStudents.some(s=>dnMarkNorm(s?.name)===n&&(!dnMarkClass(s)||dnMarkClass(s)===g))){d.claims[claim]={blocked:true};changed=true;continue;}
  if(match.length!==1)continue;const y=dnMarkNorm(r.year)||d.legacyYear,target=dnMarkRecordKey(match[0].id,g,y,t);
  if(!Object.prototype.hasOwnProperty.call(d.records,target))d.records[target]=dnMarkClean(r.marks);
  d.claims[claim]={id:String(match[0].id),target};changed=true;
 }
 return changed;
}
function dnMarkReadyDb(){const d=dnMarkDb();if(dnMarkMigrate(d))dnMarkPutDb(d);return d;}
function dnMarkGet(id,g,t,y=dnMarkYear()){if(!dnMarkStudent(id))return null;const d=dnMarkReadyDb(),a=d.records[dnMarkRecordKey(id,g,y,t)];return Array.isArray(a)?dnMarkClean(a):null;}
function dnMarkSet(id,g,t,y,values){const s=dnMarkStudent(id);if(!s||dnMarkClass(s)!==String(g))throw Error('विद्यार्थी किंवा इयत्ता बदलली आहे. पुन्हा निवडा.');const d=dnMarkReadyDb();d.records[dnMarkRecordKey(id,g,y,t)]=dnMarkClean(values);dnMarkPutDb(d);}
function dnMarkMetrics(values){if(!Array.isArray(values))return Array(9).fill(null);const a=dnMarkClean(values);const sum=x=>x.reduce((v,n)=>v+(Number(n)||0),0);return Array.from({length:9},(_,j)=>{const max=a.slice(j*22,j*22+11),got=a.slice(j*22+11,j*22+22);if(!got.some(v=>v!==''))return null;const m=sum(max),n=sum(got);if(m<=0)return null;const p=100*n/m;return {a:sum(got.slice(0,8)),b:sum(got.slice(8)),total:n,max:m,grade:p>=91?'अ-१':p>=81?'अ-२':p>=71?'ब-१':p>=61?'ब-२':p>=51?'क-१':p>=41?'क-२':''};});}
function dnMarkRemoveStudent(id){const d=dnMarkDb();let changed=false;for(const k of Object.keys(d.records)){let p;try{p=JSON.parse(k)}catch(e){continue}if(Array.isArray(p)&&p[0]===String(id)){delete d.records[k];changed=true;}}for(const [k,v] of Object.entries(d.claims)){if(v?.id===String(id)){d.claims[k]={blocked:true};changed=true;}}if(changed)dnMarkPutDb(d);}
'''
DN_CCE=r'''
function dnActiveMarks(){const w=window.gyActiveMarksStudent;if(!w?.id)return null;const s=dnMarkStudent(w.id);if(!s||dnMarkClass(s)!==w.grade||w.year!==dnMarkYear())return null;return w;}
function dnSaveMarks(){if(window.dnMarksLoading)return false;const w=dnActiveMarks();if(!w||document.getElementById('student')?.value!==w.name||document.getElementById('marksPage')?.classList.contains('hidden'))return false;const a=[...document.querySelectorAll('#rows input.mark')].map(x=>x.value);if(a.length!==198)return false;dnMarkSet(w.id,w.grade,currentTerm(),w.year,a);return true;}
function dnLoadMarks(){const w=dnActiveMarks();window.dnMarksLoading=true;try{const a=w?dnMarkGet(w.id,w.grade,currentTerm(),w.year):null;document.querySelectorAll('#rows input.mark').forEach((x,i)=>x.value=a?.[i]??'');recalc();}finally{window.dnMarksLoading=false;}}
function dnSummaryRender(){
 const $=id=>document.getElementById(id),body=$('summaryRows');if(!body)return;
 const g=dnMarkGrade($('gySummaryGrade')?.value||$('setupClass')?.value),t=dnMarkTerm($('gySummaryTerm')?.value||$('marksTermSelect')?.value),y=dnMarkYear();
 const list=dnMarkMaster().students.filter(s=>s?.id&&dnMarkClass(s)===g);const db=dnMarkReadyDb();let filled=0;const frag=document.createDocumentFragment();
 list.forEach((s,i)=>{const a=db.records[dnMarkRecordKey(s.id,g,y,t)],metrics=dnMarkMetrics(a),cells=[i+1,s.name,t===1?'प्रथम':'द्वितीय'];let max=0,got=0,valid=0;for(const m of metrics){if(!m){cells.push('','','','');continue;}cells.push(m.a,m.b,m.total,m.grade);max+=m.max;got+=m.total;valid++;}if(valid)filled++;cells.push(valid?max:'',valid?got:'',max?(100*got/max).toFixed(1)+'%':'',max?gradeFor(100*got/max):'');const tr=document.createElement('tr');cells.forEach((v,j)=>{const td=document.createElement('td');td.textContent=String(v??'');if(j===1)td.style.textAlign='left';tr.append(td)});frag.append(tr);});body.replaceChildren(frag);
 const put=(id,v)=>{const e=$(id);if(e)e.textContent=v||''};put('gySummaryImportStatusV14','विद्यार्थी: '+list.length+' | गुण भरलेले: '+filled+' | सत्र: '+(t===1?'प्रथम':'द्वितीय'));put('sumTerm','सत्र: '+(t===1?'प्रथम':'द्वितीय'));put('sumSchool',$('setupSchool')?.value||'शाळेचे नाव');put('sumYear',y);put('sumUdise',$('setupUdise')?.value);put('sumTeacher',$('setupTeacher')?.value);put('sumClass',['','पहिली','दुसरी','तिसरी','चौथी','पाचवी','सहावी','सातवी','आठवी'][+g]||'');
}
function dnCopyMax(from,to,g,t){const source=dnMarkGet(from,g,t),target=dnMarkGet(to,g,t)||dnMarkClean([]);if(!source||!source.some((v,i)=>i%22<11&&v!==''))return false;for(let i=0;i<198;i++)if(i%22<11)target[i]=source[i];dnMarkSet(to,g,t,dnMarkYear(),target);return true;}
function dn58Get(key,st,g,data){if(Object.prototype.hasOwnProperty.call(data,key))return data[key];const m=dnMarkMaster(),old=String(st.legacyId||'');if(!old||old===st.id||m.deletedStudents.length)return {};const matches=m.students.filter(s=>dnMarkClass(s)===g&&String(s.grNumber||s.grNo||s.gr||s.roll||s.id||'').trim()===old);if(matches.length!==1||matches[0].id!==st.id)return {};const r=data[g+'|'+old];if(r&&typeof r==='object'){data[key]={...r};localStorage.setItem('gyanada58ResultMarksV2',JSON.stringify(data));return data[key];}return {};}
'''

def dn_script(h,id,js):
    m=re.search(r'<script(?:\s|>)',h,re.I)
    if not m:raise SystemExit('STOP: no script insertion anchor: '+id)
    return h[:m.start()]+f'<script id="{id}">'+js+'</script>\n'+h[m.start():]

def dn_remove_script(h,id):
    pattern=r'<script\b[^>]*\bid="'+re.escape(id)+r'"[^>]*>.*?</script>'
    m=list(re.finditer(pattern,h,re.S|re.I))
    if len(m)!=1:raise SystemExit('STOP: unexpected script '+id)
    return h[:m[0].start()]+h[m[0].end():]

def dn_cce_final(h):
    h=dn_script(h,'dn-cce-id-marks-core',DN_COMMON+DN_CCE)
    h=block(h,'function storeCurrentStudent(){try{','function marksTermChanged(){','function storeCurrentStudent(){return dnSaveMarks();}\nfunction loadStudentMarks(id){return dnLoadMarks();}')
    h=block(h,'function saveData(){\n const data={school:','function clearMarks(){',"function saveData(){if(!dnSaveMarks()){alert('प्रथम विद्यार्थी निवडा.');return;}alert('गुण सेव्ह झाले.');}\nfunction loadData(){return;} // No old roll-only cache loading.")
    h=block(h,'function renderSummary(){\n const tbody=','const progressSubjects=', 'function renderSummary(){return dnSummaryRender();}\n')
    h=block(h,'function firstTermGrades(roll,term=1){','function renderProgress(){',r'''function firstTermGrades(roll,term=1,studentId){const out=Array(10).fill('');const id=studentId||dnNotesOldRosterId(roll),s=dnMarkStudent(id);if(!s)return out;const metrics=dnMarkMetrics(dnMarkGet(id,dnMarkClass(s),term));[0,1,2,3,4,6,7,8,9].forEach((target,i)=>out[target]=metrics[i]?.grade||'');return out;}''')
    h=once(h,"values.class=value('setupClass')||value('gyResultClass');","values.class=dnMarkClass(master);")
    h=once(h,"firstTermGrades(roll,term):[];","firstTermGrades(roll,term,master.id):[];")
    # Remove legacy roll snapshots and use exactly the same summary renderer for display and print.
    h=block(h,' function snapshotCurrent(){',' function init(){\n  const root=$(\'summaryPage\');', ' function snapshotCurrent(){return;}\n function render(){return dnSummaryRender();}')
    h=once(h,"const KEY='gyanadaCCEAllStudentMarks', SNAP='gyanadaCCEGradeSnapshotsV17';","const KEY=dnMarkKey, SNAP='gyanadaCCEGradeSnapshotsV17';")
    # Marks roster and actions — stable IDs, including equal names.
    h=once(h,"const n=nameOf(s);if(!n||seen.has(n))return false;seen.add(n);return true","const n=String(s.id||'');if(!nameOf(s)||!n||seen.has(n))return false;seen.add(n);return true")
    h=once(h,"function showList(){\n const p=by('gyTopMarksPage')", "function showList(){\n window.gyActiveMarksStudent=null;\n const p=by('gyTopMarksPage')")
    h=once(h,"if(!list[i])return;\n if(by('setupClass'))", "if(!list[i]||!dnMarkStudent(list[i].id))return;\n window.gyActiveMarksStudent=null;\n if(by('setupClass'))")
    h=once(h,"window.gyActiveMarksStudent={grade:activeGrade,name:nameOf(list[i]),index:i};","window.gyActiveMarksStudent={id:String(list[i].id),grade:activeGrade,name:nameOf(list[i]),year:dnMarkYear(),index:i};")
    h=block(h,'function forward(i){\n if(i>=list.length-1)return;','function init(){\n const top=by(\'gyTopMarksPage\')',r'''function forward(i){if(i>=list.length-1||!list[i]||!list[i+1])return;const status=by('gyMarksStatus'),term=currentTerm();try{status.textContent=dnCopyMax(list[i].id,list[i+1].id,activeGrade,term)?nameOf(list[i])+' यांची एकूण गुण विभागणी पुढील विद्यार्थ्याला दिली.':'प्रथम या विद्यार्थ्याचे गुणपत्रक भरून सेव्ह करा.';}catch(e){status.textContent=e.message;}}''')
    h=once(h,"if(e.data?.type==='GYANADA_STUDENT_DATA'){updateClasses();if(by('gyStudentMarksList').style.display!=='none')render()}","if(e.source===parent&&e.data?.type==='GYANADA_STUDENT_DATA'){updateClasses();if(window.gyActiveMarksStudent&&!dnActiveMarks())showList();else if(by('gyStudentMarksList').style.display!=='none')render()}")
    h=dn_remove_script(h,'gy-marks-student-isolation')
    # Original maximum-copy panel must also read and write the stable-ID store.
    h=block(h," function saved(){try{return JSON.parse(localStorage.getItem('gyanadaCCEAllStudentMarks')||'{}')}catch(e){return {}}}", ' function refresh(){const p=document.getElementById(\'gyCopyMaxPanel\')',r''' function roster(){return dnMarkMaster().students.filter(s=>s?.id&&dnMarkClass(s)===grade()).map((s,i)=>({id:String(i+1),studentId:s.id,name:String(s.name||'')}));}''')
    h=block(h," function copy(){const p=document.getElementById('gyCopyMaxPanel')", " function init(){const page=document.getElementById('marksPage');if(!page||document.getElementById('gyCopyMaxPanel'))",r''' function copy(){const p=document.getElementById('gyCopyMaxPanel'),choice=p.querySelector('select').value,status=p.querySelector('.gyCopyStatus'),list=roster(),from=list[0];if(!from||!choice)return;try{dnSaveMarks();const targets=list.filter(x=>x.id!=='1'&&(choice==='all'||x.id===choice));let n=0;for(const s of targets)if(dnCopyMax(from.studentId,s.studentId,grade(),term()))n++;status.textContent=n?n+' विद्यार्थ्यांना एकूण गुण विभागणी दिली. प्राप्त गुण सुरक्षित आहेत.':'प्रथम गुण सेव्ह करा.';}catch(e){status.textContent=e.message;}}
 window.gyApplyCopiedFirstMax=function(){return;};''')
    # Result-review reads only canonical records and counts all distinct IDs.
    h=once(h,"const name=nameOf(s),id=norm(name);if(!id||seen.has(id))continue;seen.add(id);list.push({name,gender:gender(s.gender||s.sex||s.लिंग)})","const name=nameOf(s),id=String(s.id||'');if(!name||!id||seen.has(id))continue;seen.add(id);list.push({id,name,gender:gender(s.gender||s.sex||s.लिंग)})")
    h=once(h,"const scoped=read('gyanadaCCEStudentScopedMarksV1')||{};","const scoped=dnMarkReadyDb().records;")
    h=once(h,"scoped[JSON.stringify([selected,st.name,term])]","scoped[dnMarkRecordKey(st.id,selected,dnMarkYear(),term)]")
    h=once(h,"['gyanadaTeacherProfile','gyanadaCCEStudentScopedMarksV1'].includes(e.key)","['gyanadaTeacherProfile',dnMarkKey].includes(e.key)")
    # Do not restore older roll-keyed marks from hidden helpers. Keep old keys as archival data.
    h=once(h,"function cleanSaved(){\n try{\n  const key='gyanadaCCEAllStudentMarks'", "function cleanSaved(){return;/* archival records not edited */}\nfunction dnUnusedLegacyCleanSaved(){\n try{\n  const key='gyanadaCCEAllStudentMarks'")
    # 5th/8th result table: actual stable IDs, guarded migration from previous GR-keyed rows.
    h=once(h,"id:String(s.grNumber||s.grNo||s.gr||s.roll||s.id||'').trim()", "id:String(s.id||'').trim(),legacyId:String(s.grNumber||s.grNo||s.gr||s.roll||s.id||'').trim()")
    h=once(h,"if(!s.name)return false;const k=s.id||s.name;", "if(!s.name||!s.id)return false;const k=s.id;")
    h=once(h,"let r=data[key(st)]||{};return f.endsWith('Max')", "let r=dn58Get(key(st),st,$('gy58Class').value,data);return f.endsWith('Max')")
    # The existing data cache is refreshed before an input, to avoid resurrecting deleted rows.
    h=once(h,"let k=el.dataset.gy58Key,f=el.dataset.gy58Field;data[k]??={};", "let k=el.dataset.gy58Key,f=el.dataset.gy58Field;data=read(KEY);if(!dnMarkStudent(k.slice(k.indexOf('|')+1)))return;data[k]??={};")
    # Remove two orphan listeners from the older 5/8 module; the real notes module already has its own listeners.
    h=once(h,"window.addEventListener('message',e=>{if(e.data?.type==='GYANADA_STUDENT_DATA'){window.gyClassStudentData=e.data.data;setTimeout(()=>{if(state.view==='roster'&&root())rosterView()},60)}});\nwindow.addEventListener('storage',e=>{if(state.view==='roster'&&root())rosterView()});",'')
    h=once(h,"id:String(s.grNumber||s.grNo||s.gr||s.id||s.roll||'').trim(),attendanceNo:","id:String(s.id||'').trim(),legacyId:String(s.grNumber||s.grNo||s.gr||s.id||s.roll||'').trim(),attendanceNo:")
    h=once(h,"let k=s.id||s.name;if(!s.name||seen.has(k))return false;","let k=s.id;if(!s.name||!k||seen.has(k))return false;")
    h=once(h,"const recordKey=g+'|'+(st.id||st.name),r=data()[recordKey]||{},cfg=", "const recordKey=g+'|'+st.id,r=dn58Get(recordKey,st,g,data()),cfg=")
    h=once(h,"if(k){const all=data();all[recordKey]", "if(k){if(!dnMarkStudent(st.id))return;const all=data();all[recordKey]")
    h=once(h,"const select=by('gy58MarksStudent'),out=by('gy58MarksSheet'),g=by('gy58Class')?.value||'';", "const select=by('gy58MarksStudent'),out=by('gy58MarksSheet'),g=by('gy58Class')?.value||'';")
    h=once(h,"const list=students(),old=select.value;", "const list=students(),old=select.selectedOptions[0]?.dataset.studentId||'';")
    h=once(h,'''list.map((st,i)=>'<option value="'+i+'">'+clean(st.name)+'</option>').join('');
 if(old!==''&&list[Number(old)])select.value=old;''','''list.map((st,i)=>'<option data-student-id="'+clean(st.id)+'" value="'+i+'">'+clean(st.name)+'</option>').join('');
 const idx=list.findIndex(st=>st.id===old);if(idx>=0)select.value=String(idx);''')
    # User selects an option before certificate() rebuilds it: preserve selection by actual ID above.
    h=once(h,"const students=source().filter(s=>classOf(s)===selected);", "const students=dnMarkMaster().students.filter(s=>classOf(s)===selected);")
    return h

def dn_class_final(h):
    h=dn_script(h,'dn-class-cce-cleanup-core',DN_COMMON)
    h=once(h,'persist();if(st)dnCCEDeleteStudentNotes(id);renderStudents();',r'''persist();if(st){dnCCEDeleteStudentNotes(id);try{dnMarkRemoveStudent(id);const a=dnMarkReadJson('gyanada58ResultMarksV2',{});let changed=false;for(const k of Object.keys(a)){if(k.slice(k.indexOf('|')+1)===String(id)){delete a[k];changed=true;}}if(changed)localStorage.setItem('gyanada58ResultMarksV2',JSON.stringify(a));}catch(e){console.warn(e);alert('विद्यार्थी काढला आहे. जुन्या गुणांची स्वच्छता पूर्ण झाली नाही; ते नवीन विद्यार्थ्यास वापरले जाणार नाहीत.');}}renderStudents();''')
    return h

DN_CUM=r'''
function dnCumReadNotes(id,term,year){const d=dnMarkReadJson('dnCCEStudentNotesV3',{}),k=JSON.stringify([String(id),String(year),dnMarkTerm(term)]);const a=d.records?.[k];return Array.isArray(a)?a:null;}
function dnCumCategory(v){const x=dnMarkNorm(v).replace(/[\s\-_/.,:ः()]/g,'');return /आवड|छंद/.test(x)?'hobby':/सुधार/.test(x)?'improve':/व्यक्तिमत्त्व|व्यक्तिमत्व/.test(x)?'person':/विशेषगुण|विशेषप्रगती/.test(x)?'special':'';}
function dnCumRefresh(){
 const selected=window.gyCumCurrentStudent;if(!selected?.id||!document.body.classList.contains('gy-cum-viewer-mode'))return;
 const st=dnMarkStudent(selected.id);if(!st)return;
 const cls=dnMarkClass(st),year=dnMarkYear();if(!cls||!year)return;
 const db=dnMarkReadyDb(),byGrade={};
 // The cumulative form has one row per grade and term. Use its recorded academic year if known,
 // otherwise the latest identified record for that grade. Never use the teacher's first class.
 for(const [key,a] of Object.entries(db.records)){let p;try{p=JSON.parse(key)}catch(e){continue}if(!Array.isArray(p)||p[0]!==String(st.id)||!dnMarkGrade(p[1])||!Array.isArray(a))continue;const [id,g,y,t]=p;const cell=document.querySelector('#body6 [data-class="'+g+'"][data-term="1"][data-col="0"]');const existing=dnMarkNorm(cell?.textContent);if(existing&&existing!==String(y)&&g!==cls)continue;const prior=byGrade[g];if(!prior||String(y)>prior)byGrade[g]=String(y);}
 byGrade[cls]=year;
 let auto=dnMarkReadJson('dnCumCceAutoV1',{}),studentAuto=auto[st.id]||{},changed=false,metaChanged=false;
 function fill(page,g,t,col,value,authoritative){const cell=document.querySelector('#body'+page+' [data-class="'+g+'"][data-term="'+t+'"][data-col="'+col+'"]');if(!cell)return;const k=JSON.stringify([page,g,t,col]),old=studentAuto[k],cur=dnMarkNorm(cell.textContent);if(!authoritative)return;const v=String(value??'');if(v){if(cur!==v){cell.textContent=v;changed=true;}if(old!==v){studentAuto[k]=v;metaChanged=true;}}else if(old!==undefined){if(cur===dnMarkNorm(old)){cell.textContent='';changed=true;}delete studentAuto[k];metaChanged=true;}}
 for(const [g,y] of Object.entries(byGrade)){
  for(const t of [1,2]){
   const a=db.records[dnMarkRecordKey(st.id,g,y,t)],metrics=dnMarkMetrics(a);if(Array.isArray(a)){
    for(let i=0;i<9;i++)fill(i<6?6:7,g,t,i<6?i+3:i-4,metrics[i]?.grade||'',true);
    if(metrics.some(Boolean)){const yr=document.querySelector('#body6 [data-class="'+g+'"][data-term="1"][data-col="0"]');if(yr&&!dnMarkNorm(yr.textContent)){yr.textContent=y;changed=true;}}
   }
   const uniqueGradeForYear=y===year?g===cls:Object.entries(byGrade).filter(([,v])=>v===y).length===1;const notes=uniqueGradeForYear?dnCumReadNotes(st.id,t,y):null;if(notes!==null){const groups={};for(const n of notes){const c=dnCumCategory(n?.subject||n?.category),v=dnMarkNorm(n?.text||n?.note);if(c&&v)(groups[c]||(groups[c]=new Set())).add(v);}
    for(const [page,col,c] of [[8,2,'special'],[8,3,'improve'],[9,3,'hobby'],[9,4,'person']])fill(page,g,t,col,[...(groups[c]||[])].join(' ; '),true);
   }
  }
 }
 if(metaChanged){auto[st.id]=studentAuto;localStorage.setItem('dnCumCceAutoV1',JSON.stringify(auto));}
 if(changed){window.dnCumSaveCurrent?.();const e=document.getElementById('gyanadaSyncStatus');if(e)e.textContent='CCE मधील श्रेणी व वर्णनात्मक नोंदी योग्य इयत्ता आणि सत्रात भरल्या.';}
}
window.dnCumRefresh=dnCumRefresh;
'''

def dn_cum_final(h):
    h=dn_script(h,'dn-cum-id-core',DN_COMMON+DN_CUM)
    # Disable all three competing name/roll-based CCE import scripts; keep attendance and all print templates.
    for id in ['gy-cumulative-descriptive-import-2026','gy-cumulative-readonly-descriptive-v2','gy-cumulative-cce-subject-grade-autofill-2026']:
        h=dn_remove_script(h,id)
    # This legacy anonymous script writes notes to tbody's first row. Remove the whole specific block.
    a=h.index('<script>\n(function(){\nlet sync=null,studentData=null,profile=null;')
    b=h.index('</script>',a)+len('</script>')
    if 'function fillNotes(name)' not in h[a:b] or 'function syncGradePagesForStudent' not in h[a:b]:raise SystemExit('STOP: legacy cumulative bridge mismatch')
    h=h[:a]+h[b:]
    # Stable selection and reset of previous student's cells before restoring the selected student's own record.
    h=once(h,'function cells(){return [...document.querySelectorAll(\'main .page [contenteditable="true"],main .page input,main .page select,main .page textarea\')]}', '''const dnCumBaseline=[...document.querySelectorAll('main .page [contenteditable="true"],main .page input,main .page select,main .page textarea')].filter(e=>!e.closest('#p4,#p5')).map(e=>[e,e.matches('input,textarea,select')?e.value:e.innerHTML]);
function cells(){return [...document.querySelectorAll('main .page [contenteditable="true"],main .page input,main .page select,main .page textarea')];}
function dnCumReset(){for(const [e,v] of dnCumBaseline){if(e.isConnected)dnCumPut(e,v);}}
function dnCumValue(e){return e.matches('input,textarea,select')?e.value:e.innerHTML;}
function dnCumPut(e,v){if(e.matches('input,textarea,select'))e.value=v;else e.innerHTML=v;}
function dnCumCoord(e){const page=e.closest('.page')?.id,cls=e.dataset.class,term=e.dataset.term,col=e.dataset.col;return page&&cls&&term&&col!==undefined?JSON.stringify([page,cls,term,col]):null;}
function dnCumV2Key(o){return 'gy-cum-student-v2-'+encodeURIComponent(String(o.id));}
function dnCumWarn(){const e=document.getElementById('gyanadaSyncStatus');if(e)e.textContent='जुन्या संचयी नोंदींची रचना बदलली आहे; मूळ प्रत सुरक्षित आहे. कृपया पूर्वीची हस्तलिखित माहिती तपासा.';console.warn('Legacy cumulative layout does not match; archival snapshot untouched.');}
''')
    h=block(h,'function save(){if(!selected||restoring)return;','function getClasses(p){',r'''function save(){if(!selected||restoring||!dnMarkStudent(selected.id))return;window.dnCumAadhaarBlank?.();try{const fields=cells(),coords={};for(const e of fields){const k=dnCumCoord(e);if(k)coords[k]=dnCumValue(e);}localStorage.setItem(dnCumV2Key(selected),JSON.stringify({version:2,fields:fields.map(dnCumValue),coords}));}catch(e){console.warn('Cumulative save',e);}}
function restore(){restoring=true;try{const fields=cells();const fresh=dnMarkReadJson(dnCumV2Key(selected),null);const legacy=dnMarkReadJson(key(selected),null);if(fresh?.version===2){if(Array.isArray(fresh.fields)&&fresh.fields.length===fields.length)fields.forEach((e,i)=>dnCumPut(e,fresh.fields[i]));else dnCumWarn();for(const e of fields){const k=dnCumCoord(e);if(k&&Object.prototype.hasOwnProperty.call(fresh.coords||{},k))dnCumPut(e,fresh.coords[k]);}return;}if(Array.isArray(legacy)){if(legacy.length===fields.length){fields.forEach((e,i)=>dnCumPut(e,legacy[i]));}else{dnCumWarn();}return;}
// The previous explicit save sometimes used a GR/name key. Only recover when the owner is unambiguous.
const m=dnMarkMaster(),sel=el('gyanadaStudentSelect'),label=sel?.selectedOptions[0]?.textContent.trim()||'';if(!label)return;const oldId=String(selected.generalRegister||selected.gr||selected.id),prefix='gyanadaCumulativeBrowserSavedV1:';const stable=dnMarkReadJson(prefix+selected.id+'|'+label,null);let manual=stable;if(!manual&&m.deletedStudents.length===0&&m.students.filter(s=>String(s.generalRegister||s.gr||s.id)===oldId).length===1)manual=dnMarkReadJson(prefix+oldId+'|'+label,null);if(Array.isArray(manual?.fields)){if(manual.fields.length===fields.length&&manual.fields.every((x,i)=>x.i===i&&x.kind===fields[i].tagName)){manual.fields.forEach((x,i)=>dnCumPut(fields[i],x.value));}else dnCumWarn();}}catch(e){console.warn('Cumulative restore',e);}finally{restoring=false;}}
''')
    h=once(h,"function open(o){\n selected=o;", "function open(o){\n if(!o?.id||!dnMarkStudent(o.id))return;if(selected)save();restoring=true;dnCumReset();selected=o;window.gyCumCurrentStudent=o;")
    h=once(h,"const opts=[...original.options];const target=opts.find(x=>txt(x.textContent).includes(nameOf(o)));if(target){original.value=target.value;original.dispatchEvent(new Event('change',{bubbles:true}))}","const i=roster.findIndex(x=>x.id===o.id);if(i>=0&&[...original.options].some(x=>x.value===String(i))){original.value=String(i);}")
    h=once(h,"page=1;window.gyCumCurrentStudent=o;restore();setTimeout(()=>{if(window.gyCumRefreshGrades)window.gyCumRefreshGrades()},100);window.dispatchEvent(new Event('gyCumStudentOpened'));if(window.gyCumCceSnapshot&&window.gyCumApplySessionGrades)window.gyCumApplySessionGrades(o,window.gyCumCceSnapshot);if(window.gyCumCceSnapshot&&window.gyCumApplyCceGrades)window.gyCumApplyCceGrades(o,window.gyCumCceSnapshot);", "page=1;if(original)original.dispatchEvent(new Event('change',{bubbles:true}));window.dnCumSwitchPage4?.();restore();restoring=true;window.dnCumFillSelected?.();restoring=false;window.dispatchEvent(new Event('gyCumStudentOpened'));dnCumRefresh();")
    h=once(h,"window.gyCumReturn=()=>{save();selected=null;", "window.dnCumSaveCurrent=save;window.gyCumReturn=()=>{save();selected=null;window.gyCumCurrentStudent=null;")
    h=once(h,"if(page===6||page===7){if(window.gyCumRefreshGrades)window.gyCumRefreshGrades();setTimeout(()=>window.gyCumSyncActualGrades?.(),180)}", "if(page>=6&&page<=9)dnCumRefresh();")
    h=once(h,"function updateRoster(arr){if(!Array.isArray(arr))return;roster=arr;if(openedList)list()}","function updateRoster(arr){if(!Array.isArray(arr))return;roster=arr;if(selected&&!arr.some(s=>s.id===selected.id)){selected=null;window.gyCumCurrentStudent=null;document.body.classList.remove('gy-cum-viewer-mode');document.body.classList.add('gy-cum-dashboard-mode');showLaunch();}if(openedList)list()}")
    h=once(h,"function switchStudent(){const key=selectedKey();", "window.dnCumSwitchPage4=()=>switchStudent();function switchStudent(){const key=selectedKey();")
    h=once(h,"function load(){busy=true;convert();let data=null;", "function load(){busy=true;convert();tbody.querySelectorAll('select').forEach(s=>s.value='');let data=null;")
    h=once(h,"function picker(){if(document.getElementById('gyanadaStudentPicker'))return;", "window.dnCumFillSelected=()=>{const st=window.gyCumCurrentStudent;if(!st?.id)return;let info={};try{info=JSON.parse(localStorage.getItem('gyanadaCCESchoolInfo')||'{}')}catch(e){}fill(st,info);};function picker(){if(document.getElementById('gyanadaStudentPicker'))return;")
    # Prevent a delayed old manual-save restore from overwriting the canonical values or another pupil.
    h=once(h,"document.addEventListener('change',e=>{if(e.target?.id==='gyanadaStudentSelect')setTimeout(restore,600)});\nwindow.addEventListener('message',e=>{if(e.data?.type==='GYANADA_STUDENT_DATA')setTimeout(restore,1200)});\nsetTimeout(()=>{position();restore()},1500);", "window.addEventListener('gyCumStudentOpened',()=>{position();dnCumRefresh();});\nsetTimeout(position,1500);")
    # Only one active ID-based browser save. Preserve old manual-save data as a fallback when autosave is absent.
    h=once(h,"const id=student&&(student.generalRegister||student.gr||student.id||student.name);\n return id?String(id)+'|'+name:(name||'default');", "const id=student?.id;\n return id?String(id)+'|'+name:'no-selection';")
    h=once(h,"function save(){try{const key=prefix+studentKey();", "function save(){if(!window.gyCumCurrentStudent?.id)return;try{window.dnCumSaveCurrent?.();const key=prefix+studentKey();")
    # Page7 attendance retains its original editable attribute for legacy index order.
    h=once(h,"cell.textContent=values[col];cell.contentEditable='false';cell.dataset.gyPage7Auto='true';", "cell.textContent=values[col];cell.setAttribute('inert','');cell.dataset.gyPage7Auto='true';")
    h=once(h,"const student=snapshot.students?.[Number(select.value)];if(!student)return;", "const selected=window.gyCumCurrentStudent;const student=snapshot.students?.find(s=>s.id===selected?.id);if(!student)return;")
    # Re-sync synchronously before PDF, and on view entry / focus / relevant message.
    h=once(h,'function gyCumNativePrint(all){window.dnCumAadhaarBlank?.();','function gyCumNativePrint(all){window.dnCumAadhaarBlank?.();window.dnCumRefresh?.();')
    h+='''\n<script id="dn-cum-cce-refresh-events">(function(){function sync(){try{dnCumRefresh()}catch(e){console.warn('CCE cumulative sync',e)}}window.addEventListener('gyCumStudentOpened',sync);window.addEventListener('focus',sync);window.addEventListener('beforeprint',sync);window.addEventListener('message',e=>{if(e.source===parent&&['GYANADA_STUDENT_DATA','GYANADA_CCE_SYNC'].includes(e.data?.type))setTimeout(sync,100)});})();</script>'''
    return h

def dn_final_shell(s):
    m=list(re.finditer(r'(<script\b[^>]*\bid="dn-payload"[^>]*>)([A-Za-z0-9+/=]+)(</script>)',s))
    if len(m)!=1:raise SystemExit('STOP: account isolation shell missing')
    m=m[0];payload=base64.b64decode(m[2],validate=True).decode()
    for name,fn in [('cceFrame',dn_cce_final),('classFrame',dn_class_final),('cumulativeFrame',dn_cum_final)]:
        ms=list(re.finditer(r'(\b'+name+r':\s*")([A-Za-z0-9+/=]+)(")',payload))
        if len(ms)!=1:raise SystemExit('STOP: module missing or duplicated: '+name)
        x=ms[0];old=base64.b64decode(x[2],validate=True).decode()
        if hashlib.sha256(old.encode()).hexdigest()!=DN_FINAL_HASHES[name]:raise SystemExit('STOP: reviewed source changed: '+name)
        new=fn(old);payload=payload[:x.start(2)]+base64.b64encode(new.encode()).decode()+payload[x.end(2):];print('Combined CCE repair:',name,hashlib.sha256(new.encode()).hexdigest())
    return s[:m.start(2)]+base64.b64encode(payload.encode()).decode()+s[m.end(2):]

output=dn_final_shell(output)
p.write_text(output);c.write_text(cloud)
print('Cloud script content version:', version)
print('Account isolation candidate built; browser testing required')
