# 双游戏版本交接

最新源码：`reports/game-v0111-compat-20261013-01/build/source`，InformationalVersion **0.9.4-game-compat.1**。从上轮 **0.9.4-vanilla-compat.1** 继续，保留 Android startup fix.2、原版兼容修复、双角色与已有玩法。Loader 在同目录 `build/loader`，单独 AssemblyName RinArcherCore.Loader。

已验证游戏：v0.111.0 / 41cef1ea 与 v0.107.1 / 59260271；完整 SHA / MVID 以及最终候选 DLL 身份见 [验证](reports/game-v0111-compat-20261013-01/VALIDATION.json)。每版 42 项实际短流程 + 21 项版本分流检查；Human QA PENDING，Android / 联机 / 完整 Run / 跨版本导入 Run 未验证。

[报告](reports/game-v0111-compat-20261013-01/REPORT.md)、[安装与独立启动](reports/game-v0111-compat-20261013-01/INSTALL.md)、[源码绑定](reports/game-v0111-compat-20261013-01/SOURCE_BINDING.json)。推荐双版本包共用资源，严格身份匹配，未知构建不得最低版本回退。原 Matrix 文档保持原始签名，新的 GameBuildCompatibility 显式处理已审查 API / 原版 Hook 差异；不要将旧 Matrix 所有分支视为新版逐项运行通过。

上一轮复杂原版事件 / 遗物缺口保留在 [继承剩余表](reports/game-v0111-compat-20261013-01/REMAINING_INHERITED.json)。本轮没有扩大这些适配或自动发布 / 正式安装。历史候选与玩家 Profile 保留。
