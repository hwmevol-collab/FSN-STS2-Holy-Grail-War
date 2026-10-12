from fuc_common import *
ROOT=FW/'source_diagnostic'
OUTPUT=pathlib.Path('C:/Users/Murasame/Documents/Codex/2026-10-06/files-pasted-by-the-user-fate-2/outputs')
def available(name):
    p=ROOT/name
    return readjson(p) if p.exists() else {'status':'NOT_COMPLETED'}
def countcsv(name):
    p=ROOT/name
    return len(readrows(p)) if p.exists() else 0
def run():
    source=readjson(ROOT/'SOURCE_DIAGNOSTIC.json');base=readjson(BACK/'BASELINE.json');verify=available('STABILITY_VERIFICATION.json');fpk=available('FPK_EXTRACTION_SUMMARY.json');models=available('MODEL_SUMMARY.json');textures=available('TEXTURE_SUMMARY.json');motion=available('MOTION_SUMMARY.json');audio=available('AUDIO_SUMMARY.json');game=available('GAME_DATA_SUMMARY.json');cross=available('CROSS_SOURCE_SUMMARY.json');tools=available('TOOLS_AUDIT.json')
    assert models.get('status')!='NOT_COMPLETED' and textures.get('status')!='NOT_COMPLETED' and audio.get('status')!='NOT_COMPLETED','Wait for authorized recoverable work to finish before final report'
    assert sha(SRC)==source['source_sha256'] and SRC.stat().st_size==source['actual_zip_bytes'],'Source changed; investigate before reporting'
    files=readjson(ROOT/'PARTIAL_ISO_FILESYSTEM_INVENTORY.json');missing=[r for r in files if not r['complete_extent']];missingcounts=dict(collections.Counter(pathlib.Path(r['logical_path']).suffix for r in missing));csvwrite(ROOT/'MISSING_FILES.csv',missing)
    workfiles=list(ROOT.rglob('*'));workbytes=sum(p.stat().st_size for p in workfiles if p.is_file());disk=shutil.disk_usage('E:/')._asdict()
    status=dict(created_at=now(),result='FSN_FUC_MASTER_ASSET_INTEGRATION_PARTIAL',execution_status='SOURCE_BLOCKED_WORK_RECOVERED_NOT_INTEGRATED',reason='ZIP truncated; missing compressed tail and central directory. The full ISO CRC/SHA256 cannot be verified.',source=source,baseline_total=base['total_assets'],catalog_added=0,catalog_after=246605,first_reserved_next_id='FSN246606',fpk={k:v for k,v in fpk.items() if k not in {'containers','magic_clusters'}},models=models,textures=textures,motions=motion,audio=audio,game_data=game,cross_source=cross,missing_files_by_extension=missingcounts,protection_verification=verify,work_recovery_bytes=workbytes,disk_E=disk,required_user_input='Complete ZIP/ISO/CSO local path, or complete the original ZIP and reply',integration_completed=False,gallery_refreshed=False,gallery_browser_regression_performed=False)
    jsonwrite(L/'Reports/FUC_INTEGRATION_STATUS.json',status)
    commits='\n'.join(f"- [{r['repository']}]({r['repository']}) — `{r['commit']}`" for r in tools.get('repositories',[]))
    report=f'''# Fate/unlimited codes Portable 恢复与接入报告

`FSN_FUC_MASTER_ASSET_INTEGRATION_PARTIAL`

**执行状态：SOURCE_BLOCKED_WORK_RECOVERED_NOT_INTEGRATED。正式接入尚未完成。**

本机 ZIP 在压缩数据中途截断，缺失尾部和 ZIP 中央目录。已继续处理完整可读的 FPK、模型、纹理和音频，将成果保留在 WORK；未给它们分配正式 FSN asset_id，未追加统一 Catalog，未改 Gallery。本报告不能作为全库集成 PASS。

## A. ROM Identity

- 本机可读 PARAM.SFO：DISC_ID=`ULJM05451`，TITLE=`Fate/unlimited codes PORTABLE`，DISC_VERSION=`1.00`，PSP_SYSTEM_VER=`5.03`。
- UMD metadata：`ULJM-05451|A7BFCD7094DD5726|0001|G...`。两个本机字段共同支持日版身份；没有套用欧美版 hash/地址。
- ZIP：`{SRC}`；实际 {source['actual_zip_bytes']:,} bytes；SHA-256 `{source['source_sha256']}`。
- Local ZIP header 内 ISO 文件名：`{source['local_header_filename']}`；声明解压长度 {source['declared_iso_bytes']:,} bytes、压缩长度 {source['declared_compressed_bytes']:,} bytes、CRC32 `{source['declared_crc32']}`。
- 压缩数据起点 {source['data_offset']}；实际可读 {source['available_compressed_bytes']:,} bytes；缺少 **{source['missing_compressed_bytes']:,} bytes**，尚不含 ZIP 中央目录和结尾记录。
- Deflate EOF=`{source['deflate_stream_eof']}`。Recovered prefix={source['recovered_prefix_bytes']:,} bytes；它不是完整 ISO，不能计算或宣称完整 ISO SHA-256/CRC 已验证。
- Prefix SHA-256 `{source['prefix_sha256']}`，只标识恢复前缀。

## B. Filesystem

实际读取 ISO9660 PVD 与完整目录树，共列出 {source['filesystem_files_listed']:,} 文件条目。每个目录记录的大小和 LBA 均校验 LE/BE 双份字段。

- 可读完整文件 extents：{source['complete_file_extents']:,}；在 WORK 中保存 {source['complete_extent_bytes']:,} bytes。
- 不完整/缺失：{source['incomplete_file_extents']:,}，扩展名统计 `{json.dumps(missingcounts,ensure_ascii=False)}`。
- 文件清单：`{ROOT/'PARTIAL_ISO_FILESYSTEM_INVENTORY.csv'}`；缺失清单：`{ROOT/'MISSING_FILES.csv'}`。
- 全部恢复文件带 `UNVERIFIED_ROM_PREFIX` 来源状态；extent 完整不等于完整 ROM CRC 已验证。

## C. Containers

全部 **{fpk.get('container_count',0)} 个 FPK** 位于可读范围；逐包完成提取，共声明/保存 **{fpk.get('declared_entries',0):,}/{fpk.get('extracted_entries',0):,} 条目**，包括零字节占位。

索引保存原 container、原 entry name、entry index、offset、compressed/uncompressed size、archive integrity word、output SHA-256 与 magic。不同包各用独立目录，未覆盖同名资源。

共 {fpk.get('strict_prs_crosschecked_entries',0):,} 个首/末/最大条目进行独立严格 PRS 对照，要求实际产生声明长度，哈希与工具输出一致。所有 WORK FPK 输入前后 hash 相同。

FPKCodes 的两个本机限制已确认并处理：压缩长度等于原始长度的 raw 条目需直接复制；部分原始 entry name 首部被截短并以 `/` 起头，WORK 输出只去除路径根前缀，索引保留原名。不对其恢复不存在的名称。

TTD 内嵌 TIM2 已进行结构/边界验证与提取。声音 PBD/PHD/PEF、其他自定义格式仍保留未知索引。PSP UPDATE/DATA.BIN 的 PSAR 更新资源仅保存原 bytes，未运行系统更新或解析更新程序。

## D. Tools

{commits}

- 两个 FPKCodes README、extract/rebuild 源码和 PRS 源码已审计。上游 rebuild/integrity-check/fix-ISO 均未调用。
- Noesis 4.474 官方包：SHA-256 `{tools.get('noesis',{}).get('archive_sha256','')}`；使用内置 GMO/TIM2 handler。
- 命令：`Noesis64.exe ?cmode <input> <output.gltf|output.png>`。Noesis 的 `.glb` 扩展是另一个导出器，早期探测文件保留为失败格式证据，不属于成功 GLB。正式 WORK 模型由 glTF 2.0 无几何改动打包成 GLB 2.0。
- vgmstream `{tools.get('vgmstream',{}).get('release','')}` 官方 CLI，包 SHA-256 `{tools.get('vgmstream',{}).get('archive_sha256','')}`，用于本机 VAG 解码。命令：`vgmstream-cli.exe -m -I <input.vag>` 和 `-i -o <temporary.wav> <input.vag>`。按真实 VAG header data_size/16*28 校验 mono/sample count。
- FFmpeg：`{tools.get('libraries',{}).get('ffmpeg_version','')}`；用于 ATRAC3 与 PCM->FLAC，FLAC 转换后完整解码复核。其 native VAG demuxer 将 version=4 当成 stereo，不适用于本机这些 mono VAG；早期 FFmpeg VAG 输出全部由 vgmstream 重新替换，未计入最终有效 Working Copy。
- pycdlib 1.21.0 已安装在现有 WORK 隔离 Python；本次截断目录调查使用读取实际目录 extents 的诊断脚本。
- Recomp 公开准备流程支持 NPEH00007 1.01，未将其固定 EU hash/offset 用到日版。其 battle map 有 provisional/unwired 动画字段，无现成 FUC MOT/FAN/AMO 离线解析器可直接复用。
- UnlimitedCodes-HD 只下载 README、textures.ini、tree、commit 元数据；未下载或混入第三方替换图。所有外部命名证据标为 `external_reference`，日版 runtime texture hash 映射未建立。
- PPSSPP 未使用，用户现有配置未读取或修改。日版 BOOT.BIN 已是可读 ELF，无须 EBOOT 解密。

## E. Models

- 所有 {models.get('logical_models',0)} GMO 原文件具有 `OMG.00.1PSP` magic，完整保留于 WORK FPK 提取层。
- 按 SHA 去重 {models.get('unique_models',0)}；转换 {models.get('converted_unique_models',0)}，失败 {models.get('failed_unique_models',0)}。
- 内部路径分布：chr=148，eft=662，stg=32。它们是逻辑资源条数，不能等同于可玩角色数。
- GLB 2.0 检查 bufferViews/accessor 范围、mesh/indices、materials/images、skin bind accessor 与 JOINTS_0/WEIGHTS_0。
- 模型索引：`{ROOT/'MODEL_INDEX.csv'}`，含 vertex/index/mesh/material/texture/bone/animation count 和 bbox。
- 这里只通过结构检查；未做逐模型渲染与游戏等价验证。

## F. Skeleton

保留 GLB 内骨骼层级、名称、父关系、node transform、inverse bind matrices 与蒙皮权重；SKELETON_INDEX 保存 {models.get('bone_rows',0):,} 骨骼行。Noesis 导出可能为刚体/特效建立单 root skin，不能把所有带 skin 的模型解释为战斗角色。

`{ROOT/'SKELETON_INDEX.csv'}`。角色绑定/多模型共用 skeleton 的完整语义尚未确认。

## G. Animations

- MOT 原文件 {motion.get('mot_files',0)}，54/54 头部和 BE offset table 通过本机边界校验。
- 表槽 {motion.get('table_slots',0):,}，非空候选 motion slice **{motion.get('nonempty_candidate_clip_slices',0):,}**，保存编号/offset/size/hash；每个槽单独索引。
- **motion 通道已解析=0，播放验证=0**；这些候选 slices 不是已验证可播放 animation clip。
- AMO={motion.get('amo_files',0)}，FAN={motion.get('fan_files',0)}，raw 保留；骨骼绑定、fps、frame count、循环、动作语义、事件/特效/声音时序仍 unknown。
- GMO 自带导出 animation={models.get('embedded_animation_count',0)}。未生成动画预览。
- 索引：`{ROOT/'ANIMATION_INDEX.csv'}`；不猜 Excalibur 或具体 move 名。

## H. Textures

- TTD raw 完整保留；TIM2 结构校验解析失败 {textures.get('parse_failures',0)}。
- 逻辑 TIM2 图片 {textures.get('logical_texture_pictures',0):,}；独立 payload {textures.get('unique_tim2_files',0):,}。
- PNG Working Copy {textures.get('converted_unique_png',0):,}；失败 {textures.get('failed_unique_png',0)}；实际 PNG 可完整解码，alpha 通道保留。
- TIM2 palette、image type、mip count、GS/header bytes、嵌入 offset 均保存。没有根据 PSP 平台额外假定 swizzle。
- GMO 自带纹理随 Noesis 模型导出，嵌入 GLB；其 PNG 辅助文件保留在各 model hash 目录。
- `{ROOT/'TEXTURE_INDEX.csv'}`。

## I. Effects

真实 `eft/` 路径资源 **{countcsv('EFFECT_INDEX.csv'):,} 条**，含 GMO、TTD、BAM、TUV、MIL、PAR 等。原 bytes 保存；图片/模型可转换部分已处理。

自定义 timeline/command/trigger 与模型、纹理、音频之间的 bindings 尚未可靠解析。未凭视觉猜宝具特效名称。`{ROOT/'EFFECT_INDEX.csv'}`。

## J. Stages

真实 stg 路径索引 **{countcsv('STAGE_INDEX.csv')} 条**，其中 32 个逻辑 GMO；模型/纹理按上述流程处理，stage semantic name 保留 unknown。`{ROOT/'STAGE_INDEX.csv'}`。

## K. 2D Assets

已保存/转换 chrsel、extra、game、logo、mission、nextstg、rank、result、title、vs、story 等 FPK 的 TTD/TIM2 图片。原路径和容器可检索。2D 页面切片、字体 glyph metrics 与完整 UI 语义还未解析。

图片在 WORK，可用于后续复核；本轮未加入统一 thumbnail/Contact Sheet/Gallery，原 Gallery 内容保持冻结。

## L. Audio

- 完整可读 VAG/AT3 逻辑文件 {audio.get('available_logical_audio',0):,}；独立 payload {audio.get('unique_audio',0):,}。
- FLAC 主 Working Copy成功 **{audio.get('converted_unique_flac',0):,}**，失败 **{audio.get('failed_unique_audio',0)}**；每个成功文件做全长解码检查，VAG 声道/样本数/时长按成熟专用 decoder 与原 header 对照，原 VAG/AT3 bitstream 保留。临时 WAV 转 FLAC 后移除。
- Codec统计 `{json.dumps(audio.get('codecs',{}),ensure_ascii=False)}`；每个文件记录 duration/sample_rate/channels/hash。
- 截断导致 {audio.get('missing_loose_vag_extents',0):,} 个 loose VAG extent 未完整到达；部分可能与 FPK 内语音重叠，但未证明全量替代，不能宣称音频全库恢复。
- PBD/PHD/PEF 声音 bank（各43个）尚未恢复 SE 独立条目。
- `{ROOT/'FUC_AUDIO_INDEX.csv'}`、`{ROOT/'FUC_VOICE_INDEX.csv'}`；角色只记录 filename code，move/action 为空。

## M. Game Data

日版 BOOT.BIN 是未加密 ELF，SHA-256 `{game.get('boot_elf_sha256','')}`。已索引 **{game.get('indexed_ascii_candidate_strings',0):,}** 条资源/角色/command 等 ASCII 字符串候选及真实文件 offset。

没有把这些字符串提升为已解析 move/attack/command 表；日文脚本编码和数据结构、roster playable 状态、damage/meter/unlock 表尚未解析。`{ROOT/'FUC_GAME_DATA_INDEX.csv'}`。

## N. Unknown

`FUC_UNKNOWN_FORMATS.csv` 保存 {countcsv('FUC_UNKNOWN_FORMATS.csv'):,} 条未解析自定义 payload，含 hash、magic、first64、sample entropy、cluster、原始路径。UNKNOWN_CLUSTERS 按总 bytes 排序；最高优先级包括 MOT、PBD、SEQ、BAM/PAR 等。MOT 候选边界解析不改变其 motion 语义仍未知的状态。

## O. Cross-source

读取现有 246,605 资产的 Preservation/Working SHA 比较 {cross.get('recovered_fpk_payloads_compared',0):,} FPK payload。排除零字节占位后 exact_payload 关系 {cross.get('exact_payload_relations',0)}；GMO `{cross.get('fuc_unique_model_rows',0)}` 条可标记 FUC_unique（旧 Catalog 无 GMO）。

Perceptual image/audio similarity 未运行；无未经验证的 confirmed similarity。`{ROOT/'FSN_VS_FUC.csv'}`。

## P. Integration

| 项目 | 结果 |
|---|---:|
| before | 246605 |
| added | 0 |
| after | 246605 |
| old IDs preserved | 246605 |
| missing old ID | {verify.get('missing_old_id','unverified')} |
| changed old rows | {verify.get('changed_old_rows','unverified')} |
| old raw path loss | {verify.get('old_raw_path_loss','unverified')} |
| old working path loss | {verify.get('old_working_path_loss','unverified')} |
| old thumbnail loss | {verify.get('old_thumbnail_loss','unverified')} |
| source modified/deleted/added | 0 / 0 / 0 |
| SQLite integrity_check | {verify.get('sqlite_integrity','unverified')} |

CSV/JSONL/SQLite 和 Gallery code 的原 SHA 均保持一致；{verify.get('protected_paths_checked',0):,} 个受保护路径无丢失、大小或 modification time 变化。正式 FUC 起始 ID 仍应为 FSN246606，但本次没有分配。

冻结基线：`{L/'Reports/FUC_PRE_INTEGRATION_BASELINE.json'}`。轻量备份：`{BACK}`；备份索引/code/reports {base['backup_bytes']:,} bytes，不复制旧 RawExtracted 或 Working Copy。现有 Original/Remastered/FHA 未重新提取；FHA 4 条旧 checksum 例外未改动。

## Q. Gallery

旧 Gallery catalog/index/contact_sheets 页面文件 SHA 未改动，仍有 246,605 arrays。**本轮没有 Gallery refresh、FUC filter、localhost 浏览器回归，因此对应验收项未满足。**

这里的旧路径保护检查不能替代要求的浏览器图片/音频/视频播放测试。正式接入完成后才能进行整套 localhost 回归。

## R. Disk

冻结前 E 可用 {base['disk_E']['free']:,} bytes；当前 {disk['free']:,} bytes。WORK 恢复目录逻辑占用约 {workbytes:,} bytes（不包含轻量备份与工具）。模型按 SHA 去重341份 GLB；TIM2 2350份独立 PNG；音频1579份独立 FLAC，避免同一来源同时生成多种主格式。中间 glTF/buffer 在成功 GLB 打包后移除。

## S. Failures

1. **实质阻塞：源 ZIP 缺 204,134,110 bytes 压缩尾部及中央目录。** 完整 ISO CRC/hash、1,525 文件 extents、全部5个 PMF不可恢复。保留原截断 ZIP 未修改；不能声称完整 ROM bytes 已保留。
2. 全部 FPK 的可读压缩 payload 已恢复并检查，但它们来源仍是不能进行完整 ROM CRC验证的 prefix。
3. MOT 仅 offset table/candidate slices；FAN/AMO 和动画通道/绑定尚未可靠解析。motion raw 完整保留在已读 FPK 中；需独立 parser/可执行文件读取逻辑研究，并与已恢复 skeleton 对照。
4. SE bank PBD/PHD/PEF、自定义 effects timeline、SEQ/game data 和字体 metrics 未解析；它们有 UNKNOWN 清单，未忽略。
5. 全量统一 Catalog/参考索引/Contact Sheet/Gallery 与 localhost 回归均未执行。本次新增 source Metadata 仅保存 ZIP诊断，不是第四正式来源完成。
6. 最初 Noesis `.glb` 探测输出格式不符，已改由 glTF2打包；错误探测文件没有加入 MODEL_INDEX 或成功计数。

继续执行所需输入：**完整 ZIP/ISO/CSO 的本机路径，或补齐当前 ZIP。** 完整源到位后先新建源修订记录并验证 CRC/ISO身份，对比本次所有完整 extents/hash，补齐尾部；再推进动画/SE/effect/game-data 解析，进行追加式集成与 Gallery 回归。现有冻结基线和旧 IDs 保持不变。

复现入口：`{W/'scripts/FUC_ASSETS.ps1'}`。`-Phase RecoverAvailable` 重跑 WORK恢复，已验证文件可复用；`-Phase All` 对不完整源明确报错，不伪造成功。目前脚本尚未实现正式 integration 分支，需在完整源后继续实现。

## T. Recommended next step

本轮后可建议 Official Material 页面索引 / Animation Reference Index / Semantic Catalog；本轮未开始它们。当前先解决 S 中的完整源与未解析格式。
'''
    target=L/'Reports/FUC_INTEGRATION_REPORT.md';target.write_text(report,encoding='utf-8');OUTPUT.mkdir(parents=True,exist_ok=True);shutil.copy2(target,OUTPUT/'FUC_INTEGRATION_REPORT.md');shutil.copy2(L/'Reports/FUC_INTEGRATION_STATUS.json',OUTPUT/'FUC_INTEGRATION_STATUS.json');shutil.copy2(ROOT/'MISSING_FILES.csv',OUTPUT/'FUC_MISSING_FILES.csv')
    log('REPORT SAVED',target,'OUTPUT',OUTPUT)
if __name__=='__main__':run()
