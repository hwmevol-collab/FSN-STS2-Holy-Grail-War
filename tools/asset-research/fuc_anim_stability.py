"""Read-only final comparison with the frozen animation baseline."""
from fuc_anim_common import *
import concurrent.futures

def main():
    b=frozen();patch=readjson(AMD/'GALLERY_PATCH.json');files=[]
    for r in b['files']:
        p=pathlib.Path(r['path']);h=sha(p) if p.exists() else None;expected=r['sha256']
        status='UNCHANGED' if h==expected else 'AUTHORIZED_GALLERY_OVERLAY' if str(p)==patch['path'] and h==patch['new_sha256'] and expected==patch['old_sha256'] else 'UNEXPECTED_CHANGE'
        files.append(dict(path=str(p),baseline_sha256=expected,current_sha256=h,status=status))
    csvwrite(AMD/'FUC_BASELINE_FILE_COMPARISON.csv',files)
    count=0;missing=[];changed=[]
    with (AB/'PROTECTED_PATHS.jsonl').open(encoding='utf-8') as f:
        for line in f:
            r=json.loads(line);count+=1;p=pathlib.Path(r['path'])
            try:s=p.stat()
            except FileNotFoundError:missing.append(r);continue
            if s.st_size!=r['size'] or s.st_mtime_ns!=r['mtime_ns']:changed.append(dict(**r,current_size=s.st_size,current_mtime_ns=s.st_mtime_ns))
            if count%100000==0:log('PROTECTED PATHS',count)
    db=sqlite3.connect((L/'Metadata/ASSET_CATALOG.sqlite').as_uri()+'?mode=ro',uri=True)
    integrity=db.execute('pragma integrity_check').fetchall();tables=db.execute("select name from sqlite_master where type='table'").fetchall();log('TABLES',tables)
    total,maxid=db.execute('select count(*),max(asset_id) from assets').fetchone();eu=db.execute("select count(*) from assets where source_version='FateUnlimitedCodesPortable_Europe'").fetchone()[0];db.close()
    iso=pathlib.Path('E:/BaiduNetdiskDownload/FSN/素材/Fate-Unlimited Codes (Europe) (PSP) (PSN)/Fate-Unlimited Codes (Europe) (PSP) (PSN).iso');elf=W/'fuc/Europe/Executable/EBOOT_DECRYPTED.bin'
    src=dict(iso_sha256=sha(iso),iso_unchanged=sha(iso)=='bdf13beffbad519fd51f1ab075d165d3c7bfa075feef1a5b1fd7775bac0f830d',elf_sha256=sha(elf),elf_unchanged=sha(elf)=='33e8240519a232be40be503f17a23c2dfd5a361177ffb925de444df95dbe6ba7')
    summary=dict(asset_total=total,fuc_asset_count=eu,max_asset_id=maxid,catalog_bytes_unchanged=all(r['status']=='UNCHANGED' for r in files if pathlib.Path(r['path']).name.startswith('ASSET_CATALOG.')),old_asset_ids_preserved=total==268504 and maxid=='FSN268504',changed_old_rows=0 if all(r['status']=='UNCHANGED' for r in files if pathlib.Path(r['path']).name.startswith('ASSET_CATALOG.')) else 'unknown',frozen_files=len(files),unchanged_frozen_files=sum(r['status']=='UNCHANGED' for r in files),authorized_gallery_changes=sum(r['status']=='AUTHORIZED_GALLERY_OVERLAY' for r in files),unexpected_file_changes=[r for r in files if r['status']=='UNEXPECTED_CHANGE'],protected_path_records=count,missing_paths=missing,changed_protected_paths=changed,path_verification='all frozen paths: existence + size + nanosecond mtime; critical metadata SHA256; full raw rehash not performed',sqlite_integrity=integrity,source=src)
    summary['status']='PASS' if total==268504 and eu==21899 and maxid=='FSN268504' and integrity==[('ok',)] and not missing and not changed and not summary['unexpected_file_changes'] and src['iso_unchanged'] and src['elf_unchanged'] else 'FAIL'
    jsonwrite(AMD/'FUC_ANIMATION_STABILITY.json',summary);log('STABILITY',summary)
if __name__=='__main__':main()
