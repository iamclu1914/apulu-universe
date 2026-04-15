# Enable MorningMain Scheduled Task
# Run this script as Administrator

try {
    Write-Host "Checking current MorningMain task status..." -ForegroundColor Yellow
    $task = Get-ScheduledTask -TaskName "MorningMain" -TaskPath "\Vawn\" -ErrorAction Stop
    Write-Host "Current State: $($task.State)" -ForegroundColor Cyan

    Write-Host "Enabling MorningMain task..." -ForegroundColor Yellow
    Enable-ScheduledTask -TaskName "MorningMain" -TaskPath "\Vawn\" -ErrorAction Stop
    Write-Host "SUCCESS: MorningMain task enabled!" -ForegroundColor Green

    # Verify configuration
    Write-Host "`nTask Configuration:" -ForegroundColor Yellow
    $updatedTask = Get-ScheduledTask -TaskName "MorningMain" -TaskPath "\Vawn\"
    Write-Host "State: $($updatedTask.State)" -ForegroundColor Cyan

    $triggers = $updatedTask.Triggers
    Write-Host "Schedule: $($triggers.StartBoundary)" -ForegroundColor Cyan

    $actions = $updatedTask.Actions
    Write-Host "Command: $($actions.Execute) $($actions.Arguments)" -ForegroundColor Cyan

} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please run this script as Administrator" -ForegroundColor Yellow
    Read-Host "Press Enter to continue..."
}