# PowerShell script to register Fun Learning Kids Windows Task Scheduler jobs
# 1. On Logon: Triggers when the user turns on the laptop and signs in
# 2. Morning: Daily at 09:00 AM
# 3. Evening: Daily at 09:30 PM

$Action = New-ScheduledTaskAction -Execute "C:\kids_automation\run_automation.bat" -WorkingDirectory "C:\kids_automation"

$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$TriggerMorning = New-ScheduledTaskTrigger -Daily -At "09:00"
$TriggerEvening = New-ScheduledTaskTrigger -Daily -At "21:30"

# Settings optimized for laptops: run if missed, run on battery, do not stop on battery
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

try {
    Register-ScheduledTask -TaskName "FunLearningKids_OnLogon" -Action $Action -Trigger $TriggerLogon -Settings $Settings -Description "Fun Learning Kids laptop startup/logon trigger" -Force | Out-Null
    Write-Host "✅ Registered Task: FunLearningKids_OnLogon (Runs when laptop starts / user logs in)"
} catch {
    Write-Warning "Could not register FunLearningKids_OnLogon: $_"
}

try {
    Register-ScheduledTask -TaskName "FunLearningKids_Morning" -Action $Action -Trigger $TriggerMorning -Settings $Settings -Description "Fun Learning Kids morning YouTube automation" -Force | Out-Null
    Write-Host "✅ Registered Task: FunLearningKids_Morning (Daily at 09:00 AM)"
} catch {
    Write-Warning "Could not register FunLearningKids_Morning: $_"
}

try {
    Register-ScheduledTask -TaskName "FunLearningKids_Evening" -Action $Action -Trigger $TriggerEvening -Settings $Settings -Description "Fun Learning Kids evening YouTube automation" -Force | Out-Null
    Write-Host "✅ Registered Task: FunLearningKids_Evening (Daily at 09:30 PM)"
} catch {
    Write-Warning "Could not register FunLearningKids_Evening: $_"
}

Write-Host "`n🎉 Task Scheduler setup complete! The system will check on laptop startup and at scheduled times."
