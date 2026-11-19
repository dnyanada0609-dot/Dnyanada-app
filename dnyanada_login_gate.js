/* DNYANADA teacher gate — test build. Keep Firestore rules server-enforced. */
(function () {
  'use strict';
  const config = {apiKey:'AIzaSyAeOvBJxwIRD6rjRdTa7Ay-C9fFwYlHB1Y',authDomain:'dnyanada-app-17c4a.firebaseapp.com',projectId:'dnyanada-app-17c4a',appId:'1:97980812707:web:4eef6c18836d47ba9f9e16'};
  const root = document.documentElement;
  root.classList.add('dnyanada-login-locked');
  const style = document.createElement('style');
  style.textContent = 'html.dnyanada-login-locked body > :not(#dnyanada-login-gate){visibility:hidden!important}#dnyanada-login-gate{position:fixed!important;inset:0!important;z-index:2147483647!important;visibility:visible!important;background:#edf5fc!important;overflow:auto!important;font:16px system-ui,sans-serif!important;color:#163a62!important}#dnyanada-login-gate *{box-sizing:border-box}#dnyanada-login-gate .panel{max-width:430px;margin:8vh auto 20px;background:#fff;border-radius:16px;padding:24px;box-shadow:0 6px 25px #1232}#dnyanada-login-gate input{display:block;width:100%;padding:12px;margin:8px 0 14px;border:1px solid #a9b7c6;border-radius:8px;font:inherit}#dnyanada-login-gate button{padding:12px 18px;border:0;border-radius:8px;background:#12659c;color:#fff;font:inherit}#dnyanada-login-gate p{white-space:pre-wrap;overflow-wrap:anywhere}';
  document.head.appendChild(style);
  const gate = document.createElement('div');
  gate.id = 'dnyanada-login-gate';
  gate.innerHTML = '<div class="panel"><h2>DNYANADA शिक्षक लॉगिन</h2><p>₹199 वार्षिक सदस्यत्व पडताळणी</p><form id="dnyanada-auth-form"><label>ईमेल<input id="dnyanada-email" type="email" autocomplete="username" required></label><label>पासवर्ड<input id="dnyanada-password" type="password" autocomplete="current-password" required></label><button id="dnyanada-submit" type="submit">लॉगिन करा</button></form><p id="dnyanada-auth-status" role="status">Firebase जोडत आहे...</p></div>';
  document.body.appendChild(gate);
  const el = id => document.getElementById(id);
  const status = s => { el('dnyanada-auth-status').textContent = s; };
  const norm = s => String(s == null ? '' : s).trim().toLowerCase();
  function loadScript(src) { return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=()=>reject(Error('Firebase स्क्रिप्ट लोड झाली नाही. इंटरनेट तपासा.'));document.head.appendChild(s);}); }
  function timeout(p,ms) { return Promise.race([p,new Promise((_,reject)=>setTimeout(()=>reject(Error('Firebase प्रतिसादासाठी वेळ संपली.')),ms))]); }
  function expiryValid(value) {
    if (!value) return false;
    let d;
    if (typeof value.toDate === 'function') d = value.toDate();
    else if (typeof value === 'string') {
      const m = value.trim().match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/);
      d = m ? new Date(+m[3],+m[2]-1,+m[1],23,59,59) : new Date(value);
    } else d = new Date(value);
    return !isNaN(d.getTime()) && d.getTime() >= Date.now();
  }
  let auth,db,approvedUid=null;
  async function verify(user) {
    if (!user) { approvedUid=null; root.classList.add('dnyanada-login-locked'); gate.hidden=false;status('लॉगिन करा.');return; }
    status('शिक्षक खाते आणि सदस्यत्व तपासत आहे...');
    const [t,s]=await timeout(Promise.all([db.collection('teachers').doc(user.uid).get(),db.collection('subscriptions').doc(user.uid).get()]),15000);
    if (!t.exists || !s.exists) throw Error('शिक्षक किंवा सदस्यत्वाची नोंद नाही.');
    const td=t.data(),sd=s.data();
    if (norm(td.status)!=='active' || norm(sd.status)!=='active' || !expiryValid(sd.expiryDate)) throw Error('खाते किंवा ₹199 सदस्यत्व सक्रिय नाही अथवा मुदत संपली आहे.');
    approvedUid=user.uid;
    gate.hidden=true;
    root.classList.remove('dnyanada-login-locked');
  }
  (async()=>{
    try {
      await loadScript('https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js');
      await loadScript('https://www.gstatic.com/firebasejs/10.14.1/firebase-auth-compat.js');
      await loadScript('https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore-compat.js');
      firebase.initializeApp(config,'dnyanada-login-gate');
      const app=firebase.app('dnyanada-login-gate');auth=app.auth();db=app.firestore();
      auth.onAuthStateChanged(async user=>{
        try { await verify(user); }
        catch(e){approvedUid=null;root.classList.add('dnyanada-login-locked');gate.hidden=false;status('प्रवेश नाकारला: '+e.message);}
      },e=>status('Firebase त्रुटी: '+e.message));
      el('dnyanada-auth-form').addEventListener('submit',async e=>{
        e.preventDefault();const b=el('dnyanada-submit');b.disabled=true;
        try {status('लॉगिन सुरू आहे...');const c=await timeout(auth.signInWithEmailAndPassword(el('dnyanada-email').value.trim(),el('dnyanada-password').value),15000);await verify(c.user);el('dnyanada-password').value='';}
        catch(err){status('लॉगिन अयशस्वी: '+(err.code||'')+' '+err.message);}
        finally{b.disabled=false;}
      });
      // Recheck access when app returns from background, rather than trusting a past approval indefinitely.
      document.addEventListener('visibilitychange',async()=>{if(!document.hidden && approvedUid && auth.currentUser){root.classList.add('dnyanada-login-locked');gate.hidden=false;try{await verify(auth.currentUser);}catch(e){approvedUid=null;status('पुन्हा पडताळणी अयशस्वी: '+e.message);}}});
    } catch(e){status('सुरुवातीची त्रुटी: '+e.message);}
  })();
})();
