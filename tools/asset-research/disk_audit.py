from common import *
import ctypes, time
from ctypes import wintypes

def measure(root, sectioned=False, allocation_cache=None):
    seen=set();sections=collections.defaultdict(lambda:dict(files=0,logical_bytes=0,unique_file_ids=0,unique_content_bytes=0,allocated_bytes_within_section=0,additional_allocated_bytes=0))
    section_seen=collections.defaultdict(set);errors=[];count=0;start=time.monotonic()
    if allocation_cache is None:allocation_cache={}
    class StandardInfo(ctypes.Structure):
        _fields_=[('AllocationSize',ctypes.c_longlong),('EndOfFile',ctypes.c_longlong),('NumberOfLinks',wintypes.DWORD),('DeletePending',ctypes.c_ubyte),('Directory',ctypes.c_ubyte)]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.restype=wintypes.HANDLE
    kernel.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    kernel.GetFileInformationByHandleEx.argtypes=[wintypes.HANDLE,ctypes.c_int,wintypes.LPVOID,wintypes.DWORD]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    def allocation(path, identity):
        if identity in allocation_cache:return allocation_cache[identity]
        handle=kernel.CreateFileW(path,0,7,None,3,0,None)
        if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
        info=StandardInfo()
        try:
            if not kernel.GetFileInformationByHandleEx(handle,1,ctypes.byref(info),ctypes.sizeof(info)):raise ctypes.WinError(ctypes.get_last_error())
        finally:kernel.CloseHandle(handle)
        allocation_cache[identity]=info.AllocationSize
        return info.AllocationSize
    getsize=ctypes.windll.kernel32.GetCompressedFileSizeW
    getsize.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_uint32)];getsize.restype=ctypes.c_uint32
    def walk(directory):
        with os.scandir(directory) as entries:
            for e in entries:
                if e.is_dir(follow_symlinks=False):
                    if e.is_junction() or e.is_symlink():continue
                    yield from walk(e.path)
                elif e.is_file(follow_symlinks=False):yield e
    top_order=['Original','Remastered','Converted','Gallery','Metadata','Reports','Canonical']
    roots=[root/p for p in top_order if (root/p).is_dir()] if sectioned else [root]
    for target in roots:
        for entry in walk(target):
            try:
                # On Windows DirEntry.stat caches zero inode/device values; os.stat gives the actual NTFS file id.
                st=os.stat(entry.path,follow_symlinks=False);identity=(st.st_dev,st.st_ino);relative=pathlib.Path(entry.path).relative_to(root)
                parts=relative.parts
                section='/'.join(parts[:2]) if sectioned and parts[0] in {'Original','Remastered'} else parts[0] if sectioned else parts[0]
                s=sections[section];s['files']+=1;s['logical_bytes']+=st.st_size
                if identity not in section_seen[section]:
                    allocated=allocation(entry.path,identity)
                    s['unique_file_ids']+=1;s['unique_content_bytes']+=st.st_size;s['allocated_bytes_within_section']+=allocated;section_seen[section].add(identity)
                    if identity not in seen:s['additional_allocated_bytes']+=allocated;seen.add(identity)
                count+=1
                if count%50000==0:print(root.name,'DISK',count,'files',round(time.monotonic()-start,1),'s',flush=True)
            except Exception as e:errors.append(dict(file=entry.path,error=repr(e)))
    return dict(root=str(root),files=count,unique_file_ids=len(seen),logical_bytes=sum(x['logical_bytes'] for x in sections.values()),allocated_bytes=sum(x['additional_allocated_bytes'] for x in sections.values()),sections=dict(sections),errors=errors)

def run():
    shared={};library=measure(L,True,shared);work=measure(W,False,shared)
    result=dict(measured_at=now(),library=library,work=work,library_and_work_allocated_bytes=sum(shared.values()),disk_E=shutil.disk_usage('E:/')._asdict(),method='FileStandardInfo AllocationSize, de-duplicated by NTFS (device,file id) from os.stat. Per-section allocation can overlap via hardlinks; global allocation counts each file id once. Library traversal attributes RawExtracted before Canonical. Metadata and later report files can grow slightly after this snapshot; reparse directories are skipped.')
    jsonwrite(L/'Reports/DISK_USAGE.json',result);print('DISK DONE',result['library']['files'],result['library']['allocated_bytes'],flush=True)
if __name__=='__main__':run()
