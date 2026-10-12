from common import *
import sqlite3

def run():
    db=sqlite3.connect(L/'Metadata/ASSET_CATALOG.sqlite');integrity=[r[0] for r in db.execute('PRAGMA integrity_check')];dbcount=db.execute('SELECT count(*) FROM assets').fetchone()[0]
    with (L/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:csvcount=sum(1 for _ in csv.DictReader(f))
    with (L/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8') as f:jsoncount=sum(1 for line in f if json.loads(line))
    totals={}
    queries={'version':'source_version','format':'detected_format','category':'category','conversion':'conversion_status','route':'route','locale':'locale'}
    for name,col in queries.items():totals[name]={r[0]:r[1] for r in db.execute(f'SELECT "{col}",count(*) FROM assets GROUP BY "{col}"')}
    per_version=[]
    for ver in ('Original','Remastered'):
        q=lambda expr:db.execute('SELECT count(*) FROM assets WHERE source_version=? AND ('+expr+')',(ver,)).fetchone()[0]
        images=q("detected_format IN ('PNG','WEBP','JPEG','BMP','TLG','ICO','PE_RESOURCE_ICON')")
        audio=q("conversion_status IN ('native_audio','decrypted_ogg')")
        video=q("conversion_status='native_video'")
        text=q("conversion_status IN ('utf8_text','decrypted_text')")
        scripts=q("extension IN ('.ks','.tjs','.ksc','.asd','.vert','.frag')")
        total=q('1=1');per_version.append(dict(version=ver,total=total,images=images,audio=audio,video=video,script_files=scripts,text_files_including_scripts=text,other=total-images-audio-video-text,unresolved=q("conversion_status='unresolved_preserved'")))
    required=['SOURCE_INVENTORY.csv','SOURCE_INVENTORY.json','ASSET_CATALOG.csv','ASSET_CATALOG.jsonl','ASSET_CATALOG.sqlite','ORIGINAL_OVERRIDE_MAP.csv','ORIGINAL_VS_REMASTERED.csv','DUPLICATES_EXACT.csv','IMAGE_SIMILARITY.csv','SCRIPT_INDEX.csv','VOICE_INDEX.csv','VOICE_DIALOGUE_MAPPING.csv','ASSET_REFERENCES.csv','UNKNOWN_FORMATS.csv','EXTRACTION_LOG.csv','EXTRACTION_FAILURES.csv','FCD_INDEX.csv','DATABASE_INDEX.csv','MEDIA_TECHNICAL.csv','HARDLINKS.csv','CONTACT_SHEETS.csv']
    files={n:(L/'Metadata'/n).is_file() for n in required};counts={}
    for n in ['SCRIPT_INDEX.csv','VOICE_INDEX.csv','VOICE_DIALOGUE_MAPPING.csv','ASSET_REFERENCES.csv','DATABASE_INDEX.csv','UNKNOWN_FORMATS.csv','EXTRACTION_LOG.csv','EXTRACTION_FAILURES.csv','FCD_INDEX.csv']:
        with (L/'Metadata'/n).open(encoding='utf-8-sig',newline='') as f:counts[n]=sum(1 for _ in csv.DictReader(f))
    result=dict(checked_at=now(),sqlite_integrity=integrity,catalog_counts=dict(sqlite=dbcount,csv=csvcount,jsonl=jsoncount),required_indices=files,index_row_counts=counts,totals=totals,per_version_media=per_version,pass_=integrity==['ok'] and dbcount==csvcount==jsoncount and all(files.values()))
    jsonwrite(L/'Reports/ACCEPTANCE_AUDIT.json',result);db.close();print('ACCEPTANCE',result['pass_'],dbcount,counts,flush=True)
    if not result['pass_']:raise RuntimeError('Acceptance audit failed')
if __name__=='__main__':run()
