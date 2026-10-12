"""One natural input edge, one continuous debugger session, original read-only game RAM.
Native character update boundaries and every retained call are ordered; host times are diagnostic only.
"""
from fuc_replay_debugger import *
import struct,time,uuid,argparse
U=lambda b,o=0:struct.unpack_from('<I',b,o)[0]
F=lambda b,o=0:struct.unpack_from('<f',b,o)[0]
valid=lambda p:0x08800000<=p<0x09ffff00

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--frames',type=int,default=100);ap.add_argument('--folder',required=True);a=ap.parse_args()
 out=BR/a.folder;assert not out.exists();out.mkdir(parents=True)
 c=readjson(BR/'InterpreterLanCharacter/CHARACTER_RUNTIME.json');actor=int(c['character'],0);body=int(c['body'],0);player=int(c['player'],0);weapon=int(c['equipment'][0]['model'],0)
 d=BattleDebugger();active={};temp={};events=[];frames=[];effects={};infos={};frame=-1;order=0;start=None;selected=False;done=False;sound={};failure=None
 eid='lan145_'+uuid.uuid4().hex[:16]
 def add(pc,label,condition=''):
  if pc in active:raise RuntimeError(('duplicate BP',hex(pc),label,active[pc]))
  d.call('cpu.breakpoint.add',address=pc,enabled=True);active[pc]=label
 def ret(rr,label,data=None):
  pc=rr['ra'];add(pc,label);temp[pc]=data or {}
 def dump(name,data):(out/name).write_bytes(data);return name
 def minfo(p):
  if p in infos:return infos[p]
  b=d.read(p,0x340);n=U(b,0x58);assert 0<n<256;sdk=U(b,0x38);sh=d.read(sdk,0x40);ps=list(struct.unpack('<'+'I'*n,d.read(U(sh,0x18),n*4)));rb=d.read(U(b,0x48),2);rc=struct.unpack('<h',rb)[0];remap=list(struct.unpack('<'+'h'*rc,d.read(U(b,0x48)+2,rc*2)))
  x=dict(model=hex(p),path=cstring(d,U(b,0x34)+0x10),nodes=n,runtime_nodes=U(b,0x5c),sdk_nodes=ps,remap=remap,sdk=hex(sdk));infos[p]=x
  dump(f'model_{p:08x}_initial.bin',b);jsonwrite(out/'MODEL_IDENTITIES.json',infos);return x
 def pose(p,tag):
  x=minfo(p);ps=x['sdk_nodes'];lo=min(ps);hi=max(ps)+0x180;raw=d.read(lo,hi-lo);sdk=b''.join(raw[k-lo:k-lo+0x180] for k in ps);rt=d.read(x['runtime_nodes'],x['nodes']*0x140)
  dump(tag+'_sdk.bin',sdk);dump(tag+'_rt.bin',rt);dump(tag+'_model.bin',d.read(p,0x340));return dict(model=hex(p),sdk=tag+'_sdk.bin',runtime=tag+'_rt.bin',wrapper=tag+'_model.bin',nodes=x['nodes'])
 def fx(p,tag,withpose=True):
  cb=d.read(p,0x98);dump(tag+'_context.bin',cb);x=dict(context=hex(p),state=U(cb,4),owner=hex(U(cb,8)),flags=hex(U(cb)),base=hex(U(cb,0x74)),threads=[],models=[])
  for k in range(min(U(cb,0x38),10)):
   t=U(cb,0x10+k*4)
   if valid(t):b=d.read(t,0x84);dump(tag+f'_thread{k}.bin',b);x['threads'].append(dict(pointer=hex(t),words=list(struct.unpack('<33I',b))))
  for k in range(min(U(cb,0x64),10)):
   rec=U(cb,0x3c+k*4)
   if not valid(rec):continue
   rb=d.read(rec,0xb0);dump(tag+f'_record{k}.bin',rb);m=U(rb,4);item=dict(record=hex(rec),model=hex(m),words=list(struct.unpack('<44I',rb)),commands=[])
   for j in range(min(U(rb,0xc),12)):
    q=U(rb,0x10+j*4)
    if valid(q):db=d.read(q,0x3c);item['commands'].append(dict(pointer=hex(q),words=list(struct.unpack('<15I',db))));dump(tag+f'_command{k}_{j}.bin',db)
   if valid(m):item['path']=minfo(m)['path'];item['pose']=pose(m,tag+f'_fx{k}') if withpose else None
   x['models'].append(item)
  return x
 def event(label,rr,status):
  nonlocal order
  pb=d.read(player,0x100);dump(f'e{order:05d}_player.bin',pb)
  e=dict(episode_id=eid,call_order_index=order,native_frame=frame,update_phase=label,pc=hex(status['pc']),cpu_ticks=status.get('ticks'),registers=rr,body_clip=U(pb,0x1c),body_time=F(pb,8),body_delta=F(pb,12),player_flags=hex(U(pb)),player_dump=f'e{order:05d}_player.bin',transition_fields=[F(pb,o) for o in [0x10,0x14]],current_clip=hex(U(pb,0x18)))
  events.append(e);order+=1;return e
 def flush():
  jsonwrite(out/'EVENTS.json',events);jsonwrite(out/'FRAMES.json',frames);jsonwrite(out/'AUDIO_CHAIN.json',sound);jsonwrite(out/'EPISODE_CAPTURE.json',dict(episode_id=eid,pid=readjson(BR/'RUNTIME_PROCESS.json')['process_id'],character=hex(actor),body=hex(body),player=hex(player),weapon=hex(weapon),first_clip145_frame=start,frames=len(frames),events=len(events),effect_contexts=[hex(x) for x in effects],complete=done,failure=failure,ram_writes=0,hook_writes=0,source='original Europe ISO; one natural triangle input edge; no injected game calls',master_clock='observed per-frame motion-player entry 08884B28 (body delta measured); final body/weapon after equipment iterator and apply; intra-frame call order retained; host wall clock excluded'))
 try:
  d.pause()
  for bp in d.call('cpu.breakpoint.list').get('breakpoints',[]):d.call('cpu.breakpoint.remove',address=bp['address'])
  minfo(body);minfo(weapon)
  add(0x08884b28,'frame_start');add(0x08831138,'equipment_frame')
  for pc,label,cond in [(0x08886410,'clip_select',f'a0==0x{player:08x}'),(0x088326f4,'fan_eval',''),(0x08832584,'fan_clock',f'a0==0x{actor:08x}'),(0x08831e90,'bpo_apply',f'a0==0x{actor:08x}'),(0x08877378,'body_apply',f'a0==0x{body:08x}'),(0x08837964,'weapon_attach',''),(0x088311c8,'weapon_applied',f's1==0x{actor:08x}'),(0x088d4354,'effect_activate','ra==0x0897ec6c'),(0x089a8264,'audio_event',f'a0==0x{actor:08x}')]:add(pc,label,cond)
  d.resume();deadline=time.monotonic()+600
  while time.monotonic()<deadline:
   if (out/'STOP_REQUESTED').exists():raise RuntimeError('controlled diagnostic stop request')
   status=d.call('cpu.status')
   if not status.get('stepping'):time.sleep(.005);continue
   pc=status['pc'];rr=regs(d);label=active.get(pc)
   if label is None:raise RuntimeError(('unowned stop',status))
   # Filter register values read at the stop, avoiding JIT conditional-site ambiguity.
   filters={'frame_start':player,'equipment_frame':actor,'clip_select':player,'fan_eval':actor,'fan_clock':actor,'bpo_apply':actor,'body_apply':body,'weapon_attach':actor,'audio_event':actor}
   skip=label in filters and rr['a0']!=filters[label]
   if label=='weapon_applied':skip=rr['s1']!=actor
   if label=='effect_activate':skip=rr['ra']!=0x0897ec6c
   if label=='effect_callback':skip=rr['a0'] not in effects
   if label in ['seq_dispatch','seq_secondary']:skip=rr['s5'] not in effects
   if label=='offset_point':skip=rr['ra']!=0x088cf9b0
   if label=='external_copy':skip=rr['ra']!=0x088c9a90
   if label=='encoded_request':skip=rr['ra']!=0x089a84a8
   if label=='queue_consumer':skip=rr['s0']!=int(sound['queue'],0)
   if label=='sas_keyon':skip=rr['a0']!=sound['slot']
   if skip:d.resume();continue
   data=temp.pop(pc,None)
   if data is not None:d.call('cpu.breakpoint.remove',address=pc);active.pop(pc)
   if label=='frame_start':frame+=1
   e=event(label,rr,status);tag=f'e{e["call_order_index"]:05d}'
   if label=='frame_start':
    e['pose']=pose(body,tag+'_body');ret(rr,'mot_eval_post')
    if frame==2:d.call('input.buttons.send',buttons={'triangle':True});e['input']='single triangle press begins'
    if frame==9:d.call('input.buttons.send',buttons={'triangle':False});e['input']='triangle release'
    if frame%10==0:flush();print(json.dumps(dict(frame=frame,clip=e['body_clip'],time=e['body_time'],events=len(events),effects=len(effects),sound_id=sound.get('sound_id'),audio_keyon=sound.get('keyon_return'))),flush=True)
    if start is not None and frame-start>=a.frames:done=True;break
   elif label=='equipment_frame':e['equipment_mode']=rr['a1'];ret(rr,'frame_end',dict(mode=rr['a1']))
   elif label=='frame_end':
    b=pose(body,tag+'_body');w=pose(weapon,tag+'_weapon');char=d.read(actor,0x2600);dump(tag+'_character.bin',char)
    row=dict(equipment_mode=0,event=e['call_order_index'],frame=frame,body_clip=e['body_clip'],body_time=e['body_time'],body=b,weapon=w,effects=[])
    for ctx in list(effects):
     eb=d.read(ctx,0x98)
     if U(eb,8)==actor and U(eb,0x74)==effects[ctx]['base']:
      z=fx(ctx,tag+f'_ctx{ctx:08x}');row['effects'].append(z)
    frames.append(row)
   elif label=='clip_select':
    e['requested_clip']=rr['a1'];e['transition_bits']=rr.get('f12');ret(rr,'clip_selected',dict(requested=rr['a1']))
    if rr['a1']==145 and not selected:start=frame;selected=True;d.call('input.buttons.send',buttons={'triangle':False});e['input']='release after natural selection'
   elif label=='clip_selected':e['requested_clip']=data['requested']
   elif label in ['mot_eval','fan_eval','bpo_apply','body_apply']:
    e['pose']=pose(body,tag+'_body');ret(rr,label+'_post')
    if label in ['fan_eval','fan_clock','bpo_apply']:dump(tag+'_character.bin',d.read(actor,0x800))
   elif label in ['mot_eval_post','fan_eval_post','bpo_apply_post','body_apply_post']:
    e['pose']=pose(body,tag+'_body')
   elif label=='fan_clock':dump(tag+'_character.bin',d.read(actor,0x800));ret(rr,'fan_clock_post')
   elif label=='fan_clock_post':dump(tag+'_character.bin',d.read(actor,0x800))
   elif label=='weapon_attach':
    # No filtered heap guesses: assert this is the actor's actual attachment record.
    if rr['a0']==actor and rr['a1']==actor+0x5dc:e['pose']=pose(body,tag+'_body');e['weapon']=pose(weapon,tag+'_weapon');ret(rr,'weapon_attach_post')
   elif label=='weapon_attach_post':e['weapon']=pose(weapon,tag+'_weapon')
   
   elif label=='weapon_applied':e['weapon']=pose(weapon,tag+'_weapon')
   elif label=='effect_activate':
    e['activation_context']=hex(rr['a0']);ret(rr,'effect_activated',dict(ctx=rr['a0']))
   elif label=='effect_activated':
    ctx=data['ctx'];e['effect']=fx(ctx,tag)
    if not any(m.get('path')=='eft/chr/lan/1002.gmo' for m in e['effect']['models']):d.resume();continue
    base=int(e['effect']['base'],0);effects[ctx]=dict(base=base,activation_event=e['call_order_index']);dump(tag+'_runtime_seq.bin',d.read(base,30608))
    for pp,ll,co in [(0x088d3a80,'effect_callback',f'a0=={hex(ctx)}'),(0x088d39f4,'seq_dispatch',f's5=={hex(ctx)}'),(0x088d3a34,'seq_secondary',f's5=={hex(ctx)}'),(0x089449f0,'offset_point','ra==0x088cf9b0'),(0x08944668,'external_copy','ra==0x088c9a90')]:
     if pp not in active:add(pp,ll,co)
   elif label=='effect_callback':e['effect']=fx(rr['a0'],tag);ret(rr,'effect_callback_post',dict(ctx=rr['a0']))
   elif label=='effect_callback_post':e['effect']=fx(data['ctx'],tag)
   elif label in ['seq_dispatch','seq_secondary']:
    cursor=rr['a2'];handler=rr['v0'];raw=d.read(cursor,64);cb=d.read(rr['s5'],0x98);base=U(cb,0x74);thread=rr['s3'];e.update(context=hex(rr['s5']),thread=hex(thread),seq_offset=cursor-base,handler=hex(handler),command_words=list(struct.unpack('<16I',raw)),opcode=raw[0]);dump(tag+'_command.bin',raw);dump(tag+'_thread_before.bin',d.read(thread,0x84));e['effect']=fx(rr['s5'],tag,False);ret(dict(rr,ra=pc+8),'seq_return',dict(ctx=rr['s5'],thread=thread,seq_event=e['call_order_index']))
   elif label=='seq_return':
    e['seq_event']=data['seq_event'];dump(tag+'_thread_after.bin',d.read(data['thread'],0x84));e['effect']=fx(data['ctx'],tag)
   elif label=='offset_point':
    dump(tag+'_matrix.bin',d.read(rr['a1'],64));dump(tag+'_vector.bin',d.read(rr['a2'],16));e['source_matrix']=tag+'_matrix.bin';e['vector']=tag+'_vector.bin';e['source_pointer']=hex(rr['a1']);ret(rr,'offset_point_post',dict(target=rr['a0']))
   elif label=='offset_point_post':dump(tag+'_result.bin',d.read(data['target'],16));e['result']=tag+'_result.bin'
   elif label=='external_copy':
    dump(tag+'_source.bin',d.read(rr['a1'],16));dump(tag+'_before.bin',d.read(rr['a0'],16));e.update(source=tag+'_source.bin',target_pointer=hex(rr['a0']));ret(rr,'external_copy_post',dict(target=rr['a0']))
   elif label=='external_copy_post':dump(tag+'_after.bin',d.read(data['target'],16));e['after']=tag+'_after.bin'
   elif label=='audio_event':
    if selected and not sound:
     sound.update(event=e['call_order_index'],sound_id=rr['a1'],event_arguments={k:rr[k] for k in ['a0','a1','a2','a3']},random_state=U(d.read(0x08b1d1e0,4)),list_pointer=hex(rr['s0']),list_count=rr['s2'],selection_pointer=hex(rr['v1']))
     if 0<rr['s2']<128 and valid(rr['s0']):sound['list']=list(struct.unpack('<'+'I'*rr['s2'],d.read(rr['s0'],rr['s2']*4)));sound['random_index']=(rr['v1']-rr['s0'])//4
     add(0x08874990,'encoded_request','ra==0x089a84a8')
   elif label=='encoded_request':sound['encoded_request']=e['call_order_index'];sound['request_args']={k:rr[k] for k in ['a0','a1','a2','a3']};d.call('cpu.breakpoint.remove',address=pc);active.pop(pc);ret(rr,'queue_created')
   elif label=='queue_created':
    queue=rr['v0'];q=d.read(queue,0x16);dump('audio_queue.bin',q);encoded=struct.unpack_from('<H',q,4)[0];bank=encoded>>8;program=(encoded&127)-1;handle=U(d.read(0x089fcd70+bank*4,4));hb=d.read(handle,0x4c);dump('audio_logical_handle.bin',hb);registered=U(hb,8);record=U(d.read(0x08a13c5c+registered*4,4));rb=d.read(record,16);dump('audio_bank_record.bin',rb);header,bodyptr=struct.unpack_from('<2I',rb);dump('audio_bank_header.bin',d.read(header,16172));sound.update(queue=hex(queue),encoded=encoded,logical_bank=bank,program=program,registered_bank=registered,handle=hex(handle),bank_record=hex(record),header=hex(header),body=hex(bodyptr),queue_created_event=e['call_order_index']);add(0x08946a9c,'queue_consumer',f's0=={hex(queue)}')
   elif label=='queue_consumer':
    assert rr['a0']==sound['registered_bank'] and rr['a2']==sound['program'];dump('audio_queue_at_consumer.bin',d.read(int(sound['queue'],0),0x16));sound['queue_consumer_event']=e['call_order_index'];d.call('cpu.breakpoint.remove',address=pc);active.pop(pc);add(0x089477bc,'sample_lookup',f'a0=={rr["a0"]}')
   elif label=='sample_lookup':sound['sample_lookup_event']=e['call_order_index'];d.call('cpu.breakpoint.remove',address=pc);active.pop(pc);ret(rr,'sample_lookup_post',dict(target=rr['a2']))
   elif label=='sample_lookup_post':
    b=d.read(data['target'],0x44);dump('audio_lookup.bin',b);sound['lookup_payload'],sound['lookup_size']=struct.unpack_from('<2I',b,4);add(0x08949a88,'voice_start')
   elif label=='voice_start':
    b=d.read(rr['a0'],0x68);dump('audio_voice.bin',b);sound.update(voice=hex(rr['a0']),voice_start_event=e['call_order_index'],voice_group=U(b,0x10),voice_bank=U(b,0x14),payload=U(b,0x20),size=U(b,0x24));assert sound['voice_bank']==sound['registered_bank'] and (sound['payload'],sound['size'])==(sound['lookup_payload'],sound['lookup_size']);d.call('cpu.breakpoint.remove',address=pc);active.pop(pc);add(0x0894a314,'sas_setvoice')
   elif label=='sas_setvoice':
    assert(rr['a1'],rr['a2'])==(sound['payload'],sound['size']);dump('audio_payload.bin',d.read(rr['a1'],rr['a2']));sound.update(slot=rr['a0'],payload_sha256=sha(out/'audio_payload.bin'),setvoice_event=e['call_order_index'],setvoice_loop=rr['a3']);d.call('cpu.breakpoint.remove',address=pc);active.pop(pc);ret(rr,'sas_setvoice_post')
   elif label=='sas_setvoice_post':sound['setvoice_return']=rr['v0'];add(0x0894a1ac,'sas_keyon',f'a0=={sound["slot"]}')
   elif label=='sas_keyon':sound['keyon_event']=e['call_order_index'];d.call('cpu.breakpoint.remove',address=pc);active.pop(pc);ret(rr,'sas_keyon_post')
   elif label=='sas_keyon_post':sound['keyon_return']=rr['v0'];sound['keyon_return_event']=e['call_order_index']
   d.resume()
  if not done:raise TimeoutError('bounded episode capture timed out')
 except Exception as ex:failure=repr(ex);raise
 finally:
  flush();d.pause();d.call('input.buttons.send',buttons={'triangle':False})
  for pc in list(active):
   try:d.call('cpu.breakpoint.remove',address=pc)
   except RuntimeError:pass
  jsonwrite(out/'CLEANUP.json',dict(cpu=d.call('cpu.breakpoint.list'),memory=d.call('memory.breakpoint.list'),ram_writes=0));d.close()
if __name__=='__main__':main()
