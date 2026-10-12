from common import *
import re,sqlite3
IMAGE={'PNG','WEBP','JPEG','BMP','TLG','DDS','ICO','GIF','TGA'}
AUDIO={'OGG','WAV','FLAC','MP3','FCD'}
VIDEO={'AVI','MP4','MPEG','ASF','MATROSKA','OGV'}
def route_for(logical,container,mapping=''):
    s=logical+' '+mapping;c=pathlib.Path(container).name.lower()
    if c=='saber.dat' or 'セイバールート' in s or 'セイバーエピローグ' in s:return 'Fate / Saber'
    if c=='rin.dat' or '凛ルート' in s or '凛エピローグ' in s:return 'Unlimited Blade Works / Rin'
    if c=='sakura.dat' or '桜ルート' in s or '桜エピローグ' in s:return "Heaven's Feel / Sakura"
    if 'プロローグ' in s:return 'Prologue'
    if '/resident/' in s or '/system/' in s:return 'System'
    return 'Unknown'
def classify(r,original_names=None):
    s=r['source_logical_path'].lower();c=r['source_container'].lower();fmt=r['detected_format'];ext=pathlib.Path(s).suffix
    if ext in {'.ogv','.mpg','.mpeg','.avi','.wmv','.mkv','.mp4'}:return 'Movies'
    if fmt in AUDIO:
        if 'voice' in c or '/voice/' in s or (fmt=='FCD' and re.match(r'^\d',pathlib.Path(s).name)):return 'Voice'
        if 'bgm' in c or '/bgm/' in s or pathlib.Path(s).name.startswith(('bgm','psbgm','op0')):return 'BGM'
        return 'SE'
    if fmt in IMAGE:
        if 'save_thumb' in c or '_thumb' in s:return 'SaveAssets'
        if original_names:
            cats=original_names.get(pathlib.Path(s).stem.casefold(),set())
            if len(cats)==1:return next(iter(cats))
        if 'fgimage' in c or '/fgimage/' in s:return 'Characters'
        if 'bgimage' in c or '/bgimage/' in s:return 'Backgrounds'
        if '/ui/' in s or '/image/' in s or pathlib.Path(c).name=='image.xp3':return 'UI'
        if '/effects/' in s or '/effect/' in s:return 'Effects'
        return 'Textures'
    if ext in {'.ttf','.otf','.ttc'} or fmt in {'TTF','OTF','TTC'}:return 'Fonts'
    if ext=='.epk':
        if re.search(r'uistring|statictext|uiconst|timeline|weapon_data|servant_data|correct_data|bgm_flag',s):return 'Database'
        return 'Localization' if '/locale/' in s else 'Dialogue'
    if ext=='.ks':return 'Scenario'
    if ext in {'.tjs','.ksc'}:return 'Scripts'
    if ext in {'.ksd','.last'}:return 'SaveAssets'
    if ext in {'.ini','.json','.xml','.cfg'}:return 'Config'
    if fmt.startswith('TEXT') or ext in {'.txt','.fdt','.csv'}:return 'Database' if 'data' in s or ext=='.fdt' else 'Metadata'
    if fmt=='PE':return 'Metadata'
    return 'Unknown'
def load_base():
    rows=[]
    for p in [L/'Original/Metadata/XP3_ENTRIES.jsonl',L/'Remastered/Metadata/DAT_ENTRIES.jsonl']:
        for line in p.open(encoding='utf-8'):
            r=json.loads(line);rows.append({k:r[k] for k in ['source_version','source_container','source_logical_path','extracted_path','size','sha256','detected_format']})
    fpd_logs=json.loads((W/'reports/FPD_LOG.json').read_text('utf-8'))
    for log in fpd_logs:
        p=pathlib.Path(log['source']);out=L/'Remastered/RawExtracted'/('BIN' if p.suffix=='.bin' else 'ROOT_FPD')/p.name
        for f in out.rglob('*'):
            if not f.is_file():continue
            with f.open('rb') as stream:b=stream.read(64)
            rows.append(dict(source_version='Remastered',source_container=log['source_container'],source_logical_path=f.relative_to(out).as_posix(),extracted_path=str(f),size=f.stat().st_size,sha256=sha(f),detected_format=signature(b,f.suffix)))
    inventory=json.loads((L/'Metadata/SOURCE_INVENTORY.json').read_text('utf-8'))
    for r in inventory:
        if r['detected_format'] in {'XP3','FPD'} or (r['source_version']=='Remastered' and r['relative_path'].startswith('obb/pack/') and r['extension']=='.dat'):continue
        src=pathlib.Path(r['absolute_path']);dst=L/r['source_version']/'RawExtracted/Loose'/r['relative_path'];dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():shutil.copy2(src,dst)
        rows.append(dict(source_version=r['source_version'],source_container='Loose',source_logical_path=r['relative_path'],extracted_path=str(dst),size=r['size'],sha256=r['sha256'],detected_format=r['detected_format']))
    rows.sort(key=lambda r:(r['source_version'],r['source_container'],r['source_logical_path'],r['extracted_path']))
    epk={r['source']:r for r in json.loads((L/'Remastered/Metadata/EPK_INDEX.json').read_text('utf-8'))};names=collections.defaultdict(set)
    for r in rows:
        if r['source_version']=='Original' and r['detected_format'] in IMAGE:names[pathlib.Path(r['source_logical_path']).stem.casefold()].add(classify(r))
    fields=['asset_id','source_version','source_container','source_logical_path','extracted_path','converted_path','filename','extension','detected_format','category','route','locale','character','width','height','alpha','duration','sample_rate','channels','codec','bitrate','fps','audio_tracks','size','sha256','duplicate_group','override_group','conversion_status','notes','thumbnail_path','phash','dhash','decrypted_path','script_mapping','text_encoding']
    for i,r in enumerate(rows,1):
        e=epk.get(r['extracted_path'],{});p=pathlib.Path(r['source_logical_path']);m=re.search(r'/locale/([^/]+)/',r['source_logical_path'])
        r.update(asset_id=f'FSN{i:06d}',filename=p.name,extension=p.suffix.lower(),category=classify(r,names),route=route_for(r['source_logical_path'],r['source_container'],e.get('script_mapping','')),locale=m.group(1) if m else ('ja' if r['source_version']=='Remastered' and (p.suffix=='.ks' or '/epk/' in r['source_logical_path']) else 'Unknown'),character='unknown',converted_path=e.get('text_path',''),decrypted_path=e.get('decrypted_path',''),script_mapping=e.get('script_mapping',''),text_encoding=e.get('encoding',''),conversion_status='decrypted_text' if e.get('readable_text') else 'pending',notes='')
        for k in fields:r.setdefault(k,'')
    with (W/'reports/BASE_ASSETS.jsonl').open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    jsonwrite(W/'reports/CATALOG_FIELDS.json',fields)
    groups=collections.defaultdict(list)
    for r in rows:groups[r['sha256']].append(r)
    plan={'logical_assets':len(rows),'unique_payloads':len(groups),'duplicate_payloads':sum(len(v)-1 for v in groups.values()),'categories':dict(collections.Counter(r['category'] for r in rows)),'format':dict(collections.Counter(r['detected_format'] for r in rows)),'size':sum(r['size'] for r in rows),'unique_size':sum(v[0]['size'] for v in groups.values()),'image_unique':sum(v[0]['detected_format'] in IMAGE for v in groups.values()),'disk_free':shutil.disk_usage('E:/').free}
    jsonwrite(W/'reports/CONVERSION_PLAN.json',plan);print(json.dumps(plan),flush=True)
    return rows
if __name__=='__main__':load_base()
