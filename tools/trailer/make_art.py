from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
R=Path(__file__).resolve().parent
A=R/'runtime/game/mods/RinArcherCore/Presentation/Assets'
OUT=R/'deliverables'; OUT.mkdir(exist_ok=True)
FONT='C:/Windows/Fonts/msyh.ttc'
def font(n): return ImageFont.truetype(FONT,n)
def text(draw,xy,s,size,color='#f8efe0'):
    draw.text(xy,s,font=font(size),fill=color,stroke_width=2,stroke_fill='#12131a')
def base():
    im=Image.open(A/'contract-landscape.png').convert('RGB').resize((1920,1080))
    im=ImageEnhance.Brightness(im).enhance(.40).convert('RGBA')
    for name,x,y,h in [('select-archer.png',1080,0,1150),('select-rin.png',720,135,1040)]:
        p=Image.open(A/name).convert('RGBA');p=p.resize((round(p.width*h/p.height),h))
        im.alpha_composite(p,(x,y))
    shade=Image.new('RGBA',im.size);sd=ImageDraw.Draw(shade)
    for x in range(1920): sd.line((x,0,x,1080),fill=(9,10,18,round(230*max(0,1-x/1200))))
    im=Image.alpha_composite(im,shade)
    logo=Image.open(A/'fsn-logo.png').convert('RGBA');logo.thumbnail((590,320));im.alpha_composite(logo,(86,65))
    return im
im=base();d=ImageDraw.Draw(im)
text(d,(88,389),'× Slay the Spire 2',54)
text(d,(82,511),'凛与 Archer 参战',84,'#f3d07a')
text(d,(88,638),'宝石魔术 · 投影兵装 · 双人切换',37)
d.rounded_rectangle((88,760,681,827),radius=8,fill='#a3293f')
text(d,(108,773),'Public Beta v0.9.4 已公开',34)
text(d,(88,867),'免费非官方 MOD',35)
text(d,(88,935),'现阶段仅凛与 Archer 可玩',29,'#d4c5b0')
im.convert('RGB').save(OUT/'FSN_Trailer_Cover.png')
im=base();d=ImageDraw.Draw(im)
text(d,(88,395),'× Slay the Spire 2',54)
text(d,(88,495),'免费非官方 MOD',59,'#f3d07a')
text(d,(88,590),'Public Beta v0.9.4',43)
text(d,(88,667),'仅凛与 Archer 可玩',37)
text(d,(88,737),'大量内容未完成，仍有 BUG',37)
text(d,(88,818),'欢迎 BUG、数值、卡牌、遗物与内容建议',30)
text(d,(88,886),'Steam Workshop  3818087982',33,'#f3d07a')
im.convert('RGB').save(R/'temp/outro.png')
print(OUT/'FSN_Trailer_Cover.png')
