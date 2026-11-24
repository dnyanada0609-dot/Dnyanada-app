from pathlib import Path
import re

p = Path("DNYANADA_Admin_Panel_Consolidated.html")
s = p.read_text(encoding="utf-8")

def replace(old, new):
    global s
    if s.count(old) != 1:
        raise SystemExit("STOP: Code mismatch: " + old[:80])
    s = s.replace(old, new, 1)

# 1. Dashboard design

replace("</style>", """
.stats-grid{
 display:grid;
 grid-template-columns:repeat(2,minmax(0,1fr));
 gap:12px;
 margin:16px 0;
}
.stat-card{
 padding:18px 8px;
 border-radius:12px;
 text-align:center;
 border:1px solid #ccd8e5;
 font-weight:600;
}
.stat-card strong{
 display:block;
 font-size:32px;
 margin-bottom:6px;
}
.stat-total{background:#e8f0fc;color:#245bb0}
.stat-active{background:#e6f5eb;color:#21834c}
.stat-inactive{background:#fce9e9;color:#b73737}
.stat-expired{background:#fff1dc;color:#946013}
</style>""")

# 2. Dashboard cards

replace(
 "<h2>शिक्षक खाते व्यवस्थापन</h2>",
 """<h2>शिक्षक खाते व्यवस्थापन</h2>
<div class="stats-grid">
 <div class="stat-card stat-total">
  <strong id="countTotal">—</strong>
  एकूण शिक्षक
 </div>
 <div class="stat-card stat-active">
  <strong id="countActive">—</strong>
  सक्रिय शिक्षक
 </div>
 <div class="stat-card stat-inactive">
  <strong id="countInactive">—</strong>
  निष्क्रिय शिक्षक
 </div>
 <div class="stat-card stat-expired">
  <strong id="countExpired">—</strong>
  मुदत संपलेले शिक्षक
 </div>
</div>
<button id="refreshStats" class="secondary">
 शिक्षक संख्या अपडेट करा
</button>
<p id="statsInfo" class="muted"></p>
"""
)

# 3. Remove demo section

s, n = re.subn(
 r'<div class="editor"><h2>जुन्या डेमो नोंदी बंद करा</h2>.*?</div>',
 '',
 s,
 count=1,
 flags=re.S
)
if n != 1:
    raise SystemExit("STOP: Demo section not found")

# 4. Remove demo checkbox

s, n = re.subn(
 r"const choose=mk\('input'\);.*?card\.append\(chooseLabel\);",
 "",
 s,
 count=1,
 flags=re.S
)
if n != 1:
    raise SystemExit("STOP: Demo checkbox not found")

# 5. Remove old demo function

s, n = re.subn(
 r"async function disableSelected\(\)\{.*?(?=async function setTeacher)",
 "",
 s,
 count=1,
 flags=re.S
)
if n != 1:
    raise SystemExit("STOP: Demo function not found")

replace(
 "$('disableSelected').onclick=disableSelected;",
 ""
)

# 6. Dashboard counts

replace(
 "async function loadTeachers(){",
 """
let statsVersion=0;

async function loadStats(){
 if(!authorized || !auth.currentUser)return;

 const version=++statsVersion;
 const uid=auth.currentUser.uid;
 const ids=[
  'countTotal','countActive',
  'countInactive','countExpired'
 ];

 ids.forEach(id=>$(id).textContent='—');
 $('statsInfo').textContent='शिक्षक संख्या तपासत आहे...';
 $('refreshStats').disabled=true;

 try{
  const now=firebase.firestore.Timestamp.now();

  const [teachers,expiredSubs]=await Promise.all([
   db.collection('teachers').get({source:'server'}),
   db.collection('subscriptions')
    .where('expiryDate','<',now)
    .get({source:'server'})
  ]);

  if(version!==statsVersion ||
     !authorized ||
     auth.currentUser?.uid!==uid)return;

  const expiredIds=new Set(
   expiredSubs.docs.map(d=>d.id)
  );

  let total=0,active=0,inactive=0,expired=0;

  teachers.forEach(doc=>{
   if(doc.id===uid)return;

   total++;
   const status=String(
    doc.data().status||''
   ).trim().toLowerCase();

   if(status==='active')active++;
   else inactive++;

   if(expiredIds.has(doc.id))expired++;
  });

  $('countTotal').textContent=total;
  $('countActive').textContent=active;
  $('countInactive').textContent=inactive;
  $('countExpired').textContent=expired;

  $('statsInfo').textContent=
   'खाते स्थितीनुसार सक्रिय व निष्क्रिय संख्या. '+
   'मुदत संपलेले शिक्षक स्वतंत्रपणे मोजले आहेत.';

 }catch(e){
  if(version===statsVersion){
   $('statsInfo').textContent=
    'संख्या मिळाली नाही: '+(e.code||e.message);
  }
 }finally{
  if(version===statsVersion){
   $('refreshStats').disabled=false;
  }
 }
}

async function loadTeachers(){
 if(authorized)loadStats();
"""
)

# 7. Connect dashboard refresh

replace(
 "$('saveFee').onclick=saveFee;",
 """$('saveFee').onclick=saveFee;
 $('refreshStats').onclick=loadStats;"""
)

# 8. Annual fee default

replace('value="199"', 'value="222"')
replace('annualFee=199', 'annualFee=222')
replace('raw.price??199', 'raw.price??222')
replace('v>0?v:199', 'v>0?v:222')
replace('₹199 हे केवळ', '₹222 हे केवळ')

# 9. First password change flag

old = "status:'inactive',createdAt:"
new = "status:'inactive',mustChangePassword:true,createdAt:"

if old in s:
    replace(old,new)
elif s.count(new)!=1:
    raise SystemExit("STOP: Password flag check failed")

# 10. Correct title

s=s.replace(
 "DNYANADA DNYANADA Admin Panel",
 "DNYANADA Admin Panel"
)

# 11. Final validation

if "disableSelected" in s or "demo-select" in s:
    raise SystemExit("STOP: Old demo code remains")

if 'id="countTotal"' not in s:
    raise SystemExit("STOP: Dashboard missing")

p.write_text(s,encoding="utf-8")

print("SUCCESS: DNYANADA Admin Dashboard updated")
