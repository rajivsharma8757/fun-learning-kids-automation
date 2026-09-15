# PowerShell script to remove Fun Learning Kids scheduled tasks
Unregister-ScheduledTask -TaskName "FunLearningKids_OnLogon" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "FunLearningKids_Morning" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "FunLearningKids_Evening" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "All FunLearningKids tasks have been removed from Task Scheduler."
