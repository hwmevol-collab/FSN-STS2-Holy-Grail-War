# 独立试玩 / 手动安装

本机推荐双击 **Launch-Test-v111.cmd**。使用已准备好的 v0.111.0 隔离运行目录和新测试 Profile，游戏内选择 Rin / Archer 契约开始新 Run。**Launch-Test-v107.cmd** 使用保留的 v0.107.1 独立副本。启动器先检查游戏 / 变体文件，Loader 再核对运行程序集 MVID；不读取或覆盖正式玩家存档。这里没有自动 QA MOD。

隔离目录引用本机游戏文件；移动报告目录后需按新位置重新准备。正式游戏及 Workshop 没有由本次任务改动。

外部手动安装候选：解压 ZIP，将其中 `mods/RinArcherCore` 文件夹完整放入指定游戏的 `mods` 目录。双版本包的 `lib/0.107.1`、`lib/0.111.0`、`mod-variants.manifest` 与共享资源必须一起保留。仅需当前 Beta 时可以使用 v111 单版 ZIP；两个包择一使用，不能同时放两份 RinArcherCore。

依赖：本轮实际验证 **BaseLib 3.4.7、RitsuLib 0.6.7**；RitsuLib 必须是完整多版本包，包含相应 `compat/0.111.0` 或 `compat/0.107.1` 及 `shared`。候选 ZIP 不捆绑游戏或这些依赖；本机隔离启动目录已配置对应依赖。

仅认已经验证的完整游戏身份：v0.111.0 / commit 41cef1ea，v0.107.1 / commit 59260271；对应 SHA-256 / MVID 见 `VALIDATION.json`。不同 commit / hash / MVID，或其他版本都会拒绝加载，不会向最低版本回退。

不要把 v111 保存覆盖回旧版保存。本轮验证的是每个版本自己的保存 / 继续，**没有验证跨版本导入旧 Run**。Android、联机、物理手柄与完整 Run 尚未验收；以前复杂原版事件 / 遗物的剩余缺口没有在本轮扩大开发。
