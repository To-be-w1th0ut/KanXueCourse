# KanXueCourse

这是一个统一的 Web 漏洞教学项目仓库，包含：

- `web-fieldlab/`：统一版教学平台
  - SQL 注入
  - XSS
  - SSTI
  - SSRF
  - 越权（水平 / 垂直）
- `legacy/sqli-fieldlab/`：早期独立 SQLi 靶场
- `legacy/xss-fieldlab/`：早期独立 XSS 靶场

## 推荐使用

优先使用统一版：

```bash
cd web-fieldlab
cp .env.example .env
docker compose up --build
```

默认访问：

- http://127.0.0.1:5070

## 目录说明

```text
KanXueCourse/
├── web-fieldlab/
└── legacy/
    ├── sqli-fieldlab/
    └── xss-fieldlab/
```

## 说明

该仓库用于本地教学与授权实验环境。
