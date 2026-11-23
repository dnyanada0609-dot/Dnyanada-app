from pathlib import Path
import re,base64
p=Path('www/index.html')
s=p.read_text(encoding='utf-8')
m=re.search(r'(cceFrame:")([A-Za-z0-9+/=]+)(")',s)
if not m: raise SystemExit('ERROR: CCE module not found')
h=base64.b64decode(m.group(2)).decode('utf-8')
marker='DNY_PROGRESS_SYNC_FIX_20261123'
if marker in h:
 print('CCE progress sync already installed; skipped')
 raise SystemExit(0)
if 'function dnyNotesRecordKey(roll,term)' not in h or 'function dnyNotesStorageKey()' not in h:
 raise SystemExit('ERROR: account notes patch must run before progress sync patch')
# Keep original note category matching and existing teacher-scoped storage; repair only its reader.
a=h.index('function notesForProgress(roll,term){')
b=h.index('loadRoster();loadWorkdays();buildRows();',a)
chunk=h[a:b]
old="let all={};try{all=JSON.parse(localStorage.getItem('gyanadaCCEDescriptiveNotes')||'{}')}catch(e){}"
new="let all={};try{const k=dnyNotesStorageKey();if(k)all=JSON.parse(localStorage.getItem(k)||'{}')}catch(e){}"
if old in chunk: chunk=chunk.replace(old,new,1)
elif new not in chunk: raise SystemExit('ERROR: unknown progress reader storage format')
oldlist="const list=all[`${roll}_${t}`]||all[String(roll)+(t===2?'_2':'')]||[];"
newlist="const list=all[dnyNotesRecordKey(roll,t)]||[];"
if oldlist in chunk:
 chunk=chunk.replace(oldlist,newlist,1)
else:
 alternative="const list=all[String(roll)+'_'+t]||(t===1?all[String(roll)]:null)||[];"
 if alternative in chunk:
  chunk=chunk.replace(alternative,newlist,1)
 elif newlist not in chunk:
  raise SystemExit('ERROR: unknown progress reader student key')
h=h[:a]+chunk+h[b:]
# Keep both local progress card notices in sync after reload and on every edit.
needle="set('progressNoticeText_2',notice);"
if h.count(needle)!=1: raise SystemExit('ERROR: progress notice field not found uniquely')
h=h.replace(needle,needle+" /* DNY_PROGRESS_SYNC_FIX_20261123 */",1)
# The separate progress iframe's existing bridge also receives the notice in its values.
needle="values.location=[value('setupTaluka'),value('setupDistrict')].filter(Boolean).join(' / ');"
if h.count(needle)!=1: raise SystemExit('ERROR: progress iframe bridge not found uniquely')
h=h.replace(needle,needle+"\n values.notice=value('setupNotice');",1)
needle="'location','p1','h1','i1','p2','h2','i2'"
if h.count(needle)!=1: raise SystemExit('ERROR: progress bridge field list changed')
h=h.replace(needle,"'location','notice','p1','h1','i1','p2','h2','i2'",1)
# Ensure main CCE progress view refreshes when user navigates back to it.
needle='function syncProgressNoteFields(){'
if h.count(needle)!=1: raise SystemExit('ERROR: progress note refresh function changed')
# Do not modify saved student notes or unrelated modules.
encoded=base64.b64encode(h.encode('utf-8')).decode('ascii')
s=s[:m.start(2)]+encoded+s[m.end(2):]
p.write_text(s,encoding='utf-8')
print('CCE progress reader uses teacher/student scoped notes; notice included in progress relay.')
