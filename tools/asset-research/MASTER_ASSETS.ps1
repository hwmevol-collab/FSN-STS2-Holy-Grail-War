param([ValidateSet('Verify','Refresh','Full')][string]$Mode='Verify',[string]$LibraryRoot='E:\FSN_MASTER_ASSET_LIBRARY')
$ErrorActionPreference='Stop'
$mainWork='E:\FSN_MASTER_ASSET_WORK'
$python=Join-Path $mainWork 'tools\python\Scripts\python.exe'
$node='C:\Users\Murasame\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$scriptRoot=Join-Path $mainWork 'scripts'
if ($Mode -eq 'Full') {
    # Full runs always get fresh output and reports, preserving the existing master library.
    $runStamp=Get-Date -Format 'yyyyMMdd_HHmmss'
    if ($LibraryRoot -eq 'E:\FSN_MASTER_ASSET_LIBRARY') { $LibraryRoot='E:\FSN_MASTER_ASSET_LIBRARY_'+$runStamp }
    if (Test-Path -LiteralPath $LibraryRoot) { throw 'Full mode requires a new output directory' }
    $runWork=Join-Path $mainWork ('runs\'+$runStamp)
    New-Item -ItemType Directory -Path $runWork -Force | Out-Null
    foreach ($part in @('tools','repos','scripts')) { New-Item -ItemType Junction -Path (Join-Path $runWork $part) -Target (Join-Path $mainWork $part) | Out-Null }
    foreach ($part in @('tmp','logs','staging','reports')) { New-Item -ItemType Directory -Path (Join-Path $runWork $part) -Force | Out-Null }
    Copy-Item -LiteralPath (Join-Path $mainWork 'reports\REF_COMMITS.json'),(Join-Path $mainWork 'reports\requirements-lock.txt') -Destination (Join-Path $runWork 'reports')
    $env:FSN_WORK_ROOT=$runWork
} else { $env:FSN_WORK_ROOT=$mainWork }
$resolvedRoot=[IO.Path]::GetFullPath($LibraryRoot)
if (-not $resolvedRoot.StartsWith('E:\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Outputs must be on E:' }
$env:FSN_LIBRARY_ROOT=$resolvedRoot
$env:TEMP=Join-Path $env:FSN_WORK_ROOT 'tmp';$env:TMP=$env:TEMP
$env:PIP_CACHE_DIR=Join-Path $env:TEMP 'pip';$env:PYTHONPYCACHEPREFIX=Join-Path $env:TEMP 'pycache'
foreach ($part in @('Original\RawExtracted','Original\Converted','Original\Metadata','Remastered\RawExtracted\BIN','Remastered\RawExtracted\DAT','Remastered\RawExtracted\EPK','Remastered\Converted','Remastered\Metadata','Canonical','Converted','Metadata','Gallery','Reports')) { New-Item -ItemType Directory -Path (Join-Path $LibraryRoot $part) -Force | Out-Null }
function Run-Step([string]$Name,[string[]]$Arguments=@()) {
    Write-Host $Name
    & $python -u (Join-Path $scriptRoot $Name) @Arguments
    if ($LASTEXITCODE -ne 0) { throw ($Name+' failed; see retained logs and outputs') }
}
if ($Mode -eq 'Full') {
    Run-Step 'inventory.py'
    Run-Step 'extract_archives.py' @('XP3')
    Run-Step 'extract_archives.py' @('FPD')
    Run-Step 'extract_dat.py'
    Run-Step 'verify_xp3.py'
    Run-Step 'decrypt_epk.py'
    Run-Step 'catalog_base.py'
    Run-Step 'convert_assets.py'
    Run-Step 'extract_pe.py'
} else { Run-Step 'inventory.py' @('--verify') }
if ($Mode -ne 'Verify') {
    Run-Step 'convert_assets.py'
    Run-Step 'refine_formats.py'
    Run-Step 'decode_tft.py'
    Run-Step 'index_scripts.py'
    Run-Step 'finalize_catalog.py'
    Run-Step 'export_logs.py'
    Run-Step 'compare_images.py'
    Run-Step 'build_gallery.py'
    & $node (Join-Path $scriptRoot 'validate_gallery.cjs')
    if ($LASTEXITCODE -ne 0) { throw 'Offline gallery validation failed' }
    Run-Step 'qa_assets.py'
    Run-Step 'inventory.py' @('--verify')
    Run-Step 'acceptance_audit.py'
    Run-Step 'research_unknown.py'
    Run-Step 'disk_audit.py'
    Run-Step 'final_report.py'
}
Write-Host ('Done: '+$LibraryRoot)
