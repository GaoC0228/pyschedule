# 审计存档目录

此目录用于存储审计日志相关的归档文件。

## 目录结构

```
audit_archives/
├── logs/       # 脚本执行日志文件
├── outputs/    # 脚本输出文件（CSV、Excel等）
└── scripts/    # 脚本快照备份
```

## 文件命名规则

格式: `{YYYYMMDD}_{user_id}_{uuid}_{original_name}`

示例: `20251204_1_a1b2c3d4-5e6f_report.csv`

## 注意事项

- 文件实行逻辑删除，不会物理删除
- 定期清理策略：保留365天
- 文件大小限制：单文件最大100MB
