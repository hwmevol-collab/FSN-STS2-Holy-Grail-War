$env:TEMP='E:\FSN_MASTER_ASSET_WORK\tmp'
$env:TMP=$env:TEMP
$env:PATH='D:\mingw64\bin;'+$env:PATH
# C++20 span header is unused by upstream and unavailable in installed GCC 8.
$header='E:\FSN_MASTER_ASSET_WORK\repos\FSNr_raw\include\decenc.h'
(Get-Content -LiteralPath $header -Raw).Replace('#include <span>','// compatibility: unused span include removed') | Set-Content -LiteralPath $header -Encoding utf8
& 'D:\mingw64\bin\g++.exe' -std=c++17 -O2 -fno-strict-aliasing -shared -static 'E:\FSN_MASTER_ASSET_WORK\scripts\epk_bridge.cpp' -o 'E:\FSN_MASTER_ASSET_WORK\tools\epk_bridge.dll'
if ($LASTEXITCODE -ne 0) { throw 'EPK compiler failed' }
