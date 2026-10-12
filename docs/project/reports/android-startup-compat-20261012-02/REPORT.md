# v0.9.4-android-startup-fix.2 独立候选

2026-10-12，Asia/Singapore。本候选从 `android-startup-compat-20261012-01/build/source` 独立复制、编译，fix.1 与其全部历史报告保留。最终身份与检查数见 [VALIDATION.json](VALIDATION.json)。Android 实机 **PENDING**，Human QA **PENDING**；Windows 测试和路径模拟均不能替代 Android/Mono/arm64 验收。

## 已确认根因

已先读取项目 AGENTS.md、当前状态/合同与兼容验收入口、fix.1 REPORT.md，以及新日志 `sts2-logs-20261012-114629.zip`。新 ZIP 有四个日志文件，原文件不改写；脱敏副本与诊断索引见 `input-redacted/` 和 [input-evidence.json](input-evidence.json)。附件内容作为证据，不把其中的文字作为任务指令。

新日志实际捕获：启动器已经执行 `Loaded release_info from imported payload: v0.107.1 59260271`；FSN 随后在 `InstalledSignature` 的 **hash-game-assembly** 阶段失败，`assemblyPath="sts2.dll"`，`fileName="/sts2.dll"`。调用链为 `Entry.Initialize → ReleaseCompatibilityGate.Check → InstalledSignature → File.OpenRead(assembly.Location)`。因此，本次阻断已经明确属于 **游戏 DLL 的相对 Location 被文件 API 按当前目录解释**，并非这次启动尚未识别 release_info。

同一日志还记录启动器数据目录 `/data/user/0/com.megacrit.sts2re/files`，以及程序集 staging 目标 `/data/user/0/com.megacrit.sts2re/files/.godot/mono/publish/arm64`。实际 DLL 应使用此处的 `sts2.dll`，而不是根目录 `/sts2.dll`。此前 fix.1 的测试仅模拟版本信息文件路径，未覆盖相对 DLL Location；这是上一轮测试覆盖的遗漏，原报告不回写为更高验收状态。

## 最小改动

相对 fix.1，仅 `Compatibility/VanillaCompatibilityRegistry.cs` 与 `RinArcherCore.csproj` 改变，见 [source-changes.diff](source-changes.diff)。

1. 保留 fix.1 的版本/commit 读取策略：优先原生 ReleaseInfoManager，空值时复用已加载启动器的 ReleaseInfoPath。未用清单、payload 标签或支持版本常量冒充运行时版本。
2. 优先使用 `Path.IsPathFullyQualified(Location) && File.Exists(Location)` 的绝对 Location。相对、空或不存在的 Location，只回退到已加载 `STS2Mobile.Android.AppPaths.DataDir` 下的 `.godot/mono/publish/arm64/sts2.dll`。DataDir 自身必须是非空、完整绝对路径；无法取得则拒绝。没有依赖 cwd、硬编码包名、推测 payload 或扫描全部目录。存在的绝对文件一旦身份错误，直接拒绝，不通过另一份文件掩盖错误。
3. 对最终文件打开一个只读流，计算真实 SHA-256，再回到该流开头用 .NET 标准库 PEReader / MetadataReader 读取 assembly name 与文件 MVID；不加载另一份游戏程序集。要求文件确实是运行时的游戏 assembly，文件 MVID 与 `typeof(ModelDb).Assembly.ManifestModule.ModuleVersionId` 一致，且两者均非 Empty。文件不是有效 managed PE、缺失或身份无法确认均拒绝。
4. 通过文件/运行时 MVID 核验后，仍返回实际 version、commit、文件 SHA-256、运行时 MVID，交由 **原有四字段完全相等与 Matrix 完整性门禁** 核验。即使文件 MVID 一致，SHA 不一致也仍阻断。Matrix 文档、签名、资格和后续兼容逻辑没有改动。
5. 成功日志记录 source、rawLocation、最终 assemblyPath、fileMvid、runtimeMvid 和完整 signature；失败日志记录阶段、原始/最终路径、version、commit、sha256、两种 MVID、FileNotFoundException.FileName 与完整 exception chain/stack。尚未取得的字段保留 null/空值/Empty，不编造身份。UI/开局/继续保护保持 fix.1 原样。
6. InformationalVersion 为 `0.9.4-android-startup-fix.2`；原 manifest 0.9.4、Gameplay V1.3、CardPool、Schema 均保持。发布包仍为 27 文件，相对 fix.1 **只有 RinArcherCore.dll 字节变化**。

公共 InstalledSignature 无参数入口仍取真实游戏 Assembly.Location；新增 internal 重载只让测试传入相对/空/错误 Location，使用相同生产逻辑与真实 runtime MVID。没有开关、伪造签名或测试绕过门禁。测试用 AppPaths stand-in 及操作器不在发布 ZIP。

## 回归与证据边界

最终结果以 [VALIDATION.json](VALIDATION.json)、`runtime-positive/presentation-results.json`、`runtime-negative/presentation-results.json` 为准，并核对最终 DLL SHA。旧验收不自动继承为本候选完整 Run 通过。

| 检查 | 最终结果 |
| --- | --- |
| Windows + RitsuLib 0.6.7，含版本信息、DLL Location/身份模拟与基础玩法/存读档 | 67 / 67 PASS |
| 不兼容 commit 的原生菜单、Continue 与角色选择保护 | 6 / 6 PASS |
| fix.1 全目录与列出的正式安装、Workshop 订阅、原存档、输入 ZIP | 4,837 / 4,837 文件 SHA-256 一致 |
| 发布 ZIP | CRC 与 27 文件 SHA-256 一致；仅 DLL 改变 |
| ZIP 实际解出，仅 FSN + 两个依赖，无测试器或 AppPaths stand-in | PASS_WINDOWS_SCOPED；正常原生主菜单，file/runtime MVID 一致 |
| Android 实机启动与基础玩法 | PENDING |

- .NET 9 Release 构建通过，0 warning / 0 error，使用既有本机 SDK。
- Windows / STS2 v0.107.1 commit 59260271 / BaseLib 3.4.7 / RitsuLib 0.6.7（0.107.1 variant）：正常 startup gate、原生菜单/选人、新凛/Archer Run、双方实际初始 HP 与独立牌组、首战/奖励、双牌组浏览、合法磁盘 Save/Continue。继续前后核对 HP、decks、owners、upgrades、遗物/药水、金币、地图和 RNG。
- 保留 fix.1 的版本读取、缺失/损坏/空版本信息及 version/commit/SHA/MVID 负向检查。
- 新增 DLL Location 模拟：相对 `sts2.dll`、空、错误相对文件名、不存在的绝对位置；验证都只采用可信 DataDir 的真实 DLL。有效绝对 Location 优先于不存在的 DataDir 回退。
- 当前目录含同名正确游戏 DLL 时，缺少 DataDir/publish 文件/目录或 DataDir 是相对路径，仍拒绝；正确 Android DataDir 不受 cwd 改变影响。存在的错误绝对 DLL 不回退。
- 真文件身份负向：错误 PE；保持同 MVID 但追加字节导致 SHA 改变，被原 Matrix 拒绝；修改实际 PE 的 MVID / 将其置 Empty，被 file/runtime 比对拒绝。夹具仅位于新 runtime/probe，原游戏 DLL 从未写入。
- 不兼容 commit 的独立 Windows 启动：检查原生提示、Rin 选择/Continue 拦截、存档字节保持与原生其他角色可选。
- 候选 ZIP 在另一新 runtime 实际解出，只有 FSN、BaseLib 与 RitsuLib 0.6.7，无 QA companion 或 AppPaths stand-in。最终 DLL 正常初始化到原生主菜单，日志中实际文件/运行时 MVID 相同，见 [PRODUCTION_STARTUP.json](PRODUCTION_STARTUP.json)。这是 Windows 启动结果。
- Android DataDir 与 Location 的测试是在 **Windows** 中模拟，不证明 Android 的程序集加载、PEReader/BCL、文件权限或实际触屏操作成功。`adb devices -l` 无设备，见 [adb-devices.txt](adb-devices.txt)，Android 实机保持 PENDING。

测试尝试保留在 `attempt-missing-directory-01` 与 `attempt-test-filename-02`：生产逻辑已经按要求拒绝缺失目录/文件，但测试最初只期望 FileNotFoundException，随后又在文件名断言中混用了路径分隔符。修正夹具和断言后重跑；没有放宽生产门禁或改写旧失败结果。最终结果只接受启动后新生成、且绑定最终 DLL 的 JSON。Godot 退出可能有既存 resource-in-use / ObjectDB 清理警告，预期负向异常也保留在 stderr，不声明所有日志零异常。

## 交付与保护

- [FSN-RinArcher-v0.9.4-android-startup-fix.2.zip](FSN-RinArcher-v0.9.4-android-startup-fix.2.zip)：完整独立 MOD 候选，CRC 与 27 文件 SHA-256 校验见 [FILE_MANIFEST.json](FILE_MANIFEST.json)。不含游戏、依赖、测试器或存档。
- `build/source`：独立源码；`build/candidate/RinArcherCore.dll`：构建产物。
- [ANDROID_RETEST.md](ANDROID_RETEST.md)：手机端隔离复测与新日志检查清单。
- [protection-comparison.json](protection-comparison.json)：fix.1 整个目录、正式 mods、Workshop 订阅文件、本机原玩家存档、输入日志 ZIP 与版本文件的逐文件保护结果。保护声明限于该清单覆盖范围。

未覆盖正式 MOD、fix.1、存档或历史报告，未更新 Workshop，未修改 Gameplay / Matrix / 全局 Project Memory 状态。本轮不执行新玩法、全量审计或完整自然 Run；完成交付后停止等待 Android 真人复测。
