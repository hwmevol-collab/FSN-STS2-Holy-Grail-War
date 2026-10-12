from fuc_common import *
import pycdlib
def sfo(b):
    assert b[:4]==b'\0PSF'
    version,ks,ds,n=struct.unpack_from('<4I',b,4);out={}
    for i in range(n):
        ko,typ,length,cap,do=struct.unpack_from('<HHIII',b,20+16*i)
        key=b[ks+ko:].split(b'\0',1)[0].decode('utf-8');v=b[ds+do:ds+do+length]
        out[key]=struct.unpack('<I',v)[0] if typ==0x404 else v.rstrip(b'\0').decode('utf-8','replace')
    return out
def detect(b,ext):
    for m,f in [(b'\0PSF','PSF'),(b'PSMF','PMF'),(b'MIG.00.1PSP','GIM'),(b'OMG.00.1PSP','GMO'),(b'~PSP','PSP_ENCRYPTED_EXECUTABLE'),(b'\x7fELF','ELF'),(b'VAGp','VAG'),(b'PGF','PGF')]:
        if b.startswith(m):return f
    return signature(b,ext)
def run():
    marker=FUC/'Metadata/ISO_SUMMARY.json'
    if marker.exists():log('ISO extraction already verified');return
    iso_root=FW/'image';iso_root.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(SRC) as z:
        for entry in z.infolist():
            if entry.is_dir():continue
            assert not pathlib.PurePosixPath(entry.filename).is_absolute() and '..' not in pathlib.PurePosixPath(entry.filename).parts
            dst=iso_root/entry.filename;dst.parent.mkdir(parents=True,exist_ok=True)
            if not dst.exists():
                with z.open(entry) as a,dst.open('wb') as f:shutil.copyfileobj(a,f)
    images=list(iso_root.rglob('*.iso'));assert len(images)==1
    image=images[0]
    with image.open('rb') as f:f.seek(32768);pvd=f.read(2048)
    assert pvd[1:6]==b'CD001','Actual image not ISO9660'
    preservation=FUC/'RawExtracted/ISO'/image.name;preservation.parent.mkdir(parents=True,exist_ok=True)
    if not preservation.exists():os.link(image,preservation)
    cd=pycdlib.PyCdlib();cd.open(str(image));rows=[]
    for dirname,dirs,files in cd.walk(iso_path='/'):
        for name in files:
            logical=(dirname.rstrip('/')+'/'+name);clean=logical.lstrip('/').split(';')[0]
            role='Executable' if '/SYSDIR/' in logical else 'Containers' if clean.lower().endswith('.fpk') else 'Loose'
            p=FUC/'RawExtracted'/role/clean;p.parent.mkdir(parents=True,exist_ok=True)
            if not p.exists():cd.get_file_from_iso(str(p),iso_path=logical)
            rec=cd.get_record(iso_path=logical);assert p.stat().st_size==rec.data_length
            b=p.open('rb').read(64)
            rows.append(dict(logical_path=clean,physical_path=str(p),size=p.stat().st_size,sha256=sha(p),magic=b[:16].hex(),extension=p.suffix.lower(),detected_format='FPK_CANDIDATE' if p.suffix.lower()=='.fpk' else detect(b,p.suffix),container='ISO9660',iso_path=logical,lba=rec.extent_location(),notes='Complete ISO filesystem file'))
    cd.close();rows.sort(key=lambda x:x['logical_path']);csvwrite(FUC/'Metadata/SOURCE_INVENTORY.csv',rows);jsonwrite(FUC/'Metadata/SOURCE_INVENTORY.json',rows)
    param=next(r for r in rows if r['logical_path']=='PSP_GAME/PARAM.SFO');identity=sfo(pathlib.Path(param['physical_path']).read_bytes())
    umd=next(r for r in rows if r['logical_path']=='UMD_DATA.BIN');ub=pathlib.Path(umd['physical_path']).read_bytes()
    data=dict(created_at=now(),source_image=str(image),preserved_image=str(preservation),image_sha256=sha(image),image_size=image.stat().st_size,iso_volume_id=pvd[40:72].decode('ascii','replace').strip(),filesystem='ISO9660',file_count=len(rows),file_bytes=sum(r['size'] for r in rows),extensions=dict(collections.Counter(r['extension'] for r in rows)),PARAM_SFO=identity,UMD_DATA=ub.decode('ascii','replace'),japanese_identity_verified=identity.get('DISC_ID')=='ULJM05451' and b'ULJM-05451' in ub)
    jsonwrite(marker,data);log('ISO SUMMARY',data)
if __name__=='__main__':run()
