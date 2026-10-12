"""Export only naturally confirmed model/MOT pairs as 60 Hz frame-baked GLB working copies.

STEP is the baked-frame hold rule, not a claim about MOT interpolation (which is
linear in direction/twist storage). Model/skin/IBM/geometry binary stays intact.
"""
from fuc_motion_evaluator import *
from scipy.spatial.transform import Rotation
import copy
MODELS={'sir':'FSN250564','rin':'FSN249429','lan':'FSN248769'}
def load_glb(path):
    b=pathlib.Path(path).read_bytes();magic,version,length=struct.unpack_from('<III',b)
    assert magic==0x46546c67 and version==2 and length==len(b)
    jl,jt=struct.unpack_from('<II',b,12);assert jt==0x4e4f534a
    doc=json.loads(b[20:20+jl]);bl,bt=struct.unpack_from('<II',b,20+jl);assert bt==0x004e4942
    return doc,bytearray(b[28+jl:28+jl+bl])
def node_matrix(n):
    if 'matrix' in n:return mat(n['matrix'])
    m=np.eye(4);m[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()*np.array(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0]);return m
def decompose(m):
    s=np.linalg.norm(m[:3,:3].astype(np.float64),axis=0);r=m[:3,:3]/s
    if np.linalg.det(r)<0:raise ValueError('Negative determinant')
    q=Rotation.from_matrix(r).as_quat();q/=np.linalg.norm(q)
    return np.asarray(m[:3,3],np.float32),np.asarray(q,np.float32),np.asarray(s,np.float32)
def main():
    frozen();verified={r['code'] for r in readjson(AW/'Runtime/Natural/NATURAL_BANK_SOURCE_VERIFICATION.json') if r['status']=='PASS'}
    mi=readrows(EU/'Metadata/MODEL_INDEX.csv');bi=readrows(EU/'Metadata/SOURCE_BONE_INDEX.csv');idx=readjson(EU/'Metadata/ANIMATION_INDEX.json');outputs=[];adapter=[]
    previous={r['animation_asset_id']:r for r in readjson(AW/'GLB_EXPORTS.json')} if (AW/'GLB_EXPORTS.json').exists() else {}
    for code in ['sir','rin','lan']:
        model=next(r for r in mi if r['asset_id']==MODELS[code]);doc,original_bin=load_glb(model['working_path']);sk=skeleton(code);lut=np.frombuffer((AW/f'Runtime/Motion/{code}/rotation_sine_lut.bin').read_bytes(),dtype='<f4')
        bones=[r for r in bi if r['model_sha256']==model['source_sha256']];mapping={int(r['source_bone_ordinal']):int(r['glb_node_id']) for r in bones};parents={child:i for i,n in enumerate(doc['nodes']) for child in n.get('children',[])}
        errs=[];mismatches=[]
        for n in sk['nodes']:
            gi=mapping[n['ordinal']];errs.append(float(np.max(np.abs(node_matrix(doc['nodes'][gi])-mat(n['bind_local'])))))
            if n['parent'] is not None and parents.get(gi)!=mapping[n['parent']]:mismatches.append(n['ordinal'])
        a=dict(code=code,model_asset_id=model['asset_id'],nodes=len(sk['nodes']),max_bind_matrix_error=max(errs),parent_mismatches=mismatches,tolerance=2e-5,initial_trial_tolerance=2e-6,initial_trial_result='rin and lan exceeded 2e-6; retained in GLB_SOURCE_SKELETON_COMPARISON.json',status='PASS' if max(errs)<=2e-5 and not mismatches else 'FAIL',coordinate_adapter='identity source local matrices and hierarchy; float32 Noesis TRS reconstruction measured')
        adapter.append(a)
        if a['status']!='PASS':raise ValueError(a)
        if code not in verified:continue
        for clip in [0,1,2]:
            ir=next(r for r in idx if r['source_name']==f'chr/{code}/0000.mot' and r['motion_table_index']==clip and '0000.fpk' in r['source_path'] and r.get('working_path'))
            if ir['asset_id'] in previous:
                old=previous[ir['asset_id']]
                if sha(old['animated_glb'])!=old['sha256']:raise ValueError('Existing animated working copy changed')
                outputs.append(old);continue
            decoded=readjson(ir['working_path']);end=F(decoded['end_time']);times=np.asarray(sorted(set([float(F(i/60)) for i in range(int(np.ceil(float(end)*60))) if F(i/60)<end]+[float(end)])),np.float32)
            poses=[evaluate(decoded,sk,t,lut) for t in times];g=copy.deepcopy(doc);binary=original_bin.copy();g['animations']=[];samplers=[];channels=[];matrix_errors=[];world_errors=[];quat_errors=[]
            def accessor(vals,kind):
                vals=np.asarray(vals,dtype='<f4');binary.extend(b'\0'*((-len(binary))%4));off=len(binary);raw=vals.tobytes();binary.extend(raw)
                vi=len(g['bufferViews']);g['bufferViews'].append(dict(buffer=0,byteOffset=off,byteLength=len(raw)))
                ac=dict(bufferView=vi,componentType=5126,count=len(vals),type=kind)
                if kind=='SCALAR':ac.update(min=[float(vals.min())],max=[float(vals.max())])
                ai=len(g['accessors']);g['accessors'].append(ac);return ai
            time_accessor=accessor(times,'SCALAR');trs_by_node={}
            for n in sk['nodes']:
                ordinal=n['ordinal'];gi=mapping[ordinal];trs=[decompose(mat(p['nodes'][ordinal]['local_matrix'])) for p in poses];trs_by_node[ordinal]=trs
                g['nodes'][gi].pop('matrix',None)
                for key,values,kind in [('translation',[x[0] for x in trs],'VEC3'),('rotation',[x[1] for x in trs],'VEC4'),('scale',[x[2] for x in trs],'VEC3')]:
                    va=accessor(values,kind);si=len(samplers);samplers.append(dict(input=time_accessor,output=va,interpolation='STEP'));channels.append(dict(sampler=si,target=dict(node=gi,path=key)));g['nodes'][gi][key]=np.asarray(values[0]).tolist()
                for p,(t,q,s) in zip(poses,trs):
                    reconstructed=node_matrix(dict(translation=t.tolist(),rotation=q.tolist(),scale=s.tolist()));matrix_errors.append(float(np.max(np.abs(reconstructed-mat(p['nodes'][ordinal]['local_matrix'])))));quat_errors.append(abs(float(np.linalg.norm(q.astype(np.float64)))-1))
            for pi,p in enumerate(poses):
                worlds={}
                for n in sk['nodes']:
                    ordinal=n['ordinal'];t,q,s=trs_by_node[ordinal][pi];local=node_matrix(dict(translation=t.tolist(),rotation=q.tolist(),scale=s.tolist()));world=worlds[n['parent']]@local if n['parent'] is not None else local;worlds[ordinal]=world;world_errors.append(float(np.max(np.abs(world-mat(p['nodes'][ordinal]['world_matrix'])))))
            if max(matrix_errors)>2e-5 or max(world_errors)>2e-4 or max(quat_errors)>1e-6:raise ValueError(('GLB pose reconstruction error',code,clip,max(matrix_errors),max(world_errors)))
            extra=dict(source_version='FateUnlimitedCodesPortable_Europe',animation_asset_id=ir['asset_id'],model_asset_id=model['asset_id'],mot_asset_id=ir['parent_asset_id'],mot_file=ir['source_name'],clip_index=clip,binding_status='confirmed_natural_bank_and_model',pose_validation='original-game controlled single-clip comparison on 3 skeletons',source_interpolation='linear four stored components, then direction/twist matrix',export_interpolation='60 Hz frame-baked STEP',loop='not encoded; player-controlled',scope='raw single clip; excludes gameplay movement, mirroring and transition blending',semantic_name='clip_%04d'%clip)
            g['animations']=[dict(name='clip_%04d'%clip,channels=channels,samplers=samplers,extras=extra)];g['buffers'][0]['byteLength']=len(binary)
            j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4);binary+=b'\0'*((-len(binary))%4)
            output=EU/f'Converted/AnimatedModels/{code}__mot_0000__clip_{clip:04d}.glb';output.parent.mkdir(parents=True,exist_ok=True)
            if output.exists():raise FileExistsError('Never overwrite an existing working copy without deliberate revision')
            output.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary)
            outputs.append(dict(**extra,animated_glb=str(output),sha256=sha(output),sample_count=len(times),duration=float(end),max_local_matrix_error=max(matrix_errors),max_world_matrix_error=max(world_errors),max_quaternion_norm_error=max(quat_errors),playback_status='pending',asset_id_policy='working copy of existing animation asset; no new ID'))
    jsonwrite(AW/'Runtime/GLB_ADAPTER_VALIDATION.json',adapter);jsonwrite(AW/'GLB_EXPORTS.json',outputs);log('GLB EXPORTS',outputs)
if __name__=='__main__':main()
