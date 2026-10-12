from fha_prepare import *
from disk_audit import measure
def run():
    old=[json.loads(s) for s in (BACK/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8')];rows=[json.loads(s) for s in (FHA/'Metadata/ASSETS.jsonl').open(encoding='utf-8')];oldpaths={r['converted_path'] for r in old};oldthumbs={r['thumbnail_path'] for r in old if r['thumbnail_path']}
    objects={r['converted_path'] for r in rows if r['converted_path'] and pathlib.Path(r['converted_path']).is_relative_to(L/'Converted') and r['converted_path'] not in oldpaths};thumbs={r['thumbnail_path'] for r in rows if r['thumbnail_path'] and r['thumbnail_path'] not in oldthumbs}
    # AllocationSize queried for selected new objects, with actual NTFS identities.
    import ctypes
    from ctypes import wintypes
    class Standard(ctypes.Structure):_fields_=[('AllocationSize',ctypes.c_longlong),('EndOfFile',ctypes.c_longlong),('NumberOfLinks',wintypes.DWORD),('DeletePending',ctypes.c_ubyte),('Directory',ctypes.c_ubyte)]
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.restype=wintypes.HANDLE;k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE];k.CloseHandle.argtypes=[wintypes.HANDLE];k.GetFileInformationByHandleEx.argtypes=[wintypes.HANDLE,ctypes.c_int,wintypes.LPVOID,wintypes.DWORD]
    def selected(paths):
        seen=set();logical=allocated=0
        for p in paths:
            s=os.stat(p);logical+=s.st_size;key=(s.st_dev,s.st_ino)
            if key in seen:continue
            seen.add(key);h=k.CreateFileW(p,0,7,None,3,0,None);assert h!=ctypes.c_void_p(-1).value;info=Standard()
            try:assert k.GetFileInformationByHandleEx(h,1,ctypes.byref(info),ctypes.sizeof(info))
            finally:k.CloseHandle(h)
            allocated+=info.AllocationSize
        return dict(paths=len(paths),unique_file_ids=len(seen),logical_bytes=logical,allocated_bytes=allocated)
    result=dict(measured_at=now(),raw=measure(FHA/'RawExtracted'),fha_converted_directory=measure(FHA/'Converted'),new_converted_objects=selected(objects),new_thumbnails=selected(thumbs),new_contact_sheets=measure(L/'Gallery/contact_sheets/HollowAtaraxia'),fha_metadata=measure(FHA/'Metadata'),fha_work=measure(FW),canonical_new_payload_allocated_bytes=0,method='NTFS AllocationSize/file identities; rows link to shared Working Copy objects. FHA Converted directory is an index, objects live in unified Converted/Objects. These category figures overlap Work via hardlinks and must not be blindly summed.')
    baseline=json.loads((BACK/'BASELINE.json').read_text('utf-8'));before=sum(r['size'] for r in baseline['files'] if pathlib.Path(r['path']).parent==L/'Metadata');after=sum(p.stat().st_size for p in (L/'Metadata').iterdir() if p.is_file());result['global_metadata_logical_before']=before;result['global_metadata_logical_after']=after;result['global_metadata_logical_growth']=after-before
    jsonwrite(L/'Reports/FHA_DISK_DETAILS.json',result);print('FHA DISK DETAILS DONE',flush=True)
if __name__=='__main__':run()
