"""Read-only recovery evidence for a truncated ZIP. Never produces a complete ROM or modifies master assets."""
from fuc_common import *
def run():
    root=FW/'source_diagnostic';root.mkdir(parents=True,exist_ok=True)
    with SRC.open('rb') as src:
        h=struct.unpack('<IHHHHHIIIHH',src.read(30));name=src.read(h[9]).decode('utf-8','replace');src.read(h[10]);start=src.tell()
        assert h[0]==0x04034b50 and h[3]==8
        dec=zlib.decompressobj(-15);dst=root/'ISO_PREFIX_UNVERIFIED.partial';total=0;crc=0
        with dst.open('wb') as out:
            while b:=src.read(1024*1024):
                payload=dec.decompress(b);out.write(payload);total+=len(payload);crc=zlib.crc32(payload,crc)
        data=dict(created_at=now(),source_path=str(SRC),source_sha256=sha(SRC),actual_zip_bytes=SRC.stat().st_size,source_mtime_ns=SRC.stat().st_mtime_ns,local_header_filename=name,declared_iso_bytes=h[8],declared_compressed_bytes=h[7],declared_crc32=f'{h[6]:08x}',data_offset=start,available_compressed_bytes=SRC.stat().st_size-start,missing_compressed_bytes=h[7]-(SRC.stat().st_size-start),deflate_stream_eof=dec.eof,recovered_prefix_bytes=total,prefix_crc32=f'{crc:08x}',prefix_path=str(dst),prefix_sha256=sha(dst),status='TRUNCATED_ZIP_SOURCE_BLOCKED',warning='ISO prefix is incomplete and CRC cannot be verified. No master catalog integration authorized from this diagnostic output.')
    log('DEFLATE DIAGNOSTIC',data)
    # ISO9660 directory records contain LE/BE duplicate extent and size fields.
    files=[];seen=set();missingdirs=[]
    with dst.open('rb') as f:
        f.seek(32768);pvd=f.read(2048);assert pvd[1:6]==b'CD001'
        rootrec=pvd[156:190]
        def directory(rec,logical):
            extent,beextent=struct.unpack_from('<I',rec,2)[0],struct.unpack_from('>I',rec,6)[0]
            size,besize=struct.unpack_from('<I',rec,10)[0],struct.unpack_from('>I',rec,14)[0]
            assert extent==beextent and size==besize
            if (extent,size) in seen:return
            seen.add((extent,size));offset=extent*2048
            if offset+size>total:missingdirs.append(dict(path=logical,lba=extent,size=size));return
            f.seek(offset);block=f.read(size);i=0
            while i<len(block):
                length=block[i]
                if not length:i=((i//2048)+1)*2048;continue
                r=block[i:i+length];i+=length;assert len(r)==length
                n=r[32];nm=r[33:33+n]
                if nm in (b'\0',b'\1'):continue
                nm=nm.decode('ascii');path=(logical+'/'+nm).lstrip('/').split(';')[0]
                ex=struct.unpack_from('<I',r,2)[0];sz=struct.unpack_from('<I',r,10)[0];flags=r[25]
                assert ex==struct.unpack_from('>I',r,6)[0] and sz==struct.unpack_from('>I',r,14)[0]
                if flags&2:directory(r,path);continue
                complete=ex*2048+sz<=total
                outpath=root/'CompleteFilesystemExtents'/path
                item=dict(logical_path=path,lba=ex,offset=ex*2048,declared_size=sz,available_size=max(0,min(sz,total-ex*2048)),complete_extent=complete,physical_path='',sha256='',magic='',source_status='UNVERIFIED_ISO_PREFIX')
                if complete:
                    outpath.parent.mkdir(parents=True,exist_ok=True);f.seek(ex*2048)
                    with outpath.open('wb') as out:
                        remain=sz
                        while remain:
                            b=f.read(min(remain,1024*1024));assert b;out.write(b);remain-=len(b)
                    item.update(physical_path=str(outpath),sha256=sha(outpath),magic=outpath.open('rb').read(64).hex())
                files.append(item)
        directory(rootrec,'')
    files.sort(key=lambda r:r['logical_path']);csvwrite(root/'PARTIAL_ISO_FILESYSTEM_INVENTORY.csv',files);jsonwrite(root/'PARTIAL_ISO_FILESYSTEM_INVENTORY.json',files)
    from fuc_iso import sfo
    identity={}
    for r in files:
        if r['logical_path']=='PSP_GAME/PARAM.SFO' and r['complete_extent']:identity['PARAM_SFO']=sfo(pathlib.Path(r['physical_path']).read_bytes())
        if r['logical_path']=='UMD_DATA.BIN' and r['complete_extent']:identity['UMD_DATA']=pathlib.Path(r['physical_path']).read_bytes().decode('ascii','replace')
    data.update(identity=identity,iso_volume_id=pvd[40:72].decode('ascii','replace').strip(),filesystem_files_listed=len(files),complete_file_extents=sum(r['complete_extent'] for r in files),incomplete_file_extents=sum(not r['complete_extent'] for r in files),missing_directory_extents=missingdirs,complete_extent_bytes=sum(r['declared_size'] for r in files if r['complete_extent']),japanese_identity_supported_by_prefix=identity.get('PARAM_SFO',{}).get('DISC_ID')=='ULJM05451')
    jsonwrite(root/'SOURCE_DIAGNOSTIC.json',data);jsonwrite(L/'Reports/FUC_SOURCE_DIAGNOSTIC.json',data)
    log('PREFIX FILESYSTEM',data)
if __name__=='__main__':run()
