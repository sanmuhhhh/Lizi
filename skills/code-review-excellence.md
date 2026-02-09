---
name: code-review-excellence
description: DDS 代码审查技能。审查 AutoCoreDDS MR/PR 时加载，按固定流程产出结构化报告。
---

# DDS 代码审查

按以下四个阶段顺序执行，最终输出固定格式报告。

---

## Phase 1：读懂变更

```bash
# 查看提交信息
git log --oneline -10

# 查看具体改动
git diff HEAD~1 --stat
git diff HEAD~1
```

需要明确：
- 这次变更的**意图**（新功能 / Bug 修复 / 重构 / 性能优化）
- **涉及哪些模块**（ddsc / ddsi / ddsrt / security / rpc ...）
- 改动规模（行数、文件数）

> 如果提交信息不清晰，在报告中标注"提交信息不足"。

---

## Phase 2：基础代码质量

不需要查规范，凭代码常识检查：

**内存安全**
- malloc/free 是否配对
- 样本 loan 后是否归还（`dds_return_loan`）
- 指针使用前是否判空

**错误处理**
- `dds_return_t` 返回值是否检查
- 错误路径是否有资源泄漏（Entity 未 delete）
- 错误码是否向上传递而非被吞掉

**并发安全**
- 多线程访问 Entity 是否有锁保护
- Listener 回调中是否有死锁风险（持锁期间调用用户代码）
- 回调中是否直接删除 Entity（危险，应延迟）

**可读性**
- 变量名是否区分 Writer/Reader 侧语义
- 魔法数字是否应提取为常量
- 复杂逻辑是否有注释

---

## Phase 3：DDS 规范合规

代码审查必须检查规范合规性。根据改动模块，查阅 `./dds_spec/` 中对应章节：

| 涉及内容 | 查阅规范 |
|----------|----------|
| Discovery 流程（SPDP/SEDP） | `RTPS2.5_full.md` §8.5 |
| HEARTBEAT / ACKNACK / GAP 处理 | `RTPS2.5_full.md` §8.4 |
| QoS 兼容性判断逻辑 | `OMG_DDS_1.4_full.md` §2.2.3 |
| Serialization / TypeObject | `dds_xtypes_1.3_full.md` |
| Security 插件接口 | `dds_security_full.md` |
| RPC 请求-应答关联 | `DDS_RPC_full.md` |
| IDL 生成代码正确性 | `IDL_4.2_full.md` |

检查重点：
- 协议状态机流转是否符合规范
- QoS 兼容性：offered >= requested（方向和规则见附录）
- RTPS 序列号单调递增，不能回绕
- GUID 在 Participant 范围内唯一
- `RESOURCE_LIMITS` 与 `HISTORY` depth 一致（depth ≤ max_samples_per_instance）

引用规范时标注章节，例如：`RTPS 2.5 §8.4.7.2`。

---

## Phase 4：输出报告

严格按以下格式输出，不增减章节：

```
## 代码审查报告

**提交**：<commit hash> - <提交信息>
**变更范围**：<涉及模块> | <+X行 -Y行>
**变更类型**：新功能 / Bug修复 / 重构 / 性能优化

---

### 🔴 阻塞问题（必须修复）

<!-- 无则写"无" -->

🔴 [blocking] <问题描述>
位置：`<文件路径>:<行号>`
规范依据：<规范名 §章节>（如无规范依据则省略此行）
建议：<具体修改方案>

---

### 🟡 重要问题（应当修复）

<!-- 无则写"无" -->

🟡 [important] <问题描述>
位置：`<文件路径>:<行号>`
建议：<具体修改方案>

---

### 🟢 建议优化（不阻塞）

<!-- 无则写"无" -->

🟢 [nit] <建议>

---

### 🎉 值得肯定

<!-- 无则省略本节 -->

---

### 结论

**审查结论**：✅ 通过 / 🔄 修改后通过 / ❌ 需重大修改

**规范合规检查**：已执行（查阅章节：<列出实际查阅的规范章节>）

**说明**：<一句话总结主要问题或肯定点>
```

---

## 附录：QoS 兼容性速查

| QoS 策略 | 兼容规则 |
|----------|----------|
| `RELIABILITY` | offered ≥ requested（RELIABLE > BEST_EFFORT）|
| `DURABILITY` | offered ≥ requested（PERSISTENT > TRANSIENT > TRANSIENT_LOCAL > VOLATILE）|
| `DEADLINE` | offered.period ≤ requested.period |
| `LIVELINESS` | offered ≥ requested，且 offered.lease ≤ requested.lease |
| `OWNERSHIP` | 必须相同 |
| `PARTITION` | 交集非空 |

## 附录：常见 Bug 模式

**QoS 创建时机错误**
```c
// 错误：Entity 创建后再设置 QoS 对部分策略无效
dds_entity_t writer = dds_create_writer(pub, topic, NULL, NULL);
// 正确：创建时传入
dds_qos_t *qos = dds_create_qos();
dds_qset_reliability(qos, DDS_RELIABILITY_RELIABLE, DDS_MSECS(100));
dds_entity_t writer = dds_create_writer(pub, topic, qos, NULL);
dds_delete_qos(qos);
```

**Listener 回调中删除 Entity（死锁）**
```c
// 错误
void on_data_available(dds_entity_t reader, void *arg) {
    dds_delete(reader);  // 持锁期间再获锁，死锁
}
// 正确：通过标志位让主线程延迟删除
void on_data_available(dds_entity_t reader, void *arg) {
    atomic_store(&should_delete, true);
}
```

**RESOURCE_LIMITS 与 HISTORY 不一致**
```c
// 错误：实际 depth = min(100, 5) = 5，与预期不符
dds_qset_history(qos, DDS_HISTORY_KEEP_LAST, 100);
dds_qset_resource_limits(qos, 10, DDS_LENGTH_UNLIMITED, 5);
// 正确
dds_qset_history(qos, DDS_HISTORY_KEEP_LAST, 5);
dds_qset_resource_limits(qos, 50, DDS_LENGTH_UNLIMITED, 5);
```
