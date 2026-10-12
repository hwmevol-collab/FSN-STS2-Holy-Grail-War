param([Parameter(Mandatory)][string]$Path)
$ErrorActionPreference='Stop'
# The opt-in bridge refreshes these small files on the render thread. A reader
# can briefly overlap a truncate/write; wait for a complete snapshot to parse.
for($attempt=0;$attempt-lt20;$attempt++){
    try{$snapshot=Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json;if($null-eq$snapshot){throw 'Empty QA snapshot'};return $snapshot}catch{if($attempt-eq19){throw};Start-Sleep -Milliseconds 25}
}
