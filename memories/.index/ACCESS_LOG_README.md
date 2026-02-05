# Access Log

记忆访问日志，用于追踪每个记忆片段的访问历史和重要性。

## Schema

| Field | Type | Description |
|-------|------|-------------|
| `last_access` | ISO 8601 datetime | 最后访问时间 |
| `access_count` | int | 累计访问次数 |
| `base_importance` | float | 基础重要性评分 (0.0-1.0)，默认 0.5 |
| `created_at` | ISO 8601 datetime | 首次记录时间 |

## 重要性计算公式

```
importance = (
    0.30 * recency_factor +      # 时间衰减: 0.5^(days/7)
    0.20 * access_frequency +     # 访问频率: min(1.0, log(count+1)/5)
    0.20 * semantic_similarity +  # 语义相关性
    0.20 * base_importance +      # 基础评分
    0.10 * context_relevance     # 上下文相关
)
```

## 维护

- 最大条目数：10,000（FIFO 淘汰最旧的）
- 最小重要性阈值：0.1（永不删除）
- 损坏时自动重建空日志
