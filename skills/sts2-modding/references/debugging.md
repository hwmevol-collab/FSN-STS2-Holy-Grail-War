# Debugging, loading, and necessary validation

来源：Basics 01/02/07/08/09/10/11；Ritsu Utilities 03/04/05/09；[索引](sources.md)。日期 2026-10-12；IDE hot-reload 与新版开发工具默认 TUTORIAL/未本机执行。

## Diagnose the actual loaded build

先读本次错误与加载身份，查 manifest、initializer、DLL、资源路径、使用的 profile。compile DLL 不等于 game 已加载，菜单显示模型不等于真实 Run 是该角色；不要拿历史 candidate 的 PASS 证明新二进制。
搜索定位：中文名 → localization key/model ID → 模型/命令/Hook/调用方。已有反编译/atlas 与当前 DLL 身份一致时复用；不一致只反编译所需类型。异常优先首个因果错误，别只修后续 NullReference。
ModInitializer 初始化唯一 patch/register scope，Godot C# script lookup 与资源PCK加载分别确认。manifest ID 与 DLL/PCK 同名约定/min_game_version/dependencies/affects_gameplay 以实际loader为准。

## Minimal diagnostic tools

- 原生 console：help 与 help command 核对本版本；card/power/relic/potion/enchant、damage/block/heal、room 等仅在隔离QA场景使用；console 的 index 不是自定义双成员角色 ID。
- 日志包含 run seed、act/room、card instance/owner、selected recipient、phase、真实金额前后与 cancellation；只在问题路径增日志，不 dump 整存档/账号/全量素材。
- Harmony.GetPatchInfo/patch dump 看目标和竞争 owner；TargetMethod 未找到时看 exactsignature/assembly/namespace，再查教程版本，别盲目刷新哈希。
- Debug portable PDB、Optimize=false、正确 source mapping；IDE hot reload 只适合支持的代码编辑，不保证类型结构/patch 注册改变生效；PCK 不能靠同一机制热重载，必要时重启隔离 runtime。
- --log/--log-file、--force-steam=off、--fastmp/--clientId、--autoslay/--bootstrap 是教程入口；实际 parser/release gating 验证后用。autoslay/bootstrap 并非所有 release 默认可用，不为一次诊断永久关闭 release gate。
- 本机使用 .tools/dotnet；ILSpy 若找不到运行时，指向已有 DOTNET_ROOT，必要 roll-forward 只改当前命令进程，不更改全局配置或升级工具。

## Test what changed

模型变化：compile/定向测试，必要原生短流程。UI变化：真实显示+输入/取消。存档变化：隔离profile合法 checkpoint save/load 与 readback。动画：实际播放/中断/退出和资源缺失。联机变化：host/client 实际同步，单机不能代替。
工程验收、完整Run、人类复测、平衡是不同范围。测试通过后交付；不因 Skill 增加全量审计、重复测试或发布流程。已有项目的明确回归约定仍遵守。
无关 MOD、正式安装、原 saves/logs、旧候选保持原样；需要安装/发布依据当前授权，教程的 build 自动复制target不是本地项目默认许可。

## Adjacent utilities — TUTORIAL, task-scoped

Runtime hotkeys 应尊重文本框/console 焦点，register handle 配对释放。Update checker 是通知/链接，非自动下载安装；版本manifest失败保持可玩，不掩盖真实错误。
Telemetry 是可选且需用户/玩家授权，明确类别和用途；未经批准不要引入服务或上传日志。库 consent/queue 不能绕过；只发短字段/受控payload。远端额度/价目/部署信息不存成长期事实；日常调试优先本地日志。
Workshop 章已研究：uploader Content/workspace与 preview/dependencies/visibility 的区别。仅当任务明确授权发布时再查当前官方 uploader 文档，避免旧CLI/字段覆写；本轮 Skill 创建不发布。
