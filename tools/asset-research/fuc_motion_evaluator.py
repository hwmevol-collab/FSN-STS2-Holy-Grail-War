"""FUC Europe diagnostic single-clip evaluator, backed by original game code.

Runtime functions: loader 08883F10, channel 088842F0/08884A30,
ID remap 08881F90/0888255C, direction/twist matrix 0887772C,
bind composition 08877378, SDK parent composition 0893F7DC.
Inputs are existing decoded MOT and captured source skeleton metadata.
No animation-export eligibility is implied by this diagnostic evaluator.
"""
from fuc_anim_common import *
import numpy as np, struct, argparse
F=np.float32

def mat(values):return np.asarray(values,dtype=np.float32).reshape(4,4).T.copy()
def flat(m):return np.asarray(m,dtype=np.float32).T.reshape(-1).tolist()
def mul(a,b):
    # PSP VFPU dot products; separately rounded multiply and ordered sum.
    o=np.empty((4,4),np.float32)
    for i in range(4):
        for j in range(4):
            x=F(a[i,0]*b[0,j])
            for k in range(1,4):x=F(x+F(a[i,k]*b[k,j]))
            o[i,j]=x
    return o

def runtime_keys(channel):
    v=np.asarray(channel['values'],np.float32).copy()
    if channel['track_flags']&1:
        # 08883F10..08883FA4 scales all four floats by 0x3DCCCCCD,
        # then stores only upper 16 bits back to the source's 8-byte key.
        v=F(v*F(.1));v=(v.view(np.uint32)&np.uint32(0xffff0000)).view(np.float32)
    return v

def curve(channel,t):
    if channel['flags']!=0x0202:raise ValueError('Unsupported coordinate representation')
    ts=np.asarray(channel['times'],np.float32);v=runtime_keys(channel);t=F(t)
    if not len(ts):raise ValueError('Empty coordinate channel')
    if t>=ts[-1]:return v[-1].copy()
    if t<=ts[0]:return v[0].copy()
    hits=np.flatnonzero(ts==t)
    if len(hits):return v[hits[0]].copy()
    k=int(np.searchsorted(ts,t,side='right')-1)
    a=F(F(t-ts[k])/F(ts[k+1]-ts[k]))
    return F(v[k]+F(a*F(v[k+1]-v[k])))

def direction_twist(rotation,scale,translation,lut):
    # This is a normalized X-direction plus X-roll in degrees, NOT axis-angle.
    r=np.asarray(rotation,np.float32);x,y,z=r[:3]
    length=F(np.sqrt(F(F(z*z)+F(F(x*x)+F(y*y)))))
    if length==0:raise ValueError('Zero direction: unsupported engine singularity')
    x,y,z=F(r[:3]*F(F(1)/length))
    m=np.eye(4,dtype=np.float32);m[:3,0]=[x,y,z]
    yz=F(F(y*y)+F(z*z))
    if yz!=0:
        k=F(F(F(1)-x)/yz)
        m[:3,1]=[-y,F(x+F(F(z*z)*k)),F(F(F(-z)*y)*k)]
        m[:3,2]=[-z,F(F(F(-z)*y)*k),F(x+F(F(y*y)*k))]
    # FUC lookup index is not a continuous sine calculation.
    index=((int(np.trunc(F(r[3]*F(182.04444885253906))))+2)>>2)&0x3fff
    s,c=lut[index],lut[(index+0x1000)&0x3fff]
    rx=np.eye(4,dtype=np.float32);rx[1:3,1:3]=[[c,-s],[s,c]]
    if yz==0:
        m[1:3,1:3]=rx[1:3,1:3]
    elif r[3]!=0:m=mul(m,rx)
    for i in range(3):m[:,i]=F(m[:,i]*F(scale[i]))
    m[:3,3]=translation[:3];m[3,3]=1
    return m

def skeleton(code):
    root=AW/f'Runtime/Models/{code}';cap=readjson(root/'CAPTURE.json');n=cap['node_count']
    rb=(root/'bone_remap.bin').read_bytes();remap=list(struct.unpack('<'+'h'*(len(rb)//2),rb))[1:]
    before=(root/'runtime_nodes.bin').read_bytes();nodes=[]
    for i in range(n):
        b=(root/f'sdk_node_{i:03d}.bin').read_bytes();r=before[i*0x140:(i+1)*0x140]
        par=struct.unpack_from('<I',b,0x3c)[0]&0xfff
        nodes.append(dict(ordinal=i,parent=par if par<n else None,
            flags=struct.unpack_from('<I',r)[0],sdk_flags=struct.unpack_from('<I',b,0x18)[0],
            bind_local=flat(mat(struct.unpack_from('<16f',b,0xb0))),
            translation=list(struct.unpack_from('<4f',r,0x20)),scale=list(struct.unpack_from('<4f',r,0x30)),
            rotation_storage=list(struct.unpack_from('<4f',r,0x50))))
    return dict(code=code,remap=remap,nodes=nodes,evidence_path=str(root),status='controlled_runtime_confirmed_subset')

def evaluate(decoded,sk,time,lut):
    nodes=[dict(x) for x in sk['nodes']];t=F(time)
    for c in decoded['channels']:
        if not c['values']:continue
        b=c['source_bone_id']
        if b<0 or b>=len(sk['remap']) or sk['remap'][b]<0:continue
        n=nodes[sk['remap'][b]];key={0x21:'translation',0x22:'scale',0x28:'rotation_storage'}.get(c['track_flags'])
        if not key:raise ValueError('Unsupported channel flags')
        n[key]=curve(c,t).tolist()
    for n in nodes:
        if n['flags']&(8|16|32|4|0x40000):raise ValueError('Unsupported matrix mode')
        delta=direction_twist(n['rotation_storage'],n['scale'],n['translation'],lut)
        local=mul(mat(n['bind_local']),delta) if n['flags']&0x100 else delta
        n['delta_matrix']=flat(delta);n['local_matrix']=flat(local)
    done=set();active=set()
    def world(i):
        n=nodes[i]
        if i in done:return mat(n['world_matrix'])
        if i in active:raise ValueError('Source hierarchy cycle')
        active.add(i);p=n['parent'];l=mat(n['local_matrix'])
        w=mul(world(p),l) if p is not None else l
        n['world_matrix']=flat(w);active.remove(i);done.add(i);return w
    for i in range(len(nodes)):world(i)
    return dict(time=float(t),clip_index=decoded.get('motion_table_index'),nodes=nodes,
        scope='diagnostic single raw clip, no transitions/mirroring/gameplay transform',
        gltf_coordinate_adapter='identity verified on sir/rin/lan; see GLB_ADAPTER_VALIDATION.json',
        animation_export_eligible=False,export_gate='evaluator alone grants no export approval; consult FUC_VALIDATED_ANIMATIONS.csv')

def main():
    p=argparse.ArgumentParser(description=__doc__);source=p.add_mutually_exclusive_group(required=True);source.add_argument('--decoded-mot');source.add_argument('--mot');p.add_argument('--clip-index',type=int);p.add_argument('--code',choices=['sir','rin','lan']);p.add_argument('--skeleton-metadata');p.add_argument('--sine-lut');p.add_argument('--time',type=float,required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    if not a.code and not(a.skeleton_metadata and a.sine_lut):p.error('Provide --code or both --skeleton-metadata and --sine-lut')
    sk=readjson(a.skeleton_metadata) if a.skeleton_metadata else skeleton(a.code)
    lut=np.frombuffer(pathlib.Path(a.sine_lut or AW/f'Runtime/Motion/{a.code}/rotation_sine_lut.bin').read_bytes(),dtype='<f4')
    if a.mot:
        from fuc_motion_channels import parse_clip
        if a.clip_index is None:p.error('--mot requires --clip-index')
        raw=pathlib.Path(a.mot).read_bytes();flags,count,table,total=struct.unpack_from('>4I',raw);assert table==16 and total==len(raw)
        if not 0<=a.clip_index<count:p.error('Clip index outside source offset table')
        offsets=struct.unpack_from('>'+str(count)+'I',raw,table);offset=offsets[a.clip_index]
        if not offset:p.error('Clip is an empty offset slot')
        end=min([o for o in offsets if o>offset]+[len(raw)]);decoded=parse_clip(raw,offset,end);decoded['motion_table_index']=a.clip_index
    else:decoded=readjson(a.decoded_mot)
    jsonwrite(a.output,evaluate(decoded,sk,a.time,lut))
if __name__=='__main__':main()
