from pathlib import Path
p=Path('www/index.html')
s=p.read_text(encoding='utf-8')
js=Path('dnyanada_login_gate.js').read_text(encoding='utf-8')
needle='</body>'
pos=s.lower().rfind(needle)
if pos<0: raise SystemExit('ERROR: closing body tag not found')
if 'dnyanada-login-gate' in s: raise SystemExit('ERROR: gate already injected')
s=s[:pos]+'<script>\n'+js+'\n</script>\n'+s[pos:]
p.write_text(s,encoding='utf-8')
print('DNYANADA login gate embedded before final </body>')
