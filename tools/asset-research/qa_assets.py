from common import *
import subprocess,random,sqlite3
from PIL import Image,ImageDraw,ImageFont
FFPROBE='D:/DDplay/ffmpeg/ffprobe.exe';FFMPEG='D:/DDplay/ffmpeg/ffmpeg.exe'
def run():
    path=L/'Metadata/ASSET_CATALOG.jsonl';rows=[json.loads(s) for s in (path if path.exists() else W/'reports/BASE_ASSETS.jsonl').open(encoding='utf-8')]
    if not path.exists():
        cv={r['sha256']:r for r in map(json.loads,(W/'reports/CONVERSION_RESULTS.jsonl').open(encoding='utf-8'))}
        for r in rows:r.update({k:v for k,v in cv.get(r['sha256'],{}).items() if k!='sha256'})
    rng=random.Random(20261006);samples={}
    for r in rows:
        if r['converted_path'] and (r['category'] in {'BGM','Voice','SE','Movies'} or r['detected_format']=='FCD'):
            samples.setdefault((r['source_version'],r['source_container'],r['category'],r.get('decrypt_method','')),[]).append(r)
    checks=[]
    for key,items in sorted(samples.items()):
        r=rng.choice(items);p=r['converted_path'];cmd=[FFPROBE,'-v','error','-show_format','-show_streams','-of','json',p];proc=subprocess.run(cmd,capture_output=True,timeout=90);data=json.loads(proc.stdout) if proc.returncode==0 else {}
        # Full decoding of short audio and the first 20 seconds of each video exercises actual codecs.
        cmd2=[FFMPEG,'-v','error','-i',p]
        if r['category']=='Movies' or float(r.get('duration') or 0)>180:cmd2+=['-t','20']
        cmd2+=['-f','null','-'];dec=subprocess.run(cmd2,capture_output=True,timeout=180)
        checks.append(dict(asset_id=r['asset_id'],source_version=r['source_version'],container=r['source_container'],category=r['category'],file=p,probe_exit=proc.returncode,decode_exit=dec.returncode,streams=data.get('streams',[]),format=data.get('format',{}),stderr=proc.stderr.decode('utf-8',errors='replace')+dec.stderr.decode('utf-8',errors='replace'),probe_command=subprocess.list2cmdline(cmd),decode_command=subprocess.list2cmdline(cmd2)))
        print('MEDIA_QA',r['asset_id'],proc.returncode,dec.returncode,flush=True)
    jsonwrite(L/'Reports/MEDIA_SAMPLE_QA.json',checks)
    images=[]
    terms=['01星空','01月夜','アーチャー01a','セイバー01','003-バス停','01汎用セイバー','bg0001']
    for ver in ['Original','Remastered']:
        candidates=[r for r in rows if r['source_version']==ver and r.get('thumbnail_path') and any(t in r['filename'] for t in terms)]
        seen=set()
        for r in candidates:
            if r['source_container'] not in seen:images.append(r);seen.add(r['source_container'])
            if len(seen)>=8:break
    images=images[:16];sheet=Image.new('RGB',(1280,math.ceil(len(images)/4)*250),'#e9edf2');draw=ImageDraw.Draw(sheet)
    try:font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
    except OSError:font=ImageFont.load_default()
    for i,r in enumerate(images):
        x=(i%4)*320;y=(i//4)*250
        with Image.open(r['converted_path']) as im:
            im=im.convert('RGBA');im.thumbnail((310,208));sheet.paste(im,(x+(320-im.width)//2,y),im)
        draw.text((x+8,y+210),r['asset_id']+' '+r['source_version'],fill='#142030',font=font);draw.text((x+8,y+230),r['filename'][:26],fill='#142030',font=font)
    sheet.save(L/'Reports/IMAGE_VISUAL_QA.jpg',quality=90);jsonwrite(L/'Reports/IMAGE_VISUAL_QA.json',[dict(asset_id=r['asset_id'],source_version=r['source_version'],file=r['converted_path']) for r in images])
    jsonwrite(W/'reports/QA_SUMMARY.json',{'media_samples':len(checks),'media_failures':sum(c['probe_exit']!=0 or c['decode_exit']!=0 for c in checks),'visual_image_samples':len(images)})
if __name__=='__main__':
    import math
    run()
