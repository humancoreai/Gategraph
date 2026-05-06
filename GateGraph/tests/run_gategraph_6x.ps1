param(
    [int]$Runs = 6,
    [int]$PauseMs = 750
)

$ErrorActionPreference = "Continue"

if (-not (Test-Path "tests\evidence_ci.py")) {
    Write-Host "ERROR: Bitte im GateGraph-Projektroot starten (Ordner mit tests\evidence_ci.py)." -ForegroundColor Red
    exit 1
}

$results = @()

for ($i = 1; $i -le $Runs; $i++) {
    Write-Host ""
    Write-Host "===== RUN $i / $Runs =====" -ForegroundColor Cyan

    $start = Get-Date

    # WHY: cmd captures stdout+stderr as plain text and avoids PowerShell NativeCommandError interruption.
    $output = cmd /c "python tests\evidence_ci.py 2>&1"
    $exitCode = $LASTEXITCODE

    $end = Get-Date
    $duration = [math]::Round(($end - $start).TotalSeconds, 3)

    $outputText = ($output -join "`n")

    $passed = "Unknown"
    if ($outputText -match "Passed:\s*True") {
        $passed = "True"
    } elseif ($outputText -match "Passed:\s*False") {
        $passed = "False"
    }

    $logPath = ""
    $logMatch = [regex]::Match($outputText, "Log:\s*(.+)")
    if ($logMatch.Success) {
        $logPath = $logMatch.Groups[1].Value.Trim()
    }

    $passCount = ([regex]::Matches($outputText, "(?m)^PASS\s+")).Count
    $failCount = ([regex]::Matches($outputText, "(?m)^FAIL\s+")).Count
    $timeoutCount = ([regex]::Matches($outputText, "status=timeout")).Count

    Write-Host "Run $i result: passed=$passed exit=$exitCode duration=${duration}s pass_items=$passCount fail_items=$failCount timeouts=$timeoutCount"
    if ($logPath) { Write-Host "Log: $logPath" }

    $results += [pscustomobject]@{
        run = $i
        passed = $passed
        exit_code = $exitCode
        duration_seconds = $duration
        pass_items = $passCount
        fail_items = $failCount
        timeout_items = $timeoutCount
        log = $logPath
    }

    Start-Sleep -Milliseconds $PauseMs
}

Write-Host ""
Write-Host "===== SUMMARY =====" -ForegroundColor Green
$results | Format-Table -AutoSize

$durations = @($results | ForEach-Object { [double]$_.duration_seconds })
$avgAll = [math]::Round((($results | Measure-Object duration_seconds -Average).Average), 3)
$minAll = [math]::Round((($results | Measure-Object duration_seconds -Minimum).Minimum), 3)
$maxAll = [math]::Round((($results | Measure-Object duration_seconds -Maximum).Maximum), 3)

$after3 = @($results | Where-Object { $_.run -ge 4 })
if ($after3.Count -gt 0) {
    $avgAfter3 = [math]::Round((($after3 | Measure-Object duration_seconds -Average).Average), 3)
    $maxAfter3 = [math]::Round((($after3 | Measure-Object duration_seconds -Maximum).Maximum), 3)
    $minAfter3 = [math]::Round((($after3 | Measure-Object duration_seconds -Minimum).Minimum), 3)

    Write-Host ""
    Write-Host "Zeitverhalten:" -ForegroundColor Yellow
    Write-Host "avg all runs: ${avgAll}s"
    Write-Host "min all runs: ${minAll}s"
    Write-Host "max all runs: ${maxAll}s"
    Write-Host "avg duration runs 4-${Runs}: ${avgAfter3}s"
    Write-Host "min duration runs 4-${Runs}: ${minAfter3}s"
    Write-Host "max duration runs 4-${Runs}: ${maxAfter3}s"
}

$csv = "six_run_simulation_results_fixed.csv"
$results | Export-Csv -Path $csv -NoTypeInformation -Encoding UTF8
Write-Host ""
Write-Host "CSV geschrieben: $csv"
