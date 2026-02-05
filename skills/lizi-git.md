# Git 提交规范

## 提交信息格式

一句话简洁描述，不要列表：
```
<type>: <简洁描述>
```

## Type 类型

- feat: 新功能
- fix: 修复 bug
- chore: 杂项（配置、依赖等）
- docs: 文档
- refactor: 重构
- style: 格式调整

## 示例

✅ 好的：
- `feat: 添加身份验证系统`
- `fix: 修复拼音匹配逻辑`
- `chore: 更新 gitignore`

❌ 不好的：
- `feat: 添加身份验证系统\n\n- 新增 lizi_verify\n- 新增 lizi_secrets`
- `更新了一些东西`

## 提交流程

1. `git status` 查看变更
2. `git add <files>` 暂存
3. `git commit -m "<type>: <描述>"` 提交
4. 等伞木说"提交"或"推送"再 `git push`
