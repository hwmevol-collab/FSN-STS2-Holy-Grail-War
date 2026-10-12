from fuc_anim_common import *
old="if(!data){if(notice)notice.textContent=notice.textContent.split(' · ')[0]+' · 运动通道已解码 · 骨骼绑定 / 播放未验证';continue;}"
new="if(!data){if(notice)notice.textContent=notice.textContent.split(' · ')[0]+' · 运动通道已解码 · 骨骼绑定 / 播放未验证';else if(body.textContent.includes('8ing_MOT')){const n=document.createElement('div');n.className='meta';n.textContent='运动通道已解码 · 整包骨骼绑定 / 播放未完整验证；已验证片段请单独查看';body.append(n);}continue;}"
for p in [L/'Gallery/fuc_animation_overlay.js',W/'scripts/fuc_anim_integrate.py']:
    s=p.read_text('utf-8')
    if old in s:p.write_text(s.replace(old,new),encoding='utf-8')
    else:assert new in s
