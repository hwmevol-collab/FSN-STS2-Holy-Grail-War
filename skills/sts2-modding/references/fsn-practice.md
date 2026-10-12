# FSN practical lessons

适用：E:/BaiduNetdiskDownload/FSN/milestone-a 的 RinArcherCore；父目录旧 FateStayNight（士郎/Saber）独立。验证日期 2026-10-12。本文件只存可复用技术；即时 candidate/human QA 状态仍从项目 AGENTS/CURRENT_STATE/PROJECT_STATE 读取，不在 Skill 维护第二份项目状态。

## Reuse before designing a second system — SOURCE_VERIFIED

工程入口：AGENTS.md → PROJECT_CONTEXT/CURRENT_STATE/DESIGN_BIBLE/DECISIONS/ACCEPTANCE_INDEX/KNOWN_DEBTS → 任务相关报告；机器路径集中 project-memory/locations.json。
既有 Global Contract Engine：ContractRuntime、CardBanks、Targeting、ContractSave、DualReward 与 compatibility registry。共享 Player 与独立成员/永久 Deck/Bank/HP 的边界是实现合同。未来 Contract 用 capability/config/adapters，不 clone 第二套。
依据：milestone-a/PROJECT_CONTEXT.md、DESIGN_BIBLE.md，Runtime/Targeting.cs、ContractSave.cs、CardBanks.cs；这是项目约定，不要求所有 STS2 MOD 都双角色。

## Display targeting without changing play semantics — SOURCE_VERIFIED

症状：共享 Player 导致 Self 高亮了错误成员；修显示不应更改牌的实际 TargetType/提交目标。
做法：CardTargetPreview.TryResolve 按真实内容Owner/受益成员给 UI recipients；保留实际 legality。等待显式选择的牌先无固定 preview。NTargetManager 的 nodeFilter 与 IsValidTarget 一致，mouse/controller 都复用。
依据：milestone-a/UI/CardTargetPreview.cs（TryResolve、ContractMultiTargetPreviewHook、ContractSingleTargetPreviewHook），Runtime/Targeting.cs；历史高亮运行证据需按 ACCEPTANCE_INDEX 读取，本轮只查源码。

## Reentered nodes can retain canceled tokens — SOURCE_VERIFIED

症状：Archer visuals reparent 导致退出/重入 SceneTree；原生 reticle readonly CancellationToken 已取消，OnDeselect 不再清高亮。
做法：既有 ArcherPreviewClearHook 仅在有效、在树内、对应 Archer 且已取消的对象上清 Tween/reticle；不要全局忽略取消。
依据：milestone-a/UI/CardTargetPreview.cs 的 ArcherPreviewClearHook。此为窄范围修正，不能推广成通用 Godot cancel绕过；不重新执行原人类验收。

## Safe save readback instead of notification-as-success — SOURCE_VERIFIED

ContractSave.Checkpoint 使用 SaveGate 串行、合法 room checkpoint；WriteCheckpoint 保存后 LoadRunSave 并核对 native HP/gold/seed，再检查 _ritsulib sidecar SavePhase/ArcherHp。Slot.Set 记录状态，snapshot 不重建独立牌组。
依据：milestone-a/Runtime/ContractSave.cs 的 Register、Sync、WriteCheckpoint；Runtime/CardBanks.cs 的 ArcherDeck RunPersistent。玩法版本/Schema 不匹配拒绝且保留匹配旧Candidate，不未经授权迁移存档。

## Tutorial chronology can be wrong for an installed build — SOURCE_VERIFIED

教程迁移表称 GeneratePlayCount/MoveToResultPileWithoutPlaying 为 0.111 新增；本机 0.107.1 DLL 已有。先查实际程序集，不以章节发布日期推定API不存在。迁移表仍有检索价值。
依据：固定教程commit Migrations/01 与本次 actual-api/MegaCrit.Sts2.Core.Models.CardModel.decompiled.cs:2015、2089；基线 SHA/MVID 见 baseline.json。新版行为未验证，存在方法也不代表所有相关新流程相同。

## A library feature table is not an API availability test

结论：教程 Basics/03 的 dated 功能表标记 BaseLib 自定义目标为不支持；实际 BaseLib 3.4.7 包含 `BaseLib.Patches.Features.CustomTargetType`，其 `RegisterSingleTargetType`、`RegisterMultiTargetType`、`IsCustomSingleTargetType`、`IsCustomMultiTargetType` 方法已从程序集元数据读回。选择库前查实际API，不能据旧功能表给现有工程迁移库。
适用：BaseLib 3.4.7.0 / FSN v0.107.1 编译基线，DLL SHA 55863CA6ADC30A61A7544874E157A519FFE148CCF2B18025947609C4BFF813CE。
状态：API_VERIFIED（方法存在）；具体调用签名、patch行为、mouse/controller UI 尚 UNVERIFIED，不据此声称功能已运行通过。
依据：教程固定commit Basics/03（sources.md）；外部研究缓存 assembly-metadata.json 中 BaseLib 类型/方法列表；baseline.json 对应路径/MVID/SHA。
验证日期：2026-10-12。

## Combat entry and banked turn-end cards — RUNTIME_VERIFIED

结论与做法：原生 `AfterRoomEntered` 早于 `BeforeCombatStart` 的起始成员选择。个人开战效果要暂存并在选择后按该成员执行一次；不能先给固定 Player.Creature、再复制给 Active。`OnTurnEndInHandWrapper` 会先把牌移出 Hand，故冻结后备牌必须在 wrapper 入口核对真实实例、所属成员和前台 Hand，不能等 `OnTurnEndInHand` 才检查牌堆。回前台后恢复原版 wrapper。角色 Power 的共享回合生命周期与后备手牌冻结是不同边界。
适用：FSN 双成员；STS2 0.107.1 / 59260271，BaseLib 3.4.7，RitsuLib 0.6.7 compat0.107.1。
依据：独立候选 `reports/vanilla-compatibility-20261012-01/build/source/Compatibility/VanillaCombatEntry.cs`、`VanillaHandEnd.cs`；同目录 `runtime-directed-25/results.json`、`runtime-graph-final/presentation-results.json`，DLL BBDC5AEBB43BC64505BF4AF926A0F80622CFA5F7D6D9D626A3D91FA1EAB1F928（该轮构建）。铜质鳞片 / Wither / Burn / Decay 和真实 Switch、回合末已执行；未推广为全部牌分支、人类 QA、Android 或联机通过。验证日期：2026-10-12。

## Event ownership before disclosure and checkpoint — RUNTIME_VERIFIED

结论与做法：`EventModel.BeginEvent` 先赋 Owner，再调 `BeforeEventStarted`。选择角色应放在后者、原版隐藏结果生成前；在 BeginEvent 前异步等待会使 NEventRoom 看见未初始化事件。AsyncLocal 子调用中的新绑定不会自动改写父 async continuation 已捕获的旧 frame；从已持久化的 event/member key 解析当前选择。非战斗 Archer 的 HP/Deck 必须在原版 `OnEventStateChanged` 存档前同步；完成事件用稳定 room key 恢复 prefinished，不能在 Continue 时再次领奖。
适用与依据：上述版本；`VanillaExpandedAdapters.cs`、`GenericScopeHooks.cs`、`FullActEventBridge.cs`。上述 graphic 证据含真实 AbyssalBaths Archer 分支及两次磁盘 Save-Continue，范围是已完成事件；多页事件中途恢复不据此宣称通过。验证日期：2026-10-12。

## Patch small selector wrappers before model detours — RUNTIME_VERIFIED

结论与做法：为模型 async MoveNext 安装 detour 时可能触发 JIT，极小原生命令 wrapper 会被内联。事后提高 Harmony Priority 或查看 GetPatchInfo 并不能证明调用会走 patch。先安装卡牌选择 / 永久牌堆识别等小 wrapper 的 patch，再安装模型 detour；以实际 Archer 候选实例验证。只处理带 HarmonyPatch 的类，不能把辅助类的普通 `Prepare` 误当 patch lifecycle。
适用与依据：上述版本；`Entry.cs`、`VanillaDeckGenericSelection`。directed-25 实际 Dolly's Mirror 在双牌组选择中选取、复制 Archer，唯一 InstanceId 与序列化通过；这不是所有 JIT / 库版本的普遍顺序要求。验证日期：2026-10-12。

## Custom permanent pile semantics and native death prevention — RUNTIME_VERIFIED

结论与做法：原版比较 `PileType.Deck` 或调用 `CardPile.IsCombatPile` 不自动认识注册的 Archer 永久牌堆；在已知银行类型处做精确原版 Deck 别名，保留真实牌堆，不全局改枚举。附魔选择的 validation lambda 可能在 async MoveNext 之外，需检查实际 IL。变牌保留原卡成员 / InstanceId，复制生成新 InstanceId。另：`AfterDeath(wasRemovalPrevented:true)` 可在 HP=0、`AfterPreventingDeath` 恢复 HP 前触发，不能此时判双角色契约败北。
适用与依据：上述版本；`VanillaTransformOwner.cs`、`VanillaEnchantmentSelection.cs`、`Compatibility/RuntimeHooks.cs` 的死亡 Hook。directed-25 实际 WoodCarvings Archer 附魔 / 固定变牌及 Lizard Tail Archer 死亡预防通过。随机变牌、其他死亡预防及中途恢复须各自验证，不能由这几项外推。验证日期：2026-10-12。

随机变牌补充：`CardSelectCmd.FromDeckForTransformation` 独立读取原生 Deck，不能只修 FromDeckGeneric；对其 async body 的候选 Cards getter 接入真实永久实例 union，保留原版变牌 UI / prefs。共享 Contract pool 会含两成员的牌；`CardFactory.GetDefaultTransformationOptions` 对原角色牌只使用原卡成员的已有池，并继续执行原版排除原 ID、稀有度、战斗和多人过滤。`runtime-directed-33/results.json`（DLL A4CFF4A286C480372CA1F2846F756AB7F5AFA63528578E5DACC0FCB85A47CCBE）实际 Aroma of Chaos、New Leaf、Astrolabe 三卡升级已通过；不由此推导所有变牌来源通过。测试手动设置 Event.Owner 时还须按原生初始化其 per-event Rng，否则随机分支会因未初始化夹具失败，不能把它误判为适配错误。

## One package, native assembly scan and shared resource root — RUNTIME_VERIFIED

结论与做法：复用 STS2-Template（MIT，commit 767e7be8c1f7d7a0d51e261e1147023d852ab881）的 initializer forwarding / GameAssemblyRegistration。壳的 AssemblyName 加 `.Loader`，文件仍用 MOD ID；内容程序集使用原名，避免 ALC 身份撞名。0.111 调 `ModManager.AssociateAssemblyWithMod`；0.107 的 `Mod.assembly` 会在初始化器返回后被 TryLoadMod 覆盖，需在 OnModDetected 再设内容程序集。只反射隔离旧字段，不能仅登记 RitsuLib 并假定游戏模型扫描也成功。
FSN 严格合同：按完整 version / commit / SHA / MVID 精确选择，拒绝未知身份，无模板的最高目标回退；内容 DLL 另核 SHA。共享图片、音乐、PCK、本地化取包根，不能再取 `lib/<版本>` 下的内容 DLL 目录。单版目录保持原路径。Android 的 ReleaseInfoPath / DataDir 回退及 runtime/file MVID 一致性检查保留，不由桌面双版测试推断 Android 通过。
依据：`reports/game-v0111-compat-20261013-01/build/loader`、ContentPaths.cs、runtime-111-graph-dual-02 / runtime-107-graph-dual-01 的 presentation-results.json。每版 42 项实际流程、21 项分流负向检查；源码 / DLL 绑定见该目录 SOURCE_BINDING.json。仅对应已验证构建与此包布局；人类、完整 Run、联机、Android 未验证。验证日期：2026-10-13。

## Native visual writes can invalidate a model-only skin cache — RUNTIME_VERIFIED

v0.111.0 / 41cef1ea 的 `NCard.UpdateVisuals` 新增 `UpdatePortrait()`，每次重写横幅/插画框 Texture 与 Material；0.107.1 的同方法无此调用。模型实例/语言/稀有度相同不代表节点属性未变。FSN 将 TitleBanner / PortraitBorder 的 Texture、Material=null、SelfModulate=White 恢复放在 `PresentationCardSkin.Apply` 缓存提前返回前，位置/尺寸仍在原布局缓存分支，纹理沿用 PresentationTheme 资源缓存；不要每次 invalidation / Reload 全部皮肤。
依据：原诊断 `analysis/beta-android-diagnosis-20261013/DIAGNOSIS.txt` 与 111-NCard.cs；修复 `reports/game-visual-loader-fix-20261013-01/build/source/UI/PresentationTheme.cs:114-137`。同目录 runtime-111-graph-dual-02、runtime-107-graph-dual-01 的 presentation-results.json 各 191 项断言 PASS（含启动流程及重复实例断言）：代表牌 48 次 UpdateVisuals 后缓存状态/纹理实例/布局稳定，双方原生牌库升级预览、手牌悬停及 Switch 后纹理/材质正确，截图抽查通过。范围是这两个已验证 Windows 构建；不代表全部卡牌、完整 Run、人类或 Android 验收。验证日期 2026-10-13。

## A bootstrap loader must resolve relative Android Assembly.Location — Windows simulation verified; Android PENDING

Loader 的初始化先于内容 DLL，后者路径修复不能补救壳读取裸名 `sts2.dll`。按现有内容 gate 的规则：存在的绝对 Location 直接使用；空值、相对或不存在 Location 回退到有效绝对 `AppPaths.DataDir/.godot/mono/publish/arm64/sts2.dll`，不按 cwd 解析，也不因裸名文件在 cwd 存在而信任它。记录最终打开路径；缺失/无效 DataDir 和缺失 publish DLL 失败关闭。保留程序集名、运行/文件 MVID、完整 version/commit/SHA 元组与内容 DLL 哈希校验，不能只看版本字符串。
依据：原诊断 `analysis/beta-android-diagnosis-20261013` 的 Android sts2.log/godot.log；修复 `reports/game-visual-loader-fix-20261013-01/build/loader/WorkshopBootstrap.cs:36-62`。上述双版本图形 QA 在 Windows 用 QA-only AppPaths 和 game Assembly.Location getter patch **实际调用 Actual**：空/裸名/存在相对文件/失效绝对路径回退、有效绝对路径优先、无效 DataDir/缺失文件拒绝、另一 sts2 MVID/错误程序集/同 MVID 改 SHA 拒绝；Initialize 拒绝篡改内容副本。仅这些分支 RUNTIME_VERIFIED，模拟不覆盖 Android loader/文件系统/运行平台；Android 真机修复回读保持 PENDING。验证日期 2026-10-13。
