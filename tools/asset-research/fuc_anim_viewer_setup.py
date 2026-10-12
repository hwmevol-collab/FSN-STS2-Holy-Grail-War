"""Fetch official registry viewer/validator packages into this diagnostic workspace only."""
from fuc_anim_common import *
import urllib.request,tarfile,io,shutil
def package(name,version):
    meta=json.loads(urllib.request.urlopen(f'https://registry.npmjs.org/{name}/{version}',timeout=30).read());url=meta['dist']['tarball'];data=urllib.request.urlopen(url,timeout=30).read();dest=AW/f'Tools/{name}';dest.mkdir(parents=True,exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tf:
        for m in tf.getmembers():
            if not m.isfile():continue
            rel=pathlib.PurePosixPath(m.name)
            if rel.parts[0]!='package' or '..' in rel.parts:raise ValueError('Unsafe package member')
            out=dest/pathlib.Path(*rel.parts[1:]);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(tf.extractfile(m).read())
    return dict(name=name,version=version,registry='https://registry.npmjs.org',url=url,sha256=hashlib.sha256(data).hexdigest(),path=str(dest),package_integrity=meta['dist'].get('integrity'))
def main():
    records=[package('three','0.180.0'),package('gltf-validator','2.0.0-dev.3.10')];jsonwrite(AW/'Tools/PROVENANCE.json',records)
    viewer=EU/'Converted/AnimatedModels/viewer';vendor=viewer/'vendor';vendor.mkdir(parents=True,exist_ok=True)
    for rel in ['build/three.module.js','build/three.core.js','examples/jsm/loaders/GLTFLoader.js','examples/jsm/utils/BufferGeometryUtils.js']:
        out=vendor/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(AW/'Tools/three'/rel,out)
    exports=readjson(AW/'GLB_EXPORTS.json');jsonwrite(viewer/'clips.json',[dict(file='../'+pathlib.Path(r['animated_glb']).name,**r) for r in exports]);log('VIEWER TOOLS',records)
if __name__=='__main__':main()
