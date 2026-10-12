---
name: sts2-modding
description: Develop, review, debug, or migrate Slay the Spire 2 (STS2 / 杀戮尖塔2) MODs in C# and Godot with version-matched Harmony, BaseLib, and RitsuLib APIs. Use for cards, relics, powers, events, characters, targeting, saves, UI, animation, and runtime faults; retain reusable evidence-backed lessons after each task. Excludes STS1 and unrelated Godot work.
---

# STS2 MOD development

理解 → 修改 → 必要测试 → 交付。先复用项目已工作的实现与证据；只读当前问题需要的参考，不全量审计、不重复全套测试、不建立额外门禁。用户授权范围和项目 AGENTS 优先；Skill 不授予安装、发布、迁移玩家存档或推进里程碑的权限。

## Work

1. 读实际工程入口与相关源码，区分独立 MOD、当前 candidate 和正式安装。查项目引用、运行依赖与实际游戏版本；不要把下面的 FSN 快照视为所有项目的默认版本。
2. 针对任务选择参考。教程是线索；版本冲突按实际 DLL 的元数据/定向反编译、对应项目源码和同版本运行证据处理。无需每次下载仓库或重新反编译全游戏。
3. 优先模型 Hook、原生命令与既有库扩展；需要 patch 时选最小作用点。保留 Owner、真实实例、RNG、取消/重试与生命周期语义。修改已批准内容，不凭教程示例扩展玩法。
4. 用必要编译、定向行为检查或隔离运行验证变化；UI/动画要看真实显示与操作，存档要读回恢复结果。静态验证、工程运行验证、人类验收分别报告。已有检查通过后，只有新变化或未解决风险才扩大测试。
5. **每次 STS2 任务结束、最终交付前，自动做一次轻量经验提炼**，按 [learning.md](references/learning.md) 更新有价值的新知识；无新增则不写文件。持续学习由任务内指令执行，无后台轮询或定时任务。

## Read only what is needed

| 问题 | 参考 |
| --- | --- |
| 游戏/库版本、签名编译失败、升级或库迁移 | [versions-and-migrations.md](references/versions-and-migrations.md) |
| Harmony、async patch、Hook 顺序、触发遗漏或重复 | [patches-and-hooks.md](references/patches-and-hooks.md) |
| 卡牌、遗物、Power、事件、角色、怪物、注册/本地化 | [content.md](references/content.md) |
| 目标/Owner、预览、取消、初始化和运行生命周期 | [targeting-and-lifecycle.md](references/targeting-and-lifecycle.md) |
| 持久化、奖励恢复、牌堆、RNG、联机 | [saves-rewards-network.md](references/saves-rewards-network.md) |
| UI、场景转换、动画、VFX、材质和音频 | [ui-animation-assets.md](references/ui-animation-assets.md) |
| 调试、加载/打包、必要测试 | [debugging.md](references/debugging.md) |
| FSN 特有引擎、路径、可复用实战记录 | [fsn-practice.md](references/fsn-practice.md) |
| FSN 最终归档、无原目录恢复与维护状态 | [final-archive-recovery.md](references/final-archive-recovery.md) |
| 来源、教程 commit、完整独立章节索引 | [sources.md](references/sources.md) |
| 提炼经验、证据格式、去重和控制体积 | [learning.md](references/learning.md) |

参考按具体结论标记验证状态；TUTORIAL 不等于本机可用，API_VERIFIED / SOURCE_VERIFIED 不等于运行通过。程序集身份在 [baseline.json](references/baseline.json)。版本变化只复核任务相关签名/语义；项目已有兼容合同仍按项目规则执行。
