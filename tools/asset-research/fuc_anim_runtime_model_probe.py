"""Original FUC loader tests. Caller requests a real archive/base path.
All SDK models, remaps, bind data and motion banks are built by game code.
Controlled debugger invocation is explicit; this is not a natural battle trace.
"""
from fuc_anim_runtime_harness import *
def setup(h,code,co_load=True):
    h.write(0x08801200,f'fpack/chr/{code}/0000.fpk'.encode()+b'\0')
    started=h.call(0x08958018,a0=0x08801200,a1=1)
    for i in range(15):
        h.call(0x089b0228,a0=20000)
        if h.call(0x08957ae0,a0=0):break
    else:raise RuntimeError('FPK read did not complete')
    loaded=h.call(0x08957b18,a0=0x2000)
    h.write(0x08801300,f'chr/{code}/0000'.encode()+b'\0')
    resource=h.call(0x088869d8,a0=0x08801300,a1=0x11) if co_load else 0
    if co_load and not resource:raise RuntimeError('Resource co-load failed')
    return resource,dict(fpk_loader_result=started,finish_result=loaded,resource=hex(resource),base_path=f'chr/{code}/0000',flags='0x11')
def main():
    captures=[]
    for code in ['sir','rin','lan']:
        d=Debugger();d.resume();time.sleep(1);d.close();h=Harness()
        folder=AW/f'Runtime/Models/{code}';folder.mkdir(parents=True,exist_ok=True)
        try:
            resource,e=setup(h,code,co_load=False)
            model=h.call(0x088833b4,a0=0x08801300,a1=0,a2=0x11)
            if not model:raise RuntimeError('Model creation failed')
            b=h.d.read(model,0x340);(folder/'model_wrapper.bin').write_bytes(b)
            u=lambda o:struct.unpack_from('<I',b,o)[0]
            resource=u(0x34);e['resource']=hex(resource);h.d.dump(resource,128,folder/'resource_after_model.bin')
            count=u(0x58);remap=u(0x48);nodes=u(0x5c);sdk=u(0x38)
            if not(0<count<1024 and remap and nodes and sdk):raise RuntimeError(('Incomplete model',count,remap,nodes,sdk))
            map_count=struct.unpack('<h',h.d.read(remap,2))[0]
            h.d.dump(remap,2*(map_count+1),folder/'bone_remap.bin');h.d.dump(nodes,count*0x140,folder/'runtime_nodes.bin');h.d.dump(sdk,64,folder/'sdk_handle.bin')
            h.d.dump(0x089fd998,count*64,folder/'source_names.bin')
            source_table=struct.unpack_from('<I',h.d.read(sdk,64),0x18)[0]
            ptrs=struct.unpack('<'+'I'*count,h.d.read(source_table,4*count))
            h.d.dump(source_table,4*count,folder/'sdk_node_pointers.bin')
            for i,p in enumerate(ptrs):h.d.dump(p,0x180,folder/f'sdk_node_{i:03d}.bin')
            e.update(model=hex(model),sdk=hex(sdk),node_count=count,remap=hex(remap),remap_count=map_count,nodes=hex(nodes),sdk_nodes=[hex(p) for p in ptrs],scope='diagnostic_only original game archive/resource/model loaders; no injected skeleton names or guessed bone offsets')
            jsonwrite(folder/'CAPTURE.json',e);captures.append(e);log('MODEL CAPTURE',e)
        finally:h.close()
    jsonwrite(AW/'Runtime/MODEL_PROBE_SUMMARY.json',captures)
if __name__=='__main__':main()
