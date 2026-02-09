# 栗子 (Lizi)

伞木的 AI 助手，一只小栗子精灵。提供记忆系统、日常聊天、技术问答能力。

## 目录结构

```
lizi/
├── agents/
│   └── lizi.md          ← agent 定义
├── skills/
│   ├── mcu_ctest.md     ← MCU 测试 skill
│   └── ...              ← 其他 skills
├── tools/
│   ├── lizi_recalling.* ← 回忆工具
│   ├── lizi_memorize.*  ← 记忆工具
│   ├── lizi_looking_watch.ts
│   ├── lizi_verify.*    ← 身份验证
│   ├── lizi_secrets.*   ← 加密隐私存储
│   ├── lizi_deduplicate-memories.*
│   ├── mcu_*.           ← MCU 覆盖率/测试工具
│   └── embedding_utils.py / importance.py / watch.py
├── memories/            ← 本地私有，不随 install 部署
└── secrets/             ← 本地私有，不随 install 部署
```

---

## 安装

将此内容粘贴给你的 LLM agent 执行：

```
请按照以下指南安装 lizi：
https://raw.githubusercontent.com/sanmuhhhh/lizi/main/README.md
```

---

## For LLM Agents

你正在帮用户安装 lizi agent 套件。请按以下步骤执行：

### Step 1: 克隆仓库

```bash
git clone https://github.com/sanmuhhhh/lizi ~/.config/lizi
```

### Step 2: 执行安装脚本

```bash
bash ~/.config/lizi/install.sh
```

### Step 3: 告知用户

安装完成后告知用户：

> 安装完成！重启 opencode 后：
> - 按 **Tab** 可切换到 `lizi` agent
> - 记忆目录在 `~/.config/lizi/memories/`，私有数据不会随 git 提交

---

## 卸载

```bash
bash ~/.config/lizi/uninstall.sh
```

> 记忆数据保留在 `~/.config/lizi/memories/`，不会被卸载影响。
