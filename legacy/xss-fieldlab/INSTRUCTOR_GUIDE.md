# FieldLab XSS 教师指南

## 一、课程定位

这套靶场的核心不是教学生背 payload，而是让他们理解：
1. 数据进入浏览器的哪条解析链
2. 不同上下文为什么需要不同防御手段
3. 为什么“过滤一下 script”不等于修复

## 二、授课骨架

### 先按主轴讲
- 服务端反射型 XSS：L01 L02 L03 L12
- 服务端存储型 XSS：L04 L09 L10 L11
- DOM 型 XSS：L06 L07 L08
- 混合 / 二次 XSS：L05

### 再按上下文讲
- HTML 文本：L01 L04 L05 L06 L12
- HTML 属性：L02
- JavaScript 字符串：L03
- API 模板：L07
- postMessage / srcdoc：L08
- Markdown：L09
- SVG：L10
- URL 协议：L11

## 三、逐关讲解摘要

### L01 反射型 HTML 文本上下文
- 核心：原始模板渲染
- 教学点：autoescape 为什么有效

### L02 反射型属性上下文
- 核心：属性边界与事件属性
- 教学点：属性上下文不是“文本节点的小变种”

### L03 JavaScript 字符串上下文
- 核心：inline script
- 教学点：HTML 转义与 JS 安全序列化不是一回事

### L04 存储型评论墙
- 核心：持久化传播
- 教学点：sanitize 与 allowlist

### L05 二次 XSS：签名档审核
- 核心：第一次保存、第二次渲染
- 教学点：数据库里的数据也不天然可信

### L06 DOM 型：hash → innerHTML
- 核心：浏览器端 sink
- 教学点：服务端不参与也会有 XSS

### L07 DOM 型：JSON 模板渲染
- 核心：API 数据 + innerHTML
- 教学点：接口安全和前端渲染安全要分开讲

### L08 postMessage / srcdoc
- 核心：消息触发 + 新文档 sink
- 教学点：origin、schema、sink 三件事要一起做

### L09 Markdown / 富文本预览
- 核心：Markdown 渲染后依然是 HTML
- 教学点：render 后 sanitize

### L10 SVG 内联预览
- 核心：SVG 进入 DOM 解析链
- 教学点：不要内联不可信 SVG

### L11 javascript: 书签
- 核心：链接协议也是执行入口
- 教学点：协议白名单

### L12 伪修复
- 核心：只删 script
- 教学点：黑名单无法覆盖多种执行路径

## 四、统一修复原则
1. 明确上下文，再选择编码方式
2. textContent / createElement 优先于 innerHTML
3. 富文本与 Markdown 渲染后必须再 sanitize
4. URL 要做协议白名单
5. SVG 不要内联渲染不可信内容
6. 存储后的二次输出仍要做防护
7. 黑名单不是修复策略，只是脆弱补丁

## 五、课堂验证建议
- 优先使用 `fieldlab.record('lab-slug','message')` 作为稳定回显
- 不建议把 alert 作为唯一验证方式
- 每轮练习结束前执行局部 reset，保持下组学生的环境一致
