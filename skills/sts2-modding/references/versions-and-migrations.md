# Versions and migrations

来源与 commit：[sources.md](sources.md)。核对日期 2026-10-12。
教程追踪 public-beta；BaseLib 总览声明 3.1.2；Hook 顺序章明确 0.111；RitsuLib 教程未给所有例子锁库版本。不能把整个仓库统一标成已验证 v0.111 API。

## FSN snapshot — API_VERIFIED

实际根 E:/BaiduNetdiskDownload/FSN/milestone-a；引用：RinArcherCore.csproj、dependencies/RitsuLib.References.props。

| 对象 | 核对结果 |
| --- | --- |
| 游戏 release_info.json | v0.107.1 / commit 59260271；sts2.dll AssemblyVersion 0.1.0.0 不是游戏版本 |
| sts2.dll | SHA256 A1F9E653F1E28E4076558FEE1E60D218619CB7E057B887C6417F62C62C6D7A52；MVID 97f10687-c306-4798-ab75-8b9f23f34dfb |
| BaseLib | Workshop 3737335127 DLL/manifest 3.4.7（程序集 3.4.7.0） |
| RitsuLib | 0.6.6 的 compat/0.107.1 API 与 Runtime，shared Shared/Ui/Settings 也为 0.6.6.0 |
| Harmony | 游戏 0Harmony.dll 2.4.2.0，含 MethodType.Async |
| 构建 | csproj net9.0；已有项目记录 Godot 4.5.1-m.12 custom_build，本轮未重跑 Godot/游戏 |

完整身份见 [baseline.json](baseline.json)。这是编译引用快照，不承诺所有历史 runtime/candidate 相同，也不强制其他 MOD 使用此版本；运行依赖另读对应 binding/manifest。

已额外读回最新 Public Beta v0.9.3 的 INSTALL_BINDING.json、clean-install/release_info.json、库 manifest 和上述 8 个实际 DLL；均与编译引用 SHA 相同。此为本轮文件身份核对，不新增运行验收。

## Actual v0.107.1 versus tutorials — SOURCE_VERIFIED

| 关注点 | 本机 DLL | 较新教程 / 限制 |
| --- | --- | --- |
| Damage modifiers | Additive/Multiplicative 最后是 CardModel? cardSource；Cap 没有 amount 参数 | 0.108+ 加 CardPlay? 的 override 不匹配 |
| AttackCommand | FromCard(CardModel card) | 新例子 FromCard(card,cardPlay) 不能直接复制 |
| 出牌结果 | protected virtual PileType GetResultPileTypeForCardPlay；Hook.ModifyCardPlayResultPileTypeAndPosition 返回 tuple | 新 CardLocation/GetResultLocationForCardPlay 不适用 |
| 额外播放 | 已有 GeneratePlayCount、MoveToResultPileWithoutPlaying | 迁移表称 0.111 新增，本机反例优先 |
| 出牌结束 | OnPlayWrapper 只在 IsInProgress 时调 AfterCardPlayed | 0.111 顺序不能保证结束战斗一击也发此 Hook |
| 动画 | GenerateAnimator(MegaSprite controller) | 0.111 Creature 参数/AnimationStates 重构未本机验证 |
| 事件战斗 | BeginEvent(Player,bool)、GenerateInternalCombatState/ResetInternalCombatState 存在 | 0.108+ EventCombatSynchronizer 只是迁移线索 |
| RNG | uint Seed；int Counter；Rng(uint,int) | 0.109+ ulong/Counter 移除不适用 |
| BaseLib 卡图 | CustomCardModel 扩展点 CustomPortraitPath | 3.1.2 教程 PortraitPath override 与 3.4.7 实际类有差异 |

方法体证据：研究缓存 actual-api 下同名 decompiled 文件，见 sources；绑定 baseline.json 游戏 SHA/MVID。此表是 2026-10-12 的旧版核对范围；新版补充证据见下一节，不能将补充范围外的教程一并提升。

## Actual 0.111.0 migration — SOURCE_VERIFIED / scoped RUNTIME_VERIFIED

适用：0.107.1 / 59260271 → 0.111.0 / 41cef1ea。新 sts2.dll SHA 0861BFA1DF347538D932F22D580E75420F08082792EB914E53B4882764ACDBE9，MVID 73b63ee0-6c0a-47bb-b0d1-b21f6d94222e；BaseLib 3.4.7、RitsuLib 0.6.7（各自 compat）。不是任意同 semver 构建均兼容。

- Hook.BeforeTurnEnd / AfterTurnEnd 改为 BeforeSideTurnEnd / AfterSideTurnEnd；模型本身的 BeforeSideTurnEnd 不应重复改名。读取实际 CombatManager 调用顺序后移动旧逻辑。
- CreatureCmd.Damage 完整重载增加 CardPlay；保留明确的 dealer 与实际 CardPlay。新的便利重载会从 cardSource.Owner.Creature 推导 dealer，共享 Player 的 MOD 不能直接用它替换原有成员来源。作用域须带进 async continuation，预览 / 非出牌伤害不伪造 CardPlay。
- CardPileCmd.Add(IEnumerable<CardModel>,CardPile,...) 增加 isChangingOwners；检查全部 patch / MoveNext transpiler 目标，别只修直接调用。PotionFactory 的私有 CreateRandomPotion 更名为 CreateRandomPotions，GetPotionOptions 的 blacklist 参数已移除。
- CardCreationOptions 移除直接卡列表构造；以对应原池 + 原候选 ID filter 表达原语义。NControllerManager.IsUsingController 改为 IsUsingDirectionalNavigation，需保留鼠标释放焦点与方向导航分支。
- 原版模型 Hook / 类型也可能改变：DiamondDiademPower 已移除，新 Diamond Diadem 是首回合 20 Block + 1 Blur；不能只换程序集哈希或跳过缺失依赖。Bone Tea / Fiddle / Hand Drill / Pendulum / Pollinous Core / Toasty Mittens 的 Hook 变更需按当前效果保留作用域。新语义仍用原生命令、条件与数量。

依据：FSN `reports/game-v0111-compat-20261013-01/actual-api/0.111.0` 的定向反编译、model-hook-delta.json、build/source/Compatibility/GameApi.cs 与 GameBuildCompatibility.cs。两版最终双版本包各 42 项真实首战 / 事件 / 磁盘存读档检查，构建身份见同目录 VALIDATION.json、SOURCE_BINDING.json。API / 源码差异已核实；每个改名遗物分支并非均实际触发。Android、联机、物理手柄、跨版本 Run 导入未验证。验证日期：2026-10-13。

## Migration map — TUTORIAL; verify destination

- 0.103→0.105：manifest min_game_version/dependencies；PlayerChoiceContext、creator、scope；能量计数器粒子节点。
- 0.105→0.107：HpLossHookPhase、回合末 participants、source/clonedBy、ActModel abstract 成员、Power given additive/multiplicative。Hook 与 AbstractModel 不总同名。
- 0.107→0.109：目标/CardLocation、RNG、Owner 复制、choice context、事件战斗、CardCreationOptions 要一起看。
- 0.109→0.111：CombatId 约束异步战斗归属；输入/lobby 拆分、handshake/error、动画/回合末重构。不要硬编码网络枚举数字。
- BaseLib→RitsuLib：注册属性、基类、AssetProfile、关键词、角色/初始池、事件 option/page key 均需映射；ID 从 namespace 前缀变 ModId_Category 格式。模型/存档/牌组/奖励引用一起考虑。迁移章与内容章冲突时取实际目标库。
- FSN 的 BaseLib 内容 + Ritsu 工具并存是现有架构，不自动迁移。别复制 Version="*" 拉新依赖，复用锁定引用。
