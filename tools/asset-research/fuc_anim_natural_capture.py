"""Capture natural battle players without writing game memory or running injected calls."""
from fuc_anim_natural_trace import regs
from fuc_anim_debugger import *
import struct
def u32(b,o=0):return struct.unpack_from('<I',b,o)[0]
def main():
    import sys
    d=Debugger();d.pause();root=AW/'Runtime/Natural';root=root/sys.argv[1] if len(sys.argv)>1 else root;summary=[]
    try:
        for a in [0x088833b4,0x088869d8,0x08886580,0x08886410]:
            try:d.call('cpu.breakpoint.remove',address=a)
            except RuntimeError:pass
        players=sorted({int(readjson(p)['player_address'],0) for p in root.glob('trace_*.json') if 'player_address' in readjson(p)})
        for player in players:
            pb=d.read(player,0x38);model=u32(pb,0x34)
            if not 0x08800000<=model<0x0a000000:continue
            mb=d.read(model,0x340);n=u32(mb,0x58)
            if n not in [49,60]:continue
            folder=root/f'player_{player:08x}';folder.mkdir(exist_ok=True)
            nodes=u32(mb,0x5c);sdk=u32(mb,0x38);resource=u32(mb,0x34);sdb=d.read(sdk,0x40);ptrs=struct.unpack('<'+'I'*n,d.read(u32(sdb,0x18),n*4))
            for name,a,size in [('player',player,0x38),('model',model,0x340),('resource',resource,0x4c),('runtime_nodes',nodes,n*0x140),('sdk',sdk,0x40),('bank_array',u32(pb,0x2c),u32(pb,0x30)*4)]:d.dump(a,size,folder/(name+'.bin'))
            remap=u32(mb,0x48);rc=struct.unpack('<h',d.read(remap,2))[0];d.dump(remap,2*(rc+1),folder/'bone_remap.bin')
            (folder/'sdk_nodes.bin').write_bytes(b''.join(d.read(p,0x180) for p in ptrs))
            lut=u32(d.read(0x08b1d1d4,4));d.dump(lut,0x10000,folder/'rotation_sine_lut.bin')
            banks=list(struct.unpack('<'+'I'*u32(pb,0x30),d.read(u32(pb,0x2c),u32(pb,0x30)*4)))
            linked={};queue=[resource]
            while queue and len(linked)<4096:
                rp=queue.pop()
                if rp in linked or not 0x08800000<=rp<0x0a000000:continue
                rb=d.read(rp,0x4c);linked[rp]=rb
                queue.extend([u32(rb,8),u32(rb,12)])
            bank_sources=[]
            anim_index=readjson(EU/'Metadata/ANIMATION_INDEX.json');mot_sources={r['source_path']:r for r in anim_index if r.get('source_path') and r.get('source_name','').endswith('.mot')}
            for bi,bp in enumerate(banks):
                if not bp:continue
                for rp,rb in linked.items():
                    if u32(rb,0x34)==bp:
                        (folder/f'bank_{bi}_resource.bin').write_bytes(rb)
                        bank_sources.append(dict(bank_slot=bi,bank=hex(bp),resource=hex(rp),name=rb[16:48].split(b'\0')[0].decode('ascii','replace')))
            for i,bank in enumerate(banks):
                if bank:
                    bh=d.read(bank,16);bs=u32(bh,12);slots=u32(bh,4)>>16
                    if not 0<bs<10000000 or not 0<slots<10000:raise ValueError('Bank bounds')
                    d.dump(bank,bs,folder/f'bank_{i}.bin')
                    table=struct.unpack('<'+'I'*slots,d.read(u32(bh,8),slots*4));rel=[p-bank if p else 0 for p in table]
                    matches=[]
                    for sp,ir in mot_sources.items():
                        source=pathlib.Path(sp).read_bytes()
                        if len(source)!=bs or struct.unpack_from('>I',source,4)[0]!=slots:continue
                        so=list(struct.unpack_from('>'+'I'*slots,source,16))
                        if so!=rel:continue
                        raw=(folder/f'bank_{i}.bin').read_bytes()
                        identical=sum(a==b for a,b in zip(raw[16+slots*4:],source[16+slots*4:]))
                        matches.append(dict(mot_file=ir['source_name'],mot_asset_id=ir['parent_asset_id'],sha256=ir['source_sha256'],offset_slots=slots,all_offset_slots_exact=True,payload_bytes=bs-16-slots*4,unchanged_payload_bytes=identical,source_path=sp))
                    bank_sources.append(dict(bank_slot=i,bank=hex(bank),fingerprint_matches=matches))
            current=u32(pb,0x18)
            if current:
                head=d.read(current,16);count=struct.unpack_from('<H',head,2)[0]
                d.dump(current,16+count*32,folder/'current_clip_header.bin')
            e=dict(player=hex(player),model=hex(model),resource=hex(resource),model_file=d.read(resource,0x4c)[16:48].split(b'\0')[0].decode('ascii','replace'),bank_sources=bank_sources,resource_records_visited=len(linked),nodes=hex(nodes),node_count=n,sdk=hex(sdk),sdk_ptrs=list(ptrs),banks=[hex(x) for x in banks],current_clip=hex(current),clip_index=u32(pb,0x1c),player_flags=hex(u32(pb)),time=struct.unpack_from('<f',pb,8)[0],delta_time=struct.unpack_from('<f',pb,12)[0],registers=regs(d),scope='natural battle read-only snapshot; may include blending/mirroring/gameplay transform')
            jsonwrite(folder/'CAPTURE.json',e);summary.append({k:v for k,v in e.items() if k not in ['registers','sdk_ptrs']})
        jsonwrite(root/'NATURAL_PLAYERS.json',summary);log('NATURAL PLAYERS',summary)
    finally:d.close()
if __name__=='__main__':main()
