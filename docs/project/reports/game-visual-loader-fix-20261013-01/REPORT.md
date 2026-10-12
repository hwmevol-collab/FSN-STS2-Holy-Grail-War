# 0.9.4-game-compat.1 · visual-loader-fix-01

从指定上一轮 `build/source`、`build/loader` 复制独立候选；版本仍为 **0.9.4-game-compat.1**。本轮只修改 `PresentationTheme.cs` 与 `WorkshopBootstrap.cs`，其余 229 个源码/依赖文件、28 个共享包资源与上轮一致（含玩法、素材、存档和事件/遗物适配）。具体差异与 DLL SHA 见 [SOURCE_BINDING.json](SOURCE_BINDING.json)。

修复结果：`PresentationCardSkin.Apply` 在布局缓存提前返回前恢复横幅/插画框的 Texture、Material、SelfModulate；仍复用原纹理资源与布局状态。Loader 接受存在的绝对 Assembly.Location；否则使用有效绝对 AppPaths.DataDir 下 `.godot/mono/publish/arm64/sts2.dll`，不按工作目录解析裸名，并记录 rawLocation/resolvedPath。版本、commit、SHA、运行/文件 MVID、程序集名称及内容 DLL 哈希检查均保留。

| 验证构建 | 本轮结果 |
| --- | --- |
| v0.107.1 / 59260271 | Windows 实际图形流程 191 项断言 PASS；身份/分流负向 21 项 PASS |
| v0.111.0 / 41cef1ea | Windows 实际图形流程 191 项断言 PASS；身份/分流负向 21 项 PASS |

包含原生启动/选人/首战、双方手牌真实悬停、原生牌库升级预览/详情、已升级牌、Switch 后牌面；4 张不同成员/稀有度代表牌共 48 次反复刷新，缓存状态、纹理实例和布局均保留。已抽查真实截图。检查数量包含流程与多实例重复断言，不等于所有卡牌/所有玩法覆盖。

路径测试实际执行 `WorkshopBootstrap.Actual`，在 Windows QA 中模拟空 Location、裸名、存在的相对文件、失效绝对路径及 DataDir；有效路径通过，无效 DataDir/缺失 publish DLL 拒绝。错误程序集/另一版本 MVID、相同 MVID 修改 SHA、篡改内容 DLL 均拒绝，原路径和清单恢复后再次校验通过。[VALIDATION.json](VALIDATION.json) 绑定具体结果和新 DLL；日志保留最终路径。该模拟不是 Android 真机回读。

交付：[双版本 ZIP](FSN-RinArcher-0.9.4-game-compat.1-visual-loader-fix-01-dual.zip)、[安装说明](INSTALL.md)。本机 `Launch-Test-v111.cmd` / `Launch-Test-v107.cmd` 使用新建隔离副本及空白 Profile，无 QA 伴随 MOD。ZIP SHA/大小见 [PACKAGE.json](PACKAGE.json)。依赖沿用已验证 BaseLib 3.4.7、RitsuLib 0.6.7 多版本包。

限制：Android 真机与 Human QA **PENDING**；本轮未重跑完整 Run、事件/遗物、铜质鳞片/Wither 或存读档全套，不将上轮结果直接提升为新二进制的全量验证。QA 强制退出仍有 Godot RID/资源回收日志和既有 UID 路径回退提示，本轮不展开资源清理。未改 Workshop、正式安装、玩家存档或历史验收。Skill 的两条诊断已按本轮证据更新，Windows 模拟与 Android 实机状态分开记录。
