from fuc_common import *
from fuc_iso import sfo,detect
import pycdlib,io
EU_SRC=pathlib.Path('E:/BaiduNetdiskDownload/FSN/素材/Fate-Unlimited Codes (Europe) (PSP) (PSN)/Fate-Unlimited Codes (Europe) (PSP) (PSN).iso')
EU=FW/'europe-probe'
def run():
    out=EU/'SOURCE_IDENTITY.json'
    if out.exists():assert readjson(out)['sha256']==sha(EU_SRC);log('Europe identity already verified');return
    st=EU_SRC.stat();h=sha(EU_SRC);cd=pycdlib.PyCdlib();cd.open(str(EU_SRC));rows=[]
    for dirname,dirs,files in cd.walk(iso_path='/'):
        for name in files:
            iso_path=dirname.rstrip('/')+'/'+name;rec=cd.get_record(iso_path=iso_path);clean=iso_path.lstrip('/').split(';')[0];offset=rec.extent_location()*2048;size=rec.data_length
            assert offset+size<=st.st_size,'ISO extent extends beyond source size'
            dst=EU/'Filesystem'/clean;dst.parent.mkdir(parents=True,exist_ok=True)
            if not dst.exists():cd.get_file_from_iso(str(dst),iso_path=iso_path)
            assert dst.stat().st_size==size;b=dst.open('rb').read(64)
            rows.append(dict(logical_path=clean,iso_path=iso_path,physical_path=str(dst),lba=rec.extent_location(),offset=offset,size=size,sha256=sha(dst),magic=b[:16].hex(),extension=dst.suffix.lower(),detected_format=detect(b,dst.suffix),container='ISO9660'))
    cd.close();rows.sort(key=lambda r:r['logical_path'])
    param=next(r for r in rows if r['logical_path']=='PSP_GAME/PARAM.SFO');umd=next(r for r in rows if r['logical_path']=='UMD_DATA.BIN')
    data=dict(created_at=now(),source=str(EU_SRC),size=st.st_size,mtime_ns=st.st_mtime_ns,sha256=h,PARAM_SFO=sfo(pathlib.Path(param['physical_path']).read_bytes()),UMD_DATA=pathlib.Path(umd['physical_path']).read_bytes().decode('ascii','replace'),filesystem_file_count=len(rows),all_file_extents_in_source_bounds=True,extensions=dict(collections.Counter(r['extension'] for r in rows)))
    jsonwrite(out,data);csvwrite(EU/'SOURCE_INVENTORY.csv',rows);jsonwrite(EU/'SOURCE_INVENTORY.json',rows);log('EUROPE ISO VERIFIED',data)
if __name__=='__main__':run()
