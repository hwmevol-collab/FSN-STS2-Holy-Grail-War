"""Final-freeze documentation only. No extractor, exporter or runtime capture invoked.

prepare writes new sidecars and usage files. finalize requires every audit PASS,
then writes the final manifest and writes the freeze marker last.
"""
from fuc_final_audit import *
import ast,html,shutil,zipfile,urllib.parse,importlib.metadata,platform,re,sys
OUT=pathlib.Path('C:/Users/Murasame/Documents/Codex/2026-10-06/files-pasted-by-the-user-fate-2/outputs')
SM=EU/'Metadata/SemanticMapping';AV=EU/'Metadata/AnimationValidation'
FSTATUS='FUC_FINAL_FREEZE_AND_AUDIT_PASS';CSTATUS='FUC_RESEARCH_PHASE_COMPLETE_FOR_MOD_DEVELOPMENT'
CHECKS=['SOURCE_AUDIT','CATALOG_AUDIT','FUC_FINAL_PRESERVATION_AUDIT','WORKING_COPY_AUDIT','FUC_FINAL_MODEL_AUDIT','GOLDEN_REGRESSION','SEMANTIC_AUDIT','GALLERY_FINAL_AUDIT','GLOBAL_PROTECTED_PATH_AUDIT','FINAL_STABILITY_GATE']
def csvwrite(p,rr):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(rr[0]));wr.writeheader();wr.writerows(rr)
def textwrite(p,t):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,'utf-8')
def stats(p):
    count=size=0;skipped=[]
    if p.is_file():return dict(path=str(p),files=1,logical_bytes=p.stat().st_size)
    for root,dirs,files in os.walk(p,followlinks=False):
        for d in dirs[:]:
            q=pathlib.Path(root)/d
            if q.is_symlink() or (hasattr(q,'is_junction') and q.is_junction()):dirs.remove(d);skipped.append(str(q))
        for n in files:
            q=pathlib.Path(root)/n
            if q.is_symlink():skipped.append(str(q));continue
            count+=1;size+=q.stat().st_size
    return dict(path=str(p),files=count,logical_bytes=size,skipped_links=skipped)
def link(p):
    return urllib.parse.quote(os.path.relpath(p,L/'Gallery').replace('\\','/'),safe='/')
def known_unknown():
    # Counts have explicit units. A captured subset never means all files validated.
    specifications=[
      ('ISO',2738,'2738 extracted files','read-only source identity rechecked','DISC_ID NPEH00007 / v1.01','0 missing files','NON_BLOCKING','Use preserved files; do not re-extract','ISO files'),
      ('FPK',542,'542 archives / 6558 payloads','historical independent PRS verification retained','path and payload identities','payload semantics vary','ON_DEMAND','Select indexed payload by path; no re-extraction','archives'),
      ('Models',842,'341 unique GMO → 341 static GLB','3 character skeletons; separate Replay body/weapon/effect subset','source-code and asset ID mapping','full costume/variant semantics; exact PSP rendering','NON_BLOCKING','Use static GLB; consult source path for variants','logical GMO'),
      ('Skeleton',4059,'4059 transform nodes / 2642 weighted joints','3 skeletons; 45 Golden poses / 2535 node comparisons','ID remap confirmed on sir/rin/lan','remaining skeleton remaps; provisional bN names','ON_DEMAND','Validate a chosen new model before motion export','source transform nodes'),
      ('Textures',6290,'2371 unique PNG','representative browser PNG smoke','source TIM2/path mapping','exact PSP palette/shader/material reconstruction','NON_BLOCKING','Use PNG and static GLB textures; adapt to MOD renderer','logical textures'),
      ('MOT',3676,'3676 clips / 54 MOT; 198831 channels; 2044587 values','9 single-clip Golden animations; lan clip145 Replay separate','3 runtime state bank/clip anchors; only 3 UI name bindings','3667 clips lack single-clip runtime validation','ON_DEMAND','Choose a needed clip and validate only that subset','nonempty clips'),
      ('FAN',1271,'raw preserved; loader/consumer and layout subset decoded','shared FAN/BPO sir/rin/lan; generalization 22 samples','pose consumer links for captured states','independent clock and uncaptured programs','ON_DEMAND','Use frozen Replay / single-clip animations; investigate only selected FAN','raw resources'),
      ('AMO',154,'raw preserved; structural inventory','no confirmed live AMO interpolation','none asserted','runtime interpolation and consumers','ON_DEMAND','Retain raw bytes; research only if a required asset depends on AMO','raw resources'),
      ('SEQ',388,'raw preserved; Lancer effect program subset decoded','Lancer 1000.seq → 1002.gmo; captured birth/update/end','one same-Episode effect relation','remaining SEQ programs and triggers','ON_DEMAND','Use captured effect evidence; do not generalize all SEQ','raw resources'),
      ('Effects',2056,'indexed raw and available working models/textures/audio','one Lancer effect program / same-Episode Replay','one confirmed move→effect relation','remaining ownership/timing and render behavior','ON_DEMAND','Filter EFFECT_INDEX and graph; verify selected effect only','effect resource rows'),
      ('BAM',469,'raw preservation / inventory','none claimed','unknown','format and runtime semantics','ON_DEMAND','Keep raw; open a separate targeted task if needed','raw resources'),
      ('TUV',366,'raw preservation / inventory','none claimed','unknown','format and runtime semantics','ON_DEMAND','Keep raw; open a separate targeted task if needed','raw resources'),
      ('MIL',138,'raw preservation / inventory','none claimed','unknown','format and runtime semantics','ON_DEMAND','Keep raw; open a separate targeted task if needed','raw resources'),
      ('PAR',107,'raw preservation / inventory','none claimed','unknown','format and runtime semantics','ON_DEMAND','Keep raw; open a separate targeted task if needed','raw resources'),
      ('Audio',5537,'3576 VAG/ATRAC logical + 1961 bank-stream logical; 3740 unique FLAC across the two converters','FSN260985 request→bank/program→SAS; representative browser FLAC','one confirmed move→sound relation','remaining dialogue/move meaning; pool variants','ON_DEMAND','Use audio indexes; do not infer character speech from simultaneous playback','logical audio rows'),
      ('PPHD/PBD',43,'43 banks / 1961 logical streams / 1623 unique FLAC; 17 empty slots','observed 0x232D → FSN260985','one bank/program/payload causal anchor','PEF bindings generally unknown; native SAS sample clock','NON_BLOCKING','Use decoded FLAC; retain bank and program references','banks'),
      ('Video',5,'5 PMF → 5 MP4','representative browser MP4 playback','source path mapping','no additional video semantic claim','NON_BLOCKING','Use MP4 for MOD/reference','PMF files'),
      ('Character',20,'20 ELF internal identities','3 runtime UI characters: lan/sir/rin','3 runtime + 17 explicit string-reference identities','full playable roster is not established by this table alone','ON_DEMAND','Distinguish internal identity from playable confirmation','internal identities'),
      ('Command',1231,'178 normal rows + 783 conditional programs + sidecar UI/runtime rows','8 input→state pairs; 11 accepted selector samples / 2 rejected','ROM table predicates and selected runtime results','remaining final-state variants and histories','ON_DEMAND','Keep raw predicates; verify one final state through consumer return','relational command rows'),
      ('Move',611,'352 ROM state subjects + 259 unbound UI subjects','8 state results; only 3 actual returned bank/clip anchors','3 bound UI name entries; lan145 M ATTACK has no separate move name','most state→resource and UI→state links','ON_DEMAND','Use source/status fields; never rename an unbound clip','sidecar subjects'),
      ('UI Move Names',262,'262 UI entries','3 final-state name anchors','3 bound / 259 explicitly unbound','259 state bindings; supplementary unknown glyphs','ON_DEMAND','Keep as semantic_backlog; no command/order/name inference','UI entries'),
      ('Stages',96,'96 stage index rows','no full stage runtime reconstruction claimed','path/code inventory','stage semantics, animation and rendering subset','ON_DEMAND','Use indexed static assets; verify a chosen stage if needed','stage resource rows'),
      ('Fonts',5,'5 font index resources; Move UI glyph subset recovered','Move List glyph consumer evidence retained','262 entries plus supplementary text references','36 distinct supplementary glyph IDs not decoded','ON_DEMAND','Retain explicit glyph tokens; use recovered text only in verified scope','font index resources'),
      ('Unknown formats',3102,'historical format inventory retained','later FAN/SEQ/etc subsets documented separately','no blanket semantic mapping','inventory overlaps later-researched subsets; not 3102 new unresolved assets','ON_DEMAND','Query exact raw path and current sidecar; do not restart broad reverse engineering','historical inventory rows'),
      ('Battle Blend',1,'runtime-authoritative final pose baked for one Episode','83-frame Lancer145 Replay','single captured Episode only','universal blend formula','NON_BLOCKING','Use raw single-clip Golden or captured final-pose Replay','frozen Episode'),
      ('PSP Materials',341,'standard GLB materials and embedded textures','portable viewer checks only','no claim of exact PSP shading','palette/shader/native material equivalence','NON_BLOCKING','Adapt materials to the target renderer','unique static models'),
      ('SAS Clock',1,'request/start causal chain and source FLAC retained','Replay audio start event 174 at native frame6','FSN260985 confirmed','exact native sample clock and sample-perfect mixing','NON_BLOCKING','Use event-aligned playback; do not claim sample-accurate PSP emulation','confirmed sound anchor'),
    ]
    rr=[dict(subsystem=s,total=t,decoded=d,runtime_validated=rv,semantic_mapped=sm,unknown=u,development_impact=di,recommended_action=a,count_unit=unit,evidence_scope='Frozen historical indexes and current final audit; no new runtime capture') for s,t,d,rv,sm,u,di,a,unit in specifications]
    csvwrite(MD/'FUC_FINAL_KNOWN_UNKNOWN_MATRIX.csv',rr);return rr
def disk_inventory():
    roots=[]
    for base in [EU,W/'fuc']:
        for p in base.iterdir():
            if p.is_dir():roots.append(stats(p))
    euro=[]
    for p in (W/'fuc/Europe').iterdir():
        if p.is_dir():euro.append(stats(p))
    result=dict(timestamp=now(),measurement='Sum of file lengths / logical path bytes, not allocated disk clusters or unique hardlink bytes. Overlapping nested inventories are not additive.',roots=roots,Europe_work_subdirectories=euro,free_bytes=shutil.disk_usage(L).free,deletion_actions=0)
    write(MD/'FUC_FINAL_DISK_INVENTORY.json',result)
    categories=[]
    for p,cat,purpose in [
      (EU/'RawExtracted','ESSENTIAL','Formal source ISO, ISO files and raw FPK payloads'),
      (EU/'Converted','ESSENTIAL','Working PNG/FLAC/MP4/static and validated animated GLB/Replay plus viewer dependencies'),
      (EU/'Metadata','ESSENTIAL','Formal indexes, semantic graph, frozen proofs and manifests'),
      (L/'Metadata','ESSENTIAL','268504-row unified Catalog and inherited indexes'),
      (L/'Gallery','ESSENTIAL','Unified Gallery, previews, textures, sidecar entry pages and local vendor libraries'),
      (SCRIPTS,'ESSENTIAL','Selected permanent reproduction tools; exact subset defined in tool manifest'),
      (W/'backups/fuc-animation-pre-validation','ESSENTIAL','Debugger frozen() requires this pre-validation BASELINE; preserve all backup companions'),
      (W/'backups/fuc-battle-runtime-pre','ESSENTIAL','Whole-library protected-path snapshot and battle baseline required by audits/runtime helpers'),
      (W/'backups/fuc-semantic-mapping-pre','ESSENTIAL','Semantic frozen baseline and protected prior indexes'),
      (W/'tools/python','ESSENTIAL','Existing Python environment and module runtime'),
      (W/'tools/noesis-fuc','ESSENTIAL','Noesis converter and required plugins'),
      (W/'tools/vgmstream-fuc/runtime','ESSENTIAL','vgmstream converter runtime'),
      (W/'tools/ppsspp-isolated','ESSENTIAL','Isolated emulator, config/memstick and prior diagnostic saves; on-demand only'),
      (W/'fuc/AnimationValidation/Runtime','EVIDENCE','Golden source skeletons, sine LUTs and45 runtime pose frames'),
      (W/'fuc/AnimationValidation/Playback','EVIDENCE','286-frame standard-viewer proof'),
      (W/'fuc/BattleReplay/Episode08','EVIDENCE','Only accepted same-Episode Lancer capture; 83frames'),
      (W/'fuc/BattleReplay/ViewerAcceptanceFinalV3','EVIDENCE','Accepted Replay comparison and playback proof'),
      (W/'fuc/BattleGeneralization','EVIDENCE','Shared pose/effect/sound provenance proofs; also contains historical probes'),
      (W/'fuc/SemanticMapping','EVIDENCE','ROM parsing, UI glyph captures, command anchors and rejected diagnostic samples'),
      (W/'fuc/FinalFreeze','EVIDENCE','Final baseline and current audit/browser logs'),
      (W/'fuc/Europe/Executable','EVIDENCE','Original decrypted EBOOT ELF and static investigation; not a patch'),
      (W/'fuc/europe-probe','HISTORICAL_DIAGNOSTIC','Pre-integration probes; keep original failures and hypotheses'),
      (W/'fuc/source_diagnostic','HISTORICAL_DIAGNOSTIC','Truncated ZIP diagnosis'),
      (W/'fuc/Japan_Recovery','HISTORICAL_DIAGNOSTIC','Irreplaceable partial Japanese source recovery;0formalIDs, never treat as cache'),
      (L/'FateUnlimitedCodesPortable','HISTORICAL_DIAGNOSTIC','Earlier Japan recovery library, independent from Europe'),
      (SCRIPTS/'__pycache__','RECOVERABLE_CACHE','Interpreter bytecode; source remains authoritative'),
    ]:
        if p.exists():categories.append(dict(path=str(p),classification=cat,purpose=purpose,retention='KEEP; this task deletes nothing',overlap='Classification may overlap nested paths; do not sum sizes as unique disk usage'))
    write(MD/'FUC_LONG_TERM_ARTIFACTS.json',dict(timestamp=now(),items=categories,deleted=0,policy='ESSENTIAL/EVIDENCE/HISTORICAL_DIAGNOSTIC/RECOVERABLE_CACHE all retained. Failed traces and Japan Recovery are not disposable.'))
    cache=stats(SCRIPTS/'__pycache__');candidates=[dict(path=cache['path'],logical_bytes=cache['logical_bytes'],files=cache['files'],classification='RECOVERABLE_CACHE',condition='Python can regenerate bytecode from retained sources; obtain user decision before any future deletion.')]
    # Working extraction/conversion copies may be hardlinked and may supply Golden paths.
    for r in euro:
        if pathlib.Path(r['path']).name in ['FPKExtracted','Models','TextureRaw','Textures','Audio','AudioBank','Videos','integration_stage']:
            candidates.append(dict(path=r['path'],logical_bytes=r['logical_bytes'],files=r['files'],classification='REVIEW_ONLY',condition='Do not delete wholesale: paths may be referenced by runtime evidence and may be hardlinks. Future per-file hash/reference/hardlink audit required; no free-space savings asserted.'))
    write(MD/'FUC_OPTIONAL_CLEANUP_CANDIDATES.json',dict(timestamp=now(),candidates=candidates,deleted=0))
    table='\n'.join(f"| `{r['path']}` | {r['files']:,} | {r['logical_bytes']:,} | {r['classification']} | {r['condition']} |" for r in candidates)
    textwrite(L/'Reports/FUC_OPTIONAL_CLEANUP_CANDIDATES.md',f'''# FUC Optional Cleanup Candidates

本轮删除操作：**0**。以下均为未来供用户决定的候选，不是删除授权。

| 路径 | 文件数 | 逻辑字节 | 分类 | 未来处理条件 |
|---|---:|---:|---|---|
{table}

文件长度之和不等于可释放空间；存在硬链接，且上述部分目录重叠。既有 `Metadata/DISK_FOOTPRINT.json` 保存了上一轮 file-ID 去重测量，不能将这次目录长度直接当作实际占用。

不列为可删缓存：Japan Recovery、accepted/rejected runtime captures、失败 probe、旧报告、原始 ELF、isolated memstick/save/config、Golden LUT/skeleton、Episode08、正式 Preservation 与已验证 GLB。保留它们是可复现性的一部分。

更多分类：`FateUnlimitedCodesPortable_Europe/Metadata/FinalFreeze/FUC_LONG_TERM_ARTIFACTS.json`。本轮没有删除、移动或缩减任何历史目录。
''')
    return result
def tools():
    groups={
      'source preservation / ISO parser':['FUC_ASSETS.ps1','fuc_iso.py','fuc_europe_inventory.py'],
      'FPK strict parser and independent verification':['fuc_fpk_extract.py','fuc_fpk_probe.py','fuc_full_fpk_verify.py'],
      'model / source skeleton / texture converters':['fuc_models_stage.py','fuc_source_bones.py','fuc_textures_stage.py'],
      'audio / bank / video converters':['fuc_audio_stage.py','fuc_soundbanks_stage.py','fuc_video_stage.py'],
      'MOT decoder / evaluator / standard animation exporter':['fuc_motion_channels.py','fuc_motion_evaluator.py','fuc_anim_glb_export.py','fuc_anim_gltf_validate.cjs','fuc_anim_pose_compare.py','fuc_anim_bank_verify.py'],
      'runtime debugger / FAN / equipment / effect / sound evidence':['fuc_anim_debugger.py','fuc_battle_debugger.py','fuc_battle_equipment_analyze.py','fuc_general_effect_pose.py','fuc_general_sound_chain.py','fuc_general_audio_match.py','fuc_general_golden_gate.py'],
      'same-Episode Replay reconstruction':['fuc_replay_debugger.py','fuc_replay_episode.py','fuc_replay_build.py','fuc_replay_golden_gate.py','fuc_replay_gltf_validate.cjs','fuc_replay_sound_chain.py'],
      'semantic parser / command schema / minimal anchor workflow':['fuc_semantic_parse.py','fuc_semantic_static.py','fuc_semantic_anchor.py','fuc_semantic_debugger.py','fuc_semantic_build.py'],
      'final read-only audit and additive documentation':['fuc_final_audit.py','fuc_final_checks.py','fuc_final_documents.py','fuc_final_server.py'],
    }
    selected={};queue=[]
    for purpose,names in groups.items():
        for name in names:
            p=SCRIPTS/name;assert p.is_file(),p;selected[p]=purpose;queue.append(p)
    # Preserve local module dependency closure without promoting every failed probe.
    while queue:
        p=queue.pop()
        if p.suffix!='.py':continue
        for node in ast.walk(ast.parse(p.read_text('utf-8-sig'))):
            names=[node.module] if isinstance(node,ast.ImportFrom) and node.module else [n.name for n in node.names] if isinstance(node,ast.Import) else []
            for name in names:
                q=SCRIPTS/(name.split('.')[0]+'.py')
                if q.is_file() and q not in selected:selected[q]='local dependency of '+p.name;queue.append(q)
    records=[]
    for p,purpose in sorted(selected.items()):
        runtime='Python3.13 (numpy/scipy/pycdlib/websocket-client as applicable; see recorded dependency versions)' if p.suffix=='.py' else 'PowerShell7/Windows PowerShell' if p.suffix=='.ps1' else 'Node.js + preserved gltf-validator package'
        safe=p.name.startswith('fuc_final_') or p.name=='fuc_motion_evaluator.py'
        records.append(dict(tool=p.name,path=str(p),sha256=sha(p),purpose=purpose,required_runtime=runtime,status='retained; audited source bytes',golden_dependency=any(x in p.name for x in ['evaluator','channels','glb','replay','common','pose_compare','final_']),execution_policy='audits write only new FinalFreeze paths; evaluator output must be in WORK' if safe else 'historical reproduction / on-demand only; review output targets before running; do not rerun Full/reindex/export over frozen library'))
    extra=[
      (W/'tools/noesis-fuc/Noesis64.exe','Noesis4.474 GMO/static GLB converter','Windows; keep whole noesis-fuc plugin/runtime directory'),
      (W/'tools/ppsspp-isolated/runtime/PPSSPPWindows64.exe','PPSSPP isolated runtime for future targeted verification only','Windows; preserve isolated config/memstick; do not use user PPSSPP state'),
      (W/'tools/python/Scripts/python.exe','Existing Python environment launcher','Python3.13 base installation at D:/python; keep venv and base runtime'),
      (pathlib.Path(sys._base_executable),'Python base runtime','Keep base Python installation and venv packages together'),
      (pathlib.Path(shutil.which('node')),'Node.js runtime for preserved glTF validator','Keep Node.js installation'),
      (pathlib.Path('D:/DDplay/ffmpeg/ffmpeg.exe'),'FFmpeg audio/video converter','Keep adjacent runtime'),
      (pathlib.Path('D:/DDplay/ffmpeg/ffprobe.exe'),'Media verifier','Keep adjacent runtime'),
      (W/'tools/vgmstream-fuc/runtime/vgmstream-cli.exe','vgmstream bank/VAG decoder','Keep complete runtime folder'),
      (L/'Gallery/fuc_lan_clip145_replay.js','Accepted83-frame Replay viewer','HTTP localhost; preserved Three.js/GLTFLoader vendor modules'),
      (L/'Gallery/FUC_LAN_CLIP145_REPLAY.html','Replay viewer entry','HTTP localhost'),
      (EU/'Converted/AnimatedModels/viewer/index.html','Nine Golden animation viewer','HTTP localhost; preserved vendor modules'),
      (W/'fuc/AnimationValidation/Tools/gltf-validator/package.json','Khronos glTF validator package identity','Node.js; keep complete package directory'),
    ]
    for p,purpose,runtime in extra:
        assert p.is_file(),p
        records.append(dict(tool=p.name,path=str(p),sha256=sha(p),purpose=purpose,required_runtime=runtime,status='preserved existing runtime/viewer; not installed or updated in final audit',golden_dependency=True))
    modules=set()
    for p in selected:
        if p.suffix!='.py':continue
        for node in ast.walk(ast.parse(p.read_text('utf-8-sig'))):
            names=[node.module] if isinstance(node,ast.ImportFrom) and node.module else [n.name for n in node.names] if isinstance(node,ast.Import) else []
            for name in names:
                top=name.split('.')[0]
                if top not in sys.stdlib_module_names and not (SCRIPTS/(top+'.py')).exists():modules.add(top)
    distributions=importlib.metadata.packages_distributions();needed={d for m in modules for d in distributions.get(m,[])}
    mods={}
    for name in sorted(needed):
        try:mods[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:mods[name]='not found'
    unresolved=[m for m in sorted(modules) if not distributions.get(m)]
    manifest=dict(timestamp=now(),tools=records,python=platform.python_version(),python_packages=mods,external_import_modules=sorted(modules),unresolved_external_modules=unresolved,dependency_directories=[str(W/'tools/noesis-fuc'),str(W/'tools/vgmstream-fuc/runtime'),str(W/'tools/ppsspp-isolated'),str(W/'fuc/AnimationValidation/Tools/gltf-validator'),str(EU/'Converted/AnimatedModels/viewer/vendor')],policy='Only permanent parsers/reproduction/audit tools and their local dependencies selected. Historical probes remain preserved but are not active tool entries. Never rerun integration against frozen Catalog.',missing_tools=0)
    write(MD/'FUC_FINAL_TOOL_MANIFEST.json',manifest);return manifest
def usage():
    textwrite(L/'Reports/FUC_USAGE_GUIDE.md',r'''# FUC Europe 使用指南（供 MOD 开发）

正式来源：`FateUnlimitedCodesPortable_Europe`，NPEH00007 / v1.01。统一 Catalog 268,504 条，其中 Europe21,899 条；最大 ID FSN268504。FUC 研究阶段已冻结，素材可用于后续 FSN × Slay the Spire2 开发。

## 从哪里开始

总入口：`E:\FSN_MASTER_ASSET_LIBRARY\Gallery\FUC_INDEX.html`。主 Gallery 的版本筛选选择 FateUnlimitedCodesPortable_Europe。纯索引可直接打开；含 three.js/fetch 的动画、语义和 Replay 页面需要本地 HTTP。

可在终端使用已有 Python 启动只读静态服务器，随后打开 `http://127.0.0.1:8999/Gallery/FUC_INDEX.html`：

```powershell
& 'E:\FSN_MASTER_ASSET_WORK\tools\python\Scripts\python.exe' -m http.server 8999 --bind 127.0.0.1 --directory 'E:\FSN_MASTER_ASSET_LIBRARY'
```

使用完按 Ctrl+C 停止。8999 静态服务器只供浏览，验收按钮的本机证据写回需要独立接收器；普通播放无需接收器。不要用旧验收接收器向既有 Golden 文件写回新证据。

主要索引根目录：`E:\FSN_MASTER_ASSET_LIBRARY\FateUnlimitedCodesPortable_Europe\Metadata`。路径与 asset_id 以 Catalog/索引为准，不能用文件名相似性替代绑定证据。

## 我要找角色模型或纹理

模型：`MODEL_INDEX.csv` → source_name/source_path → asset_id → working_path。842 个逻辑 GMO 复用341 个唯一静态 GLB。用 `CHARACTER_ASSET_MAP.csv`、`SemanticMapping/FUC_CHARACTER_CODE_MAP.csv` 定位目录代码；20 个内部身份不等于20个已确认可玩角色。

骨骼：`SOURCE_BONE_INDEX.csv` 为源 transform nodes；`SKELETON_INDEX.csv` 为转换后的 skin/joints。源 bone ID、GMO node ordinal、GLB node、GLB joint 是不同编号。`bN` 名称只是 Noesis provisional mapping，不能据此命名身体部位。

纹理：`TEXTURE_INDEX.csv` → working_path（PNG），或使用 GLB 内嵌纹理。6,290 个逻辑图片对应2,371个唯一PNG。`FUC_TEXTURE_EXTERNAL_REFERENCE.csv` 保留外部纹理引用；精确 PSP shader/palette 未全量重建，MOD 使用目标引擎材质即可。

## 我要找动作，并判断能否直接使用

`ANIMATION_INDEX.csv` 收录3,676条已解码非空clip；它证明通道解码，不代表全部可用动画。

直接使用范围以 `AnimationValidation/FUC_VALIDATED_ANIMATIONS.csv` 为准：sir/rin/lan 三个模型，clip0/1/2各三条，共9条。查看 binding、bone_mapping、translation、rotation、scale、time、interpolation、runtime_compared 字段。只有通过这些 gate 且有 animated_glb 的条目才能作为已验证动画使用。

标准播放器：`Converted/AnimatedModels/viewer/index.html`；原 GLB 与 preview 路径在 validated表。60Hz时钟已确认，source translation、direction+twist rotation、默认scale、bone-ID remap 和原插值只在已证明范围内适用。循环播放是查看器选项，不能自动当作源游戏loop标志。

剩余3,667条记录为 ON_DEMAND；不要批量导出、猜动作名，或把 clip编号直接对应 GLB joint。

## 我要看完整 Lancer Replay

`Gallery/FUC_LAN_CLIP145_REPLAY.html`。它来自同一自然 Episode，83帧，包含 runtime final body pose、枪、SEQ effect birth/update/end 与 FSN260985 音频启动事件。

`Metadata/BattleReplay/FUC_LAN_CLIP145_REPLAY_MANIFEST.json` 和 timeline 是依赖权威；GLB在 `Converted/BattleScenes/lan_clip145/lan_clip145_battle_pose.glb`。这是一个已捕获最终姿态的重放，不能把它当作任意 clip145原始动画或通用战斗blend公式。PSP精确材质及SAS原生sample clock仍未知。

`FUC_BATTLE_RUNTIME.html` 和 `_V2.html` 是早期阶段快照，其中旧“尚未完成”描述在当时成立。当前完整重播/冻结状态以 FUC_INDEX、Final Manifest 和最终报告为准；历史页面不改写。

## 我要找招式、Command 或状态

使用 `Metadata/SemanticMapping`：Character Code Map → Command Index → Move Index → Move Animation Map → Resource Graph；Effect/Sound Map补充已确认关系。

当前3条真实返回bank/clip anchor：lan state145→bank0 clip145 FSN258272；sir state155→bank0 clip155 FSN259886；rin state159→bank0 clip159 FSN258899。UI名绑定仅3条：lan155 Unique Move、sir155 Unique Move、rin159 Gand Shot。

Lancer145是 △ / M ATTACK，没有独立招式显示名，move_name应继续留空。Lancer155的UI name成立，不自动等于其动画来源已完整runtime验证。

262个UI条目中259个未绑定最终state，保留为 semantic_backlog。`confirmed_table` 表示ROM表证据，`confirmed_string_reference` 表示字符串/字形来源证据，均不等于最终runtime动画确认；`strong_candidate`仍是候选。不要按显示顺序、command文字、名字或动画外观猜映射。

## 我要找音频或 VFX

音频：`FUC_AUDIO_INDEX.csv`（5,537逻辑行）、`FUC_VOICE_INDEX.csv`、`SOUND_BANK_INDEX.csv`；raw VAG/ATRAC及PPHD/PBD保留。FLAC working_path可直接使用。`SemanticMapping/FUC_MOVE_SOUND_MAP.csv` 与 `BattleGeneralization/FUC_SOUND_ID_MAP.csv` 提供已确认sound关系：0x232D→FSN260985。对白语义未确认，不要自行加台词名。

VFX：`EFFECT_INDEX.csv` 2,056行；先按路径/格式找模型或纹理，再查 `FUC_MOVE_EFFECT_MAP.csv`、BattleGeneralization矩阵证据与Replay timeline。已确认 Lancer1000.seq→1002.gmo快照规则不自动推广到所有效果。AMO/BAM/TUV/MIL/PAR仅保留/索引或局部结构，不保证完整runtime可用。

## 以后确实需要验证一个新 MOT

这是后续按需新任务，本次冻结不自动继续。先确定一个具体 model/MOT/clip，复制工作结果到WORK新目录，复用原始数据和长期工具。

`fuc_motion_evaluator.py` 支持 `--mot <原MOT路径> --clip-index N --time 秒 --output <WORK新JSON>`，已验证模型可以用 `--code sir|rin|lan`；其他模型必须提供真实 `--skeleton-metadata` 与 `--sine-lut`。time由60Hz时钟转换，不能用viewer帧率猜。

最小流程：资源loader证明配对→bone-ID/remap证明→选时间点求值→独立portable PPSSPP读取同一runtime pose→translation/rotation/scale/matrix数值对比→通过后导出新的AnimatedModels文件→标准viewer回归。保留误差、时间单位、插值和rotation证据；evaluator本身不授予export资格。单raw clip与runtime blended pose分别验证。

## 以后确实需要验证一个新 Move

复用 `fuc_semantic_parse.py`、`fuc_semantic_anchor.py` 和已保存ELF/Command schema。选择一条command，在独立portable PPSSPP记录输入历史、最终state、selector请求与实际返回bank/clip；不能把request当作actual return。若有UI名，必须保留明确字形引用和state证据。只有实际观察到才添加effect/sound关系。

先在WORK新sidecar中完成关系及dangling检查。保留旧asset_id、Catalog核心字段和Frozen成果；新增关系以版本化sidecar保存。新model/clip不是改编号理由。需要新逻辑资产时另走显式增量流程，不能重跑Full/reindex。

## 长期保留与未知项

`Metadata/FinalFreeze/FUC_FINAL_TOOL_MANIFEST.json` 列出永久工具SHA及运行环境；`FUC_LONG_TERM_ARTIFACTS.json` 区分正式素材、证据、历史诊断及可再生缓存。复制工具时保留依赖目录，尤其Noesis plugins、Python环境/base runtime、Three.js vendor、isolated memstick/config和gltf-validator。

所有工具存在并不意味着可以原地重跑：旧导出/整合脚本可能写固定路径，只适合阅读或在未来隔离工作区审查后调用。不要对冻结Catalog运行FUC_ASSETS Full或重建整合命令。

`FUC_FINAL_KNOWN_UNKNOWN_MATRIX.csv` 是当前未知项权威。259UI绑定、3667MOT、AMO及其余效果格式均按需；PSP精确材质、SASsample clock、通用battle blend对当前MOD非阻塞。Japan Recovery单独保留，0正式ID，不能当作完整日版或删除缓存。

最终报告：`E:\FSN_MASTER_ASSET_LIBRARY\Reports\FUC_FINAL_REPORT.md`。
机器冻结标志：`E:\FSN_MASTER_ASSET_LIBRARY\FateUnlimitedCodesPortable_Europe\FUC_FROZEN_FOR_MOD_DEVELOPMENT.json`。
''')
def gallery():
    texture=rows(EU/'Metadata/TEXTURE_INDEX.csv')[0];audio=rows(EU/'Metadata/FUC_AUDIO_INDEX.csv')[0];video=rows(EU/'Metadata/VIDEO_INDEX.csv')[0];model=rows(EU/'Metadata/MODEL_INDEX.csv')[0]
    def choose(r):return pathlib.Path(r.get('working_path') or r.get('converted_path'))
    destinations=[('模型 · 341 unique GLB',EU/'Metadata/MODEL_INDEX.csv','842个逻辑模型；索引按source path与asset_id定位。'),('纹理 · PNG',EU/'Metadata/TEXTURE_INDEX.csv','6,290条逻辑图片，2,371份唯一PNG。'),('动画 · 9条已验证',EU/'Converted/AnimatedModels/viewer/index.html','sir / rin / lan各3条；其余3,667条仅已解码。'),('动画验证表',AV/'FUC_VALIDATED_ANIMATIONS.csv','配对、骨骼、旋转、时间轴及runtime状态。'),('招式与Command',L/'Gallery/FUC_SEMANTIC_MOVES.html','262 UI entries；3已绑定，259待按需处理。'),('完整 Lancer Replay',L/'Gallery/FUC_LAN_CLIP145_REPLAY.html','同一Episode · 83帧 · body / spear / effect / audio。'),('Effects',EU/'Metadata/EFFECT_INDEX.csv','2,056个资源；只使用已确认关系。'),('Audio',EU/'Metadata/FUC_AUDIO_INDEX.csv','5,537条逻辑音频，FLAC working copies。'),('最终报告',L/'Reports/FUC_FINAL_REPORT.md','完整审计结果及冻结决定。'),('使用指南',L/'Reports/FUC_USAGE_GUIDE.md','面向未来MOD开发的查找与按需验证流程。'),('Known / Unknown',MD/'FUC_FINAL_KNOWN_UNKNOWN_MATRIX.csv','明确范围与开发影响；不猜名称或绑定。'),('Final Manifest',EU/'Metadata/FUC_FINAL_MANIFEST.json','来源、索引、Golden hashes及长期工具。')]
    cards=''.join(f'<a class="card" href="{link(p)}"><h2>{html.escape(title)}</h2><p>{html.escape(desc)}</p><span>打开 →</span></a>' for title,p,desc in destinations)
    t,a,v,m=map(choose,[texture,audio,video,model])
    page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FUC Europe · 冻结素材总入口</title><style>
:root{{color-scheme:dark}}*{{box-sizing:border-box}}body{{margin:0;background:#101820;color:#e9edf2;font:16px/1.65 system-ui}}main{{max-width:1100px;padding:40px 24px;margin:auto}}a{{color:#86dadd;text-decoration:none}}a:focus-visible,button:focus-visible{{outline:3px solid #e9c574;outline-offset:4px}}h1{{font-size:34px;line-height:1.3;margin:12px 0}}h2{{font-size:20px;margin:0 0 8px}}p{{margin:8px 0}}.muted,small{{color:#b5c3cf}}.status{{color:#a9e4c4}}.facts{{display:flex;gap:24px;flex-wrap:wrap;margin:24px 0 32px}}.facts strong{{display:block;font-size:28px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}}.card{{display:block;border:1px solid #34505b;padding:22px;background:#172630;border-radius:8px}}.card p{{color:#c0cdd7;min-height:52px}}.card:hover{{border-color:#86dadd}}.card span{{font-size:14px}}section{{margin-top:36px;padding-top:24px;border-top:1px solid #34505b}}.samples{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px}}img{{width:128px;height:128px;object-fit:contain;background:#20323f}}audio,video{{width:100%;display:block}}video{{max-width:480px}}button{{padding:8px 14px;margin:10px 6px 0 0;border:1px solid #709ba4;border-radius:5px;background:#233944;color:#fff;cursor:pointer}}nav{{display:flex;flex-wrap:wrap;gap:20px}}footer{{margin:36px 0;color:#b5c3cf;font-size:14px}}@media(max-width:520px){{main{{padding:24px 18px}}h1{{font-size:27px}}}}
</style></head><body><main><small>FSN MASTER ASSET LIBRARY / FateUnlimitedCodesPortable_Europe</small><h1>FUC Europe · 冻结素材总入口</h1><p class="status">研究阶段已结束 · 可进入 MOD 开发</p><p class="muted">以源文件、数值验收与明确证据为准。新增入口不改动主 Gallery。</p><div class="facts"><div><strong>21,899</strong>正式 FUC 资产</div><div><strong>341</strong>唯一静态 GLB</div><div><strong>9 / 3,676</strong>已验证 / 已解码动画</div><div><strong>3 / 262</strong>已绑定 UI 名称</div></div><div class="grid">{cards}</div>
<section><h2>历史证据入口</h2><p class="muted">以下是各阶段的原始快照；当前完整 Replay 与冻结范围以此页和最终报告为准。</p><nav><a href="FUC_BATTLE_RUNTIME.html">Battle Runtime</a><a href="FUC_BATTLE_RUNTIME_V2.html">Battle Runtime V2</a><a href="index.html">主素材 Gallery · 268,504</a></nav></section>
<section><h2>代表性素材</h2><div class="samples"><div><p>纹理 · {html.escape(texture['asset_id'])}</p><img id="sampleTexture" alt="FUC 源纹理示例" src="{link(t)}"><p><a href="{link(m)}">静态 GLB · {html.escape(model['asset_id'])}</a></p></div><div><p>音频 · {html.escape(audio['asset_id'])}</p><audio id="sampleAudio" controls preload="metadata" src="{link(a)}"></audio><button id="audioPlay">播放音频示例</button><button id="audioPause">暂停音频示例</button><p id="audioStatus" role="status"></p></div><div><p>PMF → MP4</p><video id="sampleVideo" controls preload="metadata" src="{link(v)}"></video><button id="videoPlay">播放视频示例</button><button id="videoPause">暂停视频示例</button><p id="videoStatus" role="status"></p></div></div></section>
<footer>剩余3,667条MOT与259条UI绑定按需验证；AMO / 其他效果格式、精确PSP材质、SAS采样时钟不阻塞当前开发。Japan Recovery保留独立，不在正式Catalog。</footer></main><script>
for(const kind of ['audio','video']){{const media=document.getElementById('sample'+kind[0].toUpperCase()+kind.slice(1)),status=document.getElementById(kind+'Status');document.getElementById(kind+'Play').onclick=()=>media.play().then(()=>{{status.textContent='正在播放'}}).catch(e=>{{status.textContent='播放失败：'+e.message}});document.getElementById(kind+'Pause').onclick=()=>{{media.pause();status.textContent='已暂停'}};media.addEventListener('ended',()=>{{status.textContent='播放完毕'}});media.addEventListener('error',()=>{{status.textContent='媒体加载失败'}})}}
</script></body></html>'''
    assert not (L/'Gallery/FUC_INDEX.html').exists(),'Do not overwrite an inherited entry'
    textwrite(L/'Gallery/FUC_INDEX.html',page)
def prepare():
    assert not (EU/'FUC_FROZEN_FOR_MOD_DEVELOPMENT.json').exists(),'Frozen library: do not rerun prepare; use a new WORK audit directory'
    assert not (EU/'Metadata/FUC_FINAL_MANIFEST.json').exists(),'Final manifest already exists'
    MD.mkdir(parents=True,exist_ok=True);OUT.mkdir(exist_ok=True)
    known_unknown();disk_inventory();tools();usage();gallery();log('PREPARED',str(MD))
def copy_evidence():
    for name in CHECKS:
        shutil.copy2(WORK/f'{name}.json',MD/f'{name}.json')
    shutil.copy2(WORK/'GOLDEN_RAW_EVALUATOR_COMPARISON.csv',MD/'GOLDEN_RAW_EVALUATOR_COMPARISON.csv')
    shutil.copytree(WORK/'BrowserEvidence',MD/'BrowserEvidence',dirs_exist_ok=True)
def finalize():
    assert not (EU/'FUC_FROZEN_FOR_MOD_DEVELOPMENT.json').exists(),'Freeze marker already exists; no replacement allowed'
    assert not (EU/'Metadata/FUC_FINAL_MANIFEST.json').exists(),'Final manifest already exists; no replacement allowed'
    checks={n:read(WORK/f'{n}.json') for n in CHECKS}
    assert all(x['status']=='PASS' for x in checks.values()),[(n,x['status']) for n,x in checks.items()]
    assert read(WORK/'BrowserEvidence/GOLDEN_THREEJS_REGRESSION.json')['status']=='PASS'
    played=read(WORK/'BrowserEvidence/GOLDEN_REALTIME_PLAYBACK.json')
    assert len(played)==9 and all(r['status']=='PASS' and r['time']>0 for r in played)
    replay=read(WORK/'BrowserEvidence/lan_clip145_replay_viewer_validation.json');play=read(WORK/'BrowserEvidence/lan_clip145_replay_playback.json')
    assert replay['status']=='PASS' and play['status']=='PASS'
    copy_evidence();timestamp=now();c=checks['CATALOG_AUDIT'];sem=checks['SEMANTIC_AUDIT'];disk=read(MD/'FUC_FINAL_DISK_INVENTORY.json');matrix=rows(MD/'FUC_FINAL_KNOWN_UNKNOWN_MATRIX.csv');b=read(WORK/'BASELINE.json')
    # All FUC_INDEX links resolve to existing local deliverables (including future manifest/marker names).
    required=[MD/'FUC_FINAL_TOOL_MANIFEST.json',MD/'FUC_LONG_TERM_ARTIFACTS.json',MD/'FUC_FINAL_KNOWN_UNKNOWN_MATRIX.csv',L/'Reports/FUC_USAGE_GUIDE.md',L/'Gallery/FUC_INDEX.html']
    assert all(p.is_file() for p in required)
    confidence='\n'.join(f'| {k} | {v:,} |' for k,v in sem['confidence_field_occurrences'].items())
    report=f'''# FUC Final Freeze and Audit

## A. Final Status

**{FSTATUS}**\n\n**{CSTATUS}**\n\n冻结时间：{timestamp}（UTC）。当前低层研究保持 CLOSED FOR MOD DEVELOPMENT。本轮只审计、回归、文档化和打包，没有新增研究或runtime capture。

## B. Source Identity

Europe NPEH00007 / v1.01；source_version=FateUnlimitedCodesPortable_Europe。原ISO及正式Preservation ISO各738,394,112字节，当前SHA-256均为 `bdf13beffbad519fd51f1ab075d165d3c7bfa075feef1a5b1fd7775bac0f830d`，与原记录一致。直接只读读取原ISO PARAM.SFO复核身份；没有解包ISO。源路径详见SOURCE_AUDIT.json。

Japan Recovery截断、非正式源、0Catalog ID；WORK/Japan_Recovery及独立旧FateUnlimitedCodesPortable区全部保留。

## C. Extraction

既有提取：2,738 ISO files；542/542 FPK；6,558/6,558 payloads。严格PRS独立验证记录保留。本轮21,899逻辑资产→15,070唯一Preservation源文件，全量源SHA及size核验，missing0、mismatch0。没有重新提取或覆盖Raw。

## D. Models / Skeleton

842逻辑GMO→341唯一GLB，全部容器、buffers/accessors、source mapping低成本审计通过。4,059源transform nodes、2,642weighted skin joints。3个Golden skeleton规则已验证；Noesis `bN`仍是provisional名称，不推断人体语义。341静态GLB全部保持原SHA。

## E. Textures / 2D

6,290逻辑图片，2,371唯一PNG。Working及源路径完整，实际浏览器PNG解码通过。精确PSP材质/shader/palette未全量恢复，NON_BLOCKING；现有PNG和标准GLB可用于目标MOD渲染。

## F. Audio / Video

VAG/ATRAC3：3,576逻辑音频→2,117唯一FLAC（2,078 PSX-ADPCM、39 ATRAC3）。43PPHD/PBD banks：1,961逻辑stream→1,623唯一FLAC，17empty slots。两条转换链合计3,740份唯一Working FLAC（分别按各链源身份去重，非跨链声学去重）。FUC_AUDIO_INDEX共5,537行。5PMF→5MP4保留；本轮代表FLAC及MP4真实浏览器播放通过。FSN260985上下游因果链与SAS KeyOn证据保留；原生sample clock未知，不声称sample-perfect PSP混音。

## G. Animations

54MOT、15,440offset slots、3,676非空decoded clips、198,831channels、2,044,587key values。Runtime validated单clip仅9条：sir/rin/lan各clip0/1/2。剩余3,667条保持未验证，ON_DEMAND。

本轮重新读取这9条原MOT并求值，对照既有Golden runtime：45frames /2,535nodes，failures0，max error0。Three.js0.180重新逐帧：286frames /16,357node comparisons，missing0、failures0，max matrix error约1.03122267×10⁻⁶，未退化。另对9条逐条实际播放确认time推进并暂停。旧9GLB及预览均未改动，没有新导出。

## H. Battle Runtime

FUC_BATTLE_RUNTIME_MAPPING_PASS、FUC_BATTLE_RUNTIME_GENERALIZATION_PASS既有证据冻结。FAN/BPO shared framework覆盖sir/rin/lan；Lancer spear attachment与effect外部矩阵来源/快照规则已证明在记录范围成立。AMO未获live interpolation证明，其他角色有效装备/专属effect不自动泛化。没有扩展逆向、自然capture、通用blend或SAS时钟研究。

## I. Full Replay

FUC_LAN_CLIP145_FULL_BATTLE_REPLAY_PASS保持。同一Episode `lan145_93c825fbc10749e7`，83frames、1.3666667938232422秒，runtime-authoritative final body pose+spear+SEQ effect+音频启动。

本轮独立Three.js回归：body4,980、weapon332、effect102次矩阵比较；body最大误差1.0482635468432241×10⁻⁶、weapon4.154258079758222×10⁻⁷、effect1.0361715103712754×10⁻⁶；missing0、visibility mismatch0。实际播放在native frame6确认body/weapon/effect均visible，音频FSN260985启动且currentTime>0、error=null。audio event174，master start0.06666667014360428秒；这证明事件启动，不证明原生sample clock。所有依赖、timeline、GLB和原viewer hash保持原状。

## J. Character / Move / Command Semantics

FUC_MOVE_COMMAND_SEMANTIC_MAPPING_PASS保持。20ELF内部身份，不能写成20已确认playable。19字符normal command schema的178rows、17字符conditional schema的783programs；Command Index1,231关系行；352ROM state subjects+259unbound UI subjects=611Move Index subjects。

实际selector返回锚点3条：lan145→bank0 clip145 FSN258272；sir155→bank0 clip155 FSN259886；rin159→bank0 clip159 FSN258899。5条request/source候选保持strong_candidate。UI最终state绑定仅lan155 Unique Move、sir155 Unique Move、rin159 Gand Shot。lan145仅△ / M ATTACK，没有独立显示名，继续留空。

## K. Semantic Coverage

262UI entries：3已绑定、259未绑定，全部保留。8input→state pairs，11accepted selector samples /2rejected；Resource Graph1,655edges。11CSV索引所有asset和sidecar move/state引用无dangling。5conflict记录是保留的证据边界，不是5个损坏引用。

| Evidence grade | 状态字段出现次数 |
|---|---:|
{confidence}

统计单位为各关系索引status字段（含state_binding_status）的出现次数，不是唯一资产、唯一动作或runtime验证总数；复合 `confirmed_runtime_ui` 与 `state_binding_unknown`另按原字段保留。完整按表统计见SEMANTIC_AUDIT.json。confirmed_table/string_reference/UI证据不擅自升级为runtime motion确认。

## L. Gallery / Browsers

本轮Codex in-app browser真实smoke：主Gallery268,504/268,504、FUC texture/audio/PMF→MP4/staticGLB link、九条animation、Semantic Moves、Battle Runtime、V2、完整Replay及新增FUC_INDEX。旧主renderer、Theora preview_map、Gallery脚本均原SHA不变。没有重复逐一播放全库；本轮浏览器范围以GALLERY_FINAL_AUDIT.json为准。

新增纯sidecar `Gallery/FUC_INDEX.html`，串联Models、Textures、Animations、Semantic Moves、Replay、Effects、Audio、Reports、Unknown、Usage Guide。历史Battle Runtime/V2页面中较早的未完成描述原样保存；新入口明确解释阶段差异，当前状态以Final Manifest为准。页面使用本机HTTP，vendor库已保存。

多页面连续导航时记录过1条MutationObserver错误；保留原始diagnostic。随后独立加载主Gallery Golden卡片与新入口，均0console errors，原动画卡片/预览链接和媒体功能通过，未改旧页面。没有把诊断删除或改写为从未发生。

## M. Reproducibility

永久工具和本地模块依赖闭包列于FUC_FINAL_TOOL_MANIFEST.json，每项有路径、SHA、用途、运行环境、保留状态、Golden dependency。保留Python3.13环境、Noesis4.474完整插件目录、vgmstream、FFmpeg、isolatedPPSSPP、Khronos validator及Three.js vendor。本轮未安装、升级或启动PPSSPP。

低成本复核：fuc_final_checks.py的models/golden/semantic模式不会重建资产，gate核验旧哈希；浏览器使用独立FinalFreeze接收路径，未写回旧Golden。第一次Source audit对SFO目录名猜测`;1`失败后，修正本轮新工具fuc_final_audit.py读取既有SOURCE_INVENTORY.iso_path。基线保留该工具最初SHA，最终Gate显式记载仅这1项本轮新工具修复；继承工具非授权变化0。

## N. Known / Unknown

完整矩阵：FUC_FINAL_KNOWN_UNKNOWN_MATRIX.csv，共{len(matrix)}子系统行，涵盖所有要求的ISO/FPK/模型/骨骼/纹理/MOT/FAN/AMO/SEQ/效果/音频/PPHD/PBD/视频/角色/command/move/UI/stage/font/unknown formats。3,102unknown-format库存是历史原始分类，含后续已研究的FAN/SEQ等subset，不冒充3,102全新未研究资产。

主要限制：3,667MOT、259UI绑定、其余AMO/BAM/TUV/MIL/PAR与SEQ/effect、20身份的playable范围、36supplementary glyph IDs、精确PSP材质、SASsample clock、通用battle blend。原始字节、索引、失败与候选证据均保留，不猜命名。

## O. Development Impact

当前MOD素材使用没有BLOCKING项；{sum(r['development_impact']=='ON_DEMAND' for r in matrix)}行ON_DEMAND，{sum(r['development_impact']=='NON_BLOCKING' for r in matrix)}行NON_BLOCKING。具体未验证动作或新招式在确实需要时另开最小增量验证，不是继续本专项的前置条件。Exact PSP渲染/时钟/通用blend不阻塞使用现有标准素材与已验证subset。

## P. Stability

Original42,546；Remastered160,056；HollowAtaraxia44,003；Europe21,899；Total268,504，max FSN268504。new IDs0、missing old IDs0、changed old rows0、duplicate IDs0、invalid parent0、semantic dangling0、SQLite integrity=ok。

CSV/JSONL/SQLite每行每继承字段一致（只规范化empty/null、声明REAL的数值、SQLite布尔0/1），三个文件SHA均与冻结基线相同：

- CSV `{c['catalog_sha256']['ASSET_CATALOG.csv']}`
- JSONL `{c['catalog_sha256']['ASSET_CATALOG.jsonl']}`
- SQLite `{c['catalog_sha256']['ASSET_CATALOG.sqlite']}`

Working11,369个唯一引用全部存在，已登记working SHA全通过；21,899FUC Preservation关系完整。另对统一库既有{checks['GLOBAL_PROTECTED_PATH_AUDIT']['protected_path_references']:,}条引用/{checks['GLOBAL_PROTECTED_PATH_AUDIT']['protected_unique_paths']:,}个唯一路径复核存在与size，missing0、size changed0；未重新hash旧FSN/FHA Raw。最终再次核验{checks['FINAL_STABILITY_GATE']['frozen_files']:,}个基线文件及2ISO，旧静态GLB/9动画/Replay/semantic/主Gallery非授权变化0。唯一差异为上述本轮新audittool修复，不涉及旧资产。所有新文件为sidecar/report/package，不修改Catalog。

## Q. Disk / Long-term Artifacts

本轮只读目录长度盘点见FUC_FINAL_DISK_INVENTORY.json；可用E盘空间记录为{disk['free_bytes']:,}字节。统计是逻辑path bytes，重叠目录及硬链接不能当作可释放空间累加。既有file-ID去重DISK_FOOTPRINT.json原样保留。FUC_LONG_TERM_ARTIFACTS.json按ESSENTIAL/EVIDENCE/HISTORICAL_DIAGNOSTIC/RECOVERABLE_CACHE分类；工具运行环境及Accepted captures均保留。

## R. Cleanup Candidates

FUC_OPTIONAL_CLEANUP_CANDIDATES.md仅提出Python bytecode及需逐文件复审的中间Working目录。Raw/Golden/Japan/failed traces不作为可删缓存；删除0、移动0。未来清理决定留给用户，本轮未执行。

## S. Usage Guide

`E:\\FSN_MASTER_ASSET_LIBRARY\\Reports\\FUC_USAGE_GUIDE.md`面向开发，提供模型/纹理/动作/Replay/Command/声音/VFX入口与按需验证流程，不必重新遍历历史报告。旧管线不能对冻结库重跑Full/reindex；新增关系先使用WORK版本化sidecar。

## T. Freeze Decision

所有当前audit、Golden、Replay、semantic和stability gates通过，Final Manifest及机器marker随后生成，正式冻结研究阶段。已知局部覆盖不降低Final PASS。无新增asset_id、无新动作/模型/preview、无进一步逆向。最终入口与轻量索引/工具包供未来MOD直接使用。

权威文件：`FateUnlimitedCodesPortable_Europe/Metadata/FUC_FINAL_MANIFEST.json`、`FateUnlimitedCodesPortable_Europe/FUC_FROZEN_FOR_MOD_DEVELOPMENT.json`。原阶段summary中binding0/table0等旧计数是历史快照；最终能力以本Manifest与后续AnimationValidation/SemanticMapping证据为准，不重写旧历史。
'''
    textwrite(L/'Reports/FUC_FINAL_REPORT.md',report)
    indexes=[snap(p) for p in sorted((EU/'Metadata').rglob('*')) if p.is_file() and (p.suffix in ['.csv','.json'] or p.name=='ASSETS.jsonl') and p.name!='FUC_FINAL_MANIFEST.json']
    hashes={}
    for category,subset in [
      ('static_glb',[r for r in b['files'] if '/Converted/Models/' in r['path'].replace('\\','/') and r['path'].endswith('.glb')]),
      ('validated_animation_glb',[r for r in b['files'] if '/Converted/AnimatedModels/' in r['path'].replace('\\','/') and r['path'].endswith('.glb')]),
      ('replay_glb_viewer',[r for r in b['files'] if ('/Converted/BattleScenes/lan_clip145/' in r['path'].replace('\\','/') and r['path'].endswith('.glb')) or pathlib.Path(r['path']).name in ['FUC_LAN_CLIP145_REPLAY.html','fuc_lan_clip145_replay.js']]),
    ]:hashes[category]=subset
    assert len(hashes['static_glb'])==341 and len(hashes['validated_animation_glb'])==9
    assets=rows(EU/'Metadata/ASSETS.csv');minid=min(r['asset_id'] for r in assets)
    manifest=dict(status=FSTATUS,research_status=CSTATUS,freeze_timestamp=timestamp,source_version='FateUnlimitedCodesPortable_Europe',source_identity=checks['SOURCE_AUDIT'],asset_total=268504,FUC_asset_count=21899,asset_id_range=[minid,'FSN268504'],max_id='FSN268504',new_asset_ids=0,catalog_sha256=c['catalog_sha256'],source_counts=c['source_counts'],extraction=dict(ISO_files=2738,FPK_archives=542,FPK_payloads=6558),models=dict(logical=842,unique_GMO=341,static_GLB=341,source_transform_nodes=4059,weighted_joints=2642),textures=dict(logical=6290,unique_PNG=2371),audio=dict(logical=5537,VAG_ATRAC_logical=3576,VAG_ATRAC_unique_FLAC=2117,bank_stream_logical=1961,bank_unique_FLAC=1623,PPHD_banks=43,bank_empty_slots=17),video=dict(PMF=5,MP4=5),MOT=dict(files=54,offset_slots=15440,decoded_clips=3676,channels=198831,key_values=2044587,runtime_validated_single_clips=9,unvalidated_single_clips=3667),animation=dict(status='FUC_ANIMATION_RUNTIME_VALIDATION_PASS',models=3,clips=9,raw_runtime_frames=45,raw_node_comparisons=2535,raw_max_error=0,threejs_frames=286,threejs_node_comparisons=16357,threejs_max_error=1.0312226656431639e-6),semantic=dict(status='FUC_MOVE_COMMAND_SEMANTIC_MAPPING_PASS',internal_identities=20,playable_roster_count=None,runtime_UI_characters=['lan','sir','rin'],Move_subjects=611,ROM_states=352,Command_rows=1231,UI_entries=262,bound_UI_entries=3,unbound_UI_entries=259,actual_return_bank_clip_anchors=3,request_candidates=5,resource_graph_edges=1655,confidence_field_occurrences=sem['confidence_field_occurrences'],confidence_unit=sem['confidence_count_unit'],dangling_references=0),Replay=dict(status='FUC_LAN_CLIP145_FULL_BATTLE_REPLAY_PASS',episode='lan145_93c825fbc10749e7',frames=83,maximum_matrix_error=1.0482635468432241e-6,visibility_mismatches=0,audio_asset='FSN260985',scope='one runtime-authoritative same-Episode final-pose replay; not universal raw animation/blend'),unknowns=matrix,known_limitations=[r['unknown'] for r in matrix],unknown_impact=dict(BLOCKING=0,NON_BLOCKING=sum(r['development_impact']=='NON_BLOCKING' for r in matrix),ON_DEMAND=sum(r['development_impact']=='ON_DEMAND' for r in matrix)),major_indexes=indexes,Golden_hashes=hashes,complete_pre_baseline=snap(WORK/'BASELINE.json'),final_stability=checks['FINAL_STABILITY_GATE'],audit_status={n:x['status'] for n,x in checks.items()},tools=snap(MD/'FUC_FINAL_TOOL_MANIFEST.json'),reports=[snap(L/'Reports'/n) for n in ['FUC_FINAL_REPORT.md','FUC_USAGE_GUIDE.md','FUC_OPTIONAL_CLEANUP_CANDIDATES.md']],gallery_entry=snap(L/'Gallery/FUC_INDEX.html'),deletion_actions=0,new_runtime_capture=0)
    fp=EU/'Metadata/FUC_FINAL_MANIFEST.json';assert not fp.exists(),'Never overwrite an existing final manifest';write(fp,manifest)
    # Resolve every visible entry link after final documents exist, before freeze marker.
    page=(L/'Gallery/FUC_INDEX.html').read_text('utf-8');targets=re.findall(r'href="([^\"]+)"',page);bad=[]
    for target in targets:
        path=(L/'Gallery'/urllib.parse.unquote(target.split('?')[0])).resolve()
        if not path.is_file():bad.append(dict(link=target,path=str(path)))
    assert not bad,bad
    marker=dict(status=FSTATUS,research_status=CSTATUS,timestamp=timestamp,source_version='FateUnlimitedCodesPortable_Europe',asset_count=21899,unified_asset_count=268504,max_id='FSN268504',new_asset_ids=0,catalog_hashes=c['catalog_sha256'],final_manifest=snap(fp),final_report=snap(L/'Reports/FUC_FINAL_REPORT.md'),usage_guide=snap(L/'Reports/FUC_USAGE_GUIDE.md'),known_unknown_matrix=snap(MD/'FUC_FINAL_KNOWN_UNKNOWN_MATRIX.csv'),semantic_status='FUC_MOVE_COMMAND_SEMANTIC_MAPPING_PASS',runtime_status='CLOSED FOR MOD DEVELOPMENT',validated_single_clip_count=9,replay_status='FUC_LAN_CLIP145_FULL_BATTLE_REPLAY_PASS',audit_gates=manifest['audit_status'],known_unknowns_do_not_reopen_research=True)
    marker['entry_links_checked']=len(targets);marker['missing_entry_links']=0
    mp=EU/'FUC_FROZEN_FOR_MOD_DEVELOPMENT.json';assert not mp.exists(),'Do not replace an existing freeze';write(mp,marker)
    for p in [L/'Reports/FUC_FINAL_REPORT.md',L/'Reports/FUC_USAGE_GUIDE.md',L/'Reports/FUC_OPTIONAL_CLEANUP_CANDIDATES.md',MD/'FUC_FINAL_KNOWN_UNKNOWN_MATRIX.csv',MD/'FUC_FINAL_TOOL_MANIFEST.json',MD/'FUC_LONG_TERM_ARTIFACTS.json',fp,mp]:shutil.copy2(p,OUT/p.name)
    # Light archive: indexes/proof/scripts only. No ISO, Raw, GLB, media or full traces.
    selected={pathlib.Path(r['path']) for r in read(MD/'FUC_FINAL_TOOL_MANIFEST.json')['tools'] if pathlib.Path(r['path']).parent==SCRIPTS}
    package=[]
    for p in (EU/'Metadata').rglob('*'):
        if p.is_file() and not p.name=='ASSETS.jsonl' and p.suffix in ['.csv','.json']:package.append((p,'Library/'+p.relative_to(L).as_posix()))
    for p in selected:package.append((p,'Tools/scripts/'+p.name))
    for p in [L/'Reports/FUC_FINAL_REPORT.md',L/'Reports/FUC_USAGE_GUIDE.md',L/'Reports/FUC_OPTIONAL_CLEANUP_CANDIDATES.md',L/'Reports/FUC_FINAL_FREEZE_PRE_BASELINE.json',L/'Gallery/FUC_INDEX.html',mp]:package.append((p,'Library/'+p.relative_to(L).as_posix()))
    zip_path=OUT/'FUC_FINAL_INDEXES_AND_TOOLS.zip'
    assert not zip_path.exists()
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p,name in sorted(package):z.write(p,name)
        z.writestr('README.txt','FUC FINAL FREEZE: indexes / reports / selected tool sources only. Not a full asset backup. Original paths and hashes remain in manifests. Preserve Library Raw/Converted, WORK runtime evidence and whole runtime/vendor directories separately. No tools were installed or executed from this package.\n')
    with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None;members=len(z.infolist())
    write(OUT/'FUC_FINAL_PACKAGE_INTEGRITY.json',dict(status='PASS',package=snap(zip_path),members=members,scope='light index/proof/script archive; not a full preservation backup'))
    log('FINAL',FSTATUS,CSTATUS,'PACKAGE',zip_path.stat().st_size,'MEMBERS',members)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['prepare','finalize']);a=ap.parse_args();globals()[a.mode]()
