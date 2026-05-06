# KanXueCourse 全平台安装教程（局域网可访问版）

本文档提供从软件安装到项目启动的全链路命令，覆盖：

- Linux（Ubuntu / Debian）
- macOS
- Windows（PowerShell + WSL 2）

## 目标

安装完成后，统一版教学平台默认：

- Web 监听 `0.0.0.0:5070`
- 可通过 `http://<你的局域网IP>:5070` 被同局域网机器访问
- MariaDB 仍只监听本机 `127.0.0.1:3308`

---

## 一、项目运行依赖

宿主机需要：

- Git
- Docker
- Docker Compose
- Windows 额外需要 WSL 2

容器内会自动安装：

- Flask==3.0.3
- PyMySQL==1.1.1
- SQLAlchemy==2.0.36
- Markdown==3.6
- bleach==6.1.0
- lxml==5.3.0
- PyYAML==6.0.2

---

## 二、Linux（Ubuntu / Debian）

### 1. 安装 Git + Docker + Compose

```bash
sudo apt update
sudo apt install -y git ca-certificates curl

sudo apt remove -y docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc || true

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF2
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF2

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
```

### 2. 下载项目并启动

```bash
cd "$HOME"
rm -rf KanXueCourse
git clone https://github.com/To-be-w1th0ut/KanXueCourse.git
cd KanXueCourse/web-fieldlab
cp .env.example .env
sudo docker compose up -d --build
sudo docker compose ps
```

### 3. 查看局域网访问地址

```bash
hostname -I | awk '{print $1}'
curl -s http://127.0.0.1:5070/healthz
```

访问：

```text
http://<你的局域网IP>:5070
```

---

## 三、macOS

### 1. 安装 Git

```bash
xcode-select --install
```

如为 Apple Silicon，可选安装 Rosetta 2：

```bash
softwareupdate --install-rosetta
```

### 2. 安装 Docker Desktop

```bash
ARCH="$(uname -m)"
if [ "$ARCH" = "arm64" ]; then
  DOCKER_URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
else
  DOCKER_URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
fi

curl -L "$DOCKER_URL" -o /tmp/Docker.dmg
sudo hdiutil attach /tmp/Docker.dmg
sudo /Volumes/Docker/Docker.app/Contents/MacOS/install --accept-license
sudo hdiutil detach /Volumes/Docker
open -a Docker
```

等待 Docker 启动：

```bash
until docker info >/dev/null 2>&1; do
  echo "waiting Docker Desktop..."
  sleep 5
done
```

### 3. 下载项目并启动

```bash
cd "$HOME"
rm -rf KanXueCourse
git clone https://github.com/To-be-w1th0ut/KanXueCourse.git
cd KanXueCourse/web-fieldlab
cp .env.example .env
docker compose up -d --build
docker compose ps
```

### 4. 查看局域网访问地址

```bash
ipconfig getifaddr en0 || ipconfig getifaddr en1
curl -s http://127.0.0.1:5070/healthz
```

访问：

```text
http://<你的局域网IP>:5070
```

---

## 四、Windows（管理员 PowerShell）

### 1. 安装 Git

```powershell
winget install --id Git.Git -e --source winget
git --version
```

### 2. 安装 WSL 2

```powershell
wsl --install
wsl --update
wsl --version
```

> 如果执行后提示重启，请先重启系统再继续。

### 3. 安装 Docker Desktop

#### x64

```powershell
$installer = "$env:TEMP\DockerDesktopInstaller.exe"
Invoke-WebRequest 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe' -OutFile $installer
Start-Process $installer -Wait -ArgumentList 'install','--accept-license'
```

#### ARM64

```powershell
$installer = "$env:TEMP\DockerDesktopInstaller.exe"
Invoke-WebRequest 'https://desktop.docker.com/win/main/arm64/Docker%20Desktop%20Installer.exe' -OutFile $installer
Start-Process $installer -Wait -ArgumentList 'install','--accept-license'
```

启动 Docker Desktop：

```powershell
Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
$env:Path += ';C:\Program Files\Docker\Docker\resources\bin'
```

等待 Docker 启动：

```powershell
for ($i = 0; $i -lt 60; $i++) {
  try {
    docker info | Out-Null
    break
  } catch {
    Start-Sleep -Seconds 5
  }
}
```

### 4. 下载项目并启动

```powershell
Set-Location $HOME
if (Test-Path .\KanXueCourse) { Remove-Item .\KanXueCourse -Recurse -Force }

git clone https://github.com/To-be-w1th0ut/KanXueCourse.git
Set-Location .\KanXueCourse\web-fieldlab
Copy-Item .env.example .env -Force

docker compose up -d --build
docker compose ps
Invoke-RestMethod http://127.0.0.1:5070/healthz | ConvertTo-Json -Depth 5
```

### 5. 查看局域网访问地址

```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
  $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*'
} | Select-Object InterfaceAlias,IPAddress
```

访问：

```text
http://<你的局域网IP>:5070
```

---

## 五、一键安装脚本

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/To-be-w1th0ut/KanXueCourse/main/scripts/install_linux.sh -o install_linux.sh
bash install_linux.sh
```

### macOS

```bash
curl -fsSL https://raw.githubusercontent.com/To-be-w1th0ut/KanXueCourse/main/scripts/install_macos.sh -o install_macos.sh
bash install_macos.sh
```

### Windows

```powershell
Invoke-WebRequest https://raw.githubusercontent.com/To-be-w1th0ut/KanXueCourse/main/scripts/install_windows.ps1 -OutFile install_windows.ps1
powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
```

---

## 六、常用运维命令

### 启动

```bash
cd ~/KanXueCourse/web-fieldlab
docker compose up -d --build
```

### 查看状态

```bash
docker compose ps
```

### 查看日志

```bash
docker compose logs --tail=100
docker compose logs -f web
```

### 健康检查

```bash
./scripts/healthcheck.sh
curl -s http://127.0.0.1:5070/healthz
```

### 停止

```bash
docker compose down
```

### 删除卷

```bash
docker compose down -v
```

---

## 七、说明

- Web 默认开放到局域网，适合教学投屏和多人同网访问。
- 如不希望局域网访问，请把 `web-fieldlab/docker-compose.yml` 中的 Web 端口绑定改回 `127.0.0.1:${HOST_WEB_PORT:-5070}:5000`。
- 数据库端口仍默认只监听本机，避免误暴露。
