# FieldLab XSS Range

FieldLab XSS Range 是一套本地化、可重置、偏实战讲解的 XSS 教学靶场：
- 默认仅本机访问
- 支持漏洞模式 / 安全模式对照
- 覆盖反射型、存储型、DOM 型、二次 XSS
- 每关带学生提示、教师讲解路径、环境重置脚本
- 提供“执行控制台”，便于课堂验证脚本是否真正跑起来

## 一、分类框架

本靶场沿用“1 个主轴 + 多个副轴”的教学结构。

### 主轴：脚本进入浏览器解析的路径
- 服务端反射型 XSS
- 服务端存储型 XSS
- DOM 型 XSS
- 混合 / 二次 XSS

### 副轴 1：按上下文分类
- HTML 文本上下文
- HTML 属性上下文
- JavaScript 字符串上下文
- Markdown / 富文本上下文
- SVG / XML 上下文
- URL 协议上下文
- API 模板上下文
- postMessage / srcdoc 上下文

### 副轴 2：按触发时机分类
- 立即触发
- 存储后触发
- 导航后触发
- 消息触发

### 副轴 3：按 sink 分类
- 原始模板渲染
- innerHTML
- inline script
- iframe srcdoc
- href / javascript:
- Markdown 渲染器
- 内联 SVG
- 黑名单伪修复

## 二、关卡矩阵

| 关卡 | 主轴 | 上下文 | 时机 | sink |
|---|---|---|---|---|
| L01 | 服务端反射型 | HTML 文本 | 立即触发 | 原始模板渲染 |
| L02 | 服务端反射型 | HTML 属性 | 立即触发 | 原始模板渲染 |
| L03 | 服务端反射型 | JavaScript 字符串 | 立即触发 | inline script |
| L04 | 服务端存储型 | HTML 文本 | 存储后触发 | 原始模板渲染 |
| L05 | 混合 / 二次 | HTML 文本 | 存储后触发 | 原始模板渲染 |
| L06 | DOM 型 | HTML 文本 | 导航后触发 | innerHTML |
| L07 | DOM 型 | API 模板 | 立即触发 | innerHTML |
| L08 | DOM 型 | postMessage / srcdoc | 消息触发 | iframe srcdoc |
| L09 | 服务端存储型 | Markdown / 富文本 | 存储后触发 | Markdown 渲染器 |
| L10 | 服务端存储型 | SVG / XML | 存储后触发 | 内联 SVG |
| L11 | 服务端存储型 | URL 协议 | 存储后触发 | href / javascript: |
| L12 | 服务端反射型 | HTML 文本 | 立即触发 | 黑名单伪修复 |

## 三、技术栈
- Web：Flask
- 数据：SQLite（挂载到本地 `data/fieldlab.db`）
- 前端：Jinja2 + 原生 JS
- 部署：Docker Compose
- Sanitizer：Bleach
- Markdown：Python-Markdown

## 四、启动

```bash
cd "/Users/w1th0ut/Documents/New project/xss-fieldlab"
cp .env.example .env
docker compose up --build
```

访问：
- 首页：[http://127.0.0.1:5060](http://127.0.0.1:5060)
- 关卡总览：[http://127.0.0.1:5060/labs](http://127.0.0.1:5060/labs)
- 健康检查：[http://127.0.0.1:5060/healthz](http://127.0.0.1:5060/healthz)

## 五、模式说明
- `?mode=vuln`：漏洞模式
- `?mode=safe`：安全模式

## 六、重置

全量：

```bash
./scripts/reset_lab.sh all
```

局部：

```bash
./scripts/reset_lab.sh stored-comments
./scripts/reset_lab.sh second-order-signature
./scripts/reset_lab.sh markdown-preview
./scripts/reset_lab.sh svg-preview
./scripts/reset_lab.sh url-bookmarks
./scripts/reset_lab.sh events
```

## 七、教学建议

推荐顺序：
1. L01 / L02 / L03 先讲上下文差异
2. L04 / L05 讲存储型与二次 XSS
3. L06 / L07 / L08 讲 DOM sink
4. L09 / L10 / L11 讲复杂渲染器和协议问题
5. L12 用来回收“伪修复为什么不可靠”

## 八、说明
本项目仅用于本地教学与授权实验环境，不应用于未授权目标。
