"""Build the final report from durable extraction, index and acceptance evidence."""
from fha_prepare import *
OUT=pathlib.Path('C:/Users/Murasame/Documents/Codex/2026-10-06/gallery-chrome-fate-hollow-ataraxia-pc/outputs')
def loadjson(p):return json.loads(p.read_text('utf-8'))
def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def number(n):return f'{n:,}'
def gib(n):return f'{n/1024**3:.3f} GiB ({n:,} bytes)'
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(x).replace('|','/') for x in r)+' |' for r in rows])
def run():
    b=loadjson(BACK/'BASELINE.json');s=loadjson(FHA/'Metadata/SOURCE_SUMMARY.json');e=loadjson(FHA/'Metadata/EXTRACTION_SUMMARY.json');c=loadjson(FHA/'Metadata/FINAL_COVERAGE.json');i=loadjson(FHA/'Metadata/INDEX_SUMMARY.json');j=loadjson(FHA/'Metadata/INTEGRATION_COMMIT.json');g=loadjson(FHA/'Metadata/GALLERY_COMMIT.json');v=loadjson(L/'Reports/FHA_STABILITY_VERIFICATION.json');ui=loadjson(L/'Reports/FHA_GALLERY_VALIDATION.json');d=loadjson(L/'Reports/FHA_DISK_USAGE.json');dd=loadjson(L/'Reports/FHA_DISK_DETAILS.json');roles=loadjson(FHA/'Metadata/IMAGE_ROLE_SUMMARY.json');tools=loadjson(FHA/'Metadata/TOOLS_MANIFEST.json')
    assert v['status']=='PASS' and v['after']==g['after']==j['after']
    ui_current=ui.get('index_sha256')==sha(L/'Gallery/index.html') and ui.get('catalog_js_sha256')==sha(L/'Gallery/catalog.js')
    status='FSN_FHA_MASTER_ASSET_INTEGRATION_PASS' if not e['checksum_exceptions'] and ui['status']=='PASS' and ui_current and not c['unknown'] and not c['converted_failed'] else 'FSN_FHA_MASTER_ASSET_INTEGRATION_PARTIAL'
    comparisons=readcsv(FHA/'Metadata/FSN_VS_FHA.csv');bytype=collections.defaultdict(set);pairs=collections.Counter()
    for r in comparisons:bytype[r['match_type']].add(r['fha_asset_id']);pairs[r['match_type']]+=1
    refs=readcsv(FHA/'Metadata/ASSET_REFERENCES.csv');rtypes=collections.Counter(r['reference_type'] for r in refs);unresolved=collections.Counter(r['resolution_status'] for r in refs if not r['target_asset_id'])
    logs=loadjson(FHA/'Metadata/EXTRACTION_LOG.json');overrides=readcsv(FHA/'Metadata/OVERRIDE_MAP.csv');ogroups=collections.defaultdict(set)
    for r in overrides:ogroups[r['relationship']].add(r['override_group'])
    media=loadjson(FHA/'Metadata/CHECKSUM_EXCEPTION_MEDIA_VALIDATION.json');repairs=loadjson(FHA/'Metadata/CXDEC_REFERENCE_REPAIRS.json');baselinefiles={pathlib.Path(r['path']).name:r for r in b['files']}
    assert sha(L/'Reports/FINAL_REPORT.md')==baselinefiles['FINAL_REPORT.md']['sha256']
    work=d['sections'][str(W)];library_allocated=sum(r['additional_allocated_bytes_across_roots'] for p,r in d['sections'].items() if p!=str(W))
    paragraphs=[f'''# Fate/hollow ataraxia PC 增量集成报告

状态：**`{status}`**  
生成时间：{now()}（UTC；本机时区 Asia/Singapore）

FHA 已作为 `HollowAtaraxia` 加入统一 Catalog 和 Gallery。新增 **{number(c['logical_assets'])}** 条逻辑资产，统一库由 **{number(b['total_assets'])}** 增至 **{number(v['after'])}**。Original / Remastered 的全部旧编号、40 个旧字段值、媒体路径及 Gallery 记录均保留。

严格状态仍为 PARTIAL：4 条封包 Adler32 校验差异未消除，其中 2 条为可完整解码的 WAV；真实 Chrome 自动化连接不可用，旧 Theora 视频在应用内浏览器播放失败，Chrome 的视频回归尚未确认。FHA 的图像、语音、BGM、MP4、搜索、筛选及分页已做实际页面验收。

## A. Source

调查根目录：`{ROOT}`  
真正游戏目录：`{s['game_root']}`  
递归覆盖父目录内的附属文件和游戏子目录，未按 patch / backup / locale 名称跳过文件。

{table(['项目','实际值'],[['Source files',s['source_files']],['Source bytes',gib(s['source_bytes'])],['Physical containers',s['physical_containers']],['Nested XP3 containers',s['nested_containers']],['E 盘开始可用',gib(s['disk_E']['free'])],['E 盘磁盘审计时可用',gib(d['disk_E']['free'])]])}

完整指纹在 `HollowAtaraxia/Metadata/SOURCE_INVENTORY.csv` 和 `.json`：路径、大小、SHA-256、mtime / mtime_ns、magic、识别格式和说明。后续格式识别只更新描述，不修改初始源文件指纹。

源扩展名分布：{json.dumps(s['extensions'],ensure_ascii=False)}。最终格式分布：{json.dumps(s['source_format_counts'],ensure_ascii=False)}。逐 magic 的分布保存在 `SOURCE_SUMMARY.json` 的 `magic_hex_counts`。

结束复核：modified source files = **0**；deleted source files = **0**；added source files = **0**。63 个源文件重新读取全部 SHA-256、大小、纳秒 mtime，全部与初始记录一致。

## B. Format / Engine

实际引擎资料为 KiriKiri / KAG（含 TJS、KS、FCF、加密文本和 CXDEC）。11 个文件是真正 XP3。三个扩展名为 XP3 的文件实际是 Molebox / NewDES QUICKBOX：`language_SChinese.xp3`、`voice.xp3`、`voice2.xp3`，内部各有一个 XP3。

`FateFD.exe` 是 Molebox 包装的 PE。静态恢复其目录、内嵌 `cxdec.tpm`、NewDES extra 区及其中第四个 XP3。没有运行游戏 EXE 或把 TPM 加载到操作系统。

外层 XP3 使用与目录内 114,688-byte TPM 相匹配的 FHA CXDEC；内层 XP3 使用恢复出的 46,080-byte TPM 控制区。真实文件与算法输出、目录 CRC32、数据块 CRC16、XP3 Adler32 和文件 magic 共同支持识别；未直接沿用 FSN 的 `--plugin=fsn`。

## C. Tools

{table(['工具 / 源码','版本 / commit','用途'],[[t['tool'],t.get('version','')+' '+t['commit'],t['algorithm']] for t in tools['sources']])}

Arc 二进制 SHA-256：`{tools['sources'][0]['sha256']}`。FFmpeg / ffprobe：6.1.1。Python：{tools['python'].splitlines()[0]}。Python 包版本和脚本 SHA-256 在 `HollowAtaraxia/Metadata/TOOLS_MANIFEST.json`。

算法来源：[arc_unpacker FHA CXDEC 插件](https://github.com/vn-tools/arc_unpacker/blob/ff3b9d9b071cc85ea6c50081aa4a7a88cab4d27a/src/dec/kirikiri/xp3_archive_decoder_plugins.cc)、[Molebox VFS](https://github.com/sudachen/Molebox/blob/f526e8a41bcb7884231154e8e5ccb74c789f188d/Core/src/svfs.cpp)、[NewDES 实现](https://github.com/sudachen/xternal/blob/1cfcaacbdeca03cacc8f8d6ed8a51c8942ca277d/libhash/src/ndes.c)、[GARbro KiriKiri 源码](https://github.com/morkt/GARbro/tree/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/KiriKiri)。实际历史 Molebox 构建使用 NewDES，不能直接照搬较新源码中的 Blowfish 常量。

可复现入口：`E:/FSN_MASTER_ASSET_WORK/scripts/FHA_ASSETS.ps1 -Source HollowAtaraxia -Phase All`。已提交库会跳过提取和重新分配 ID；对已集成资产直接重跑 Extract / Convert / Index / Compare 被拒绝，语义修正须走保留 ID 的 FHA 专属修订。

典型命令（完整实际参数逐容器保存在 `EXTRACTION_LOG.json/.csv`）：

```text
arc_unpacker.exe --dec=kirikiri/xp3 --plugin=fha --numeric-file-names --no-recurse --no-color -t=2 -v=1 -o=<WORK输出> <暂存XP3>
python fha_molebox.py --extract
python fha_nested.py
python fha_filter_vm.py
python fha_convert.py
ffmpeg -v error -nostdin -i <原始MPEG> -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart <唯一MP4对象>
```

独立 CXDEC 复核在 Unicorn 的隔离内存里调用恢复出的 TPM 密钥生成代码，OS 调用替换为内存内存根；不运行原生 EXE / DLL。脚本、工具源码、日志和探查结果均长期保存在 WORK。

## D. Extraction

{table(['层级','Detected','Attempted','Success','Partial','Failed'],[['实际源容器外层',15,15,14,1,0],['发现的内层 XP3',4,4,2,2,0],['全部解包层级',19,19,16,3,0]])}

上述 Success / Partial 按该层自身校验计数。若把内层校验异常传播至其实际源文件，15 个实际源容器为 12 success / 3 partial / 0 failed。所有层级的 declared entries 与 extracted entries 相同：{sum(x.get('expected_entries',0) for x in logs):,} / {sum(x.get('files_extracted',0) for x in logs):,}；另保留松散文件与 EXE extra 内层容器对象，得到 {c['logical_assets']:,} 条逻辑资产。

每个 XP3、补丁和内层包独立保存于 `HollowAtaraxia/RawExtracted/XP3`、`Molebox`、`NestedXP3`；松散文件在 `Loose`。超长或 Windows 不合法名称映射为安全实体路径，原逻辑名称始终保留在索引。

SHA-256 唯一 payload：{number(c['unique_payloads'])}；FHA 内 exact duplicate records：{number(c['logical_assets']-c['unique_payloads'])}。`OVERRIDE_MAP.csv` 有 {number(i['override_rows'])} 条历史记录，关系组数：{json.dumps({k:len(x) for k,x in ogroups.items()},ensure_ascii=False)}。同路径不同内容均保留，没有自动选择或删除旧补丁内容。

## E. Images

{table(['项目','逻辑数量'],[['Images',c['images']],['TLG',c['format_counts']['TLG']],['BMP',c['format_counts']['BMP']],['PNG',c['format_counts']['PNG']],['转换为 PNG',c['conversion_status']['converted_png']],['保留原生 PNG',c['conversion_status']['native_png']],['新增唯一缩略图',g['new_unique_thumbnails']],['新增 Contact Sheet',g['new_contact_sheets']]])}

TLG / BMP 提供 PNG Working Copy，透明通道保留；PNG、字体及原媒体保留原格式。统一 SHA 对象在 `Converted/Objects`，FHA 的 `Converted/WORKING_COPY_INDEX.csv` 指向实际 Working Copy，不再复制第二套相同实体。

旧缩略图 {b['old_thumbnail_paths']:,} 个和旧 Contact Sheet 5,565 页均保留。全库 Contact Sheet 8,562 页，唯一缩略图 45,802 个。

`IMAGE_ROLES.csv` 按来源证据记录角色层 / 背景渲染桶 / Gallery 壁纸图：{json.dumps(roles['unique_asset_counts'],ensure_ascii=False)}。Background 是渲染角色，可以包含剧情 CG；70 条 CG 来自 Gallery 壁纸存储前缀。EventCG / Effect 尚未做可靠的批量语义分离，相关图片保存在原来源桶并可通过文件名、脚本引用查找。这里的 unknown 是语义未知，与无法识别文件格式不同。

28,199 条资产具有人物身份依据；1,365 条服装标签依据文件名。字典和文件名前缀支持 Bazett、Caren、Avenger 及实际出现的 FSN 角色。`TAG_EVIDENCE.csv` 保留依据。数字姿势 / 字母差分保留原标记，未猜测情绪；`**`、`？？？` 等身份占位符保留为 unknown / 空 speaker。

## F. Audio

{table(['项目','逻辑数量'],[['Audio',c['audio']],['Voice',c['voice']],['BGM',c['bgm']],['SE（包含小游戏 / UI / 战斗等来源）',c['se']]])}

Codec 分布：{json.dumps(c['audio_codecs'],ensure_ascii=False)}。28,145 条 voice 为原生 Ogg Opus，直接保留 bitstream；Vorbis / WAV 同样不重复转码。codec、duration、sample_rate、channels、bitrate、SHA-256 存在统一 Catalog，Voice 技术字段另存 FHA `VOICE_INDEX.csv`。

2 段 Adler32 异常 WAV 的独立解密输出与 Arc 完全一致，且 FFmpeg 全程解码 exit code 均为 0。此结果证明可解码，不等于封包 checksum 已匹配。

## G. Script

Scenario + Scripts 来源桶 {number(c['scripts'])} 条；Script / 系统文本 / 表索引 {number(i['scripts'])} 条。可读文本 / gettext Working Copy 共 {number(c['text'])} 条。原 bytes 保存，UTF-8 Working Copy 单独保存。

编码分布：{json.dumps(c['text_encodings'],ensure_ascii=False)}。KiriKiri 加密文本按其实际封装恢复 UTF-16，再生成 UTF-8；gettext MO 保留原件并生成可读 JSON。

`SCRIPT_INDEX.csv` 有资产 ID、原文件、scene、字符名、行数、选项数及图像 / voice / BGM / SE / movie 引用统计；原日期 / 场景表恢复 {number(i['scene_table_rows'])} 行，保存在 `SCENE_TABLE.csv`。day、time_slot、location 仅按明确源行填写，loop_phase 没有可靠证据时为空。没有按剧情常识填补循环结构。

## H. Voice mapping

新增 voice-dialogue relations：**{number(i['voice_dialogue_rows'])}**。覆盖 {number(i['mapped_voice_assets'])} / {number(i['voice_assets'])} 个 voice 资产；其余 {number(i['voice_assets']-i['mapped_voice_assets'])} 个保留语音和索引，没有虚构台词。

依据为明确 KAG voice 命令、文件名、`voicename2key.dic` 的 116 个原始代码、`init.tjs` 的文件名规则，以及花札胜利数组中的明确角色 / 台词 / voice 字面量。动态表达式不执行。

完整 FHA 字段在 `HollowAtaraxia/Metadata/VOICE_DIALOGUE_RELATIONS.csv`。统一 `VOICE_DIALOGUE_MAPPING.csv` 保留原有字段和旧行，`VOICE_DIALOGUE_RELATIONS.csv` 是兼容统一别名。日文 / 简体中文补丁映射和历史脚本均保留；speaker 证据不足为空。

## I. Asset references

新增 {number(i['references'])} 条关系，其中 {number(i['resolved_references'])} 条已解析，{number(i['unresolved_references'])} 条保留未解析。

{table(['reference_type','关系记录'],sorted(rtypes.items()))}

每条记录保留 script ID、行号、命令、原引用名称、目标 ID / 路径及解析状态；FHA 专属副本另有原属性名及 scene page。相同存储名的多补丁候选全部保留，所以关系行数可能超过脚本命令数。未解析状态：{json.dumps(dict(unresolved),ensure_ascii=False)}。这属于静态表达式解析覆盖率，未解析不意味着对应原始资源被删除。

数据库 / 系统资料索引 {number(i['database_tables'])} 项，涵盖 FCF、字典、文本表、gettext 等。花札 / 小游戏的 sprite、UI、规则、台词和声音保留，没有按“主线之外”排除。

视频：4 条原始 MPEG 全部保留，并各提供一个 H.264 / AAC MP4 Working Copy。分辨率 800 × 600；详细 fps、duration、codec、audio_tracks 在 Catalog。原始时长约 110.707、90.854、122.149、94.981 秒；原件与 Working Copy 分开记录，未生成多个完整转码副本。

## J. FSN vs FHA

`Metadata/FSN_VS_FHA.csv` 与 FHA 专属副本共有 {number(len(comparisons))} 行。

{table(['类型','比较关系行','涉及 FHA 唯一资产'],[[k,number(pairs[k]),number(len(bytype[k]))] for k in ['exact_payload','same_visual_candidate','higher_resolution_candidate','modified_candidate','FHA_unique_candidate']])}

仅 exact_payload 的 SHA-256 完全相同关系为 confirmed；其它 pHash / dHash / 尺寸关系都是候选。候选分类不能证明同一人物、服装、事件或艺术内容，也不会触发删除。FHA_unique_candidate 包含所有媒体和文本类别的未匹配 payload，不只图片。

## K. Unknown

FHA UNKNOWN 文件格式：**{c['unknown']}**。`UNKNOWN_FORMATS.csv` 和 `UNKNOWN_CLUSTERS.csv` 保留标准表头，目前没有未识别 payload 行。已知 PE 程序 / 插件 40 条按原 bytes 保存；这是已识别代码二进制，不宣称反编译其全部行为。

4 条 checksum 异常在 `EXTRACTION_SUMMARY.json`、`EXTRACTION_LOG.json` 和独立复核文件中明确记录。语义 unknown、静态动态引用和 checksum 异常分别记录，均未被 Ignore。

旧 Remastered 的 178 FTPR + 54 GUTC partial 项仍为原状态；统一 UNKNOWN 表原 232 行完整保留，本轮没有深入处理它们。

## L. Integration

{table(['来源','before','added','after'],[['Original',42546,0,42546],['Remastered',160056,0,160056],['HollowAtaraxia',0,44003,44003],['Total',202602,44003,246605]])}

实际 SQLite 基线与用户给出的 202,602 一致，difference = 0。原最大 ID `FSN202602`；FHA 仅追加 `FSN202603` 至 `FSN246605`。

{table(['稳定性检查','结果'],[['旧 asset_id 总数',v['old_ids']],['完整保留旧 asset_id',v['old_ids_preserved']],['missing old ID',v['missing_old_ids']],['changed old row（旧 40 字段）',v['changed_old_rows']],['old catalog row loss',0],['old raw path loss',v['missing_paths']['old_extracted_path']],['old working path loss',v['missing_paths']['old_converted_path']],['old thumbnail path loss',v['missing_paths']['old_thumbnail_path']],['old gallery asset loss',v['old_gallery_asset_loss']],['旧 Gallery 数组变化',v['old_gallery_array_changes']],['SQLite integrity_check',v['sqlite_integrity']],['SHA-256 readback errors',v['sha256_errors']]])}

334,236 个唯一文件实体完成 SHA-256 回读；所有旧 RawExtracted、Working Copy、thumbnail、Canonical、decrypted path 和旧 Contact Sheet 均存在。旧 JSONL 保留字节级前缀；CSV 和附属索引逐旧字段 / 旧行比对，丢失 = 0。

{table(['统一索引','before','added','after'],[[name,st['old_rows_preserved'],st['added_rows'],st['old_rows_preserved']+st['added_rows']] for name,st in v['indexes'].items() if name in {'ASSET_REFERENCES.csv','SCRIPT_INDEX.csv','VOICE_INDEX.csv','VOICE_DIALOGUE_MAPPING.csv','CONTACT_SHEETS.csv'}])}

旧 40 字段无损保留，新增 11 个兼容可选字段；旧 JSONL 缺少新增字段时按空值解释，SQLite / CSV 采用可选空值。Schema 说明在 `Metadata/FHA_SCHEMA_EXTENSION.json`。

轻量备份：`{BACK}`，冻结文件合计 {gib(sum(r['size'] for r in b['files']))}。只备份索引、Gallery HTML / JS 和报告，不复制旧 RawExtracted。`Reports/FHA_PRE_INTEGRATION_BASELINE.json` 保存 SHA-256、大小、行数、SQLite 计数、最大 ID 和 Gallery 基线。旧 `FINAL_REPORT.md` 本轮 SHA-256 不变。

Canonical 新增 {j['new_canonical_objects']:,} 个 SHA 对象链接，原 Canonical 和旧逻辑来源均保留。新增 Canonical 媒体 payload 物理增长为 0；硬链接目录项的 NTFS 元数据开销另计，不把逻辑大文件长度重复累加。

转换成功（实际转格式 / 解码文本 / 索引混合日志）{c['converted_success']:,}；原生可用 / 原件保留 {c['native_or_preserved']:,}；转换失败 **{c['converted_failed']}**。

## M. Gallery

入口保持 `E:/FSN_MASTER_ASSET_LIBRARY/Gallery/index.html`。旧 202,602 个数组和枚举位置完整保留；追加 FHA 44,003 条，版本筛选增加 HollowAtaraxia。增加有证据的人物筛选、场景 / 日期搜索和原生 Opus 播放支持。

真实渲染验收：应用内浏览器通过 `http://127.0.0.1:8786/Gallery/index.html`，共 {len(ui['tests'])} 项通过记录，console error / warning 为 0，测试请求的 missing asset / 404 / 403 / 500 为 {ui['http_missing_asset_requests']}。

通过：页面加载 246,605 条；Original / Remastered / FHA 完整图像；旧两个来源音频；FHA Opus / BGM / MP4；编号及文件名搜索；三个版本、旧路线、类别、来源包、格式、分辨率、最小宽度、人物筛选；分页、紧凑显示及 FHA Contact Sheet。

**完整 Gallery 回归仍为 PARTIAL。** 真实 Chrome 扩展连接重试仍不可用；旧 `FSN042476` Theora 视频在应用内浏览器的实际 Play 点击后未能播放。其原文件全程 FFmpeg 解码成功，原 SHA / 路径 / Catalog 行不变，因此不能据此断言 Chrome 发生退化，也不能写 Chrome 视频回归 PASS。

自动工具拒绝 file 协议访问，已按任务要求使用本机 HTTP 做可用的实际 UI 验收；没有绕过浏览器协议策略。双击入口及 Chrome 最终视频播放仍待真实 Chrome 复核。浏览器证据对应当前 HTML / JS SHA：{ui_current}。

证据：`Reports/FHA_GALLERY_VALIDATION.json`、`FHA_OLD_VIDEO_DECODE.json`；可重放步骤：`WORK/scripts/FHA_BROWSER_ACCEPTANCE.js`。测试服务器结束后关闭，不作为 Gallery 双击运行的依赖。

## N. Disk

{table(['范围','实测占用 / 口径'],[['FHA source',gib(d['source']['allocated_bytes'])],['HollowAtaraxia RawExtracted',gib(dd['raw']['allocated_bytes'])],['FHA Converted（Working Copy 索引目录）',gib(dd['fha_converted_directory']['allocated_bytes'])],['新增共享 Converted objects',gib(dd['new_converted_objects']['allocated_bytes'])],['新增 thumbnails',gib(dd['new_thumbnails']['allocated_bytes'])],['新增 Contact Sheets',gib(dd['new_contact_sheets']['allocated_bytes'])],['FHA Metadata',gib(dd['fha_metadata']['allocated_bytes'])],['统一 Metadata 逻辑字节增长',gib(dd['global_metadata_logical_growth'])],['Canonical 新媒体 payload 物理增长',0],['FHA WORK（本目录去重后）',gib(dd['fha_work']['allocated_bytes'])],['全部 WORK（本目录去重后）',gib(work['allocated_bytes'])],['WORK 相对库的额外实体分配',gib(work['additional_allocated_bytes_across_roots'])],['全部库（实体分配）',gib(library_allocated)],['全部库 + WORK（跨目录去重）',gib(d['library_and_work_allocated_bytes'])]])}

使用 NTFS `(device, file id)` 与 FileStandardInfo AllocationSize。Canonical 的逻辑约 18.4 GiB 未重复计入库 / WORK 实体总量。独立分类或目录数字可能通过 hardlink 重叠，不能直接相加；目录 / MFT 开销未计入文件流占用。详表在 `FHA_DISK_USAGE.json`、`FHA_DISK_DETAILS.json`，报告及新证据产生后的增长很小。WORK 保留提取缓存、历史算法探查和复现证据，未把它们伪称为库本身新增媒体。

## O. Failures / Remaining

1. `sound.xp3/se245.wav`：包内 Adler32 `0xbb300abb`，独立解密后 `0x76ae0abf`；保留 3,103,820 bytes，完整 WAV 解码成功。
2. `sound.xp3/se247.wav`：包内 Adler32 `0x851a5c8d`，独立解密后 `0x233d5c89`；保留 1,275,720 bytes，完整 WAV 解码成功。
3. 内层 language / EXE 各一条声明不加密的 157-byte 警告文本：包内 checksum 与可读原 bytes 不同，原件和 UTF-8 均保留。不能把无法匹配的 checksum 改写成成功。
4. 113 条静态引用未解析，含动态表达式；未虚构目标。4,179 条语音没有明确静态台词映射，保留完整语音。EventCG / Effect 及大量表情语义未作可靠批量分类，未作视觉猜测。
5. Chrome 的实际视频回归未完成，IAB 的旧 Theora 播放失败；文件与旧索引均无损。此项使第 14 个完成条件尚未全通过。

容器提取失败 0；媒体 / 文本转换失败 0；源修改 / 旧资产丢失 / 旧 ID 变化 / 哈希回读失败均 0。以上剩余事项使最终状态保持 PARTIAL。

## P. Recommended next step

在用户审阅本报告后，下一任务仅调查 **Fate/unlimited codes Portable（PSP）**：先只读清点 ZIP / ISO / PSP 目录与真实容器，再按其格斗游戏的模型、纹理、骨骼 / 动画、音频和脚本结构制定独立提取策略；保持本库 ID 增量与索引备份流程。本轮未打开或提取 FUC，也未开始 Complete Material、Side Material 或动画素材。
''']
    report='\n'.join(paragraphs);target=L/'Reports/FHA_INTEGRATION_REPORT.md';target.write_text(report,encoding='utf-8');OUT.mkdir(parents=True,exist_ok=True);shutil.copy2(target,OUT/target.name)
    summary=dict(status=status,generated_at=now(),report=str(target),source_files=s['source_files'],containers_attempted=19,added_assets=c['logical_assets'],total_assets=v['after'],old_ids_preserved=v['old_ids_preserved'],missing_old_ids=0,changed_old_rows=0,source_modified=0,gallery_status=ui['status'],checksum_exceptions=len(e['checksum_exceptions']),outputs_copy=str(OUT/target.name))
    jsonwrite(L/'Reports/FHA_INTEGRATION_STATUS.json',summary);shutil.copy2(L/'Reports/FHA_INTEGRATION_STATUS.json',OUT/'FHA_INTEGRATION_STATUS.json')
    print(status,'REPORT',target,flush=True)
if __name__=='__main__':run()
