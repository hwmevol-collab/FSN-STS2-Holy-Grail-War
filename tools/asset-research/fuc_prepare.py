from fuc_common import *
def freeze():
    out=L/'Reports/FUC_PRE_INTEGRATION_BASELINE.json'
    if out.exists():log('Retaining frozen FUC baseline');return
    assert not BACK.exists(),'Existing backup must be reviewed, never overwritten'
    BACK.mkdir(parents=True);FW.mkdir(parents=True,exist_ok=True)
    records=[]
    files=list((L/'Metadata').rglob('*'))+list((L/'Reports').rglob('*'))
    files += [p for p in (L/'Gallery').rglob('*') if p.suffix.lower() in {'.html','.js','.css','.json'}]
    for p in sorted(set(files)):
        if not p.is_file():continue
        dst=BACK/p.relative_to(L);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
        h=sha(p);assert h==sha(dst)
        rec=dict(path=str(p),backup=str(dst),size=p.stat().st_size,sha256=h,mtime_ns=p.stat().st_mtime_ns)
        if p.suffix=='.csv':
            with p.open(encoding='utf-8-sig',newline='') as f:
                rd=csv.reader(f);rec['fields']=next(rd);rec['row_count']=sum(1 for _ in rd)
        elif p.suffix=='.jsonl':
            with p.open(encoding='utf-8') as f:rec['row_count']=sum(1 for _ in f)
        records.append(rec)
    db=sqlite3.connect(f'file:{(L/"Metadata/ASSET_CATALOG.sqlite").as_posix()}?mode=ro',uri=True)
    counts=dict(db.execute('SELECT source_version,COUNT(*) FROM assets GROUP BY source_version'))
    ids=[x[0] for x in db.execute('SELECT asset_id FROM assets')]
    tables={n:db.execute('SELECT COUNT(*) FROM "'+n+'"').fetchone()[0] for n, in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    integrity=db.execute('PRAGMA integrity_check').fetchone()[0];schema=db.execute('SELECT sql FROM sqlite_master').fetchall();db.close()
    assert len(ids)==246605 and len(set(ids))==len(ids) and max(ids)=='FSN246605' and integrity=='ok'
    js=(L/'Gallery/catalog.js').read_text('utf-8');meta=json.loads(re.search(r'window.FSN_META=(.*?);\s*window.FSN_ASSETS',js,re.S)[1])
    gallery=re.findall(r'^\["(FSN\d+)"',js,re.M);assert set(gallery)==set(ids) and meta['count']==len(ids)
    rows=rowsjson(BACK/'Metadata/ASSET_CATALOG.jsonl')
    paths={k:sorted({r[k] for r in rows if r.get(k)}) for k in ['extracted_path','converted_path','thumbnail_path']}
    missing={k:[p for p in ps if not pathlib.Path(p).is_file()] for k,ps in paths.items()}
    assert not any(missing.values()),str({k:len(v) for k,v in missing.items()})
    writejsonl(BACK/'PROTECTED_PATHS.jsonl',[dict(kind=k,path=p,size=pathlib.Path(p).stat().st_size,mtime_ns=pathlib.Path(p).stat().st_mtime_ns) for k,ps in paths.items() for p in ps])
    state=dict(created_at=now(),status='IMMUTABLE_PRE_INTEGRATION',total_assets=len(ids),source_counts=counts,max_asset_id=max(ids),files=records,sqlite_tables=tables,sqlite_integrity=integrity,sqlite_schema=schema,gallery_array_count=len(gallery),gallery_meta=meta,protected_path_counts={k:len(v) for k,v in paths.items()},preexisting_missing_paths=missing,thumbnail_count=sum(1 for p in (L/'Gallery/thumbnails').rglob('*') if p.is_file()),contact_sheet_count=sum(1 for p in (L/'Gallery/contact_sheets').rglob('*') if p.is_file()),disk_E=shutil.disk_usage('E:/')._asdict(),backup_bytes=sum(x['size'] for x in records),backup_policy='Metadata, Gallery code, schema, Reports; image payloads protected by path manifest, no RawExtracted copy')
    jsonwrite(BACK/'BASELINE.json',state);jsonwrite(out,state);log('FROZEN',counts,'backup bytes',state['backup_bytes'])
def inventory_zip():
    out=FW/'SOURCE_ZIP_BASELINE.json'
    if out.exists():return
    st=SRC.stat()
    error='';entries=[]
    try:
        with zipfile.ZipFile(SRC) as z:
            entries=[dict(name=i.filename,size=i.file_size,compressed_size=i.compress_size,crc32=f'{i.CRC:08x}',timestamp=i.date_time,compression=i.compress_type) for i in z.infolist()]
    except zipfile.BadZipFile as e:
        error=str(e)
        with SRC.open('rb') as f:
            h=struct.unpack('<IHHHHHIIIHH',f.read(30));name=f.read(h[9]).decode('utf-8','replace');extra=f.read(h[10])
        assert h[0]==0x04034b50
        entries=[dict(name=name,size=h[8],compressed_size=h[7],crc32=f'{h[6]:08x}',dos_date=h[5],dos_time=h[4],compression=h[3],flags=h[2],data_offset=30+h[9]+h[10],source='Local file header only; central directory missing')]
    data=dict(path=str(SRC),size=st.st_size,sha256=sha(SRC),mtime_ns=st.st_mtime_ns,entries=entries,zip_error=error,complete_zip=not bool(error))
    jsonwrite(out,data);jsonwrite(FUC/'Metadata/SOURCE_ZIP_BASELINE.json',data);log('ZIP',data)
if __name__=='__main__':freeze();inventory_zip()
