"""FSN animation reference pipeline. Source trees are read-only; all writes use E:."""
import os, sys, pathlib, json, csv, hashlib, sqlite3, shutil, datetime, re, subprocess, collections, time, unicodedata
sys.stdout.reconfigure(encoding='utf-8')
W=pathlib.Path('E:/FSN_MASTER_ASSET_WORK'); L=pathlib.Path('E:/FSN_MASTER_ASSET_LIBRARY'); S=pathlib.Path('E:/BaiduNetdiskDownload/FSN/素材')
A=L/'AnimationReferences'; M=A/'Metadata'; T=W/'animation-reference'; B=W/'backups/animation-reference-pre'
PY=W/'tools/python/Scripts/python.exe'; FF=pathlib.Path('D:/DDplay/ffmpeg/ffmpeg.exe'); FP=FF.with_name('ffprobe.exe'); PLAY=FF.with_name('ffplay.exe')
for d in [M,T,B,W/'tmp/animation-reference',W/'logs'] : d.mkdir(parents=True,exist_ok=True)
os.environ.update(TEMP=str(W/'tmp/animation-reference'),TMP=str(W/'tmp/animation-reference'),PIP_CACHE_DIR=str(W/'tmp/pip'),PYTHONPYCACHEPREFIX=str(W/'tmp/pycache'),OMP_NUM_THREADS='2')
VIDEO_EXT={'.mkv','.mp4','.m2ts','.mts','.ts','.avi','.webm','.mov','.mpeg','.mpg','.ogv','.wmv','.flv','.vob','.m4v'}
SUB_EXT={'.ass','.ssa','.srt','.vtt','.sup','.pgs'}; FONT_EXT={'.ttf','.otf','.ttc','.woff','.woff2'}
EXCLUDES={'fate stay night','fate stay night remastered','fate hollow ataraxia','fateunlimitedcodesportable_europe','referencebooks','fsn_master_asset_library'}
def excluded(n):return n.lower() in EXCLUDES or 'material' in n.lower() or 'fate-unlimited codes' in n.lower()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def log(*v):print(now(),*v,flush=True)
def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(q,p)
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def jl(p,rows):
    p=pathlib.Path(p);q=p.with_name(p.name+'.tmp');q.parent.mkdir(parents=True,exist_ok=True)
    with q.open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    os.replace(q,p)
def readjl(p):
    with pathlib.Path(p).open(encoding='utf-8-sig') as f:return [json.loads(x) for x in f if x.strip()]
def csvout(p,rows,fields=None):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);fields=fields or list(dict.fromkeys(k for r in rows for k in r));q=p.with_name(p.name+'.tmp')
    with q.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
    os.replace(q,p)
def tc(ms):
    ms=round(ms);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}.{ms%1000:03d}'
def command(args,timeout=180):
    p=subprocess.run([str(x) for x in args],capture_output=True,timeout=timeout,encoding='utf-8',errors='replace',creationflags=0x08000000)
    if p.returncode:raise RuntimeError(p.stderr[-6000:])
    return p.stdout
def source_files():
    rows=[]
    for root,ds,fs in os.walk(S,followlinks=False):
        ds[:]=[d for d in ds if d.lower() not in EXCLUDES and not (pathlib.Path(root)==S and excluded(d)) and not (pathlib.Path(root)/d).is_symlink() and not os.path.isjunction(pathlib.Path(root)/d)]
        rows.extend(pathlib.Path(root)/f for f in fs)
    return sorted(rows,key=lambda p:str(p.relative_to(S)).casefold())
def magic(p):
    with open(p,'rb') as f:b=f.read(4096)
    if b.startswith(b'\x1aE\xdf\xa3'):return 'matroska'
    if b[4:8]==b'ftyp':return 'iso_bmff'
    if b.startswith(b'RIFF') and b[8:12]==b'AVI ':return 'avi'
    if b.startswith(b'OggS'):return 'ogg'
    if b.startswith(b'\x00\x00\x01\xba'):return 'mpeg'
    if b.startswith(b'\x30\x26\xb2\x75'):return 'asf'
    if b.startswith(b'FLV'):return 'flv'
    if len(b)>376 and all(b[i]==0x47 for i in [0,188,376]):return 'mpegts'
    return 'other'
def frozen_baseline():
    dest=L/'Reports/ANIMATION_REFERENCE_PRE_INTEGRATION_BASELINE.json'
    if dest.exists():return read(dest)
    catalogs={}
    for ext in ['csv','jsonl','sqlite']:
        p=L/('Metadata/ASSET_CATALOG.'+ext);q=B/p.relative_to(L);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);h=sha(p);assert h==sha(q);catalogs[ext]={'sha256':h,'size':p.stat().st_size}
    db=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite')+'?mode=ro',uri=True);count,maxid=db.execute('select count(*),max(asset_id) from assets').fetchone();integrity=db.execute('pragma integrity_check').fetchone()[0];db.close()
    assert (count,maxid,integrity)==(270461,'FSN270461','ok'),(count,maxid,integrity)
    manifest=[];summary={}
    for directory in ['Gallery','ReferenceBooks','Reports']:
        size=0;n=0
        for root,ds,fs in os.walk(L/directory):
            for name in fs:
                p=pathlib.Path(root)/name;st=p.stat();r={'path':str(p.relative_to(L)),'size':st.st_size,'mtime_ns':st.st_mtime_ns,'sha256':sha(p)};manifest.append(r);size+=st.st_size;n+=1
                if p.suffix.lower() in {'.html','.js','.css','.json','.jsonl','.md','.csv','.sqlite','.ps1'}:
                    q=B/p.relative_to(L);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        summary[directory]={'files':n,'bytes':size};log('Frozen',directory,n)
    jl(B/'PROTECTED_MANIFEST.jsonl',manifest)
    result={'created_at':now(),'asset_total':count,'max_id':maxid,'sqlite_integrity':integrity,'catalogs':catalogs,'protected':summary,'disk_free_before':shutil.disk_usage(L).free,'backup':str(B),'no_raw_or_video_copies':True}
    save(dest,result);save(B/'BASELINE.json',result);return result
