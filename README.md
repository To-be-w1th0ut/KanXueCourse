# KanXueCourse

这是一个统一的 Web 漏洞教学项目仓库。

## 当前主项目

- `web-fieldlab/`：统一版教学平台
  - SQL 注入
  - XSS
  - SSTI
  - SSRF
  - 越权（水平 / 垂直）
  - 文件上传
  - 支付逻辑漏洞
  - 代码 / 命令注入
  - XXE
  - JSONP
  - 条件竞争

## 推荐使用方式

优先使用统一版：

```bash
cd web-fieldlab
cp .env.example .env
docker compose up --build
```

默认访问：

- http://127.0.0.1:5070

## 目录结构

```text
KanXueCourse/
└── web-fieldlab/
```

## 说明

该仓库用于本地教学与授权实验环境。
