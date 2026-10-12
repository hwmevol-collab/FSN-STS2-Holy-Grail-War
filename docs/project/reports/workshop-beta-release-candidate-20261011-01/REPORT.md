# Workshop Beta RC01 — v0.9.1

本轮结果：**PARTIAL / Human QA PENDING**。实际耗时约 **236 分钟**；没有上传 Workshop，正式 Steam、历史 Candidate 和用户存档未覆盖。

## 本机验收入口

- 双击 [启动-Workshop-Beta-RC01.cmd](启动-Workshop-Beta-RC01.cmd)。独立 Profile，从正常新开局开始；不含测试伴随 MOD。
- 干净安装候选：[package/mods/RinArcherCore](package/mods/RinArcherCore)；[MOD-only ZIP](FSN-RinArcher-Workshop-Beta-RC01-v0.9.1.zip)。26 个文件，约 49.7 MB，不含原版游戏、依赖、调试存档或 Remix。
- [实际截图](GALLERY.md)、[完整路线证据](NATURAL_RUN_EVIDENCE.json)、[中英 Workshop 草稿](WORKSHOP_DESCRIPTION_DRAFT.md)、[安装说明](INSTALL.md)。

## 实际修改

1. 普通安装直接启用已有原生完整地图，恢复末幕 Boss 的精确入口资格，并为 Contract 接入原生 The Architect 终局对话；保留原生 RNG、跨幕、评分、WinRun 与结算流程。
2. 商店恢复 **2 凛＋2 Archer＋随机成员第 5 张**，以及原生 Uncommon / Rare 两个无色槽位。首次生成后库存固定；购买先选择真实永久牌组，取消不扣钱，已售出槽位重复点击不发卡、不扣钱。使用原生基础价格保存库存，价格修正只应用一次。历史已经生成的四卡商店继续保留库存。
3. 无色池仅精确恢复 Finesse、Flash of Steel、Dark Shackles、Master of Strategy、Hand of Greed，仍使用原生解锁、稀有度、价格和 RNG。加入真正永久卡牌的成员元数据及战斗归属，不复制一套无色卡，不放开全部 C/D。
4. 真实 Run 遇到 Thieving Hopper 从 Archer 牌组偷牌失败，修复原生永久牌堆识别；实际偷走、击败敌人、同一张 ARC-U23 返回 Archer 已验证。新增被盗无色牌返还奖励的可选归属字段；没有改 Card ID、原生 Player Owner 或 Schema3。
5. 简中玩家术语统一为 **凛（Master） / Archer（Servant）**，通过现有本地化表维护；英文保持英文。两种语言 507 个 MOD 界面键成对；原版名称仍用原生本地化。松散本地化以 `.loc` 装载，避免原生扫描器误把语言 JSON 当 MOD manifest。

涉及 23 个生产文件，详见 [MODIFIED_FILES.json](MODIFIED_FILES.json)。Gameplay V1.3 卡牌数值、六项 E2C Adapter、美术、卡框、插画、角色 PCK 与外部 BGM 方案保持原样。

## 必要验证

**完整自然结算流程验收仍 PARTIAL；原生终局复测通过**。第五条真实新开局 Seed `9EZB3DN0FY` 已在原生历史取得 Win=true，检查脚本在点击结算按钮前退出。随后原样恢复该路线此前实际生成的原生存档备份，未修改任何字段，重新合法完成第三幕、终局、胜利，并通过原生结算返回主菜单的节点检查。后半段是明确标注的备份恢复复测，不冒充未手工恢复备份的一次完整自然流程。复测使用交付 DLL。

- 共进行 7 条自然新开局路线，6 条真实战败；第五条真实胜利但检查脚本在点击结算按钮前退出，均保留原始日志，不计为完整菜单流程 PASS。检查脚本的加载时序/恢复错误保留在 controller-attempt 目录；从同一路线的真实原生磁盘 Continue 恢复，不跳房间、不伪造击杀、不改 HP/金币/牌组、不强制换幕、不覆写 Seed。
- 原生地图、战斗、事件、商店、Rest / Smith、宝箱、奖励、双成员 HP / MaxHP、真实牌组实例与升级、遗物、药水、金币和 RNG 的 Save/Continue 比较均留有记录。
- 商店 5＋2、取消、两名成员购买、重开、已售出重复点击、磁盘 Continue 均在真实赚取金币的流程验证。中英标签及实际 1920×1080 / 1280×720 商店截图已交付。
- 中英选人、双牌组、普通/升级/复杂资源牌、战斗、奖励、事件、篝火已抽样。最终结算按当时原生场景语言检查；另从真实磁盘胜利记录进入英文历史页，1080p / 720p 无残留中文。运行中热切换不会刷新所有原生缓存文字。胜利后菜单截图捕获过早，原件为转场黑屏，保留但不作为可见菜单证据；截图集中稳定的主菜单来自另一次实际历史页检查，不冒充同一胜利后的连续画面。
- 编译 0 警告 / 0 错误；MOD-only ZIP 解压读取、依赖/版本/资源引用及独立入口预检通过。工程范围见 [ENGINEERING_CHECKS.json](ENGINEERING_CHECKS.json)，不等于真人、美术或平衡验收。

## 仍需真人确认的边界

- 六项 E2C 保留；其他未适配内容继续合法排除。本轮不扩第二批遗物/事件/药水。
- 五种无色效果未逐张自然抽样：实际本轮日志可确认 Dark Shackles / Master of Strategy；其余不虚报效果运行 PASS。折扣遗物与新商店基础价组合、被盗无色牌返还奖励后 Continue 未自然遇到。
- 联机、手柄和整体平衡未验收；单条通关不表示所有 Seed、事件或构筑都已验证。
- 首测冻结的 2D/3D 混合、部分卡图复用、普通技能演出及少量 UI 瑕疵继续列为 Beta 已知限制，不重启美术精修。
- 公开素材来源与权利状态如实见 [ASSET_AND_RELEASE_NOTES.md](ASSET_AND_RELEASE_NOTES.md)。用户接受相关风险不等于官方授权；Remix 仅本机外部引用，未入包。发布前需最终真人验收、确认 Workshop 依赖与联系渠道，并取得用户上传批准。尚缺的发布验收证据：一条不经手工备份恢复的新开局 → 正常 Save/Continue → 胜利 → 菜单流程。最短路径是在当前 RC 上由真人或修正后的自动操作完成一次；本轮已有真实 Win 和终局复测证据，但不把它们拼成自然完整流程 PASS。

完成后停止，等待用户审核。
