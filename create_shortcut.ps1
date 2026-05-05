# ============================================================
# AthleteIQ 快捷方式创建脚本
# 在桌面创建启动快捷方式
# ============================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DesktopPath = [Environment]::GetFolderPath("Desktop")

# 创建桌面快捷方式指向 start.bat
$ShortcutPath = Join-Path $DesktopPath "AthleteIQ.lnk"
$TargetPath = Join-Path $ScriptDir "start.bat"
$IconPath = Join-Path $ScriptDir "frontend\favicon.ico"  # 如果有的话

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.WindowStyle = 1  # Normal window
$Shortcut.Description = "AthleteIQ 运动员数据监测系统 - 基于 NSCA-CSCS / CPSS 标准"
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Save()

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AthleteIQ 快捷方式已创建在桌面！" -ForegroundColor Green
Write-Host "  $ShortcutPath" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "双击桌面 'AthleteIQ' 即可启动系统" -ForegroundColor White
Write-Host ""

# 将项目文件夹打包为 zip
$ZipPath = Join-Path $ScriptDir "..\AthleteIQ_项目包.zip"
$SourceDir = $ScriptDir

Write-Host "正在打包项目..." -ForegroundColor Cyan

# 排除不需要的文件
$Exclude = @("node_modules", "venv", "__pycache__", ".git", "dist", ".next")
$TempFile = New-TemporaryFile

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($SourceDir, $ZipPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  项目已打包到: $ZipPath" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "快捷方式: 桌面 -> AthleteIQ" -ForegroundColor Yellow
Write-Host "启动命令: 双击桌面快捷方式" -ForegroundColor Yellow
Write-Host "      或: 右键管理员运行 start.bat" -ForegroundColor Yellow

Read-Host "按回车退出"
