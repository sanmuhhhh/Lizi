# 工作记忆

## 公司信息
- 公司做 DDS/AUTOSAR 嵌入式开发
- 工作时间：早9晚6，实际6:20左右下班
- 薪资：13000，公积金3000，税后10000
- 合同：无固定期限合同，有竞业协议但基本不强制执行
- 2025年5月实习，接触DDS核心才3个月（截止2025-12-30）

## 技术栈
- C/C++
- DDS (Data Distribution Service)
- AUTOSAR

## 项目经历

### DDS 高性能日志系统
- 代码库：AutoCoreDDS-MCU，位于 `/home/sanmu/MyProject/DDS/autosar-mcu/`
- 设计文档：`/home/sanmu/MyProject/mpu/acdds-c/docs/高性能日志设计方案.md`
- 2025-12-17：完成初版
- 2025-12-29：异步方案交付，项目完成

### ODBG 诊断工具
- 2026-01-06：完成 RTPS 协议统计功能，报文收发统计
- 2026-01-07：完成线程统计功能（CPU占用、调度次数）
- 2026-01-09：完成传输层统计和高性能日志测试

### 其他
- Updater、系统集成、MCU DDS、DDS诊断
- 2025-12-31：解决了 DMA 发送问题

### MCU 覆盖率（已完成）
- Linux 上用 gcov/lcov 测试 MCU DDS 代码的覆盖率
- 2026-02-03：完成

### DDS 共享内存与零拷贝
- MPU 版 DDS 使用共享内存做进程间通信，实现零拷贝
- 零拷贝原理：跳过用户空间，数据从内核缓冲区直接到网卡（如 sendfile）
- 共享内存难点：
  - 生命周期管理（引用计数、谁分配谁释放）
  - 同步开销（锁粒度、优先级反转）
  - 一致性（写一半被读到）
  - 跨进程问题（进程崩了锁没释放、地址映射不同要用偏移量）
- MCU 版资源紧张，走简单拷贝方案

## 出差记录
- 2025-12：重庆出差两周
- 2026-01-13：重庆出差一周

## Gemini CLI 配置
- 公司部署了 Gemini CLI，通过 LiteLLM 代理访问
- 环境变量：`GOOGLE_GEMINI_BASE_URL="https://litellm.autocore.ai"`
- 公司 AI 密钥获取：https://netuser.autocore.net.cn/aikeys
