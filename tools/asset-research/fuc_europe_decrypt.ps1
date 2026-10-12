[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$base='E:\FSN_MASTER_ASSET_WORK\tools\ppsspp-isolated'
$runtime=Join-Path $base 'runtime'
$memstick=Join-Path $base 'memstick'
$iso='E:\BaiduNetdiskDownload\FSN\素材\Fate-Unlimited Codes (Europe) (PSP) (PSN)\Fate-Unlimited Codes (Europe) (PSP) (PSN).iso'
$output='E:\FSN_MASTER_ASSET_WORK\fuc\Europe\Executable\EBOOT_DECRYPTED.bin'
New-Item -ItemType Directory -Force -Path $runtime,$memstick,(Split-Path -Parent $output) | Out-Null
if(-not(Test-Path -LiteralPath (Join-Path $runtime 'PPSSPPWindows64.exe'))){Expand-Archive -LiteralPath (Join-Path $base 'ppsspp_win_1.20.4.zip') -DestinationPath $runtime}
$exe=Get-ChildItem -LiteralPath $runtime -Recurse -File -Filter 'PPSSPPWindows64.exe' | Select-Object -First 1
$ini=Join-Path $base 'dump_eboot.ini'
"[General]`nDumpFileTypes = 1`n" | Set-Content -LiteralPath $ini -Encoding ascii
$arguments=@('--windowed','--pause-menu-exit',"--memstick=`"$memstick`"","--appendconfig=`"$ini`"","`"$iso`"")
$process=Start-Process -FilePath $exe.FullName -WorkingDirectory $exe.DirectoryName -ArgumentList $arguments -WindowStyle Hidden -PassThru
$deadline=[DateTime]::UtcNow.AddSeconds(120)
$dump=$null
try{
    while([DateTime]::UtcNow -lt $deadline){
        $dump=Get-ChildItem -LiteralPath $memstick,(Join-Path $runtime 'memstick') -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '(?i)eboot' -and $_.Extension -ieq '.bin' -and $_.Length -eq 2000320 } | Select-Object -First 1
        if($dump){break}
        $process.Refresh();if($process.HasExited){break}
        Start-Sleep -Milliseconds 250
    }
    if(-not $dump){throw 'Isolated PPSSPP did not produce a complete EBOOT dump.'}
    $hash=(Get-FileHash -LiteralPath $dump.FullName -Algorithm SHA256).Hash
    if($hash -ne '33E8240519A232BE40BE503F17A23C2DFD5A361177FFB925DE444DF95DBE6BA7'){throw 'Actual European dump differs from the independently documented reference; preserve it for investigation.'}
    Copy-Item -LiteralPath $dump.FullName -Destination $output
    [ordered]@{version='1.20.4';iso=$iso;output=$output;size=$dump.Length;sha256=$hash;isolated_memstick=$memstick;process_id=$process.Id;method='Official DumpFileTypes=1; source read only'} | ConvertTo-Json | Set-Content -LiteralPath 'E:\FSN_MASTER_ASSET_WORK\fuc\Europe\Executable\DECRYPT_EVIDENCE.json' -Encoding utf8
}finally{
    $process.Refresh()
    if(-not $process.HasExited){Stop-Process -Id $process.Id; $process.WaitForExit()}
}
