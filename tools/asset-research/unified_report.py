from unified_common import *
import shutil
def report():
    summary=read(S/'Metadata/SEMANTIC_FINAL_SUMMARY.json');qa=read(S/'Reports/SEMANTIC_DATA_QA.json') if (S/'Reports/SEMANTIC_DATA_QA.json').exists() else {'status':'PENDING'}
    stable=read(S/'Reports/SEMANTIC_STABILITY.json') if (S/'Reports/SEMANTIC_STABILITY.json').exists() else {'status':'PENDING'}
    ui=read(S/'Reports/BROWSER_ACTUAL_QA.json') if (S/'Reports/BROWSER_ACTUAL_QA.json').exists() else {'status':'PENDING'}
    passed=qa['status']=='PASS' and stable['status']=='PASS' and ui['status']=='PASS' and ui.get('database_sha256')==qa.get('database_sha256')
    status='UNIFIED_FSN_SEMANTIC_CATALOG_PASS' if passed else 'UNIFIED_FSN_SEMANTIC_CATALOG_PARTIAL'
    label_limit='Unresolved FHA dictionary speaker labels remain Other / source_local_speaker_label; identity and alias unification require evidence.'
    if label_limit not in summary['known_limitations']:summary['known_limitations'].append(label_limit)
    counts=summary['counts'];base=read(B/'BASELINE.json')
    guide='''# FSN 统一语义选材台使用指南

双击 `E:\\FSN_MASTER_ASSET_LIBRARY\\Open-FSN-Semantic-Catalog.cmd`。服务只监听 127.0.0.1，不需要互联网。

## 我要做某个角色

1. 在搜索框输入 Lancer、Rin、Saber、Archer、Sakura，也可以用日文名、已收录别名、内部 code。
2. 查看实体概览中六大来源的关系数量。数量表示覆盖，不表示证据质量。
3. 选择 MOD 用途，例如「战斗动画参考」。优先查看「已确认关联」的 FUC motion，再按需要查看「仅文本提及」与候选镜头。
4. 打开「证据详情」，阅读原始 Evidence Type、原状态、原文、Source ID、Locator、Confidence 与 Provenance。
5. 用「打开原来源浏览器」返回已有 Gallery、ReferenceBooks、AnimationReferences 或 FUC 语义浏览器。
6. 将需要的图片、动画、shot 或资料页加入选材篮，填写用途、选择理由与备注。
7. 导出 Selection Manifest。清单保存编号、原文件路径、时间点、来源版本、关系和证据；媒体复制数为 0。

## 组合查询

可输入 `Rin + Jewel`、`Lancer + Gae Bolg`、`Archer + Projection`、`Saber + Avalon`。

「合并查看所选实体」展示两边已有的结构化关系。「共同命中同一引用」只显示同一 page／shot／script line 等对象的交集。共同出现姓名和术语不等于人物使用该武器、人物出现在画面、动作已确认；空结果是允许的。

在 Lancer + Gae Bolg 中，Lancer 的 FUC equipment model 是已确认装备关系；枪的命名仍受本地 FUC 证据限制。FSN248770 不会仅凭外形自动变成 Gáe Bolg。

## 读懂状态

- **已确认关联**：关联受该来源的明确记录支持；仍应检查原等级。confirmed_runtime、confirmed_table、confirmed_ui 均分别保留。
- **仅文本提及**：字幕、脚本或官方页文字中出现相关名字。不能当作画面人物确认。
- **强候选／候选**：保留原候选，包括视觉相似、目录归属和未完全绑定的 FUC 资源。
- **未知**：没有足够语义证据。用 asset ID 可找到原始记录，也可以按需选材；不会给未知素材编造证据。

S5 是直接 runtime／exact hash，S4 是显式 UI／文本，S3 是 table／script，S2 是 alias／context，S1 是 candidate，S0 是 unknown。卡片显示「原证据最高 S」，是关系附带原证据的最高强度；例如明确 OCR 文本与候选章节可以并存，这不会把候选关系升级。等级只是辅助，原始类型、状态和证明范围始终保留。

## 来源、范围和用途

来源可多选。scope 表示作品来源与参考用途，不是 canon 等级。Carnival 为 PARODY_COMEDY，Fate/Zero 与 Prototype 为 FATE_RELATED_REFERENCE，卫宫家今天的饭为 DAILY_LIFE_REFERENCE。其他或混合身份保留 OTHER。

用途排名分别计算：卡面考虑既有尺寸和证据；战斗动画参考考虑已验证 FUC motion；设定参考优先官方页。它们都是 derived recommendation，不声称素材是「最佳」。未审镜头可供定向参考，但标签不变成已确认战斗或人物出现。

## Lancer / Rin 的定向核查

搜索 `lan:state:145` 可查看已冻结的 state145 → clip145 → effect／audio／equipment 资源边。state145 没有独立招式显示名，仍保留 Lancer state145／M ATTACK 的上下文。

搜索 Rin，类型选择 FUC Move / State，可查看 Gand Shot 与 rin:state:159 的明确绑定。未绑定的 UI entries 仍独立保留，不自动补齐。

## 动画回源

shot 详情保留 shot_id、media_asset_id、源时间点及 PTS。在详情中使用「回源播放该镜头」，或复制：

```powershell
& 'E:\\FSN_MASTER_ASSET_WORK\\scripts\\OPEN_ANIMATION_REFERENCE.ps1' -ShotId '具体 shot_id'
```

调用已有 helper，不生成新视频或分镜。字幕中的 Lancer、Saber 等职阶名在相关作品中可能有不同指代；记录是名字／词汇提及，不是人物身份或画面确认。

## 资料页与历史差异

页面正文、OCR、printed page 与扫描页分别保留。文字姓名引用不等于画面人物确认。Side Material 的旧文字保留来源，不被 Complete Material 的晚期资料覆盖。别名的 search_alias、source_spelling、internal_code 等类型可以在实体概览展开查看。

## 待审与增量更新

「按需审阅」整合既有动画、官方 OCR、FUC 与视觉相似候选；本轮不批量处理。未来围绕具体 MOD 所需少量对象新增 manual_review evidence，保留 rejected／旧 candidate 和历史。

永久入口：`E:\\FSN_MASTER_ASSET_WORK\\scripts\\UNIFIED_SEMANTIC_CATALOG.ps1`。Inventory 冻结基线；Entities／Aliases／Evidence／Relations／CrossSource／Usage／Database 共享一个原子依赖构建；Browser 更新新增工作台；Verify 校验旧库；QA 校验数据库与语义不变量；Report 输出验收决定。All 执行全链路，但实际浏览器验收仍需要操作真实页面。

本次最终验收版本为 v2，v1 历史快照保留在 SemanticCatalog\\Revisions\\v1。v2 修订了 72 个未归一 FHA 说话者标签的实体类型；全部 152 个实体 ID、别名、证据与关系保留，修订明细见 ENTITY_CLASSIFICATION_HISTORY.json。源索引以后发生变化时必须使用新 revision，如 `-Revision v3`；稳定实体映射保存在 IMMUTABLE_ID_REGISTRY.json。已有证据、关系和历史不删除。刷新不会重新 OCR、解包、检测 shot 或运行 FUC。

## 服务关闭与后续阶段

双击 Stop-FSN-Semantic-Catalog.cmd，只停止带本工作台令牌的服务。它不会结束其他本地服务。

素材工程验收通过后，下一步是 FSN × Slay the Spire 2 MOD 正式设计：确定第一批可玩角色、核心机制和卡牌框架。本轮不选择首发角色或设计机制，也不再开启新的大型素材工程。
'''
    (L/'Reports/FSN_SEMANTIC_CATALOG_USAGE.md').write_text(guide,encoding='utf-8')
    (S/'Reports/FSN_SEMANTIC_CATALOG_USAGE.md').write_text(guide,encoding='utf-8')
    cov=summary['source_coverage'];major=[]
    c=ro(DB)
    for query in ['Lancer','Rin','Saber','Archer','Sakura']:
        eid=c.execute('select entity_id from aliases where normalized_alias=? limit 1',(norm(query),)).fetchone()
        if eid:major.append(next((r for r in cov if r['entity_id']==eid[0]),{}))
    table='| Entity | Original | Remastered | FHA | FUC | Official | Animation mentions |\n|---|---:|---:|---:|---:|---:|---:|\n'+''.join('| '+r.get('preferred_label','')+' | '+' | '.join(str(r.get(k,0)) for k in ['Original_count','Remastered_count','HollowAtaraxia_count','FateUnlimitedCodesPortable_Europe_count','OfficialMaterial_count','Animation_mentions'])+' |\n' for r in major)
    sections=[
      ('A. Baseline',f"旧 Catalog **270,798** 条，最大 ID **FSN270798**。三种 Catalog 的行数、schema、SHA-256 与 SQLite integrity 已记录在 UNIFIED_SEMANTIC_PRE_BASELINE.json。备份 `{B}` 仅元数据／报告，不含媒体。稳定性验收：**{stable['status']}**。"),
      ('B. Source Families','接入 Original、Remastered、HollowAtaraxia、FateUnlimitedCodesPortable_Europe、OfficialMaterial、AnimationReference。主 Catalog 来源版本分项：\n\n'+js(base['source_version_counts'])),
      ('C. Entity Ontology',f"独立 opaque ENT ID；{counts['entities']:,} entities。实体类型 vocabulary 包括全部要求的 Character／Variant／Weapon／NP／Magecraft／Ability／Item／Location／Faction／Organization／Route／Event／Concept／Term／Move／Command／Costume／MediaWork／Other。未获可靠类型证据的设置词条保留 Term／Other，不强制细分。没有新 FSN ID。"),
      ('D. Alias Model',f"{counts['aliases']:,} aliases，复用官方页、动画检索词汇、FUC indexed code/name 和 FHA dictionary。source_spelling、search_alias 与 internal_code 分开，search alias 不冒充官方翻译。规范化保留原文和日文浊点，支持 NFKC 与拉丁重音。源支持的显示拼写优先于既有 derived canonical label。"),
      ('E. Evidence Model',f"{counts['evidence']:,} evidence。原始 evidence type／status／raw text／locator／source path／record SHA256 与完整 provenance 均保留。S0–S5 只是辅助层，不压平 confirmed_runtime 与 confirmed_table。"),
      ('F. Relations',f"{counts['relations']:,} relations。实体→source 与 source-local→source-local 资源图均有 evidence bridge 和 revision history。mentioned_in 与 depicted_in／appears_in 分开。文字共同命中不会自动生成 uses_weapon 等关系。"),
      ('G. Original / Remastered','复用 SCRIPT_INDEX、解码 text_path、ASSET_REFERENCES、VOICE_DIALOGUE_MAPPING、ORIGINAL_VS_REMASTERED 和 IMAGE_SIMILARITY。已有文本原文可以建立 exact mention，明确 source reference 建立脚本→asset 资源边。未确认 speaker／character 的资产仍未知；相似关系不因接入语义层升级。'),
      ('H. FHA','复用明确 filename convention、TAG_EVIDENCE、voicename2key dictionary 与已映射 speaker。原有日／场景／costume／expression 字段保留为元数据，不批量生成碎片实体。未归一到独立人物的 FHA 字典说话者标签（例如全員）以 Other / source_local_speaker_label 表示；ID 与原证据保留，不当成已确认独立人物。'),
      ('I. FUC','冻结标记 FUC_RESEARCH_PHASE_COMPLETE_FOR_MOD_DEVELOPMENT 已核验。仅消费 Final Manifest、SemanticMapping、AnimationValidation、BattleRuntimeMapping、BattleGeneralization 与 BattleReplay。state145 保留未命名；Rin Gand Shot 绑定 state159；Lancer FSN248770 是 equipment relation，不凭外形命名 Gáe Bolg。候选 bank／selector scope 及 unknown UI binding 原样保留。没有重新 runtime。'),
      ('J. Official Materials','1,957 page assets 全部保留 page_id／page_asset_id／scan page／printed page。姓名文本引用是 mentioned_in，OCR candidate 保持候选。未增加视觉人物确认。Side Material 历史内容与晚期资料独立追溯。'),
      ('K. Animation References','17 works、337 media、67,499 shots、106,006 subtitle rows。现有 term hits 与 review queue 接入；shot ID 不分配 FSN ID。没有新检测或缩略图生成。scope 明确定义且不表示 canon。高 motion 仅是技术字段。'),
      ('L. Cross-source Entity Coverage',table+'\n所有数量是 distinct source subjects；覆盖数不作质量排序。主要角色页面统一展示六来源，缺少可靠关系的来源保留 0，不为覆盖率强制连接。'),
      ('M. Usage Candidates',f"{counts['usage_candidates']:,} recommendation rows。按 usage_type 计算 evidence／scope／技术质量排名，保存 reason。所有 shot battle_animation 用途只表示可审阅参考，不表示战斗动作或画面人物已确认。"),
      ('N. Review Queue',f"{counts['review_queue']:,} records；只统一既有待审候选和无法匹配记录，不自动审阅或删除 unknown。拒绝与人工确认将新增证据并保留历史。"),
      ('O. Conflicts / Historical Differences',f"{counts['conflicts']:,} records。既有 FUC conflicts 保留，拼写变化单独列出；不宣布历史来源错误。alias variation 是差异记录，不等于事实矛盾。"),
      ('P. Database',f"数据库 `{DB}`。必需 tables、source_subjects、跨源 alias evidence、history 与四套 FTS 均已建立。数据 QA：**{qa['status']}**，integrity_check 与 foreign_key_check 见 SEMANTIC_DATA_QA.json。"),
      ('Q. Browser / Workbench',f"SemanticCatalog/index.html；本机 API，24 条分页，复用全部现有缩略图。组合检索、六来源多选、scope／evidence／usage／type 筛选、证据面板、复制 ID、原来源浏览器回链。实际 UI QA：**{ui['status']}**，环境 **{ui.get('browser','pending')}**；详细点击验收与截图见 BROWSER_ACTUAL_QA.json。Chrome 连接失败与实际使用环境分别记录，不声称 Chrome 通过。"),
      ('R. MOD Selection Export',f"JSON 清单存于 SemanticCatalog/Exports；包含 entity／usage／source_type／source_id／reason／原证据等级／原路径／notes、页或媒体 ID、shot timecode 和完整 evidence。只引用，不复制媒体。实际四类型 UI 导出结果：{ui.get('selection_export','pending')}。"),
      ('S. Stability',f"new FSN IDs = 0。稳定性 status **{stable['status']}**；基线旧文件已检查 {stable.get('protected_files_checked',0):,} 个，元数据 SHA256 检查 {stable.get('metadata_hashes_checked',0)} 个。媒体验证边界为 baseline size／mtime，没有重新哈希媒体。独立 ID registry、源键散列与 revision history 保留。"),
      ('T. Known Limitations','\n'.join('- '+x for x in summary['known_limitations'])+'\n\n未归一的 FHA 说话者字典标签使用 Other，不推断为独立人物；不同来源的短名没有足够 alias 证据时保持独立。\n\n未要求 100% 资产／shot／页面视觉语义化；unknown、candidate 和 on-demand 不阻塞本轮验收。尚未人工确认的职阶词在 Zero 等相关作品中可有不同指代。'),
      ('U. Development Usage','先搜实体与概念，再审证据，按用途筛选，定向审阅少量候选，导出 Selection Manifest。素材真正进入 MOD 工程时才复制 working copy。中文指南：FSN_SEMANTIC_CATALOG_USAGE.md。'),
      ('V. Final Asset-Library Closure Decision',f"**{status}**\n\n"+('**FSN_MASTER_ASSET_LIBRARY_COMPLETE_FOR_MOD_DEVELOPMENT**\n\n素材收集、整理、引用与统一语义基础已足够。本轮后停止大型下载／解包／OCR／分镜／runtime／全量语义标注。下一步：**开始 FSN × Slay the Spire 2 MOD 正式设计**，确定第一批可玩角色、核心机制和卡牌框架。' if passed else '关键验收尚未全部通过，详见数据／稳定性／真实浏览器 QA。不会提前输出 complete marker。'))]
    report_text='# UNIFIED FSN SEMANTIC CATALOG REPORT\n\n'+now()+'\n\n'+''.join('## '+title+'\n\n'+body+'\n\n' for title,body in sections)
    path=L/'Reports/UNIFIED_FSN_SEMANTIC_CATALOG_REPORT.md';path.write_text(report_text,encoding='utf-8');(S/'Reports/UNIFIED_FSN_SEMANTIC_CATALOG_REPORT.md').write_text(report_text,encoding='utf-8')
    summary.update(status=status,final_timestamp=now(),browser_qa=ui['status'],data_qa=qa['status'],stability=stable['status']);dump(S/'Metadata/SEMANTIC_FINAL_SUMMARY.json',summary)
    marker={'status':'FSN_MASTER_ASSET_LIBRARY_COMPLETE_FOR_MOD_DEVELOPMENT' if passed else status,'timestamp':now(),'catalog_asset_count':270798,'max_asset_id':'FSN270798','semantic_revision':summary['semantic_catalog_revision'],'entity_count':counts['entities'],'relation_count':counts['relations'],'evidence_count':counts['evidence'],'source_families':FAMILIES,'animation_shot_count':67499,'official_page_count':1957,'fuc_frozen':True,'known_limitations':summary['known_limitations'],'usage_guide':str(L/'Reports/FSN_SEMANTIC_CATALOG_USAGE.md'),'final_report':str(path),'semantic_status':status,'baseline':str(L/'Reports/UNIFIED_SEMANTIC_PRE_BASELINE.json'),'database_sha256':qa.get('database_sha256'),'new_FSN_IDs':0}
    if passed:
        dump(L/'FSN_MASTER_ASSET_LIBRARY_COMPLETE_FOR_MOD_DEVELOPMENT.json',marker)
        rev=S/'Revisions'/summary['semantic_catalog_revision']
        if not rev.exists():
            rev.mkdir();shutil.copy2(DB,rev/'FSN_SEMANTIC.sqlite');shutil.copytree(S/'Metadata',rev/'Metadata');dump(rev/'REVISION_FREEZE.json',marker)
    else:dump(S/'Reports/SEMANTIC_PENDING_ACCEPTANCE.json',marker)
    c.close();print(status,flush=True);return marker
if __name__=='__main__':report()
