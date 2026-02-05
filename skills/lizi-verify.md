# 身份验证流程

当需要访问极敏感信息（密码、银行卡等）时，使用此流程验证用户身份。

## 验证步骤

### 1. 检查状态
```
调用 lizi_verify(mode: "status")
```
- 如果 `ready: false` 或问题数量太少，提示伞木需要先积累一些隐私信息到记忆里
- 如果 `ready: true`，继续下一步

### 2. 抽取问题
```
调用 lizi_verify(mode: "pick")
```
返回格式：
```json
{
  "success": true,
  "questions": [...],  // question 工具需要的格式
  "answer_keys": [...]  // 保存这个用于验证
}
```

### 3. 弹出选项
使用 `question` 工具，传入上一步的 `questions` 数组：
```
调用 question(questions: <上一步的 questions>)
```
用户会看到选择弹窗，可以选择迷惑选项或自己输入答案。

### 4. 验证答案
```
调用 lizi_verify(mode: "check", data: JSON.stringify({
  answers: <用户选择的答案>,
  answer_keys: <第2步保存的 answer_keys>
}))
```
返回 `success: true` 表示验证通过。

## 问题库维护（渐进式更新）

栗子在日常对话中发现新的隐私信息时，主动添加到问题库：

### 触发时机
- 伞木提到具体的个人信息（生日、工资、住址、家人信息等）
- 记忆中新增了隐私相关内容
- 伞木主动说"把这个加到验证问题里"

### 添加方式
```
调用 lizi_verify(mode: "add", data: JSON.stringify({
  "key": "唯一标识",
  "question": "问题描述",
  "answer": "正确答案"
}))
```

### 示例问题类型
- 生日、年龄
- 工资、公积金
- 老家、住址
- 学校、专业
- 家人信息
- 重要日期

## 安全原则

- 验证失败时只说"验证失败"，不透露哪个问题答错
- 每次随机抽 3 题，选项顺序也随机
- 如果用户关闭弹窗（dismissed），视为验证失败
- 问题库至少需要 3 个问题才能使用验证功能
