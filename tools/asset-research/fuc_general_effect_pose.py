"""Scoped Lan1000/1002 initial external-matrix evaluator and capture audit.

Only the observed first matrix-command snapshot rule is supported. This does
not implement arbitrary SEQ, effect lifetime, material, audio or body blending.
"""
from fuc_general_common import *
from fuc_motion_evaluator import mul,mat,flat
import numpy as np

def external_snapshot(source_world,offset_xyz):
    offset=np.eye(4,dtype=np.float32);offset[:3,3]=np.asarray(offset_xyz,np.float32)
    return mul(np.asarray(source_world,np.float32),offset)

def main():
    rows=[];cap=readjson(BR/'LanTablesFinal/capture.json');assert cap['remap'][154]==32
    for i in [1,2]:
        p=BR/f'LanOffsetTransform{i}';q=BR/f'LanExternalPosition{i}';r=readjson(p/'000_entry.json');src=mat(struct.unpack('<16f',(p/'000_entry_a1.bin').read_bytes()[:64]));v=struct.unpack('<4f',(p/'000_entry_a2.bin').read_bytes()[:16]);target=mat(struct.unpack('<16f',(q/'external_matrix.bin').read_bytes()));actual_point=np.frombuffer((p/'000_post_a0.bin').read_bytes()[:16],'<f4');result=external_snapshot(src,v[:3]);assert v[3]==1 and r['registers']['ra']==0x088cf9b0 and r['registers']['a1']==int(cap['sdk_nodes'][32],16)+0xf0
        err=result-target;ma=float(np.max(np.abs(err)));fr=float(np.linalg.norm(err));point_error=float(np.max(abs(result[:,3]-actual_point)));assert ma==fr==point_error==0
        rows.append(dict(sample=i,body_time_at_matrix_command=r['actor']['time'],source_bone_ID=153,source_gmo_ordinal=32,source_pointer=hex(r['registers']['a1']),source_matrix=flat(src),offset_vector=list(v),result_matrix=flat(result),runtime_matrix=flat(target),max_abs_error=ma,frobenius_error=fr,point_error=point_error,status='PASS'))
    jsonwrite(BR/'EFFECT_SNAPSHOT_EVALUATOR_AUDIT.json',dict(samples=rows,status='PASS',scope='F32 ordered arithmetic; captured source world at first matrix command, not an assumed raw body pose at activation. Hold this matrix during the observed snapshot interval.'))
    print('snapshot evaluator:2 full matrices + transformed points; all errors0')
if __name__=='__main__':main()
