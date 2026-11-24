from pathlib import Path

p = Path("DNYANADA_Admin_Panel_Consolidated.html")
s = p.read_text(encoding="utf-8")

def replace(old, new):
    global s
    if s.count(old) != 1:
        raise SystemExit("STOP: Expected code not found uniquely")
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
 padding:16px 8px;
 border-radius:12px;
 text-align:center;
 border:1px solid #ccd8e5;
 font-weight:600;
}
.stat-card strong{
 display:block;
 font-size:30px;
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

# 3. Read dashboard counts

replace(
    "async function loadTeachers(){",
    """
let statsVersion = 0;

async function loadStats(){
 if(!authorized || !auth.currentUser)return;

 const version = ++statsVersion;
 const uid = auth.currentUser.uid;
 const ids = [
  'countTotal','countActive',
  'countInactive','countExpired'
 ];

 ids.forEach(id=>$(id).textContent='—');
 $('statsInfo').textContent='शिक्षक संख्या तपासत आहे...';
 $('refreshStats').disabled=true;

 try{
  const now=firebase.firestore.Timestamp.now();

  const [total,active,inactive,expired] =
   await Promise.all([
    db.collection('teachers').get(),
    db.collection('teachers')
      .where('status','==','active').get(),
    db.collection('teachers')
      .where('status','==','inactive').get(),
    db.collection('subscriptions')
      .where('expiryDate','<',now).get()
   ]);

  if(version!==statsVersion || !authorized ||
     auth.currentUser?.uid!==uid)return;

  $('countTotal').textContent=total.size;
$('countActive').textContent=active.size;
$('countInactive').textContent=inactive.size;
$('countExpired').textContent=expired.size;
  
  
  
  $('statsInfo').textContent=
   'सक्रिय व निष्क्रिय संख्या खाते स्थितीनुसार आहे. '+
   'मुदत संपलेली संख्या सदस्यत्व नोंदींनुसार आहे.';

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

async function loadTeachers(){"""
)

# 4. Connect refresh button

replace(
    "$('saveFee').onclick=saveFee;",
    """$('saveFee').onclick=saveFee;
$('refreshStats').onclick=loadStats;"""
)

# 5. Load counts after admin login

replace(
    "await loadFee();await loadTeachers();",
    "await loadFee();await loadTeachers();await loadStats();"
)

# 6. Annual fee default

replace('value="199"', 'value="222"')
replace('annualFee=199', 'annualFee=222')
replace('raw.price??199', 'raw.price??222')
replace('v>0?v:199', 'v>0?v:222')
replace('₹199 हे केवळ', '₹222 हे केवळ')

p.write_text(s, encoding="utf-8")

print("SUCCESS: Admin dashboard updated")
