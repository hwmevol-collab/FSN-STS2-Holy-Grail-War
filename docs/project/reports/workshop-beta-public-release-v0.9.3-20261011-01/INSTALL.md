# 安装 / Installation

安装包仅含 `mods/RinArcherCore`；不含原版游戏、BaseLib、RitsuLib、测试 MOD、存档；包含指定选人 OGG 音乐。

依赖：Slay the Spire 2 v0.107.1、BaseLib 3.4.7、RitsuLib 0.6.6（0.107.1 兼容分支）。已验证版本，不保证未来 API 兼容。[BaseLib](https://steamcommunity.com/sharedfiles/filedetails/?id=3737335127)、[RitsuLib](https://steamcommunity.com/sharedfiles/filedetails/?id=3747602295)、[RitsuLib 0.6.6](https://github.com/BAKAOLC/STS2-RitsuLib/releases/tag/v0.6.6)。

将 ZIP 内容解压到游戏目录，确保路径为 `mods/RinArcherCore/RinArcherCore.dll`。启用三个 MOD 后重启。不与历史 RinArcherCore 同时启用；旧存档使用匹配历史版本。一个 MOD 自动支持简中 / 英文，其他语言回退英文。

本机双击 `启动-Public-Beta-v0.9.3.cmd` 使用新隔离安装及 Profile，正式 Steam、历史 Candidate 和用户存档不被改写。原版游戏文件在本机隔离目录中使用只读用途硬链接；不会包含在发布 ZIP 中。

选人 Remix 已内置于 `Presentation/Audio/this-illusion-remix.ogg`。不需要绝对路径、环境变量或额外音乐安装；缺失 / 损坏时回退原生 BGM。请完整保留 MOD 子目录。

The ZIP contains only `mods/RinArcherCore`, including the selection Remix, with no base game, dependencies, test mod, or saves. Install the tested dependencies above, extract into the game folder, enable the mod, and restart. Use only one RinArcherCore version. The game language selects Simplified Chinese or English automatically; other languages fall back to English.

Music is loaded from the mod's bundled `Presentation/Audio/this-illusion-remix.ogg`, with no absolute path or environment-variable setup. A missing or corrupt track falls back to native music.
