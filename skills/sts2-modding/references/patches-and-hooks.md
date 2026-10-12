# Harmony and Hook execution

来源：Basics 10/12，RitsuLib Utilities 03，[索引](sources.md)。日期 2026-10-12，具体版本看 [versions](versions-and-migrations.md)。

## Smallest patch seam — TUTORIAL + Harmony official docs

先模型 override/库扩展，再小范围 Prefix/Postfix。选具体 declaring type、方法类型、重载参数，ref/out 需 ByRef/ArgumentType；别模糊匹配首个同名方法。初始化唯一 Harmony owner ID、明确 assembly，避免重复 PatchAll。

| 注入/机制 | 做法 |
| --- | --- |
| __instance | 实例方法 this；static 不使用 |
| 原参数 / __0 | 名字或位置匹配，写入 ref，类型对实际签名 |
| __result | 同步结果用 ref；skip 原方法提供有效结果 |
| ___field | 三下划线接真实字段，写入 ref；私有字段逐版本查 |
| __state | 同一 patch class Prefix→Postfix 临时数据；不自动覆盖整个异步完成期 |
| __originalMethod / __runOriginal | 方法元数据不能用来调用未 patch 原逻辑；是否运行供判断 |
| Prefix false | 跳过原方法及后续有副作用 Prefix；无副作用 Prefix 可能仍跑；不因 skip 跳过 Postfix/Finalizer |
| Postfix | 增量处理返回值；异常路径清理用 Finalizer/try-finally，不当作永远完成回调 |
| Finalizer | 保留原异常，不吞错误掩盖版本/坏状态 |
| TargetMethod(s), Prepare, Cleanup | 动态目标/版本条件；required target 缺失不 silent ignore 核心功能 |
| Transpiler | 其他扩展点不足才用；匹配稳定 IL 模式而非指令索引，保留 labels/exception blocks；失败不半改写 |

排序用 HarmonyPriority/Before/After 指定关系，参数是 Harmony owner ID，不靠加载顺序猜最后结果；Harmony.GetPatchInfo 查真实竞争者。
官方：[Prefix](https://harmony.pardeike.net/v2/articles/patching-prefix.html)、[Postfix](https://harmony.pardeike.net/v2/articles/patching-postfix.html)、[Priorities](https://harmony.pardeike.net/v2/articles/priorities.html)。教程对 skip 有简化，此处按官方语义约束。

## Async — API_VERIFIED availability, implementation advice

本机 Harmony 2.4.2.0 含 MethodType.Async。普通 async 方法 Postfix 在 Task 返回时跑，不等于效果已 await 完成。完整完成后处理优先对应 Hook，或包装返回 Task 并 await，保留 Task/Task<T>、异常、取消合同。
需修改状态机才查 AsyncStateMachineAttribute/iterator/MoveNext；__instance 是编译器状态机，不能当原类。MoveNext 多次恢复，不是“整张牌一次”，防重复扣费/计数。`<>4__this` 是内部实现，逐版本核对。
Ritsu ModPatcher 可 RegisterPatch/RegisterPatches 后一次 PatchAll；不用为格式统一重写既有 Harmony。

## Listener order — SOURCE_VERIFIED v0.107.1

- CombatState：友方再敌方，每 Creature Powers → 活跃 Player 未融化 Relics/非空 Potions/Orbs/AllPiles cards，每张 card 后 Affliction/Enchantment；Monster 加其模型。最后 Modifiers/Badges/MultiplayerScaling。
- RunState：活跃 Player 永久 Deck cards/Enchantment；战斗外再 Relics/Potions/global listeners；Contains 过滤后外部 subscribers；有 childCombatState 再战斗序列。永久 Deck 与战斗副本生命周期不同。
- Hook.IterateCombatHookListeners 在进入枚举检查 IsOverOrEnding，IsStarting 豁免；少数死亡/终结 Hook 直接遍历。调用方也能提前过滤，如旧 OnPlayWrapper 的 IsInProgress。
- Early/普通/Late 通常整轮遍历，不是每 listener 连跑三种回调；逐 Hook 看函数，不假定都有三轮。

## Important chains — SOURCE_VERIFIED v0.107.1

| 场景 | 先后与陷阱 |
| --- | --- |
| 出牌 | 入 Play → 结果 pile/position modifiers → GeneratePlayCount → 每次 BeforeCardPlayed/history start/OnPlay/Enchantment/Affliction/history finish/条件 AfterCardPlayed → 结果堆 → 空手检查。按 CardPlay.PlayIndex/PlayCount/IsAutoPlay 区分重放 |
| Damage | 附魔加乘 → listeners 整轮 additive/整轮 multiplicative/cap → BeforeDamageReceived → Block → HpLoss BeforeOsty → redirect → AfterOsty → lose HP → block/HP/given/存活 received → death。死者不走普通 AfterDamageReceived；原目标与转移目标不同 |
| Power | Before amount change → given additive/multiplicative → received modifiers → 原生多人缩放 → BeforeApplied/ApplyInternal → modifiers 后回调 → AfterApplied/AfterPowerAmountChanged；读实际 applied 结果 |
| 回合开始 | AmountOnTurnStart → BeforeSideTurnStart → Creature.AfterTurnStart/清 Block → AfterBlockCleared → SetupPlayerTurn 能量/BeforeHandDraw/ModifyHandDraw/Draw/AfterPlayerTurnStart → side/Orb/auto-pre-play。SetupPlayerTurn 并行启动，等待位置影响跨玩家顺序 |
| 回合结束 | auto-post-play → Hook.BeforeTurnEnd（分发 AbstractModel.BeforeSideTurnEndVeryEarly/Early/普通）→ DoTurnEnd → BeforeFlush → PhaseTwo Flush/cleanup → Hook.AfterTurnEnd；新版 Hook 名字不可复制到旧 DLL |

伤害不是每个 listener 先加后乘；preview 也会走修改器，不在纯数值 modifier/预览中产生副作用。

## Newer flow descriptions — TUTORIAL, not old runtime guarantees

0.111 章还覆盖开始/胜利、死亡防止、房间栈恢复、地图生成/恢复、奖励 Populate/Modify/Offer/Take、商店/金币/遗物/药水/球/换堆。用概念定位本机函数，不照搬确切顺序。
新版回合末交错播放、CardLocation、CombatId、结束时 AfterCardPlayed 均有差异。AfterRoomEntered 不授予重复发奖；新地图与恢复地图分开。AfterDeath 可能通知死亡被阻止，应读 wasRemovalPrevented。结束/清理 Hook 能否玩家选择，核对 choice context/调用方。

依据：研究缓存 actual-api 的 CombatState、RunState、Hook、CardModel、CreatureCmd、PowerCmd、CombatManager；绑定 baseline.json。此轮无游戏运行，不升为 RUNTIME_VERIFIED。
