# RC01 安装与验收入口 / Installation

本机双击 `启动-Workshop-Beta-RC01.cmd`，使用独立游戏目录和独立 Profile。正式 Steam、历史 Candidate 和用户存档不被覆盖。已有游戏正在运行时，入口会拒绝同时启动。

`package/mods/RinArcherCore` 是 MOD 安装候选；ZIP 内路径同样从 `mods/` 开始。仅包含本 MOD 的 DLL、manifest、角色 PCK、实际引用的图片/音效和本地化文本。它不是原版游戏，也不含依赖或测试 MOD。不要将整份 `runtime-*` 目录上传到 Workshop。

依赖：BaseLib 3.4.7+、RitsuLib 0.6.6+。本次验证版本为 STS2 v0.107.1、BaseLib 3.4.7、RitsuLib 0.6.6（0.107.1 API）。后续游戏更新可能要求重新适配；manifest 的最低版本不表示未来所有版本均已测试。普通 MOD 安装不需要 QA 参数即可启用完整地图。

只有一个 MOD，简体中文与 English 跟随游戏语言，其他语言回退 English。保留 Card ID、原生 Player Owner 和存档 Schema3；新增商店无色库存及永久成员归属记录，以及原生被盗卡牌返还奖励的可选归属字段。历史玩法版本存档仍应使用其原 Candidate，不强制迁移。

选人 Remix 使用外部本地引用：环境变量 `FSN_CONTRACT_SELECT_BGM` 可指定本机 OGG；独立入口已指向用户提供的文件。文件缺失或没有设置时回退原生 BGM。该 OGG 不在安装包中。不要将它复制进公开包。

正式安装/Workshop 上传仍待用户批准；本轮不自动写入正式 Steam mods 目录。

Double-click the local RC launcher for isolated human review. The mod-only installation candidate is `package/mods/RinArcherCore`; do not upload the isolated game runtime or QA folders. Install BaseLib and RitsuLib separately. The tested game version is v0.107.1; compatibility with later updates is not implied.

One mod supports Simplified Chinese and English automatically. Optional local selection music is supplied through `FSN_CONTRACT_SELECT_BGM`; without a readable file, native music is used. No Remix audio is distributed. Installation into the live Steam directory and Workshop upload require the user's release approval.
