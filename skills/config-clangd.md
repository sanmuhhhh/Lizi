---
name: config-clangd
description: 为 AutoCoreDDS C/C++ 项目配置 clangd 代码跳转和智能补全。当无法 Ctrl+Click 跳转代码时运行此技能。
---

# 配置 clangd 代码跳转

## 步骤 1：生成编译数据库

在项目根目录运行 CMake，启用编译命令导出：

```bash
mkdir -p build
cmake -S . -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

## 步骤 2：创建符号链接到项目根目录

```bash
ln -sf build/compile_commands.json compile_commands.json
```

验证：

```bash
ls -la compile_commands.json
```

## 步骤 3：创建 `.vscode/settings.json`

```bash
mkdir -p .vscode
```

写入以下内容（根据实际 clangd 路径调整）：

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

## 步骤 4：验证

重启 VSCode 或重新加载窗口（`Ctrl+Shift+P` → `Developer: Reload Window`），然后在任意 `.c` 文件中 `Ctrl+Click` 函数名验证跳转是否生效。

## AutoCoreDDS 特有说明

- 项目使用 CMake 构建，`build/` 目录在根目录下
- 主要源码路径：`src/core/ddsc/`、`src/core/ddsi/`、`src/ddsrt/`
- 如果项目有多个构建配置（Debug/Release），优先用 Debug 配置生成 `compile_commands.json`
