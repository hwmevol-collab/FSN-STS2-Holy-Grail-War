from fuc_common import *
import concurrent.futures,wave
ROOT=STAGE_ROOT
VGM=W/'tools/vgmstream-fuc/runtime/vgmstream-cli.exe'
def convert(r):
    folder=ROOT/'AudioBank';folder.mkdir(exist_ok=True);key=r['audio_key'];wav=folder/f'{key}.wav';flac=folder/f'{key}.flac';marker=folder/f'{key}.json'
    if marker.exists():return readjson(marker)
    result=dict(audio_key=key,payload_sha256=r['payload_sha256'],status='FAILED',working_path='')
    try:
        cached=FW/'source_diagnostic/AudioBank'/f'{key}.json'
        if ROOT!=FW/'source_diagnostic' and cached.exists():
            previous=readjson(cached)
            if previous['status']=='DECODED_PPHD_PSX_FLAC_VERIFIED':
                source=pathlib.Path(previous['working_path'])
                if not flac.exists():os.link(source,flac)
                previous.update(working_path=str(flac),reused_conversion_from=str(source),reuse_evidence='Identical ADPCM payload SHA256 and sample rate from complete Europe ISO')
                jsonwrite(marker,previous);return previous
        p=subprocess.run([str(VGM),'-m','-I','-s',str(r['subsong']),r['header_path']],capture_output=True,timeout=60);assert p.returncode==0;meta=json.loads(p.stdout)
        assert meta['sampleRate']==r['sample_rate'] and meta['channels']==1 and meta['numberOfSamples']==r['stream_size']//16*28
        p=subprocess.run([str(VGM),'-i','-s',str(r['subsong']),'-o',str(wav),r['header_path']],capture_output=True,timeout=180);assert p.returncode==0 and wav.exists(),p.stderr.decode('utf-8','replace')
        with wave.open(str(wav)) as w:assert w.getnframes()==meta['numberOfSamples'] and w.getnchannels()==1
        p=subprocess.run([str(FF),'-nostdin','-v','error','-xerror','-i',str(wav),'-c:a','flac','-compression_level','5','-y',str(flac)],capture_output=True,timeout=180);assert p.returncode==0
        p=subprocess.run([str(FF),'-v','error','-xerror','-i',str(flac),'-f','null','-'],capture_output=True,timeout=180);assert p.returncode==0
        wav.unlink();result.update(status='DECODED_PPHD_PSX_FLAC_VERIFIED',working_path=str(flac),working_sha256=sha(flac),duration=meta['numberOfSamples']/meta['sampleRate'],channels=1,sample_rate=meta['sampleRate'],sample_count=meta['numberOfSamples'],decoder='vgmstream r2117',looping_info=meta.get('loopingInfo'))
    except Exception as e:result['error']=str(e)
    jsonwrite(marker,result);return result
def run():
    rows=readjson(ROOT/'FPK_EXTRACTED_INDEX.json');headers=[r for r in rows if r['name'].endswith('.phd')];streams=[];banks=[];empty=[]
    for r in headers:
        p=pathlib.Path(r['physical_path']);b=p.read_bytes();body=p.with_suffix('.pbd');assert b[:4]==b'PPHD' and body.exists()
        ppva=struct.unpack_from('<I',b,24)[0];assert b[ppva:ppva+4]==b'PPVA';n=struct.unpack_from('<i',b,ppva+20)[0];maximum=ppva+32+16*n
        if maximum+4<=len(b) and struct.unpack_from('<i',b,maximum)[0]>0:n+=1
        pbd=body.read_bytes();assert n>=0 and ppva+32+16*n<=len(b)
        for i in range(n):
            offset,rate,size,flags=struct.unpack_from('<4I',b,ppva+32+16*i)
            if offset==rate==size==flags==0xffffffff:
                empty.append(dict(source_container=r['container'],header_name=r['name'],subsong=i+1,status='EMPTY_PPVA_SLOT_ALL_FFFFFFFF'));continue
            assert offset+size<=len(pbd) and size%16==0 and flags==0xffffffff
            payloadhash=hashlib.sha256(pbd[offset:offset+size]).hexdigest()
            streams.append(dict(audio_key=payloadhash+'_'+str(rate),source_container=r['container'],header_name=r['name'],header_path=str(p),body_path=str(body),header_sha256=r['sha256'],body_sha256=sha(body),subsong=i+1,offset=offset,stream_size=size,sample_rate=rate,flags=f'{flags:08x}',payload_sha256=payloadhash,semantic_role='unknown',source_status=r['source_status'],evidence='Sony PPHD/PPVA table independently bounded; vgmstream r2117 confirms metadata and decodes paired PBD'))
        banks.append(dict(header_name=r['name'],source_container=r['container'],header_path=str(p),body_path=str(body),subsong_count=n,status='TABLE_VALIDATED'))
    unique={r['audio_key']:r for r in streams};done={};log('PPHD banks',len(banks),'streams',len(streams),'unique',len(unique))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,x in enumerate(pool.map(convert,unique.values())):
            done[x['audio_key']]=x
            if i%100==0:log('SE bank conversion',i+1,'/',len(unique))
    index=[dict(r,**{k:v for k,v in done[r['audio_key']].items() if k not in r}) for r in streams];csvwrite(ROOT/'SOUND_BANK_INDEX.csv',index);jsonwrite(ROOT/'SOUND_BANK_INDEX.json',index);jsonwrite(ROOT/'SOUND_BANK_HEADERS.json',banks);csvwrite(ROOT/'SOUND_BANK_EMPTY_SLOTS.csv',empty)
    summary=dict(pphd_banks=len(banks),empty_slots=len(empty),logical_bank_streams=len(streams),unique_bank_streams=len(unique),converted_unique_flac=sum(r['status']=='DECODED_PPHD_PSX_FLAC_VERIFIED' for r in done.values()),failed_unique_streams=sum(r['status']=='FAILED' for r in done.values()),pef_sequence_programs='PPHD/PBD audio recovered; PPEF program/timing bindings remain unknown')
    jsonwrite(ROOT/'SOUND_BANK_SUMMARY.json',summary);log('SOUND BANK SUMMARY',summary)
if __name__=='__main__':run()
