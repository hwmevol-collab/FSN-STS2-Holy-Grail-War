from fuc_anim_common import *
p=EU/'Converted/AnimatedModels/viewer/index.html'
s=p.read_text('utf-8')
if 'async function saveEvidence' not in s:
    s=s.replace("const clips=await", "async function saveEvidence(name,body,type){const response=await fetch('http://127.0.0.1:8998/evidence?name='+encodeURIComponent(name),{method:'POST',headers:{'Content-Type':type},body});if(!response.ok)throw new Error('Evidence receiver '+response.status);}\nconst clips=await")
    s=s.replace("const link=document.querySelector('#validationDownload');", "await saveEvidence(select.value.split('/').pop().replace('.glb','.viewer-validation.json'),JSON.stringify(result,null,2),'application/json');out.textContent+=' · 证据已保存';const link=document.querySelector('#validationDownload');")
    s=s.replace("rec.onstop=()=>{const a=", "rec.onstop=async()=>{const blob=new Blob(chunks,{type:'video/webm'});await saveEvidence(select.value.split('/').pop().replace('.glb','.webm'),blob,'video/webm');status.textContent+='\\nWebM 预览已保存';const a=")
    p.write_text(s,encoding='utf-8')
log('EVIDENCE RECEIVER WIRED',p)
