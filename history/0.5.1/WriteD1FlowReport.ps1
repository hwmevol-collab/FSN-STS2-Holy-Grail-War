$ErrorActionPreference='Stop'
$flowReport=Join-Path $PSScriptRoot 'reports\d1-native-container-flow'
$a=Get-Content (Join-Path $flowReport 'acceptance.json') -Raw|ConvertFrom-Json
$i=Get-Content (Join-Path $flowReport 'install-verification.json') -Raw|ConvertFrom-Json
$b=Get-Content (Join-Path $flowReport 'installed-boot-verification.json') -Raw|ConvertFrom-Json
if($a.status-ne'D1_NATIVE_CONTAINER_FLOW_PASS'-or$b.status-ne'PASS'-or$a.testedDllSha256-ne$i.installedDllSha256-or$i.installedDllSha256-ne$b.installedDllSha256){throw 'Acceptance/install/boot do not match'}
$text=@'
# D1 Native Combat Reward Container Flow — v0.4.2

本地修复已实现、重新验证并安装。`D1_NATIVE_CONTAINER_FLOW_PASS`。用户已确认 v0.4.1 地图可点击、跨战斗基本流程通过；v0.4.2 人工复测仍为 **PENDING**。本轮停止在 D1，没有进入 D2。

## 正常 Run 流程

`Combat Victory → Native Loot / 搜刮 → 一个 Card Reward Item → 用户点击 → 1 / 2 MASTER → 2 / 2 SERVANT → 原 Native Loot → 该 Card Reward Item resolved → 其他奖励 / native Proceed`

新胜利不再自动开选牌。Gold 与原生其他项继续由原生 `RewardsSet`、`NRewardsScreen`、`NRewardButton` 与原生奖励同步器管理。原生 Card Selection 的卡牌节点、hover、input、查看、按钮、controller/navigation、布局和缩放保留。双阶段语义与双方 HP 提示保留。

根因是 v0.4.1 的 `ResumeDualRewardHook` 在每次 `RewardsSet.Offer` 后调用了 Card Reward 按钮，混淆了新胜利与载入 pending selection。现在只有 native saved-run initialization 发出的恢复请求才能自动恢复 Servant；未打开的公共 Master reward 保持在搜刮容器。具体调用链见 [architecture investigation](d1-native-container-flow/ARCHITECTURE_INVESTIGATION.md)。

## Save / Continue 与 Public UI

已实际通过原生暂停菜单 Save and Quit、退出进程、原生 Continue 验证：容器生成后未点击的 Master offer / rarity state / native item identity 不重掷；Master 获得后退出，Continue 恢复同一 Servant offer；双方各获得一次永久实例；完成后回同一容器并 resolved 卡牌项；已领取 Gold / 测试用 native Potion 不能重复领取；完整容器再次载入没有卡牌、Gold 或 Potion 再领入口。native Proceed 可返回既有 D1 图。

原生退出时先通过原生 overlay teardown 取消未提交选牌，等待原生奖励按钮的回调完成，再调用原生主菜单返回，避免容器先销毁而异步按钮仍访问它。取消不等于 Skip，不添加卡牌，不改变 pending offer。

`PUBLIC_UI_MODE`：正常 **Rin / Archer · D1 Run Integration** 默认精简 HUD，显示 active owner、双方 HP/Block、Mana/Jewel、IA、投影强化与切换操作。大型 Debug HUD、QA-only Guard / Suppress / fixture controls 和奖励内「保存并返回主菜单」按钮默认隐藏。F8 可切换开发信息，Public 模式仍不显示 QA controls。正常退出使用原生暂停 / Save and Quit / Continue。明确的 **Rin / Archer · D1 QA / Debug** 与原 A/B/C QA 入口保留完整调试能力、telemetry 和 QA 保存辅助按钮。

## 范围保持

`D1_QA_MAP_SPARSITY = EXPECTED_NON_BLOCKING` 已登记。三节点 QA topology、原生地图行数 envelope、placement、scroll/clamp 和 spacing 与 v0.4.1 完全相同。没有视觉填图。完整 native Act map 等后续对应房间支持并得到授权后再做。

`Content/` 与 `Runtime/` 全部源码逐文件 SHA-256 与本轮 v0.4.1 备份一致，包含 Dual Reward 规则、HP/Deck persistence、encounter reset。3-card offer、owner isolation、独立 rarity/RNG、duplicate policy、Master→Servant、卡牌数值均保持。没有新增正式 Potion/Relic 掉落、Campfire、Merchant、Event、Command Spell 或素材。

**测试边界**：新容器 QA 的 Fire Potion 是测试 DLL 里添加的单个现有原生 fixture，用来验证 native item identity / acquisition / save persistence。它不在安装的 DLL 内，正式 D1 继续抑制 Potion/Relic drops。没有增加 Potion/Relic gameplay。原生 Relic 恢复路径由架构代码检查覆盖，本轮没有新增 Relic 图形领取场景。

## 重新验证

| 回归 / 图形检查 | 本轮结果 |
|---|---:|
| A 85 + B 58 + 高光 10 + C 308 + D1 63 不变量 | 524 / 524 PASS |
| 既有 D1 五阶段，跨进程 / 跨战斗 / Act transition / defeat | 97 / 97 PASS |
| 既有 QA Save/Exit 与 legacy map | 17 / 17 PASS |
| 既有 2560×1440 地图 / 原生奖励 | 42 / 42 PASS |
| C 原生 5 场战斗 | 20 / 20 PASS |
| A 原生完整战斗 | PASS |
| B Arsenal / Reinforcement / Field 原生场景 | {{B_CHECKS}} PASS |
| 鼠标 / controller 高光原生场景 | 22 / 22 PASS |
| 新 Public reward-container，1920×1080 三阶段 | {{CONTAINER_1080}} / {{CONTAINER_1080}} PASS |
| 新 Public reward-container，2560×1440 三阶段 | {{CONTAINER_1440}} / {{CONTAINER_1440}} PASS |

全部旧不变量与 v0.4.1 D1 图形检查 ID 均保留；新容器两种分辨率的 {{IMAGE_COUNT}} 张 PNG 已逐张读回实际尺寸并记录 hash。人工查看了精简 HUD、原生 Loot、Master / Servant 原生卡牌、返回原容器与 completed reload。构建 0 warnings / 0 errors。测试通过的核心 SHA-256：`{{CORE_HASH}}`。

原生鼠标输入经过 viewport hit testing；手柄输入是原生 controller action 的软件模拟，**实体手柄仍待人工验收**。隔离测试的 Ritsu telemetry notification 挡住 gear 下半部时，driver 只改实际点击点；controller→mouse 使用移出 / 移回动作；Continue 等待原生 transition 完成。没有修改通知权限、生产 UI geometry 或绕过 card selection 回调。

保留原有进程退出时 RID / shader / resource cleanup diagnostics 和 headless dummy-texture diagnostics，本轮未解决这些既有诊断；通过的是功能断言与无相关 managed exception，不声称所有日志无 ERROR。保留的失败测试输入 / tutorial 尝试与最终证据分开。driver 另修复主菜单重开导致重复启动、transition 中提前点击及 bridge JSON 写入期间读取的问题。高光 driver 改为移动实际 viewport 鼠标后送入原生输入事件，避免旧事件仅携带坐标而实际鼠标仍在手牌区；22 个既有断言、指纹与原生出牌路径保持。验收只使用同一核心 DLL 的最终 PASS 证据。

## 安装与人工复测

真实安装：`E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore`；独立人工目录：`E:\BaiduNetdiskDownload\FSN\milestone-a\d1-human-runtime\mods\RinArcherCore`。二者仅更新 RinArcherCore DLL / JSON，版本 0.4.2，hash 与通过测试的 DLL 一致。{{PROTECTED_FILES}} 个保护文件均保持原 hash，包括其他 MOD、真实 STS2 存档和既有人工 profile。测试驱动未安装。

实际安装的原始游戏 exe 已在独立 APPDATA headless 启动，核心 mod 初始化、主菜单与进程退出读回 PASS。图形功能验证在隔离 runtime 内完成；没有运行或改写用户真实存档。源码、v0.4.1 安转载荷、人工 profile 与旧证据备份位于 `d1-native-container-flow/backup-path.txt` 指向的目录。

继续使用 `PlayMilestoneD1.cmd` / `LaunchMilestoneD1Playtest.ps1`，选正常 **D1 Run Integration**；正常奖励页无 QA 保存按钮，通过原生暂停菜单退出。重点人工确认胜利先搜刮、点击卡牌项才开 Master、Servant 后返回搜刮、原生保存恢复与简化 HUD。F8 是开发信息开关，明确的 QA / Debug 入口保留原调试控制。

没有要求或安装 Godot Editor。当前 STS2 runtime + .NET 9 + BaseLib + RitsuLib + C# 足以完成。近期目标仍为 `v0.0.0.0.1 Steam Workshop Public Vertical Slice`，本地 v0.4.2 是测试版本，尚未发布 Workshop。现在停止，等待人工复测。
'@
$text=$text.Replace('{{B_CHECKS}}',[string]$a.bNative).Replace('{{CONTAINER_1080}}',[string]$a.container1080).Replace('{{CONTAINER_1440}}',[string]$a.container1440).Replace('{{IMAGE_COUNT}}',[string]$a.containerImages).Replace('{{CORE_HASH}}',$a.testedDllSha256).Replace('{{PROTECTED_FILES}}',[string]$i.protectedFiles)
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'reports\D1_NATIVE_CONTAINER_FLOW_REPORT.md'),$text,[Text.UTF8Encoding]::new($false))
Write-Output 'D1 v0.4.2 report written from acceptance, install and boot evidence'
