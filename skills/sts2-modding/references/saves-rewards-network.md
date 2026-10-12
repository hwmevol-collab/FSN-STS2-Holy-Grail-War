# Persistence, rewards, piles, and networking

来源：BaseLib 09/10/16；Ritsu Gameplay 04/08/09/10/13/14、Utilities 01/10；[索引](sources.md)。2026-10-12。库机制通常 TUTORIAL；本机核对范围如下。

## Match storage to ownership and lifetime

| 需求 | 机制 | 注意 |
| --- | --- | --- |
| 保存 model 的 property | SavedProperty | 不把 field 当 property；支持类型和 model 类别逐库核对 |
| 给现有对象挂状态 | SpireField/AttachedState | 内存附加不自动持久化；TryGet 不应创建默认状态 |
| 对象可序列化附加状态 | BaseLib SavedSpireField / Ritsu SavedAttachedState | 本机类存在；受 SavedProperties 支持类型与 registration freeze 约束 |
| 一局共享/每玩家 | RunSavedData / PlayerRunSavedData | 注册 stable modId/key；per-player 用真实 NetId，不用角色名猜玩家 |
| 跨局设置/解锁 | ModDataStore Global/Profile | Profile 随档隔离；修改缓存后显式 Save，切档失效旧引用 |
| 自定义永久牌堆 | ModCardPileRegistry + RunPersistent | 框架牌堆与真实实例为事实源，不再从 shadow snapshot 重造一副 |

API/SOURCE_VERIFIED：Ritsu 实际 RunSavedDataStore.For(modId).RegisterPerPlayer<T>(key,defaultFactory,options)，T:class,new()；ModDataStore 的 Get/Modify/Save；BaseLib SavedSpireField 类。FSN ContractSave.Register/Get/Slot.Set、CardBanks.ArcherDeck 的 RunPersistent 用法已源码核对。运行恢复证据引用原项目对应报告，不从本次研究推断 PASS。

## Durable checkpoints

注册 data/schema 的默认 factory 稳定，不含随机数/时间戳/Node。Run slot 的 WhenSet/WhenNonDefault/AlwaysWhenRegistered 各决定导出条件；不把 Get 后改对象等同显式 Set/Modify 记录。
数据 payload 只存序列化数值/ID/状态；Node、Texture、combat references 不入 JSON。schema 和 gameplay revision 分开；迁移仅在当前任务明确需要且有合法设计时执行。没验证的旧玩法不能靠“字段能反序列化”当作可迁移。
保存调用完成/RunSaved 通知不保证文件写入成功；核对 native save + sidecar 与同一房间/seed/owner/phase。FSN ContractSave 明确拒绝非安全 mid-combat，并读回 current_run.save 的 _ritsulib/run_saved_data；复用合法 checkpoint，不能擅自补任意出牌中断恢复。

## Rewards and RNG

ModCustomReward 需稳定 RewardType、factory、JSON payload/serializer。随机 offer 在生成时确定并保存；Take/skip/cancel/Continue 恢复都最多结算一次，不在 OnSelect 恢复时重新 roll。
原生 RewardsSet 的 Populate/Modify/AfterModifying/Offer/Take 各有边界；添加 custom reward 后仍要 Populate 和序列化。按来源 budget/稀有度/角色/Act/解锁过滤，distinct 候选容量在 RNG 之前检查；不能末端换奖、空奖或少发。
使用原生 seeded RNG 和正确 stream/counter；纯 preview 不消费。WeightedList 空列表 GetRandom 抛错，用 TryGetRandom 或关闭无合法来源；不要靠重试消费 RNG 绕过不足。
Ritsu SecondaryResource 的 turnStartPolicy/persistencePolicy 是独立选项；Gain/Lose/Spend/Reset 由命令/Hook 执行，Spend 返回成功后再产生收益；X 取实际支付值，不重复读取已变的当前余额。FSN 已有共享 Mana 服务，除明确迁移不接第二套资源引擎。

## Multiplayer — TUTORIAL; actual multiplayer not tested this task

原生动作同步与确定性是玩法事实源，不把一般消息回调当动作队列。Shared run slot 的 lobby staging 由 host 接受贡献，clients 用 per-player slots 和本地 NetId；开始时 commit authoritative snapshot。
Ritsu Sidecar 适合轻量 UI/skin/data 消息；StableSync 描述传输可靠性，不承诺与出牌动作排序。ManagedNetAction 用原生队列，Request=true 仅发出 enqueue 请求，不是动作完成；ownerNetId 只能本地玩家。Combat/CombatPlayPhaseOnly/NonCombat/Any 的执行资格不同；payload 64KB 上限按当前库核对。
Reward 集合选择原生同步，但 custom side effects 仍需在各端确定性或显式同步；用同一 action/context/RNG。不假定调用任意 Cmd 就自动修复所有 custom state 的同步。optional Interop 缺失是正常分支：ModInterop/AssemblyInterop 需正确类型名/assembly 与登记，不硬依赖不可选装模块。
