# Locked Design Bible

Last reviewed: 2026-10-09。来源：[用户设计合同](project-memory/request-source.txt)；实现证据由
[ACCEPTANCE_INDEX](ACCEPTANCE_INDEX.md) 与 [MILESTONE_INDEX](MILESTONE_INDEX.md) 导航。
LOCKED 未经用户明确授权不得改变；IMPLEMENTED 只表示对应已验收工程范围。PROVISIONAL 为
尚可调整的长期方案；DEFERRED / NOT_IMPLEMENTED 为计划。DESIGNED 不代表交付。

## Contract Pair / Energy / Switch — LOCKED, IMPLEMENTED (A)

一个 MASTER + 一个 SERVANT；同一时刻 ACTIVE / RESERVE。双方独立 HP、MaxHP、Block、Status、
Deck、Draw、Hand、Discard、Exhaust。每 shared player turn 基础 3 shared Energy，非 3+3；已兼容的
原生 max-energy modifiers 仍按 single Contract budget 执行（E2A）。
每 shared player turn 1 voluntary free switch，0 Energy；不是 Card/Skill/Attack/Power；不抽牌、
不弃牌、不刷新 Energy、不生成新 Turn；下个 shared player turn 恢复。

## Dual Hand / Hand Banking — LOCKED, IMPLEMENTED (A/B)

双方各 Opening Hand = 5，之后选 Starting Active。Reserve Hand visible/read-only/banked。
Switch-out 保留同一 card instances。正常 turn end 只有最终 Active discard/cycle，Reserve 保留手。
Reserve 仍经历 statuses、DoT、timers、Block lifecycle、shared turn effects；Ethereal 等不能永久冻结。
HAND_BANKING_REIMPLEMENTATION = FORBIDDEN_WITHOUT_AUTHORIZED_TRIGGER。

## Target / Block / Status / Death — LOCKED, IMPLEMENTED (A/B)

Target taxonomy：FRONT（resolution 当前 Active）、MASTER、SERVANT、BOTH、LOCKED（显式具体 member）、
ANY_CONTRACT_MEMBER。角色目标不随普通切换改成另一 role。
Block member scoped；Switch 不转移、不清除。普通 Block 在 shared player turn start 双方按生命周期
清理；Reserve 不能永久银行 Block。
Status clock：Shared-turn（Reserve 继续）、Action-based（等相关 action）、Persistent；scope SELF/FIELD/CONTRACT。
任一 member 死亡 = Contract Defeat；保留 death-prevention pipeline 扩展点。
QA Rival fixture 的任一死亡也败北；完整 authored Rival 内容仍 NOT_IMPLEMENTED。

## Contract Mana / Jewel / IA — LOCKED, IMPLEMENTED (A/B/C)

Mana encounter shared：start 3 / cap 10，每场 reset；Rin Active shared turn start 基础 +1；Mana 0
无默认额外 debuff。Rin Jewel：start 1 / cap 3，每场 reset；Reserve 保留；Jewel Boost 与 Direct Consume
Jewel 分开。
Archer Independent Action：每 shared player turn 第一个打印 Mana Cost exactly 1、且 IA 实际完成
1→0 的牌才触发；不减 Energy。其他 modifier 已令最终 Mana 0 时不消耗 IA；未用不累计。

## Projection / ARM_RESOLVED / Reinforced — LOCKED, IMPLEMENTED (B/C)

Archer 无 numeric projection meter。Projected Arms 为 generated special card instances；只有
Kanshou & Bakuya、Rho Aias、Hrunting 三件，无第四件。正常成功使用 Exhaust；未用且 Archer end
Active 时 normal discard；Switch-out 可 Hand Bank。当前数值/升级只由 [CONTENT_BASELINE](CONTENT_BASELINE.md)
抽取，不在这里维护第二份卡表。
ARM_RESOLVED 为每战 set；只由正常成功用兵装、U02 Broken Phantasm、R03 high-order Broken 加入；
generation/bank/discard/generic sacrifice C11/canceled effect 不加入。
Rin Reinforce Projection 设置 next successful projected generation = Reinforced。可选 Jewel Boost
同时给该 instance Mana -1；Pending boolean/non-stacking，成功生成才消费。强化按武器各自效果，
不是 generic +5。

## Command Spell — LOCKED, DESIGNED, NOT_IMPLEMENTED, DEFERRED

COMMAND_SPELL_IMPLEMENTATION = NOT_IMPLEMENTED。
Run 3/3 seals，无常规回复；未来 CONTRACT_CORE_RIN_ARCHER system relic/interface 为非经济遗物，
不可 shop/remove/transform/duplicate/random reward。
SURVIVE：1 seal lethal intervention，HP→1，同一 damage/HP-loss sequence 内不可再死；下一独立伤害
可再次 lethal；适用 combat、DoT、event HP loss。
UNLEASH：1 seal，必要时 command-switch Archer Active，不消耗 normal free switch；Mana→10；本 shared
turn Archer Card Mana cost=0；Energy 不变。
RECALL：1 seal Command Switch，忽略 ordinary switch lock，不消耗 normal free switch；清 explicit
target LOCK；MASTER/SERVANT role targeting 不能绕过。

## Dual Reward / Persistence — LOCKED, IMPLEMENTED (D1)

每 Vanilla normal Card Reward：1/2 MASTER Rin，3 cards、pick 0–1/skip；再 2/2 SERVANT Archer，
3 cards、pick 0–1/skip；最多 2 permanent cards。双方独立 rarity state/logical RNG；seeded offers、
Save stable、reload 不 reroll。Starter 排除 ordinary reward，Projected Arms 排除 permanent reward。
原生 Loot 容器持有 Gold/其他奖励；点击 Card Reward 才进两阶段；完成返回同一 Loot 容器。
E2A 原生 bonus reward 只分配一次预算，例如 3+4，而非 4+4；先决定 Owner 再 roll hidden result。
Run persist：双方 HP/MaxHP/permanent decks/upgrades，Gold/Relics/Potions、现有 map/run flags；future
Command Seals 等未来实现后才有持久化。Encounter reset：Mana/Jewel/Hands/combat piles/Block/combat
statuses/Projected Arms/Pending Reinforcement/ARM_RESOLVED/FIELD；战后不自动治疗。
现有 Save/Continue 以已验收 native checkpoint 为限，非任意战斗逐帧恢复。

## Campfire / Merchant — LOCKED, IMPLEMENTED (D2; UX update E2A)

Rest 选 Rin 或 Archer Focus：Focus 30% MaxHP，Partner 10%；overheal 不转移；两次真实 Character Heal
仍只一次 Rest action。当前 UX：Rest→choose focus→click member→immediate commit，无第二层确认。
Smith：两副 permanent Deck 共用 target budget=1，只升级一张；Projected Arm 不能 Smith。
Merchant：一个 Contract Gold wallet；Rin ×2 / Archer ×2 card stock；Owner 不影响价格；Starter/Projected
不进 ordinary shop card pool。每店一个 removal service、两副 Deck 共用；全 Run 一个 global
cardRemovalCount，原生递增价格；跨 Owner 不重置。

## Vanilla compatibility — LOCKED, IMPLEMENTED in independent E2A candidate

PRESERVE_VANILLA_EFFECT_BUDGET；PRESERVE_NATIVE_CHARACTER_ACT_POOL_UNLOCK_CONDITIONS；
NO_POOL_EXPANSION_BY_CLASSIFICATION。原生一次收益不因两成员自动复制。
Scopes：CONTRACT、ACTIVE_AT_TRIGGER、CARD_OWNER、DAMAGE_TARGET、CHOOSE_MEMBER、CHOOSE_DECK、
DUAL_DECK_SELECTOR、RANDOM_PERMANENT_CARD_UNION、ACTIVE_HAND、ENEMY、UNSAFE。
Combat start personal effect 用 Starting Active；draw/hand 只 Active hand，不远程改 Reserve。
Card-play 按 actual card instance Owner。On-damage 按 actual DamageEvent recipient；BOTH 若两个真实
events，各合法触发。Healing/MaxHP/personal Block/Strength/Dexterity/member Potion 选择真实 member。
合法永久随机卡从两 Deck eligible instance union 均匀抽 instance，不先 50/50 选 Deck。
INFORMATION_PARITY：choose owner→roll hidden result，除非 Vanilla 本来先展示结果。
A NATIVE_SAFE / B GENERIC_ADAPTER 仅在 readiness 完整时启用；C WAITING_FOR_CUSTOM_ADAPTER；D
FILTERED_PUBLIC_ALPHA；unknown/new ID fail closed。Compatibility-ready 不等于加入 Rin native Pool。
固定依赖先全闭包 ready；间接来源先保留原生池/角色/解锁/稀有度，验证完整 budget/distinct 容量
再 RNG；不足整来源/选项 unavailable，不少发、换奖、空奖或末端过滤。
Matrix lessons 必须保留：TARGET_SCOPE_SOURCE_CONSISTENCY、TRANSITIVE_ELIGIBILITY_CLOSURE、
FIXED_REWARD_DEPENDENCY、MULTI_TARGET_EFFECT_SPLITTING。Brimstone/Philosopher enemy Strength
是 ENEMY；Potion Courier fixed Foul Potion dependency 仍 C。当前 Matrix 与计数见
[COMPATIBILITY_STATE](COMPATIBILITY_STATE.md)；正式 v0.5.1 尚未替换 candidate。

## Public UX — LOCKED, IMPLEMENTED engineering; human retest CONFIRMED_PASS

Starting Active native choose-a-card scene：两 transient MASTER–Rin/SERVANT–Archer cards；不入 deck/
pile，不算 play、不触发 counter/reward/history、不改 opening hands。
FRIENDLY_POTION_TARGETING：战斗内原生 Potion throw/target UI 直接指向 Rin/Archer 真实 Creature，
Reserve 合法；cancel 不 consume，立即 retry；非战斗 fallback member popup。
Rest single-click commit 沿已验收 30/10，一次行动。正式
[MILESTONE_E2A_HUMAN_QA_CLOSEOUT](reports/MILESTONE_E2A_HUMAN_QA_CLOSEOUT.json) = PASS，参见
[CURRENT_STATE](CURRENT_STATE.md)。复用四项 USER_CONFIRMED UX 复测，原具体时间 UNKNOWN；
其余兼容覆盖沿原工程证据，不把软件 controller PASS 当作物理手柄真人 PASS。

## Long-term enemy / war / roster — DESIGNED, NOT_IMPLEMENTED

Rival Contract 状态：Master/Servant HP、Active/Reserve、Mana、visible Command Seals、switch；行动：
authored Action Set + Intent + AI state machine，无隐藏 Enemy Deck。普通 Attack FRONT；特殊可
Master/Servant/Reserve；任一死 = defeat。完整 Rival implementation DEFERRED。
Holy Grail War：7 Contracts，玩家选一、亲自击败其余 6，不用 NPC offscreen elimination 代替；
Reconnaissance/Escalation/Endgame，每阶段 2 Rival，玩家选顺序，后一个 stronger Showdown。
HOLY_GRAIL_WAR_IMPLEMENTATION = NOT_IMPLEMENTED。
Roster PROVISIONAL（输入称“建议/接受”，未给每项单独锁定证据）：Shirou/Saber、Rin/Archer、
Sakura/Rider、Illya/Berserker、Kuzuki/Caster、Bazett/Lancer、Zouken/True Assassin。Kirei/Gilgamesh
为 post-war/hidden threat candidate；Sasaki 为 Caster special encounter；Shinji 为 Rider/Sakura narrative
role，非长期默认 player Contract。
Rin identity LOCKED：Jewel Magecraft / Combat Magecraft / Flow & Conversion / Contract Support；
Archer identity LOCKED：Projection/toolbox/Arsenal/IA/ARM_RESOLVED。UBW 为高端 build endpoint，
UBW_IMPLEMENTATION = NOT_IMPLEMENTED；禁止 generic NP gauge。Full Act、E2C、正式 Presentation
和 Workshop 状态见 debts，不能从长期设计推断已实现。

## E2B Candidate 01 historical native room spine scope — PARTIAL

E2B 初次任务授权地图/房间适配；当时证据见
[E2B](reports/MILESTONE_E2B_FULL_ACT_ROOM_SPINE.json)。独立开发 flag 使用原生 StandardActMap，
复用 Global Contract Engine、E2A resolver、原 Loot/序列化与 EnterAct。Registry 分类和 Matrix 不变。
Boss 保留原生单 Owner CardReward 的预算和池；不擅自套普通 Dual Reward、补充卡池或削减数量。
Empty native Event pool 无合法回退时先关闭入口；Native exhaustion 不得落入被拒绝内容。
Ancient C 内容保持关闭。因此 fullAct 仍 NOT_IMPLEMENTED，组件/磁盘恢复通过不等于完整闭环。
E2A 四项 UX 的已确认 formal PASS 只属于原 E2A Candidate；E2B Human QA / Closeout 为 PENDING。

## E2B blocker resolution — 2026-10-09 authorized development contract

本次任务授权的 `CONTRACT_BOSS_CARD_REWARD` 使用双方已验收 Alpha Rare 池的并集，保留原生 BossEncounter Rare 规则、三个不同候选、共选择 0–1 张，候选明确 Owner，永久卡只进入对应成员牌组。Offer 采用独立确定性 Boss 流并写入原生 Loot Ledger 关联的 Contract sidecar，取消不结算，领取或跳过最多结算一次。普通 Dual Reward LOCKED 合同不变。旧 E2B 报告的暂行单 Owner 阻塞是历史开发边界，并非 LOCKED Boss 合同；本合同依据新任务授权建立，实际验收状态以新报告为准。

精确 C 适配仅限 Neow、Tezcatara、JungleMazeAdventure、ColossalFlower。Native character/Act/unlock/HP 条件保持；资格通过并不扩展普通池。Ancient 入幕原生恢复仅作用于原生 Owner Rin；不同时恢复 Archer。角色定向事件使用既有 MemberTargetResolver 明确选一人，原生 Gold/Relic 预算仍只结算一次。全部事件候选已访问后，Unknown/Event 在分派前关闭，不允许原生游标回落到不兼容或重复事件；此最小池覆盖限制需要在完整路线与试玩中披露。

本次内容是 E2B 内的授权增量，Engineering、Human QA 与 Formal Closeout 分开；新设计文本本身不批准任何 PASS。

E2B actual-native regression adapters (2026-10-09): native ordinary-monster AllOpponents maps
one Contract entity to existing FRONT, preserving original hit count. Without an enemy Contract,
FRONT card effects select an ordinary enemy through the native card target UI; that play retains
its selected target for every hit and does not retarget a dead target. Existing FRONT Alpha power
checks reuse the selected card in native Play. Existing enemy-Contract FRONT/MASTER/SERVANT/BOTH
and authored locked targets are unchanged. Temporary native Status cards reuse their existing
GenericCombatCardOwnership binding during a native batch hand flush; only one bound member is
accepted, with no permanent foreign cards, no mixed-member admission or bank reconstruction.
These changes address actual runtime failures recorded in the new E2B evidence, rather than
relaxing ownership or targeting contracts. Full Act acceptance remains evidence-gated.

E2B Treasure Continue adapter：复用已验收的 act/map-coordinate Treasure ledger；Complete 与 GoldProcessed 均成立时，恢复已完成 Treasure UI 不再写入新的入口 checkpoint，不改变已保存的结算阶段。原生非战斗 Continue 的 history append 语义保留；不重发 Gold/Relic，不重新抽取 Treasure，不引入 mid-combat 保存。最终状态由新候选真实 checkpoint 检查决定。

当前 E2B Blocker Resolution 实际结论见 [新验收](reports/MILESTONE_E2B_BLOCKER_RESOLUTION_01.json)，优先于上段 Candidate01 暂行约束；新合同不自行提升工程/真人状态。

## E2B Event Exhaustion Final — ACCEPTED engineering scope

当前原生完整 Act 工程 PASS，见 [最终验收](reports/MILESTONE_E2B_EVENT_POOL_EXHAUSTION_FINAL_RESOLUTION.json)。原生 RoomSet 的 VisitedEventIds 是唯一优先软条件；真正一次性、角色、Act、解锁和状态资格由 IsAllowed 保留。耗尽后仅复用原版允许重复的合法 Event，最多扫描一个原生池周期，不改 RNG/Unknown 概率、不扩池。历史“一次性候选”措辞由 ADR-084 在此 scope 明确 supersedes，旧报告保留。

Hive 精确增加 LostWisp：Search 原生 60±15 shared Gold；Claim 原生 LostWisp 遗物和恰好一张 Decay。通过既有 owned-card/pile/save 服务绑定到选择的一个成员永久 Deck，仍是原版诅咒，不是新增 Alpha 卡牌；不可打出、不可升级，回合末手牌对固定 Owner 原生 2 Unpowered|Move damage，普通卡池/奖励/商店不包含。原四项 C 及 Boss owner budget 保持，不另造 Event/Contract Engine。原生新进度无 Ancient 的起点、强制 Event/Event/Monster 及 post-Shop blacklist 原样保留。

工程、Human Retest、Formal Human Closeout 分离：后两者 PENDING；完整 Run/平衡/物理手柄/其他未实现系统未获批准。E2C 仍 NOT_STARTED，本轮结束停止。

## Gameplay V1.2 — authorized independent candidate

2026-10-10用户正式授权本轮统一实施；54模型JSON数值在本独立玩法Candidate supersedes旧卡牌数值基线，
但不覆盖LOCKED底层合同。实现/机器规格/工程证据见
[报告](reports/rin-archer-gameplay-v1.2-20261010-01/IMPLEMENTATION_REPORT.md)、[规格](reports/rin-archer-gameplay-v1.2-20261010-01/IMPLEMENTED_MANIFEST.json)、
[验收](reports/rin-archer-gameplay-v1.2-20261010-01/ENGINEERING_ACCEPTANCE.json)。状态 IMPLEMENTED_CANDIDATE；Human/Formal PENDING。
双方各10张起始实例（Archer弓箭/投影各2），奖励池各20张（8 Common / 8 Uncommon / 4 Rare），生成兵装3件。
原11种起始/28张奖励加12新奖励及3兵装共54模型。费用/完整普通升级文本唯一实现目录为
[GameplayCatalog](Content/GameplayCatalog.cs)，效果见 [GameplayRules](Runtime/GameplayRules.cs)。

供魔获得魔力与兑换能量两分支分别每共享回合一次；C13所有副本共享一次额度。
Hand Tuning每目标成员每共享回合一次；允许明确选取Reserve真实手牌实例，以自身牌堆和原生抽弃事件/RNG结算，
保持Owner/实例/正常回合末及Hand Banking。Reserve展示本身仍只读；只有已确认的卡牌效果执行整理。
选择取消不支付、不切换、不重洗RNG；满手/非法目标/额度耗尽显示原因。
强化投影Pending先于U10，成功生成一次最多消费一个强化来源，失败保留；IA仍精确印刷及实际魔力1→0。
跨回合待命保留至本场消耗/重置；U15不叠加，仅消费合法Archer正能量牌。
同名Power最高等级单引擎，手动重复副本同ID每共享回合一次抽1张自己的牌，自动/重放不补偿。
协作事实源是成功CardPlay；多段额外伤害按整张卡总额分配，成长本次效果先用旧层数再累积。
新增GameplayRevision/CardPoolRevision及Schema3，绝不把Matrix作为玩法版本，不迁移旧Run。
旧工程/真人验收及完整Act证据保持原SHA范围；本Candidate完整Run、平衡及物理手柄待真人试玩。

## 2026-10-10 Gameplay方向更新与QA修复

用户已确认允许小卡组及合理无限流，取代默认防无限的平衡目的；上节V1.2限次仍描述当前实现，并未在本轮删除。共享3能量、免费Switch、IA精确1→0、Owner/真实实例/RNG及原生事件合同不因此失效。
54模型中文表达和悬浮提示已优化，费用/效果/目标保持；ARC-C14审计无数值改动。新Candidate同一Gameplay/CardPool/Schema3，可在新的隔离Profile继续原V1.2合法检查点副本；其他旧玩法版本仍拒绝，不迁移。
现有引擎不保存任意出牌中断现场，原试玩存档只恢复到其原生合法检查点，不补算旧失败技能。
[报告](reports/rin-archer-v1.2-human-qa-fix-20261010-01/REPORT.md) / [验收](reports/rin-archer-v1.2-human-qa-fix-20261010-01/ENGINEERING_ACCEPTANCE.json)；Human/Formal PENDING，E2C NOT_STARTED。

## Gameplay V1.3 — authorized expansion

本轮用户已授权实现输入V1.3 JSON/Markdown；其历史DRAFT标记不再构成停止条件。
对本独立玩法版本，上文V1.2的供魔两分支额度、C13共享额度、每成员Hand Tuning额度、
C16同实例回合锁、同名Power抽牌补偿回合锁均被明确放宽。真实根出牌、原生重放和重复Hook仍须区分；
同名Power最高等级单引擎，新的手动重复副本逐次抽1，自动/原生重放不提供重复副本补偿。
共享3能量、免费Switch每回合一次、IA精确1→0、双独立牌组与Hand Banking、ARM_RESOLVED不同种类集合、
Dual Reward/Boss预算及Owner、任一成员死亡失败，继续LOCKED。新增兵装累计次数与原不同种类集合分别维护。
36张新奖励牌使双方正常池各38张（13普通/15罕见/10稀有）；11起始模型与双方各10实例不变，3兵装不扩品种。
自用强化和兵装强化待命互斥；成功生成时强化投影优先于U10且只消费一个来源。
虚弱/易伤/脆弱/中毒按真实来源、层数、生命周期转移；来源或计时不兼容的同类合并不合法，免疫拒绝不奖励。
指数倍率、累计兵装及下一回合能量欠账使用宽整数；伤害/格挡/能力量仅按已核实原生999999999边界饱和，
能量/累计统计按各自Int32存储边界保护，不设平衡上限。原生力量、虚弱等在直接基础效果之后结算。
GameplayRevision=RIN_ARCHER_GAMEPLAY_V1_3，CardPoolRevision=RIN_ARCHER_CARD_POOL_V1_3_90；Schema3不迁移旧Run。
验收只覆盖定向检查与图形短流程，完整Act及Human/Formal待真人；不自动E2C/正式安装/Workshop发布。

## V1.3 QA Fix 公共恢复与精确Ancient适配

原生Ancient入场公共恢复分别使用凛、Archer自己的MaxHP与缺失生命；WearyTraveler比例保持原生80%，同一房间不重复领取。此条修复历史只恢复凛的遗漏，明确指定成员的事件/奖励仍仅作用该Owner。第三幕保留原生身份/解锁/选项类别和数量；卓越斗篷单选成员承担9MaxHP代价并获得3张事件专用灵体，普通90模型/76奖励池不变。甲虫缩小未记录成员锁定，按行动时前排施加；明确LOCKED和直接指定Power目标不改。详见 reports/rin-archer-v1.3-human-qa-fix-20261010-01/REPORT.md。
