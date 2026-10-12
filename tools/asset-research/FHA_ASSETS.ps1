param(
    [ValidateSet('HollowAtaraxia')][string]$Source='HollowAtaraxia',
    [ValidateSet('All','Inventory','Extract','Convert','Index','Compare','Integrate','Gallery','Verify','Disk','Report')][string]$Phase='All'
)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$fhaPython='E:\FSN_MASTER_ASSET_WORK\tools\python\Scripts\python.exe'
$fhaScripts='E:\FSN_MASTER_ASSET_WORK\scripts'
$fhaMetadata='E:\FSN_MASTER_ASSET_LIBRARY\HollowAtaraxia\Metadata'
function Invoke-FhaScript([string]$Name,[string[]]$Arguments=@()) {
    & $fhaPython (Join-Path $fhaScripts $Name) @Arguments
    if ($LASTEXITCODE -ne 0) { throw "FHA phase failed: $Name" }
}
$fhaCommitted=Test-Path -LiteralPath (Join-Path $fhaMetadata 'INTEGRATION_COMMIT.json')
if ($fhaCommitted -and $Phase -in @('Extract','Convert','Index','Compare')) { throw 'Integrated IDs are frozen. Use a reviewed FHA-only revision; destructive phase replay is refused.' }
if ($Phase -in @('All','Inventory')) { Invoke-FhaScript 'fha_prepare.py' }
if (-not $fhaCommitted) {
    if ($Phase -in @('All','Extract')) {
        if (-not (Test-Path -LiteralPath (Join-Path $fhaMetadata 'EXTRACTION_SUMMARY.json'))) {
            Invoke-FhaScript 'fha_extract.py'
            Invoke-FhaScript 'fha_molebox.py' @('--extract')
            Invoke-FhaScript 'fha_nested.py'
            Invoke-FhaScript 'fha_filter_vm.py'
            Invoke-FhaScript 'fha_extraction_finalize.py'
        }
    }
    if ($Phase -in @('All','Convert')) { Invoke-FhaScript 'fha_convert.py' }
    if ($Phase -in @('All','Index')) { Invoke-FhaScript 'fha_index.py' }
    if ($Phase -in @('All','Compare')) { Invoke-FhaScript 'fha_compare.py' }
}
if ($Phase -in @('All','Integrate')) { Invoke-FhaScript 'fha_integrate.py' }
if ($Phase -in @('All','Gallery')) { Invoke-FhaScript 'fha_gallery.py' }
if ($Phase -in @('All','Verify')) {
    Invoke-FhaScript 'fha_image_roles.py'
    Invoke-FhaScript 'fha_finalize.py'
    Invoke-FhaScript 'fha_verify.py'
}
if ($Phase -in @('All','Disk')) { Invoke-FhaScript 'fha_disk.py'; Invoke-FhaScript 'fha_disk_details.py' }
if ($Phase -in @('All','Report')) { Invoke-FhaScript 'fha_report.py' }
Write-Output 'FHA phase finished. Browser acceptance evidence is retained separately; this command never fabricates a browser PASS.'
