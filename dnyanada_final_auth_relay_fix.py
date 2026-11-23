from pathlib import Path
import re, sys
p=Path('www/index.html')
s=p.read_text(encoding='utf-8')
marker='DNY_FINAL_VERIFIED_CCE_RELAY_20261123'
if marker in s:
 print('Already installed');sys.exit(0)
# Require the existing login gate and CCE relay, avoiding changes to other modules.
start=s.find('<script id="dny-auth-context-relay">')
end=s.find('</script>',start)
if start<0 or end<0 or s.count('<script id="dny-auth-context-relay">')!=1:
 raise SystemExit('Expected exactly one CCE auth relay; no changes')
login_anchor='    approvedUid = user.uid;\n    addButtons();'
if s.count(login_anchor)!=1:raise SystemExit('Login approval anchor missing/ambiguous; no changes')
# Approved user event is sent only AFTER teacher + subscription verification.
s=s.replace(login_anchor,'''    approvedUid = user.uid;
    window.dispatchEvent(new CustomEvent('DNY_VERIFIED_TEACHER', {detail:{uid:user.uid}}));
    addButtons();''',1)
# Clear the CCE identity when login state changes or access is revoked.
# A new login is always revalidated before a new identity is delivered.
logout_anchor='    if (!user) {\n      approvedUid = null;'
if s.count(logout_anchor)!=1:raise SystemExit('Login signout anchor missing/ambiguous; no changes')
s=s.replace(logout_anchor,'''    if (!user) {
      approvedUid = null;
      window.dispatchEvent(new Event('DNY_VERIFIED_TEACHER_CLEARED'));''',1)
# Clear when the user initiates signout, before Firebase signOut finishes.
logout_click='      approvedUid = null;\n      sequence++;'
if s.count(logout_click)!=1:raise SystemExit('Logout click anchor missing/ambiguous; no changes')
s=s.replace(logout_click,'''      approvedUid = null;
      window.dispatchEvent(new Event('DNY_VERIFIED_TEACHER_CLEARED'));
      sequence++;''',1)
# Recalculate boundaries after modifications.
start=s.find('<script id="dny-auth-context-relay">');end=s.find('</script>',start)+len('</script>')
relay='''<script id="dny-auth-context-relay">
/* DNY_FINAL_VERIFIED_CCE_RELAY_20261123 */
(function(){
 'use strict';
 let verifiedUid='';
 function frame(){return document.getElementById('cceFrame')}
 function deliver(){
  try{if(verifiedUid&&frame()?.contentWindow)
   frame().contentWindow.postMessage({type:'DNY_AUTH_CONTEXT',uid:verifiedUid},'*')
  }catch(e){}
 }
 window.addEventListener('DNY_VERIFIED_TEACHER',function(e){
  const uid=String(e.detail?.uid||'');
  if(!/^[a-zA-Z0-9_-]{6,128}$/.test(uid))return;
  verifiedUid=uid;deliver();
 });
 window.addEventListener('DNY_VERIFIED_TEACHER_CLEARED',function(){verifiedUid=''});
 window.addEventListener('message',function(e){
  if(e.data?.type==='DNY_AUTH_CONTEXT_REQUEST'&&e.source===frame()?.contentWindow)deliver();
 });
 function init(){if(frame())frame().addEventListener('load',function(){setTimeout(deliver,150)})}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
</script>'''
s=s[:start]+relay+s[end:]
p.write_text(s,encoding='utf-8')
print('Verified teacher UID now delivered to CCE after subscription approval; existing CCE data unchanged.')
