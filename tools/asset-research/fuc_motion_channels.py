"""Read-only bounded MOT channel recovery; GNTool algorithm validated locally.
No semantic names, playback or bone binding are inferred from file proximity.
"""
from fuc_common import *
ROOT=STAGE_ROOT
def parse_clip(b,o,end):
    zero,n,hs,speed,duration=struct.unpack_from('>HHIff',b,o)
    assert zero==0 and hs==16 and n<2048 and o+16+32*n<=end
    assert math.isfinite(speed) and math.isfinite(duration) and 0<=duration<3600
    channels=[]
    for i in range(n):
        at=o+16+32*i
        flags,track,bone,count,time,pad,to,co,p1,p2=struct.unpack_from('>4Hf5I',b,at)
        assert pad==p1==p2==0 and math.isfinite(time)
        assert o+to+4*count<=end and to>=16+32*n
        times=list(struct.unpack_from('>'+str(count)+'f',b,o+to))
        assert all(math.isfinite(x) for x in times)
        coords=[];raw_words=[];enc='none'
        if flags&0x200:
            unit=8 if flags&2 else 16 if flags&4 else 0
            assert unit and co>=16+32*n and o+co+unit*count<=end
            assert co==((to+4*count+15)//16)*16
            enc='IEEE754_float32_high16' if unit==8 else 'IEEE754_float32'
            for k in range(count):
                raw=b[o+co+k*unit:o+co+(k+1)*unit]
                vals=list(struct.unpack('>4f',b''.join(raw[j:j+2]+b'\0\0' for j in range(0,8,2)))) if unit==8 else list(struct.unpack('>4f',raw))
                assert all(math.isfinite(x) for x in vals)
                # Independent exact coordinate re-encoding check, including truncated float words.
                encoded=b''.join(struct.pack('>f',v)[:2] for v in vals) if unit==8 else struct.pack('>4f',*vals)
                assert encoded==raw
                coords.append(vals)
        else:assert co==0
        assert struct.pack('>'+str(count)+'f',*times)==b[o+to:o+to+4*count]
        channels.append(dict(channel_index=i,flags=flags,track_flags=track,source_bone_id=bone,key_count=count,total_time=time,time_offset=to,coordinate_offset=co,coordinate_encoding=enc,times=times,values=coords,track_type_candidate={1:'translation',2:'scale',8:'rotation'}.get(track&0x1f,'control_or_unknown'),time_nondecreasing=all(a<=z for a,z in zip(times,times[1:])),interpretation_evidence='GNTool track flags; FUC runtime interpolation and bone binding require independent verification'))
    return dict(channel_count=n,play_speed=speed,end_time=duration,channels=channels,validation='ALL_CHANNEL_BOUNDS_FINITE_VALUES_EXACT_COORDINATE_ROUNDTRIP')
def run():
    rows=readjson(ROOT/'FPK_EXTRACTED_INDEX.json');out=[];errors=[];cstats=collections.Counter();roundtrips=0
    for r in rows:
        if not r['name'].endswith('.mot'):continue
        b=pathlib.Path(r['physical_path']).read_bytes();flags,count,table,total=struct.unpack_from('>4I',b)
        assert table==16 and total==len(b)
        offsets=list(struct.unpack_from('>'+str(count)+'I',b,table));bounds=sorted(set(x for x in offsets if x))+[len(b)];ends=dict(zip(bounds,bounds[1:]))
        for i,o in enumerate(offsets):
            item=dict(animation_id=f"MOT_{r['sha256'][:12]}_{i:04d}",asset_id='',source_name=r['name'],source_container=r['container'],source_path=r['physical_path'],source_sha256=r['sha256'],motion_table_index=i,offset=o,size=ends[o]-o if o else 0,clip_sha256='',model_id='',character_code=r['name'].split('/')[1] if r['name'].startswith('chr/') else '',character='unknown',clip_name=f'motion_{i:04d}',semantic_role='unknown',frame_count='',fps='',duration='',bone_count='',animated_bones='',loop='',linked_effects='',linked_sound='',linked_model='',working_path='',raw_clip_path='',status='EMPTY_TABLE_SLOT',notes='Original table IDs preserved; no guessed move names')
            if o:
                raw=b[o:ends[o]];h=hashlib.sha256(raw).hexdigest();item['clip_sha256']=h;folder=ROOT/'MotionClips'/h;folder.mkdir(parents=True,exist_ok=True);rawpath=folder/'clip.gnta';rawpath.write_bytes(raw);item['raw_clip_path']=str(rawpath)
                try:
                    j=parse_clip(b,o,ends[o]);j.update(source_sha256=r['sha256'],motion_table_index=i,source_name=r['name'],source_container=r['container'],clip_sha256=h)
                    jp=folder/'channels.json';jsonwrite(jp,j);bones={x['source_bone_id'] for x in j['channels'] if x['values'] and x['source_bone_id']!=65535}
                    item.update(status='CHANNELS_DECODED_ROUNDTRIP_VALIDATED_BINDING_UNVERIFIED',duration=j['end_time'],bone_count=len(bones),animated_bones=';'.join(map(str,sorted(bones))),working_path=str(jp),notes='Channel times and float/high16 coordinates fully decoded and exactly re-encoded. Track role provisional from GNTool; runtime interpolation, source bone IDs and playback unverified. Duration field is source end_time; fps not assumed.')
                    for x in j['channels']:cstats[(x['flags'],x['track_flags'],x['coordinate_encoding'])]+=1;roundtrips+=x['key_count']
                except Exception as e:item.update(status='CLIP_CHANNEL_PARSE_FAILED',notes=str(e));errors.append(dict(animation_id=item['animation_id'],source=r['name'],offset=o,error=str(e)))
            out.append(item)
    csvwrite(ROOT/'ANIMATION_INDEX.csv',out);jsonwrite(ROOT/'ANIMATION_INDEX.json',out);jsonwrite(ROOT/'MOTION_CHANNEL_FAILURES.json',errors)
    summary=dict(mot_files=sum(r['name'].endswith('.mot') for r in rows),table_slots=len(out),nonempty_clips=sum(bool(x['offset']) for x in out),decoded_clips=sum(x['status'].startswith('CHANNELS_DECODED') for x in out),failed_clips=len(errors),channel_count=sum(cstats.values()),keyframe_roundtrips=roundtrips,model_bindings_verified=0,playback_validated=0,track_clusters=[dict(flags=k[0],track=k[1],encoding=k[2],channels=v) for k,v in cstats.items()],algorithm_reference='NicholasMoser/GNTool BoneAnimation.java and Coordinate.java; local bounded and exact value re-encoding validation',status='DECODED_CURVES_BINDING_AND_RUNTIME_UNVERIFIED')
    jsonwrite(ROOT/'MOTION_SUMMARY.json',summary);log('MOTION CHANNEL SUMMARY',summary)
if __name__=='__main__':run()
