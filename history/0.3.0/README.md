# Rin / Archer — Milestone C Alpha Card Pool

当前版本为 RinArcherCore 0.3.0。28 张 Reward 与全部升级、两个 Owner Registry、ARM_RESOLVED、U10 全回合强化、Jewel Boost Rare、Exhaust / IA / Zero-Mana engines、seeded Draft Lab 和七个 Forced Archetype 已完成。最终报告见 `reports/MILESTONE_C_REPORT.md`；A 85/85、B 58/58、高光 10/10、C 308/308，共 461/461 PASS，C 原生图形 20/20 PASS。

运行 `LaunchMilestoneCPlaytest.ps1` 打开独立存档目录的人工试玩。该入口只带 BaseLib、RitsuLib 与实际安装的 RinArcherCore，不带测试 DLL。主菜单选「QA_ALPHA_DRAFT_LAB」，选择 Seed 310 / 311 / 312、做六轮每人三牌的 Pick / Skip，再选基础或 FIELD QA；或选「QA_ALPHA_ARCHETYPE」进入七组指定构筑。ARC_PRECISION 提供专用 Reserve Weak helper。每轮、牌与升级都保留内部 ID 和 Owner。

QA Draft 按 cardId 不重复加入 Deck；没选的牌可在以后 offer 再出现。每个 offer 内无重复。`NOT_FINAL_REWARD_SYSTEM`、`DUPLICATE_REWARD_POLICY_DEFERRED`、`POWER_DUPLICATE_STACK_POLICY_DEFERRED` 均保留。这是 Alpha Gameplay Validation；正式双奖励 Run、最终掉率、Full Pool、UBW、第四件 Arsenal、正式素材仍暂缓。

自动原生 QA 完成四组 Forced Build 和一场自由 Draft 战斗；没有冒充人工试玩或据此调整数值。v0.2.1 安装备份及 C 源码基线见 `reports/milestone-c/backup-path.txt`；`RestoreMilestoneB.ps1` 只恢复该备份的 DLL/JSON。

以下保留 Milestone B 的机制与历史验收说明；当前版本、C 入口、安装与验收以本段和 C 报告为准。

## Milestone B 历史机制说明

`NOT_SHIPPING_CONTENT` 本地 Vertical Slice，版本 0.2.1。基于已验收的 Milestone A，保留 Dual Contract Core 与 10+10 Starter；新增三件投影武器、Trace、强化投影、ANY targeting、Guard Master、FIELD/Suppression 及中文 QA UI。未进入 Milestone C，未加入 Reward Card、正式素材、UBW 或 Broken Phantasm。

`SELF_TARGET_HIGHLIGHT_ROUTING` 已修复，Self 高光跟随牌的真正角色 Owner，Cover 指向 Rin，FRONT 指向敌方 Active，Hrunting 明确选择前没有固定预选。A 85/85、B 58/58、UI 10/10、原生图形 22/22 PASS；用户已确认 Multi-Hit 和高光复测。`MILESTONE_B_HUMAN_QA_CLOSEOUT` 已完成，最终状态 `RIN_ARCHER_ALPHA_MECHANICS_PASS`。

## 试玩

正常启动当前 STS2 v0.107.1，启用已安装的 BaseLib 3.4.7、RitsuLib 0.6.6 兼容包与 RinArcherCore。在主菜单选择「Milestone B 基础契约 QA」或「QA_FIELD_PRESSURE」。选择凛或弓兵开场；双方仍各自有 5 张 Opening Hand。

投影：从干将·莫邪、Rho Aias（开发名）、Hrunting（开发名）中明确选择一件。取消保留原牌与资源。武器进入弓兵当前手牌或后备 Bank，使用后消耗；未使用的 Active 武器结束回合进入弃牌堆。切出后保留原实例，切回不重新生成。

强化投影：下一次成功生成的武器获得强化，可明确选择消费 1 Jewel，使武器本场战斗魔力消耗 -1。Pending 跨回合与切换保留，禁止重复施加。升级只降低本牌能量 1→0。Trace+ 的 -1 魔力只持续当前共享玩家回合，Bank 不能延长它。

强化武器标题显示「强化」：干将·莫邪 6×2 真实 Hit；Rho Aias 给弓兵与凛各 8 Block；Hrunting 为 14 Damage。普通数值分别为 6、弓兵 8 Block、9 Damage。Hrunting 出牌前出现中文 Master/Servant 目标框，可选后备敌方成员，取消不扣资源。

QA 目标标签位于敌方 Intent 附近。上方显示 Pending、Guard 与 FIELD。Guard 和 Suppress 按钮是 QA-only helper，只在明确的 QA 契约中启用，不进入 Deck 或 Reward Pool。

FIELD QA：敌方御主 42 HP、从者 56 HP；循环 12 FRONT → 8 BOTH → 14 MASTER → 御主 +10 Block / 切从者。压制期间 FIELD 仍显示，攻击回到基础 9/5/11，到下一玩家回合恢复。QA FIELD 本场战斗持续；底层也支持有限 duration 在压制中正常推进。

## 构建与检查

工程仍在 `E:\BaiduNetdiskDownload\FSN\milestone-a`。现有 SDK 为 `E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe`，没有安装新依赖。

`RunTests.ps1` 构建并异步运行原生测试：`native-runtime/core-test-results.json` 是 A 的 85 项；`alpha-test-results.json` 是 B 的 58 项；`highlight-test-results.json` 是新增 UI 的 10 项。旧 A / B 测试均保留。测试 DLL 只位于隔离 runtime，真实安装不包含测试驱动。`RunHighlightQa.ps1` 运行鼠标 / 手柄的 22 项原生高光图形 QA。

`RunTests.ps1 -NativeQa` 打开隔离图形 QA，随后 `RunMilestoneBQa.ps1 -Phase Arsenal`。强化场景使用 `-Phase Reinforcement`。FIELD 可用 `RunTests.ps1 -NativeQa -Field` 和 `RunMilestoneBQa.ps1 -Phase Field`。同时只运行一个隔离进程。脚本使用正常 GameAction 队列及 QA-only starter fixture；不改真实 Deck、存档或数值。

## 安装与恢复

真实安装目录：`E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore`。B 仅更新此目录的 DLL/JSON；BaseLib、RitsuLib、其它 MOD 与真实存档保留。v0.2.1 更新前的 v0.2.0 安装备份见 `reports/self-target-highlight/backup-path.txt`。`UpdateHighlightFix.ps1 -VerifyOnly` 检查安装载荷与安装前保护快照；人工试玩会更新用户日志 / 存档，因此这些差异需结合 `reports/milestone-b-closeout/` 的当前读回记录判断，不能覆盖试玩数据。旧 A / B 安装恢复脚本保留为历史工具。

最终验收、原生 A–K 场景、telemetry 与限制见 `reports/MILESTONE_B_REPORT.md`。原 A 报告与人工验收记录保留。B 不代表平衡结论、真人全流程试玩、多人网络或最终 Rival UI 验收；本轮停止在 Milestone B。
