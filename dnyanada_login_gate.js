/* DNYANADA Login Gate */
(function () {
  "use strict";

  if (document.getElementById("dnyanada-login-gate")) return;

  const config = {
    apiKey: "AIzaSyAeOvBJxwIRD6rjRdTa7Ay-C9fFwYlHB1Y",
    authDomain: "dnyanada-app-17c4a.firebaseapp.com",
    projectId: "dnyanada-app-17c4a",
    appId: "1:97980812707:web:4eef6c18836d47ba9f9e16"
  };

  const ADMIN_URL = "https://dnyanada-app-17c4a.web.app/";
  const root = document.documentElement;
  root.classList.add("dnyanada-login-locked");

  const style = document.createElement("style");
  style.textContent = `
    html.dnyanada-login-locked body > :not(#dnyanada-login-gate) {
      visibility: hidden !important;
    }
    #dnyanada-login-gate {
      position: fixed !important;
      inset: 0 !important;
      z-index: 2147483647 !important;
      visibility: visible !important;
      background: #edf5fc !important;
      overflow: auto !important;
      font: 16px system-ui,sans-serif !important;
      color: #163a62 !important;
    }
    #dnyanada-login-gate[hidden],
    #dnyanada-login-gate [hidden] {
      display: none !important;
    }
    #dnyanada-login-gate * {
      box-sizing: border-box;
    }
    #dnyanada-login-gate .panel {
      max-width: 430px;
      margin: 6vh auto 20px;
      padding: 22px;
      background: white;
      border-radius: 16px;
      box-shadow: 0 6px 25px #1232;
    }
    #dnyanada-login-gate input,
    #dnyanada-login-gate select {
      display: block;
      width: 100%;
      padding: 12px;
      margin: 7px 0 13px;
      border: 1px solid #a9b7c6;
      border-radius: 8px;
      font: inherit;
    }
    #dnyanada-login-gate button {
      padding: 11px 14px;
      margin: 5px 4px 5px 0;
      border: 0;
      border-radius: 8px;
      background: #12659c;
      color: white;
      font: inherit;
      cursor: pointer;
    }
    #dnyanada-login-gate button:disabled {
      opacity: .5;
    }
    #dnyanada-login-gate .secondary {
      background: #60758a;
    }
    #dn-status {
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }
  `;
  document.head.appendChild(style);

  const gate = document.createElement("div");
  gate.id = "dnyanada-login-gate";

  gate.innerHTML = `
    <div class="panel">
      <h2>DNYANADA Smart Teacher App</h2>

      <label for="dn-role">लॉगिन प्रकार</label>
      <select id="dn-role">
        <option value="teacher">शिक्षक</option>
        <option value="admin">Admin</option>
      </select>

      <div id="dn-teacher">
        <h3>शिक्षक लॉगिन</h3>
        <p>वार्षिक सदस्यत्व पडताळणी</p>

        <form id="dn-form">
          <label for="dn-email">ईमेल</label>
          <input id="dn-email" type="email"
                 autocomplete="username" required>

          <label for="dn-password">पासवर्ड</label>
          <input id="dn-password" type="password"
                 autocomplete="current-password" required>

          <button id="dn-submit" type="submit">
            लॉगिन करा
          </button>
        </form>

        <button id="dn-forgot" class="secondary" type="button">
          पासवर्ड विसरलात?
        </button>
      </div>

      <div id="dn-admin" hidden>
        <h3>Admin व्यवस्थापन</h3>
        <p>अधिकृत Admin Panel उघडा.</p>
        <button id="dn-open-admin" type="button">
          Admin Panel उघडा
        </button>
      </div>

      <div id="dn-change" hidden>
        <h3>पासवर्ड बदला</h3>

        <label for="dn-old">सध्याचा पासवर्ड</label>
        <input id="dn-old" type="password"
               autocomplete="current-password">

        <label for="dn-new">
          नवीन पासवर्ड (किमान 12 अक्षरे)
        </label>
        <input id="dn-new" type="password"
               autocomplete="new-password">

        <label for="dn-confirm">
          नवीन पासवर्ड पुन्हा लिहा
        </label>
        <input id="dn-confirm" type="password"
               autocomplete="new-password">

        <button id="dn-save" type="button">
          पासवर्ड सेव्ह करा
        </button>

        <button id="dn-cancel" class="secondary" type="button">
          रद्द करा
        </button>
      </div>

      <p id="dn-status" role="status">
        Firebase जोडत आहे...
      </p>
    </div>
  `;

  document.body.appendChild(gate);

  const el = id => document.getElementById(id);
  const status = msg => {
    el("dn-status").textContent = msg;
  };

  const norm = v =>
    String(v == null ? "" : v).trim().toLowerCase();

  const field = (o, k) =>
    o[k] ?? o[k + " "] ?? "";

  let auth;
  let db;
  let approvedUid = null;
  let changing = false;
  let sequence = 0;

  const logoutBtn = () =>
    document.getElementById("dnyanada-logout");

  const passwordBtn = () =>
    document.getElementById("dnyanada-password-settings");

  function showGate(msg) {
    root.classList.add("dnyanada-login-locked");
    gate.hidden = false;

    if (logoutBtn()) logoutBtn().hidden = true;
    if (passwordBtn()) passwordBtn().hidden = true;

    if (msg) status(msg);
  }

  function unlock() {
    gate.hidden = true;
    root.classList.remove("dnyanada-login-locked");

    if (logoutBtn()) logoutBtn().hidden = false;
    if (passwordBtn()) passwordBtn().hidden = false;
  }

  function showTeacher() {
    changing = false;
    el("dn-role").value = "teacher";
    el("dn-teacher").hidden = false;
    el("dn-admin").hidden = true;
    el("dn-change").hidden = true;
  }

  function showChange() {
    if (!auth || !auth.currentUser ||
        approvedUid !== auth.currentUser.uid) return;

    changing = true;
    el("dn-teacher").hidden = true;
    el("dn-admin").hidden = true;
    el("dn-change").hidden = false;

    showGate("सध्याचा व नवीन पासवर्ड लिहा.");
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = () =>
        reject(Error("Firebase लोड झाले नाही. इंटरनेट तपासा."));
      document.head.appendChild(s);
    });
  }

  function timeout(p, ms) {
    return Promise.race([
      p,
      new Promise((_, reject) =>
        setTimeout(
          () => reject(Error("Firebase प्रतिसादासाठी वेळ संपली.")),
          ms
        )
      )
    ]);
  }

  function expiryValid(v) {
    if (!v) return false;

    let d;

    if (typeof v.toDate === "function") {
      d = v.toDate();
    } else if (typeof v === "string") {
      const m = v.trim().match(
        /^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/
      );

      d = m
        ? new Date(+m[3], +m[2] - 1, +m[1], 23, 59, 59)
        : new Date(v);
    } else {
      d = new Date(v);
    }

    return !isNaN(d.getTime()) &&
           d.getTime() >= Date.now();
  }

  function addButtons() {
    if (logoutBtn()) return;

    const out = document.createElement("button");
    out.id = "dnyanada-logout";
    out.textContent = "⏻";
    out.title = "लॉगआऊट";
    out.setAttribute("aria-label", "लॉगआऊट");

    out.style.cssText =
      "position:fixed;right:10px;top:10px;" +
      "width:36px;height:36px;z-index:2147483000;" +
      "padding:0;background:#b42318;color:white;" +
      "border:2px solid white;border-radius:50%;" +
      "font-size:20px;cursor:pointer";

    out.onclick = async () => {
      if (!confirm("लॉगआऊट करायचे आहे का?")) return;

      showGate("लॉगआऊट होत आहे...");
      approvedUid = null;
      sequence++;

      try {
        await auth.signOut();
        showTeacher();
        status("लॉगआऊट झाले. पुन्हा लॉगिन करा.");
      } catch (e) {
        status("लॉगआऊट त्रुटी: " + e.message);
      }
    };

    const key = document.createElement("button");
    key.id = "dnyanada-password-settings";
    key.textContent = "🔑";
    key.title = "पासवर्ड बदला";
    key.setAttribute("aria-label", "पासवर्ड बदला");

    key.style.cssText =
      "position:fixed;right:52px;top:10px;" +
      "width:36px;height:36px;z-index:2147483000;" +
      "padding:0;background:#12659c;color:white;" +
      "border:2px solid white;border-radius:50%;" +
      "font-size:17px;cursor:pointer";

    key.onclick = showChange;

    document.body.append(out, key);
  }

  async function verify(user) {
    const ticket = ++sequence;

    if (!user) {
      approvedUid = null;
      showTeacher();
      showGate("शिक्षक लॉगिन करा.");
      return;
    }

    if (!changing) {
      showGate("शिक्षक खाते आणि सदस्यत्व तपासत आहे...");
    }

    const [t, s] = await timeout(Promise.all([
      db.collection("teachers").doc(user.uid).get(),
      db.collection("subscriptions").doc(user.uid).get()
    ]), 15000);

    if (ticket !== sequence ||
        auth.currentUser?.uid !== user.uid) return;

    if (!t.exists) {
      throw Error("शिक्षकाची नोंद नाही.");
    }

    if (!s.exists) {
      throw Error("सदस्यत्वाची नोंद नाही.");
    }

    const td = t.data();
    const sd = s.data();

    if (field(td, "status") &&
        norm(field(td, "status")) !== "active") {
      throw Error("शिक्षक खाते सक्रिय नाही.");
    }

    if (norm(field(sd, "status")) !== "active") {
      throw Error("सदस्यत्व सक्रिय नाही.");
    }

    if (!expiryValid(field(sd, "expiryDate"))) {
      throw Error(
        "सदस्यत्वाची मुदत संपली किंवा तारीख अवैध आहे."
      );
    }

    approvedUid = user.uid;
    addButtons();

    if (!changing) unlock();
  }

  function authError(e) {
    return (e.code ? e.code + " : " : "") +
      (e.message || String(e));
  }

  el("dn-role").addEventListener("change", () => {
    if (changing) return;

    const admin = el("dn-role").value === "admin";

    el("dn-admin").hidden = !admin;
    el("dn-teacher").hidden = admin;

    status(admin
      ? "Admin Panel स्वतंत्रपणे उघडेल."
      : "शिक्षक लॉगिन करा.");
  });

  el("dn-open-admin").addEventListener("click", () => {
    const w = window.open(ADMIN_URL, "_blank");

    if (!w) {
      window.location.href = ADMIN_URL;
    }
  });

  el("dn-forgot").addEventListener("click", async () => {
    if (!auth) {
      status("Firebase जोडले जात आहे.");
      return;
    }

    const email = el("dn-email").value.trim();

    if (!email) {
      status("प्रथम ईमेल पत्ता लिहा.");
      el("dn-email").focus();
      return;
    }

    const btn = el("dn-forgot");
    btn.disabled = true;

    try {
      await timeout(
        auth.sendPasswordResetEmail(email),
        15000
      );

      status(
        "खाते अस्तित्वात असल्यास पासवर्ड रीसेट " +
        "ईमेल पाठवला जाईल. Inbox आणि Spam तपासा."
      );
    } catch (e) {
      status("रीसेट अयशस्वी: " + authError(e));
    } finally {
      btn.disabled = false;
    }
  });

  el("dn-form").addEventListener("submit", async e => {
    e.preventDefault();

    if (!auth) {
      status("Firebase जोडले जात आहे.");
      return;
    }

    const btn = el("dn-submit");
    btn.disabled = true;

    try {
      showGate("लॉगिन सुरू आहे...");

      const c = await timeout(
        auth.signInWithEmailAndPassword(
          el("dn-email").value.trim(),
          el("dn-password").value
        ),
        15000
      );

      await verify(c.user);
      el("dn-password").value = "";
    } catch (err) {
      approvedUid = null;
      showGate("लॉगिन अयशस्वी: " + authError(err));
    } finally {
      btn.disabled = false;
    }
  });

  el("dn-save").addEventListener("click", async () => {
    if (!auth || !auth.currentUser ||
        approvedUid !== auth.currentUser.uid) {
      status("पुन्हा लॉगिन करा.");
      return;
    }

    const old = el("dn-old").value;
    const next = el("dn-new").value;
    const confirmNew = el("dn-confirm").value;

    if (next.length < 12) {
      status("नवीन पासवर्ड किमान 12 अक्षरांचा असावा.");
      return;
    }

    if (next !== confirmNew) {
      status("नवीन पासवर्ड दोन्ही ठिकाणी सारखा नाही.");
      return;
    }

    if (old === next) {
      status("नवीन पासवर्ड वेगळा असावा.");
      return;
    }

    const btn = el("dn-save");
    btn.disabled = true;

    try {
      const user = auth.currentUser;

      const credential =
        firebase.auth.EmailAuthProvider.credential(
          user.email,
          old
        );

      await timeout(
        user.reauthenticateWithCredential(credential),
        15000
      );

      await timeout(
        user.updatePassword(next),
        15000
      );

      el("dn-old").value = "";
      el("dn-new").value = "";
      el("dn-confirm").value = "";

      changing = false;
      showTeacher();

      await verify(user);
    } catch (e) {
      status("पासवर्ड बदलता आला नाही: " + authError(e));
    } finally {
      btn.disabled = false;
    }
  });

  el("dn-cancel").addEventListener("click", async () => {
    changing = false;
    showTeacher();

    if (auth?.currentUser &&
        approvedUid === auth.currentUser.uid) {
      try {
        await verify(auth.currentUser);
      } catch (e) {
        approvedUid = null;
        showGate("पडताळणी अयशस्वी: " + authError(e));
      }
    } else {
      showGate("शिक्षक लॉगिन करा.");
    }
  });

  (async () => {
    try {
      await loadScript(
        "https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js"
      );

      await loadScript(
        "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth-compat.js"
      );

      await loadScript(
        "https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore-compat.js"
      );

      const app =
        firebase.apps.find(
          a => a.name === "dnyanada-login-gate"
        ) ||
        firebase.initializeApp(
          config,
          "dnyanada-login-gate"
        );

      auth = app.auth();
      db = app.firestore();

      auth.onAuthStateChanged(
        async user => {
          try {
            await verify(user);
          } catch (e) {
            approvedUid = null;
            showGate(
              "प्रवेश नाकारला: " + authError(e)
            );
          }
        },
        e => showGate(
          "Firebase त्रुटी: " + authError(e)
        )
      );

      document.addEventListener(
        "visibilitychange",
        async () => {
          if (
            document.hidden ||
            changing ||
            !approvedUid ||
            !auth.currentUser
          ) return;

          try {
            await verify(auth.currentUser);
          } catch (e) {
            approvedUid = null;
            showGate(
              "पुन्हा पडताळणी अयशस्वी: " +
              authError(e)
            );
          }
        }
      );
    } catch (e) {
      showGate(
        "सुरुवातीची त्रुटी: " + authError(e)
      );
    }
  })();
})();
