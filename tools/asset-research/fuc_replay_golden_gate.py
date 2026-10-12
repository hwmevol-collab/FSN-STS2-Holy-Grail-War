from fuc_replay_common import *
from fuc_motion_evaluator import evaluate,skeleton,mat
import numpy as np
def main():
    battle_frozen();idx=readjson(EU/'Metadata/ANIMATION_INDEX.json');rows=[];out=BR/'GoldenRegression';out.mkdir(exist_ok=True)
    for code in ['sir','rin','lan']:
        sk=skeleton(code);lut=np.frombuffer((AW/f'Runtime/Motion/{code}/rotation_sine_lut.bin').read_bytes(),dtype='<f4')
        for clip in [0,1,2]:
            ir=next(r for r in idx if r['source_name']==f'chr/{code}/0000.mot' and r['motion_table_index']==clip and '0000.fpk' in r['source_path'] and r['working_path']);j=readjson(ir['working_path'])
            for fraction in [0,25,50,75,100]:
                source=AW/f'Runtime/Motion/{code}/clip_{clip:04d}_fraction_{fraction:03d}.json';runtime=readjson(source);offline=evaluate(j,sk,runtime['time'],lut)
                jsonwrite(out/f'{code}_clip_{clip:04d}_fraction_{fraction:03d}.json',offline)
                for n,r in zip(offline['nodes'],runtime['nodes']):
                    errors={k:float(np.max(np.abs(np.asarray(n[k])-r[rk]))) for k,rk in [('translation','translation'),('rotation_storage','rotation_storage'),('scale','scale'),('delta_matrix','runtime_delta_matrix'),('local_matrix','runtime_local_matrix'),('world_matrix','runtime_world_matrix')]}
                    rows.append(dict(code=code,asset_id=ir['asset_id'],clip=clip,fraction=fraction,time=runtime['time'],node=n['ordinal'],max_error=max(errors.values()),errors=json.dumps(errors),runtime_capture_sha256=sha(source),status='PASS' if max(errors.values())==0 else 'FAIL'))
    csvwrite(out/'GOLDEN_RUNTIME_EVALUATOR_COMPARISON.csv',rows);summary=dict(models=3,clips=9,pose_frames=45,nodes=len(rows),failures=sum(r['status']=='FAIL' for r in rows),max_matrix_error=max(r['max_error'] for r in rows),scope='fresh evaluation against frozen original-game 45-frame captures; this is not a new natural battle acquisition',status='PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL')
    jsonwrite(out/'GOLDEN_EVALUATOR_SUMMARY.json',summary);log('GOLDEN',summary);assert summary['failures']==0
if __name__=='__main__':main()
