"""Allocation audit using NTFS file identities, including the third source."""
from fha_prepare import *
from disk_audit import measure
def run():
    shared={};sections={}
    roots=[L/n for n in ['Original','Remastered','HollowAtaraxia','Converted','Gallery','Metadata','Reports','Canonical']]+[W]
    for root in roots:
        before=set(shared);r=measure(root,False,shared);r['additional_allocated_bytes_across_roots']=sum(v for k,v in shared.items() if k not in before);sections[str(root)]=r
        print('DISK ROOT',root,r['files'],r['allocated_bytes'],flush=True)
    source=measure(ROOT,False,{});baseline=json.loads((BACK/'BASELINE.json').read_text('utf-8'))
    growth={r['path']:pathlib.Path(r['path']).stat().st_size-r['size'] for r in baseline['files'] if pathlib.Path(r['path']).exists() and pathlib.Path(r['path']).is_relative_to(L/'Metadata')}
    result=dict(measured_at=now(),sections=sections,source=source,library_and_work_allocated_bytes=sum(shared.values()),metadata_baseline_file_growth_bytes=sum(growth.values()),metadata_file_growth=growth,disk_E=shutil.disk_usage('E:/')._asdict(),method='FileStandardInfo AllocationSize, deduplicated by NTFS (device,file id). Roots attributed in listed order; Canonical hardlinks add no payload allocation. Within-root allocation can overlap another root; only additional/global values may be added. Source measured separately. Reparse directories skipped; directory/MFT overhead excluded. Reports and subsequent evidence may grow slightly after snapshot.')
    jsonwrite(L/'Reports/FHA_DISK_USAGE.json',result);print('FHA DISK DONE',flush=True)
if __name__=='__main__':run()
