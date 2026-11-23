
from pathlib import Path

p = Path("www/index.html")
s = p.read_text(encoding="utf-8")
js = Path("dnyanada_login_gate.js").read_text(encoding="utf-8")

needle = "</body>"
pos = s.lower().rfind(needle)

if pos < 0:
    raise SystemExit("ERROR: closing body tag not found")

if 'id="dnyanada-login-gate"' in s:
    print("DNYANADA login gate already present; skipped.")
else:
    s = s[:pos] + "<script>\n" + js + "\n</script>\n" + s[pos:]
    p.write_text(s, encoding="utf-8")
    print("DNYANADA login gate embedded successfully.")
