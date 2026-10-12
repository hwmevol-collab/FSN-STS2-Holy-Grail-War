# FSN × Slay the Spire 2 — Holy Grail War

**暂停开发与维护，无恢复更新计划或时间表。Windows only. Development and maintenance are on hiatus with no planned update schedule. Android is unsupported.**

An unofficial, completely free Fate/stay night fan MOD. Rin Tohsaka and Archer form one Master–Servant Contract, with separate HP, Block, statuses, hands and permanent decks; shared Energy/Mana/Jewels; switching and banked Reserve hands. Rin-focused, Archer-focused and cooperative builds remain playable. Other Master–Servant teams and the complete Holy Grail War are unfinished concepts.

非官方、完全免费的同人 MOD。当前可玩的是 Rin / Archer 双角色契约，支持凛单核、Archer 单核与协同构筑。其他契约与完整圣杯战争仍未完成。

- Workshop: https://steamcommunity.com/sharedfiles/filedetails/?id=3818087982
- Final candidate: **0.9.4-game-compat.1-visual-loader-fix-01-dual**; internal informational version **0.9.4-game-compat.1**.
- Windows game builds: **v0.107.1 / 59260271** and **v0.111.0 / 41cef1ea**. Complete SHA-256/MVID identities are in [verified-games.json](verified-games.json). Unknown builds are rejected.
- Dependencies: **BaseLib 3.4.7**, **RitsuLib 0.6.7 complete multi-version package** (matching compat directories and shared). Game/dependency binaries are not in Git.
- [Final state](CURRENT_STATE.md) · [Recovery handoff](FINAL_HANDOFF.md) · [Design bible](docs/project/DESIGN_BIBLE.md) · [Historical packages](docs/HISTORICAL_RELEASES.json)

## Install / 安装

Subscribe to the Workshop item and its [BaseLib](https://steamcommunity.com/sharedfiles/filedetails/?id=3737335127) and [RitsuLib](https://steamcommunity.com/sharedfiles/filedetails/?id=3747602295) dependencies, enable the MOD, then restart. Or download the final Release ZIP and put its complete mods/RinArcherCore folder in an isolated game copy's mods directory. Keep lib/0.107.1, lib/0.111.0, mod-variants.manifest and shared resources together. Do not enable another RinArcherCore copy simultaneously. Back up your own saves before updates; cross-version Run imports are not verified.

订阅工坊及前置依赖后启用并重启游戏；手动安装需完整保留子目录。不要同时启用两份 RinArcherCore。存档请自行备份，跨游戏版本导入 Run 未验证。

## Build / 编译

Install .NET SDK 9. Supply legally obtained, version-matched game and dependency directories:

```powershell
./tools/Build.ps1 -Game107 'X:/Games/STS2-107' -Game111 'X:/Games/STS2-111' -BaseLibDll 'X:/Mods/BaseLib/BaseLib.dll' -RitsuRoot 'X:/Mods/STS2-RitsuLib' -Dotnet dotnet
./tools/Package.ps1 -ResourcesZip 'X:/Downloads/FSN-RinArcher-0.9.4-game-compat.1-visual-loader-fix-01-dual.zip'
```

Artifacts go to artifacts/; no game installation, save migration or Workshop publication occurs. [FINAL_HANDOFF.md](FINAL_HANDOFF.md) explains restored paths, Matrix resources and payload hashes. Binary art libraries and original-game assets are excluded from Git; see [ASSET_REQUIREMENTS.json](ASSET_REQUIREMENTS.json), Godot source snapshots and release/shared-resource requirements. The private archive retains the original project and source material layout.

## Architecture / 架构

src/Runtime: ContractRuntime, CardBanks, targeting, economy/rewards and saves. src/Compatibility: registry/Matrix, native adapters and ownership/lifecycle bridges. src/Content: cards/characters/gameplay models. src/UI: native UI extensions, textures, typography and animations. loader/: exact game identity selection, payload verification, initializer forwarding and native assembly registration, adapted from STS2-Template. history/: superseded code snapshots. tools/: original research/build/capture tools. docs/project/: historical project decisions and scoped acceptance evidence. godot/: scene/script sources; assets retain their original rights.

## Known limits / 已知问题

Selected vanilla events/relics/status effects were adapted, including Bronze Scales and Wither ownership fixes; **full vanilla compatibility is not claimed**. Final scoped visual/path tests passed on the two exact Windows builds. Continuous verification of a complete natural Run remains partial, and human gameplay/balance acceptance is pending. Multiplayer, physical-controller coverage and cross-version save import are not verified. Some assets/effects are reused, and presentation/balance remain unfinished. **Unofficial Android ports are no longer supported; the dual Loader still has actual startup faults and may not load. No mobile fixes are planned.** Historical builds are test/superseded candidates, not supported substitutes.

部分原版内容有定向适配，不代表全原版内容完全兼容。完整自然 Run 证据仍有缺口；真人、平衡、联机和物理手柄验收未完成。Android 已停止支持，实际启动故障未继续修复。历史候选的已知故障见 Releases 与原报告。

## Rights, licenses and contact / 权利、许可与联系

This is a completely free, non-commercial, unofficial fan project, not authorized, endorsed or sponsored by TYPE-MOON, Mega Crit or any original rights holder. Fate characters, story, original art/CG, logos, FUC models, music and other third-party material remain the property of their respective owners. Existing third-party licenses and attribution are retained (including loader/STS2-Template.LICENSE and THIRD_PARTY_NOTICES.txt). The THIS ILLUSION remix's precise arranger/source attribution remains unconfirmed. No new license is assigned to material that the author does not own.

No repository-wide license was found for the author's original MOD code. Publishing source for community reference does **not** establish a new permission grant; consult the original per-file terms or contact the author before relying on unlicensed code. This archive does not silently relabel the project MIT or license the original assets as open source.

本项目非官方、完全免费，不代表任何原权利人授权、背书或赞助。原作素材与第三方内容权利归原权利人；保留已有许可证和署名。未发现原创 MOD 代码的统一许可，公开源码不等同于新增授权条款；不擅自把原作素材授予开源许可。版权或素材删改请求请通过 [Workshop 评论／讨论区](https://steamcommunity.com/sharedfiles/filedetails/?id=3818087982) 联系作者 Murasame / Slpeey；暂停维护期间不保证回复时限。Contact the author through that Workshop page for copyright concerns and removal/correction requests.
