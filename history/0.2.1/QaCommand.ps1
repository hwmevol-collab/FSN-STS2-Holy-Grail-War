param([Parameter(Mandatory)][string]$Operation,[int]$Index=0,[bool]$Boost=$false,[string]$Owner='CHAR_ARCHER',[string]$Name='qa-capture')
$ErrorActionPreference='Stop'
$qaRoot=Join-Path $PSScriptRoot 'native-runtime'
$qaResult=Join-Path $qaRoot 'qa-last-result.json'
$qaBefore=if(Test-Path -LiteralPath $qaResult){(Get-Item -LiteralPath $qaResult).LastWriteTimeUtc}else{[datetime]::MinValue}
$qaCommand=Join-Path $qaRoot 'qa-command.json'
if(Test-Path -LiteralPath $qaCommand){throw 'A QA command is already pending'}
@{op=$Operation;index=$Index;boost=$Boost;owner=$Owner;name=$Name} | ConvertTo-Json -Compress | Set-Content -LiteralPath $qaCommand -Encoding utf8
$qaDeadline=(Get-Date).AddSeconds(35)
do{
    Start-Sleep -Milliseconds 150
    if((Test-Path -LiteralPath $qaResult) -and (Get-Item -LiteralPath $qaResult).LastWriteTimeUtc -gt $qaBefore){
        $qaResponse=Get-Content -LiteralPath $qaResult -Raw | ConvertFrom-Json
        if(!$qaResponse.ok){throw $qaResponse.error}
        $qaResponse | ConvertTo-Json -Compress
        return
    }
}while((Get-Date) -lt $qaDeadline)
throw 'QA command timeout; inspect native-qa stderr and qa-state.json'
