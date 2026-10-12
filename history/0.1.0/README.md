# Rin / Archer — Milestone A

这是 `NOT_SHIPPING_CONTENT` 的本地 Vertical Slice，版本 0.1.0。只包含 Contract Core、指定的 10+10 Starter，以及 `QA_PAIR_BASIC`。Trace / Reinforce Projection 明确显示 `[MILESTONE B EFFECT PLACEHOLDER]`。本轮未实现 Arsenal、Projected Arms、UBW、Command Spell gameplay、正式 Rival 或正式 FSN 资产。

## 运行

已安装到 `E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods` 的 `BaseLib`、`STS2-RitsuLib`、`RinArcherCore` 三个目录。依赖固定为游戏 v0.107.1 / BaseLib 3.4.7 / RitsuLib 0.6.6 的 0.107.1 兼容包。

正常启动游戏，按原版 MOD 加载流程启用 MOD。在主菜单点击 **Rin / Archer · Milestone A QA**。双方各自生成 5 张 Opening Hand 后，选择 Start as Rin 或 Start as Archer；Rin 在 Turn 1 获得 +1 Mana，Archer 不获得。主手牌可出牌，上方 Reserve Hand 只读。左侧显示 Switch、两组 HP/Block/牌堆与共享资源。

QA 敌方四步循环为 FRONT 10 → 切 Master、+2 Mana、FRONT 6 → 切 Servant、MASTER 12 → BOTH 7。击败敌方任一成员即结束契约。QA 无奖励，不是正式剧情战斗。

## 构建与验证

使用现有 SDK：`E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe`。项目是现有 FSN 工程中的独立组件，没有复用旧 Shirou/Saber 的玩法语义。

运行 `RunTests.ps1` 可构建并在隔离的真实游戏进程中运行 85 项原生 API 测试。脚本异步启动；检查 `native-runtime\core-test-results.json` 的 PASS 与 passed/total。测试失败会留下错误文件和失败结果，不会把部分通过写成全部通过。

运行 `RunTests.ps1 -NativeQa` 打开隔离的图形 QA。`QaCommand.ps1 -Operation start -Owner CHAR_ARCHER` 明确选择 Archer 后，`RunBattleQa.ps1` 用原版 GameAction 队列完成固定战斗并保存截图。这是原生自动驱动，不等同于人工鼠标验收。测试 DLL 仅在隔离 runtime 中使用，未安装到真实游戏 mods。

隔离游戏使用 `RinArcherCoreQA-20261007` 用户目录并关闭 Steam 接入；真实安装启动探针另外隔离 APPDATA。真实存档未被 QA 改写。

## 架构与保存边界

Active 使用 vanilla Hand；Reserve 使用 Ritsu extra-hand / extra-pile，关闭手动出牌和 vanilla end-turn 行为。切换移动同一 CardModel 引用与五个 combat pile 的归属视图，不 draw/discard/refresh，不改变永久牌组和资源。视图重挂只重建 Godot 卡牌节点。

Archer 是持续存在的独立友方 Creature，未设置 PetOwner，HP、Block、Power 均独立。Reserve 的原生 Poison 与 Weak 时钟持续推进。Jewel 属于 Rin 的 CharacterResources；Energy 和 Mana 属于契约。Archer 永久 Deck 通过 Ritsu RunPersistent 保存，独立 HP 通过 RunSavedData 保存。原版存档以房间边界为准；没有实现任意动作中途的战斗快照或跨设备/多人回滚验收。

## 安装与恢复

备份路径记录在 `reports\install-backup-path.txt`。`InstallLocal.ps1 -VerifyOnly` 重验原游戏文件、Workshop 库、旧 FSN 源码、真实存档和安装载荷。`RestoreLocal.ps1` 仅在安装载荷仍匹配时，把三个新 MOD 目录移回备份；遇到额外文件或修改会停止。它不会覆盖真实存档。

完整 A–J 验收结论见 `reports\MILESTONE_A_REPORT.md`，精确文件清单见 `reports\files-changed.txt`。本轮停在 Milestone A。
