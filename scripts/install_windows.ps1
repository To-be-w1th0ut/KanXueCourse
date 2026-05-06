param(
  [string]$TargetDir = "$HOME\KanXueCourse"
)

$ErrorActionPreference = 'Stop'
$RepoUrl = 'https://github.com/To-be-w1th0ut/KanXueCourse.git'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  throw '请以管理员身份运行 PowerShell。'
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  winget install --id Git.Git -e --source winget
}

try {
  wsl --status | Out-Null
} catch {
  wsl --install
  Write-Host 'WSL 已开始安装，请重启系统后重新运行脚本。'
  exit 0
}

wsl --update

$dockerExe = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
if (-not (Test-Path $dockerExe)) {
  $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
  if ($arch -eq 'Arm64') {
    $dockerUrl = 'https://desktop.docker.com/win/main/arm64/Docker%20Desktop%20Installer.exe'
  } else {
    $dockerUrl = 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe'
  }
  $installer = "$env:TEMP\DockerDesktopInstaller.exe"
  Invoke-WebRequest $dockerUrl -OutFile $installer
  Start-Process $installer -Wait -ArgumentList 'install','--accept-license'
}

Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
$env:Path += ';C:\Program Files\Docker\Docker\resources\bin'

for ($i = 0; $i -lt 60; $i++) {
  try {
    docker info | Out-Null
    break
  } catch {
    Start-Sleep -Seconds 5
  }
}

if (Test-Path (Join-Path $TargetDir '.git')) {
  git -C $TargetDir pull --ff-only
} else {
  if (Test-Path $TargetDir) { Remove-Item $TargetDir -Recurse -Force }
  git clone $RepoUrl $TargetDir
}

Set-Location (Join-Path $TargetDir 'web-fieldlab')
Copy-Item .env.example .env -Force

docker compose up -d --build
docker compose ps

for ($i = 0; $i -lt 30; $i++) {
  try {
    Invoke-RestMethod http://127.0.0.1:5070/healthz | Out-Null
    break
  } catch {
    Start-Sleep -Seconds 3
  }
}

$lan = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
  $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.PrefixOrigin -ne 'WellKnown'
} | Select-Object -First 1 -ExpandProperty IPAddress

Write-Host "[+] 本机访问: http://127.0.0.1:5070"
Write-Host "[+] 局域网访问: http://$lan:5070"
