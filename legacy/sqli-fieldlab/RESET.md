# Reset 指南

## 全量重置

适用：需要把数据库卷彻底清空，恢复到初始种子状态。

```bash
./scripts/reset_lab.sh all
```

这会执行：
- `docker compose down -v`
- `docker compose up -d --build`

## 局部重置

### 重置成绩相关数据

适用关卡：
- `L06 审计报表堆叠查询`
- `L09 成绩调整 UPDATE 注入`

```bash
./scripts/reset_lab.sh grade-editor
./scripts/reset_lab.sh report-stacked
```

### 重置二次注入保存数据

适用关卡：
- `L07 二次注入：保存筛选器`

```bash
./scripts/reset_lab.sh second-order
```

## 建议

- 每轮学生练习结束后，至少执行一次局部 reset。
- 一节课开始前，建议执行一次全量 reset，保证所有学生看到的是一致初始状态。
