# Reset 指南

## 全量重置

```bash
./scripts/reset_lab.sh all
```

## 局部重置

```bash
./scripts/reset_lab.sh stored-comments
./scripts/reset_lab.sh second-order-signature
./scripts/reset_lab.sh markdown-preview
./scripts/reset_lab.sh svg-preview
./scripts/reset_lab.sh url-bookmarks
./scripts/reset_lab.sh events
```

## 建议
- 课堂开始前执行一次全量 reset
- 存储型与二次 XSS 关卡讲完后执行一次局部 reset
