$ErrorActionPreference='Stop'
$cRoot=$PSScriptRoot;$cReport=Join-Path $cRoot 'reports\milestone-c'
$cTests=@(foreach($name in @('core','alpha','highlight','reward')){Get-Content -LiteralPath (Join-Path $cReport "$name-test-results.json") -Raw | ConvertFrom-Json})
if($cTests.Where({$_.status-ne'PASS'}).Count-or($cTests.passed | Measure-Object -Sum).Sum-ne461){throw 'Automated PASS gate failed'}
$cGraph=Get-Content -LiteralPath (Join-Path $cReport 'graphical\results.json') -Raw | ConvertFrom-Json
$cInstall=Get-Content -LiteralPath (Join-Path $cReport 'install-verification.json') -Raw | ConvertFrom-Json
if($cGraph.status-ne'PASS'-or$cGraph.passed-ne20-or$cGraph.battles.Count-ne5-or$cInstall.protectedMismatches.Count-or$cInstall.payloadMismatches.Count){throw 'Graphical/install PASS gate failed'}
$cBoot=Get-Content -LiteralPath (Join-Path $cRoot 'reports\installed-boot.stdout.log') -Raw
if($cBoot-notmatch 'RinArcherCore.Entry'-or$cBoot-notmatch '\[RIN_ARCHER\] GODOT_VERSION=4.5.1'){throw 'Installed native boot unverified'}
Copy-Item -LiteralPath (Join-Path $cRoot 'reports\installed-boot.stdout.log'),(Join-Path $cRoot 'reports\installed-boot.stderr.log') -Destination $cReport -Force
@{status='PASS';executable='ORIGINAL_GAME_EXE';userData='ISOLATED_APPDATA';modDllSha256=$cInstall.installedDllSha256;loaded=$true;deferredBoot=$true;gameplayCoverage='Provided by separate graphical QA, not this boot probe';exitResourceWarnings=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $cReport 'installed-boot-verification.json') -Encoding utf8
$cRegistry=Get-Content -LiteralPath (Join-Path $cReport 'alpha-card-registry.json') -Raw | ConvertFrom-Json
$cChanged=Get-Content -LiteralPath (Join-Path $cReport 'files-changed.txt')
$cEvents=@(Get-Content -LiteralPath (Join-Path $cReport 'native-telemetry.jsonl') | ForEach-Object {$_ | ConvertFrom-Json})
$cPickRows=$cEvents | Where-Object ev -EQ 'REWARD_PICK' | ForEach-Object {'| {0} | {1} | {2} |' -f $_.detail.round,$_.detail.owner,$_.detail.cardId}
$cCardRows=$cRegistry | ForEach-Object {'| {0} | {1} | {2} | {3} | {4}E / {5}M | {6} |' -f $_.Id,$_.Owner,$_.Rarity,$_.Type,$_.Energy,$_.Mana,$_.Upgrade}
$cBattleRows=$cGraph.battles | ForEach-Object {'| {0} | {1} | {2} | {3} |' -f $_.source,$_.result,$_.turns,$_.actions}
$cStamp=[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTimeOffset]::UtcNow,'Singapore Standard Time').ToString('o')
$cAcceptance=@{status='RIN_ARCHER_ALPHA_CARD_POOL_PASS';version='0.3.0';completedAt=$cStamp;milestoneA=@{passed=85;total=85};milestoneB=@{passed=58;total=58};highlight=@{passed=10;total=10};milestoneC=@{passed=308;total=308};total=461;nativeGraphical=@{passed=20;total=20};rewardDefinitions=28;alphaDefinitionSlots=51;BASELINE_A_PASS=$true;BASELINE_B_PASS=$true;ALL_UPGRADES_IMPLEMENTED=$true;OWNER_POOLS_ISOLATED=$true;QA_DRAFT_LAB_PASS=$true;FORCED_ARCHETYPE_PASS=$true;ARM_RESOLVED_PASS=$true;JEWEL_RULES_PASS=$true;PROJECTION_RULES_PASS=$true;BROKEN_PROFILE_PASS=$true;ZERO_MANA_ARCHER_PASS=$true;ALL_AUTOMATED_TESTS_PASS=$true;REAL_GRAPHICAL_QA_PASS=$true;DESIGN_DEVIATIONS=0;DESIGN_CONTRACT_CONFLICT=0;IMPLEMENTATION_BLOCKERS=0;humanMilestoneCPlaytestClaimed=$false;balanceNumbersChanged=$false;installedDllSha256=$cInstall.installedDllSha256;protectedFiles=$cInstall.protectedFiles;protectedMismatches=@();workStoppedAt='Milestone C';scopeExpansion=$false}
$cAcceptance | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $cReport 'acceptance.json') -Encoding utf8
$cText=@'
# Milestone C — Rin / Archer Alpha Reward Pool

最终状态：`RIN_ARCHER_ALPHA_CARD_POOL_PASS`。本地 RinArcherCore v0.3.0 已保护性安装。Alpha Gameplay Validation 完成；停止在 Milestone C。

## A. Precondition

B 正式 Closeout 为 PASS。开工前读回 v0.2.1 安装 DLL 与构建 DLL，均匹配 B 人工 Closeout 的 SHA-256；现场重跑 A 85/85、B 58/58、高光 10/10。`SELF_TARGET_HIGHLIGHT_ROUTING` 已有 22/22 原生图形证据及用户直接复测 PASS，两个人工 pending 为 0。最终仍保留 A/B/UI 全部旧断言，六个旧测试文件逐个 SHA-256 不变。B 的历史报告与人工验收元数据保留原时间窗口。

现场 STS2 v0.107.1、BaseLib 3.4.7、RitsuLib 0.6.6 compat-0.107.1；net9.0。没有安装新的 SDK/库。

## B. Card Registry

实际注册 28 个 Reward ID，两个 owner registry 各 6 Common / 6 Uncommon / 2 Rare；卡模型对应独立 Rin/Archer Pool 标识。通过显式 QA Registry 发放，无 vanilla auto-add；未进入正式 Run Reward。Projected Arms 不进入永久 Deck/Reward。机器注册表：`milestone-c/alpha-card-registry.json`。

| ID | Owner | Rarity | Type | Base Cost | Upgrade |
|---|---|---|---|---|---|
__CARD_ROWS__

契约统计为 Rin Starter 10 + Archer Starter 10 + Rewards 28 + Arms 3 = 51 个 Alpha definition slots。Starter 内既有重复 ID 保持原样；没有声称新增 51 个唯一类。中文名称仍为开发名，内部 ID 保持权威。升级卡描述显示当前升级数值。

## C. New Runtime Mechanics

- `GenerateArm()` 为统一生成入口。Pending、U10 boolean、实例 Mana 折扣、当前回合 Energy/Mana modifier 均在入手前应用；仅入手成功后消费 Pending。U10+Pending 不叠强化，但正常消费 Pending 并保留其 Jewel 实例折扣。U10 在共享玩家回合结束失效。
- `ARM_RESOLVED` 是本场战斗 armId Set；正常成功 play、U02、R03 加入；生成、Bank、Discard、C11、Cancel 不加入。U01 贡献封顶三种；U14 只选择尚未 resolved 的兵装。
- `JEWEL_BOOST` 与 `DIRECT_JEWEL_CONSUME` 独立。R04 仍要求 Jewel>=1，首次 Boost 免费，之后正常扣；C13/U10/U14 不享受免费 Boost。Rin U12 在 normal Supply 之后；Rin R05 在原生 Player End、Enemy Turn 之前。
- U12 Archer 通过真实 Projected Arm Exhaust 事件触发，四种来源共用每共享回合一次 flag；抽 Archer 牌、给 Archer Block。U13 只随实际 IA 1→0 触发。R05 付款前记录 Mana=0 资格；+8 分配到原 per-hit profile；self Block +6 独立机会，Cover 不消耗它。
- C04/U04 用统一意图/目标 resolver，包含 FRONT/MASTER/BOTH/LOCKED；Guard 预览目标不消费 Guard。所有伤害仍经原生 Block/HP/Power/lethal pipeline，U04 三 Hit、R03 K&B 四 Hit。R03 只按显式 armId profile，忽略强化加成。
- 可取消选择复用 B 的 native PlayCardAction 付款前入口。图形 QA 发现并修复了连续选择回调被旧窗口清除的问题；清理状态先于完成任务，延迟销毁只清理自己的 handler。失败尝试保留于 `milestone-c/graphical-attempt-*`。

## D. Automated Tests

```text
A regression: 85/85 PASS
B regression: 58/58 PASS
Highlight regression: 10/10 PASS
C new: 308/308 PASS
Total: 461/461 PASS
Build: 0 warnings / 0 errors
```

全部执行于真实 STS2 隔离进程和原生 API。覆盖全部 Reward 及 Upgrade、付款前 Cancel、FIELD/fallback、Pending 共存、折扣期限/零下限、所有 Exhaust 来源、distinct cap3、精准合法目标、R03 两种 profile、R05 付款前判定/分配/独立 flag、Owner/vanilla 隔离与 seeded Draft。原有测试未删除、跳过或放宽。结果及完整 check IDs：`milestone-c/*-test-results.json`；旧文件保护：`old-tests-preservation.json`。

## E. Real Game QA

最终 DLL 在隔离图形进程中通过 20/20 原生断言，包含契约指定的九组 Scenario。使用原生 GameAction 队列，选择窗口先真实渲染再由测试驱动响应。专用机制场景明确使用 QA fixture；四组 Forced Build 与自由 Draft 战斗使用真实抽牌、正常费用与原生回合，没有战斗中补资源。截图已查看。

| Scenario | 结果与证据 |
|---|---|
| 1 Jewel | R04 first Boost Jewel 1→1；C13 直接 1→0。`S1-*.png/json` |
| 2 U10 | Rin U10→Switch→两次 Trace，两件强化，生成 metadata reinforcedByAllProjection=true。`S2-*.png/json` |
| 3 Supply | Rin End +1，下一 Start normal +1 后 U12 +1，事件顺序原生验证。`S3-end-start-mana.*` |
| 4 Broken | Hrunting 普通 Reserve Master 9；U02 FRONT 18；R03 Master 20+Vulnerable2。`S4-*.png/json` |
| 5 Exhaust | C11+U12：合计两次抽牌、8 Block、不记录 resolved。`S5-*.png/json` |
| 6 Precision | clean Reserve 非法；ARC_PRECISION 的 QA helper 施加 Debuff 后可选并命中 Reserve。`S6-*.png/json` |
| 7 Zero Mana | Close Combat 原两 Hit，总计14=6+8，非每 Hit+8。`S7-zero-mana-result.*` |
| 8 Draft | 12 次真实 offer、10 次 pick、2 次 skip，双 Deck 各15，无 Owner 混入。`S8-*.png/json` 与 reward telemetry |
| 9 Forced/Free Battle | 四组 Forced 与一场自由 Draft 均完成原生胜利，见下表。`battle-*.png/json` |

| Build | Result | Shared Turns | Native Card Plays |
|---|---|---|---|
__BATTLE_ROWS__

以上为自动原生图形 QA，不冒充用户人工试玩。真实安装后另外从原 `SlayTheSpire2.exe`、隔离 APPDATA 启动，确认已安装 v0.3.0 assembly、initializer 与 Godot deferred boot。该安装探针仅证明加载；玩法证据来自图形 QA。

## F. Draft Lab

`QA_ALPHA_DRAFT_LAB` 可在主菜单选择 seed 310/311/312，六轮每人每轮三牌，Pick 0–1 或 Skip，之后选择 `QA_PAIR_BASIC` 或 `QA_FIELD_PRESSURE`。本次自由 Draft 为 Seed 311。每 offer 内无重复 ID；已选 ID 本 session 不重复发放，没选的牌可再次 offer。候选采样仅用于 QA，不定义最终掉率、最终重复牌规则或 Power 叠加。

```text
NOT_FINAL_REWARD_SYSTEM
DUPLICATE_REWARD_POLICY_DEFERRED
POWER_DUPLICATE_STACK_POLICY_DEFERRED
```

| Round | Owner | Pick |
|---|---|---|
__PICK_ROWS__

第3轮双方各 Skip 一次。固定偏好仅在实际 seeded offer 内选择，没有强制生成偏好牌。Forced 七预设均可进入，核心 ID 按契约注入 QA Deck；10+10 Starter definitions 不改。ARC_PRECISION 的 Reserve Weak 按钮仅在该 QA 预设有 capability 时出现。

## G. Telemetry

最终图形运行收集 1064 个事件、85 次 CARD_PLAYED 与85次 ALPHA_CARD_RESOLVED；12 offer /10 pick /2 skip；16 Arm Generated、7 Arm Resolved Added、3 Consumed as Broken、1 Free Jewel Boost、1 U10、1 Projected Exhaust Engine、1 IA Engine Block、1 Zero-Mana Attack Bonus。五场完整战斗各有 COMBAT_SUMMARY，包含契约指定的15项 metric（未触发项目为0）。细节含 owner/rarity/upgrade、Energy/Mana/Jewel、Boost free、target，以及 generation/resolve source。

`native-telemetry.jsonl` 来自最终图形 stdout，排除旧失败尝试。原始完整上下文在该文件；`graphical/telemetry-*.jsonl` 分别保留 Forced/Free Battle 的运行时事件。`telemetry-summary.json`、`telemetry-samples.json` 可读回 free Boost Jewel 1→1、resolved distinct、供魔时序与 +8 分配。[4,4] 实际两 Hit；三/四 Hit 分配也由自动测试验证。

## H. Balance Observations

`BALANCE_OBSERVATION`：五场自动策略战斗均为4–5个共享回合；每场仅自然打出1–3张 Reward，不能据此评价 Rare 强度或整个池的平衡。自由 Draft 实际形成凛的战斗/宝石/支援混合，以及弓兵的 Broken/Exhaust/0-Mana 混合；是否让玩家自然想选不同东西，仍需用户人工 Draft 反馈。

没有自行调整任何指定数值。自动策略、指定 seed、基础 QA 敌人及短战斗限制已明确；未将该结果当作完整 Run 平衡结论。

## I. Design Compliance

```text
DESIGN_DEVIATIONS = 0
DESIGN_CONTRACT_CONFLICT = 0
```

RIN-U10 使用最新全回合版本；未实现旧 provisional 的下一件/折扣版本。未扩 Full Pool、UBW、Caladbolg II、第四 Arsenal、正式卡图/素材/语音/BGM/VFX、Relic/Event/Shop/Campfire、令咒玩法、Rival roster、正式双 Reward Run 或 Workshop 发布。没有进入 FSN_MASTER_ASSET_LIBRARY 做 Selection Manifest。

## J. Blockers / Known Issues

```text
IMPLEMENTATION_BLOCKERS = 0
```

- 用户的 Milestone C 人工 Draft/Playtest、长期构筑偏好与平衡反馈尚未发生；本次 PASS 是实现与自动/原生图形 gate。
- Power duplicate stacking 和最终 duplicate reward policy 均暂缓；QA session 不发重复 ID，未永久把 Power 定义为 Unique。
- headless 退出保留既有 Godot RID/ObjectDB/resource 警告；RitsuLib 仍报告 Steamworks.NET 部分类型枚举警告。图形最终运行无 gameplay exception。部分截图含 RitsuLib telemetry permission 提示，未替用户选择权限。
- 任意动作中途战斗快照、网络多人、正式整局 reward progression 和真人全流程通关未验证，也不属于本轮范围。

## K. Files Changed

精确源码/脚本/文档列表同时保存于 `milestone-c/files-changed.txt`。

__FILES__

真实安装仅更新 `mods/RinArcherCore/RinArcherCore.dll` 与 `RinArcherCore.json`。DLL SHA-256：`__DLL_HASH__`。1493 个其它 MOD/真实用户目录保护文件哈希全部未变，payload mismatch=0。原游戏加载检查继续使用隔离 APPDATA。未向真实 mods 安装测试 DLL；源码、B 载荷备份保留。

## L. Evidence / Package / Playtest

- 本报告：`reports/MILESTONE_C_REPORT.md`；机器 gate：`reports/milestone-c/acceptance.json`。
- 测试、注册表、graphical原生结果、22张截图、telemetry、构建、旧测试保护、空白检查、安装与启动读回：`reports/milestone-c/`。
- 备份：`__BACKUP__`；恢复已验收 B：`RestoreMilestoneB.ps1`，只恢复 DLL/JSON。
- 交付包：`dist/RinArcherCore-0.3.0-local.zip`、`-source.zip`、`-evidence.zip`；完整读取及解压/哈希验证收据：`reports/milestone-c/package-verification.json`。
- 人工试玩：运行 `LaunchMilestoneCPlaytest.ps1`，在独立 `RinArcherCore-MilestoneC-Manual` 用户目录打开主菜单 Draft/Archetype。人用 runtime 已准备、载荷哈希与真实安装一致、不含测试 DLL；该新入口的用户点击流程留待用户人工复测。

Milestone C 已停止。下一步由用户真实 Draft / Playtest 后决定。
'@
$cFileBlock="``````text`n"+($cChanged-join"`n")+"`n``````"
$cText=$cText.Replace('__CARD_ROWS__',($cCardRows-join"`n")).Replace('__BATTLE_ROWS__',($cBattleRows-join"`n")).Replace('__PICK_ROWS__',($cPickRows-join"`n")).Replace('__FILES__',$cFileBlock).Replace('__DLL_HASH__',$cInstall.installedDllSha256).Replace('__BACKUP__',$cInstall.backup)
[IO.File]::WriteAllText((Join-Path $cRoot 'reports\MILESTONE_C_REPORT.md'),$cText,[Text.UTF8Encoding]::new($false))
Write-Output 'Milestone C implementation/runtime gates PASS; report generated'
