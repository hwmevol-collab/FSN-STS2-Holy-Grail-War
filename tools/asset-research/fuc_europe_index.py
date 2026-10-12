"""Deterministic appendable Europe logical assets; Japan recovery is never assigned IDs."""
from fuc_common import *
from PIL import Image
import concurrent.futures
ROOT=STAGE_ROOT
EU=L/'FateUnlimitedCodesPortable_Europe'
EXTRA=['asset_kind','parent_asset_id','entry_index','embedded_offset','model_format','model_id','bone_count','weighted_skin_bone_count','animation_count','animation_id','mesh_count','material_count','texture_count','character_code','character_evidence','texture_role','stage','source_evidence','metadata_path']
def link(source,dest):
    source=pathlib.Path(source);dest=pathlib.Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():os.link(source,dest)
    assert source.stat().st_size==dest.stat().st_size
    return str(dest)
def run():
    assert SOURCE_VERSION=='FateUnlimitedCodesPortable_Europe' and readjson(ROOT/'SOURCE_IDENTITY.json')['source_complete']
    marker=EU/'Metadata/INDEX_COMPLETE.json'
    if marker.exists():log('EUROPE index already generated',readjson(marker));return
    with (BACK/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:legacy=next(csv.reader(f))
    assets=[];rawpaths={};workpaths={};primary={};models=readjson(ROOT/'MODEL_INDEX.json');textures=readjson(ROOT/'TEXTURE_INDEX.json');anims=readjson(ROOT/'ANIMATION_INDEX.json');bank=readjson(ROOT/'SOUND_BANK_INDEX.json');audio=readjson(ROOT/'FUC_AUDIO_INDEX.json');videos=readjson(ROOT/'VIDEO_INDEX.json');model_lookup={(m['source_container'],m['logical_path']):m for m in models};audio_lookup={a['sha256']:a for a in audio};video_lookup={v['sha256']:v for v in videos}
    def working(p):
        if not p:return ''
        if p not in workpaths:workpaths[p]=link(p,EU/'Converted'/pathlib.Path(p).relative_to(ROOT))
        return workpaths[p]
    def make(key,name,container,path,kind,h='',size=None,detected='UNKNOWN',category='Unknown',converted='',status='unresolved_preserved',**extra):
        p=pathlib.Path(path);r={k:'' for k in legacy+EXTRA};r.update(asset_id='',source_version=SOURCE_VERSION,source_container=container,source_logical_path=name,extracted_path=str(p),converted_path=converted,filename=name.split('/')[-1],extension=p.suffix.lower(),detected_format=detected,category=category,route='Unknown',locale='Europe',character='unknown',size=p.stat().st_size if size is None else size,sha256=h or sha(p),conversion_status=status,asset_kind=kind,_key=key,source_evidence='Complete NPEH00007 1.01 ISO; SHA256 and filesystem bounds independently verified',**extra)
        if converted:r['working_sha256']=sha(converted)
        assets.append(r);return r
    def process(r,name,container,path,key,kind):
        ext=pathlib.Path(name).suffix.lower();wp='';meta={};detected=r.get('detected_format','UNKNOWN');cat='Unknown';status='unresolved_preserved'
        if ext=='.gmo':
            m=model_lookup[(container,name)];wp=working(m['working_path']);detected='GMO';cat='Stages' if name.startswith(('stg/','stage/')) else 'Models';status='converted_glb_structure_validated';mp=EU/'Metadata/Models'/r['sha256']/'MODEL_METADATA.json';meta.update(model_format='GMO / GLB 2.0',model_id='GMO_'+r['sha256'][:16],bone_count=m['bone_count'],weighted_skin_bone_count=m.get('weighted_skin_bone_count',''),animation_count=0,mesh_count=m['mesh_count'],material_count=m['material_count'],texture_count=m['texture_count'],metadata_path=str(mp))
        elif r['sha256'] in audio_lookup:
            a=audio_lookup[r['sha256']];wp=working(a['working_path']);detected='VAG' if ext=='.vag' else 'ATRAC3';cat='Audio';status='converted_lossless_flac_verified';meta.update({k:a.get(k,'') for k in ['duration','sample_rate','channels','codec']})
        elif r['sha256'] in video_lookup:
            v=video_lookup[r['sha256']];wp=working(v['working_path']);detected='PMF';cat='Video';status='converted_mp4_full_decode_verified';meta.update({k:v.get(k,'') for k in ['duration','width','height','fps','codec','audio_tracks']})
        elif ext=='.png':
            wp=str(path);detected='PNG';cat='Image';status='native_image_verified'
            with Image.open(path) as im:im.load();meta.update(width=im.width,height=im.height,alpha='A' in im.getbands())
        elif ext=='.fpk':detected='FPK';cat='Containers';status='all_entries_extracted_validated'
        elif ext=='.mot':detected='8ing_MOT';cat='Animations';status='all_nonempty_clips_channels_decoded_binding_unverified'
        elif ext=='.ttd':detected='TTD_with_TIM2';cat='TextureContainers';status='all_embedded_tim2_converted'
        elif ext in {'.phd','.pbd'}:detected='Sony_PPHD' if ext=='.phd' else 'Sony_PPHD_ADPCM_Body';cat='AudioContainers';status='pphd_streams_decoded'
        elif ext in {'.bin','.prx','.sfo'}:cat='System';status='preserved_indexed'
        elif ext in {'.txt','.lst'}:cat='Text';detected='TEXT_CANDIDATE';status='preserved_string_indexed'
        elif name.startswith('eft/'):cat='Effects'
        elif name.startswith(('stg/','stage/')):cat='Stages'
        if name.startswith('chr/'):meta['character_code']=name.split('/')[1];meta['character_evidence']='Explicit internal chr/<code>/ path; character name unconfirmed'
        return make(key,name,container,path,kind,h=r['sha256'],size=r['size'],detected=detected,category=cat,converted=wp,status=status,**meta)
    loose=readjson(ROOT/'SOURCE_INVENTORY.json');payloads=readjson(ROOT/'FPK_EXTRACTED_INDEX.json')
    for r in loose:
        name=r['logical_path'];dest=EU/'RawExtracted'/('Executable' if name.startswith('PSP_GAME/SYSDIR/') else 'Loose')/name;path=link(r['physical_path'],dest);rawpaths[r['physical_path']]=path
        process(r,name,'ISO9660:NPEH00007',path,'ISO/'+name,'iso_file')
    for r in payloads:
        name=r['name'];dest=EU/'RawExtracted/Containers'/r['container']/r['safe_name'];path=link(r['physical_path'],dest);rawpaths[r['physical_path']]=path
        p=process(r,name,r['container'],path,'FPK/'+r['container']+'/'+f"{r['entry_index']:05d}"+'/'+name,'fpk_payload');p.update(entry_index=r['entry_index'],notes=f"FPK offset={r['offset']}; compressed_size={r['compressed_size']}; uncompressed_size={r['uncompressed_size']}; original entry name retained")
        primary[(r['container'],name)]=p
    for t in textures:
        path=link(t['raw_path'],EU/'RawExtracted/TextureObjects'/(t['texture_sha256']+'.tm2'));rawpaths[t['raw_path']]=path;wp=working(t['working_path']);parent=primary[(t['parent_container'],t['parent_name'])]
        a=make('Texture/'+parent['_key']+'/'+f"{t['embedded_index']:04d}"+f"/{t['picture_index']:03d}",t['parent_name']+f"#TIM2/{t['embedded_index']:04d}/{t['picture_index']:03d}",t['parent_container'],path,'embedded_tim2_picture',h=t['texture_sha256'],detected='TIM2',category='Textures',converted=wp,status='converted_png_verified',width=t['width'],height=t['height'],alpha=t.get('alpha',''),embedded_offset=t['embedded_offset'],texture_role='unknown',notes='Original TIM2 bytes and palette/mip/GS headers retained; metadata contains parent offset and dimensions');a['_parent_key']=parent['_key']
    # Embedded GMO textures are logical image views whose original bytes stay in the complete GMO.
    for m in models:
        parent=primary[(m['source_container'],m['logical_path'])];folder=pathlib.Path(m['working_path']).parent
        for image in sorted(folder.glob('*.png')):
            wp=working(str(image));name=m['logical_path']+'#texture/'+image.name
            with Image.open(image) as im:w,h=im.size;alpha='A' in im.getbands()
            a=make('ModelTexture/'+parent['_key']+'/'+image.name,name,m['source_container'],parent['extracted_path'],'embedded_gmo_texture_view',h=parent['sha256'],detected='GMO_Embedded_Texture',category='Textures',converted=wp,status='gmo_texture_png_derived',width=w,height=h,alpha=alpha,texture_role='model_embedded',model_id=parent['model_id'],notes='Preservation path is the complete original GMO containing this texture, not a claimed standalone original PNG. Noesis texture view is PNG Working Copy.');a['_parent_key']=parent['_key']
    for a in anims:
        if not a['offset']:continue
        assert a['status'].startswith('CHANNELS_DECODED')
        path=link(a['raw_clip_path'],EU/'RawExtracted/MotionObjects'/(a['clip_sha256']+'.gnta'));rawpaths[a['raw_clip_path']]=path;wp=working(a['working_path']);parent=primary[(a['source_container'],a['source_name'])]
        row=make('Motion/'+parent['_key']+'/'+f"{a['motion_table_index']:05d}",a['source_name']+f"#clip/{a['motion_table_index']:04d}",a['source_container'],path,'mot_clip',h=a['clip_sha256'],detected='8ing_MOT_Clip',category='Animations',converted=wp,status='channels_roundtrip_verified_binding_unverified',animation_id=a['animation_id'],duration=a['duration'],bone_count=a['bone_count'],embedded_offset=a['offset'],character_code=a['character_code'],notes=a['notes']);row['_parent_key']=parent['_key']
    for a in bank:
        dst=EU/'RawExtracted/AudioBankObjects'/(a['payload_sha256']+'.adpcm');dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():
            with open(a['body_path'],'rb') as f:f.seek(a['offset']);data=f.read(a['stream_size'])
            assert hashlib.sha256(data).hexdigest()==a['payload_sha256'];dst.write_bytes(data)
        parent=primary[(a['source_container'],str(pathlib.PurePosixPath(a['header_name']).with_suffix('.pbd')))];wp=working(a['working_path'])
        row=make('SoundBank/'+a['source_container']+'/'+a['header_name']+'/'+f"{a['subsong']:05d}",a['header_name']+f"#subsong/{a['subsong']:04d}",a['source_container'],dst,'pphd_subsong',h=a['payload_sha256'],detected='PSX_ADPCM',category='Audio',converted=wp,status='lossless_flac_pphd_decoded_verified',embedded_offset=a['offset'],duration=a['duration'],sample_rate=a['sample_rate'],channels=a['channels'],codec='adpcm_psx',entry_index=a['subsong'],notes='Headerless original ADPCM stream sliced at verified PPVA offset; sample rate and loop flags retained in SOUND_BANK_INDEX');row['_parent_key']=parent['_key']
    # Keep an independent complete ISO preservation copy; never hardlink user input.
    identity=readjson(ROOT/'SOURCE_IDENTITY.json');src=pathlib.Path(identity.get('source_path',identity.get('path','')))
    if not src.is_file():src=pathlib.Path('E:/BaiduNetdiskDownload/FSN/素材/Fate-Unlimited Codes (Europe) (PSP) (PSN)/Fate-Unlimited Codes (Europe) (PSP) (PSN).iso')
    iso=EU/'RawExtracted/ISO/FateUnlimitedCodesPortable_Europe_NPEH00007_v1.01.iso';iso.parent.mkdir(parents=True,exist_ok=True)
    if not iso.exists():shutil.copy2(src,iso)
    assert sha(iso)==identity['sha256']
    ep=ROOT/'Executable/EBOOT_DECRYPTED.bin';dp=link(ep,EU/'Converted/Executable/EBOOT_DECRYPTED.bin');workpaths[str(ep)]=dp
    assets.sort(key=lambda r:r['_key']);ids={r['_key']:f'FSN{246605+i:06d}' for i,r in enumerate(assets,1)}
    for r in assets:r['asset_id']=ids[r['_key']];r['parent_asset_id']=ids.get(r.pop('_parent_key',''),'')
    def thumbnail(r):
        if r['category'] not in {'Image','Textures'} or not r['converted_path']:return
        try:
            h=r['working_sha256'];target=L/'Gallery/thumbnails'/('fuc_eu_'+h+'.png')
            if not target.exists():
                with Image.open(r['converted_path']) as im:im=im.convert('RGBA');im.thumbnail((240,180));im.save(target)
            r['thumbnail_path']=str(target)
        except Exception as e:r['error']=str(e)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(thumbnail,assets))
    # Source metadata is copied with only explicit physical-path rewrites; Japan files stay intact.
    replacements=dict(rawpaths,**workpaths)
    def rewrite(v):
        if isinstance(v,str):return replacements.get(v,v)
        if isinstance(v,list):return [rewrite(x) for x in v]
        if isinstance(v,dict):return {k:rewrite(x) for k,x in v.items()}
        return v
    md=EU/'Metadata';md.mkdir(parents=True,exist_ok=True)
    for p in ROOT.iterdir():
        if p.is_file() and p.suffix in {'.json','.csv'}:
            if p.suffix=='.json':jsonwrite(md/p.name,rewrite(readjson(p)))
            else:csvwrite(md/p.name,[rewrite(r) for r in readrows(p)],next(csv.reader(p.open(encoding='utf-8-sig'))))
    for h in {m['source_sha256'] for m in models}:jsonwrite(md/'Models'/h/'MODEL_METADATA.json',rewrite(readjson(ROOT/'Models'/h/'MODEL_METADATA.json')))
    bykey={(r['source_container'],r['source_logical_path']):r for r in assets if r['asset_kind']=='fpk_payload'}
    # Add formal IDs to per-class indexes; table placeholder rows remain with empty clip asset IDs.
    for filename,rs,pair in [('MODEL_INDEX',models,('source_container','logical_path')),('TEXTURE_INDEX',textures,('parent_container','parent_name')),('ANIMATION_INDEX',anims,('source_container','source_name'))]:
        for row in rs:
            parent=bykey.get((row[pair[0]],row[pair[1]]));row['parent_asset_id']=parent['asset_id'] if parent else ''
            if filename=='MODEL_INDEX':row['asset_id']=row['parent_asset_id']
            elif filename=='ANIMATION_INDEX':row['asset_id']=next((r['asset_id'] for r in assets if r['asset_kind']=='mot_clip' and r['animation_id']==row['animation_id']),'')
            elif filename=='TEXTURE_INDEX':row['asset_id']=ids['Texture/'+parent['_key']+'/'+f"{row['embedded_index']:04d}/{row['picture_index']:03d}"]
        jsonwrite(md/(filename+'.json'),rewrite(rs));csvwrite(md/(filename+'.csv'),[rewrite(r) for r in rs])
    voices=[]
    for r in assets:
        if r['category']=='Audio' and ('voice' in r['source_logical_path'].lower() or r['character_code']):voices.append(dict(voice_asset=r['asset_id'],character='unknown',character_code=r['character_code'],voice_id=r['filename'],move_action='',duration=r['duration'],source=r['source_logical_path'],evidence='Explicit voice path; action and speaker not guessed',working_path=r['converted_path']))
    csvwrite(md/'FUC_VOICE_INDEX.csv',voices,['voice_asset','character','character_code','voice_id','move_action','duration','source','evidence','working_path'])
    csvwrite(md/'FUC_AUDIO_INDEX.csv',[{k:r[k] for k in ['asset_id','asset_kind','source_container','source_logical_path','extracted_path','converted_path','sha256','working_sha256','codec','duration','sample_rate','channels','conversion_status']} for r in assets if r['category']=='Audio'])
    jsonwrite(md/'SOURCE_IDENTITY.json',dict(identity,preservation_iso_path=str(iso),source_version=SOURCE_VERSION))
    # Preserve stable logical keys for future re-runs and a separately named full Japan source.
    writejsonl(md/'ASSETS.jsonl',assets);csvwrite(md/'ASSETS.csv',assets,legacy+EXTRA+['_key']);csvwrite(md/'ASSET_ID_MAP.csv',[dict(logical_key=r['_key'],asset_id=r['asset_id'],source_version=SOURCE_VERSION) for r in assets])
    summary=dict(source_version=SOURCE_VERSION,assets=len(assets),first_asset_id=assets[0]['asset_id'],last_asset_id=assets[-1]['asset_id'],kinds=dict(collections.Counter(r['asset_kind'] for r in assets)),categories=dict(collections.Counter(r['category'] for r in assets)),Japan_recovery_catalog_rows=0,unique_new_thumbnails=len({r['thumbnail_path'] for r in assets if r['thumbnail_path']}),complete_iso_copy_sha256=sha(iso),status='INDEX_READY_FOR_APPEND_ONLY_INTEGRATION')
    jsonwrite(marker,summary);log('EUROPE INDEX',summary)
if __name__=='__main__':run()
