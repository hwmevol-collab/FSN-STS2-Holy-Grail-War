"""Controlled original GMO/MOT loader + motion-player diagnostics.
The pairing is requested by this harness, not read from a battle character table.
"""
from fuc_anim_runtime_model_probe import *
def main():
    idx=readjson(EU/'Metadata/ANIMATION_INDEX.json');captures=[]
    import sys
    for code in (sys.argv[1:] or ['sir','rin','lan']):
        d=Debugger();d.resume();time.sleep(1);d.close();h=Harness();folder=AW/f'Runtime/Motion/{code}';folder.mkdir(parents=True,exist_ok=True)
        try:
            _,e=setup(h,code,co_load=False)
            model=h.call(0x088833b4,a0=0x08801300,a1=0,a2=0x11)
            if not model:raise RuntimeError('GMO model create failed')
            modeldata=h.d.read(model,0x340);count=struct.unpack_from('<I',modeldata,0x58)[0];nodes=struct.unpack_from('<I',modeldata,0x5c)[0]
            sdk=struct.unpack_from('<I',modeldata,0x38)[0]
            sdk_table=struct.unpack_from('<I',h.d.read(sdk,64),0x18)[0]
            sdk_ptrs=struct.unpack('<'+'I'*count,h.d.read(sdk_table,count*4))
            lut=struct.unpack('<I',h.d.read(0x08b1d1d4,4))[0]
            h.d.dump(lut,0x4000*4,folder/'rotation_sine_lut.bin')
            res=h.call(0x088869d8,a0=0x08801300,a1=0x10)
            if not res:raise RuntimeError('MOT load failed')
            rd=h.d.read(res,0x4c);(folder/'mot_resource.bin').write_bytes(rd);bank=struct.unpack_from('<I',rd,0x34)[0]
            h.d.dump(bank,16,folder/'bank_header.bin')
            player=h.call(0x088866b0,a0=model,a1=1,a2=1)
            if not player:raise RuntimeError('Motion player allocation failed')
            h.call(0x08885c2c,a0=player);h.call(0x08886580,a0=player,a1=1,a2=0,a3=bank)
            e.update(model=hex(model),nodes=hex(nodes),node_count=count,mot_resource=hex(res),mot_bank=hex(bank),player=hex(player),scope='diagnostic_only original loaders and motion player; manually requested pair; raw single clip with transition flag cleared')
            h.d.dump(model,count*0x140+0x340,folder/'model_before_animation.bin')
            h.d.dump(0x089fd998,count*64,folder/'source_names.bin')
            for clip in [0,1,2]:
                ir=next(r for r in idx if r['source_name']==f'chr/{code}/0000.mot' and r['motion_table_index']==clip and r['working_path'])
                decoded=readjson(ir['working_path']);selected=h.call(0x08886410,a0=player,a1=clip,f12=0)
                pb=h.d.read(player,0x38);(folder/f'clip_{clip:04d}_player_bound.bin').write_bytes(pb)
                current=struct.unpack_from('<I',pb,0x18)[0]
                if selected==0xffffffff or not current:raise RuntimeError(('Clip selection failed',selected,current))
                h.d.dump(current,16+decoded['channel_count']*32,folder/f'clip_{clip:04d}_relocated_header.bin')
                for fraction in [0,.25,.5,.75,1]:
                    target=struct.unpack('<f',struct.pack('<f',decoded['end_time']*fraction))[0]
                    # Evaluate exact source time without gameplay transitions/loops.
                    flags=struct.unpack('<I',h.d.read(player,4))[0]&~(0x80|0x8|0x2)
                    h.write(player,struct.pack('<I',flags));h.write(player+8,struct.pack('<f',target));h.write(player+12,struct.pack('<f',0))
                    h.call(0x08884b28,a0=player)
                    h.call(0x08877378,a0=model)
                    pose=h.d.read(nodes,count*0x140);tag=f'clip_{clip:04d}_fraction_{int(fraction*100):03d}'
                    (folder/(tag+'_nodes.bin')).write_bytes(pose)
                    sdk_pose=b''.join(h.d.read(p,0x180) for p in sdk_ptrs)
                    (folder/(tag+'_sdk_nodes.bin')).write_bytes(sdk_pose)
                    rows=[]
                    for i in range(count):
                        block=pose[i*0x140:(i+1)*0x140]
                        rows.append(dict(node_ordinal=i,flags=struct.unpack_from('<I',block)[0],translation=struct.unpack_from('<4f',block,0x20),scale=struct.unpack_from('<4f',block,0x30),rotation_storage=struct.unpack_from('<4f',block,0x50),runtime_delta_matrix=struct.unpack_from('<16f',block,0xa0),runtime_local_matrix=struct.unpack_from('<16f',sdk_pose,i*0x180+0xb0),runtime_world_matrix=struct.unpack_from('<16f',sdk_pose,i*0x180+0xf0)))
                    jsonwrite(folder/(tag+'.json'),dict(time=target,fraction=fraction,clip=clip,animation_asset_id=ir['asset_id'],scope=e['scope'],nodes=rows))
                log('MOTION CLIP CAPTURE',dict(code=code,clip=clip,channel_count=decoded['channel_count'],player=hex(player),selected_bank=selected))
            jsonwrite(folder/'CAPTURE.json',e);captures.append(e)
        finally:h.close()
    jsonwrite(AW/'Runtime/MOTION_PROBE_SUMMARY.json',captures)
if __name__=='__main__':main()
