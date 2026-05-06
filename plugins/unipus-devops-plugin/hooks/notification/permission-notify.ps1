# Smart notification hook for Claude Code permission prompts
# Only notifies when Claude Code window is NOT in focus

# Define Win32 API to get foreground window
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern int GetWindowThreadProcessId(IntPtr hWnd, out int processId);
}
'@

# Get the foreground (focused) window's process ID
$fgWindow = [Win32]::GetForegroundWindow()
$fgPid = 0
$null = [Win32]::GetWindowThreadProcessId($fgWindow, [ref]$fgPid)

# Check if Claude Code or related process is focused
$claudeProcesses = Get-Process | Where-Object {
    ($_.ProcessName -match 'claude|Code|WindowsTerminal|powershell|bash') -and
    ($_.MainWindowHandle -ne 0)
}

$isFocused = $claudeProcesses | Where-Object { $_.Id -eq $fgPid }

# Only notify if Claude is NOT focused
if (-not $isFocused) {
    # Get custom message from environment or use default
    $msg = if ($env:CLAUDE_NOTIFICATION) {
        $env:CLAUDE_NOTIFICATION
    } else {
        'Master，Claude 等你发令！'
    }

    # Send notification with sound
    Import-Module BurntToast
    New-BurntToastNotification `
        -Text 'Claude Code', $msg `
        -Sound 'Default' `
        -AppLogo (Join-Path $env:USERPROFILE '.claude\icon.png')
}
