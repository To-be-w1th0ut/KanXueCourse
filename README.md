# KanXueCourse

这是一个统一的 Web 漏洞教学项目仓库，当前主项目为 `web-fieldlab/`。

## 课程覆盖

- SQL 注入
- XSS
- SSTI
- SSRF
- 越权（水平 / 垂直）
- CSRF
- 文件上传
- 支付逻辑漏洞
- 代码 / 命令注入
- XXE
- JSONP
- 条件竞争

## 快速开始（默认局域网可访问）

```bash
cd web-fieldlab
cp .env.example .env
docker compose up -d --build
```

启动后：

- 本机访问：`http://127.0.0.1:5070`
- 局域网访问：`http://<你的局域网IP>:5070`
- 健康检查：`http://<你的局域网IP>:5070/healthz`

> 当前默认配置中，Web 服务监听宿主机 `0.0.0.0:5070`，因此同一局域网机器可直接访问；数据库端口仍只绑定本机 `127.0.0.1:3308`。

## 完整安装文档

- 全平台安装教程：[`docs/INSTALL_LAN_ALL_PLATFORMS.md`](docs/INSTALL_LAN_ALL_PLATFORMS.md)
- 统一版项目说明：[`web-fieldlab/README.md`](web-fieldlab/README.md)

## 一键安装脚本

### Linux（Ubuntu / Debian）

```bash
curl -fsSL https://raw.githubusercontent.com/To-be-w1th0ut/KanXueCourse/main/scripts/install_linux.sh -o install_linux.sh
bash install_linux.sh
```

### macOS

```bash
curl -fsSL https://raw.githubusercontent.com/To-be-w1th0ut/KanXueCourse/main/scripts/install_macos.sh -o install_macos.sh
bash install_macos.sh
```

### Windows（管理员 PowerShell）

```powershell
Invoke-WebRequest https://raw.githubusercontent.com/To-be-w1th0ut/KanXueCourse/main/scripts/install_windows.ps1 -OutFile install_windows.ps1
powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
```

## 目录结构

```text
KanXueCourse/
├── docs/
├── scripts/
└── web-fieldlab/
```

## 说明

该仓库用于本地教学与授权实验环境。
