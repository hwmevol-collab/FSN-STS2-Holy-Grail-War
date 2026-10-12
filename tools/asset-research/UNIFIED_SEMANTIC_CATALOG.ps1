param([ValidateSet('Inventory','Entities','Aliases','Evidence','Relations','CrossSource','Usage','Database','Browser','Verify','QA','Report','All')][string]$Mode='Inventory',[string]$Revision='v1')
$ErrorActionPreference='Stop'
$env:PYTHONPYCACHEPREFIX='E:\FSN_MASTER_ASSET_WORK\pycache\unified'
$env:PYTHONIOENCODING='utf-8'
$taskPython='D:\Python\python.exe'
$taskScripts='E:\FSN_MASTER_ASSET_WORK\scripts'
function Run-TaskScript([string]$Name,[string[]]$TaskArguments=@()) {
    & $taskPython (Join-Path $taskScripts $Name) @TaskArguments
    if($LASTEXITCODE -ne 0){throw "Unified semantic stage failed: $Name"}
}
if($Mode -eq 'Inventory'){Run-TaskScript 'unified_inventory.py';return}
if($Mode -eq 'Verify'){Run-TaskScript 'unified_inventory.py' @('Verify');return}
if($Mode -eq 'Browser'){Copy-Item -LiteralPath (Join-Path $taskScripts 'unified_browser.html') -Destination 'E:\FSN_MASTER_ASSET_LIBRARY\SemanticCatalog\index.html';return}
if($Mode -eq 'QA'){Run-TaskScript 'unified_qa.py';return}
if($Mode -eq 'Report'){Run-TaskScript 'unified_report.py';return}
# Entity/alias/evidence dependencies form one atomic, reproducible sidecar transaction.
Run-TaskScript 'unified_inventory.py'
Run-TaskScript 'unified_build.py' @($Revision)
Run-TaskScript 'unified_refine.py'
Copy-Item -LiteralPath (Join-Path $taskScripts 'unified_browser.html') -Destination 'E:\FSN_MASTER_ASSET_LIBRARY\SemanticCatalog\index.html'
if($Mode -eq 'All'){
    Run-TaskScript 'unified_inventory.py' @('Verify')
    Run-TaskScript 'unified_qa.py'
    Run-TaskScript 'unified_report.py'
}
