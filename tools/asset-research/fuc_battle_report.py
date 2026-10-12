"""Produce an evidence-gated report for the validated battle-runtime subset."""
from fuc_battle_common import *
OUT=pathlib.Path(r'C:/Users/Murasame/Documents/Codex/2026-10-06/files-pasted-by-the-user-fate-2/outputs')
def link(p,label=None):return f'[{label or pathlib.Path(p).name}]({str(p).replace(chr(92),"/")})'
def main():
 b=battle_frozen();e=readjson(BR/'BATTLE_EVIDENCE_SUMMARY.json');rt=readjson(BR/'GoldenRegression/GOLDEN_EVALUATOR_SUMMARY.json')
 viewers=[readjson(p) for p in (BR/'PlaybackAcceptance').glob('*_viewer-validation.json')];goldenui=readjson(BR/'PlaybackAcceptance/GOLDEN_UI_ACTIONS.json');assert len(viewers)==len(goldenui)==9
 vw=dict(timestamp=now(),models=3,clips=9,frames=sum(x['frames'] for x in viewers),node_comparisons=sum(x['samples'] for x in viewers),max_matrix_error=max(x['max_matrix_error'] for x in viewers),missing_nodes=sum(len(x['missing_nodes']) for x in viewers),validation_failures=sum(x['status']!='PASS' for x in viewers),playback_failures=sum('播放中' not in x['playing'] for x in goldenui),status='PASS' if all(x['status']=='PASS' and not x['missing_nodes'] for x in viewers) and all('播放中' in x['playing'] for x in goldenui) else 'FAIL',viewer='Fresh final Three.js UI validation and playback after all investigation/tool/Gallery changes',chrome_validated=False)
 jsonwrite(BR/'PlaybackAcceptance/GOLDEN_BROWSER_SUMMARY.json',vw)
 st=readjson(BR/'STABILITY_FINAL.json');clean=readjson(BR/'DEBUGGER_CLEANUP.json');equip=readjson(BR/'Playback/lan_equipment_viewer_validation.json');ui=readjson(BR/'PlaybackAcceptance/EQUIPMENT_UI_ACTIONS.json');fan=readjson(BR/'FAN_RUNTIME_PROOF.json');matrix=readrows(BMD/'FUC_EFFECT_MATRIX_COMPARISON.csv');tl=readrows(BMD/'FUC_BATTLE_TIMELINE_EVENTS.csv');audio=readrows(BMD/'FUC_BATTLE_AUDIO_EVENTS.csv');gallery=readjson(BR/'GALLERY_BROWSER_REGRESSION.json');media=readjson(BR/'GALLERY_MEDIA_CHECKS.json')
 gates=dict(A_Golden=rt['failures']==0 and rt['models']==3 and rt['clips']==9 and vw['status']=='PASS' and vw['clips']==9 and vw['max_matrix_error']<=b['golden']['max_threejs_matrix_error']*1.01,B_FAN=len(fan)==3 and all(x['max_error']==0 and x['source_identity_status']=='confirmed_runtime' for x in fan),C_Equipment=e['equipment_runtime_copy_samples']>=2 and equip['status']=='PASS' and len(ui['clips_played'])==3,D_Effect=e['effect_confirmed_resource_count']>=1 and len(matrix)==6 and all(float(r['local_error'])==float(r['world_error'])==0 for r in matrix) and any(r['event_type']=='effect_stop' for r in tl),E_Timeline=any(r['event_type']=='effect_spawn' and abs(float(r['time_seconds'])-.05)<1e-7 and float(r['virtual_frame_60hz'])==3 for r in tl),F_Stability=st['status']=='PASS' and st['missing_old_ids']==st['changed_old_rows']==st['frozen_path_loss']==0 and st['sqlite_integrity']=='ok')
 status='FUC_BATTLE_RUNTIME_MAPPING_PASS' if all(gates.values()) else 'FUC_BATTLE_RUNTIME_MAPPING_PARTIAL'
 s=dict(status=status,timestamp=now(),scope=e['scope'],pass_definition='Minimum A-F subset; not full2056 effects or a complete audio-synchronized battle preview',acceptance_gates=gates,golden_evaluator=rt,golden_browser=vw,evidence=e,stability=st,cleanup=clean,gallery=dict(browser='Codex in-app browser',chrome_validated=False,sample_records=len(gallery['samples']),renderer_unchanged=True,new_separate_entry=str(L/'Gallery/FUC_BATTLE_RUNTIME.html'),original_video_scope='unchanged link-only card, standard first-frame decode; no in-browser Original MPEG playback claim',theora_preview='Remastered042476 prior MP4 preview decoded and played',fuc_video='H264 video decoded and played to end after diagnostic receiver changed to threaded service'),preview=dict(body_equipment_clips=3,attachment_matrix_error=0,full_effect_audio_timeline=False,animated_glbs_added=0,battle_webm_added=0),unknowns=['AMO actual consumer','FAN independent clock unit','effect body153-to-external-matrix latching/offset acquisition formula','complete effect script/material/particle interpretation','upper-layer soundID->bank and clip->audio causal mapping','MOT0x22 and0x40 new runtime semantics','general move/command names','full synchronized battle preview'])
 jsonwrite(BMD/'FUC_BATTLE_RUNTIME_VALIDATION_SUMMARY.json',s);jsonwrite(OUT/'FUC_BATTLE_RUNTIME_VALIDATION_SUMMARY.json',s)
 idx='\n'.join(f'- {link(p)}：{len(readrows(p))} 行。' for p in sorted(BMD.glob('*.csv')))
 report=f'''# Fate/unlimited codes Portable Europe 战斗运行时验证报告

**{status}**

验收范围：FAN 角色姿态/纹理控制、Lancer 身体与枪、一个实际 SEQ 特效、底层声音样本播放。满足用户定义的 A–F 最小标准。完整的 Body + Weapon + Effect + Audio 同步战斗预览仍未恢复；AMO 实际消费、声音上游因果映射和特效外部矩阵来源偏移公式仍为 unknown。

## A. Baseline

冻结前资产数 **268,504**，FUC Europe **21,899**，最大 ID **FSN268504**。冻结旧 AnimationValidation 索引、报告、工具、9 个动画 GLB、预览和 Gallery HTML/JS/metadata；527 个关键文件共 1,665,395,954 字节有 SHA-256、大小及可用行数，轻量备份在 `E:/FSN_MASTER_ASSET_WORK/backups/fuc-battle-runtime-pre`。未复制 RawExtracted 或 ISO。

Golden 为 sir/rin/lan 三个已证实模型、9 条 clip0/1/2。新工作目录 `E:/FSN_MASTER_ASSET_WORK/fuc/BattleRuntimeMapping`，新索引目录 `E:/FSN_MASTER_ASSET_LIBRARY/FateUnlimitedCodesPortable_Europe/Metadata/BattleRuntimeMapping`。旧 AnimationValidation 层不改写。

证据：{link(L/'Reports/FUC_BATTLE_RUNTIME_PRE_BASELINE.json')}。

## B. Golden Regression

| 最终验收 | 数量 | 结果 |
|---|---:|---|
| 模型 / clip | 3 / 9 | PASS |
| 新运行 evaluator 对原冻结游戏 pose | 45 帧 / 2,535 节点 | 0 failures；最大 TRS/local/world 误差 0 |
| Three.js 新逐帧验收 | 286 帧 / 16,357 节点 | 0 missing node；最大矩阵绝对误差 {vw['max_matrix_error']:.16g} |
| 浏览器实际播放 | 9 条 | 0 playback failure |
| 9 个 Animated GLB | 原文件 SHA 相同 | 未重新导出；原 Khronos Validator 通过记录继续成立 |

运行时回归是**新 evaluator 运算对既有、冻结的真实游戏 45 帧采样**，没有冒充本轮重新采集全部受控帧。Three.js 验收及播放按钮操作在全部运行时调查后重新执行，证据写入新的 PlaybackAcceptance 目录。

证据：{link(BR/'GoldenRegression/GOLDEN_EVALUATOR_SUMMARY.json')}、{link(BR/'PlaybackAcceptance/GOLDEN_BROWSER_SUMMARY.json')}、{link(BR/'PlaybackAcceptance/GOLDEN_UI_ACTIONS.json')}。

## C. FAN

1,271 个逻辑文件、470 个唯一 payload。全部符合 `16-byte LE header + entry_count ×16` 的边界规则；未识别出 ASCII magic，header 第二字不能凭常见值1宣称版本。

角色 loader `08832A68` 通过 `088869D8(a0=path,a1=0x1000)` 请求 FAN，保存资源到 `char+44` 的64槽表；资源 wrapper 的 `+34` 是原始 LE payload，`+10` 为文件名。实际读取 Rin、Shiro 的68次 FAN，AMO11次，79个成功 loader 结果保留；237条逻辑索引可按 payload prefix 比对，包括 costume 来源中的相同内容，不代表237次独立消费。

`08832880` 设置 FAN选择与 `char+184` 状态、`char+1C0` payload。`088326F4` 按整数 frame 选择 payload+10 的16字节记录：frame、mode/BPO index、texture selector A、texture selector B/AMO index。mode>=0 调 `08831E90`；-2/-3 指向 AMO 分支；-1 不应用姿态。

实际 Lancer `2000.fan` 完整128字节与当前 payload相同。原游戏 evaluator `a1=2` 在三次自然调用后，boneID55 remap到 GMO ordinal9，输出 translation `(0,-0.004000000189989805,0,1)`、Euler储存 `(0,0,16,1)`，精确匹配原 `2001.bpo` 的浮点值，最大误差0。调用前该状态已经相同，因此这里证明**源文件身份、消费者与实际输出一致**，不声称此调用首次改变了节点。

这是角色 FAN 的实际姿态/纹理控制链；并未证明 FAN 是全身 MOT bank、招式图或 VFX 全局事件表。BPO 的 Euler 存储和已有 MOT direction+roll 存储是不同路径，未改变旧 evaluator。

纹理消费者 `08831920`：selector=-1保留，0恢复缓存；正值经过字符 ID 表达式查询并写 SDK texture table。A 对应 body+50，B 对应 body+54；未把全部 selector 强命名成具体眼睛/嘴图片。FAN 时钟推进 `08832584` 及 `char+5CC*2` 已静态追到，但独立 FPS/时钟单位未动态证实。

证据：{link(BR/'LoaderTrace')}、{link(BR/'FAN_RUNTIME_PROOF.json')}、{link(BMD/'FUC_FAN_INDEX.csv')}。

## D. AMO

154 个逻辑文件、27 个唯一 payload，全部头/selector范围检查通过。`088869D8` 的 AMO 分支使用 flag4000，`08832A68` 存入 char+164 的8槽表；源 payload LE 未改写。

FAN mode -2 调 `08832220`，-3 调 `088320C4`。静态字段读取表明 AMO header+4/+8 指向 character BPO 表 char+144；+C 为 step divisor，+10 控制 selector 序列模式/长度，+14 起为 selector序列。文件末尾 -1 等值原样保留。没有证据支持把 AMO 扩写成某个英文名称或普通 MOT bank。

**AMO loader 已有 runtime 证据，实际 interpolation consumer 本轮未命中。** 因此角色 AMO 的消费关系仍为 confirmed_static_reference，不能与 FAN 已验证角色输出混为一谈。B 门槛由 FAN 的闭环满足。

证据：{link(BMD/'FUC_AMO_INDEX.csv')}、{link(BR/'Static/08832220_088326f4.txt')}。

## E. Animation Banks

复用旧真实自然运行证据：player+2C指 bank array，+30 为槽数；sir/rin/lan bank0为各自 chr/code/0000.mot，bank1为 `chr/cmn/0000.mot` **FSN251096**，源来自 cmn/sys.fpk。原 NATURAL CAPTURE 的所有 offset slots及 payload字段匹配，未仅按文件前缀猜测 common bank。

本轮 Lancer player09C6B290，bank0=09422650；clip145 源 offset811E0，当前 clip pointer094A3830，满足 `09422650+811E0=094A3830`，当前 idx=145，关联旧 clip资产 **FSN258272**。没有给该动作招式名。

FAN/AMO 与 MOT bank 的选择、costume/state切换和 move→bank/clip 规则未确认，表中对应字段留空。

证据：{link(BMD/'FUC_ANIMATION_BANK_RUNTIME_MAP.csv')}、{link(AW/'Runtime/Natural/Round2/player_09c52740/CAPTURE.json')}、{link(BR/'EffectTimelineHeld/000_entry.json')}。

## F. Equipment

Lancer body **FSN248769 chr/lan/0000.gmo**，枪 **FSN248770 chr/lan/0001.gmo**。枪有独立4-node GMO；实际 wrapper09C581E0、SDK09C4FEA0。现有静态 GLB 的路径别名可能显示0201，payload SHA与该逻辑0001资产一致；未重新转换。

character09C09700+5DC 为 attachment record09C09CDC。记录strideC8，共8槽；每槽4个装备子node ID。当前 +4=枪wrapper、+8=装备boneID0，+18=bodyboneID153；其他三个装备子槽为-1。局部偏移 translation0、Euler0、scale111。

body bone153 → GMO ordinal32 `w_153R` → GLB node42；weapon bone0 → ordinal1 → GLB node2。body R_hand 是 bone15/ordinal29，其矩阵与实际来源不同，未把“看起来挂右手”当成绑定规则。

`08837D04` 遍历活跃记录，`08837964` remap并取 body153 world，`089449AC` 把64字节复制到 weapon ordinal1 的 runtime+F0，再经 `08877378` 组合到 SDK local/world。5次 attachment自然调用、2次原matrixcopy；两次 source/destination 最大绝对误差及 Frobenius误差均0。

## G. Lancer Probe

完整证据链：

```text
character09C09700
  +3C -> body wrapper0941BE30(初始采样) /0941D560(后续)
  +5DC -> attachment record09C09CDC
  record+4 -> weapon09C581E0 (chr/lan/0001.gmo)
  record+18 -> body bone153
  body remap -> ordinal32 -> SDK09C7F200 +F0=09C7F2F0
  record+8 -> weapon bone0 -> ordinal1
  08837964 ->089449AC -> weapon09C58750
  08877378 -> weapon SDK local/world
```

heap 地址仅用于本次运行的采样，下一次运行要重新从参数/记录发现，不能硬编码当永久ID。viewer 根据已证明的bodyGLB42 world设置 weaponGLB2 local，明确转换 `inverse(weaponParentWorld) × body153World`，未试+1/-1骨骼偏移。

独立 Three.js 检查初始枪4个world矩阵及2个parentcopy，共6个矩阵，误差0；旧body clip0/1/2均实际播放。未观察到当前枪的独立MOT；任意武器 visibility事件、palette/material覆盖与武器特殊motion未确认。

证据：{link(BR/'EQUIPMENT_RUNTIME_PROOF.json')}、{link(BR/'WeaponAttachmentNatural')}、{link(BR/'Playback/lan_equipment_viewer_validation.json')}、{link(BR/'PlaybackAcceptance/EQUIPMENT_UI_ACTIONS.json')}。

## H. VFX Runtime

确认一个真实资源：**FSN248817 eft/chr/lan/1002.gmo**。执行程序为 **FSN248810 eft/chr/lan/1000.seq**。运行时SEQ base094E2AC0与原30,608字节逐字节比对，仅+0C的4字节 loader资源指针 relocation字段不同，其他30,604字节相同；dump末尾32字节overread排除。未误报整个runtime dump SHA相同。

原战斗 VM caller0897EC64 → `088D4354(ctx,model descriptor)` 激活/重配置预分配效果实例。ctx08D8CE64，实际clone wrapper09530C10、template094F7BE0、nodecount3。owner稍后设置为character09C09700。这里是池中对象的**真实激活/复用**，没有把资源已加载或wrapper存在当成spawn。

ctx结构98字节：+0 flags，+4 state，+8 owner，+C contextID，+10 thread指针数组，+38 threadcount，+3C model-record数组，+64 modelcount，+68执行command计数，+74bytecodebase。+68不能当时间。

callback `088D3A80`、thread更新 `088D37EC` 被原游戏自然调用。两次完整episode各9次callback：state0→1→F0，threadPC清0；下一次cleanup清model flag20000并设bit1，ctx保留在池中。已有模型cache不删除，不能称为destroy source resource。

模型命令 caller088CDB28 →原 `08877378`，两次实时变换消费对3个节点的 local/world共6组数值比较，最大误差0。程序控制node1 scaleY0.4与0.8；这是实际effect TRS，**不是 MOT0x22 的新验证**。

证据：{link(BR/'EFFECT_SEQ_SOURCE_PROOF.json')}、{link(BMD/'FUC_EFFECT_RUNTIME_INDEX.csv')}、{link(BMD/'FUC_EFFECT_UPDATE_TRACE.csv')}、{link(BMD/'FUC_EFFECT_MATRIX_COMPARISON.csv')}、{link(BR/'EffectNearCleanup')}。

## I. Motion → Effect

自然按键episode中，当前body MOT bank0 clip145 **FSN258272** 在 `time=0.05000000447034836`、dt0.01666666753590107被捕获。其虚拟帧=3。此时原 VM 正在调用效果激活函数，后续同ctx owner确定为Lancer，资源为1002.gmo。

事件源是实际 SEQ/battle VM，而非 MOT track或FAN/AMO。本记录证明这次真实激活发生在该clip的此时刻，不声称所有move/state上下文每次都固定在帧3，也未命名招式。

证据：{link(BMD/'FUC_MOTION_EFFECT_EVENTS.csv')}。

## J. Effect Attachment

effect thread08DA8A04+14保存了body153 world pointer09C7F2F0。这确认了实际bone来源引用。effect node1的runtime+F0保存外部矩阵；原模型消费将它与当前TRS组合，SDK层级继续生成world矩阵，已做数值闭环。

**该效果并非已证明全程identity地跟随当前bone153。** 采样world与当前body153 world不相同；“连续直接骨骼附着”假设记为rejected，外部矩阵取得时的锁定/偏移/space处理仍unknown。此处D门槛由已确认的真实外部world矩阵应用、资源激活与生命周期满足，不借此宣称完整的bone attachment公式。

矩阵证据从 `08877378` 的原始输入TRS与external matrix重新计算，测试样本 rotation=0，scaleY=.4/.8，T=0；6节点local/world全部误差0。对其他Euler角度、particle physics、camera/screen attachment不泛化。

证据：{link(BMD/'FUC_EFFECT_ATTACHMENTS.csv')}、{link(BMD/'FUC_EFFECT_MATRIX_COMPARISON.csv')}。

## K. Audio Events

European ELF 的 sceSasCore import table独立核对：NID99944089→stub089B0598 SetVoice，NID76F01ACA→stub089B0590 KeyOn。名称与签名参考 [PPSSPP官方SAS实现](https://github.com/hrydgard/ppsspp/blob/master/Core/HLE/sceSas.cpp)，游戏地址和样本选择来自本机欧版，不以外部项目替代游戏证据。

`08949A88` voice-record 起播路径 → `0894A314` 提交ADPCM → `0894A1AC` KeyOn。record stride68，+20 payload，+24大小。三次**自然 key-on entry**同步dump完整payload，返回值均0：

| 样本 | 当时body clip/time | 字节 | 源匹配 | 层级 |
|---|---|---:|---|---|
| slot0 | 145 /0.06666667014360428 | 11,520 | battle.phd subsong23 /FSN261974 | confirmed_runtime |
| slot1 | 145 /0.06666667014360428 | 5,744 | chr_lan00.phd subsong4 /FSN260984 | confirmed_runtime |
| slot2 | 145 /0.0833333358168602 | 3,152 | 15个库中相同payload，含lan subsong54 /FSN261033 | confirmed_runtime，源bank歧义保留 |

三段SHA精确匹配已有音频索引和资产，未重新解码音频。**SAS voice slot≠sound ID**；表中sound_id留空。完整上游soundID→bank/program和clip/effect→sound因果关系仍unknown。当前clip的时间仅是同时观测到的body clock，不能把混音器调用时间自动当成动作事件的命令时间，也没有据此拼统一声音轨。

证据：{link(BR/'AudioKeyOnPayload/AUDIO_KEYON_SUMMARY.json')}、{link(BMD/'FUC_BATTLE_AUDIO_EVENTS.csv')}。

## L. Battle Timeline

已恢复同一effect episode的2条真实记录：

| 事件 | body时钟 | 60Hz虚拟帧 | 实际消费者 |
|---|---:|---:|---|
| 1002.gmo pooled activation |0.05000000447034836 |3 |088D4354 |
| effect stateF0 /threadPC0 |0.1666666716337204 |10 |088D3A80/088D24CC |

效果thread有独立fixed8 wait：普通tick减0x100，即256；源wait立即数左移8。实际出现256、1024、768、512、256、0。body时间序列中0.1秒重复一次，表明callback与body推进不能简单等同。记录9个update callbacks和一次后继cleanup，不将9callbacks强写成9/60秒生命周期，不用调试主机wall-clock算游戏时间。

声音是在另一自然采样episode记录的，尚未证明上游事件源；没有把两次episode手工拼成完整battle timeline。

证据：{link(BMD/'FUC_BATTLE_TIMELINE_EVENTS.csv')}、{link(BMD/'FUC_EFFECT_UPDATE_TRACE.csv')}。

## M. Additional MOT validation

本轮没有新增MOT动画GLB，仍只有9条原validated clip。没有批量导出剩余3,667条，没有升级0x22或0x40语义。effect的script scaleY不是MOT轨道。旧60Hz、rotation direction+roll、Linear source interpolation、缺scale默认1等Golden结论保持原范围。

## N. VFX Formats

BAM/TUV/MIL/PAR没有本轮实际消费者闭环，索引保持unknown。wrapper/同FPK只能作容器线索。没有把2,056个VFX强行语义化，没有猜粒子/材质格式。已恢复的是SEQ effectcontext、线程wait/end、模型变换命令和复用生命周期的validated subset。

证据：{link(BMD/'FUC_VFX_FORMATS.csv')}。

## O. Preview

新增 `Converted/BattleScenes/lan_attachment`，复用3条旧bodyGLB与已有weaponGLB，通过runtime-confirmed bone mapping显示Lancer身体与枪。独立viewer附着6矩阵误差0；实际clip0/1/2播放。现有颜色与游戏palette仍有差别，未宣称材质完全一致。

**完整效果/声音战斗预览=0；新的battle WebM=0；新的Animated GLB=0。** 未用手工资源拼接补齐未知演出。已有3个animation WebM保留。本页明确显示哪些部件已验证、哪些未接入。

预览入口：{link(L/'Gallery/FUC_BATTLE_RUNTIME.html')}。在已有Gallery服务8986下可直接打开，输出目录另附打开预览脚本。

## P. Gallery

主renderer、catalog.js、preview_map与旧animation overlay完全不修改。新增独立 `Gallery/FUC_BATTLE_RUNTIME.html` 作为附加入口，不向未知MOT卡贴battle verified标签。

Codex in-app browser已抽样：四来源图片显示、四来源audio播放；Remastered Theora的原MP4 preview、FHA MP4与FUC MP4播放。FUC视频实际到达end，frame480×272；早期ready0是本轮单线程证据server阻塞，切换独立诊断receiver为threaded后同一原文件正常。未改视频、Gallery索引或原Gallery服务。

Original MPEG本来是link-only卡；本轮核对原链接和独立FFmpeg首帧解码，**不声称Original MPEG已在浏览器内播放**。各版本筛选数量仍42,546/160,056/44,003/21,899，四来源第二页均60卡；静态GLB link、validatedAnimatedGLB入口、MOT未验证提示、已有动画WebM也核对。旧Theora preview机制继续有效。

**Chrome not validated**。这是in-app browser和标准媒体验证，没有冒充真实Chrome。

证据：{link(BR/'GALLERY_BROWSER_REGRESSION.json')}、{link(BR/'GALLERY_MEDIA_CHECKS.json')}。

## Q. Stability

| 项目 | 最终结果 |
|---|---:|
| asset_total /max_id |268504 /FSN268504 |
| FUC Europe资产 |21899 |
| 新逻辑ID |0 |
| missing old IDs |0 |
| changed old rows |0 |
| frozen critical file changes |0 /527 |
| protected path references |624836 |
| unique protected paths |456988 |
| frozen path loss |0 |
| 341 static GLB changes |0 |
| SQLite integrity |ok |

CSV、JSONL、SQLite Catalog逐字节SHA相同，证明旧行/字段值及ID未改变。冻结path存在且大小保持；未重算全库Raw所有payload SHA，也不把这一点冒充完整逐字节Raw验证。未解包ISO/FPK、未修改Raw/Preservation、未重新编号、未重生成静态GLB。

独立PPSSPP PID49580已关闭；最后列举CPU和memory breakpoints均为空，未安装RAM hook，未写diagnostic EBOOT。原用户PPSSPP配置/存档未访问。调试结束时全按钮release请求含不支持的l/r键被拒绝；各probe finally此前已释放用过的triangle，随后关闭独立进程。辅助脚本已修正支持键，错误如实保留。旧Gallery服务保持运行。

证据：{link(BR/'STABILITY_FINAL.json')}、{link(BR/'DEBUGGER_CLEANUP.json')}。

## R. Failures / Unknown

- AMO实际 interpolation consumer未命中；FAN独立时钟单位未动态确认。
- effect外部矩阵的完整body-source锁定/偏移公式、材质、内部全部opcode/particle行为未知；不能宣称全程bone153 identity附着。
- sound ID上游、bank/program动态解析、clip/effect与声音的因果命令尚未恢复。底层key-on与payload闭环不能代替它们。
- gameplay/root镜像、blend/transition/loop新上下文、costume bank规则、武器palette/特殊motion没有新confirmed结论。
- 0x22/0x40未额外验证；招式、台词语义未猜测。
- 多个candidate factory/clone函数probe未命中不代表函数不存在；仅不升级其与当前样本的关系。
- 早期约250个并行memory-write watch导致独立PPSSPP崩溃；保留失败记录，重新启动后改用少量原函数条件断点完成闭环，没有重复大量watch或修改ISO。
- 早期无限制MIPS xref把数据区当代码；最终xref脚本限定ELF SHF_EXECINSTR。误读089D区域的结果保留但不纳入confirmed函数表。
- 预览只显示body+枪，未输出完整带效果/声音的battle视频。

## S. Recommended next step

**扩大 Battle Runtime 到更多角色**。

限定先在已验证的sir/rin上下文复现equipment/FAN/SEQeffect规则，同时补当前Lancer effect外部矩阵取得时的锁定/偏移与soundID上游闭环，再决定是否合成完整战斗预览。当前仍不适合全roster批处理或招式语义命名。本轮到此结束，不执行下一任务。

专门索引：

{idx}

可复现工具保存在 `E:/FSN_MASTER_ASSET_WORK/scripts/fuc_battle_*`。输出复现包包含新脚本、选定原runtime captures、静态scope反汇编与新索引；保留库仍是唯一源。重采样地址必须从当次对象参数重新定位，原heap地址不能视为永久资产ID。
'''
 (L/'Reports/FUC_BATTLE_RUNTIME_MAPPING_REPORT.md').write_text(report,encoding='utf-8');(OUT/'FUC_BATTLE_RUNTIME_MAPPING_REPORT.md').write_text(report,encoding='utf-8')
 print(status);print(gates);assert all(gates.values())
if __name__=='__main__':main()
