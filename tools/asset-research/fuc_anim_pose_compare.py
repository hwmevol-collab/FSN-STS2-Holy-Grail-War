from fuc_motion_evaluator import *
from scipy.spatial.transform import Rotation

def angular_error(a,b):
    if np.array_equal(a,b):return 0.0
    ar=a[:3,:3].astype(np.float64);br=b[:3,:3].astype(np.float64)
    ar/=np.linalg.norm(ar,axis=0);br/=np.linalg.norm(br,axis=0)
    return float(np.degrees((Rotation.from_matrix(ar).inv()*Rotation.from_matrix(br)).magnitude()))

def main():
    idx=readjson(EU/'Metadata/ANIMATION_INDEX.json');rows=[]
    for code in ['sir','rin','lan']:
        folder=AW/f'Runtime/Motion/{code}';sk=skeleton(code);jsonwrite(folder/'SKELETON_EVALUATOR_INPUT.json',sk)
        lut=np.frombuffer((folder/'rotation_sine_lut.bin').read_bytes(),dtype='<f4')
        for clip in [0,1,2]:
            ir=next(r for r in idx if r['source_name']==f'chr/{code}/0000.mot' and r['motion_table_index']==clip and r['working_path']);j=readjson(ir['working_path'])
            for fraction in [0,25,50,75,100]:
                tag=f'clip_{clip:04d}_fraction_{fraction:03d}';runtime=readjson(folder/(tag+'.json'))
                offline=evaluate(j,sk,runtime['time'],lut);jsonwrite(folder/(tag+'_offline.json'),offline)
                for o,r in zip(offline['nodes'],runtime['nodes']):
                    td=float(np.max(np.abs(np.asarray(o['translation'])-r['translation'])));rd=float(np.max(np.abs(np.asarray(o['rotation_storage'])-r['rotation_storage'])));sd=float(np.max(np.abs(np.asarray(o['scale'])-r['scale'])))
                    dm=float(np.max(np.abs(mat(o['delta_matrix'])-mat(r['runtime_delta_matrix']))));lm=float(np.max(np.abs(mat(o['local_matrix'])-mat(r['runtime_local_matrix']))));wm=float(np.max(np.abs(mat(o['world_matrix'])-mat(r['runtime_world_matrix']))))
                    rows.append(dict(code=code,animation_asset_id=ir['asset_id'],clip=clip,bone=o['ordinal'],time=runtime['time'],fraction=fraction,runtime_matrix=json.dumps(r['runtime_world_matrix']),offline_matrix=json.dumps(o['world_matrix']),translation_error=td,rotation_storage_error=rd,scale_error=sd,delta_matrix_error=dm,local_matrix_error=lm,world_matrix_error=wm,matrix_frobenius_error=float(np.linalg.norm(mat(o['world_matrix'])-mat(r['runtime_world_matrix']))),rotation_error=angular_error(mat(o['delta_matrix']),mat(r['runtime_delta_matrix'])),rotation_error_unit='degrees',status='PASS' if max(td,rd,sd,dm,lm,wm)<=2e-5 else 'FAIL',scope='controlled original game loader/player/matrix path; pairing independently proven by natural battle captures'))
    csvwrite(AW/'Runtime/FUC_RUNTIME_POSE_COMPARISON.csv',rows)
    summary=dict(samples=len(rows),passed=sum(r['status']=='PASS' for r in rows),failed=sum(r['status']=='FAIL' for r in rows),models=3,clips=9,pose_frames=45,tolerance=2e-5,max_errors={k:max(r[k] for r in rows) for k in ['translation_error','rotation_storage_error','rotation_error','scale_error','delta_matrix_error','local_matrix_error','world_matrix_error','matrix_frobenius_error']})
    jsonwrite(AW/'Runtime/POSE_COMPARISON_SUMMARY.json',summary);log('POSE COMPARISON',summary)
    for r in [r for r in rows if r['status']=='FAIL'][:10]:log('FAIL',{k:v for k,v in r.items() if not k.endswith('matrix')})
if __name__=='__main__':main()
