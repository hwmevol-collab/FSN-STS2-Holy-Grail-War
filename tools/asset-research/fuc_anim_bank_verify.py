"""Verify a naturally used relocated MOT bank against existing decoded source clips."""
from fuc_motion_evaluator import *
def main():
    idx=readjson(EU/'Metadata/ANIMATION_INDEX.json');results=[]
    for folder in (AW/'Runtime/Natural').rglob('player_*'):
        cap=readjson(folder/'CAPTURE.json');code=cap['model_file'].split('/')[1]
        match=cap['bank_sources'][0]['fingerprint_matches'][0];base=int(cap['banks'][0],0);raw=(folder/'bank_0.bin').read_bytes()
        slots=match['offset_slots'];table=list(struct.unpack_from('<'+'I'*slots,raw,16));channels=keys=0;errors=[]
        for ir in [r for r in idx if r['parent_asset_id']==match['mot_asset_id'] and r.get('working_path')]:
            j=readjson(ir['working_path']);clip=ir['motion_table_index'];off=table[clip]-base
            flag,n,sz,transition,end=struct.unpack_from('<HHIff',raw,off)
            if n!=j['channel_count'] or end!=j['end_time'] or transition!=j['play_speed']:errors.append([clip,'header'])
            for c in j['channels']:
                ci=c['channel_index'];co=off+16+ci*32;packed,bone,count,total,_,tp,vp,_,_=struct.unpack_from('<IHHf5I',raw,co)
                if (packed&0xffff,packed>>16,bone,count,total)!=(c['track_flags'],c['flags'],c['source_bone_id'],c['key_count'],c['total_time']):errors.append([clip,ci,'channel header'])
                # Relocation may leave the no-coordinate control time as an offset.
                to=tp-base if tp>=base else off+tp
                times=np.frombuffer(raw,dtype='<f4',count=count,offset=to)
                if not np.array_equal(times,np.asarray(c['times'],np.float32)):errors.append([clip,ci,'time values'])
                if c['values']:
                    vo=vp-base if vp>=base else off+vp
                    v=(np.frombuffer(raw,dtype='<u2',count=count*4,offset=vo).astype(np.uint32)<<16).view(np.float32).reshape(count,4)
                    if not np.array_equal(v,runtime_keys(c)):errors.append([clip,ci,'coordinate values',float(np.max(np.abs(v-runtime_keys(c))))])
                    keys+=count*4
                channels+=1
        results.append(dict(code=code,model_file=cap['model_file'],mot_file=match['mot_file'],source_sha256=match['sha256'],offset_slots=slots,channels_checked=channels,key_values_checked=keys,errors=errors,status='PASS' if not errors else 'FAIL',evidence_path=str(folder)))
    jsonwrite(AW/'Runtime/Natural/NATURAL_BANK_SOURCE_VERIFICATION.json',results);log('NATURAL BANK VERIFY',results)
if __name__=='__main__':main()
