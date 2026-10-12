"""Freeze the existing library, copy only indexes, and inventory FHA read-only."""
from common import *
import sqlite3,re,mmap,sys
ROOT=pathlib.Path('E:/BaiduNetdiskDownload/FSN/素材/Fate hollow ataraxia')
FHA=L/'HollowAtaraxia';FW=W/'fha';BACK=W/'backups/fha-pre-integration'
def freeze():
    target=L/'Reports/FHA_PRE_INTEGRATION_BASELINE.json'
    if target.exists():
        print('Existing immutable baseline',target,flush=True);return
    assert not BACK.exists(), 'Do not overwrite an earlier backup'
    BACK.mkdir(parents=True)
    files=list((L/'Metadata').glob('*'))+list((L/'Gallery').glob('*.html'))+list((L/'Gallery').glob('*.js'))
    files+=[L/'Reports/FINAL_REPORT.md',L/'Reports/DISK_USAGE.json']
    files+=list(L.glob('*manifest*'))+list((L/'Metadata').glob('*schema*'))
    records=[]
    for p in sorted(set(files)):
        if not p.is_file():continue
        d=BACK/p.relative_to(L);d.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,d);h=sha(p);assert sha(d)==h
        r=dict(path=str(p),backup=str(d),sha256=h,size=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns)
        if p.suffix=='.csv':
            with p.open(encoding='utf-8-sig',newline='') as f:
                reader=csv.reader(f);r['fields']=next(reader);r['row_count']=sum(1 for _ in reader)
        elif p.suffix=='.jsonl':
            with p.open(encoding='utf-8') as f:r['row_count']=sum(1 for _ in f)
        records.append(r)
    db=sqlite3.connect(f'file:{(L/"Metadata/ASSET_CATALOG.sqlite").as_posix()}?mode=ro',uri=True)
    tables={name:db.execute('SELECT COUNT(*) FROM "'+name.replace('"','""')+'"').fetchone()[0] for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    counts=dict(db.execute('SELECT source_version,COUNT(*) FROM assets GROUP BY source_version'))
    ids=[r[0] for r in db.execute('SELECT asset_id FROM assets')];maxid=max(ids,key=lambda s:int(re.search(r'(\d+)$',s)[1]))
    assert len(set(ids))==len(ids)
    schema=db.execute('SELECT sql FROM sqlite_master').fetchall();integrity=db.execute('PRAGMA integrity_check').fetchone()[0];db.close()
    js=(L/'Gallery/catalog.js').read_text('utf-8');meta=json.loads(re.search(r'window.FSN_META=(.*?);\s*window.FSN_ASSETS',js,re.S)[1]);gallery_ids=re.findall(r'^\["(FSN\d+)"',js,re.M)
    assert set(gallery_ids)==set(ids) and meta['count']==len(ids)
    oldrows=[json.loads(s) for s in (L/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8')]
    assert len(oldrows)==len(ids)
    state=dict(created_at=now(),status='IMMUTABLE_PRE_INTEGRATION',files=records,sqlite_tables=tables,sqlite_integrity=integrity,sqlite_schema=schema,source_counts=counts,total_assets=len(ids),max_asset_id=maxid,gallery_asset_count=len(gallery_ids),gallery_meta=meta,reported_total=202602,total_difference=len(ids)-202602,disk_E=shutil.disk_usage('E:/')._asdict(),old_raw_paths=len({r['extracted_path'] for r in oldrows}),old_thumbnail_paths=len({r['thumbnail_path'] for r in oldrows if r['thumbnail_path']}))
    jsonwrite(BACK/'BASELINE.json',state);jsonwrite(target,state)
    print('BASELINE',counts,'MAX',maxid,'backup_bytes',sum(r['size'] for r in records),flush=True)
def inventory():
    FHA.joinpath('Metadata').mkdir(parents=True,exist_ok=True);FW.mkdir(parents=True,exist_ok=True)
    out=FHA/'Metadata/SOURCE_INVENTORY.json'
    if out.exists():print('Existing FHA inventory retained');return
    rows=[];containers=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file():continue
        st=p.stat()
        with p.open('rb') as f:b=f.read(64)
        fmt=signature(b,p.suffix);notes='';embedded=[]
        if fmt=='PE':
            with p.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
                start=0
                while True:
                    offset=mm.find(b'XP3\r\n \n\x1a\x8bg\x01',start)
                    if offset<0:break
                    embedded.append(offset);start=offset+11
            notes='Embedded XP3 candidate offsets: '+str(embedded) if embedded else 'PE binary; never executed'
        r=dict(absolute_path=str(p),relative_path=p.relative_to(ROOT).as_posix(),filename=p.name,extension=p.suffix.lower(),size=st.st_size,sha256=sha(p),mtime=datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat(),mtime_ns=st.st_mtime_ns,magic=b[:16].hex(),detected_format=fmt,probable_container=bool(fmt in {'XP3','ZIP','7Z','FPD'} or embedded),notes=notes)
        rows.append(r)
        if fmt=='XP3':containers.append(dict(source=str(p),source_container=r['relative_path'],kind='XP3',offset=0,size=st.st_size))
        for off in embedded:containers.append(dict(source=str(p),source_container=r['relative_path']+'#embedded_xp3@'+str(off),kind='EMBEDDED_XP3',offset=off,size=st.st_size-off))
    csvwrite(FHA/'Metadata/SOURCE_INVENTORY.csv',rows);jsonwrite(out,rows);jsonwrite(FW/'containers.json',containers)
    summary=dict(source_root=str(ROOT),game_root=str(ROOT/'Fate hollow ataraxia'),source_files=len(rows),source_bytes=sum(r['size'] for r in rows),containers=len(containers),extensions=dict(collections.Counter(r['extension'] for r in rows)),magic=dict(collections.Counter(r['detected_format'] for r in rows)),disk_E=shutil.disk_usage('E:/')._asdict())
    jsonwrite(FHA/'Metadata/SOURCE_SUMMARY.json',summary);print('INVENTORY',json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':freeze();inventory()
