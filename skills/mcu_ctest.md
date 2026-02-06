# MCU CTest 覆盖率提升

**专属仓库**: `/home/sanmu/MyProject/mcu_ctest/autosar-mcu`

---

## 0. 快速上手

```bash
# 1. 查看目标文件当前覆盖率（使用 tool）
mcu_coverage_report(file="<模块名>.c")

# 2. 创建/编辑测试文件
vim tests/<模块>_coverage.c

# 3. 快速编译验证
cd /home/sanmu/MyProject/mcu_ctest/autosar-mcu/build
cmake --build . --target cunit_Ddscp -j4 && ./bin/cunit_Ddscp -s <suite>

# 4. 完整测试（耗时 2-5 分钟，用户执行，日志重定向避免污染上下文）
cd /home/sanmu/MyProject/mcu_ctest/autosar-mcu
./scripts/test.sh --COVERAGE=on > /tmp/mcu_test.log 2>&1; echo "Exit code: $?"
# Exit code 0 = 成功，非 0 = 失败（用 tail -100 /tmp/mcu_test.log 查看错误）

# 5. 验证覆盖率
mcu_coverage_report(file="<模块名>.c")
```

---

## 1. 命令与目标

### 1.1 触发命令

```
/mcu_ctest <源文件路径> [档位]
```

| 参数 | 说明 |
|------|------|
| `<源文件路径>` | 必填，要提升覆盖率的源文件 |
| `[档位]` | 可选：`low`、`mid`（默认）、`high` |

**示例**：
```bash
/mcu_ctest src/CDD/CDD_Dds/core/ddsi/src/ddsi_ownip.c          # 默认 mid
/mcu_ctest src/CDD/CDD_Dds/core/ddsi/src/ddsi_ownip.c low      # 60%
/mcu_ctest src/CDD/CDD_Dds/core/ddsi/src/ddsi_ownip.c high     # 90%
```

### 1.2 覆盖率目标

| 档位 | 行覆盖率 | 函数覆盖率 | 分支覆盖率 | 适用场景 |
|------|----------|------------|------------|----------|
| `low` | 60% | 70% | 50% | 快速提升、初步覆盖 |
| `mid` | 75% | 85% | 65% | 中等要求（默认） |
| `high` | 90% | 95% | 80% | 高要求、核心模块 |

### 1.3 源码修改红线

> ⚠️ **禁止修改源码**（除以下两种情况外）

| 允许的修改 | 说明 |
|------------|------|
| `static` → `STATIC` | 将原生静态函数改为 STATIC 宏，使其可测试 |
| Bug 修复 | 发现源码 bug 时可修复 |

**禁止**：
- ❌ 添加测试包装函数
- ❌ 修改函数签名
- ❌ 添加条件编译 `#ifdef TEST`
- ❌ 任何其他"为了测试方便"的源码改动

**测试代码的正确做法**：
- 使用 `#include "源文件.c"` 访问静态函数
- 使用 `extern` 声明 STATIC 函数
- 使用 Stub 框架模拟依赖

---

## 2. 核心概念

### 2.1 函数类型与测试方法

| 函数类型 | 定义方式 | 测试方法 | 优先级 |
|----------|----------|----------|--------|
| **STATIC 宏函数** | `STATIC void func()` | extern 声明直接调用 | **首选** |
| **原生静态函数** | `static void func()` | #include 源文件 | 备选 |
| **Inline 函数** | 头文件中定义 | #include 头文件 | - |
| **普通函数** | 公共头文件声明 | 直接调用 | - |

### 2.2 STATIC 宏机制

源码使用 `STATIC` 宏代替 `static`（定义于 `ddsrt_assert.h`）：

```c
#if DDSRT_WITH_TEST
  #define STATIC        // 测试模式：变成全局可见
#else
  #define STATIC static // 生产模式：正常静态
#endif
```

测试时 CMake 自动定义 `DDSRT_WITH_TEST=1`，STATIC 函数变成全局符号。

### 2.3 测试文件命名规则

| 后缀 | 用途 | 示例 |
|------|------|------|
| `_test.c` | 功能测试、API 测试 | `ddsi_ownip_test.c` |
| `_coverage.c` | 覆盖率补充、边界测试 | `dds_topic_coverage.c` |
| `_inline.c` | 内联函数测试 | `entity_inline.c` |
| `_static_test.c` | 静态函数专项测试 | `q_entity_static_test.c` |

### 2.4 测试用例命名规范

> ⚠️ **防止重名**：Suite 和 Test 名称在整个项目中必须唯一

```c
CU_Test(suite_name, test_name)
```

**命名规则**：

| 组成部分 | 格式 | 示例 |
|----------|------|------|
| `suite_name` | `<模块>_<类型>` | `ddsi_ownip_coverage`, `q_entity_static` |
| `test_name` | `<函数>_<场景>` | `count_commas_empty`, `parse_config_null_input` |

**完整示例**：
```c
// 模块: ddsi_ownip, 类型: coverage
// 函数: count_commas, 场景: empty string
CU_Test(ddsi_ownip_coverage, count_commas_empty)

// 模块: q_entity, 类型: static (静态函数测试)
// 函数: validate_qos, 场景: invalid policy
CU_Test(q_entity_static, validate_qos_invalid_policy)
```

**常见场景后缀**：
- `_null` / `_null_input` - 空指针输入
- `_empty` - 空字符串/空数组
- `_overflow` - 边界溢出
- `_error` / `_fail` - 错误路径
- `_success` / `_normal` - 正常路径

---

## 3. 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: 分析覆盖率报告                                      │
│   └─ 定位未覆盖行/分支/函数                                   │
├─────────────────────────────────────────────────────────────┤
│ Phase 2: 确定测试策略                                        │
│   └─ 根据函数类型选择测试方法                                 │
├─────────────────────────────────────────────────────────────┤
│ Phase 3: 编写测试用例                                        │
│   └─ 按模板编写，使用 stub 模拟依赖                           │
├─────────────────────────────────────────────────────────────┤
│ Phase 4: 单独编译验证（快速迭代）                             │
│   └─ cmake --build → 运行单个 suite                          │
├─────────────────────────────────────────────────────────────┤
│ Phase 5: 完整测试生成覆盖率                                   │
│   └─ ./scripts/test.sh --COVERAGE=on                        │
├─────────────────────────────────────────────────────────────┤
│ Phase 6: 验证达标                                            │
│   └─ 查看 public/codecov.*.html，未达标返回 Phase 1          │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Phase 1: 分析覆盖率报告

### 4.1 使用 mcu_coverage_report 工具（推荐）

> ⚠️ **必须使用此工具**：避免手动解析 HTML，减少上下文污染

```
mcu_coverage_report(file="ddsi_ownip.c")
```

**输出示例**：
```json
{
  "file": "src/CDD/CDD_Dds/core/ddsi/src/ddsi_ownip.c",
  "report_path": "public/codecov.ddsi_ownip.c.xxx.html",
  "line_coverage": 97.1,
  "function_coverage": 100.0,
  "branch_coverage": 88.3,
  "uncovered_line_count": 3,
  "uncovered_branch_count": 5,
  "uncovered_lines": [
    {"line": 238, "source": "return 0;"},
    {"line": 263, "source": "if (!gv->using_link_local_intf)"}
  ],
  "uncovered_branches": [
    {"line": 142, "branch": "1", "info": "Branch 1 not taken."}
  ]
}
```

**直接获得**：
- 覆盖率百分比（行/函数/分支）
- 未覆盖行号 + 源码片段
- 未覆盖分支位置

### 4.2 手动定位（备用）

```bash
# 源文件 → 报告文件映射
ls public/codecov.*<模块名>*.html

# 提取未覆盖行号
grep -B1 'uncoveredLine' public/codecov.<文件>.*.html | grep 'lineno'
```

### 4.3 优先级排序

1. **未覆盖函数** - 整个函数未被调用（最高优先）
2. **错误处理分支** - `if (error)` / `return -1`
3. **NULL 检查** - 参数校验分支
4. **边界条件** - 空数组、最大值、溢出
5. **else 分支** - 被忽略的反向逻辑
6. **switch default** - 未匹配的 case

---

## 5. Phase 2: 确定测试策略

### 5.1 决策树

```
目标函数是什么类型？
│
├─ STATIC 宏函数 (`STATIC void func()`)
│   └─ ✅ 直接 extern 声明调用（推荐）
│      - 无需 #include 源文件
│      - 避免符号冲突
│
├─ 原生静态函数 (`static void func()`)
│   └─ ⚠️ #include 源文件
│      - 一个测试文件只包含一个 .c 文件
│      - 注意符号冲突
│
├─ Inline 函数（头文件定义）
│   └─ ✅ #include 头文件直接调用
│      - 测试文件命名 xxx_inline.c
│
└─ 普通公共函数
    └─ ✅ 通过公共 API 调用
       - 无需特殊处理
```

### 5.2 查找已有测试文件

```bash
ls tests/*<模块名>*.c
grep -l "include.*<模块名>" tests/*.c
```

**决策规则**：
- 已有 `_test.c` → 追加到该文件
- 已有 `_coverage.c` → 追加到该文件
- 都没有 → 创建新的 `<模块>_coverage.c`

---

## 6. Phase 3: 编写测试用例

### 6.1 测试 STATIC 宏函数（推荐）

```c
#include "CUnit/Test.h"
#include "dds.h"
#include "stub.h"

/* 直接声明 STATIC 函数（测试模式下已变成全局符号） */
extern void instance_deadline_missed_cb(struct xevent *xev, void *varg, ddsrt_mtime_t tnow);

CU_Test(ddsi_deadline, test_callback)
{
    /* 直接调用，无需 #include 源文件 */
    instance_deadline_missed_cb(NULL, NULL, now);
    CU_ASSERT_TRUE(1);
}
```

### 6.2 测试原生静态函数（备用）

```c
#include <stdint.h>
#include <string.h>
#include "CUnit/Test.h"
#include "dds.h"
#include "stub.h"

/* 最后包含源文件以访问静态函数 */
#include "../src/CDD/CDD_Dds/core/ddsi/src/ddsi_ownip.c"

CU_Test(ddsi_ownip, test_count_commas)
{
    size_t result = count_commas("a,b,c");  /* 静态函数 */
    CU_ASSERT_EQUAL(result, 2);
}
```

### 6.3 测试 Inline 函数

```c
#include "CUnit/Test.h"
#include "q_bitset.h"  /* 包含 inline 函数定义的头文件 */

CU_Test(q_bitset_inline, isset_out_of_range)
{
    uint32_t bits[2] = {0xFFFFFFFF, 0xFFFFFFFF};
    bool result = nn_bitset_isset(64, bits, 100);  /* inline 函数 */
    CU_ASSERT_FALSE(result);
}
```

### 6.4 完整测试文件模板

```c
/*
 * Copyright(c) 2021-2023 AutoCore Technology (Nanjing) Co., Ltd.
 */

/* ===== 1. 标准库 ===== */
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

/* ===== 2. CUnit ===== */
#include "CUnit/Test.h"

/* ===== 3. 项目头文件 ===== */
#include "dds.h"
#include "dds__types.h"

/* ===== 4. Stub 框架 ===== */
#include "stub.h"

/* ===== 5. STATIC 函数声明（如需要） ===== */
extern void some_static_function(int param);

/* ===== 6. 或包含源文件（原生 static 时） ===== */
// #include "../src/CDD/CDD_Dds/path/to/module.c"

/* ===== 7. Stub 定义 ===== */
static int g_stub_result = 0;
static int stub_dependency(int x) {
    return g_stub_result;
}

/* ===== 8. 测试用例 ===== */
CU_Test(module_name, normal_case)
{
    int result = function_under_test(42);
    CU_ASSERT_EQUAL(result, EXPECTED);
}

CU_Test(module_name, error_path)
{
    g_stub_result = -1;
    void *stub = set_stub((void *)dependency, (void *)stub_dependency);
    
    int result = function_under_test(0);
    
    unset_stub(stub);
    CU_ASSERT_EQUAL(result, ERROR_CODE);
}
```

---

## 7. Stub 使用指南

### 7.1 基本 API

```c
void *set_stub(void *func, void *func_stub);  // 替换函数，返回句柄
void unset_stub(void *stub);                   // 恢复原函数
```

### 7.2 实现原理

运行时修改函数入口机器码：
1. `mprotect()` 修改内存页为可写
2. 写入跳转指令到 stub 函数
3. 恢复内存保护

**限制**：
- 支持 x86_64、ARM、ARM64、MIPS64
- 函数签名必须完全一致
- 不支持已内联的函数

### 7.3 常用模式

**错误注入**：
```c
static int g_fail = 0;
static void *stub_malloc(size_t size) {
    return g_fail ? NULL : malloc(size);
}
```

**调用计数**：
```c
static int g_count = 0;
static void stub_callback(void) { g_count++; }
```

**参数捕获**：
```c
static int g_captured = 0;
static void stub_func(int x) { g_captured = x; }
```

### 7.4 多 Stub 管理

```c
/* LIFO 顺序：先设置的后恢复 */
void *s1 = set_stub((void *)f1, (void *)stub1);
void *s2 = set_stub((void *)f2, (void *)stub2);

/* 执行测试 */

unset_stub(s2);  /* 后进先出 */
unset_stub(s1);
```

---

## 8. CUnit 断言速查

```c
CU_ASSERT_EQUAL(actual, expected)      // 整数相等
CU_ASSERT_NOT_EQUAL(a, b)              // 不等
CU_ASSERT_TRUE(condition)              // 真
CU_ASSERT_FALSE(condition)             // 假
CU_ASSERT_PTR_NULL(ptr)                // 空指针
CU_ASSERT_PTR_NOT_NULL(ptr)            // 非空
CU_ASSERT_STRING_EQUAL(s1, s2)         // 字符串相等
CU_ASSERT_FATAL(condition)             // 失败则停止
```

---

## 9. Phase 4: 单独编译验证

### 9.1 添加到 CMakeLists.txt

```cmake
# tests/CMakeLists.txt
set(test_sources
    # ... 现有测试 ...
    your_new_test.c    # 新增
)
```

### 9.2 编译运行

```bash
cd /home/sanmu/MyProject/mcu_ctest/autosar-mcu

# 首次或需要重建
rm -rf build && mkdir build && cd build
cmake -DBUILD_TESTING=ON ..

# 编译
cmake --build . --target cunit_Ddscp -j4

# 运行特定 suite
./bin/cunit_Ddscp -s <suite_name>

# 运行所有测试
./bin/cunit_Ddscp
```

---

## 10. Phase 5: 完整测试生成覆盖率

> ⚠️ **耗时 2-5 分钟**，必须在 Phase 4 通过后才运行！
> 
> ⚠️ **此步骤由用户执行**，AI 等待结果即可。

### 10.1 执行命令（避免日志污染上下文）

```bash
cd /home/sanmu/MyProject/mcu_ctest/autosar-mcu
./scripts/test.sh --COVERAGE=on > /tmp/mcu_test.log 2>&1; echo "Exit code: $?"
```

### 10.2 结果处理

| Exit code | 含义 | AI 操作 |
|-----------|------|---------|
| `0` | 成功 | 调用 `mcu_coverage_report(file="<目标文件>")` 查看覆盖率 |
| 非 `0` | 失败 | 读取日志尾部定位错误：`tail -100 /tmp/mcu_test.log` |

**失败时的排查顺序**：
1. `tail -100 /tmp/mcu_test.log` - 查看最后的错误
2. `grep -i "error\|fail" /tmp/mcu_test.log | tail -20` - 提取错误关键词
3. 根据错误修复后重新执行

---

## 11. Phase 6: 验证达标

### 11.1 使用 tool 验证（推荐）

```
mcu_coverage_report(file="<目标文件>.c")
```

对比输出的 `line_coverage`、`function_coverage`、`branch_coverage` 与目标档位。

### 11.2 手动验证（备用）

```bash
xdg-open public/codecov.<文件>.*.html
```

**未达标** → 返回 Phase 1 继续补充测试

---

## 12. 多进程集成测试

某些代码路径无法通过单元测试覆盖，需要多进程测试。

### 12.1 现有示例

位置：`examples/multiproc_test/`

| 文件 | 用途 |
|------|------|
| `multiproc_pub.c` | 发布者进程 |
| `multiproc_sub.c` | 订阅者进程 |
| `run_multiproc_test.sh` | 运行脚本 |

### 12.2 运行方式

已集成到 `./scripts/test.sh --COVERAGE=on`，自动运行。

手动运行：
```bash
./examples/multiproc_test/run_multiproc_test.sh
```

### 12.3 覆盖的代码路径

- 代理实体发现：`dds_get_matched_*`
- RHC 读写：`dds_read`, `dds_take`
- 实例/样本/视图状态
- 消息分片

---

## 13. 常见问题

| 问题 | 解决方案 |
|------|----------|
| 测试编译失败 | 检查头文件顺序、符号冲突、CMakeLists.txt |
| Stub 不生效 | 函数签名必须完全一致，确保调用 unset_stub |
| 覆盖率没提升 | 确认测试执行了，确认重新运行了 test.sh |
| 找不到 STATIC 函数 | 用 extern 声明，CMake 会自动定义 DDSRT_WITH_TEST |

### 13.1 何时接受无法覆盖

某些代码路径在 Linux 测试环境下**确实无法覆盖**，应当接受并停止尝试：

| 无法覆盖的情况 | 原因 | 处理方式 |
|----------------|------|----------|
| 硬件寄存器操作 | 无真实硬件 | 接受，记录原因 |
| 中断处理程序 | Linux 无法触发 MCU 中断 | 接受 |
| 平台特定代码 `#ifdef MCU_PLATFORM` | 编译时排除 | 接受 |
| 防御性断言 `assert(false)` | 设计上不应到达 | 接受 |
| 极端竞态条件 | 无法稳定复现 | 接受，但尝试多进程测试 |

**判断标准**：
- ✅ 尝试过 Stub 模拟但仍无法触发 → 可接受
- ✅ 需要修改源码才能测试 → 可接受（禁止改源码）
- ❌ 只是"比较难写测试" → 不可接受，继续努力

**记录方式**：
向用户报告时说明：
> "以下 N 行/分支无法在 Linux 环境覆盖：[原因]。当前覆盖率 X% 已是该文件可达上限。"

---

## 14. 闭环条件

### 14.1 覆盖率达标

| 档位 | 行 | 函数 | 分支 |
|------|-----|------|------|
| `low` | >= 60% | >= 70% | >= 50% |
| `mid` | >= 75% | >= 85% | >= 65% |
| `high` | >= 90% | >= 95% | >= 80% |

### 14.2 通用条件

- [ ] 新增测试编译通过
- [ ] 新增测试运行通过
- [ ] 完整测试通过
- [ ] 未破坏已有测试

---

## 15. 参考资源

| 资源 | 路径 |
|------|------|
| 仓库规范 | `CLAUDE.md` |
| 模板测试 | `tests/ddsi_ownip_test.c` (950行) |
| 简洁示例 | `tests/ddsi_mcgroup.c` (123行) |
| Stub 实现 | `tests/stub/stub.h` |
| 多进程测试 | `examples/multiproc_test/` |
| 覆盖率报告 | `public/codecov.html` |
