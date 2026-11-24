
from pathlib import Path

login = Path("dnyanada_login_gate.js")
cloud = Path("dnyanada_cloud_backup.js")

s = login.read_text(encoding="utf-8")
c = cloud.read_text(encoding="utf-8")

def replace(text, old, new):
    if text.count(old) != 1:
        raise SystemExit("STOP: Expected code not found uniquely")
    return text.replace(old, new, 1)

# 1. Password change button on login page

s = replace(s,
    '<button id="dn-forgot"',
    '''<button id="dn-change-open"
        class="secondary" type="button">
        पासवर्ड बदला
        </button>
        <button id="dn-forgot"'''
)

s = replace(s,
    '<label for="dn-old">',
    '''<label for="dn-change-email">ईमेल</label>
        <input id="dn-change-email" type="email"
               autocomplete="username">
        <label for="dn-old">'''
)

start = s.index("  function showChange() {")
end = s.index("  function loadScript", start)

s = s[:start] + '''  function showChange() {
    changing = true;
    el("dn-change-email").value =
      el("dn-email").value.trim();
    el("dn-teacher").hidden = true;
    el("dn-change").hidden = false;
    showGate("ईमेल, सध्याचा व नवीन पासवर्ड लिहा.");
  }

  el("dn-change-open").onclick = showChange;

''' + s[end:]

# 2. Remove dashboard password icon

start = s.index('    const key = document.createElement("button");')
end = s.index("    document.body.append(out, key);", start)

s = s[:start] + s[end:]

s = replace(s,
    "document.body.append(out, key);",
    "document.body.appendChild(out);"
)

# 3. Persistent login

s = replace(s,
    "auth = app.auth();",
    """auth = app.auth();
      await auth.setPersistence(
        firebase.auth.Auth.Persistence.LOCAL
      );"""
)

# 4. Clear password after logout

s = replace(s,
    "await auth.signOut();",
    """await auth.signOut();
        el("dn-password").value = "";
        el("dn-old").value = "";
        el("dn-new").value = "";
        el("dn-confirm").value = "";"""
)

# 5. Avoid login form flash during verification

s = replace(s,
    'gate.hidden = false;',
    '''gate.hidden = false;
    el("dn-teacher").hidden =
      !!(auth && auth.currentUser && !changing);'''
)

s = replace(s,
    'if (!changing) {\n      showGate("शिक्षक खाते आणि सदस्यत्व तपासत आहे...");\n    }',
    '''if (!changing && approvedUid !== user.uid) {
      showGate("शिक्षक खाते आणि सदस्यत्व तपासत आहे...");
    }'''
)

# 6. Password change using current credentials

start = s.index('  el("dn-save").addEventListener')
end = s.index('  el("dn-cancel").addEventListener', start)

s = s[:start] + '''  el("dn-save").addEventListener("click", async () => {
    if (!auth) return;

    const email = el("dn-change-email").value.trim();
    const old = el("dn-old").value;
    const next = el("dn-new").value;
    const again = el("dn-confirm").value;

    if (!email || !old) {
      status("ईमेल व सध्याचा पासवर्ड लिहा.");
      return;
    }

    if (next.length < 12 || next !== again || old === next) {
      status("नवीन पासवर्ड किमान 12 अक्षरांचा, वेगळा आणि दोन्हीकडे समान असावा.");
      return;
    }

    const btn = el("dn-save");
    btn.disabled = true;

    try {
      changing = true;

      const result = await auth.signInWithEmailAndPassword(
        email, old
      );

      await result.user.updatePassword(next);
      approvedUid = null;
      sequence++;
      await auth.signOut();

      el("dn-old").value = "";
      el("dn-new").value = "";
      el("dn-confirm").value = "";
      el("dn-password").value = "";
      el("dn-email").value = email;

      showTeacher();
      showGate("पासवर्ड बदलला. नवीन पासवर्डने लॉगिन करा.");

    } catch (e) {
      approvedUid = null;
      sequence++;

      try {
        await auth.signOut();
      } catch (_) {}

      changing = true;
      el("dn-teacher").hidden = true;
      el("dn-change").hidden = false;
      showGate("पासवर्ड बदलता आला नाही: " + authError(e));

    } finally {
      btn.disabled = false;
    }
  });

''' + s[end:]

s = replace(s,
    "async function verify(user) {\n    const ticket",
    """async function verify(user) {
    if (changing) return;
    const ticket"""
)

# 7. Keep login form available if verification fails

s = replace(s,
    'if (msg) status(msg);',
    '''if (!changing && !approvedUid &&
        msg && /अयशस्वी|नाकारला|त्रुटी/.test(msg)) {
      el("dn-teacher").hidden = false;
    }

    if (msg) status(msg);'''
)

# 8. Smaller central cloud button

c = replace(c,
    "trigger.textContent='☁ क्लाऊड बॅकअप';",
    "trigger.textContent='☁ क्लाऊड';"
)

c = replace(c,
    "'border-radius:999px;padding:9px 18px;'+",
    "'border-radius:999px;padding:3px 8px;'+"
)

c = replace(c,
    "'font:700 14px system-ui,sans-serif;'+",
    "'font:600 10px system-ui,sans-serif;'+"
)

# 9. Hide cloud tools during login and printing

c = replace(c,
    "function addUI(){",
    """function addUI(){
 const css=document.createElement('style');
  css.textContent=`
 #dny-cloud-tools > button {
   width:65px !important;
   min-width:0 !important;
   max-width:65px !important;
   height:24px !important;
   min-height:0 !important;
   max-height:24px !important;
   padding:0 !important;
   margin:0 auto !important;
   font-size:10px !important;
   line-height:20px !important;
   border:1px solid white !important;
   box-sizing:border-box !important;
 }
 
 html.dnyanada-login-locked #dny-cloud-tools {
   display:none !important;
 }
 @media print {
   #dny-cloud-tools {
     display:none !important;
   }
 }
 `;
 document.head.appendChild(css);
"""
)

c = replace(c,
    "async function autoCheck(){",
    """async function autoCheck(){
 if(document.documentElement.classList
    .contains('dnyanada-login-locked'))return;
"""
)

# Write only after all replacements succeed

login.write_text(s, encoding="utf-8")
cloud.write_text(c, encoding="utf-8")

print("SUCCESS: Login and cloud UI patch applied")
