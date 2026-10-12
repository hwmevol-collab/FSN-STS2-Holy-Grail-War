"""Reusable FFmpeg edit. All paths derive from this file; no project writes.
Run with the bundled Python (Pillow is only needed for make_art.py).
Adjust deliverables/timeline.json after the first render, then run again.
"""
from pathlib import Path
import json, subprocess, re, sys
R=Path(__file__).resolve().parent
FF=Path('D:/FormatFactory/ffmpeg.exe')
OUT=R/'deliverables';TMP=R/'temp';OUT.mkdir(exist_ok=True)
def meta(name):return json.loads((R/'raw'/f'{name}.json').read_text(encoding='utf-8'))
def event(name,card=None,cmd='play'):
    for e in meta(name)['events']:
        if e['command']==cmd and (card is None or e.get('params',{}).get('card')==card):return round(e['time'],3)
    raise ValueError((name,card,cmd))
def default_timeline():
    rin='03_rin_magic';arc='04_archer_projection';sw='05_dual_switch';b='06_projection_build';deck='07_dual_decks'
    return [
      [b,event(b,'ARM_KANSHOU_BAKUYA')+1.6,3,'opening real projection'],
      ['01_character_select',4,6,'Rin and Archer selection'],
      [rin,event(rin,'RIN_S_JEWEL_PREPARATION'),4,'jewel preparation'],
      [rin,event(rin,'RIN_S_GANDR'),5,'boosted Gandr'],
      [rin,event(rin,'RIN_S_MANA_SUPPLY'),4,'mana supply'],
      [rin,event(rin,'RIN_S_JEWEL_RELEASE'),4,'jewel release'],
      [arc,event(arc,'ARC_S_TRACE'),5,'projection choice'],
      [arc,event(arc,'ARM_KANSHOU_BAKUYA'),4,'Kanshou Bakuya'],
      [arc,event(arc,'ARC_S_CLOSE_COMBAT'),4,'dual sword attack'],
      [arc,event(arc,'ARC_S_BOW_SHOT'),4,'bow attack'],
      [sw,0,4,'both HP and hands before switch'],
      [sw,event(sw,cmd='switch'),6,'native switch and retained hands'],
      [sw,event(sw,'ARC_S_CLOSE_COMBAT'),4,'continuous card play'],
      [b,event(b,'ARC-R13'),4,'zero mana engine'],
      [b,event(b,'ARC-R08'),4,'projection engine'],
      [b,event(b,'ARM_KANSHOU_BAKUYA'),3,'generated arms'],
      [b,event(b,'ARM_HRUNTING'),4,'Hrunting burst'],
      [deck,0,4,'Rin permanent deck'],
      [deck,event(deck,cmd='tab')+1.5,4,'Archer permanent deck'],
      ['OUTRO',0,10,'beta limitations and future goal'],
    ]
SUBS=[(0,3,'以宝石为术，以投影为剑。'),(3,9,'Fate/stay night × Slay the Spire 2\n免费非官方 MOD'),
(9,17,'远坂凛：甘德与宝石魔术'),(17,26,'积攒宝石，强化下一次进攻'),
(26,34,'Archer：投影兵装'),(34,43,'双刀与弓矢，接续攻势'),
(43,49,'双人切换，双方手牌保留'),(49,57,'独立牌组与生命，共享能量与资源'),
(57,65,'让投影构筑运转起来'),(65,72,'兵装接力，打出你的组合'),
(72,80,'两套永久牌组，两种战斗思路'),
(80,85,'未来开发目标：七组御主与从者参与圣杯战争'),
(85,90,'欢迎 BUG、数值、卡牌、遗物与内容建议')]
def stamp(t,ass=False):
    if ass:return f'{int(t)//3600}:{int(t)//60%60:02}:{int(t)%60:02}.{round(t%1*100):02}'
    return f'{int(t)//3600:02}:{int(t)//60%60:02}:{int(t)%60:02},{round(t%1*1000):03}'
def subs():
    srt='\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{s}' for i,(a,b,s) in enumerate(SUBS))+'\n'
    (OUT/'FSN_Trailer.zh-CN.srt').write_text(srt,encoding='utf-8-sig')
    ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Main,Microsoft YaHei,44,&H00ECF1FA,&H00FFFFFF,&H00201713,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,8,120,120,104,1
Style: Footer,Microsoft YaHei,35,&H00ECF1FA,&H00FFFFFF,&H00201713,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,100,100,38,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
    for a,b,s in SUBS:ass+=f'Dialogue: 0,{stamp(a,True)},{stamp(b,True)},{"Footer" if a>=80 else "Main"},,0,0,0,,{s.replace(chr(10),r"\N")}\n'
    (OUT/'FSN_Trailer.zh-CN.ass').write_text(ass,encoding='utf-8-sig')
def run(args,log):
    with (TMP/log).open('w',encoding='utf-8') as f:
        p=subprocess.run([str(FF),'-hide_banner','-y',*map(str,args)],stdout=f,stderr=f)
    if p.returncode:raise RuntimeError(f'FFmpeg failed: {TMP/log}')
def render():
    timeline=OUT/'timeline.json'
    if not timeline.exists():
        rows=default_timeline();pos=0;items=[]
        for source,start,duration,label in rows:
            items.append(dict(source=source,in_seconds=start,duration_seconds=duration,out_seconds=pos,label=label));pos+=duration
        timeline.write_text(json.dumps(dict(version='v0.9.4',workshop='3818087982',duration=pos,fps=60,clips=items),ensure_ascii=False,indent=2),encoding='utf-8')
    data=json.loads(timeline.read_text(encoding='utf-8'));subs()
    files=[]
    for i,c in enumerate(data['clips']):
        name=TMP/f'cut-{i:02}.mp4';files.append(name)
        if c['source']=='OUTRO':inputs=['-loop','1','-framerate','60','-i',TMP/'outro.png','-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
        else: inputs=['-ss',c['in_seconds'],'-i',R/'raw'/f'{c["source"]}.mkv']
        if '--final-only' not in sys.argv: run([*inputs,'-t',c['duration_seconds'],'-vf','scale=1920:1080:in_range=full:out_range=tv,fps=60,format=yuv420p,setsar=1',
             '-c:v','h264_nvenc','-preset','p5','-rc','vbr','-cq','20','-b:v','16M','-maxrate','24M','-bufsize','32M',
             '-c:a','aac','-ar','48000','-ac','2','-b:a','192k','-video_track_timescale','60000',name],f'cut-{i:02}.log')
        print(f'cut {i+1}/{len(data["clips"])} {c["label"]}',flush=True)
    listing=TMP/'concat.txt';listing.write_text('\n'.join("file '"+p.as_posix()+"'" for p in files),encoding='utf-8')
    if '--final-only' not in sys.argv: run(['-f','concat','-safe','0','-i',listing,'-c','copy',TMP/'assembly.mp4'],'concat.log')
    # Original game sound remains aligned with its matching clip. Background music is a separate input.
    music=R/'runtime/game/mods/RinArcherCore/Presentation/Audio/this-illusion-remix.ogg'
    video="fps=60,ass=deliverables/FSN_Trailer.zh-CN.ass:fontsdir=C\\:/Windows/Fonts"
    audio='[0:a]volume=1.0,asplit[game][key];[1:a]volume=0.65,afade=t=in:d=1.5,afade=t=out:st=86:d=4[music];[music][key]sidechaincompress=threshold=0.04:ratio=4:attack=8:release=250[ducked];[game][ducked]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=false[outa]'
    run(['-i',TMP/'assembly.mp4','-ss','12','-i',music,'-filter_complex',audio,'-vf',video,'-map','0:v','-map','[outa]',
         '-t','90','-c:v','h264_nvenc','-preset','p5','-rc','vbr','-cq','19','-b:v','18M','-maxrate','26M','-bufsize','36M',
         '-r','60','-fps_mode','cfr','-pix_fmt','yuv420p','-color_range','tv','-colorspace','bt709','-color_trc','bt709','-color_primaries','bt709',
         '-c:a','aac','-b:a','320k','-ar','48000','-movflags','+faststart','-metadata','title=FSN Public Beta v0.9.4 - First Cut',
         OUT/'FSN_Trailer_v01_1080p60.mp4'],'final-render.log')
    print(OUT/'FSN_Trailer_v01_1080p60.mp4',flush=True)
if __name__=='__main__':
    import os
    os.chdir(R)
    render()
