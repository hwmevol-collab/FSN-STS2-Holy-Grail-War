from fuc_common import *
import concurrent.futures
ROOT=STAGE_ROOT
VGM=W/'tools/vgmstream-fuc/runtime/vgmstream-cli.exe'
def convert(row):
    h=row['sha256'];folder=ROOT/'Audio';folder.mkdir(exist_ok=True);dest=folder/f'{h}.flac';mark=folder/f'{h}.json'
    isvag=row['source_name'].endswith('.vag')
    if mark.exists():
        previous=readjson(mark)
        if not isvag or previous.get('decoder')=='vgmstream r2117':return previous
    result=dict(sha256=h,status='FAILED',working_path='',codec='',duration='',sample_rate='',channels='')
    try:
        cached=FW/'source_diagnostic/Audio'/f'{h}.json'
        if ROOT!=FW/'source_diagnostic' and cached.exists():
            previous=readjson(cached)
            if previous['status']=='CONVERTED_LOSSLESS_FLAC_DECODE_VERIFIED' and (not isvag or previous.get('decoder')=='vgmstream r2117'):
                source=pathlib.Path(previous['working_path'])
                if not dest.exists():os.link(source,dest)
                previous.update(working_path=str(dest),reused_conversion_from=str(source),reuse_evidence='Identical source audio SHA256 from verified complete Europe ISO')
                jsonwrite(mark,previous);return previous
        source=row['physical_path'];temporary=None;decoder='FFmpeg ATRAC3'
        if isvag:
            decoder='vgmstream r2117';temporary=folder/f'{h}.wav'
            p=subprocess.run([str(VGM),'-m','-I',source],capture_output=True,timeout=60);assert p.returncode==0,p.stderr.decode('utf-8','replace');meta=json.loads(p.stdout)
            raw=pathlib.Path(source).read_bytes();declared=struct.unpack_from('>I',raw,12)[0]
            assert raw[:4]==b'VAGp' and len(raw)==48+declared and declared%16==0
            assert meta['channels']==1 and meta['numberOfSamples']==declared//16*28,'vgmstream output disagrees with bounded mono VAG header'
            p=subprocess.run([str(VGM),'-i','-o',str(temporary),source],capture_output=True,timeout=180);assert p.returncode==0 and temporary.exists(),p.stderr.decode('utf-8','replace')
            result.update(vgmstream_metadata=meta,source_vag_version=struct.unpack_from('>I',raw,4)[0],source_audio_data_offset=48,source_audio_data_bytes=declared)
            source=str(temporary)
        p=subprocess.run([str(FP),'-v','error','-show_format','-show_streams','-of','json',source],capture_output=True,timeout=60)
        assert p.returncode==0,p.stderr.decode('utf-8','replace');info=json.loads(p.stdout);s=next(s for s in info['streams'] if s['codec_type']=='audio')
        if not dest.exists() or isvag:
            p=subprocess.run([str(FF),'-nostdin','-v','error','-xerror','-i',source,'-map','0:a:0','-c:a','flac','-compression_level','5','-y',str(dest)],capture_output=True,timeout=180)
            assert p.returncode==0,p.stderr.decode('utf-8','replace')
        p=subprocess.run([str(FF),'-v','error','-xerror','-i',str(dest),'-f','null','-'],capture_output=True,timeout=180);assert p.returncode==0,p.stderr.decode('utf-8','replace')
        result.update(status='CONVERTED_LOSSLESS_FLAC_DECODE_VERIFIED',working_path=str(dest),working_sha256=sha(dest),codec='adpcm_psx' if isvag else s.get('codec_name'),duration=info.get('format',{}).get('duration',s.get('duration','')),sample_rate=s.get('sample_rate'),channels=s.get('channels'),source_probe=info,decoder=decoder)
        if isvag:
            assert int(result['channels'])==meta['channels'] and abs(float(result['duration'])-meta['numberOfSamples']/meta['sampleRate'])<0.0001
            temporary.unlink()
    except Exception as e:result['error']=str(e)
    jsonwrite(mark,result);return result
def run():
    raw=readjson(ROOT/'FPK_EXTRACTED_INDEX.json');files=readjson(ROOT/'PARTIAL_ISO_FILESYSTEM_INVENTORY.json');audio=[]
    for r in raw:
        if r['name'].endswith('.vag') and r['size']:audio.append(dict(physical_path=r['physical_path'],source_name=r['name'],sha256=r['sha256'],container=r['container'],source_status=r['source_status']))
    for r in files:
        if r['complete_extent'] and r['logical_path'].endswith(('.vag','.at3')):audio.append(dict(physical_path=r['physical_path'],source_name=r['logical_path'],sha256=r['sha256'],container=r.get('container','ISO_PREFIX'),source_status=r.get('source_status','COMPLETE_EXTENT_FROM_UNVERIFIED_ROM_PREFIX')))
    unique={r['sha256']:r for r in audio};done={};log('Available audio',len(audio),'unique',len(unique))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,x in enumerate(pool.map(convert,unique.values())):
            done[x['sha256']]=x
            if i%100==0:log('Audio conversion',i+1,'/',len(unique))
    index=[dict(r,**{k:v for k,v in done[r['sha256']].items() if k not in r and k not in {'source_probe','vgmstream_metadata'}}) for r in audio]
    csvwrite(ROOT/'FUC_AUDIO_INDEX.csv',index);jsonwrite(ROOT/'FUC_AUDIO_INDEX.json',index)
    voice=[dict(voice_asset=r['source_name'],source=r['container'],voice_id=pathlib.Path(r['source_name']).stem,character='unknown',character_code=pathlib.Path(r['source_name']).stem.split('_')[1] if pathlib.Path(r['source_name']).stem.startswith(('sys_','story_')) else pathlib.Path(r['source_name']).stem.split('_')[0],move_action='',duration=r['duration'],evidence='literal filename code only; action names not guessed',status=r['status']) for r in index if r['source_name'].endswith('.vag')]
    csvwrite(ROOT/'FUC_VOICE_INDEX.csv',voice)
    summary=dict(available_logical_audio=len(audio),unique_audio=len(unique),converted_unique_flac=sum(r['status']=='CONVERTED_LOSSLESS_FLAC_DECODE_VERIFIED' for r in done.values()),failed_unique_audio=sum(r['status']=='FAILED' for r in done.values()),missing_loose_vag_extents=sum(not r['complete_extent'] and r['logical_path'].endswith('.vag') for r in files),codecs=dict(collections.Counter(r['codec'] for r in done.values())),status='WORK_ONLY_PARTIAL_ROM_AUDIO_COVERAGE')
    jsonwrite(ROOT/'AUDIO_SUMMARY.json',summary);log('AUDIO SUMMARY',summary)
if __name__=='__main__':run()
