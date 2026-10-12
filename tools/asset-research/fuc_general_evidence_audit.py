"""Reproduce causal/texture/source-segment audits entirely from preserved new captures."""
from fuc_general_common import *
from elftools.elf.elffile import ELFFile
import io

def main():
    c=readjson(BR/'LanSoundCausality5/CAUSAL_CHAIN.json');m={r['label']:r['registers'] for r in c['chain']};p=BR/'LanSoundCausality5';q=(p/'queue.bin').read_bytes();qc=(p/'queue_at_consumer.bin').read_bytes();lr=(p/'lookup_result.bin').read_bytes();vr=(p/'voice_record.bin').read_bytes()
    checks=dict(event_equals_encoded_request=m['battle_event']['a1']==m['encoded_request']['a1'],returned_queue_equals_consumer_s0=m['queue_created']['v0']==m['queue_consumer']['s0'],queue_encoded_id_preserved=q[4:6]==qc[4:6],consumer_bank_equals_parser=m['queue_consumer']['a0']==m['sample_lookup']['a0']==c['registered_bank'],consumer_program_equals_parser=m['queue_consumer']['a2']==m['sample_lookup']['a1']==c['program_requested'],lookup_payload_size_equals_voice=lr[4:12]==vr[0x20:0x28],voice_payload_size_equals_sas=struct.unpack_from('<2I',vr,0x20)==(m['sas_setvoice']['a1'],m['sas_setvoice']['a2']),slot_setvoice_equals_keyon=m['sas_setvoice']['a0']==m['sas_keyon']['a0'],setvoice_return_zero=m['sas_setvoice_return']['v0']==0,keyon_return_zero=m['sas_keyon_return']['v0']==0)
    assert all(checks.values());jsonwrite(p/'CAUSAL_NUMERIC_AUDIT.json',dict(checks=checks,status='PASS',scope='Same returned queue, bank/program, resolved payload/size, voice record fields, original SAS returns.'))
    rows=[]
    for f in sorted((BR/'RinTextureConsumer').glob('???_entry.json')):
        j=readjson(f);reg=j['registers'];frame=reg['t0'];fb=f.with_name(f.stem+'_a2.bin').read_bytes();count=struct.unpack_from('<I',fb,8)[0];entries=[struct.unpack_from('<4i',fb,16+16*i) for i in range(count)];A=B=-1
        for time,mode,ta,tb in entries:
            if time<=frame:
                if ta>=0:A=ta
                if tb>=0 and mode not in(-2,-3):B=tb
        post=f.with_name(f.stem.replace('_entry','_post')+'_a0.bin').read_bytes();code=struct.unpack_from('<I',post)[0];cache=struct.unpack_from('<2I',post,0x1a0);expected=(((code+0x96)<<16)|(A-1)) if A>0 else A,(((code+0xa6)<<16)|(B-1)) if B>0 else B
        assert cache==expected
        rows.append(dict(character='rin',frame=frame,selector_A=A,selector_B=B,character_code_numeric=code,runtime_cached_A=hex(cache[0]),runtime_cached_B=hex(cache[1]),expected_A=hex(expected[0]),expected_B=hex(expected[1]),error=0,status='confirmed_runtime_selector_encoding',evidence=str(f),notes='Last eligible source selector then original resource-key encoding; final image semantics not assigned.'))
    csvwrite(BMD/'FUC_FAN_TEXTURE_RUNTIME_PROOF.csv',rows)
    ep=W/'fuc/Europe/Executable/EBOOT_DECRYPTED.bin';elf=ELFFile(io.BytesIO(ep.read_bytes()));sections=[dict(name=s.name,address=int(s['sh_addr']),size=int(s['sh_size']),flags=int(s['sh_flags'])) for s in elf.iter_sections() if int(s['sh_flags'])&4]
    addresses=[0x08831e90,0x088326f4,0x08837d04,0x088c9850,0x088c9a88,0x088cf9a8,0x088d3a80,0x089449f0,0x0898d91c,0x089a8264,0x08874990,0x08946a9c,0x089477bc,0x08949a88,0x0894a314,0x0894a1ac]
    scoped=[dict(address=hex(a),executable=any(s['address']<=a<s['address']+s['size'] for s in sections)) for a in addresses];assert all(r['executable'] for r in scoped)
    jsonwrite(BR/'EXECUTABLE_ADDRESS_SCOPE.json',dict(elf=str(ep),bytes=ep.stat().st_size,sha256=sha(ep),SHF_EXECINSTR_sections=sections,addresses=scoped,notes='Static xref helper scans only SHF_EXECINSTR. Disassembly is bounded to these known executable regions.'))
    jsonwrite(BR/'DISCARDED_INTERPRETATIONS.json',dict(entries=[dict(path='LanTables/SirTables equipment_records.bin',reason='Early helper used0x8C stride. Superseded by full8xC8 captures and actual08837D04 consumer.'),dict(path='SirFull/RinFull CHARACTER_RUNTIME bank path fields',reason='Early bank pointers were mistakenly treated as resource wrappers. They are relocated MOT data bases; only FullVerified and MOT_BANK_SOURCE_PROOF are accepted.'),dict(path='SirFullFinal/RinFullFinal bank count',reason='Runtime MOT slot count is LE uint16 at+6, not a BE uint32 at+4. Superseded by FullVerified.'),dict(path='LanSoundCausality1..4',reason='Failed assertions or nohit probes; program field and bank/record domains corrected in Causality5. No queue-reuse conclusion is supported.'),dict(path='effect basis identity candidate',reason='Full matrix samples and basis write watch show inherited birth orientation; identity-basis hypothesis rejected.'),dict(path='continuous identity bone153 attachment',reason='Prior rejected hypothesis remains rejected. Actual formula has source offset and cached birth pose.')],accepted_character_captures=['LanTablesFinal','SirTablesFinal','SirFullVerified','RinFullVerified'],accepted_sound_chain='LanSoundCausality5',notes='Failed raw diagnostic captures remain preserved; no failed interpretation is promoted into an accepted index.'))
    print('Causal audit10/10; Rin selector audit2/2; executable address scope16/16')
if __name__=='__main__':main()
