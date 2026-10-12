# FSN / Rin–Archer Project Memory entry

最新开发候选为 **0.9.4-game-compat.1**：[双游戏版本交接](GAME_VERSION_COMPATIBILITY_20261013.md)，从 **0.9.4-vanilla-compat.1** 继续，支持已验证的 v0.111.0 与 v0.107.1 构建。下一轮使用该交接指向的 `build/source`；不要回退到 0.9.3、Android startup fix.2 或更早快照。下方发布资料与根目录旧源码仍是各自历史状态；验收不覆盖。

## STS2 开发 Skill

所有 STS2 MOD 开发、修复、调试、评审与迁移任务默认调用 `$sts2-modding`（用户级 `C:/Users/Murasame/.codex/skills/sts2-modding/SKILL.md`），按需读取相关参考。任务交付前轻量提炼可复用经验：有新 API/补丁/版本差异/调试方法/实证教训时，去重更新该 Skill references 并记录版本、依据与验证状态；无新增不强制写入。仍按“理解 → 修改 → 必要测试 → 交付”，不新增全量审计、重复测试或复杂门禁；保留以下项目约定与授权边界，不影响无关任务。


最新发布候选：[Public Beta v0.9.3](WORKSHOP_PUBLIC_BETA_093.md)。基于干净安装验证的 v0.9.2，仅内置选人 Remix 与更新发布资料；Gameplay / 美术冻结，Human QA / 上传批准 PENDING，终局连续证据 PARTIAL，未上传 Workshop。历史 [RC01](WORKSHOP_RC_01.md) 及其完整 Run、商店 5＋2 证据保留。


最新体验整合：[Workshop Beta Core UI 01](WORKSHOP_BETA_CORE_UI_01.md)。基于凛二维 Runtime 与 V1.3 QA Fix02；独立本机 Candidate，资源黑框已移除、原生双牌组浏览与四种基础攻防已接入。工程定向验证完成，Human QA / 最终美术仍 PENDING；未上传 Workshop、未进入 E2C。完成后停止等待用户审阅。

Presentation 最新导航：[凛二维甘德 Runtime 01](PRESENTATION_RIN_2D_RUNTIME_01.md)，A 方案已接入独立真实游戏 Candidate。二维 A 主路线获方向认可，最终美术质量仍 PENDING_USER_REVIEW。[凛二维甘德 PoC](PRESENTATION_2D_GANDR_POC.md) 保留为历史离线合成样板；[Art Direction Reboot 01](PRESENTATION_ART_REBOOT_01.md) 的 FUC 技术成果保留。用户已否决 Prototype 01 美术质量，其工程记录保持原样。完成后等待用户与 ChatGPT 审阅，不自动量产、E2C 或 Workshop。

本目录为大型 FSN × Slay the Spire 2 MOD 当前 Rin/Archer vertical slice 工程。
父目录旧 FateStayNight / 士郎–Saber 工程独立。新会话必须先读本文件；不要以 README 的旧 D2
开头或上一轮聊天总结判断当前开发状态。

## 固定读取顺序

1. [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)：长期方向、工程/素材位置、架构边界。
2. [CURRENT_STATE.md](CURRENT_STATE.md)：当前工程、人类 QA、候选/安装、立即下一任务。
3. [DESIGN_BIBLE.md](DESIGN_BIBLE.md)：LOCKED / PROVISIONAL / DEFERRED 合同和实现边界。
4. [DECISIONS.md](DECISIONS.md)：ADR、supersedes、证据和理由。
5. [ACCEPTANCE_INDEX.md](ACCEPTANCE_INDEX.md)：修改相关模块前必须查已验收能力。
6. [KNOWN_DEBTS.md](KNOWN_DEBTS.md)：未实现、未验收与发布门槛。
7. 由 [MILESTONE_INDEX.md](MILESTONE_INDEX.md) 读取当前任务相关原始报告；兼容工作还读
   [COMPATIBILITY_STATE.md](COMPATIBILITY_STATE.md)，内容工作还读 [CONTENT_BASELINE.md](CONTENT_BASELINE.md)。
8. [HANDOFF_LATEST.md](HANDOFF_LATEST.md)：短导航。维护方法见
   [PROJECT_MEMORY_MAINTENANCE.md](PROJECT_MEMORY_MAINTENANCE.md)；机器状态见 [PROJECT_STATE.json](PROJECT_STATE.json)。

## Source of Truth / scope

在同一个 capability、同一版本和相同验收范围内：Accepted human QA / closeout > newer accepted
amendment > newer milestone acceptance > older milestone acceptance > historical / partial report >
chat summary。不同 scope 不互相覆盖：D2 真人 PASS 不能代替 E2A、完整 Run、平衡或物理手柄 QA。
新用户确认可以作为 `USER_CONFIRMED` 输入，但 human retest PASS、engineering PASS、formal
closeout PASS 必须分别记录。旧报告 immutable，禁止把旧 PENDING 原地改成 PASS。

E1 当前使用 E1_MATRIX_AMENDMENT_04；原 E1 → Amendment 01 → Amendment 02 → Amendment 03 → Amendment 04，前四者 SUPERSEDED。E2A 历史 closeout 仍绑定 Amendment 01。修订报告中的当时 E2A PARTIAL、旧
README 的 STOP_BEFORE_E 只描述各自历史窗口；以后续 E2A 验收确定当前工程状态。
关键事实必须有 source / evidence / lastVerified。冲突记录为 MEMORY_SOURCE_CONFLICT，列出双方
证据，禁止静默猜测；HANDOFF 只有导航作用，生成器不能自己批准 milestone。

## CLOSED_RESEARCH_RULE

PASS / RESEARCH_COMPLETE / CLOSED 系统不得重复大规模研究、逆向、替换实现或另起第二套，除非：
当前任务明确要求修改；存在可复现 regression；上游版本/signature 改变；用户明确要求重新设计。
优先读取已有 report / acceptance / source / test / evidence。

FSN 素材库 `FSN_MASTER_ASSET_LIBRARY_COMPLETE_FOR_MOD_DEVELOPMENT` /
`UNIFIED_FSN_SEMANTIC_CATALOG_PASS` CLOSED；FUC `FUC_RESEARCH_PHASE_COMPLETE_FOR_MOD_DEVELOPMENT`
CLOSED。只按具体任务查询 Semantic Catalog 并输出 Selection Manifest；不重新全量下载、解包、
OCR、分镜、Contact Sheet、索引或 FUC runtime/reverse engineering。
A/B/C/D1/D2/E1/E2A 已工程验收能力按原证据复用；E2A formal human closeout 已通过
[MILESTONE_E2A_HUMAN_QA_CLOSEOUT](reports/MILESTONE_E2A_HUMAN_QA_CLOSEOUT.json)。真人范围为四项 UX，
原复测具体时间 UNKNOWN；完整 Run、平衡与物理手柄不由此推断 PASS。
HAND_BANKING_REIMPLEMENTATION = FORBIDDEN_WITHOUT_AUTHORIZED_TRIGGER。

## GLOBAL CONTRACT ENGINE / non-regression

未来 Shirou/Saber 等 Contract 必须复用 GLOBAL CONTRACT ENGINE：Switch、Dual Hand、target
routing、dual deck/reward services、shared energy、member resolver、compatibility registry。
差异用 Contract capability / content configuration / adapters；禁止 clone 第二套架构。
当前这些模块仍在 RinArcherCore 内；概念全局边界不代表已提取为独立通用程序集。

PRODUCTION_CAPABILITY_MUST_NOT_REGRESS：开始读 Acceptance baseline；结束旧 PASS 应仍 PASS。
覆盖自动回归、原生公开 UI、Save/Load、候选行为。旧能力 FAIL 时当前 milestone 不得 PASS，除非
用户明确批准设计迁移并同步 Acceptance Contract。不要削减、skip 或重写旧断言以制造通过。
PRESERVE_VANILLA_EFFECT_BUDGET；PRESERVE_NATIVE_CHARACTER_ACT_POOL_UNLOCK_CONDITIONS；
NO_POOL_EXPANSION_BY_CLASSIFICATION。readiness 不等于原生池资格；新 ID 和版本不符 fail closed。
游戏 version / commit / SHA / MVID 改变触发 VANILLA_COMPATIBILITY_VERSION_MISMATCH，旧 Matrix
必须重新审查，不能仅刷新文档哈希恢复 gate。

## 历史任务停止合同 / 当前 E2B

FSN_PROJECT_MEMORY_V1 及 E2A Human Closeout 仅 docs / state / memory tooling。Gameplay、数值、UI/兼容行为、资格、
正式安装、存档、Matrix、旧报告和现有 candidate payload 写入均禁止。发现真实 regression 只记
KNOWN_DEBTS 与 HANDOFF。E2A Closeout 完成后停止；下一开发任务 E2B_FULL_ACT_ROOM_SPINE 仍
NOT_STARTED，不自动执行 E2B/E2C、Command Spell、Presentation 或 Workshop。后续工作必须来自新的
用户授权，并遵守对应 milestone prerequisite。V1 原始停止范围保留在其 immutable acceptance。

2026-10-09 后续新用户任务已明确授权 E2B_FULL_ACT_ROOM_SPINE 开发、隔离编译与实际 Runtime QA；
其原文见 [E2B task](reports/milestone-e2b/request-source.txt)。当时记录
[E2B](reports/MILESTONE_E2B_FULL_ACT_ROOM_SPINE.json) 为 PARTIAL，不能因组件测试通过而升级完整
工程或真人收口。E2A 历史 Closeout 仍 PASS，不能被 E2B 的 Human PENDING 回退。
E2B 当时三个阻塞：原生事件池无可用 A/B 内容、Boss 原生卡牌奖励预算不足、下一幕 Ancient 仍 C。
不扩池，不放开 C/D/Unknown 内容，不修改 Matrix，不伪造完整 Act。保留 opt-in 开发 Candidate，
正式 v0.5.1 与 E2A UX Candidate 原样。本轮结束停止，不自动进入 E2C 或其他后续阶段。

2026-10-09 新用户 [E2B Blocker Resolution task](reports/milestone-e2b-blocker-resolution-01/request-source.txt) 已授权精确 C Custom、Boss owner adapter、必要 Matrix Amendment 与真实 Full Act。上段 Candidate01 禁止 C/Matrix 的停止范围为历史，不约束本次明确新授权。当时 [E2B 新验收](reports/MILESTONE_E2B_BLOCKER_RESOLUTION_01.json) Engineering PARTIAL，Human/Formal PENDING。只批准精确四项 C，禁止广泛开放、扩池或重写 Global Engine；本次结束停止，无 E2C/安装/发布授权。

2026-10-09 新用户 [Event Exhaustion Final task](reports/milestone-e2b-event-exhaustion-01/request-source.txt) 授权原生耗尽机制修复、最小精确 Event 集合及 Matrix03。当前 [E2B 最终工程验收](reports/MILESTONE_E2B_EVENT_POOL_EXHAUSTION_FINAL_RESOLUTION.json) PASS；Human/Formal PENDING。精确五项 C 保持分类与原生资格，Global Contract Engine 不重写。下一立即任务 E2B_HUMAN_QA，后续开发 E2C_CUSTOM_ADAPTERS 尚 NOT_STARTED；本轮停止，无安装/发布授权。

2026-10-09 用户实际开局仍为铁甲战士，授权修复可复现 regression。当前 E2B 原生入口修复见
[MILESTONE_E2B_CHARACTER_ENTRY_FIX_03](reports/MILESTONE_E2B_CHARACTER_ENTRY_FIX_03.json)：新独立 Candidate
E2B_NATIVE_ENTRY_FIX_CANDIDATE_01，Engineering PASS / Human/Formal PENDING。仅新增空初始遗物预览保护及 E2B 菜单适配；原生选择通过真实点击创建凛 Run。
旧完整 Act 验收/旧 Candidate 保留，新二进制的完整路线与适用回归另行 PASS。正式 v0.5.1 不变；下一立即任务 E2B_HUMAN_QA，E2C NOT_STARTED。

2026-10-09 新用户 E2B Human QA Bugfix & Complete Card Balance Audit 授权四类可复现功能缺陷修复及本机完整卡牌只读提取。当前工程验收见[MILESTONE_E2B_HUMAN_QA_BUGFIX_01](reports/MILESTONE_E2B_HUMAN_QA_BUGFIX_01.json)；工程PASS，Human/Formal PENDING。仅原生首次Run固定Gorget源新增精确C桥接，Matrix04不扩正常池；原03与所有历史验收保留。原用户反馈/时间UNKNOWN/实际64B5 Candidate身份见[反馈输入](project-memory/e2b-human-feedback-01.json)。新Candidate与原存档副本入口见[START_HERE](reports/milestone-e2b-human-qa-bugfix-01/START_HERE.md)，原存档不改写。卡牌经济/目标候选只审计，不重做平衡；既存文本差异OPEN。保持共享3能量、Reserve生命周期、Hand Banking、Switch与Global Contract Engine。下一立即任务E2B_HUMAN_QA；E2C、UBW、Command Spell及后续发布仍未开始。完成后停止，等待用户复测及卡牌重设计讨论。

## 2026-10-10 Gameplay V1.2 authorized scope

新用户明确授权54模型统一实施、12张新奖励牌、独立Candidate及必要原生定向/图形验证。
本授权 supersedes 上轮仅审查/不改玩法的临时任务边界；LOCKED Global Contract Engine、Switch、
Hand Banking、原生预算/Owner/资格及Matrix04继续保留。结果见
[V1.2 实施报告](reports/rin-archer-gameplay-v1.2-20261010-01/IMPLEMENTATION_REPORT.md)、
[工程验收](reports/rin-archer-gameplay-v1.2-20261010-01/ENGINEERING_ACCEPTANCE.json)、
[实施规格](reports/rin-archer-gameplay-v1.2-20261010-01/IMPLEMENTED_MANIFEST.json)。
当前Gameplay/CardPool版本及SHA见 `PROJECT_STATE.gameplay`；根candidate字段仍为E2B历史验收身份。
双击 [V1.2 新Run试玩入口](Launch-V12-Playtest.cmd)，旧Run仍使用匹配旧Candidate，Schema3拒绝旧玩法版本，不自动迁移。
V1.2 ENGINEERING PASS范围仅定向检查和真实图形短流程/Continue，不继承旧DLL完整Act PASS。
E2B及V1.2 Human/Formal均PENDING；E2C NOT_STARTED。完成后停止等待真人试玩，不自动正式安装或发布。

## 2026-10-10 V1.2 Human QA修复授权

本轮仅授权技能结算修复、54模型中文文案、ARC-C14只读审计及玩法方向记录。
[修复报告](reports/rin-archer-v1.2-human-qa-fix-20261010-01/REPORT.md) / [工程证据](reports/rin-archer-v1.2-human-qa-fix-20261010-01/ENGINEERING_ACCEPTANCE.json)；当前SHA见PROJECT_STATE.gameplay。
[新Run](Launch-V12-QA-Fix-Playtest.cmd)及[原V1.2试玩存档副本](Launch-V12-QA-Fix-Continue.cmd)使用不同新Profile，无自动迁移/覆盖原存档。
用户允许小卡组与合理无限流；不增加默认防无限门禁。本轮现有限次保留，下轮建议见报告。
Human/Formal PENDING，E2C NOT_STARTED；完成后停止等待真人复测。

## 2026-10-10 Gameplay V1.3 authorized scope

用户明确授权一次性实施V1.3：90模型、36张新奖励牌、3种起始牌调整及指定5项限次放宽。
输入设计稿中的DRAFT/implementationAuthorized=false为历史，不抵消本轮用户授权。
基于已验收V1.2 QA Fix（986E449D），继续复用Global Contract Engine、Matrix04、Owner、原生预算与资格。
允许单核、小卡组与合法主动无限流；精确支付、真实成功事件去重、原生数值边界保护仍必须保留。
[报告](reports/rin-archer-gameplay-v1.3-20261010-01/REPORT.md) / [工程验收](reports/rin-archer-gameplay-v1.3-20261010-01/ENGINEERING_ACCEPTANCE.json)。
当前身份见PROJECT_STATE.gameplay；双击[新V1.3 Run](Launch-V13-Playtest.cmd)。
V1.2旧Run保留匹配旧Candidate，不迁移、不覆盖。Human/Formal PENDING，E2C NOT_STARTED；完成后停止等待真人试玩。

## 2026-10-10 V1.3真人试玩修复

本轮新授权仅三个真人缺陷、强化投影文案及脆弱审计；结果见 [RIN_ARCHER_GAMEPLAY_V1_3_QA_FIX_CANDIDATE_01](reports/rin-archer-v1.3-human-qa-fix-20261010-01/REPORT.md)。同版原存档以独立副本继续；第三幕精确依赖不扩大随机池。历史候选/Steam/原Profile和验收保留；Human/Formal PENDING，E2C NOT_STARTED，结束等待真人复测。
