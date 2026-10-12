# FSN Project Context

长期事实；最后核对 2026-10-09（Asia/Singapore）。当前状态见 [CURRENT_STATE](CURRENT_STATE.md)。
长期设计输入来自 [本轮用户任务原文](project-memory/request-source.txt)；实现事实由原报告/源码支撑。

## Vision / quality / UI

大型 Fate/stay night × Slay the Spire 2 MOD：Master/Servant playable Contracts、卡牌、遗物、
Event、Enemy、Rival Contract、Boss、Holy Grail War、FSN UI、立绘、战斗动画、VFX、BGM、SE、
Voice、Story/lore。当前 Public Vertical Slice 先完成高质量 Rin / Archer Contract。
公开显示目标 `v0.0.0.0.1 Steam Workshop Public Vertical Slice`；内部继续使用正常 semver。
公开版本尚未发布。

当前 E2B 真人测试启动入口：[Launch-E2B-Playtest.cmd](Launch-E2B-Playtest.cmd)，可双击，使用 Windows
自带 PowerShell 5.1。具体游戏内进入步骤见 [START_HERE](reports/milestone-e2b-human-qa-bugfix-01/START_HERE.md)，
启动兼容修复说明见 [PowerShell 说明](reports/milestone-e2b-launch-fix-01/START_HERE.md)。
继续原进度副本使用[Launch-E2B-Continue.cmd](Launch-E2B-Continue.cmd)。
旧真人 QA 文档的 `pwsh` 命令是原交付记录，由此启动说明取代；其测试清单与历史验收保留。

VERTICAL_COMPLETENESS_OVER_HORIZONTAL_CONTENT_COUNT：一组完整、好玩、稳定的 Rin/Archer Run
优先于半成品角色数量。NATIVE_UI_FIRST_FOR_PUBLIC_PATH：已有成熟 STS2 交互优先 reuse/extend
native UI。debug windows 仅用于开发；基础流程稳定后再生产 FSN Presentation。既有政策：
[PUBLIC_PATH_UI_POLICY](PUBLIC_PATH_UI_POLICY.md)，其中“未进入 E”的文字属于 D2 历史窗口。

## Roots / evidence

内部引用一律以本工程为基准使用相对路径。机器位置集中于
[locations.json](project-memory/locations.json)，不散落复制：开发根 `milestone-a`；主素材库
`E:/FSN_MASTER_ASSET_LIBRARY`；素材工作区 `E:/FSN_MASTER_ASSET_WORK`；原始来源 `../素材`。
机器迁移时更新 locations 并重新验证，不改 stable IDs、原来源或旧报告。

素材库已 CLOSED：270,798 assets；152 entities；448 aliases；1,046,323 relations；1,056,962
evidence。SemanticCatalog/Database/FSN_SEMANTIC.sqlite 为查询入口；原 Closing report、FUC Final
report 由 [MILESTONE_INDEX](MILESTONE_INDEX.md) 索引。统计来源为关闭报告读回，未新跑全库审计。
按任务查询 → 审证据 → Selection Manifest → 经授权才复制 working asset；mentions、candidate、
unknown 不提升为视觉语义事实。FUC 只做 on-demand lookup。

## Architecture boundaries

Global Contract Engine（复用职责）：shared energy、Switch、Dual Hand/CardBanks、target routing、
member resolution、dual permanent decks、Dual Reward、Save/Load、dual deck services、compatibility。
当前模块例：[ContractRuntime](Runtime/ContractRuntime.cs)、[CardBanks](Runtime/CardBanks.cs)、
[Targeting](Runtime/Targeting.cs)、[ContractSave](Runtime/ContractSave.cs)、[DualReward](Runtime/DualReward.cs)、
[VanillaCompatibilityRegistry](Compatibility/VanillaCompatibilityRegistry.cs)。它们当前仍属 RinArcherCore，
尚未独立封装为公共引擎包。

Rin/Archer 内容：Jewel、Rin Mana supply identity、Independent Action、Projection、三件 Arsenal、
Alpha cards；对应 [Content](CONTENT_BASELINE.md)、[AlphaMechanics](Runtime/AlphaMechanics.cs)、
[RewardMechanics](Runtime/RewardMechanics.cs)。未来 Contract 用 capability/configuration/adapters
表达差异，不复制全套架构。父目录旧 FateStayNight / 士郎–Saber MOD 独立，版本和验收不可混用。

## Current roadmap (可由用户修改)

E2A Human Closeout 已 PASS（四项 UX 确认范围）；已授权开发的 E2B 当前 Engineering PASS / Human Formal PENDING，详见
[E2B](reports/MILESTONE_E2B_HUMAN_QA_BUGFIX_01.md)。E2B 工程已完成，真人 QA / Formal Closeout 待确认；之后的 roadmap 为 →
E2C Curated Custom Compatibility → Command Spell →
Presentation Production → Full Human Run → Workshop RC → v0.0.0.0.1。

E2B 目标：Full native Act Map、Unknown MapPoint、Event Room eligibility、Elite、Boss、Treasure
full-map path、Boss reward、Act transition、Full-map Save/Continue。E2C 只做 curated 高价值、常见、
低风险 Custom compatibility；Public Alpha 不要求一次支持所有 C。E2B 之外仍为计划，不是已授权实现。

## 2026-10-10 用户确认的玩法方向

允许小卡组和合理无限流，不再默认以禁止无限循环作为平衡目标。优先创意、爽快、多种强势构筑及Workshop测试版可玩性。合法可重复组合不应仅因无限被判BUG或削弱；重复扣费、错误Owner、无界自动重入及无法继续游戏仍是工程问题。本轮只提出最小限次调整建议，不批量删除限次。证据：[本轮报告](reports/rin-archer-v1.2-human-qa-fix-20261010-01/REPORT.md)。

2026-10-10 后续V1.3新用户授权已实施指定5项限次放宽与36张新奖励牌，目标包含凛/弓兵各自单核、
可选双人协作、后备生命与状态代价及主动无限构筑。90模型独立版本的当前事实见PROJECT_STATE.gameplay与
[V1.3报告](reports/rin-archer-gameplay-v1.3-20261010-01/REPORT.md)。旧V1.2及历史验收保留原身份；
Human/Formal仍PENDING，E2C及发布未获自动推进授权。

## 原版机制资料库（只读参考）

[STS2原版机制图鉴V1](VanillaAtlas/index.html) / [JSON](VanillaAtlas/atlas.json) / [查询指南](VanillaAtlas/GUIDE.md) / [研究状态](project-memory/vanilla-atlas.json)。
原版机制查询优先复用此索引，再沿源码核对条件；不要重复全量反编译或卡牌导出。
绑定v0.107.1 / commit59260271；1,739条索引，22条部分说明，动态UNKNOWN保留。
真实浏览器交互受工具限制尚未验证，数据/源码与检索逻辑检查通过。资料索引不开放C/D，不改变Matrix或Gameplay；Human/Formal PENDING，E2C NOT_STARTED。
