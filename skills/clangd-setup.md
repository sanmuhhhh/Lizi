---
name: clangd-setup
description: 配置 C/C++ 项目的代码跳转和智能补全。当项目无法 Ctrl+Click 跳转时，运行此技能自动完成 clangd 配置。
---

# Clangd Setup

配置 C/C++ 项目使用 clangd 实现代码跳转和智能补全。

## 适用场景

- 新打开一个 C/C++ 项目，无法 Ctrl+Click 跳转
- 项目缺少 `compile_commands.json`
- VSCode 智能提示不工作

## 配置步骤

### 步骤 0：检查 clangd 是否安装

首先检查 clangd 是否已安装：

```bash
which clangd && clangd --version
```

如果未安装，需要先安装：
- Ubuntu: `sudo apt install clangd`
- macOS: `brew install llvm`

**必须确认 clangd 已安装后再进行后续步骤！**

### 步骤 1：生成编译数据库

在项目的 build 目录中重新运行 CMake，启用编译命令导出：

```bash
mkdir -p build
cd build
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ..
```

### 步骤 2：创建符号链接到项目根目录

在项目根目录创建指向编译数据库的符号链接：

```bash
cd ../
ln -sf build/compile_commands.json compile_commands.json
```

### 步骤 3：创建 .vscode/settings.json

在项目根目录创建或修改 `.vscode/settings.json`：

```bash
mkdir -p .vscode
```

创建文件内容（根据实际情况修改 clangd 路径）：

```json
{
  "C_Cpp.intelliSenseEngine": "disabled",
  "clangd.arguments": [
    "--compile-commands-dir=${workspaceFolder}/build",
    "--background-index",
    "--clang-tidy",
    "--header-insertion=never",
    "--completion-style=detailed",
    "--function-arg-placeholders=true",
    "--fallback-style=llvm"
  ],
  "clangd.path": "/usr/bin/clangd",
  "files.associations": {
    "*.h": "c",
    "*.c": "c"
  }
}
```

## 验证配置

1. 重启 VSCode 或重新加载窗口
2. 打开任意 `.c` 文件
3. Ctrl+Click 任意函数名，应该能跳转到定义

## 常见问题

- **clangd 未安装**：`sudo apt install clangd` (Ubuntu) 或 `brew install llvm` (macOS)
- **跳转不生效**：检查 `compile_commands.json` 是否存在且内容正确
- **头文件找不到**：确保 CMake 配置正确包含了所有 include 路径
