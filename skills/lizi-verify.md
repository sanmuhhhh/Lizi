# 身份验证流程

当需要访问极敏感信息（密码、银行卡等）时，使用此流程验证用户身份。

## 验证步骤

### 1. 检查状态
```
调用 lizi_verify(mode: "status")
```
- 如果 `ready: false`，提示伞木需要先积累一些隐私信息
- 如果 `ready: true`，继续下一步

### 2. 抽取问题
```
调用 lizi_verify(mode: "pick")
```
返回 questions 数组（answer_keys 已加密存储在后端）

### 3. 弹出选项
```
调用 question(questions: <上一步的 questions>)
```
用户回答后得到 answers 数组

### 4. 验证答案
```
调用 lizi_verify(mode: "check", data: JSON.stringify({answers: <用户答案>}))
```
返回 `success: true` 表示验证通过

## 问题库维护

发现新隐私信息时添加：
```
调用 lizi_verify(mode: "add", data: JSON.stringify({
  "key": "唯一标识",
  "question": "问题描述", 
  "answer": "正确答案",
  "aliases": ["别名1", "别名2"]  // 可选
}))
```

## 安全原则

- 验证失败只说"验证失败"，不透露哪个错
- 每次随机抽 3 题
- answer_keys 不返回给前端，防止日志泄露
