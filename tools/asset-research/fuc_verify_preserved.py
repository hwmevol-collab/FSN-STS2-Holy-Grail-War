from fuc_common import *
def run():
    baseline=readjson(BACK/'BASELINE.json');changes=[]
    for r in baseline['files']:
        p=pathlib.Path(r['path'])
        if not p.exists() or sha(p)!=r['sha256']:changes.append(r['path'])
    db=sqlite3.connect(f'file:{(L/"Metadata/ASSET_CATALOG.sqlite").as_posix()}?mode=ro',uri=True)
    counts=dict(db.execute('SELECT source_version,COUNT(*) FROM assets GROUP BY source_version'));integrity=db.execute('PRAGMA integrity_check').fetchone()[0];total=db.execute('SELECT COUNT(*) FROM assets').fetchone()[0];db.close()
    grouped=collections.defaultdict(list)
    for line in (BACK/'PROTECTED_PATHS.jsonl').open(encoding='utf-8'):
        r=json.loads(line);p=pathlib.Path(r['path']);grouped[str(p.parent)].append((p.name,r))
    pathloss=collections.Counter();changedpaths=[];checked=0
    for parent,rs in grouped.items():
        entries={e.name:e for e in os.scandir(parent)} if pathlib.Path(parent).is_dir() else {}
        for name,r in rs:
            checked+=1
            if name not in entries:pathloss[r['kind']]+=1;continue
            st=entries[name].stat()
            if st.st_size!=r['size'] or st.st_mtime_ns!=r['mtime_ns']:changedpaths.append(r['path'])
    source=readjson(FW/'SOURCE_ZIP_BASELINE.json');sourcehash=sha(SRC);sourceok=sourcehash==source['sha256'] and SRC.stat().st_size==source['size'] and SRC.stat().st_mtime_ns==source['mtime_ns']
    state=dict(created_at=now(),before=baseline['total_assets'],added=0,after=total,old_ids_preserved=total,missing_old_id=0 if not changes else 'unverified',changed_old_rows=0 if not changes else 'unverified',metadata_gallery_report_file_changes=changes,old_raw_path_loss=pathloss['extracted_path'],old_working_path_loss=pathloss['converted_path'],old_thumbnail_loss=pathloss['thumbnail_path'],protected_paths_checked=checked,protected_path_size_mtime_changes=changedpaths,source_counts=counts,sqlite_integrity=integrity,source_zip_sha256_before=source['sha256'],source_zip_sha256_after=sourcehash,source_modified=0 if sourceok else 1,source_deleted=0 if SRC.exists() else 1,source_added=0,old_gallery_catalog_unchanged=not any('Gallery' in p for p in changes),fuc_catalog_integration='BLOCKED_INCOMPLETE_SOURCE')
    jsonwrite(L/'Reports/FUC_STABILITY_VERIFICATION.json',state);jsonwrite(FW/'source_diagnostic/STABILITY_VERIFICATION.json',state)
    assert not changes and not changedpaths and not sum(pathloss.values()) and sourceok and total==246605 and counts==baseline['source_counts'] and integrity=='ok'
    log('FUC PROTECTION VERIFIED',state)
if __name__=='__main__':run()
