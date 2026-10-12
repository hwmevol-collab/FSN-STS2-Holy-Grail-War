# Rin / Archer V1.3 实施与工程验收

2026-10-10｜ENGINEERING PASS（定向与图形短流程）；Human QA / Formal Closeout PENDING；E2C NOT_STARTED。

## 交付

- 双击：[V1.3 新Run入口](../../Launch-V13-Playtest.cmd)。独立Runtime、Build、Profile已创建，试玩目录只包含BaseLib、RitsuLib、RinArcherCore，未带测试插件。
- GameplayRevision：`RIN_ARCHER_GAMEPLAY_V1_3`；CardPoolRevision：`RIN_ARCHER_CARD_POOL_V1_3_90`；Candidate：`RIN_ARCHER_GAMEPLAY_V1_3_CANDIDATE_01`（0.7.0-v13-candidate）。
- [试玩DLL](runtime-manual/mods/RinArcherCore/RinArcherCore.dll) SHA-256：`0BBB5A1FBC4E7C6BD95C339D6870C33DDBC0C2A364A566B80A66B7FE505BEC5E`。
- 基础身份已实核：V1.2 QA Fix `986E449D11DF778BB72BC40BDD64A8FD97488D098C74F9C5946B61B7C4C49A56`；原生0.107.1 / commit59260271 / build23811903，Matrix04保持。

## 已实施

90模型 = 11起始模型 + 76正常奖励牌 + 3投影兵装。新增36张奖励牌（每成员18张），双方正常池均38张（13普通/15罕见/10稀有）。全部普通/升级费用、中文描述、悬浮提示、模型注册及奖励资格已核对。双方各10张起始实例、弓箭射击×2与投影×2保留。

强化投影：0能量、2→1契约魔力；自用待命使下一张凛直接伤害/自身格挡总额+8→12，或强化下一件成功生成的兵装，仍可选择原有宝石折扣。两种模式互斥，兵装生成优先消费该待命，再消费U10。
掩护：自用10→14格挡并抽1张弓兵牌，或凛7→10格挡并整理1→2张凛手牌。
投影：生成兵装后抽1张弓兵牌，获得1→2契约魔力；升级保留兵装魔力折扣。

指定5项平衡限次已放开：供魔两分支、C13共享额度、Hand Tuning成员额度、C16同实例回合锁、重复Power补偿回合锁。
新增能力覆盖凛资源/宝石/状态体系、弓兵投影复制/回收/免耗/命中返能、后备状态与生命代价、累计兵装终端及指数强化。
同名能力保持最高等级单引擎；新的手动重复副本逐次抽1，原生重放与重复Hook不生成额外引擎或重复付款。

## 明确采用的局部解释

1. 状态转移只支持虚弱、易伤、脆弱、中毒。原生Power的Owner不可重绑，故使用同类型真实原生能力迁移，保留来源、层数、计时标志和回合起始量。目标已有同类但来源/计时不兼容时不转移；免疫拒绝时保留原状态且不发奖励。
2. 凛的自动转移先经过原生实际施加/免疫，再只移动本次新增层数；不绕过原生钩子，也不把转移再次识别为敌方施加。
3. 正常打出兵装才触发生成/返魔能力，幻想崩坏只增加成功消耗累计。保留原ARM_RESOLVED不同种类集合，另外用总次数记录重复使用；连环幻想崩坏按消耗本次材料前的累计计算伤害。
4. 投影连锁升级生成的两件其他兵装类别互异；无限投影的三件可重复类别。满手牌时停止生成，先检查空间再动原生生成RNG；不会自动打出生成牌。
5. 普通多敌环境没有契约“前排”，护卫反击从合法敌人中用原生目标RNG选择；其固定能力伤害不套攻击力量/虚弱，也不再次记为主动攻击命中。
6. 指数倍率、兵装累计与能量欠账用宽整数，不加平衡上限。直接伤害/格挡在原生力量、虚弱等修正前分配整牌加成；最终仅按核实的原生999999999边界饱和。能量与累计伤害统计分别按其Int32边界保护，并保留数值边界提示。
7. 借来的能量代价在下一共享回合基础能量/额外能量之后扣除，最低0，合并欠账消费一次。生命代价不能以格挡抵扣，也不能主动付至死亡；普通承伤/中毒导致任一成员死亡仍失败。

数值均按输入JSON实施；上述解释不覆盖LOCKED合同。新牌升级文本改写为完整效果，去掉“实例”等内部术语，不以设计稿中的差分句替代玩家描述。

## 验证

冻结源独立编译：0错误、0警告；122个已知构建源文件与开发源读回一致，实际改动13个生产文件。

| 范围 | 结果 | 证据 |
|---|---:|---|
| 90_MODELS_EFFECTS_RESOURCES_LOOPS | 1198/1198 PASS | [runtime-directed-final-04结果](runtime-directed-final-04/v13-results.json) |
| RIN_SOLO_NATIVE_GRAPH | 479/479 PASS | [runtime-graph-rin-final结果](runtime-graph-rin-final/v13-results.json) |
| ARCHER_SOLO_MULTI_ENEMY_NATIVE_GRAPH | 114/114 PASS | [runtime-graph-archer-final结果](runtime-graph-archer-final/v13-results.json) |
| LEGAL_NATIVE_DISK_CONTINUE | 4/4 PASS | [runtime-continue-final结果](runtime-continue-final/v13-results.json) |
| 无测试插件的独立图形Runtime | PASS，主菜单加载且响应，三生产MOD，正常关闭 | [启动证据](manual-runtime-startup.json) |
| 正式Steam、历史DLL及原试玩存档 | 5项关键身份未变 | [保护读回](critical-protection.json) |

定向覆盖：36新牌普通/升级真实效果路径；同一真实卡配合原生抽牌遗物主动循环40次；36次实际宝石强化越过原生格挡边界且倍率继续成长；取消、重复Power、IA、强化优先级、10手牌、真实后备抽弃、原生重放一次付款、负面状态转移/免疫/时钟、生命支付、死亡失败、商店/Boss预算、Smith及新ID序列化。原生可打出的状态牌也能触发弓兵零魔力能力。

图形验证使用非TestMode原生Embark、战斗、出牌行动、选择窗口、End Turn、Switch、奖励和合法保存/Continue。凛/弓兵分别先完成单核出牌，才选择另一成员出牌；多敌场景追加1只真实原生敌人验证非攻击技能与群体效果。费用节点回收、成员选择焦点、后备再生只结算一次及V1.2多敌技能结算缺陷均通过相关检查；Gorget精确适配等未改源码复用原验收。
这是注入临时卡牌/测试资源/安全格挡的受控短流程，部分合成鼠标输入使用已记录的原生可见按钮回调或PlayCardAction补足；未宣称自然构筑整幕、纯人工鼠标或真人验收。截图：[凛单核](runtime-graph-rin-final/v13-rin-solo.png)、[弓兵单核与双敌人](runtime-graph-archer-final/v13-archer-solo.png)、[原生Continue](runtime-continue-final/fixed-disk-continue.png)。

开发中失败的尝试保留，但未计入PASS：TestMode首次洗牌教程工厂、标准模式不支持编辑Seed、测试预期遗漏IA/原生状态牌自身抽牌/Smith预算，以及测试创建第11张手牌导致找不到持有节点。这些按原生合同修正夹具；另补齐真实边界上的累计伤害统计保护、原生状态牌触发和完整升级文案。

## 存档、状态与真人重点

Schema3独立校验Gameplay与CardPool，V1.2旧Run拒绝自动迁移，由原匹配Candidate继续。Continue只复制本轮新V1.3 QA合法检查点到新测试Profile；试玩Profile未注入该存档，首次双击用于新Run。
Project Memory新增ADR-089、V1.3能力/验收及DEBT-027，当前身份更新到PROJECT_STATE.gameplay；E2B历史身份与所有旧Acceptance保留，Human/Formal PENDING，E2C NOT_STARTED。[工程验收](ENGINEERING_ACCEPTANCE.json) / [范围内记忆检查](project-memory-check.json)。

优先真人试玩：强化投影自用/支援与U10优先级；凛指数宝石循环；弓兵投影复制/回收/免耗与返能；后备承受中毒及生命代价；状态转移被免疫/不兼容时的反馈；小卡组重复出牌及10手牌体验。完整Act、自然构筑平衡和物理手柄尚需真人确认，无已知未完成的V1.3指定卡牌功能。

## 实际耗时（UTC+8）

| 阶段 | 时间 | 墙钟耗时 |
|---|---|---:|
| 必要上下文与规格 | 06:21:21–06:27:35 | 6.2分钟 |
| 首次完整实施 | 06:27:35–06:33:26 | 5.8分钟 |
| 定向/图形验证及修复 | 06:33:26–07:16:02 | 42.6分钟 |
| 独立交付与项目记忆 | 07:16:02–07:21:37 | 5.6分钟 |

总计约60.3分钟；阶段内包含并行准备，详见[timing.json](timing.json)。仅复用必要背景和原验收，未做完整Act、数千Seed、历史3700项全量回归或全工作区哈希扫描。
完成后停止，等待真人试玩；未正式安装、发布或推进E2C。
