"""Publish only additive report/overview files after evidence and preservation gates."""
from fuc_general_common import *
import html

def main():
    s=readjson(BMD/'FUC_BATTLE_GENERALIZATION_SUMMARY.json');g=s['golden_browser'];ev=s['golden_evaluator'];st=s['stability'];p=BR
    assert s['status']=='FUC_BATTLE_RUNTIME_GENERALIZATION_PASS'
    b=readjson(BB/'BASELINE.json');hashes={pathlib.Path(r['path']).name:r['sha256'] for r in b['files'] if pathlib.Path(r['path']).parent==L/'Metadata'}
    report=f'''# FUC Battle Runtime Generalization

**{s['status']}**

本轮 A–E 底层系统验收通过；**完整 Body + Weapon + Effect + Audio 同步预览未完成**。未新增 asset_id，未新增 animation GLB，未重新解包或转换模型。版本始终为 `FateUnlimitedCodesPortable_Europe`。动作继续保留 clip 编号。

## A. Baseline

资产总数 **268,504**，FUC Europe **21,899**，最大 ID **FSN268504**。本轮冻结 72 个轻量关键文件，共 3,788,829 字节；另引用继承的 527 条冻结文件和旧保护路径基线。未复制 ISO、RawExtracted、大型媒体或整个 WORK。

本轮基线：`E:\\FSN_MASTER_ASSET_LIBRARY\\Reports\\FUC_BATTLE_GENERALIZATION_PRE_BASELINE.json`；备份：`E:\\FSN_MASTER_ASSET_WORK\\backups\\fuc-battle-generalization-pre`。旧 AnimationValidation、BattleRuntimeMapping、`fuc_motion_evaluator.py`、`fuc_battle_*` 均保持字节不变。新研究只使用 `fuc_general_*` 和独立 BattleGeneralization 目录。

## B. Golden Regression

| 检查 | 本轮重新执行结果 |
|---|---|
| 原 3 models / 9 clips evaluator | {ev['pose_frames']} 帧 / {ev['nodes']} 节点；失败 0；所有 TRS/local/world 最大误差 0 |
| Three.js GLTFLoader + AnimationMixer | {g['frames']} 帧 / {g['node_comparisons']} 节点；missing 0 / failure 0；最大矩阵误差 {g['max_matrix_error']:.16g} |
| 实际 Play 控件 | 九条均观察到 playing=true 与正时间；装备三条均显示身体与枪播放中 |
| Lancer 装备 viewer | 6 个原运行时参考矩阵；最大元素误差 0 |
| 原 Lancer SEQ | 两个新自然样本与 FSN248810 源字节完全一致，仅 +0x0C 四字节加载重定位不同 |

evaluator 是对冻结的原游戏 45 帧姿态重新计算，**不是九条 clip 新做一轮自然战斗采集**。Three.js 本轮确实重新加载、逐帧验收和播放，并在最终脚本完成后再次执行验收。验收文件位于 `{p}/GoldenRegression` 与 `{p}/GoldenFinalPlayback`，前一轮本次验收还保存在 PlaybackAcceptance。所有旧 GLB/WebM 和 viewer 文件未改。

## C. Character Runtime Layout

会话为独立 PPSSPP PID30860 / 欧洲版 NPEH00007。对象从真实 `08832A68` 加载入口重新发现：

| 自然样本 | Character | Body wrapper | Body asset |
|---|---|---|---|
| Lan 对 Sir | 09C656A0 | 0945A3B0 | FSN248769 |
| Sir CPU，第一场 | 09B63CF0 | 09C019B0 | FSN250564 |
| Sir 主动，第二场 | 09BF4160 | 08E7CB20 | FSN250564 |
| Rin CPU，第二场 | 09B679B0 | 09640410 | FSN249429 |

这些地址仅是历史采样证据，下一次运行必须重新发现。共享字段由消费者访问证明：body+3C、MOT player+40、FAN slots+44、BPO+144、AMO+164、FAN state+184、current payload+1C0。`08837D04` 在三个角色上下文使用 `+5DC / 8×0xC8` 装备布局。

MOT player+2C 是八槽 **MOT data-base 指针数组**，不是 resource-wrapper 数组；+30 是容量 8，并非已加载 bank 数。Sir/Rin 的 bank0 分别为 FSN250621 / FSN249468，bank1 为 FSN251096。四份源表合计 920 个 offset slot 全部满足 `runtime_pointer = base + source_offset`（空槽为0），长度也完全一致。加载后的 count 是 +6 LE uint16，+8 是重定位表地址。证据：`MOT_BANK_SOURCE_PROOF.json`。

## D. FAN Generalization

自然链 `08832A68 load → 08832880 select → 088326F4 evaluate → 08831E90 BPO → bone55 remap → runtime node` 在 Sir/Rin 中复现。新采样 **22** 次，T XYZ 与 Euler XYZ 六个值逐项源文件比较，最大误差 **0**。原 Lan 的证据继续冻结。

| 角色 | source bone ID | GMO ordinal | 关键证据 |
|---|---|---|---|
| lan |55|9|原 Golden FAN proof |
| sir |55|21|BPO1 非零值：T=(0,-0.004000000189989805,0)，Euler=(0,1,19)，10次完全一致 |
| rin |55|18|BPO0 的零 pose 经实际消费者应用，6次完全一致 |

这证明共享 remap 方法，不能把 source ID 当 GLB joint ordinal。BPO Euler 与 MOT direction+twist 是不同表示。本轮直接证明当前 key 输出，没有把 key 间插值升级为泛化确认。

167 条 FAN/BPO/AMO 运行时 payload 与对应保留源前缀相符；大于捕获长度的条目只称 prefix match。Rin 的 `08831AA8` 还捕获两次真实 texture-selector 输出：frame1 的 selectors A5/B6，对应缓存 `00970004 / 00A70005`，与原 `08831920` 资源键编码完全一致。最终图片身份/表情语义仍未命名。独立 FAN FPS/时钟换算仍 unknown。

## E. Equipment Generalization

读取全部 8×C8 记录，并自然命中 Sir/Rin `08837D04` 迭代器。登记模型：Lan1、Sir6、Rin1，共8个；保留 `equipment_model` 分类。

Lan 的有效挂接仍是 Golden：body bone153 → ordinal32 → GLB42；equipment bone0 → ordinal1 → GLB2，原真实矩阵复制与本轮 viewer 重建误差均为0。

Sir/Rin 捕获的登记记录 flags=0、equipment bone selectors=-1；虽然模型已注册、布局与默认 T/R/S 已读到，**有效挂接、激活时机和矩阵复制未确认**。不能因为 body selectors 默认15 就宣称“挂在手上”，也没有猜 weapon/accessory/gem 语义。

## F. Shiro Probe

两场新自然加载；第二场主动操作。FAN 加载/选择/consumer、BPO1 非零姿态和装备迭代器得到运行时证据。自然 square 样本 current body bank0 clip144 / t=0.05000000447034836 命中 `0897EC64 →088D4354`，激活 `eft/cmn/1004.gmo`；随后六次 update 捕获同一框架。其 SEQ 完整匹配 FSN251097 `eft/cmn/1000.seq` 31,712字节，只有 +C 重定位不同。

但 ctx+8 / thread+10 都为0，不能仅凭当前 Sir clip 宣称该公共效果归属于 Shiro。它的资源与框架已证实，角色因果关联保留 candidate。另一 cross 样本激活 `eft/cmn/1014.gmo`，也不冒充角色专属效果。

## G. Rin Probe

重新发现 Rin 对象、body、八槽 MOT bank 阵列、64 FAN /8 BPO /8 AMO 槽和装备记录。FAN load/select/consumer、BPO0 pose、两次 texture-selector 缓存编码、装备迭代器均已捕获。body bank0 全228 offset 与保留源对应。Rin 此次为 CPU 样本，未取得角色拥有的 effect activation、有效装备挂接或非零 BPO1 应用；这些状态继续 unknown。

## H. Lancer Effect Matrix Provenance

目标为 effect `eft/chr/lan/1002.gmo` runtime ordinal1 的 `RT+F0`，本次地址 `0956DFD0`。精准单地址 write breakpoint 实际命中：

| 写入/计算阶段 | 真实函数/调用者 | 数据来源 |
|---|---|---|
| 初始化 |089449AC，caller088D4E5C，return088D4E64|模型模板的初始化矩阵 |
| basis XYZ 列写入 |08944668，caller088C9850，store08944678|body153 world matrix 的对应列 |
| 源偏移装入 |08944848，caller088D02A0|08B1E150 常量 vector (0,2.4,0,0) |
| offset point 变换 |089449F0，caller088CF9A8，return088CF9B0|094209D0 body153 world × stack vector (0,2.4,0,1) |
| 平移列写入 |08944668，caller088C9A88，return088C9A90|thread+3C 缓存的变换结果；destination0956E000 |

对本次程序建立的规则是：

```text
E_external = W_body153_at_birth × Translation(0, 2.4, 0)
```

继承出生时方向，平移为完整 world matrix 乘局部偏移点；并非只复制骨骼平移或使用 identity basis。这里出生快照指首次矩阵指令执行时读取的真实source矩阵；activation时body t约.05，矩阵指令时t约.06667，两者不混为同一采样相位。两次独立出生位置样本的 world T 分别为 `(2.5122554302215576,1.0272345542907715,0.08906278014183044)` 和 `(3.1238648891448975,1.0272345542907715,0.08906278014183044)`。**两次16元素最大绝对误差=0、Frobenius误差=0**；matrix-vector 输出也误差0。永久工具 `fuc_general_effect_pose.py` 用冻结evaluator的F32有序乘法再次逐元素复核，结果同为0。

两个后续 episode 合计22次callback快照中，external矩阵变化=0；当前body153矩阵分别最大变化约0.08107328414916992和1.912119626045227。body clock确实从约.06667/.11667继续推进。因此本资源在观察区间采用 **snapshot**。basis/point 指令在出生时写入，等待更新保持缓存；这不宣称所有SEQ都相同或不存在后续其他命令重写。

“持续无偏移 identity follow bone153”的旧 rejected 规则保持 rejected。两个出生公式样本与两个后续观察 episode 分开存档，不拼造成同一次录制。

## I. Effect Generalization

Lan FSN248810→FSN248817 的 owner、自然 activation、TRS consumer、update/cleanup Golden 继续成立；新增外部矩阵 acquisition/offset/snapshot 证明。

Sir 情境下同一 activation/update框架及另一个公共资源已命中，但角色所有者尚未闭合。只将 FAN/BPO 和装备记录布局升级为 `confirmed_multi_character`；**角色拥有的 effect 规则保持 Lan 单角色范围**。没有对其他2,056 VFX资源泛化，没有招式命名。

## J. Sound Request Runtime

捕获一次自然、未注入的完整请求链：

```text
0898D91C character battle VM
→ 089A8264(character, sound_id=232D, flags=4, priority=4)
→ 089A84A0 →08874990(category1, actual ID232D)
→ returned queue089F9B5C, encoded042D
→ queue consumer08875218 →08946A9C(bank2, group0, program44, key60)
→ 089477BC PPHD program/sample lookup
→ voice record08A142B4
→ 08949A88 →0894A314 SetVoice →0894A1AC KeyOn
```

实际返回的同一 queue 指针在 consumer s0 中保存；encoded ID 未变；parser bank/program 与 consumer 参数相同；lookup返回 payload/length 与 voice+20/+24 完全相同，再与 SetVoice 参数相同；两个原 SAS 调用均 return0。十项因果审计全部通过。不是“clip正在播放，同时出现声音”的时间共现。

调用者0898D91C从真实VM列表读取所选ID（含列表随机选择），因此记录实际sound ID；还未恢复源move/command名称或源文件opcode。不把此声音强行归入 `1000.seq`；SEQ直接sound调用的有限探针未命中。

## K. Sound ID → Payload

| 域 | 本次实际值 |
|---|---|
| sound request ID |0x232D |
| logical group |35 /0x23 |
| logical bank |4 |
| registered bank |2 |
| requested program /group |44 /0 |
| PHD source |snd/se/chr_lan00.phd，FSN251363 |
| selected subsong |5 |
| payload/source audio asset |FSN260985 |
| PBD offset /payload length |14992 /6768字节 |
| SAS voice slot |0，独立于 sound ID |

注册bank通过逻辑handle+8取得；bank record/header/body来自真实数组。voice+10是logicalgroup，+14是registeredbank，不能把它们误标成bank/program。

运行时 PPHD 全16,172字节与保留源SHA完全相同；PBDbase08ED1F20+14992=payload08ED59B0；全6768字节与既有Raw音频对象完全相同，SHA-256 `d096917d381d9af6ca4e4ba8bccb34cc68d547dc4a37224f11587a7b3508ac4d`。现有转换件为该源已有22050Hz FLAC。

已区分voice源bank、SE候选路径和system/UI未知域。角色bank和真实voice请求路径可记录，但对白/说话人语义仍unknown；不能因为路径在snd/se或使用SAS就把全部音频混成一种。当前只有一个sound ID正式闭合，没有批量扩展。

## L. AMO Runtime

加载/表存储/静态引用继续保留。针对 `08832220` 和 `088320C4` 各做8秒低开销自然probe，未命中；不把wall-clock长度记作游戏时间。`runtime_consumer_not_observed`，无插值PASS、无伪造AMO proof表，未无限刷状态。

## M. Battle Timeline V2

新表按episode保存26行：activation、sound request、SAS KeyOn、公共效果观察，以及22次snapshot update。分别使用 `body_60hz`参考、`effect_fixed8`、`audio_runtime`；native wait原值保留。`body_time_at_event`仅是事件发生时读到的body时钟。native audio sampleclock及effect→body转换仍未恢复，原生事件时间不能由host调试时间代替。

effect与audio闭环来自不同episode，**没有把它们拼成一条同步预览时间轴**。源事件opcode无法证明时留空。clip145/144不猜招式名。

## N. Data-driven Battle Preview

**完整同步预览=0，新animation GLB=0。** 已保留的clip0/1/2 body+weapon预览可以继续使用；sidecar同时展示新矩阵和声音证据，但不自动同步组件。

实际进行了clip145导出资格探针：用当前evaluator在body t=.06666667计算raw单clip，与effect阶段取得的自然战斗SDK local矩阵比较，最大差异 **1.4718526005744934**，不通过。该快照没有独立锁定body矩阵更新相位，也没有隔离FAN、gameplay矩阵和可能的transition/blend，因此不能用这个差异反向猜bone偏移/时间偏移，更不能导出“看起来动”的GLB。具体原因仍需专门姿态参考采集；没有把某个blend解释当成已确认。

还缺完整SEQ渲染命令/材质覆盖、effect-native时钟映射、同一episode的声音和效果同步，以及SAS音高/样本时钟重放验收。提供 `FUC_BATTLE_PREVIEW_READINESS.json`，**不是 completed preview manifest**。没有手工猜音效时机、特效寿命或挂点，没有新增伪同步WebM。

按用户第52条，本轮C/D真实闭合且完整preview不属于A–E硬门槛，因此系统结果可以PASS；这个PASS不授权完整战斗预览。

## O. System Rules

三角色 FAN/BPO state布局与source-ID remap、八条装备记录迭代布局为 `confirmed_multi_character`。有效装备附着、birth offset/snapshot和sound-ID链为 `confirmed_single_sample`，范围只覆盖Lan实证。公共effect角色归属candidate；AMO、FAN clock、完整同步preview unknown；continuous identity follow rejected。

全部十个要求CSV及summary已保存 `{BMD}`，另有snapshot trace、texture proof、audio classification、clock/readiness sidecar。原BattleRuntimeMapping和AnimationValidation各表不改，旧结论不会被覆写。

## P. Gallery

主Gallery HTML/JS/data不改。新增 `E:\\FSN_MASTER_ASSET_LIBRARY\\Gallery\\FUC_BATTLE_RUNTIME_V2.html`，明确区分系统门槛通过与完整战斗预览未完成，链接原九clip播放器、原body+weapon组件预览、现有FSN260985独立音频、索引和报告。音频控件独立播放，不与Golden idle动画伪同步。

Old Original/Remastered/FHA/FUC Gallery数据及Theora机制依靠冻结字节一致性和全部保护路径检验保障；本轮没有重做每个旧媒体的浏览器播放验收，也不声称重做了该覆盖。

## Q. Stability

| 检查 | 最终结果 |
|---|---|
| asset_total /FUC Europe /max ID |268504 /21899 /FSN268504 |
| new logical IDs /missing old IDs /changed old rows |0 /0 /0 |
| 冻结文件非授权变化 |本轮72条=0；继承527条=0 |
| Catalog CSV SHA |{hashes.get('ASSET_CATALOG.csv','see inherited baseline')}，不变 |
| Catalog JSONL SHA |{hashes.get('ASSET_CATALOG.jsonl','see inherited baseline')}，不变 |
| SQLite SHA /integrity |{hashes.get('ASSET_CATALOG.sqlite','see inherited baseline')}，不变 /ok |
| 保护路径引用 /唯一文件路径 |624836 /456988，缺失0、尺寸变化0 |
| static GLB SHA/size/mtime |341个均不变 |
| 独立运行时清理 |CPU/memory breakpoints清空；hooks=0、scratchwrites=0；PID30860已关闭 |

未重新哈希所有Raw大文件：对保护路径验证存在和原尺寸；关键文件与341模型验证完整SHA。ISO未写入；用户其他PPSSPP配置/存档未访问。所有静态xref只扫描ELF SHF_EXECINSTR，已检查本报告16个主要地址属于执行段。无250-watch行为，仅使用精准单地址watchpoint。

## R. Failures / Unknown

保留所有失败原始capture。早期装备dump使用错误8C stride、MOT bank被误视为resourcewrapper和错误count读取，已由C8消费者及FullVerified完整表修正；这些旧诊断文件不进入正式索引。Sound试验1–4的失败来自program字段/编号域误读或有限条件probe未命中，试验5与十项审计闭合；没有证据支持此前“队列复用”猜测。单地址basis写watch还排除了identity方向假设。

未确认：Sir/Rin有效装备、第二角色ownereffect、AMO实际插值、FAN独立时钟、全SEQ材质/可见性/控制、完整clip145原始及混合pose、全音频ID表、game sample-clock/音高重放、完整同步preview、move/对白语义。没有为了覆盖率把unknown升格。

## S. Recommended Next Step

**Animation Reference Index**。最直接缺口是取得clip145隔离原始姿态、实际battle混合/外部姿态和effect消费相位的明确参考，再把同一episode的body、equipment、effect、audio进入严格replay验收。当前不开始下一任务，不开始招式语义命名。
'''
    dest=L/'Reports/FUC_BATTLE_RUNTIME_GENERALIZATION_REPORT.md';dest.write_text(report,encoding='utf-8')
    audio=lookup_audio()
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FUC 战斗运行时 · 第二轮证据</title><style>body{margin:0;background:#101820;color:#e9edf2;font:16px system-ui;line-height:1.7}main{max-width:1060px;margin:auto;padding:36px 24px}h1{font-size:29px;line-height:1.3;margin:12px 0}h2{font-size:21px}a{color:#78d6dc}section{background:#172832;padding:22px 24px;margin:22px 0;border-radius:8px}.status{color:#9fe5c4}.gap{border-left:4px solid #eab971;background:#2b2921}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:9px;border-bottom:1px solid #34505b}small{color:#b9c9d1}audio{width:100%;margin-top:12px}iframe{width:100%;height:600px;border:0;background:#101820}code{font-size:14px}nav{display:flex;gap:20px;flex-wrap:wrap}</style><main><small>FSN MASTER ASSET LIBRARY / FateUnlimitedCodesPortable_Europe</small><h1>战斗运行时：新的数值与因果证据</h1><p class="status">系统 A–E 验收通过 · 268,504 条资产保持不变 · 新 ID 0</p><section class="gap"><h2>完整同步战斗预览尚未通过</h2><p>clip145 的完整姿态参考、特效渲染与跨时钟同步仍需验证。此页呈现独立组件和证据，不自动同步声音、身体与特效。</p></section><nav><a href="./index.html">主素材 Gallery</a><a href="../Reports/FUC_BATTLE_RUNTIME_GENERALIZATION_REPORT.md">本轮详细报告</a><a href="../FateUnlimitedCodesPortable_Europe/Metadata/BattleGeneralization/FUC_BATTLE_GENERALIZATION_SUMMARY.json">验收摘要</a><a href="../FateUnlimitedCodesPortable_Europe/Converted/AnimatedModels/viewer/index.html">九条已验证动画</a></nav><section><h2>已确认的本轮结果</h2><table><tr><th>证据</th><th>结果</th><th>范围</th></tr><tr><td>FAN / BPO 姿态</td><td>22 样本，误差 0</td><td>Shiro / Rin，与原 Lancer remap 规则一致</td></tr><tr><td>出生外部矩阵</td><td>2 个状态，16 元素误差 0</td><td>Lancer 1000.seq / 1002.gmo</td></tr><tr><td>快照保持</td><td>22 次更新，外部矩阵变化 0</td><td>身体骨骼继续变化；特效保留出生快照</td></tr><tr><td>声音因果链</td><td>sound ID 0x232D → FSN260985</td><td>实际队列、bank/program、voice、SAS 调用逐级对应</td></tr><tr><td>Golden 回归</td><td>3 模型 / 9 clips 全部通过</td><td>运行时参考、标准播放器与枪的附着</td></tr></table><p><code>effect_external = body153_world_at_birth × Translation(0, 2.4, 0)</code></p><p><a href="../FateUnlimitedCodesPortable_Europe/Metadata/BattleGeneralization/FUC_EFFECT_MATRIX_PROVENANCE.csv">矩阵来源索引</a> · <a href="../FateUnlimitedCodesPortable_Europe/Metadata/BattleGeneralization/FUC_SOUND_ID_MAP.csv">sound ID 索引</a> · <a href="../FateUnlimitedCodesPortable_Europe/Metadata/BattleGeneralization/FUC_BATTLE_SYSTEM_RULES.csv">规则证据等级</a></p></section><section><h2>声音资产：独立核听</h2><p>FSN260985 · chr_lan00.phd / subsong5。实际 sound ID 0x232D 选择了这份 payload。音频的对白与招式未命名，播放不与下方组件预览同步。</p><audio controls preload="metadata" src="AUDIO_URL"></audio></section><section><h2>保留的身体 + 枪组件预览</h2><p>原有 clip0 /1 /2。有效装备附着误差仍为 0；不是本轮 clip145 完整战斗预览。</p><iframe title="原有 Lancer 身体与枪组件预览" src="../FateUnlimitedCodesPortable_Europe/Converted/BattleScenes/lan_attachment/index.html"></iframe></section><section><h2>仍未证实</h2><p>Shiro/Rin 有效装备挂接、第二角色专属特效归属、AMO 插值、FAN 独立时钟、完整 clip145 与同步特效/声音重放。普通公共特效不会因为与角色同时出现而被标成该角色技能。</p><p><a href="../FateUnlimitedCodesPortable_Europe/Metadata/BattleGeneralization/FUC_BATTLE_PREVIEW_READINESS.json">查看完整预览的数据缺口</a></p></section><small>原 Catalog、Gallery 主页面、静态 GLB、九条 Golden GLB/WebM、旧素材 ID 均未修改。</small></main></html>'''
    (L/'Gallery/FUC_BATTLE_RUNTIME_V2.html').write_text(page.replace('AUDIO_URL',html.escape(audio)),encoding='utf-8')
    print(dest)

def lookup_audio():
    c=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite').replace('\\','/')+'?mode=ro',uri=True);path=c.execute("select converted_path from assets where asset_id='FSN260985'").fetchone()[0];c.close();return '../'+pathlib.Path(path).relative_to(L).as_posix()
if __name__=='__main__':main()
