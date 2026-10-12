# 独立候选试玩

版本沿用 **0.9.4-game-compat.1**，候选修订为 **visual-loader-fix-01**。这是同一版本线的新二进制；以本目录 SOURCE_BINDING.json 的 SHA 区分。

本机双击 `Launch-Test-v111.cmd` 或 `Launch-Test-v107.cmd`：使用本报告新建的对应游戏副本和独立空白 Profile，不带 QA 伴随 MOD。只开始新测试 Run；本轮未复制正式存档。游戏/依赖文件由上轮保留副本复用，移动目录后需重新准备。

ZIP 只含 MOD 与安装说明，不含游戏、BaseLib、RitsuLib。外部测试请先准备独立游戏副本及独立 Profile，再把 ZIP 内完整 `mods/RinArcherCore` 放进该副本的 `mods`；保留 `lib/0.107.1`、`lib/0.111.0`、`mod-variants.manifest` 与共享资源，不与另一份 RinArcherCore 同时启用。需要 BaseLib **3.4.7**、RitsuLib **0.6.7 完整多版本包**（含对应 compat 与 shared）。本机测试副本已配置。

只接受已验证的 v0.107.1 / commit 59260271 和 v0.111.0 / commit 41cef1ea，以及清单中对应 SHA-256/MVID。未知构建、身份不一致和内容 DLL 哈希错误均拒绝。Android 实机 **PENDING**。

本轮没有安装到正式游戏、改 Workshop 或写入正式玩家存档。回退测试候选只需停用该独立副本；原候选及历史验收保留原样。跨游戏版本导入 Run 不属于本轮验证范围。
