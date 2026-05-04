# Unified FieldLab

Unified FieldLab 是一个统一的 Web 漏洞教学平台，把原本拆开的 SQLi 与 XSS 靶场合并进同一站点，并新增：
- SSTI
- SSRF
- 越权（水平 / 垂直）

## 一、统一环境目标

同一站点、同一导航、同一运行方式，但每个漏洞域保留自己的分类学与教学顺序：
- SQLi：按注入位置 / 回显方式 / 业务影响
- XSS：按传播路径 / 浏览器上下文 / sink
- SSTI：按模板拼装路径 / 渲染时机
- SSRF：按请求路径 / 解析绕过 / 观测方式
- 越权：按水平 / 垂直 / 读取 / 修改 / 敏感操作

## 二、技术栈

- 统一 Web：Flask
- SQLi 数据库：MariaDB
- 其它内容状态：SQLite
- SSRF 内部目标：内网 Flask 服务（仅容器网络可见）
- 前端：Jinja2 + 原生 JS
- 部署：Docker Compose

## 三、漏洞域

### 1. SQL Injection 轨道
- 保留原 SQLi 12 关：登录绕过、UNION、报错、布尔盲注、时间盲注、堆叠查询、二次注入、排序/LIMIT、UPDATE、JSON API、伪修复、ORM 误用

### 2. XSS 轨道
- 保留原 XSS 12 关：反射、属性上下文、JS 字符串、存储型、二次 XSS、DOM hash、DOM API、postMessage/srcdoc、Markdown、SVG、javascript: 协议、伪修复

### 3. SSTI 轨道
- 4 关：直接模板渲染、表达式包装、存储后二次渲染、受信片段拼接

### 4. SSRF 轨道
- 4 关：基础抓取、字符串白名单绕过、重定向链、盲 SSRF 日志观测

### 5. 越权轨道
- 4 关：水平读取、水平修改、垂直页面访问、垂直敏感操作

## 四、启动

```bash
cd "/Users/w1th0ut/Documents/New project/web-fieldlab"
cp .env.example .env
docker compose up --build
```

访问：
- 首页：[http://127.0.0.1:5070](http://127.0.0.1:5070)
- 全域总览：[http://127.0.0.1:5070/labs](http://127.0.0.1:5070/labs)
- SQLi：[http://127.0.0.1:5070/domains/sqli](http://127.0.0.1:5070/domains/sqli)
- XSS：[http://127.0.0.1:5070/domains/xss](http://127.0.0.1:5070/domains/xss)
- SSTI：[http://127.0.0.1:5070/domains/ssti](http://127.0.0.1:5070/domains/ssti)
- SSRF：[http://127.0.0.1:5070/domains/ssrf](http://127.0.0.1:5070/domains/ssrf)
- 越权：[http://127.0.0.1:5070/domains/authz](http://127.0.0.1:5070/domains/authz)

## 五、模式

所有关卡默认支持：
- `?mode=vuln`
- `?mode=safe`

## 六、重置

全量：

```bash
./scripts/reset_lab.sh all
```

SQLi：

```bash
./scripts/reset_lab.sh sqli
./scripts/reset_lab.sh sqli-grades
./scripts/reset_lab.sh sqli-filters
```

XSS / SSTI / SSRF / 越权：

```bash
./scripts/reset_lab.sh xss
./scripts/reset_lab.sh ssti
./scripts/reset_lab.sh ssrf
./scripts/reset_lab.sh authz
```

## 七、健康检查

```bash
./scripts/healthcheck.sh
```

## 八、声明

本项目仅用于本地教学与授权实验环境，不应用于未授权目标。
