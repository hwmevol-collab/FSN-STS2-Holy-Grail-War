# v0.111.0 / v0.107.1 兼容候选

本轮从 **0.9.4-vanilla-compat.1** 继续，交付 **0.9.4-game-compat.1**；没有回退、覆盖旧源码或重做上轮兼容。实际新游戏为 **v0.111.0 / 41cef1ea**，保留的旧副本为 **v0.107.1 / 59260271**。严格 SHA-256 / MVID 与最终 DLL 绑定见 [VALIDATION](VALIDATION.json)、[SOURCE_BINDING](SOURCE_BINDING.json)。

修复真实 API 差异：回合末 Side Hook、伤害命令 CardPlay、牌堆新增的所有者变更参数、药水生成、奖励构造和方向导航。保留真实角色伤害来源与出牌记录。原版 Hook 改名分别接回既有作用域；Diamond Diadem 按新版原生 20 Block + 1 Blur 机制适配，旧版继续原有机制。旧 Matrix 保持不可变，由明确的版本桥与原生条件处理新版；未知新 ID 不开放。

**双版本包在两个实际游戏版本各通过 42 项真实流程检查；各 21 项严格分流 / 拒绝检查通过。** 覆盖启动、角色选择、Archer 开战、Switch、铜质鳞片 3 荆棘不复制、Wither 后备冻结、首战与奖励、Archer 事件归属，以及两次真实磁盘保存 / 继续。新版单版先通过同类流程，再验证最终双版本包。使用新 Profile；铜质鳞片 / Wither / 指定事件为隔离 QA 夹具，不能当作完整自然 Run 或逐个遗物分支验收。

双版本 Loader 复用 [STS2-Template 的登记方案](https://github.com/SlayTheCircle/STS2-Template/tree/767e7be8c1f7d7a0d51e261e1147023d852ab881/src/STS2-Template.Loader)，按 version / commit / SHA / MVID 精确选择，并校验内容 DLL；没有最低版本回退。共享图片、音乐、PCK 与本地化从包根读取；单版与双版资源沿用原字节。实际依赖为 **BaseLib 3.4.7、RitsuLib 0.6.7**，分别使用对应 compat 目录。

试玩：双击 **Launch-Test-v111.cmd**；旧版用 **Launch-Test-v107.cmd**。新 Profile、无自动 QA MOD。外部安装及依赖见 [INSTALL](INSTALL.md)。交付 v111 / v107 单版与推荐双版本 ZIP，清单、CRC / SHA 读回见 [PACKAGES](PACKAGES.json)。未由本任务改正式安装、玩家保存或 Workshop。

限制：Android 实机、联机、物理手柄、完整 Run、跨版本导入旧 Run 未验证；Human QA PENDING。原版复杂事件与遗物缺口继承到 [REMAINING_INHERITED](REMAINING_INHERITED.json)，没有宣称全原版已完全兼容。改名遗物的全部获取 / 效果分支未逐一运行，仅保留源码核对与本轮定向流程范围。既有 UID / 退出资源清理警告仍存在。已将本次确认的版本迁移与 Loader 经验更新到 sts2-modding Skill。
