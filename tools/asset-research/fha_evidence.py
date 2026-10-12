from fha_prepare import *
import subprocess,importlib.metadata
def run():
    logs=json.loads((FHA/'Metadata/EXTRACTION_LOG.json').read_text('utf-8'))
    for item in logs:
        if item['kind']=='Molebox/NewDES' and 'ExtractMolebox' in item.get('command',''):
            item['initial_workflow_label']=item['command'];item['command']='python fha_molebox.py --extract '+pathlib.Path(item['source']).name;item['command_note']='Reproducible single-container invocation; initial field was an obsolete workflow label'
    jsonwrite(FHA/'Metadata/EXTRACTION_LOG.json',logs);csvwrite(FHA/'Metadata/EXTRACTION_LOG.csv',logs,['source','source_container','kind','tool','plugin','command','expected_entries','verified_entries','files_extracted','blocks_verified','status','errors'])
    result=json.loads((FW/'BROWSER_OBSERVED_RESULTS.json').read_text('utf-8'));result['recorded_at']=now();result['index_sha256']=sha(L/'Gallery/index.html');result['catalog_js_sha256']=sha(L/'Gallery/catalog.js')
    log=(FW/'gallery-http.stderr.log').read_text('utf-8',errors='replace');bad=[s for s in log.splitlines() if re.search(r'" (?:404|500|403) ',s)]
    result['http_error_requests']=bad;result['http_missing_asset_requests']=len([s for s in bad if 'favicon.ico' not in s]);jsonwrite(L/'Reports/FHA_GALLERY_VALIDATION.json',result)
    oldpath=L/'Remastered/RawExtracted/ROOT_FPD/boot.dat/root/logomv_h.ogv'
    p=subprocess.run(['D:/DDplay/ffmpeg/ffmpeg.exe','-v','error','-i',str(oldpath),'-f','null','-'],capture_output=True,text=True)
    decode=dict(path=str(oldpath),decode_exit_code=p.returncode,stderr=p.stderr,sha256=sha(oldpath),codec='Theora',method='Full independent FFmpeg decode of unchanged existing video; rendered IAB compatibility remains separate')
    jsonwrite(L/'Reports/FHA_OLD_VIDEO_DECODE.json',decode);assert p.returncode==0
    sources=[dict(tool='arc_unpacker',repository='https://github.com/vn-tools/arc_unpacker',commit='ff3b9d9b071cc85ea6c50081aa4a7a88cab4d27a',version='0.11',algorithm='XP3 indexing/zlib, FHA CXDEC plugin, TLG decoding',binary=str(W/'tools/arc_unpacker/arc_unpacker.exe'),sha256=sha(W/'tools/arc_unpacker/arc_unpacker.exe'),limitations='Four XP3 Adler32 exceptions retained; matching TPM required'),dict(tool='Molebox source',repository='https://github.com/sudachen/Molebox',commit='f526e8a41bcb7884231154e8e5ccb74c789f188d',algorithm='VFS catalog layout, block encryption and LZSS',limitations='This actual historical build uses NewDES; newer upstream encryption constants were not blindly applied'),dict(tool='xternal source',repository='https://github.com/sudachen/xternal',commit='1cfcaacbdeca03cacc8f8d6ed8a51c8942ca277d',algorithm='Audited NewDES and CRC16 implementation',limitations='Hidden filename hashes retained for outer Molebox entries; inner XP3 provides logical resource names'),dict(tool='GARbro source reference',repository='https://github.com/morkt/GARbro',commit='b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0',algorithm='KiriKiri encrypted-text format reference',limitations='Source reference only; no unknown closed unpacker used')]
    versions={n:importlib.metadata.version(n) for n in ['Pillow','numpy','ImageHash','mutagen','pycryptodome','unicorn','capstone','pefile']}
    manifest=dict(recorded_at=now(),python=sys.version,python_executable=sys.executable,ffmpeg=subprocess.run(['D:/DDplay/ffmpeg/ffmpeg.exe','-version'],capture_output=True,text=True).stdout.splitlines()[0],sources=sources,packages=versions,entry_point=str(W/'scripts/FHA_ASSETS.ps1'),source_policy='Read-only source; all intermediate writes in WORK or added library areas',offline_reference_filter='Unicorn executes only recovered TPM key-generator machine code in isolated memory, with no native DLL/game execution',scripts={p.name:sha(p) for p in (W/'scripts').glob('fha_*.py')})
    manifest['scripts']['FHA_ASSETS.ps1']=sha(W/'scripts/FHA_ASSETS.ps1');manifest['scripts']['FHA_BROWSER_ACCEPTANCE.js']=sha(W/'scripts/FHA_BROWSER_ACCEPTANCE.js')
    jsonwrite(FHA/'Metadata/TOOLS_MANIFEST.json',manifest);jsonwrite(L/'Reports/FHA_TOOLS_MANIFEST.json',manifest)
    print('FHA EVIDENCE SAVED; Gallery',result['status'],'HTTP asset errors',result['http_missing_asset_requests'],flush=True)
if __name__=='__main__':run()
