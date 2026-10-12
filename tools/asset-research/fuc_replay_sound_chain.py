"""Natural battle request -> queued object -> bank/program -> voice -> SAS. No injected calls."""
from fuc_replay_debugger import *
from fuc_replay_function_probe import wait,snap
import argparse,time,struct,hashlib
p=argparse.ArgumentParser();p.add_argument('--character',type=lambda x:int(x,0),required=True);p.add_argument('--button',default='triangle');p.add_argument('--folder',required=True);a=p.parse_args();out=BR/a.folder;out.mkdir(parents=True,exist_ok=True);d=BattleDebugger();active=set();chain=[]
def hit(addr,label,condition=''):
 d.call('cpu.breakpoint.add',address=addr,enabled=True,condition=condition);active.add(addr);d.resume();rr=wait(d,addr,time.monotonic()+12);d.call('cpu.breakpoint.remove',address=addr);active.remove(addr)
 s=snap(d,rr,out,label,actor=a.character);d.dump(rr['sp'],512,out/(label+'_stack.bin'));chain.append(dict(label=label,pc=hex(addr),ra=hex(rr['ra']),registers=rr));return rr
try:
 d.pause();d.call('input.buttons.send',buttons={a.button:True})
 event=hit(0x089a8264,'battle_event',f'a0=={hex(a.character)}');d.dump(a.character,0x2600,out/'battle_character.bin')
 request=hit(0x08874990,'encoded_request',f'ra==0x089a84a8');sound_id=request['a1'];d.dump(0x089baef4,0x240,out/'bank_remap_table.bin')
 returned=hit(request['ra'],'queue_created');queue=returned['v0'];assert 0x08800000<queue<0x0a000000;d.dump(queue,0x16,out/'queue.bin');q=d.read(queue,0x16);encoded=struct.unpack_from('<H',q,4)[0];bank=encoded>>8;program=(encoded&0x7f)-1;print('request',hex(sound_id),'queue',hex(queue),'bank',bank,'program',program,flush=True)
 handle=struct.unpack('<I',d.read(0x089fcd70+bank*4,4))[0];d.dump(handle,0x4c,out/'logical_bank_handle.bin');registered_bank=struct.unpack('<I',d.read(handle+8,4))[0]
 consumer=hit(0x08946a9c,'queue_consumer',f's0=={hex(queue)}');assert consumer['a0']==registered_bank and consumer['a2']==program;d.dump(queue,0x16,out/'queue_at_consumer.bin')
 brptr=struct.unpack('<I',d.read(0x08a13c5c+registered_bank*4,4))[0];bank_record=d.read(brptr,0x10);(out/'bank_record.bin').write_bytes(bank_record);header,body=struct.unpack_from('<2I',bank_record);d.dump(header,256,out/'bank_header_prefix.bin')
 lookup=hit(0x089477bc,'sample_lookup');lookupout=lookup['a2'];after=hit(lookup['ra'],'sample_lookup_return');d.dump(lookupout,0x44,out/'lookup_result.bin')
 voice=hit(0x08949a88,'voice_record_start');record=voice['a0'];vr=d.read(record,0x68);(out/'voice_record.bin').write_bytes(vr);payload,size=struct.unpack_from('<2I',vr,0x20);record_group,record_bank=struct.unpack_from('<2I',vr,0x10);assert record_bank==registered_bank;resolved=(out/'lookup_result.bin').read_bytes();assert struct.unpack_from('<2I',resolved,4)==(payload,size)
 setvoice=hit(0x0894a314,'sas_setvoice');assert setvoice['a1']==payload and setvoice['a2']==size;d.dump(payload,size,out/'payload.bin');slot=setvoice['a0'];setret=hit(setvoice['ra'],'sas_setvoice_return')
 keyon=hit(0x0894a1ac,'sas_keyon',f'a0=={slot}');keyret=hit(keyon['ra'],'sas_keyon_return');assert keyret['v0']==0
 result=dict(timestamp=now(),runtime_session='PPSSPP_PID_'+str((BR/'PPSSPP_PID.txt').read_text().strip()),battle_event_function='0x089A8264',battle_event_caller=hex(event['ra']-8),battle_event_args={x:event[x] for x in ['a0','a1','a2','a3']},sound_id=hex(sound_id),queue=hex(queue),queue_encoded_bank_program=hex(encoded),bank=bank,registered_bank=registered_bank,program_requested=program,record_group=record_group,record_bank=record_bank,bank_record=hex(brptr),header=hex(header),body=hex(body),voice_record=hex(record),sas_slot=slot,payload=hex(payload),size=size,payload_sha256=sha(out/'payload.bin'),setvoice_return=setret['v0'],keyon_return=keyret['v0'],causality='confirmed_request_object_and_nested_call_chain',chain=chain)
 jsonwrite(out/'CAUSAL_CHAIN.json',result);print(json.dumps({k:v for k,v in result.items() if k!='chain'}),flush=True)
finally:
 d.pause();d.call('input.buttons.send',buttons={a.button:False})
 for addr in active:d.call('cpu.breakpoint.remove',address=addr)
 jsonwrite(out/'TRACE_STAGES.json',chain);d.close()
