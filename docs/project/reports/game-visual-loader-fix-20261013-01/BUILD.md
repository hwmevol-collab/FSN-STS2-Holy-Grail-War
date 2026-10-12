# 最小复现

源码来自 ../game-v0111-compat-20261013-01/build/source 和 build/loader，版本保持 0.9.4-game-compat.1。生产差异仅见本目录两份 diff；SOURCE_BINDING.json 绑定最终内容 DLL、Loader 与源码。

用工程 .tools/dotnet/dotnet.exe 构建 build/source/RinArcherCore.csproj：Release；分别指定 RitsuLibReferenceTarget=0.107.1 / 0.111.0，GameDir=上轮 runtime-107-manual-dual / runtime-111-manual-dual；输出 build/candidate-107 / candidate-111。Loader 的既有旧版引用保持原样，构建 build/loader/RinArcherCore.Loader.csproj Release。具体原始构建结果见 build-107.log、build-111.log、build-loader.log。

package.py 生成独立包及新的内容 SHA 清单。checks-graph-* 只用于本轮定向 UI/路径 QA，不装入交付包。runtime.py 使用上轮保留的版本匹配游戏和依赖，创建本报告独立 Profile；graph-* 含 QA，manual-dual 不含 QA。图形检查绑定实际加载内容 DLL SHA；路径回退通过 Windows QA 的 Assembly.Location/AppPaths 模拟执行 Actual，不能代表 Android 实机通过。
