# Unified FieldLab

Unified FieldLab 是一个统一的 Web 漏洞教学平台，把多条原本分散的靶场轨道合并进同一站点，并统一了：

- 导航
- 漏洞模式 / 安全模式对照
- 重置脚本
- 教师讲义
- 课堂展示风格

## 一、统一环境目标

同一站点、同一运行方式、同一视觉环境，但每个漏洞域仍保留自己的分类学与授课顺序：

- SQLi：按注入位置 / 回显方式 / 业务影响
- XSS：按传播路径 / 浏览器上下文 / sink
- SSTI：按模板拼装路径 / 二次渲染
- SSRF：按请求路径 / 解析差异 / 观测方式
- 越权：按未授权 / 水平 / 垂直 / 对象 / 动作
- CSRF：按 token 缺失、伪来源校验、JSON API、敏感配置变更
- 文件上传：按类型、MIME、文件名、存储位置
- 支付逻辑：按价格信任、折扣状态、回调幂等
- 代码/命令注入：按解释器类型（Python / shell）
- XXE：按实体扩展目标（文件 / 内网 / 存储后二次解析）
- JSONP：按 callback 执行位与敏感数据泄露
- 条件竞争：按共享状态（券 / 库存 / 余额 / 席位）

## 二、技术栈

- 统一 Web：Flask
- SQLi 数据库：MariaDB
- 其它内容状态：SQLite
- SSRF / XXE 内部目标：内网 Flask 服务（仅容器网络可见）
- XML 解析：lxml
- 前端：Jinja2 + 原生 JS
- 部署：Docker Compose

## 三、漏洞域

### 1. SQL Injection 轨道
### 2. XSS 轨道
### 3. SSTI 轨道
### 4. SSRF 轨道
### 5. 越权轨道
### 6. CSRF 轨道
### 7. 文件上传轨道
### 8. 支付逻辑轨道
### 9. 代码 / 命令注入轨道
### 10. XXE 轨道
### 11. JSONP 轨道
### 12. 条件竞争轨道

## 四、启动（默认局域网可访问）

```bash
cd web-fieldlab
cp .env.example .env
docker compose up -d --build
```

默认监听：

- Web：`0.0.0.0:5070`
- DB：`127.0.0.1:3308`

访问：

- 本机首页：`http://127.0.0.1:5070`
- 局域网首页：`http://<你的局域网IP>:5070`
- 全域总览：`http://<你的局域网IP>:5070/labs`
- 越权：`http://<你的局域网IP>:5070/domains/authz`
- CSRF：`http://<你的局域网IP>:5070/domains/csrf`

查看本机局域网 IP：

```bash
# Linux
hostname -I | awk '{print $1}'

# macOS
ipconfig getifaddr en0 || ipconfig getifaddr en1
```

## 五、模式

所有关卡默认支持：

- `?mode=vuln`
- `?mode=safe`

## 六、重置

全量：

```bash
./scripts/reset_lab.sh all
```

分域：

```bash
./scripts/reset_lab.sh sqli
./scripts/reset_lab.sh xss
./scripts/reset_lab.sh ssti
./scripts/reset_lab.sh ssrf
./scripts/reset_lab.sh authz
./scripts/reset_lab.sh csrf
./scripts/reset_lab.sh upload
./scripts/reset_lab.sh payment
./scripts/reset_lab.sh injection
./scripts/reset_lab.sh xxe
./scripts/reset_lab.sh jsonp
./scripts/reset_lab.sh race
```

## 七、健康检查

```bash
./scripts/healthcheck.sh
curl -s http://127.0.0.1:5070/healthz
```

## 八、停止与清理

停止：

```bash
docker compose down
```

删除卷：

```bash
docker compose down -v
```

## 九、全平台安装教程

详见：[`../docs/INSTALL_LAN_ALL_PLATFORMS.md`](../docs/INSTALL_LAN_ALL_PLATFORMS.md)

## 十、声明

本项目仅用于本地教学与授权实验环境，不应用于未授权目标。
