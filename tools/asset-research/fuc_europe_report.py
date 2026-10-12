"""Evidence-backed final A-T report; does not allocate IDs or alter payloads."""
from fuc_common import *
from fuc_europe_index import EU

OUT=pathlib.Path('C:/Users/Murasame/Documents/Codex/2026-10-06/files-pasted-by-the-user-fate-2/outputs')
FINAL_STATUS='FSN_FUC_MASTER_ASSET_INTEGRATION_PARTIAL'

def footprint(roots,extra=()):
    files=[]
    for root in roots:
        for parent,dirs,names in os.walk(root,followlinks=False):
            files.extend(pathlib.Path(parent)/n for n in names)
    files.extend(extra)
    files=list(dict.fromkeys(p for p in files if p.is_file()))
    unique={};logical=0
    for p in files:
        st=p.stat();logical+=st.st_size;unique[(st.st_dev,st.st_ino)]=st.st_size
    return dict(path_count=len(files),logical_path_bytes=logical,unique_file_id_count=len(unique),unique_file_id_bytes=sum(unique.values()),meaning='File-length footprint deduplicated by Windows file ID inside the listed new library paths. Not NTFS allocated clusters and not incremental physical usage: some files are hardlinked to preexisting WORK objects.')

def run():
    md=EU/'Metadata';load=lambda n:readjson(md/n)
    identity=load('SOURCE_IDENTITY.json');index=load('INDEX_COMPLETE.json');commit=load('INTEGRATION_COMMIT.json');stable=load('STABILITY_VERIFICATION.json')
    model=load('MODEL_SUMMARY.json');motion=load('MOTION_SUMMARY.json');texture=load('TEXTURE_SUMMARY.json');audio=load('AUDIO_SUMMARY.json');banks=load('SOUND_BANK_SUMMARY.json');game=load('GAME_DATA_SUMMARY.json');semantic=load('SEMANTIC_COVERAGE_SUMMARY.json');cross=load('CROSS_SOURCE_SUMMARY.json');jpcompare=load('JAPAN_RECOVERY_COMPARISON_SUMMARY.json');prs=load('FPK_FULL_INDEPENDENT_VERIFICATION.json');tools=load('TOOLS_AUDIT.json')
    browser=readjson(L/'Reports/FUC_GALLERY_REGRESSION.json');previews=readjson(L/'Reports/FUC_LEGACY_VIDEO_PREVIEWS.json');baseline=readjson(BACK/'BASELINE.json');jp=readjson(FW/'SOURCE_ZIP_BASELINE.json');assets=rowsjson(md/'ASSETS.jsonl')
    assert commit['status']=='COMMITTED' and stable['after']==268504 and stable['old_ids_preserved']==246605 and stable['changed_old_rows']==stable['missing_old_id']==0
    assert motion['decoded_clips']==motion['nonempty_clips']==3676 and motion['failed_clips']==0 and prs['strict_independent_entries_verified']==6558 and not prs['failures']
    assert browser['status']=='IAB_REPRESENTATIVE_REGRESSION_PASSED_CHROME_UNVERIFIED' and len(previews)==16 and all(r['status']=='MP4_PREVIEW_FULL_DECODE_VALIDATED_PRESERVATION_UNCHANGED' for r in previews)
    binding_candidates=len(readrows(md/'ANIMATION_MODEL_BINDING_CANDIDATES.csv'));font_candidates=len(readrows(md/'FONT_INDEX.csv'))
    fpks=[r for r in assets if r['asset_kind']=='fpk_payload'];extcounts=collections.Counter(r['extension'] for r in fpks)
    stage_gmo=sum(r['detected_format']=='GMO' and r['category']=='Stages' for r in fpks)
    two_d=[r for r in fpks if r['source_logical_path'].startswith('2d/')]
    animation_codes=sorted({r['character_code'] for r in assets if r['asset_kind']=='mot_clip' and r['character_code']})
    roots=[EU,L/'Canonical/FateUnlimitedCodesPortable_Europe',L/'Gallery/contact_sheets/FateUnlimitedCodesPortable_Europe',L/'Gallery/video_previews']
    disk=footprint(roots,list((L/'Gallery/thumbnails').glob('fuc_eu_*')))
    usage=shutil.disk_usage('E:/');disk.update(observed_at=now(),baseline_free_bytes=baseline['disk_E']['free'],current_free_bytes=usage.free,drive_used_increase_since_frozen_baseline=baseline['disk_E']['free']-usage.free,backup_bytes=baseline['backup_bytes'],scope_roots=[str(p) for p in roots],scope_extra='Gallery/thumbnails/fuc_eu_*',drive_difference_scope='Entire E: drive, including backups/research/WORK/tools and unrelated concurrent activity; not attributed solely to formal Europe assets')
    jsonwrite(md/'DISK_FOOTPRINT.json',disk);jsonwrite(L/'Reports/FUC_DISK_FOOTPRINT.json',disk)
    gallery=load('GALLERY_COMMIT.json');gallery['runtime_browser_verification']=browser['status'];gallery['runtime_evidence_path']=str(md/'GALLERY_REGRESSION.json');jsonwrite(md/'GALLERY_COMMIT.json',gallery)
    fmt=lambda n:f'{n:,}'
    gib=lambda n:f'{n/(1024**3):.3f} GiB'
    link=lambda name,root=md:f'[{name}](<{(root/name).as_posix()}>)'
    table='\n'.join(f'| {k} | {fmt(v)} |' for k,v in index['kinds'].items())
    categories='\n'.join(f'| {k} | {fmt(v)} |' for k,v in index['categories'].items())
    repolinks='\n'.join(f"- [{r['repository'].removeprefix('https://github.com/')} @ {r['commit'][:12]}]({r['repository']}/tree/{r['commit']})" for r in tools['repositories'])
    jpc=jpcompare['counts'];nowtext=now()
    report=f'''# Fate/unlimited codes Portable Europe：提取、研究与增量接入报告

生成时间：{nowtext}。正式来源：`FateUnlimitedCodesPortable_Europe`。

**最终状态：`{FINAL_STATUS}`**。

完整欧版源、全量 ISO 文件、全部 FPK 条目已保存并接入。统一库从 **246,605 → 268,504**，新增 **21,899** 条逻辑资产；旧编号与旧字段值零变更。341 个唯一 GMO 已转为标准 GLB；54 个 MOT 的 3,676 个非空片段已解码全部运动通道。仍未证实 MOT 与 GMO 骨骼绑定、插值和旋转解释，也未完成动画实际播放、FAN/AMO 与 VFX 时序及角色／招式表语义验证，因此不输出 PASS。

截断日版所有已恢复内容独立保留，未获得统一 Catalog 编号。以后取得完整日版时以 `FateUnlimitedCodesPortable_Japan` 单独追加，不重排欧版或旧 FSN/FHA 编号。

## A. ROM Identity

| 项目 | 欧版实测结果 |
| --- | --- |
| 输入 | `{identity['source']}` |
| source_version | `{identity['source_version']}` |
| 源长度 | {fmt(identity['size'])} 字节 |
| SHA-256 | `{identity['sha256']}` |
| PARAM.SFO DISC_ID | `{identity['PARAM_SFO']['DISC_ID']}` |
| DISC_VERSION | `{identity['PARAM_SFO']['DISC_VERSION']}` |
| TITLE / PSP_SYSTEM_VER | `{identity['PARAM_SFO']['TITLE']}` / `{identity['PARAM_SFO']['PSP_SYSTEM_VER']}` |
| UMD_DATA 开头 | `NPEH-00007` |
| 文件范围 | 全部 2,738 个文件 extent 位于完整 ISO 范围内 |

身份、文件系统和 SHA-256 均先于正式提取确认。只读取用户 ISO；库内保存独立 ISO 副本。接入后再次检查输入的 SHA-256、长度和修改时间，全部一致。{link('SOURCE_IDENTITY.json')}、{link('SOURCE_INVENTORY.csv')}。

日版 ZIP 实际 {fmt(jp['size'])} 字节，SHA-256 `{jp['sha256']}`；中央目录缺失，声明的压缩数据无法完整容纳。日版恢复 SFO 为 `ULJM05451`，ISO 前缀恢复 445,467,099 字节，SHA-256 `9a21a56f78d0c16608bd23f874f41314ea929deca53cf96d9afaf08de5cac95c`。其 542 个已恢复 FPK、模型、纹理、音频及早期 MOT 研究完整保留在 `E:/FSN_MASTER_ASSET_WORK/fuc/Japan_Recovery`。旧 `source_diagnostic` 仅为指向该区域的兼容目录联接。旧通用 `FateUnlimitedCodesPortable` 区域只保留诊断资料，不是本轮正式来源；日版恢复的统一资产数为 **0**。日本 ZIP 接入后哈希、长度和修改时间也未改变。

## B. Filesystem

全量清点并提取 **2,738** 个 ISO 文件：542 FPK、2,078 VAG、39 AT3、5 PMF、62 PRX、6 BIN、2 PNG、2 SFO、1 LST、1 TXT。所有 extent 有源偏移、长度、SHA-256；无欧版缺失 extent。

`RawExtracted/ISO` 保存整盘，`RawExtracted/Loose` 保存目录内容，`RawExtracted/Executable` 保存原始可执行数据。元数据中 `PARTIAL_ISO_FILESYSTEM_INVENTORY.json` 是沿用旧脚本接口的文件名，欧版每项 `complete_extent=true`，状态为完整源；该名字不代表欧版截断。{link('SOURCE_INVENTORY.json')}、{link('NON_FPK_CONTAINER_INVESTIGATION.csv')}。

## C. Containers

**全部 542 FPK，全部 6,558 条 payload 成功提取，独立严格校验 6,558/6,558，失败 0。**

真实 FPK 结构为小端头部／目录，目录项保存原始 36 字节名称与 offset、compressed_size、uncompressed_size。压缩分支采用 Eighting PRS 的 MSB-first 标志位与反向引用；两长度相等的条目按原始字节分支处理。独立解码器要求完整输出声明长度，并逐项比较 SHA-256，避免上游零填充／裁剪行为把未解出的字节伪装成成功。{link('FPK_FULL_INDEPENDENT_VERIFICATION.json')}、{link('FPK_EXTRACTED_INDEX.csv')}。

FPK 内的 TTD/TIM2、GMO、MOT、PPHD/PBD、声音和 VFX／游戏数据均继续调查。PPHD/PBD 成对音频容器已解出 43 个 bank。非 FPK 的 BIN/PRX 等 68 个可执行／数据对象有单独调查表；未识别为通用 archive 的对象完整保留，未强行使用其他游戏的解包器。FPK 最前 4 字节的完整性字段含义尚未知，未进行重打包或修复 ISO。部分源名称本身缺首字符或以斜杠开头，逻辑名称原样保留，只对写出路径做安全规范化。

## D. Tools

审计并复用的公开源版本：

{repolinks}

MOT 通道研究参考 [NicholasMoser/GNTool @ {tools['motion_parser']['commit'][:12]}](https://github.com/NicholasMoser/GNTool/tree/{tools['motion_parser']['commit']}) 的 `BoneAnimation.java`、`Coordinate.java`、`TrackFlag.java`，再对本机 FUC 的全部片段做边界与原字节重编码验证；未引入其他游戏动作名称。

- [Noesis 官方](https://www.richwhitehouse.com/index.php?content=inc_projects.php&showproject=91) **4.474**：内置 GMO/TIM2 读取器，GMO → glTF 2.0 → 自行封装标准 GLB 2.0；TIM2 → PNG。未把 Noesis 的其他 `.glb` 导出格式当作标准 GLB。
- [PPSSPP 官方](https://www.ppsspp.org/files/1_20_4/ppsspp_win.zip) **1.20.4**：独立 portable/memstick，用官方 DumpFileTypes 取得欧版 EBOOT ELF，不访问既有模拟器配置和存档。dump 长度 2,000,320，SHA-256 `{game['eboot_elf_sha256']}`。
- [vgmstream r2117](https://github.com/vgmstream/vgmstream/releases/tag/r2117)：VAG、AT3 和 [PPHD/PBD 元数据](https://github.com/vgmstream/vgmstream/blob/r2117/src/meta/pphd.c)；FFmpeg/ffprobe **6.1.1** 负责 FLAC、MP4 工作副本与全流验证。
- pycdlib **1.21.0**；本机 Python、Pillow、NumPy／SciPy；自写严格 FPK、MOT、源 GMO 骨骼、GLB 封装、索引和稳定性脚本。格式调查从日版复用；只有 SHA 相同的旧转换成果才复用到欧版。

下载与可执行文件 SHA、命令、commit、局限和失败探测保存在 {link('TOOLS_AUDIT.json')}。脚本哈希表为 {link('REPRODUCIBILITY_MANIFEST.csv')}。

## E. Models

**842 个逻辑 GMO → 341 个唯一 GMO → 341 个标准 GLB，转换失败 0。** 其中 {stage_gmo} 个逻辑 GMO 属于场景路径，另 810 个归入 Models。全部唯一模型有网格、顶点／索引、材质、嵌入纹理、skin joint、权重、inverse bind matrix 和层级资料，检查 glTF accessor／buffer 范围与 GLB 2.0 封装。模型元数据保留来源路径与 SHA，`animation_count=0` 如实表示尚未绑定 MOT。

未把每个 GMO 都猜成独立角色、武器或宝具。字面含 `weapon`／`Sword` 的源子对象共有 15 个候选，仍保存为父 GMO/GLB 内组件；具体武器名称 unknown。{link('MODEL_INDEX.csv')}、{link('WEAPON_MODEL_INDEX.csv')}。Gallery 示例 `FSN250200` 显示 6 网格、71 骨骼、5 纹理及原件／GLB／模型资料链接。

## F. Skeleton

341 个唯一 GMO 的原始 chunk walker 保存 **4,059 个骨骼／变换节点**，其中 **2,642** 个节点属于加权 skin joint。补齐不参与 skin 的源节点，避免把仅含权重的列表误称为完整层级。

保存源 ordinal、名称、parent、源变换／bind 数据以及 GLB 对应节点。真实名称可直接匹配；78 个模型存在 Noesis 自动生成 `bN` 名称的情况，对应 ordinal 映射明确标为 **provisional**，不是运行时骨骼语义证明。源 chunk 解析失败 0。{link('SOURCE_BONE_INDEX.csv')}、{link('SKELETON_INDEX.csv')}。

`ber`、`sbr` 等来源代码与模型关系有实际路径证据，未据此自动命名角色或补齐名单；`cmn` 也是路径代码，不把 20 个路径代码算成 20 名可用角色。

## G. Animations

| 实际结果 | 数量 |
| --- | ---: |
| MOT 文件 | {motion['mot_files']} |
| offset table 槽位 | {fmt(motion['table_slots'])} |
| 非空／已解码片段 | {fmt(motion['nonempty_clips'])} / {fmt(motion['decoded_clips'])} |
| 完整读取通道 | {fmt(motion['channel_count'])} |
| 关键帧值原字节重编码验证 | {fmt(motion['keyframe_roundtrips'])} |
| 片段解析失败 | 0 |
| 已证实骨骼绑定／实际动画播放 | **0 / 0** |
| 结构性模型关联候选行 | {fmt(binding_candidates)} |

本轮已从仅有 offset table 推进到 **全部通道和关键帧**：MOT 头部／表和 clip 数据为大端；clip 带 playspeed、end_time 与 32 字节通道头。`flags=0x0202` 坐标为 IEEE754 float32 的高 16 位表示，低 16 位补零；不是普通 int16 归一化。时间值为大端 float32。每个非空片段均通过边界、有限数值、键值和原字节重编码检查；3,676 个原始 clip 字节与通道 JSON 均保存并分配正式 ID。

track `0x21`／`0x28`／`0x22` 的平移／旋转／缩放角色仅为参考算法提出的候选解释；`0x40` 为无坐标控制通道。FUC 中的具体骨骼索引、插值、旋转表示、runtime 混合和 loop 尚未验证，不输出 animation GLB 或伪造动作预览。`end_time` 作为源时间字段保留，未猜 FPS、动作名或循环方式。

实际 MOT 片段路径代码：`{', '.join(animation_codes)}`。同角色路径及索引范围形成 {fmt(binding_candidates)} 条 **候选**，数量不代表已绑定模型。完整表槽位保留，包括空位；空位不分配资产 ID。{link('ANIMATION_INDEX.csv')}、{link('ANIMATION_MODEL_BINDING_CANDIDATES.csv')}、{link('MOTION_SUMMARY.json')}。

**FAN {extcounts['.fan']} 个、AMO {extcounts['.amo']} 个**完整提取，语义未解。Noesis 对 MOT/AMO/FAN 的实测命令返回 0 但无输出 glTF，因此这些探测判定为未成功，而不是转换成功。{link('NOESIS_MOTION_FORMAT_PROBES.json')}。

## H. Textures

TTD 内提取 **6,290 个逻辑 TIM2 picture**，去重为 **2,371 个 TIM2**，全部生成 PNG，转换失败／结构解析失败均为 0。另有 **676** 条 GMO 内纹理视图；其 Preservation 指向完整父 GMO，PNG 是派生工作副本，不把 PNG 伪装成原始独立纹理。连同 ISO／FPK PNG，共 **6,970** 条可浏览图像。

原始 TIM2、调色板、mipmap、GS 寄存器和布局字段均保留；使用经验证的读取器，不假设所有数据都采用某种 PSP swizzle，不把有透明度的内容批量转 JPEG。新缩略图去重 2,372 个，使用独立 `fuc_eu_` 命名空间，未覆盖旧缩略图。{link('TEXTURE_INDEX.csv')}、{link('TEXTURE_RAW_INDEX.json')}。

## I. Effects

`eft/` 路径共 **2,056** 个真实 VFX 资源，原始 GMO、纹理、MOT、FAN/AMO、BAM/TUV/MIL/PAR 等组件完整保存。记录同 FPK 内纹理、模型、运动和音频的正式 ID，关系标记 `CO_CONTAINER_CANDIDATES_ONLY`。

这些候选不能证明攻击触发、宝具身份、粒子时序、blend 或声音同步。未知触发字段为空、角色／招式 unknown；未把路径相邻关系升级为宝具动画验证。{link('EFFECT_INDEX.csv')}。

## J. Stages

场景路径 **96 个主要资源**，含 {stage_gmo} 个逻辑 GMO，其可转换模型已包含于上面的 341 个唯一 GLB。纹理与模型关系保留。有 16 个数字目录代码：`001–010, 051, 052, 056, 057, 058, 060`，另有 `extra`；目录代码并不等于 17 个可游玩场景。场景真实名称与运行时拼装 unknown。{link('STAGE_INDEX.csv')}。

## K. 2D Assets

`2d/` 下 {fmt(len(two_d))} 个主要 FPK 资源及其嵌入图像已经保存、转换并进入 Catalog/Gallery。角色选择、UI、标题、结局／Gallery 等源路径保留，无法确认的图像仍为 unknown，不根据画面猜动作或故事关系。

Gallery 源路径搜索 `2d/chrsel/0000.ttd` 实测得到 27 条：原 TTD 和 26 条嵌入纹理视图。原容器、picture 索引、偏移、源 SHA 与父子 ID 均可追踪。新增 444 张 Contact Sheet；旧 8,562 行及对应路径保持可用。

## L. Audio

**5,537 条逻辑音频**：普通／嵌入音频 {fmt(audio['available_logical_audio'])} 条，以及 PPHD/PBD 子声音 {fmt(banks['logical_bank_streams'])} 条。

普通音频去重 {fmt(audio['unique_audio'])} 个，全部生成 FLAC，失败 0：唯一解码输入含 2,078 个 PSX ADPCM 和 39 个 ATRAC3。43 个 PPHD/PBD bank 有 1,961 个有效 stream、1,623 个唯一 payload+sample-rate 工作副本，全部 FLAC，失败 0。17 个空 PPVA 槽位单独记录，不假造音频资产。

FFmpeg 对 VAG version 4 的声道假设在调查中被否定；最终每个 VAG 按 vgmstream 实测 mono 元数据／样本数处理。原始 VAG/AT3、PPHD/PBD 和原始无头 ADPCM 切片均保留。PPEF 程序、音效触发时序、角色声音台词语义尚未知。Voice 只根据明确 voice 来源路径建立索引，speaker/action unknown，不编造文本。{link('FUC_AUDIO_INDEX.csv')}、{link('FUC_VOICE_INDEX.csv')}、{link('SOUND_BANK_INDEX.csv')}、{link('SOUND_BANK_EMPTY_SLOTS.csv')}。

原件完整保存 **5 PMF**，5 个 MP4 工作副本全流解码验证通过；Gallery 实际播放欧版 `FSN255896`，宽度 480，播放进度大于 0，无媒体错误。{link('VIDEO_INDEX.csv')}。视频结果在此单列以覆盖原任务要求，不改变 A–T 结构。

## M. Game Data

使用本机欧版 EBOOT 的真实 PPSSPP dump ELF，连同 payload 索引 **18,864** 条实际字符串及偏移。角色／move／command 活动表未可靠解析：已解码招式表 **0**，角色名单未验证。{link('FUC_GAME_DATA_INDEX.csv')}、{link('GAME_DATA_SUMMARY.json')}。

实际资源路径代码 `{', '.join(semantic['raw_character_codes'])}` 保留；不会从公开重编译工程的暂定字段猜原 ROM 招式表。{font_candidates} 个字体候选仅有来源索引，未宣称已恢复 TTF。{link('CHARACTER_ASSET_MAP.csv')}、{link('FONT_INDEX.csv')}。

## N. Unknown

**3,102 个待解析完整资源，合计 {fmt(semantic['unknown_bytes'])} 字节**。每项有正式 ID、原始路径、SHA-256、前 64 字节、magic、熵值和格式聚类；所有原始字节保留。MOT 已解码通道、已恢复 PPHD/PBD 声音不计入该未知格式清单，其剩余绑定问题单独报告。{link('FUC_UNKNOWN_FORMATS.csv')}、{link('UNKNOWN_CLUSTERS.csv')}。

统一 `Metadata/UNKNOWN_FORMATS.csv` 在冻结旧文件的字节前缀后追加欧版未知项；旧未知列表未重分类或覆盖。Unknown 主分类 1,859 行与待解析格式清单 3,102 行口径不同：后者同时包含归入 Effects 等类别但内部格式语义仍未知的资源。

## O. Cross-source

对 **13,349** 条欧版图像、音频和 GMO 逻辑资产，与冻结旧库 246,605 条记录的原件／Working SHA 做精确比较。找到 exact_payload 关系 **0**；旧库未含 GMO，842 个欧版 GMO 条目记录为该格式层面的 `FUC_unique`。这不表示旧库不存在同角色或相似画面／音效，也未把未做的 pHash／PCM 相似性当作否定证据。{link('FSN_VS_FUC.csv')}、{link('CROSS_SOURCE_SUMMARY.json')}。

截断日版恢复 ↔ 欧版：**exact_payload {fmt(jpc.get('exact_payload',0))}，different_payload {fmt(jpc.get('different_payload',0))}，Japan_recovery_only {fmt(jpc.get('Japan_recovery_only',0))}，Europe_only {fmt(jpc.get('Europe_only',0))}**。按 ISO 路径和 FPK 条目分别比较，同一条目在两个层级出现不算全局唯一对象数量。**Europe_only 仅表示“当前截断日版中未恢复到”，不得称为欧版独占。** 该对比不为日版分配编号。{link('JAPAN_RECOVERY_VS_EUROPE.csv')}。

HD 项目仅参考其 622 个有效纹理 hash／路径记录，实际本机纹理映射已验证数 **0**。未下载并混入替换纹理、未把外部图像当作原 ROM Preservation。{link('FUC_TEXTURE_EXTERNAL_REFERENCE.csv')}、{link('FUC_TEXTURE_EXTERNAL_MAPPING.csv')}。

## P. Integration

| 稳定性项目 | 结果 |
| --- | ---: |
| before | 246,605 |
| added | 21,899 |
| after | 268,504 |
| old IDs preserved | 246,605 / 246,605 |
| missing old IDs | 0 |
| changed old rows／旧字段值 | 0 |
| 旧 Raw／Working／Thumbnail 路径损失 | 0 / 0 / 0 |
| 受保护路径尺寸／修改时间变更 | 0（检查 496,039 个路径记录） |
| 旧 Gallery 数组／原元数据索引变更 | 0 / 0 |
| 新 Preservation／Working 路径 SHA 校验 | 23,706 个路径 |
| PNG 全图解码检查 | 5,146 个路径 |
| GLB 封装检查 | 341 个文件 |
| SQLite integrity | ok |
| 日版恢复正式资产 | 0 |

新编号范围 **FSN246606–FSN268504**；欧版使用独立 `source_version`，未标为 Japan 或含糊 FUC。统一 CSV／JSONL／SQLite 三种 Catalog 已写入且互相验证；旧 CSV 原字段逐值一致、旧 JSONL 字节前缀一致、SQLite 旧字段逐值一致。添加可选 3D／动画／父子字段时不重写旧语义字段。

新增逻辑资产的口径：

| asset_kind | 行数 |
| --- | ---: |
{table}

逻辑条目保留 ISO／FPK 层级与重复来源，图像 view／clip／subsong 可回溯 parent_asset_id、entry index、offset；不以物理去重替代来源历史。新增 Canonical 去重对象 10,677 个，嵌入父对象引用 12,603 个。仅新来源使用 WORK 硬链接，不给用户源 ISO 建硬链接。

按主分类分布：

| category | 行数 |
| --- | ---: |
{categories}

旧 SCRIPT_INDEX、VOICE_DIALOGUE_MAPPING／RELATIONS、DATABASE_INDEX 哈希未变；旧 ASSET_REFERENCES、VOICE_INDEX、HARDLINKS、CONTACT_SHEETS、UNKNOWN_FORMATS 的字节前缀保留。旧联系表 8,562 行路径零损失；本轮没有为全部旧联系表重新建立完整文件 SHA 基线，因此不宣称其每个文件都重新做了 SHA 对比。冻结旧 Reports 的文件 SHA 全部一致。旧 FHA 4 个 checksum 异常未重新调查。{link('STABILITY_VERIFICATION.json')}、{link('INTEGRATION_COMMIT.json')}。

## Q. Gallery

[打开统一 Gallery](http://127.0.0.1:8986/Gallery/index.html)。服务器仅监听 `127.0.0.1:8986`，根目录为库；测试期间已启动本轮自己的服务。电脑重启后如服务未运行，可在本机启动 `E:/FSN_MASTER_ASSET_WORK/scripts/fuc_serve_gallery.py`。

**Codex 应用内浏览器代表性回归通过；真实 Chrome 未验证。** Chrome 扩展连接失败，未将其冒充为 Chrome PASS。以下均来自实际 UI 点击和图片／媒体状态读取：

- Original／Remastered／FHA／Europe 图片筛选分别 6,241／67,492／12,419／6,970；每个来源抽查 3 张缩略图成功载入。初次未加载完成的图片在稳定后通过。
- 原版 `FSN000047`、FHA `FSN204245` 的 OGG 与欧版 `FSN246719` 的 FLAC 均实际播放，paused=false、readyState=4、currentTime>0、error=0。
- FHA `FSN215096`、欧版 `FSN255896` 和旧 Remastered `FSN042476` 的 MP4 播放／预览均 actual currentTime>0、error=0。
- 原旧 Theora 样本点击后未开始播放；为 16 个唯一旧 Theora 原件生成仅供 Gallery 使用的 MP4 预览并全部全流验证，随后上述旧 ID 的预览实际播放。旧原件、编号、Catalog 和 Working 链接保持不变，预览由独立 preview_map 引用。
- 欧版来源筛选 21,899；欧版图片第 2/117 页与 ID `FSN255958` 实测；源路径搜索 27 条、单 ID 搜索 1 条。
- 模型／MOT 卡片保留原件和工作版链接；MOT 明示“通道已解码，骨骼绑定及播放未验证”。旧与新联系表图片实测载入，欧版索引 444 个链接。

这是代表性播放／导航覆盖，不是全部 268,504 条资源逐个播放证明，也不是互动 3D 或绑定动画预览验收。详细记录：{link('GALLERY_REGRESSION.json')}，旧视频验证：{link('FUC_LEGACY_VIDEO_PREVIEWS.json',L/'Reports')}。

## R. Disk

统计范围为欧版正式目录、欧版 Canonical、欧版联系表、新缩略图及 16 个旧视频播放预览，不含整个旧库。

| 项目 | 实测 |
| --- | ---: |
| 新路径文件数 | {fmt(disk['path_count'])} |
| 按路径相加长度 | {fmt(disk['logical_path_bytes'])} 字节 / {gib(disk['logical_path_bytes'])} |
| 按 Windows file ID 去重长度 | {fmt(disk['unique_file_id_bytes'])} 字节 / {gib(disk['unique_file_id_bytes'])} |
| 去重文件对象数 | {fmt(disk['unique_file_id_count'])} |
| 冻结基线时 E 盘可用 | {fmt(disk['baseline_free_bytes'])} 字节 / {gib(disk['baseline_free_bytes'])} |
| 当前 E 盘可用 | {fmt(disk['current_free_bytes'])} 字节 / {gib(disk['current_free_bytes'])} |
| 全盘可用空间差 | {fmt(disk['drive_used_increase_since_frozen_baseline'])} 字节 / {gib(disk['drive_used_increase_since_frozen_baseline'])} |
| 基线备份文件长度 | {fmt(disk['backup_bytes'])} 字节 |

按 file ID 去重是此范围内的文件长度口径，不是 NTFS cluster 实际分配量；部分对象硬链接到已有 WORK，不能把去重长度直接当作接入净增长。全盘差额包含研究、WORK、工具、备份及其他并发活动，不能全部归因于正式欧版资产。{link('DISK_FOOTPRINT.json')}。

## S. Failures and limitations

| 未完成项 | 原始字节 | 已尝试／证据 | 后续技术路线 |
| --- | --- | --- | --- |
| 日版源完整性 | 原截断 ZIP、恢复前缀和所有已恢复数据保留 | 缺压缩尾部和中央目录；不接入正式 Catalog | 获得完整日版后单独增量接入，保持既有 ID |
| MOT → GMO 骨骼绑定、插值、旋转、loop、播放 | 完整 54 MOT 和 3,676 clip 保留 | 198,831 通道／2,044,587 键值解码与重编码成功；绑定／播放仍 0 | 追踪本机欧版 ELF 的动作加载和骨骼寻址，读取运行时变换；与源 bind pose／同片段逐帧比对后再输出 animation GLB |
| FAN／AMO／VFX 时序、PPEF 程序 | 所有 FPK payload 完整保留 | Noesis 无输出；公开 FPK 工具只解容器；recomp 未提供成熟离线解析器 | 按源字段聚类及 runtime 读访问建立结构，再验证触发和时序 |
| 原 GMO ordinal → 自动命名 bN | 源 chunk 和完整 GLB 保留 | 真实名称可对应；78 个模型的 bN ordinal 映射为 provisional | 通过加载函数和骨骼变换比对，不能只凭编号把候选升级为确认 |
| 角色／move／command／语音语义／场景名称 | ELF 与所有源数据保留 | 18,864 实际字符串；活动表未证实 | 在真实 ELF 数据引用中验证表结构，保持 unknown 至有证据 |
| 字体／其他未知格式 | 3,102 项完整 bytes 有清单 | magic、熵值、前 64 字节与聚类已记录 | 对高频簇读取路径和访问函数开展结构验证，不制造 TTF |
| 外部 HD 纹理映射 | 原 ROM 纹理未替换 | 622 元数据参考，已验证映射 0 | 先取得本机实际 runtime texture hash 证据 |
| Chrome 回归／互动 3D | 原资产无影响 | Chrome 连接不可用；IAB 代表性媒体与导航通过 | 成功连接真实 Chrome 后补同一组检查；当前不写 Chrome PASS |

工具失败探测另有原始日志与 {link('NOESIS_MOTION_FORMAT_PROBES.json')}。实验 Noesis Python bone exporter 未在 CLI 产生目标 JSON，未用其结果充当骨骼验收；改用实际源 GMO chunk walker。FFmpeg 的早期 VAG 假设已由最终 vgmstream 结果纠正。解密最初 watcher 仅检查指定 memstick，随后确认官方 dump 实际位于独立 portable runtime 的 memstick，并以真实 ELF 和 SHA 验证。全部最终成功／失败数以报告与对应索引为准，不以进程返回码替代输出验证。

可重复入口：`E:/FSN_MASTER_ASSET_WORK/scripts/FUC_ASSETS.ps1`。默认 Verify；`-Phase All` 在已经 COMMITTED 后仅 Verify → Compare → Report，不再追加 ID。首次完整流水线按已验证身份提取、转换、MOT 通道、数据、全量 PRS 校验、Index／Integrate、Gallery、预览和最终验证执行；冻结构建基线不可用接入后状态覆盖。原日版阶段入口另存 `FUC_JAPAN_RECOVERY_SAVED.ps1`，不作为本轮欧版执行入口。

## T. Recommended next step

建议下一轮 **Animation Reference Index**：首先解决已有 MOT 曲线与源骨骼／运行时姿态的绑定证据，再将验证过的片段做动作参考索引。之后可按已确认的资源证据建立 **Semantic Catalog**；另可开展 **Official Material 页面索引**。本轮没有实际开始这三项后续工作。
'''
    report_path=L/'Reports/FUC_INTEGRATION_REPORT.md';report_path.write_text(report,encoding='utf-8')
    summary=dict(created_at=nowtext,status=FINAL_STATUS,source_version=identity['source_version'],disc_id=identity['PARAM_SFO']['DISC_ID'],disc_version=identity['PARAM_SFO']['DISC_VERSION'],source_sha256=identity['sha256'],before=commit['before'],added=commit['added'],after=commit['after'],first_asset_id=index['first_asset_id'],last_asset_id=index['last_asset_id'],old_ids_preserved=stable['old_ids_preserved'],missing_old_ids=stable['missing_old_id'],changed_old_rows=stable['changed_old_rows'],logical_models=model['logical_models'],unique_glb_models=model['converted_unique_models'],source_bone_transform_nodes=model['original_gmo_transform_bone_rows'],motion=motion,Japan_recovery_catalog_rows=0,Gallery_browser_status=browser['status'],Gallery_url=browser['url'],important_limitations=['MOT bone binding/interpolation/rotation/runtime playback unverified','FAN/AMO/VFX timing and game-table semantics unresolved','Chrome representative regression unverified'],report=str(report_path),phase_runner=str(W/'scripts/FUC_ASSETS.ps1'))
    jsonwrite(L/'Reports/FUC_RESULT_SUMMARY.json',summary);jsonwrite(md/'RESULT_SUMMARY.json',summary)
    OUT.mkdir(parents=True,exist_ok=True)
    for source,name in [(report_path,'FUC_INTEGRATION_REPORT.md'),(L/'Reports/FUC_STABILITY_VERIFICATION.json','FUC_STABILITY_VERIFICATION.json'),(L/'Reports/FUC_GALLERY_REGRESSION.json','FUC_GALLERY_REGRESSION.json'),(L/'Reports/FUC_RESULT_SUMMARY.json','FUC_RESULT_SUMMARY.json')]:shutil.copy2(source,OUT/name)
    scripts=['common.py','fuc_common.py','FUC_ASSETS.ps1','fuc_europe_decrypt.ps1','fuc_europe_inventory.py','fuc_europe_prepare.py','fuc_fpk_probe.py','fuc_fpk_extract.py','fuc_models_stage.py','fuc_textures_stage.py','fuc_motion_channels.py','fuc_source_bones.py','fuc_motion_data_stage.py','fuc_audio_stage.py','fuc_soundbanks_stage.py','fuc_video_stage.py','fuc_europe_data.py','fuc_full_fpk_verify.py','fuc_europe_index.py','fuc_europe_integrate.py','fuc_europe_gallery.py','fuc_legacy_video_previews.py','fuc_europe_verify.py','fuc_europe_supplement.py','fuc_europe_report.py','fuc_serve_gallery.py']
    with zipfile.ZipFile(OUT/'FUC_REPRODUCIBILITY.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in scripts:z.write(W/'scripts'/name,'scripts/'+name)
        z.write(md/'TOOLS_AUDIT.json','evidence/TOOLS_AUDIT.json');z.write(md/'REPRODUCIBILITY_MANIFEST.csv','evidence/REPRODUCIBILITY_MANIFEST.csv');z.write(md/'FPK_FULL_INDEPENDENT_VERIFICATION.json','evidence/FPK_FULL_INDEPENDENT_VERIFICATION.json')
        z.writestr('README.txt','Europe pipeline source and audit evidence. No ROM/assets/tool binaries distributed here. Existing local source, audited tools, WORK and immutable baseline are required.\nOriginal installed entry: E:/FSN_MASTER_ASSET_WORK/scripts/FUC_ASSETS.ps1\nAfter a COMMITTED integration, -Phase All verifies and refreshes reports only; never reassign IDs.\nIf Gallery server is stopped: use the local Python environment to run scripts/fuc_serve_gallery.py (127.0.0.1:8986).\nJapan recovery is preserved separately and receives no Catalog IDs.\nMOT curves are decoded; bone binding and runtime playback remain unverified.\n')
    with zipfile.ZipFile(OUT/'FUC_MOTION_AND_SKELETON_INDEXES.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in ['ANIMATION_INDEX.csv','ANIMATION_MODEL_BINDING_CANDIDATES.csv','MOTION_SUMMARY.json','SKELETON_INDEX.csv','SOURCE_BONE_INDEX.csv','NOESIS_MOTION_FORMAT_PROBES.json'] :z.write(md/name,name)
        z.writestr('README.txt','Indexes reference the complete local Europe preservation/working paths. 3676 MOT clips and all channels decoded; candidate model associations are not verified bindings. No runtime animation playback acceptance is claimed. Full source and decoded channels remain in the formal library; this zip contains indexes, not a replacement for those objects.\n')
    log('FINAL EUROPE REPORT',summary);log('DELIVERABLES',str(OUT))

if __name__=='__main__':run()
