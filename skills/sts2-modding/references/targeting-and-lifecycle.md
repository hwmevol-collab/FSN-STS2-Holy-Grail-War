# Targeting and lifecycle

来源：Basics 12；Ritsu Gameplay 11/12、Utilities 02/06/07，[索引](sources.md)。核对日期 2026-10-12。

## Target resolution — API/SOURCE_VERIFIED on Ritsu 0.6.6 compat/0.107.1

CardModelTargetingExtensions.GetTargets(card, selectedTarget=null) 位于 STS2RitsuLib.Combat.CardTargeting。
单体选择类型省略 selectedTarget 返回空；显式目标先过 IsValidTarget；Self 返回 card.Owner.Creature；多体根据当前 combat/filter；RandomEnemy 用 Owner.RunState.Rng.CombatTargets.NextItem。

**不要在 hover/高亮/可打出检测调用随机目标解析。** RandomEnemy 分支推进 RNG。执行时按设计解析一次，重用该实例或目标序列；是否重取每一击由原版/已批准机制决定，不靠 UI 预览生成随机结果。证据：actual-api/STS2RitsuLib.Combat.CardTargeting.CardModelTargetingExtensions.decompiled.cs 的 GetTargets；同名本地 Ritsu src；DLL身份 baseline.json。精炼实战条目见 [fsn-practice](fsn-practice.md)。

CustomTargetType.RegisterSingleTargetType/RegisterMultiTargetType 的 ID 稳定；条件需涵盖存活/可击中/阵营/特殊合法性。库同时接入 mouse/controller/CanPlay/IsValidTarget，**特定 UI 行为仍需实际验证**。Anyone/Everyone/attacking/blocking/highest/lowest HP 是教程路由，不等于本项目已批准改变卡目标。

## Keep ownership and recipient distinct

CardModel.Owner 是 Player；自定义多成员玩法可能共用一个 Player。member、dealer、damage recipient、explicit locked target、card instance owner 是不同信息，不能统一取当前前排。
FRONT 在既有合同决定的结算时点解析；LOCKED 保留显式对象；多段打已死亡目标是否继续/取消按原生约定。预览要显示真实受益者，同时**不改 TargetType 或实际提交目标来修高亮**。
选择从原生 UI/PlayerChoiceContext await 结果；null/cancel 非成功。重试前清旧选择与高亮；冻结已选对象，不重复花钱/资源、切换或 reroll。ThrowingPlayerChoiceContext 仅适用于确定不会请求玩家选择的命令，不能用于可弹出选择的异步回调。

## Registration versus ready versus run — TUTORIAL + local API/source checks

初始化注册一次，不把 ModelDb.Init 当作游戏 UI 已就绪。Ritsu RegisterModAssembly/ContentRegistrationClosedEvent、ModelRegistry/ModelIds/ModelPreloading 阶段各有职责：类型注册在 freeze 前；ModelDb.GetId 在 IDs 就绪后；神圣根节点/UI 在 GameReady 后；Profile data 在 ProfileDataReady 后。
SubscribeLifecycle 返回的 subscription 保留并按生命周期 Dispose；晚订阅默认不重播过去事件，replayCurrentState 仅对可重播状态生效。注册本身不保证 observer 获得已发生 GameReady。
RunStarted 初始化新 Run，RunLoaded 绑定恢复状态，RunEnded 清局内对象；不能在 RunLoaded 发起新奖励/重新生成初始卡组。RoomEntering/Entered/Exited、ActEntering/Entered、CombatStarting/Victory/Ended 和 card/pile events 是通知层；不是所有名字都对应同名原生 Hook，也不能仅凭名字判断原生异步 Task 已全部结束。
ProfileSwitching/Switched 与 ProfileDataChanged/Invalidated 应解除旧绑定，避免跨档引用。RunSaving/RunSaved 是保存通知，磁盘结果另读回；CreatureDiedEvent 的 WasRemovalPrevented 为 true 可能尚未真正死亡。

本机元数据证实生命周期 API/相关事件存在；广播与原生 Hook 的逐项精确相对时间仍 TUTORIAL，未来任务沿实际 compat patch 的 TargetMethod 和 async bridge 核对，不全量推导。

## UI attachment lifetime

NodeAttachment 在 parent Ready 附加；TryGetAttached 不创建缺失节点。注册 Name/NodeName 与 DuplicatePolicy 保证同一 UI 不叠加；ChildIndex/InsertBeforeName/InsertAfterName 三选一。需要 script conversion 时用正确 factory，SetupTiming/IncludeDerivedParentTypes 按实际需求。
Ready 可能因退出/重进/切场景重复；node reference、signal subscription、Tween、CancellationToken 与实际 SceneTree 生命周期配对。不要只查非 null：验证 Godot 对象有效、在树内、仍属原 combat/run。
“父节点重入导致 native reticle token 已取消”的 FSN 已实现局部修正见 fsn-practice；只针对该场景，不能一般性绕开所有 cancel token。
