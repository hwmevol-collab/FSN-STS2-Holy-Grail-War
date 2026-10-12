"""Mature GMO conversion in WORK only. No master IDs allocated from incomplete source."""
from fuc_common import *
import concurrent.futures,base64
NOESIS=W/'tools/noesis-fuc/Noesis64.exe'
ROOT=STAGE_ROOT
def pack_glb(path,out):
    j=readjson(path);assert j['asset']['version']=='2.0';blob=bytearray();newviews=[]
    bufferbase=[]
    for b in j.get('buffers',[]):
        bufferbase.append(len(blob));u=b['uri']
        data=base64.b64decode(u.split(',',1)[1]) if u.startswith('data:') else (path.parent/u).read_bytes()
        assert len(data)>=b['byteLength'];blob.extend(data[:b['byteLength']]);blob.extend(b'\0'*((-len(blob))%4))
    for v in j.get('bufferViews',[]):v['byteOffset']=v.get('byteOffset',0)+bufferbase[v['buffer']];v['buffer']=0
    for image in j.get('images',[]):
        u=image.pop('uri');data=base64.b64decode(u.split(',',1)[1]) if u.startswith('data:') else (path.parent/u).read_bytes()
        image['mimeType']='image/png' if data.startswith(b'\x89PNG') else 'image/jpeg'
        image['bufferView']=len(j.setdefault('bufferViews',[]));j['bufferViews'].append(dict(buffer=0,byteOffset=len(blob),byteLength=len(data)))
        blob.extend(data);blob.extend(b'\0'*((-len(blob))%4))
    j['buffers']=[dict(byteLength=len(blob))]
    jb=json.dumps(j,ensure_ascii=False,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4)
    total=12+8+len(jb)+8+len(blob)
    out.write_bytes(struct.pack('<III',0x46546c67,2,total)+struct.pack('<I4s',len(jb),b'JSON')+jb+struct.pack('<I4s',len(blob),b'BIN\0')+blob)
    return j,blob
def validate(j,blob):
    acc=j.get('accessors',[]);views=j.get('bufferViews',[])
    for v in views:assert v.get('byteOffset',0)+v['byteLength']<=len(blob)
    for a in acc:
        if 'bufferView' in a:
            v=views[a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16,'MAT3':9,'MAT2':4}[a['type']];cs={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}[a['componentType']]
            assert a.get('byteOffset',0)+(a['count']-1)*v.get('byteStride',n*cs)+n*cs<=v['byteLength']
    for s in j.get('skins',[]):assert acc[s['inverseBindMatrices']]['count']==len(s['joints'])
    primitives=[p for m in j.get('meshes',[]) for p in m['primitives']]
    for node in j.get('nodes',[]):
        if 'skin' in node:
            for p in j['meshes'][node['mesh']]['primitives']:assert 'JOINTS_0' in p['attributes'] and 'WEIGHTS_0' in p['attributes']
    return primitives
def convert(r):
    h=r['sha256'];folder=ROOT/'Models'/h;folder.mkdir(parents=True,exist_ok=True);glb=folder/'model.glb';marker=folder/'MODEL_METADATA.json'
    if marker.exists():return readjson(marker)
    base=dict(source_sha256=h,source_path=r['physical_path'],source_name=r['name'],status='FAILED',source_status=r['source_status'])
    try:
        cached=FW/'source_diagnostic/Models'/h
        if ROOT!=FW/'source_diagnostic' and (cached/'MODEL_METADATA.json').exists():
            previous=readjson(cached/'MODEL_METADATA.json')
            if previous['status']=='CONVERTED_GLB_STRUCTURE_VALIDATED':
                for source in cached.iterdir():
                    if source.suffix in {'.glb','.png','.log'} and not (folder/source.name).exists():os.link(source,folder/source.name)
                previous.update(source_path=r['physical_path'],source_name=r['name'],source_status=r['source_status'],working_path=str(glb),reused_conversion_from=str(cached),reuse_evidence='Identical source GMO SHA256 from independently verified full Europe ISO')
                jsonwrite(marker,previous);return previous
        path=folder/'model.gltf';cmd=[str(NOESIS),'?cmode',r['physical_path'],str(path)]
        p=subprocess.run(cmd,capture_output=True,timeout=45);(folder/'conversion.log').write_bytes(p.stdout+p.stderr)
        assert p.returncode==0 and path.is_file(),'Noesis did not produce glTF'
        j,blob=pack_glb(path,glb);primitives=validate(j,blob);acc=j.get('accessors',[]);positions=[acc[p['attributes']['POSITION']] for p in primitives]
        bbox={'min':[min(a.get('min',[0,0,0])[i] for a in positions) for i in range(3)],'max':[max(a.get('max',[0,0,0])[i] for a in positions) for i in range(3)]} if positions else {}
        parents={c:i for i,n in enumerate(j.get('nodes',[])) for c in n.get('children',[])}
        skeletons=[dict(skin_index=i,joints=[dict(node_id=n,name=j['nodes'][n].get('name',''),parent_node=parents.get(n),matrix=j['nodes'][n].get('matrix'),translation=j['nodes'][n].get('translation'),rotation=j['nodes'][n].get('rotation'),scale=j['nodes'][n].get('scale')) for n in s['joints']],inverse_bind_accessor=s['inverseBindMatrices']) for i,s in enumerate(j.get('skins',[]))]
        base.update(status='CONVERTED_GLB_STRUCTURE_VALIDATED',working_path=str(glb),working_sha256=sha(glb),vertex_count=sum(a['count'] for a in positions),index_count=sum(acc[p['indices']]['count'] for p in primitives if 'indices' in p),mesh_count=len(j.get('meshes',[])),primitive_count=len(primitives),material_count=len(j.get('materials',[])),texture_count=len(j.get('images',[])),bone_count=len({n for s in j.get('skins',[]) for n in s['joints']}),animation_count=len(j.get('animations',[])),bounding_box=bbox,skeletons=skeletons,format='GMO magic OMG.00.1PSP -> Noesis 4.474 glTF 2.0 -> GLB 2.0',command=cmd,notes='WORK only. Bone hierarchy, bind matrices, JOINTS_0 and WEIGHTS_0 structurally checked; no visual or animated game-equivalence claim.')
        # Only GLB is kept as model Working Copy. Textures are preserved separately for indexing.
        intermediate=[path]+[folder/b['uri'] for b in readjson(path).get('buffers',[]) if not b['uri'].startswith('data:')]
        for p in intermediate:
            assert p.parent==folder;p.unlink()
    except Exception as e:base['error']=str(e)
    jsonwrite(marker,base);return base
def run():
    rows=readjson(ROOT/'FPK_EXTRACTED_INDEX.json');models=[r for r in rows if pathlib.Path(r['name']).suffix=='.gmo'];unique={r['sha256']:r for r in models}
    good={};log('GMO logical models',len(models),'unique payloads',len(unique))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,x in enumerate(pool.map(convert,unique.values())):
            good[x['source_sha256']]=x
            if i%50==0:log('Model conversion',i+1,'/',len(unique))
    index=[dict(**{k:v for k,v in good[r['sha256']].items() if k!='skeletons'},source_container=r['container'],logical_path=r['name']) for r in models]
    csvwrite(ROOT/'MODEL_INDEX.csv',index);jsonwrite(ROOT/'MODEL_INDEX.json',index)
    bones=[]
    for h,x in good.items():
        for s in x.get('skeletons',[]):
            for b in s['joints']:bones.append(dict(model_sha256=h,skin_index=s['skin_index'],inverse_bind_accessor=s['inverse_bind_accessor'],**b))
    csvwrite(ROOT/'SKELETON_INDEX.csv',bones,['model_sha256','skin_index','node_id','name','parent_node','matrix','translation','rotation','scale','inverse_bind_accessor'])
    summary=dict(logical_models=len(models),unique_models=len(unique),converted_unique_models=sum(x['status']=='CONVERTED_GLB_STRUCTURE_VALIDATED' for x in good.values()),failed_unique_models=sum(x['status']=='FAILED' for x in good.values()),unique_skinned_models=sum(x.get('bone_count',0)>0 for x in good.values()),bone_rows=len(bones),embedded_animation_count=sum(x.get('animation_count',0) for x in good.values()),stage_status='WORK_ONLY_NOT_INTEGRATED_FROM_TRUNCATED_SOURCE')
    jsonwrite(ROOT/'MODEL_SUMMARY.json',summary);log('MODELS SUMMARY',summary)
if __name__=='__main__':run()
