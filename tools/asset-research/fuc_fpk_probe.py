from fuc_common import *
def directory(p):
    raw=p.read_bytes();integrity,n,padding,length=struct.unpack_from('<4I',raw)
    assert length==len(raw) and padding==16 and 16+48*n<=len(raw)
    entries=[]
    for i in range(n):
        b=raw[16+i*48:16+(i+1)*48];name=b[:36].split(b'\0',1)[0].decode('ascii');offset,cs,us=struct.unpack_from('<3I',b,36)
        assert (offset>=16+48*n or (cs==us==0)) and offset+cs<=len(raw) and (us>0 or cs==0)
        assert '..' not in pathlib.PurePosixPath(name).parts
        safe_name=name.lstrip('/')
        entries.append(dict(entry_index=i,name=name,safe_name=safe_name,offset=offset,compressed_size=cs,uncompressed_size=us,flags='',container_integrity_word=integrity))
    assert len({r['name'].lower() for r in entries})==n
    return entries
def run():
    root=STAGE_ROOT;rs=readjson(root/'PARTIAL_ISO_FILESYSTEM_INVENTORY.json');entries=[];containers=[]
    for r in rs:
        if not r['logical_path'].endswith('.fpk') or not r['complete_extent']:continue
        try:
            es=directory(pathlib.Path(r['physical_path']));entries.extend(dict(container=r['logical_path'],container_path=r['physical_path'],**e) for e in es)
            containers.append(dict(container=r['logical_path'],declared_entries=len(es),declared_payload_bytes=sum(e['uncompressed_size'] for e in es),status='HEADER_BOUNDS_VALIDATED'))
        except Exception as e:containers.append(dict(container=r['logical_path'],status='FAILED',error=str(e)))
    csvwrite(root/'FPK_DIRECTORY_INDEX.csv',entries);jsonwrite(root/'FPK_DIRECTORY_INDEX.json',entries);jsonwrite(root/'FPK_CONTAINER_INDEX.json',containers)
    log('FPK headers',len(containers),'entries',len(entries),'payload bytes',sum(r['uncompressed_size'] for r in entries),'extensions',dict(collections.Counter(pathlib.Path(r['name']).suffix for r in entries)))
    log('FPK container folders',dict(collections.Counter('/'.join(r['container'].split('/')[5:-1]) for r in containers)))
    log('ENTRY EXAMPLES',entries[:15])
if __name__=='__main__':run()
