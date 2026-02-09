# MCU CTest 覆盖率提升

**专属仓库**: `/home/sanmu/MyProject/mcu_ctest/autosar-mcu`

---

## 0. 工作流程

1. 查看当前覆盖率 → 定位未覆盖行/分支
2. 查找相关测试文件 → 确定追加位置
3. 编写测试用例 → 使用 stub 模拟依赖
4. 快速编译验证 → 确认测试通过
5. 完整测试 + 覆盖率 → 验证达标

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

### 4.1 使用 mcu_coverage_report 工具

使用注册的 `mcu_coverage_report` 工具查看覆盖率，返回结构化数据包含：
- 覆盖率百分比（行/函数/分支）
- 未覆盖行号 + 源码片段 + 上下文
- 未覆盖分支 + 所在函数名

### 4.3 优先级排序

1. **未覆盖函数** - 整个函数未被调用（最高优先）
2. **错误处理分支** - `if (error)` / `return -1`
3. **NULL 检查** - 参数校验分支
4. **边界条件** - 空数组、最大值、溢出
5. **else 分支** - 被忽略的反向逻辑
6. **switch default** - 未匹配的 case

### 4.4 未覆盖代码分析决策树

```
未覆盖行/分支是什么类型？
│
├─ 条件分支（if/else/switch）
│   ├─ 错误返回路径（return -1, goto err）
│   │   └─ Stub 依赖函数返回错误
│   │      例: stub_malloc() 返回 NULL
│   │
│   ├─ NULL 检查分支
│   │   └─ 传入 NULL 参数触发
│   │
│   ├─ 边界条件（size == 0, overflow）
│   │   └─ 构造边界输入值
│   │
│   └─ 短路求值分支（&& / ||）
│       └─ 通常需要多个测试覆盖不同组合
│          注意: gcov 对 `a && b` 生成 4 个分支
│
├─ 错误处理标签（err_xxx:, cleanup:）
│   └─ 需要触发前面的错误路径
│      可能需要 Stub 多个函数
│
├─ 初始化代码（仅首次执行）
│   └─ 确保测试环境未预初始化
│      可能需要隔离测试进程
│
└─ 无法测试的代码
    ├─ 硬件依赖 → 接受，记录原因
    ├─ 平台特定 #ifdef → 接受
    ├─ Stub 会导致死锁/崩溃 → 接受，记录原因
    └─ 防御性代码（assert/unreachable）→ 接受
```

**分支类型速查**：

| 代码模式 | gcov 分支数 | 覆盖方法 |
|----------|-------------|----------|
| `if (a)` | 2 | true/false 各一个测试 |
| `if (a && b)` | 4 | a=false; a=true,b=false; a=true,b=true; 短路 |
| `if (a \|\| b)` | 4 | 同上，短路逻辑相反 |
| `a ? b : c` | 2 | true/false 各一个测试 |
| `switch(x)` | N+1 | 每个 case + default |

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

使用 `mcu_find_test_file` 工具查找相关测试文件。

**决策规则**：
- 已有 `_test.c` → 追加到该文件
- 已有 `_coverage.c` → 追加到该文件
- 都没有 → 创建新的 `<模块>_coverage.c`

### 5.3 Source Include 限制

> ⚠️ **在 `#include "源文件.c"` 后定义的测试可能无法正确注册**

**问题现象**：
- 符号存在于二进制中（`nm` 可见）
- 但 `-t <test_name>` 无法运行
- `-s <suite>` 显示 0 tests ran

**原因**：
CUnit 的 `CU_Test` 宏在编译时展开为静态构造函数。当 `#include` 源文件时，源文件中的符号可能与测试文件的符号发生冲突或覆盖，导致测试注册失败。

**解决方案**：

| 优先级 | 方案 | 适用场景 |
|--------|------|----------|
| 1 | 使用 extern 声明 STATIC 函数 | 函数已用 STATIC 宏 |
| 2 | 将测试定义在 include 之前 | 必须 include 源文件时 |
| 3 | 使用独立测试文件 | 避免符号污染 |

**验证测试是否正确注册**：
```bash
mcu_list_tests(suite_filter="<你的suite名>")
```

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

### 7.5 Stub 安全性参考

> ⚠️ **某些函数 Stub 后会导致死锁或崩溃**

**已知可安全 Stub 的函数**：

| 函数 | 用途 | 示例 |
|------|------|------|
| `malloc` / `ddsrt_malloc` | 内存分配失败注入 | 返回 NULL 测试错误路径 |
| `free` / `ddsrt_free` | 跟踪释放调用 | 验证资源清理 |
| `ddsrt_getenv` | 环境变量模拟 | 配置测试 |
| `ddsrt_gethostname` | 主机名模拟 | 网络相关测试 |
| `entidx_lookup_*` | 实体查找返回 NULL | 测试查找失败路径 |
| `dds_create_*` | 创建函数失败 | 测试级联错误处理 |

**已知不可安全 Stub 的函数**：

| 函数 | 风险 | 替代方案 |
|------|------|----------|
| `pthread_mutex_lock/unlock` | 死锁 | 无，接受无法覆盖 |
| `ddsrt_mutex_*` | 死锁（内部使用 pthread） | 无 |
| `dds_entity_init` | 锁初始化问题导致挂起 | 测试更上层函数 |
| `signal` / 信号处理 | 进程崩溃 | 多进程测试 |
| 已内联的函数 | Stub 无效 | 无法 Stub |
| 递归调用的函数 | 栈溢出 | 仔细设计 Stub 逻辑 |
| `nn_xmsg_new` | 崩溃 | 被广泛调用，包括清理路径 |
| `nn_xmsg_free` | 崩溃 | 内存管理核心函数 |
| `nn_xpack_*` | 崩溃 | 消息打包核心路径 |
| `new_*` 系列函数 | 无效 | 需要多进程测试，无法单元测试 |
| `proxy_*` 系列函数 | 无效 | 代理实体需要远程对端 |

**判断函数是否可 Stub**：

```
1. 函数是否涉及锁操作？
   └─ 是 → ❌ 不要 Stub
   
2. 函数是否被 inline？
   └─ 检查头文件，有 inline 关键字 → ❌ 无法 Stub
   
3. Stub 后是否会形成递归？
   └─ Stub 函数内部调用了原函数 → ❌ 栈溢出
   
4. 参考已有测试中的 Stub 用法
   └─ grep -r "set_stub.*函数名" tests/
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

使用 `mcu_build_and_coverage` 或 `mcu_run_single_test` 工具。

**手动方式（备用）**：
```bash
cd /home/sanmu/MyProject/mcu_ctest/autosar-mcu/build
cmake --build . --target cunit_Ddscp -j4
./bin/cunit_Ddscp -s <suite_name>
```

---

## 10. Phase 5: 完整测试生成覆盖率

> ⚠️ **耗时 2-5 分钟**，必须在 Phase 4 通过后才运行！

使用 `mcu_build_and_coverage` 工具一键完成编译、测试、覆盖率报告。

**手动执行（备用）**：
```bash
cd /home/sanmu/MyProject/mcu_ctest/autosar-mcu
./scripts/test.sh --COVERAGE=on > /tmp/mcu_test.log 2>&1; echo "Exit code: $?"
```

---

## 11. Phase 6: 验证达标

使用 `mcu_coverage_report` 或 `mcu_build_and_coverage` 返回的覆盖率数据，对比目标档位。

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
- `new_*` 函数（如 `new_nn_xpack`, `new_writer`）
- `proxy_*` 代理实体操作

### 12.4 多进程测试编写指南

**适用场景**：
- `new_*` 路径（需要远程对端触发）
- 跨进程通信路径
- 代理实体发现和匹配
- 消息可靠传输重传逻辑

**添加新测试步骤**：

1. **发布端** (`multiproc_pub.c`)：
```c
// 在 run_pub_tests() 中添加新场景
void test_your_scenario(dds_entity_t participant) {
    dds_entity_t topic = dds_create_topic(participant, ...);
    dds_entity_t writer = dds_create_writer(participant, topic, ...);
    
    // 发送数据触发目标代码路径
    YourType sample = {...};
    dds_write(writer, &sample);
    
    // 等待订阅端确认
    dds_sleepfor(DDS_MSECS(100));
}
```

2. **订阅端** (`multiproc_sub.c`)：
```c
// 在 run_sub_tests() 中添加对应验证
void verify_your_scenario(dds_entity_t participant) {
    dds_entity_t topic = dds_create_topic(participant, ...);
    dds_entity_t reader = dds_create_reader(participant, topic, ...);
    
    // 等待并读取数据
    void *samples[1];
    dds_sample_info_t infos[1];
    int32_t n = dds_take(reader, samples, infos, 1, 1);
    assert(n == 1);
}
```

3. **更新运行脚本** (`run_multiproc_test.sh`)：
```bash
# 如果需要特殊参数，在脚本中添加
```

4. **运行验证**：
```bash
./examples/multiproc_test/run_multiproc_test.sh
./scripts/test.sh --COVERAGE=on  # 检查覆盖率提升
```

---

## 13. 常见问题

| 问题 | 解决方案 |
|------|----------|
| 测试编译失败 | 检查头文件顺序、符号冲突、CMakeLists.txt |
| Stub 不生效 | 函数签名必须完全一致，确保调用 unset_stub |
| 覆盖率没提升 | 确认测试执行了，确认重新运行了 test.sh |
| 找不到 STATIC 函数 | 用 extern 声明，CMake 会自动定义 DDSRT_WITH_TEST |
| mcu_coverage_report 返回错误的上下文 | 确保查看的是源文件覆盖率，工具会排除 tests 目录 |
| mcu_list_tests file_filter 返回空 | 改用 suite_filter 参数按 suite 名匹配 |
| mcu_build_and_coverage quick 模式找不到 suite | 手动指定 suite 参数，或运行完整模式 |
| **新增/删除测试文件后编译失败** | 使用 `mcu_build_and_coverage(reconfigure=true)` 重新配置 CMake |
| undefined reference 链接错误 | 使用 `reconfigure=true`，或手动运行 `cmake -DENABLE_COVERAGE=on ..` |
| **`#include 源文件.c` 后调用库函数找不到数据** | 见 13.4 符号隔离陷阱 |
| **Stub 后测试超时/卡死/段错误** | 见 13.5 Stub 全局副作用 |

### 13.2 编码注意事项

> ⚠️ **完全忽略 LSP/clangd 诊断，仅以 cmake --build 结果为准**

**LSP 错误处理原则**：
- 此项目的 LSP 诊断**不可靠**，大量误报
- clangd 无法正确解析 CMake 生成的 include 路径
- 常见误报：`'sockets.h' file not found`、`undeclared identifier`、`unknown type name`
- **唯一可信的编译检查**：`mcu_build_and_coverage` 或 `cmake --build`

**处理方式**：
```
LSP 报错 → 直接忽略，运行 mcu_build_and_coverage(file="xxx.c", quick=true)
cmake --build 成功 → 代码正确，无需理会 LSP
cmake --build 失败 → 根据编译器错误修复代码
```

**禁止**：
- ❌ 试图修复 LSP 报告的"错误"（除非 cmake 也报错）
- ❌ 添加 include 来"满足" LSP（可能破坏编译）
- ❌ 花时间配置 .clangd 或 compile_commands.json

**注释规范**：
- 测试代码注释保持简短
- 不需要为每个测试函数写文档注释
- 必要时用单行注释说明测试场景即可

### 13.3 C 语言隐式函数声明陷阱

> ⚠️ **必须包含正确的头文件，否则返回指针的函数会被截断**

**问题现象**：
- 调用 `dds_create_qos()` 等返回指针的函数时 segfault
- 指针值看起来像被截断（如 `0xfffffffff7beed9c`）
- gdb 显示指针参数明显无效

**根本原因**：
C 语言的隐式函数声明规则：如果调用函数时没有可见的声明，编译器假设函数返回 `int`。在 64 位系统上，`int` 是 32 位，而指针是 64 位，导致返回值被截断。

**典型错误示例**：
```c
// 错误：缺少 #include "dds_qos.h"
dds_qos_t *qos = dds_create_qos();  // 返回值被截断成 32 位！
dds_qset_userdata(qos, "data", 4);  // segfault: qos 是无效指针
```

**解决方案**：
```c
#include "dds.h"
#include "dds_qos.h"  // 必须包含！dds.h 不会自动包含它

dds_qos_t *qos = dds_create_qos();  // 现在正确返回 64 位指针
```

**需要显式包含的头文件**：

| 函数 | 需要的头文件 |
|------|-------------|
| `dds_create_qos`, `dds_delete_qos` | `dds_qos.h` |
| `dds_qset_*`, `dds_qget_*` | `dds_qos.h` |
| `dds_create_listener`, `dds_delete_listener` | `dds_listener.h` |
| `dds_lset_*`, `dds_lget_*` | `dds_listener.h` |

**检查方法**：
1. 编译时如果看到 `implicit declaration of function 'xxx'` 警告 → 缺少头文件
2. 运行时 segfault 且指针值异常 → 检查返回指针的函数是否有正确声明
3. 用 gdb 检查指针值是否看起来像被截断（高 32 位是 0xffffffff 或 0x00000000）

### 13.4 符号隔离陷阱（#include 源文件.c）

> ⚠️ **`#include "源文件.c"` 会创建独立的全局变量副本**

**问题现象**：
- 调用 `dds_domain_find_locked()` 返回 NULL
- 明明 `dds_create_participant()` 成功了，却找不到 domain
- 测试文件里的函数和库里的函数操作的是不同的数据

**根本原因**：
当测试文件 `#include "dds_domain.c"` 时，源文件中的所有静态/全局变量（如 `dds_global`、AVL 树等）在测试文件中有一份**独立副本**。而 `dds_create_participant()` 调用的是**库里的** `dds_domain.c`，它们操作不同的全局变量。

```
测试文件副本:  dds_global (空)     ← dds_domain_find_locked() 查这里
库里的原本:    dds_global (有数据) ← dds_create_participant() 写这里
```

**解决方案**：

| 场景 | 正确做法 |
|------|----------|
| 需要获取 domain 指针 | 通过 `dds_entity_pin(participant, &e)` 获取 entity，再用 `e->m_domain` |
| 需要调用内部函数 | 用 extern 声明 STATIC 函数，不要 include 源文件 |
| 必须 include 源文件 | 只调用该文件内的静态函数，不要混用库 API |

**正确示例**：
```c
CU_Test(dds_domain_cov, test_something)
{
    dds_entity_t participant = dds_create_participant(DDS_DOMAIN_DEFAULT, NULL, NULL, NULL);
    CU_ASSERT_FATAL(participant > 0);

    // ❌ 错误：dds_domain_find_locked 查的是测试文件副本
    // dds_domain *dom = dds_domain_find_locked(DDS_DOMAIN_DEFAULT);

    // ✅ 正确：通过 entity API 获取库里真正的 domain
    dds_entity *e;
    dds_return_t rc = dds_entity_pin(participant, &e);
    CU_ASSERT_FATAL(rc == DDS_RETCODE_OK);
    dds_domain *dom = e->m_domain;
    CU_ASSERT_FATAL(dom != NULL);

    // 现在 dom 是库里真正的 domain，可以修改它
    dom->gv.default_local_plist_pp = NULL;

    dds_entity_unpin(e);
    dds_delete(participant);
}
```

### 13.5 Stub 全局副作用

> ⚠️ **Stub 影响所有线程，包括后台线程**

**问题现象**：
- 设置 Stub 后测试超时/卡死
- 段错误发生在非预期位置
- `dds_delete()` 永远不返回

**根本原因**：
`set_stub()` 修改的是函数入口的机器码，影响**整个进程**。`dds_create_participant()` 会启动多个后台线程（发现、保活等），这些线程也会调用被 Stub 的函数。

**典型危险场景**：
```c
// ❌ 危险：stub dds_handle_is_closed 影响所有线程
void *stub = set_stub((void *)dds_handle_is_closed, (void *)always_return_true);
// 后台线程检查句柄状态时，误以为所有实体都在删除中，导致崩溃或死锁
```

**安全的替代方案**：

| 危险 Stub | 安全替代 |
|-----------|----------|
| `dds_handle_is_closed` | 真实调用 `dds_handle_close()` 关闭句柄 |
| `dds_entity_init` | Stub 更上层的 `dds_handle_create` |
| 任何锁相关函数 | 无法 Stub，接受无法覆盖 |

**安全 Stub 的原则**：
1. Stub 的函数应该**只在测试流程中被调用**，不被后台线程调用
2. Stub 时间要**尽可能短**，用完立即 `unset_stub()`
3. 优先 Stub **叶子函数**（如 `malloc`），而不是被广泛调用的核心函数
4. 如果测试超时，首先怀疑 Stub 副作用

### 13.6 何时接受无法覆盖

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

## 15. 工具使用最佳实践

### 15.1 工作流推荐顺序

```
1. mcu_estimate_max_coverage(file="xxx.c")  # 【新】评估目标是否可达
2. mcu_coverage_report(file="xxx.c")        # 查看当前覆盖率和未覆盖项（含可达性分析）
3. mcu_find_test_file(source="xxx.c")       # 找到应追加测试的文件（含多进程分析）
4. mcu_list_tests(suite_filter="xxx")       # 确认 suite 名称
5. [编写测试代码]
6. mcu_run_single_test(suite="xxx")         # 快速验证测试通过
7. mcu_quick_coverage(suite, test, file)    # 【改进】快速验证覆盖率（自动备份恢复 gcda）
8. mcu_build_and_coverage(file="xxx.c")     # 生成完整覆盖率报告
```

### 15.2 工具参数选择

| 场景 | 推荐工具和参数 |
|------|----------------|
| 评估目标可达性 | `mcu_estimate_max_coverage(file="xxx.c")` |
| 只想快速编译验证 | `mcu_build_and_coverage(file="xxx.c", quick=true)` |
| 需要完整覆盖率 | `mcu_build_and_coverage(file="xxx.c")` |
| 验证单个测试 | `mcu_run_single_test(suite="xxx", test="yyy")` |
| 按源文件查测试 | 先 `mcu_find_test_file`，再 `mcu_list_tests(suite_filter="...")` |
| 快速验证覆盖率效果 | `mcu_quick_coverage(suite, test, file)` - 自动备份/恢复 gcda |
| 检查代码是否需要多进程 | `mcu_find_test_file` 返回 `multiproc_analysis` 字段 |

### 15.3 注意事项

- `mcu_build_and_coverage` 完整模式耗时 2-5 分钟，迭代时用 quick 模式
- `mcu_quick_coverage` 现在**自动备份和恢复** .gcda 文件，无需重新运行完整测试
- 覆盖率报告解析的行号对应**源文件**，不是测试文件
- gcov 对 `a && b` 生成 4 个分支，对三元运算符生成 2 个分支
- `mcu_coverage_report` 返回 `reachability` 字段标注每个未覆盖项的可达性
- `mcu_list_tests` 现在直接从源文件解析 `CU_Test(suite, test)` 宏，更准确

---

## 16. 参考资源

| 资源 | 路径 |
|------|------|
| 仓库规范 | `CLAUDE.md` |
| 模板测试 | `tests/ddsi_ownip_test.c` (950行) |
| 简洁示例 | `tests/ddsi_mcgroup.c` (123行) |
| Stub 实现 | `tests/stub/stub.h` |
| 多进程测试 | `examples/multiproc_test/` |
| 覆盖率报告 | `public/codecov.html` |
