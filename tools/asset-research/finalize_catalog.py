from common import *
from catalog_base import classify,IMAGE,VIDEO,route_for
import re,sqlite3,math
def run():
    rows=[json.loads(s) for s in (W/'reports/BASE_ASSETS.jsonl').open(encoding='utf-8')];results={r['sha256']:r for r in map(json.loads,(W/'reports/CONVERSION_RESULTS.jsonl').open(encoding='utf-8'))};groups=collections.defaultdict(list);overrides=collections.defaultdict(list)
    if (W/'reports/PE_CONVERSION_RESULTS.jsonl').exists():results.update({r['sha256']:r for r in map(json.loads,(W/'reports/PE_CONVERSION_RESULTS.jsonl').open(encoding='utf-8'))})
    typed_voice=set(json.loads((W/'reports/SCRIPT_SUMMARY.json').read_text('utf-8')).get('explicit_voice_asset_ids',[])) if (W/'reports/SCRIPT_SUMMARY.json').exists() else set()
    for r in rows:
        cv=results.get(r['sha256'],{});r.update({k:v for k,v in cv.items() if k!='sha256'});groups[r['sha256']].append(r)
        if r['source_version']=='Original':overrides[r['source_logical_path'].casefold()].append(r)
        if r['extension'] in {'.fcf','.tl'}:r['category']='Database'
        if r['extension'] in {'.vert','.frag','.asd'}:r['category']='Scripts'
        if r['extension'] in {'.tft'}:r['category']='Fonts';r['detected_format']='KIRIKIRI_PRERENDERED_FONT'
        if r['extension'] in {'.ftpr'}:r['category']='Fonts';r['detected_format']='FTPR_FONT_RESOURCE';r['notes']='Engine font cache/metrics resource identified from filename and header; internal fields remain unresolved; original OTF/TTF files separately preserved'
        if r['extension']=='.gutb':r['detected_format']='GUTC_COMPILED_UI';r['category']='UI';r['notes']='Compiled engine UI binary; all bytes retained'
        if r['extension']=='.gut':r['category']='UI'
        if r['extension']=='.ico':r['category']='Icons'
        if r['detected_format'] in VIDEO or r['extension']=='.ogv':r['category']='Movies'
        if r['detected_format']=='FCD' and '@' in r['filename']:r['category']='Voice';r['notes']='Dialogue storage variant suffix present; confirmed script references indexed separately'
        if r['asset_id'] in typed_voice:r['category']='Voice';r['notes']='Confirmed @say/voice storage reference; see ASSET_REFERENCES.csv'
        if r['extension'] in {'.dat'} and r['conversion_status']=='utf8_text':r['category']='Metadata'
        if r['detected_format'] in {'TEXT','TIMELINE_JSON','GUI_XML','EMPTY_TEXT'} and r['category']=='Unknown':r['category']='Metadata'
        if r['locale']=='Unknown' and r['source_version']=='Original':
            for name,loc in [('patchjp','ja'),('patchsc','zh-Hans'),('patchtc','zh-Hant'),('patchtw','zh-Hant')]:
                if name in r['source_container']:r['locale']=loc
    exact=[]
    for digest,items in groups.items():
        if len(items)>1:
            for r in items:r['duplicate_group']='SHA256:'+digest;exact.append(dict(duplicate_group=r['duplicate_group'],asset_id=r['asset_id'],source_version=r['source_version'],source_container=r['source_container'],logical_path=r['source_logical_path'],extracted_path=r['extracted_path'],size=r['size'],sha256=digest))
    override_rows=[]
    for logical,items in overrides.items():
        if len(items)<2:continue
        changed=len({r['sha256'] for r in items})>1
        for r in items:
            r['override_group']='OVR:'+hashlib.sha256(logical.encode('utf8')).hexdigest()[:16];container=r['source_container'];m=re.match(r'patch(\d*)\.xp3$',container,re.I)
            priority=(int(m.group(1) or 1) if m else '')
            note='Numbered-patch priority is a candidate; locale and Realta load configuration is not proven'
            override_rows.append(dict(logical_path=r['source_logical_path'],archive=container,hash=r['sha256'],size=r['size'],possible_priority=priority,duplicate_or_changed='same_path_changed_content' if changed else 'same_path_identical',asset_id=r['asset_id'],notes=note))
    csvwrite(L/'Metadata/DUPLICATES_EXACT.csv',exact,['duplicate_group','asset_id','source_version','source_container','logical_path','extracted_path','size','sha256'])
    csvwrite(L/'Metadata/ORIGINAL_OVERRIDE_MAP.csv',override_rows,['logical_path','archive','hash','size','possible_priority','duplicate_or_changed','asset_id','notes'])
    # Canonical contains one physical payload per content hash via library-internal hardlinks.
    categories=['Characters','CG','Backgrounds','Foregrounds','Effects','UI','Icons','Weapons','Items','CommandSpells','Magic','Sprites','Textures','Movies','BGM','Voice','SE','Scripts','Dialogue','Scenario','Database','Localization','Fonts','Config','SaveAssets','Metadata','Unknown']
    for cat in categories:(L/'Canonical'/cat).mkdir(parents=True,exist_ok=True)
    hardlinks=[]
    for i,(digest,items) in enumerate(groups.items()):
        first=items[0];source=pathlib.Path(first['extracted_path']);suffix=source.suffix if len(source.suffix)<15 else '.bin';target=L/'Canonical'/first['category']/(digest+suffix)
        if not target.exists():os.link(source,target)
        for r in items:r['canonical_path']=str(target)
        hardlinks.append(dict(sha256=digest,canonical_path=str(target),raw_reference=str(source),method='NTFS hardlink within output library',reference_count=len(items)))
        if i%10000==0:print('CANONICAL',i,'/',len(groups),flush=True)
    csvwrite(L/'Metadata/HARDLINKS.csv',hardlinks)
    for ver in ['Original','Remastered']:
        csvwrite(L/ver/'Converted/WORKING_COPY_INDEX.csv',[dict(asset_id=r['asset_id'],logical_path=r['source_logical_path'],source_container=r['source_container'],working_path=r['converted_path'],status=r['conversion_status']) for r in rows if r['source_version']==ver])
    unknown=[]
    for r in rows:
        if r['detected_format']=='UNKNOWN' or r['conversion_status'] in {'unresolved_preserved','failed_preserved'} or r['detected_format'] in {'FTPR_FONT_RESOURCE','GUTC_COMPILED_UI'}:
            p=pathlib.Path(r['extracted_path']);b=p.open('rb').read(65536);c=collections.Counter(b);entropy=-sum((n/len(b))*math.log2(n/len(b)) for n in c.values()) if b else 0
            unknown.append(dict(file=str(p),asset_id=r['asset_id'],source_container=r['source_container'],size=r['size'],sha256=r['sha256'],first_64_bytes_hex=b[:64].hex(),probable_format=r['detected_format'],entropy=round(entropy,4),status=r['conversion_status'],notes=r.get('error','') or r['notes']))
    csvwrite(L/'Metadata/UNKNOWN_FORMATS.csv',unknown,['file','asset_id','source_container','size','sha256','first_64_bytes_hex','probable_format','entropy','status','notes'])
    clusters=collections.defaultdict(list)
    for r in unknown:clusters[(r['probable_format'],r['first_64_bytes_hex'][:16],pathlib.Path(r['file']).suffix)].append(r)
    csvwrite(L/'Metadata/UNKNOWN_CLUSTERS.csv',[dict(format=k[0],magic=k[1],extension=k[2],count=len(v),bytes=sum(r['size'] for r in v),example=v[0]['file']) for k,v in sorted(clusters.items(),key=lambda x:sum(r['size'] for r in x[1]),reverse=True)])
    fields=json.loads((W/'reports/CATALOG_FIELDS.json').read_text('utf-8'))
    fields+=['error','encoding_note','working_sha256','decrypt_method','canonical_path']
    for r in rows:
        for k in fields:r.setdefault(k,'')
    csvwrite(L/'Metadata/ASSET_CATALOG.csv',rows,fields)
    with (L/'Metadata/ASSET_CATALOG.jsonl').open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps({k:r[k] for k in fields},ensure_ascii=False)+'\n')
    db=sqlite3.connect(L/'Metadata/ASSET_CATALOG.sqlite');db.execute('DROP TABLE IF EXISTS assets');numeric={'width','height','duration','sample_rate','channels','size','bitrate','audio_tracks'}
    db.execute('CREATE TABLE assets('+','.join('"'+k+'" '+('REAL' if k in numeric else 'TEXT') for k in fields)+')');db.executemany('INSERT INTO assets VALUES ('+','.join('?' for k in fields)+')',[tuple(r[k] if not isinstance(r[k],bool) else int(r[k]) for k in fields) for r in rows])
    for k in ['asset_id','sha256','source_version','source_container','source_logical_path','category','route','filename']:db.execute('CREATE INDEX idx_'+k+' ON assets("'+k+'")')
    db.commit();db.close()
    jsonwrite(W/'reports/CATALOG_SUMMARY.json',{'logical_assets':len(rows),'unique_payloads':len(groups),'exact_duplicate_groups':sum(len(v)>1 for v in groups.values()),'duplicate_records':sum(len(v)-1 for v in groups.values()),'formats':dict(collections.Counter(r['detected_format'] for r in rows)),'categories':dict(collections.Counter(r['category'] for r in rows)),'conversion_status':dict(collections.Counter(r['conversion_status'] for r in rows)),'unknown_list_count':len(unknown),'unrecognized_count':sum(r['detected_format']=='UNKNOWN' for r in rows),'failed_count':sum(r['conversion_status']=='failed_preserved' for r in rows)})
    print('CATALOG DONE',len(rows),flush=True)
if __name__=='__main__':run()
