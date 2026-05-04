# Reset 指南

## 全量

```bash
./scripts/reset_lab.sh all
```

## SQLi

```bash
./scripts/reset_lab.sh sqli
./scripts/reset_lab.sh sqli-grades
./scripts/reset_lab.sh sqli-filters
```

## XSS / SSTI / SSRF / 越权

```bash
./scripts/reset_lab.sh xss
./scripts/reset_lab.sh ssti
./scripts/reset_lab.sh ssrf
./scripts/reset_lab.sh authz
```

## 细粒度

```bash
./scripts/reset_lab.sh stored-comments
./scripts/reset_lab.sh second-order-signature
./scripts/reset_lab.sh markdown-preview
./scripts/reset_lab.sh svg-preview
./scripts/reset_lab.sh url-bookmarks
./scripts/reset_lab.sh ssti-mail
./scripts/reset_lab.sh ssti-theme
./scripts/reset_lab.sh authz-orders
./scripts/reset_lab.sh authz-notes
./scripts/reset_lab.sh authz-tickets
./scripts/reset_lab.sh events
```
