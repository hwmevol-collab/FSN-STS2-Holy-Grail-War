# Models, registration, and authored content

来源：BaseLib 01–16；RitsuLib Basic Content 01–16、18–19；Basics 05–06；[固定commit索引](sources.md)。日期 2026-10-12。未特别注明的教程用法为 TUTORIAL；具体签名仍查目标 DLL。

## Choose the existing framework

| 内容 | BaseLib tutorial | RitsuLib tutorial |
| --- | --- | --- |
| Card/Relic/Potion | CustomCardModel/CustomRelicModel/CustomPotionModel + Pool | ModCardTemplate/ModRelicTemplate/ModPotionTemplate + RegisterCard/Relic/Potion |
| Power/Enchantment/Orb | CustomPowerModel/CustomEnchantmentModel/CustomOrbModel | ModPowerTemplate/ModEnchantmentTemplate/ModOrbTemplate + 相应 Register 属性 |
| Event/Ancient | CustomEventModel/CustomAncientModel | ModEventTemplate/ModAncientEventTemplate + RegisterSharedEvent/Ancient 或 RegisterActEvent/Ancient |
| Character | PlaceholderCharacterModel/CustomCharacterModel + 三类池 | ModCharacterTemplate<CardPool,RelicPool,PotionPool> + RegisterCharacter |
| Monster/Encounter | CustomMonsterModel/CustomEncounterModel | ModMonsterTemplate/ModEncounterTemplate + RegisterMonster/ActEncounter |
| 全局 Hook | CustomSingletonModel | HookedSingletonModel + RegisterSingleton |

API_VERIFIED：本机 BaseLib 3.4.7 与 Ritsu 0.6.6 compat/0.107.1 元数据支持现有模型/工具（baseline.json）。FSN 已使用 BaseLib 内容，Ritsu 负责额外 piles/save/targeting 等；别因新版教程优势自动重写注册。

Ritsu 属性需 EnsureGodotScriptsRegistered + ModTypeDiscoveryHub.RegisterModAssembly，且在注册关闭前执行。ContentPack builder 的 Apply 一次，按依赖先后注册；Direct Registries 用于动态关系。BaseLib 使用自己的注册语义，不能同时给同一类型重复注册两套。
BaseLib ID 由 namespace 前缀与原模型 ID 组成；Ritsu 为 ModId_Category_Stem。发布后 ID、注册 key、动态枚举标识稳定，牵涉存档/本地化/互操作。不要手工猜 ID，读 ModelDb/注册实际结果。

## Cards and descriptions

- 模型定义 CanonicalVars；OnUpgrade 用 UpgradeValueBy；OnPlay 用实际 PlayerChoiceContext，await 原生命令以保持顺序。ModelDb 模型通常 canonical；拿入局/战斗的 mutable 实例或 factory，不直接改 canonical 数据。
- DamageCmd/CreatureCmd/PowerCmd 的 dealer、cardSource、Owner 与目标明确。ValueProp 位组合含 Move、Unpowered、Unblockable；不要重复施加原生力量/易伤倍率。Follow a matching vanilla model 的控制流，再核对本版本参数。
- Exhaust/Ethereal 等写 CanonicalKeywords；Strike/Defend 标签决定其他模型交互；格挡识别属性取实际类，教程 Tags/CanonicalTags/GainsBlock 名字可能随版本变。
- res://ModId/localization/zhs 或 eng 的 cards/relics/powers/potions/events 等 JSON 用实际模型 ID。DynamicVars key 与描述占位一一对应；diff()/inverseDiff() 管变化颜色，energyIcons()/starIcons() 管图标。BBCode/SmartFormat 不是玩法实现。
- 普通 Power description 用静态文本；smartDescription 的 Amount/Owner/Applier/Target 等需要实例；remoteDescription 可描述远程来源。收藏/升级/奖励预览无 Run/Owner，不能无条件访问 Owner guarded getter。
- Tooltip 跟文字语义一致：文本中“消耗一张牌”不等于该卡带 Exhaust；ExtraHoverTips/AdditionalHoverTips/WithTooltip/WithSharedTooltip 取当前库扩展点。

## Relics, powers, enchantments, and orbs

遗物挂载并不代表所有 Hook 只发给它的 Owner。比如 AfterPlayerTurnStart 应过滤 player==Owner；Power.AfterCardDrawn 先确认 card/Owner 属于目标生物/玩家。所有权由参数确定，不用 LocalContext 替代远程或非当前成员。
Power 选择 Type、StackType、InstanceType 和来源/持续时间；临时状态需检查自身/另一侧 turn-end、额外持续回合与多来源合并。PowerCmd.Apply 可被免疫/修改，不因尝试施加就给成功奖励。叠加策略是玩法合同，不照搬 Counter 当默认。
Enchantment 的 CanEnchant、OnEnchant、加乘修改、OnPlay 都独立；复制/变形/保存应保留相应实例数据。Orb Passive/Evoke 的数值显示、触发者和返回目标一致；新版本 Triggered/PassiveActivated/EvokeActivated 改名需查迁移。
Singleton 接全局事件但仍需对具体 owner/scope 过滤，避免一份原生收益自动给所有角色。

## Events and ancients

多页事件 = eligibility(IsAllowed) → 初始选项 → await 支付/奖励 → SetEventState 新页面 → SetEventFinished；不要在生成选项时支付/抽随机结果。取消和失败保持未结算；恢复已完成页面不重发奖。
BeforeEventStarted/OnEventFinished 可临时限制药水，但异常/恢复也必须恢复限制。教程 CanUseOrRemovePotions 属新版，旧版 CanRemovePotions 要查 DLL；避免永久泄漏 UI 限制。
事件战斗用 Encounter、EnterCombatWithoutExitingEvent、Resume 的原生房间栈；版本间内部 CombatState/EventCombatSynchronizer 不同。别自行再造战斗/奖励 engine。
Ancient 可按 Act 注册，AllPossibleOptions、GenerateInitialOptions 与先古遗物依赖一起核对。IsAllowed/角色/Act/解锁/稀有度仍约束选项，不把注册成功当池资格。
对话：AncientID.talk.CharacterID.组-行[可重复r].ancient|char|next；firstVisitEver/ANY fallback；动画 suffix 与音频选项为库扩展，按现有本地化格式。Chronology/Epoch/timeline 需真实条件及 card/relic unlock 映射，RequiresEpochAndTimeline 是主动选择，不擅自放开原生解锁。

## Characters and monsters

角色有 cards/relics/potions 三池、starting deck/relics、选人预览、资源 profile、能量计数、地图/商店/休息点/战斗 visuals。注册后还要检查**实际选人进入的是哪个 CharacterModel**，不能以菜单看见立绘就断言入口正确。
Placeholder/fallback 适合缺少资源阶段，不伪称最终美术已验收。Ancient Tooth/Ouroboros/Grimoire 等变换需要显式原生资格与真实引用闭包。
Monster 的 MoveStateMachine 同步 intents、攻击/格挡效果、Ascension HP/damage 与 NextState/branch；Encounter 才决定出场组合、RoomType、Act、slots、camera、背景。定义 Monster 不等于它已加入正常遭遇池。

## Capabilities and computed variables — TUTORIAL; verify installed subtype

Ritsu ModelCapability 组件可以给 model 独立 Hook/description/glow/assets/play-result 能力；从 registry/Create/GetOrCreate 创建，不直接 new canonical AbstractModel 子类。CardPlayCapability 过滤自己 card；CharacterCapability 不等于原生战斗 listener。SaveAdditionalState/LoadAdditionalState 或 StatefulModelCapability 存附加数据。GetOrCreate 不等同 Add/Apply/Subtract 的 merge 行为，状态和复制/升级 carry-over 要明确。
ComputedDynamicVar 适合目标/升级/预览相关数值；static context evaluator 防克隆后捕获旧 card；读 ctx.BaseValue 保持升级一致。ComputedDamage/Block 预览走原生修改器，普通 Computed 不自动加伤害 Hook。执行用 EvaluateValueOrDefault(target)，别用 BaseValue 代替动态结果。不得预览推进 RNG/支付/改变层数；只在任务需要时引入组件，保留既有简单模型。
