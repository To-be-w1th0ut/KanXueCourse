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
- 越权：按水平 / 垂直 / 对象 / 动作
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

### 1. SQL Injection 轨道（12 关）
- 登录绕过、UNION、报错、布尔盲注、时间盲注、堆叠查询、二次注入、排序/LIMIT、UPDATE、JSON API、伪修复、ORM 误用

### 2. XSS 轨道（12 关）
- 反射型、属性上下文、JS 字符串、存储型、二次 XSS、DOM hash、DOM API、postMessage/srcdoc、Markdown、SVG、javascript: 协议、伪修复

### 3. SSTI 轨道（4 关）
- 直接模板渲染、表达式包装、存储后二次渲染、受信片段拼接

### 4. SSRF 轨道（4 关）
- 基础抓取、字符串白名单绕过、重定向链、盲 SSRF 日志观测

### 5. 越权轨道（4 关）
- 水平读取、水平修改、垂直页面访问、垂直敏感操作

### 6. 文件上传轨道（3 关）
- 公开可访问 HTML 上传、MIME 信任、文件名路径穿越与覆盖

### 7. 支付逻辑轨道（4 关）
- 客户端总价篡改、负数数量、优惠券重复使用、重复支付回调

### 8. 代码 / 命令注入轨道（4 关）
- Python eval、存储后 exec、shell 拼接诊断、grep 命令注入

### 9. XXE 轨道（3 关）
- 本地文件读取、内网请求、存储后二次解析

### 10. JSONP 轨道（3 关）
- callback 可控、敏感资料泄露、黑名单伪修复

### 11. 条件竞争轨道（4 关）
- 一次性优惠券、库存超卖、钱包竞争扣款、席位争抢

## 四、启动

```bash
cd "/Users/w1th0ut/Documents/New project/KanXueCourse/web-fieldlab"
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
- 上传：[http://127.0.0.1:5070/domains/upload](http://127.0.0.1:5070/domains/upload)
- 支付逻辑：[http://127.0.0.1:5070/domains/payment](http://127.0.0.1:5070/domains/payment)
- 代码/命令注入：[http://127.0.0.1:5070/domains/injection](http://127.0.0.1:5070/domains/injection)
- XXE：[http://127.0.0.1:5070/domains/xxe](http://127.0.0.1:5070/domains/xxe)
- JSONP：[http://127.0.0.1:5070/domains/jsonp](http://127.0.0.1:5070/domains/jsonp)
- 条件竞争：[http://127.0.0.1:5070/domains/race](http://127.0.0.1:5070/domains/race)

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

其它域：

```bash
./scripts/reset_lab.sh xss
./scripts/reset_lab.sh ssti
./scripts/reset_lab.sh ssrf
./scripts/reset_lab.sh authz
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
```

## 八、声明

本项目仅用于本地教学与授权实验环境，不应用于未授权目标。
