"""Read-only captures immediately after original matrix update in real battle."""
from fuc_motion_evaluator import *
from fuc_anim_debugger import *
def wait_stop(d,pc):
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        s=d.call('cpu.status')
        if s.get('stepping'):
            if s['pc']!=pc:raise ValueError(('Unexpected breakpoint',s))
            return s
        time.sleep(.01)
    raise TimeoutError(hex(pc))
def main():
    caps=readjson(AW/'Runtime/Natural/Round2/NATURAL_PLAYERS.json');idx=readjson(EU/'Metadata/ANIMATION_INDEX.json');rows=[];d=Debugger();active=set()
    try:
        d.pause()
        for cap in caps:
            code=cap['model_file'].split('/')[1];player=int(cap['player'],0);model=int(cap['model'],0);nodes=int(cap['nodes'],0);folder=pathlib.Path(cap['bank_sources'][0]['fingerprint_matches'][0]['source_path']);sk=skeleton(code);lut=np.frombuffer((AW/f'Runtime/Motion/{code}/rotation_sine_lut.bin').read_bytes(),dtype='<f4')
            for frame in range(5):
                fn=0x08877378;d.call('cpu.breakpoint.add',address=fn,enabled=True,condition=f'a0 == {hex(model)}');active.add(fn);d.resume();entry=wait_stop(d,fn);ra=d.call('cpu.getReg',name='ra')['uintValue'];d.call('cpu.breakpoint.remove',address=fn);active.remove(fn)
                d.call('cpu.breakpoint.add',address=ra,enabled=True);active.add(ra);d.resume();post=wait_stop(d,ra);d.call('cpu.breakpoint.remove',address=ra);active.remove(ra)
                pb=d.read(player,0x38);clip=struct.unpack_from('<I',pb,0x1c)[0];t=struct.unpack_from('<f',pb,8)[0];flags=struct.unpack_from('<I',pb)[0];raw=d.read(nodes,cap['node_count']*0x140)
                p=AW/f'Runtime/Natural/PostMatrix/{code}_frame_{frame:02d}.bin';p.parent.mkdir(exist_ok=True);p.write_bytes(raw);jsonwrite(str(p)+'.json',dict(player=hex(player),model=hex(model),pc=hex(ra),entry=entry,post=post,clip=clip,time=t,flags=hex(flags),scope='read-only natural battle, immediately after model matrix update'))
                ir=next((r for r in idx if r['source_name']==f'chr/{code}/0000.mot' and r['motion_table_index']==clip and '0000.fpk' in r['source_path'] and r.get('working_path')),None)
                if not ir or flags&0x80:
                    rows.append(dict(code=code,frame=frame,clip=clip,time=t,status='SKIPPED_BLEND_OR_OTHER_BANK'));continue
                decoded=readjson(ir['working_path']);offline=evaluate(decoded,sk,t,lut)
                for n in offline['nodes']:
                    i=n['ordinal'];b=raw[i*0x140:(i+1)*0x140];actual_t=struct.unpack_from('<4f',b,0x20);actual_s=struct.unpack_from('<4f',b,0x30);actual_r=struct.unpack_from('<4f',b,0x50);td=float(np.max(np.abs(np.asarray(n['translation'])-actual_t)));sd=float(np.max(np.abs(np.asarray(n['scale'])-actual_s)));rd=float(np.max(np.abs(np.asarray(n['rotation_storage'])-actual_r)))
                    rows.append(dict(code=code,frame=frame,clip=clip,bone=i,time=t,translation_error=td,rotation_storage_error=rd,scale_error=sd,status='PASS' if max(td,rd,sd)<=2e-5 else 'DIFFERENT_RUNTIME_STATE',source_flags=hex(struct.unpack_from('<I',b)[0]),runtime_translation=json.dumps(actual_t),runtime_rotation_storage=json.dumps(actual_r),offline_translation=json.dumps(n['translation']),offline_rotation_storage=json.dumps(n['rotation_storage']),evidence_path=str(p)))
        csvwrite(AW/'Runtime/Natural/NATURAL_MOTION_STATE_COMPARISON.csv',rows);jsonwrite(AW/'Runtime/Natural/NATURAL_MOTION_STATE_SUMMARY.json',dict(samples=len(rows),passed=sum(r['status']=='PASS' for r in rows),different=sum(r['status']=='DIFFERENT_RUNTIME_STATE' for r in rows),skipped=sum(r['status'].startswith('SKIPPED') for r in rows),max_errors={key:max([r.get(key,0) for r in rows]) for key in ['translation_error','rotation_storage_error','scale_error']}));log('NATURAL MOTION STATE',readjson(AW/'Runtime/Natural/NATURAL_MOTION_STATE_SUMMARY.json'))
    finally:
        d.pause()
        for a in active:d.call('cpu.breakpoint.remove',address=a)
        d.close()
if __name__=='__main__':main()
