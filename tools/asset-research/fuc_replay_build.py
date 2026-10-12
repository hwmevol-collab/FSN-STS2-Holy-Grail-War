"""One captured episode, no new IDs. Original evaluators and source files are read-only.

Body: runtime-authoritative final world matrices adapted to the glTF hierarchy.
Weapon: body153 each frame. Effect: scoped SEQ transform subset, float32 native order.
This is deliberately not a general offline reconstruction of arbitrary battle moves.
"""
from fuc_replay_common import *
from fuc_anim_glb_export import load_glb,node_matrix,decompose
from fuc_motion_evaluator import mat,mul,flat,evaluate,skeleton,F
import numpy as np, struct, copy, csv, hashlib
from scipy.spatial.transform import Rotation
P=BR/'Episode08'
OUT=EU/'Converted/BattleScenes/lan_clip145'
def js(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def rows(p,x,fields=None):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(x[0]));w.writeheader()
        for z in x:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in z.items()})
def u(b,o):return struct.unpack_from('<I',b,o)[0]
def matrix(b,o):return mat(struct.unpack_from('<16f',b,o))
def pose(po):
    b=(P/po['sdk']).read_bytes();r=(P/po['runtime']).read_bytes();n=po['nodes']
    return dict(local=[matrix(b,i*384+176) for i in range(n)],world=[matrix(b,i*384+240) for i in range(n)],parent=[None if u(b,i*384+60)&4095==4095 else u(b,i*384+60)&4095 for i in range(n)],rt=r)
def error(a,b):
    d=np.asarray(a,dtype=float)-np.asarray(b,dtype=float)
    return float(np.max(np.abs(d))),float(np.linalg.norm(d)),float(np.max(np.abs(d[:3,3])))
def worlds(local,parents,f32=True):
    out=[]
    for i,p in enumerate(parents):out.append(local[i] if p is None else mul(out[p],local[i]) if f32 else out[p]@local[i])
    return out
def mapped(model,bones):return {int(r['source_bone_ordinal']):int(r['glb_node_id']) for r in bones if r['model_sha256']==model['source_sha256']}
def web(path):return '/'+pathlib.Path(path).relative_to(L).as_posix()
def encode_glb(model,mapping,frames,times):
    g,b=load_glb(model['working_path']);g=copy.deepcopy(g);g['animations']=[];samplers=[];channels=[];reconstructed=[];trs={};errs=[]
    def acc(values,kind):
        vals=np.asarray(values,dtype='<f4');b.extend(b'\0'*((-len(b))%4));off=len(b);raw=vals.tobytes();b.extend(raw);vi=len(g['bufferViews']);g['bufferViews'].append(dict(buffer=0,byteOffset=off,byteLength=len(raw)));a=dict(bufferView=vi,componentType=5126,count=len(vals),type=kind)
        if kind=='SCALAR':a.update(min=[float(vals.min())],max=[float(vals.max())])
        ai=len(g['accessors']);g['accessors'].append(a);return ai
    ta=acc(times,'SCALAR');parents=frames[0]['parent'];graphparents={c:i for i,n in enumerate(g['nodes']) for c in n.get('children',[])}
    for i,gi in mapping.items():
        if parents[i] is not None:assert graphparents[gi]==mapping[parents[i]]
        # Some SDK nodes have independent world corrections. Capture those final
        # worlds, not the stale/special-policy SDK local values, for this replay.
        locals_=[f['world'][i].astype(float) if parents[i] is None else np.linalg.inv(f['world'][parents[i]].astype(float))@f['world'][i] for f in frames]
        tr=[decompose(x) for x in locals_];trs[i]=tr;g['nodes'][gi].pop('matrix',None)
        for key,values,kind in [('translation',[x[0] for x in tr],'VEC3'),('rotation',[x[1] for x in tr],'VEC4'),('scale',[x[2] for x in tr],'VEC3')]:
            a=acc(values,kind);si=len(samplers);samplers.append(dict(input=ta,output=a,interpolation='STEP'));channels.append(dict(sampler=si,target=dict(node=gi,path=key)));g['nodes'][gi][key]=values[0].tolist()
    for fi,f in enumerate(frames):
        local=[node_matrix(dict(translation=trs[i][fi][0].tolist(),rotation=trs[i][fi][1].tolist(),scale=trs[i][fi][2].tolist())) for i in range(len(parents))];ww=worlds(local,parents,False);reconstructed.append(ww)
        errs.extend(error(a,b)[0] for a,b in zip(ww,f['world']))
    assert max(errs)<2e-5, max(errs)
    g['animations']=[dict(name='lan_clip145_same_episode_final_pose',samplers=samplers,channels=channels,extras=dict(episode_id=readjson(P/'EPISODE_CAPTURE.json')['episode_id'],status='validated_episode_replay',source='runtime-authoritative composed final SDK world pose',raw_clip_asset_id='FSN258272',model_asset_id='FSN248769',frame_hold='STEP; observed native cadence, no invented intermediate poses',general_offline_reconstruction=False))];g['buffers'][0]['byteLength']=len(b)
    j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4);b+=b'\0'*((-len(b))%4);path=OUT/'lan_clip145_battle_pose.glb';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)
    # Structural gate including every buffer view/accessor and normalized rotations.
    sizes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16};components={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
    for v in g['bufferViews']:assert v.get('byteOffset',0)+v['byteLength']<=len(b)
    for a in g['accessors']:
        if 'bufferView' not in a:continue
        v=g['bufferViews'][a['bufferView']];width=sizes[a['type']]*components[a['componentType']];stride=v.get('byteStride',width);assert a.get('byteOffset',0)+(a['count']-1)*stride+width<=v['byteLength']
    qe=max(abs(float(np.linalg.norm(t[1].astype(float)))-1) for tr in trs.values() for t in tr)
    assert qe<1e-6
    return path,reconstructed,dict(status='PASS',samples=len(times),animated_nodes=len(mapping),animation_channels=len(channels),max_world_matrix_error=max(errs),max_quaternion_norm_error=qe,accessor_bounds='PASS',buffer_bounds='PASS',container='PASS',mesh_skin_material_binary='existing static GLB preserved; animation appended')

def effect_subset(events,bodyframes,ident):
    """Trace-guided operand resolution; direct scale + vector curve kinds 0/5.

    Control-flow/wait is preserved from the native trace and cross-checked. Model
    selectors are the captured resolved objects, never guessed ordinal offsets.
    Material commands are retained as opaque unsupported graphics, not guessed.
    """
    commands=[x for x in events if x['update_phase']=='seq_dispatch'];first=next(x for x in events if x['update_phase']=='effect_callback_post');initial=pose(first['effect']['models'][0]['pose'])
    offset=next(x for x in events if x['update_phase']=='offset_point');birthframe=offset['native_frame'];W=bodyframes[birthframe]['world'][32];T=np.eye(4,dtype=np.float32);T[1,3]=np.float32(2.4);external=mul(W,T)
    assert error(W,matrix((P/offset['source_matrix']).read_bytes(),0))[0]==0
    assert list(struct.unpack('<4f',(P/offset['vector']).read_bytes()))[:3]==[0.,float(np.float32(2.4)),0.]
    rt=initial['rt'];scales=[np.array(struct.unpack_from('<3f',rt,i*320+48),dtype=np.float32) for i in range(3)];translations=[np.array(struct.unpack_from('<3f',rt,i*320+32),dtype=np.float32) for i in range(3)]
    curves=[];states={};trace=[];next_allowed=5;wait_checks=[]
    for frame in range(5,15):
        # Real native curve update precedes dispatch (088D3868 -> 088D5EE4).
        for curve in list(curves):
            dest=translations if curve['field']==512 else scales;i=curve['node'];dest[i]=np.asarray(dest[i]+curve['velocity'],np.float32)
            if curve['kind']==5:curve['velocity']=np.asarray(curve['velocity']+curve['acceleration'],np.float32)
            curve['remaining']-=1
            if curve['remaining']==0:curves.remove(curve)
        for x in [q for q in commands if q['native_frame']==frame]:
            assert frame>=next_allowed
            w=x['command_words'];op=w[0]&255;sub=(w[0]>>8)&255;operation='opaque_native_command';status='raw_retained';before='';after='';node='';native_wait=0
            if op==16 and sub==1:
                node=ident['remap'][w[1]];field=w[2];before=scales[node].tolist();assert field==1024;scales[node]=np.array([struct.unpack('<f',struct.pack('<I',z))[0] for z in w[3:6]],np.float32);after=scales[node].tolist();operation='direct absolute scale';status='confirmed_transform'
            elif op==18 and sub in [3,7]:
                duration=w[1];node=ident['remap'][w[3]];field=w[4];target=np.array([struct.unpack('<f',struct.pack('<I',z))[0] for z in w[5:8]],np.float32);dest=translations if field==512 else scales;before=dest[node].tolist()
                if sub==3:
                    velocity=np.asarray((target-dest[node])/np.float32(duration),np.float32);curve=dict(kind=0,node=node,field=field,remaining=duration,velocity=velocity);operation='linear vector increment curve; native kind0'
                else:
                    # Acceleration for this observed zero-origin vector move;
                    # f32 order follows 088C4D60, not a duration-fit interpolation.
                    assert np.max(np.abs(dest[node]))==0;acceleration=np.asarray(np.float32(2)*target/np.float32(duration*duration),np.float32);velocity=np.asarray(target/np.float32(duration)-acceleration*np.float32(duration*.5),np.float32);curve=dict(kind=5,node=node,field=field,remaining=duration,velocity=velocity,acceleration=acceleration);operation='position += velocity; velocity += acceleration; native kind5'
                curves.append(curve);after={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in curve.items()};status='confirmed_transform'
            elif op==17:operation='body source basis/point -> snapshot external';status='confirmed_same_episode_matrix'
            elif op==11:operation='point transform offset (0,2.4,0)';status='confirmed_same_episode_matrix'
            elif op==0 and sub==3:
                next_allowed=frame+1;operation='yield to next native update (no numeric wait field)';status='confirmed_native_yield'
            elif op==0 and sub==5:
                native_wait=w[1]<<8;next_allowed=frame+w[1];operation='thread wait fixed8; wait -= 256 each observed update';status='confirmed_wait';ret=events[x['call_order_index']+1];actual=ret['effect']['threads'][0]['words'][29];wait_checks.append(dict(event=x['call_order_index'],expected=native_wait,runtime=actual));assert actual==native_wait
            elif op==0 and sub==0:operation='context state=0xF0, clear thread PC/curve fields';status='confirmed_end'
            elif op==15 and sub==10:operation='packed per-material write at target+0x14; exact blend/palette rendering unsupported';status='static_destination_confirmed_graphics_unsupported'
            elif op==18 and sub==28:operation='opaque material/control curve; raw arguments retained';status='graphics_unsupported'
            trace.append(dict(event=x['call_order_index'],frame=frame,pc=x['pc'],seq_offset=x['seq_offset'],handler=x['handler'],opcode=op,subopcode=sub,arguments=w,thread=x['thread'],native_wait=native_wait,effect_node=node,operation=operation,before=before,after=after,status=status))
        if frame<birthframe:local=initial['local'];visible=False;stage='active pooled initializer, render-thread +8 is zero; not submitted'
        elif frame<13:
            local=[]
            for i in range(3):
                m=np.eye(4,dtype=np.float32);m[:3,:3]=np.diag(scales[i]);m[:3,3]=translations[i];local.append(mul(external,m) if i==1 else m)
            visible=True;stage='snapshot external + source-command f32 curves'
        else:
            local=states[12]['local'];visible=False;stage='ended; SDK matrices retained, no further visible update'
        states[frame]=dict(local=local,world=worlds(local,initial['parent']),visible=visible,scale=[x.tolist() for x in scales],translation=[x.tolist() for x in translations],stage=stage)
    # The secondary matrix-update stream is independently retained. It is not
    # the draw stream: rendering uses thread+8, update uses thread+0x78.
    for x in [q for q in events if q['update_phase']=='seq_secondary']:
        w=x['command_words'];trace.append(dict(event=x['call_order_index'],frame=x['native_frame'],pc=x['pc'],seq_offset=x['seq_offset'],handler=x['handler'],opcode=w[0]&255,subopcode=(w[0]>>8)&255,arguments=w,thread=x['thread'],native_wait=0,effect_node='',operation='secondary update stream at thread+0x78; model flags/matrix application',before='',after='',status='native_dispatch_captured_raw_preserved'))
    # The draw stream is statically bounded (three words) and its live pointer
    # is captured in the same episode, including the empty activation/end cases.
    for frame in range(6,13):
        x=next(q for q in events if q['native_frame']==frame and q['update_phase']=='effect_callback_post');thread=x['effect']['threads'][0];assert thread['words'][2]-int(x['effect']['base'],0)==12920
        for off,word,operation in [(12920,0x0300000f,'material state transfer; packed graphics unsupported'),(12924,0x0300320e,'model0 draw submission -> 088CE7F8 -> 088781D8'),(12928,0x200,'return from render stream')]:
            trace.append(dict(event=x['call_order_index'],frame=frame,pc='088D3BDC',seq_offset=off,handler='088CC0A4' if off==12920 else '088CD800' if off==12924 else '088D2474',opcode=word&255,subopcode=(word>>8)&255,arguments=[word],thread=thread['pointer'],native_wait=0,effect_node='',operation=operation,before='',after='',status='static_stream_plus_same_episode_live_pointer; not an individual opcode breakpoint'))
    trace.sort(key=lambda x:(x['frame'],x['event'],x['seq_offset']))
    return states,external,trace,wait_checks,initial,offset

def main():
    capture=readjson(P/'EPISODE_CAPTURE.json');events=readjson(P/'EVENTS.json');allframes=readjson(P/'FRAMES.json');fr=[f for f in allframes if f['frame']>=2];ident=readjson(P/'MODEL_IDENTITIES.json');mi=readrows(EU/'Metadata/MODEL_INDEX.csv');bi=readrows(EU/'Metadata/SOURCE_BONE_INDEX.csv');models={r['asset_id']:r for r in mi};bm=mapped(models['FSN248769'],bi);wm=mapped(models['FSN248770'],bi);em=mapped(models['FSN248817'],bi)
    assert ident[str(int(capture['body'],0))]['remap'][153]==32 and ident[str(int(capture['weapon'],0))]['remap'][0]==1
    bframes={f['frame']:pose(f['body']) for f in allframes};wframes={f['frame']:pose(f['weapon']) for f in allframes};delta=events[42]['body_delta'];times=np.array([np.float32((f['frame']-2)*delta) for f in fr],np.float32)
    output,reconstructed,glbcheck=encode_glb(models['FSN248769'],bm,[bframes[f['frame']] for f in fr],times)
    numeric=[];references=[]
    def compare(kind,frame,event,node,a,b,status='PASS'):
        mx,fo,te=error(a,b);numeric.append(dict(component=kind,native_frame=frame,master_time=float(np.float32((frame-2)*delta)),event=event,node=node,matrix_max_abs_error=mx,matrix_frobenius_error=fo,translation_max_abs_error=te,status=status if mx<2e-5 else 'FAIL',runtime_matrix=flat(b),replay_matrix=np.asarray(a).reshape(-1,order='F').tolist()))
    for fi,f in enumerate(fr):
        frame=f['frame'];bp=bframes[frame];wp=wframes[frame];target=bp['world'][32]
        wlocals=[x.copy() for x in wframes[2]['local']];wlocals[1]=target;ww=worlds(wlocals,wp['parent'])
        for i,(a,b) in enumerate(zip(reconstructed[fi],bp['world'])):compare('body_final_world',frame,f['event'],i,a,b)
        for i,(a,b) in enumerate(zip(ww,wp['world'])):compare('weapon_from_current_body153',frame,f['event'],i,a,b)
        references.append(dict(frame=frame,time=float(times[fi]),event=f['event'],body_clip=f['body_clip'],body_time=f['body_time'],body_world=[flat(x) for x in bp['world']],weapon_world=[flat(x) for x in wp['world']]))
    states,external,trace,wait_checks,initial,birth=effect_subset(events,bframes,ident[str(0x09530630)])
    fxrefs=[]
    for x in events:
        if x['update_phase']!='effect_callback_post':continue
        frame=x['native_frame']
        if frame not in states:continue
        fx=x['effect'];po=fx['models'][0]['pose'];pp=pose(po);state=states[frame]
        for i,(a,b) in enumerate(zip(state['world'],pp['world'])):compare('effect_seq_world',frame,x['call_order_index'],i,a,b)
        if 6<=frame<13:
            for i in [1]:compare('effect_external_snapshot',frame,x['call_order_index'],i,external,matrix(pp['rt'],i*320+240))
        render_pointer=fx['threads'][0]['words'][2];assert state['visible']==bool(render_pointer)
        fxrefs.append(dict(frame=frame,time=float(np.float32((frame-2)*delta)),event=x['call_order_index'],context_state=fx['state'],visible=bool(render_pointer),runtime_render_thread=hex(render_pointer),runtime_context_flags=fx['flags'],runtime_model_flags=hex(u((P/po['wrapper']).read_bytes(),0)),world=[flat(z) for z in pp['world']]))
    # Raw MOT comparison is an explicit failed control, never an export source.
    idx=readjson(EU/'Metadata/ANIMATION_INDEX.json');ir=next(x for x in idx if x['asset_id']=='FSN258272');decoded=readjson(ir['working_path']);sk=skeleton('lan');lut=np.frombuffer((AW/'Runtime/Motion/lan/rotation_sine_lut.bin').read_bytes(),dtype='<f4');raw=[]
    for frame in [3,5,6,7,12]:
        f=next(z for z in fr if z['frame']==frame);p=evaluate(decoded,sk,f['body_time'],lut);bp=bframes[frame]
        raw.append(dict(frame=frame,body_time=f['body_time'],raw_vs_sdk_local_max=max(error(mat(n['local_matrix']),bp['local'][i])[0] for i,n in enumerate(p['nodes'])),raw_vs_final_world_max=max(error(mat(n['world_matrix']),bp['world'][i])[0] for i,n in enumerate(p['nodes'])),status='raw_single_clip_is_not_final_battle_pose'))
    audio=readjson(P/'AUDIO_CHAIN.json');assert audio['sound_id']==0x232d and audio['setvoice_return']==0 and audio['keyon_return']==0;assert sha(P/'audio_payload.bin')==audio['payload_sha256'];flac=EU/f"Converted/AudioBank/{audio['payload_sha256']}_22050.flac";assert flac.exists()
    keyon=events[audio['keyon_event']];start_time=float(np.float32((keyon['native_frame']-2)*delta));clock=dict(episode_id=capture['episode_id'],sound_id=audio['sound_id'],sound_asset_id='FSN260985',working_path=str(flac),request_event=98,request_native_frame=5,request_body_time=events[98]['body_time'],keyon_event=174,keyon_return_event=175,keyon_native_frame=6,keyon_body_time=keyon['body_time'],replay_start=start_time,replay_start_rule='confirmed SAS KeyOn in native frame6; event174; order after FX matrix commitment',decoded_file_rate=22050,decoded_file_duration=0.5371428571428571,audio_start='confirmed',native_sample_clock='not fully reconstructed',native_pitch='unknown; no source-runtime waveform equivalence claimed',sample_cursor=None,host_wall_clock_used=False,causal_chain=audio)
    js(BMD/'FUC_AUDIO_REPLAY_CLOCK.json',clock)
    timeline=[]
    for x in events:
        if x['native_frame']<2:continue
        domain='effect_fixed8' if x['update_phase'].startswith(('seq','effect','offset','external')) else 'audio_runtime' if x['update_phase'] in ['audio_event','encoded_request','queue_created','queue_consumer','sample_lookup','sample_lookup_post','voice_start','sas_setvoice','sas_setvoice_post','sas_keyon','sas_keyon_post'] else 'body_60hz'
        effect=x.get('effect',{});wait=effect.get('threads',[{}])[0].get('words',[0]*30)[29] if effect.get('threads') else None
        timeline.append(dict(sequence=x['call_order_index'],master_time=float(np.float32((x['native_frame']-2)*delta)),body_time=x['body_time'],body_frame=x['native_frame']-2,update_phase=x['update_phase'],clock_domain=domain,native_time=wait if domain=='effect_fixed8' else x['body_time'] if domain=='body_60hz' else None,event_type=x['update_phase'],resource='1000.seq/1002.gmo' if domain=='effect_fixed8' else 'chr_lan00.phd' if domain=='audio_runtime' else 'chr/lan/0000.gmo',asset_id='FSN248810/FSN248817' if domain=='effect_fixed8' else 'FSN260985' if domain=='audio_runtime' else 'FSN248769',transform_source='same episode final SDK' if domain!='audio_runtime' else '',audio_source='exact queue/program/payload/SAS chain' if domain=='audio_runtime' else '',status='captured',evidence=str(P/'EVENTS.json')+'#'+str(x['call_order_index'])))
    rows(BMD/'FUC_LAN_CLIP145_REPLAY_TIMELINE.csv',timeline);rows(BMD/'FUC_FRAME_UPDATE_ORDER.csv',[dict(native_frame=x['native_frame'],call_order_index=x['call_order_index'],update_phase=x['update_phase'],body_time=x['body_time'],function=x['pc'],caller=hex(x['registers']['ra']),player_flags=x['player_flags'],transition_fields=x['transition_fields']) for x in events]);rows(BMD/'FUC_SEQ_REPLAY_TRACE.csv',trace);rows(BMD/'FUC_LAN_CLIP145_RUNTIME_VS_REPLAY.csv',numeric)
    rows(BMD/'FUC_BATTLE_POSE_COMPONENTS.csv',raw)
    components=[]
    for x in events:
        if x['update_phase'] not in ['mot_eval_post','fan_eval','fan_eval_post','bpo_apply','bpo_apply_post','body_apply','body_apply_post']:continue
        components.append(dict(stage=x['update_phase'],function=x['pc'],caller=hex(x['registers']['ra']),input_buffer=capture['player'] if x['update_phase']=='mot_eval_post' else capture['body'],output_buffer=x['pose']['runtime'],node='all 60 SDK nodes',time=x['body_time'],source_component='captured actual pipeline stage',status='observed; composition formula not generalized',notes='raw/local/world kept separately; final world is replay authority'))
    rows(BMD/'FUC_BATTLE_POSE_PIPELINE.csv',components)
    keyevents=[x for x in timeline if x['event_type'] in ['clip_select','clip_selected','effect_activate','effect_activated','offset_point','external_copy_post','audio_event','queue_created','sas_setvoice','sas_keyon','sas_keyon_post']]
    episode=dict(**capture,semantic_endpoint_coverage='complete for recorded replay scope',collector_terminal_status='extra-tail timeout preserved; not a successful 90-frame collector completion',last_complete_native_frame=fr[-1]['frame'],replay_duration=float(times[-1]),effect_end_event=408,effect_end_native_frame=13,cleanup_phase_event=431,body_departure_native_frame=16,audio_keyon_return=175,audio_decoded_preview_end=start_time+clock['decoded_file_duration'],audio_sas_voice_completion='not captured; decoded-file completion only',clock_bridge=dict(origin_event=42,origin_native_frame=2,measured_native_delta=delta,master_time='float32((native_frame-2)*measured_body_delta)',phase='call_order_index retained; rendered frame composed after FX/audio callbacks',body_time_resets_preserved=True,host_wall_clock_used=False),pointers=dict(character=capture['character'],player=capture['player'],body=capture['body'],weapon=capture['weapon'],effect_ctx='0x08D8CD94',effect_thread='0x08DA8974',audio_queue=audio['queue'],sas_slot=audio['slot']),key_events=keyevents)
    js(BMD/'FUC_LAN_CLIP145_EPISODE.json',episode)
    failures=[x for x in numeric if x['status']=='FAIL'];metrics={kind:dict(comparisons=len(z),max_matrix_element_error=max(x['matrix_max_abs_error'] for x in z),max_frobenius_error=max(x['matrix_frobenius_error'] for x in z)) for kind in sorted(set(x['component'] for x in numeric)) for z in [[x for x in numeric if x['component']==kind]]}
    assert not failures, failures[:2]
    refs=dict(episode_id=capture['episode_id'],body_mapping=bm,weapon_mapping=wm,effect_mapping=em,body=references,effect=fxrefs,glb_validation=glbcheck);js(OUT/'runtime_reference.json',refs)
    effect=dict(seq_asset_id='FSN248810',model_asset_id='FSN248817',model=web(models['FSN248817']['working_path']),mode='validated simplified geometry/transform/timing renderer',birth_native_frame=6,birth_event=132,activation_native_frame=5,activation_event=82,end_native_frame=13,end_event=408,cleanup_native_frame=14,cleanup_event=431,birth_rule='current body153 at native frame6 @ T(0,2.4,0); snapshot retained',offset=[0.,float(np.float32(2.4)),0.],offset_evidence=str(P/birth['vector']),initial_local=[flat(x) for x in initial['local']],initial_evidence=first_effect_evidence(events),seq_commands=[dict(frame=x['frame'],event=x['event'],opcode=x['opcode'],subopcode=x['subopcode'],words=x['arguments'],offset=x['seq_offset']) for x in trace],computed_states=[dict(frame=k,scale=v['scale'],translation=v['translation'],visible=v['visible'],stage=v['stage']) for k,v in states.items()],scope='trace-guided model/thread resolution; source op16 absolute scale; op18 kind0/kind5; fixed8 wait; native end; no whole-file SEQ interpreter')
    manifest=dict(episode_id=capture['episode_id'],status='validated_episode_replay_pending_viewer',character='lan (Lancer explicit user/runtime identity)',body_model=dict(asset_id='FSN248769',logical_path='chr/lan/0000.gmo'),body_animation_source=web(output),raw_clip=dict(asset_id='FSN258272',mot_asset_id='FSN248809',index=145,export_source=False),final_pose_pipeline='runtime-authoritative final SDK world; world-derived local adapter includes captured composition/cached corrections',body_mapping=bm,body_frames=[dict(frame=f['frame'],time=float(times[i]),body_clip=f['body_clip'],body_time=f['body_time']) for i,f in enumerate(fr)],weapon=dict(asset_id='FSN248770',model=web(models['FSN248770']['working_path']),mapping=wm),attachment_rule=dict(body_source_bone_id=153,body_ordinal=32,body_glb_node=42,weapon_source_bone_id=0,weapon_ordinal=1,weapon_glb_node=2,rule='each playback frame weapon0 world = current body153 world; no historical weapon matrices used'),effect=effect,effect_mapping=em,sound_request=audio,sound_asset=dict(asset_id='FSN260985',working_path=web(flac),payload_sha256=audio['payload_sha256']),audio_start=dict(master_time=start_time,event=174,native_frame=6,domain='audio_runtime',confirmed=True),clock_domains=['body_60hz','effect_fixed8','audio_runtime'],master_clock=episode['clock_bridge'],duration=float(times[-1]),reference=web(OUT/'runtime_reference.json'),timeline=web(BMD/'FUC_LAN_CLIP145_REPLAY_TIMELINE.csv'),unsupported_features=['exact PSP material packed-color/blend/palette/shader implementation','native SAS pitch and sample-clock evolution','general arbitrary battle-pose composition formula','original game camera/stage/HUD/opponent'],new_asset_ids=0,validation_summary=dict(offline='PASS',matrix_metrics=metrics,glb=glbcheck,viewer='pending',raw_control=raw))
    manifest['effect']['source_bone_remap']=ident[str(0x09530630)]['remap']
    manifest['effect']['visible_native_frames']=sorted({r['frame'] for r in fxrefs if r['visible']})
    manifest['effect']['visibility_evidence']='thread+8 render stream: zero at activation frame5, SEQ+12920 on frames6..12, zero on frame13 END; callback mode0x80 gate and source draw submission at 088CE7F8'
    js(BMD/'FUC_LAN_CLIP145_REPLAY_MANIFEST.json',manifest);js(BR/'BUILD_VALIDATION.json',dict(status='PASS',episode_id=capture['episode_id'],metrics=metrics,glb=glbcheck,raw_control=raw,wait_checks=wait_checks,effect_external=flat(external),body_source153_change_after_birth=max(error(bframes[i]['world'][32],bframes[6]['world'][32])[0] for i in range(7,13)),sample_frames=len(fr),failures=0));print(json.dumps(readjson(BR/'BUILD_VALIDATION.json'),ensure_ascii=False))
def first_effect_evidence(events):return str(P/next(x for x in events if x['update_phase']=='effect_callback_post')['effect']['models'][0]['pose']['sdk'])
if __name__=='__main__':main()
