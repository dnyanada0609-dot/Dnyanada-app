from pathlib import Path

p = Path("dnyanada_login_gate.js")
s = p.read_text(encoding="utf-8")

def replace(old, new):
    global s
    if s.count(old) != 1:
        raise SystemExit(
            "STOP: Expected login code not found uniquely"
        )
    s = s.replace(old, new, 1)

replace(
    'let changing = false;',
    '''let changing = false;
  let mandatoryChange = false;'''
)

replace(
    'if (field(td, "status") &&',
    'if ('
)

replace(
    '    approvedUid = user.uid;',
    '''    if (td.mustChangePassword === true) {
      approvedUid = null;
      mandatoryChange = true;
      changing = true;

      el("dn-change-email").value = user.email || "";
      el("dn-change-email").readOnly = true;
      el("dn-teacher").hidden = true;
      el("dn-change").hidden = false;
      el("dn-cancel").hidden = true;

      showGate(
        "पहिल्या लॉगिनला नवीन पासवर्ड तयार करणे आवश्यक आहे."
      );
      return;
    }

    mandatoryChange = false;
    el("dn-change-email").readOnly = false;
    el("dn-cancel").hidden = false;

    approvedUid = user.uid;'''
)

replace(
    '      await result.user.updatePassword(next);',
    '''      await result.user.updatePassword(next);

      const teacherRef = db.collection("teachers")
        .doc(result.user.uid);

      const teacherDoc = await teacherRef.get();

      if (teacherDoc.exists &&
          teacherDoc.data().mustChangePassword === true) {
        await teacherRef.update({
          mustChangePassword: false
        });
      }

      mandatoryChange = false;
      el("dn-change-email").readOnly = false;
      el("dn-cancel").hidden = false;'''
)

replace(
    '    changing = false;\n    showTeacher();',
    '''    if (mandatoryChange) {
      status("प्रथम नवीन पासवर्ड तयार करा.");
      return;
    }

    changing = false;
    showTeacher();'''
)

p.write_text(s, encoding="utf-8")

print("SUCCESS: First password change patch applied")
