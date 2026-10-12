# Public Beta v0.9.3 最终打包

已完成，等待用户发布批准；未上传 Workshop。

本次仅将指定 Remix 内置到 `mods/RinArcherCore/Presentation/Audio/this-illusion-remix.ogg`。通过 MOD DLL 所在目录加载，去掉外部路径 / 环境变量依赖；沿用循环、音乐与主音量、0.35 秒淡入 / 0.18 秒淡出和页面退出恢复。用户原 OGG 未改动，复制 / ZIP / 解压后哈希一致。源文件只修改 `UI/ContractSelectMusic.cs`、`RinArcherCore.csproj`、`RinArcherCore.json`，版本为 0.9.3；编译 0 错误、0 警告。

**干净安装：PASS_SCOPED。** 最终 ZIP 解压到新 `clean-install`，新 Profile `FSNWorkshopPublicBeta-20261011/v093-clean-01`，未复制历史进度或存档，启动环境移除 `FSN_CONTRACT_SELECT_BGM`。

- 简中 / English：内置音轨播放、实际曲尾循环、原生音乐 / 主音量响应、重复选择单实例、切换铁甲战士、退出及再进入通过。两种语言均记录实际 Master 混音 PCM，非静音；实录位于 `clean-install/selection-bgm-live-eng.wav` 和 `selection-bgm-live-zhs.wav`。最终听感仍由用户确认。
- 缺失 / 损坏 OGG：只对隔离安装副本临时测试，均回退原生 BGM、不阻止选择；测试后原包字节完整恢复。
- 新 Run Seed `CBXB70TSD1`：原生地图、第一场真实战斗与奖励、双成员 HP / 资源 HUD、双永久牌组、普通 / 升级预览、原生磁盘 Save/Continue、返回稳定菜单通过。Continue 保留 HP、牌组实例 / Owner / 升级、金币、遗物、药水、地图与 RNG；进入 Run 后选人音乐停止。未重跑三幕。
- 使用隔离的原生 UI 操作器完成上述实际按钮与正常出牌检查，未改 Seed、HP、资源或房间。91 项本轮定向断言通过；操作器已移出试玩安装和发布内容，三个正式 MOD 再启动正常。原始证据见 `clean-install/presentation-results.json`、`verification-runtime.log`、`production-startup-three-mods.log`。

**包与上传目录：** `FSN-RinArcher-Public-Beta-v0.9.3.zip` 共 27 个 MOD 文件，新增一个 OGG；原有 24 个非 DLL / manifest 资源与 v0.9.2 完全相同。无原版游戏、依赖文件、测试 MOD、存档、历史 Candidate 或素材库。完整文件清单见 `FILE_MANIFEST.json`。上传内容目录是本报告同目录下 `package/mods/RinArcherCore`，不要上传整个隔离游戏目录。

**依赖：** [BaseLib 3737335127](https://steamcommunity.com/sharedfiles/filedetails/?id=3737335127)、[RitsuLib 3747602295](https://steamcommunity.com/sharedfiles/filedetails/?id=3747602295)。已核对页面身份、MOD manifest 的 BaseLib ≥3.4.7 / STS2-RitsuLib ≥0.6.6 关系及实际加载。实际测试基线：游戏 0.107.1、BaseLib 3.4.7、RitsuLib 0.6.6 的 0.107.1 API；不宣称未来版本兼容。

**发布资料：** 中英正式介绍、Steam 可粘贴文本、v0.9.3 更新说明、安装说明、素材来源、依赖 / 上传清单以及已有封面与六张实际预览，统一放入 `Workshop-Publishing-Materials-v0.9.3.zip`。预览保留原出处与版本，未冒称本次新拍美术。音轨文件标签标注「THIS ILLUSION / 芳賀敬太 / Fate/stay night Original SoundTrack」，仅作为文件元数据记录；Remix 改编者和公开来源未核实，无官方授权声明。

**保留限制：** 混合 2D/3D、复用卡图、普通演出与 UI 细节、部分原版兼容尚未完成；联机 / 完整手柄 / 全面平衡未验收。原有自然胜利、终局备份复测及完整自然终局连续证据 PARTIAL 原样保留，见上一版 `TERMINAL_EVIDENCE.md`。原作图像与音轨分发权未确认，继续如实标注免费非官方同人及 Workshop 页面反馈 / 版权联系渠道。Human QA / 上传批准 PENDING。
