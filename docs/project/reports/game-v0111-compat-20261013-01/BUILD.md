# 复现构建

使用本目录 `build/source`，不要取旧快照。游戏引用须对应目标版本；RitsuLib 使用已有 `dependencies/compat/<版本>`，BaseLib 使用本轮验证的 3.4.7。

```powershell
$taskDotnet='E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe'
$taskReport='E:\BaiduNetdiskDownload\FSN\milestone-a\reports\game-v0111-compat-20261013-01'
& $taskDotnet build "$taskReport\build\source\RinArcherCore.csproj" -c Release -p:RitsuLibReferenceTarget=0.111.0 -o "$taskReport\build\candidate-111"
& $taskDotnet build "$taskReport\build\source\RinArcherCore.csproj" -c Release -p:RitsuLibReferenceTarget=0.107.1 '-p:GameDir=E:\BaiduNetdiskDownload\FSN\milestone-a\reports\vanilla-compatibility-20261012-01\runtime-graph-final-03' -o "$taskReport\build\candidate-107"
& $taskDotnet build "$taskReport\build\loader\RinArcherCore.Loader.csproj" -c Release
python "$taskReport\package.py"
```

`GAME_0107` 由 RitsuLibReferenceTarget 自动选择，旧 API / 原版机制保留在条件分支。Loader 始终对保留的旧游戏引用编译；根 DLL 文件名 RinArcherCore.dll，但 AssemblyName 为 RinArcherCore.Loader。内容 DLL 的原程序集名、模型 ID 与存档键不变。

`package.py` 只准备独立目录及变体清单，不安装或发布。`deliver.py` 依赖绑定最终 DLL 的运行结果并生成 ZIP；改动代码后不能将旧 PASS 套到新二进制。跨机器需更新项目引用与运行目录，实际游戏签名仍须重新核对。
