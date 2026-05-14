<#
.SYNOPSIS
  Install or uninstall Apulu HQ desktop shell auto-start at user login.

.DESCRIPTION
  Creates a shortcut in the user's Startup folder that launches the
  pywebview shell via pythonw.exe (no console window), starting minimized
  to the system tray.

  Per the user's environment preferences:
    - No terminal window on boot
    - Survives reboots (Startup folder fires before any manual login work)
    - Local-only, no service, no admin

.EXAMPLE
  .\install_startup.ps1 install
  .\install_startup.ps1 uninstall
  .\install_startup.ps1 launch       # manual one-shot launch (testing)
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet("install", "uninstall", "launch", "status")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"

$ProjectDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ShellScript  = Join-Path $ProjectDir "apulu_hq_shell.pyw"
$VenvDir      = Join-Path $ProjectDir ".venv"
$PythonW      = Join-Path $VenvDir "Scripts\pythonw.exe"
$StartupDir   = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "Apulu HQ.lnk"

if (-not (Test-Path $PythonW)) {
    # Fall back to system pythonw if no venv (less ideal — deps must be global)
    $PythonW = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
}

function Get-Status {
    [PSCustomObject]@{
        ShellScript       = $ShellScript
        ShellScriptExists = Test-Path $ShellScript
        PythonW           = $PythonW
        PythonWExists     = ($PythonW -and (Test-Path $PythonW))
        Shortcut          = $ShortcutPath
        ShortcutExists    = Test-Path $ShortcutPath
        BackendRunning    = $false
    }
}

function Show-Status {
    $s = Get-Status
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:8741/api/health" -TimeoutSec 1 -UseBasicParsing | Out-Null
        $s.BackendRunning = $true
    } catch {}
    $s | Format-List
}

switch ($Action) {

    "status" {
        Show-Status
    }

    "install" {
        if (-not (Test-Path $ShellScript)) {
            throw "Shell script not found: $ShellScript"
        }
        if (-not (Test-Path $PythonW)) {
            throw "pythonw.exe not found. Run 'python -m venv .venv && .\.venv\Scripts\Activate.ps1 && pip install -e .[dev] && pip install pywebview pystray pillow' first."
        }
        $shell = New-Object -ComObject WScript.Shell
        $sc = $shell.CreateShortcut($ShortcutPath)
        $sc.TargetPath = $PythonW
        # --minimized: skip showing the window on auto-launch; user opens via tray
        $sc.Arguments = "`"$ShellScript`" --minimized"
        $sc.WorkingDirectory = $ProjectDir
        $sc.Description = "Apulu HQ — interactive label operations app"
        $sc.WindowStyle = 7   # minimized
        $sc.Save()
        Write-Host "✓ Installed startup shortcut at:" -ForegroundColor Green
        Write-Host "  $ShortcutPath"
        Write-Host ""
        Write-Host "  Will launch on next user login. To start it now without rebooting:"
        Write-Host "    .\install_startup.ps1 launch" -ForegroundColor Cyan
    }

    "uninstall" {
        if (Test-Path $ShortcutPath) {
            Remove-Item $ShortcutPath -Force
            Write-Host "✓ Removed: $ShortcutPath" -ForegroundColor Green
        } else {
            Write-Host "No shortcut found at $ShortcutPath"
        }
    }

    "launch" {
        if (-not (Test-Path $ShellScript)) { throw "Shell script not found: $ShellScript" }
        if (-not (Test-Path $PythonW))     { throw "pythonw.exe not found at $PythonW" }
        Write-Host "Launching $ShellScript (detached, no console)..."
        Start-Process -FilePath $PythonW -ArgumentList "`"$ShellScript`"" -WorkingDirectory $ProjectDir -WindowStyle Hidden
        Write-Host "✓ Launched. The window should appear in a few seconds."
        Write-Host "  Status: try ``.\install_startup.ps1 status`` in ~10s to confirm backend is up."
    }
}
