import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"

export default tool({
  description: `栗子的身份验证工具，用于保护极敏感信息。

使用方式：
1. status - 检查验证系统是否就绪
2. pick - 随机抽取问题，返回 question 工具需要的格式
3. check - 验证用户的答案
4. add - 添加单个验证问题（渐进式更新）
5. setup - 批量设置验证问题库`,
  args: {
    mode: tool.schema.enum(["status", "pick", "check", "add", "setup"]).describe("模式"),
    data: tool.schema.string().optional().describe("JSON数据"),
  },
  async execute(args, context) {
    const liziDir = path.join(os.homedir(), ".config/lizi")
    const venvPython = path.join(context.directory, ".opencode/.venv/bin/python3")
    const script = path.join(liziDir, "tools/lizi_verify.py")
    
    let pyMode = args.mode
    if (args.mode === "check") pyMode = "verify"
    
    const proc = Bun.spawn([venvPython, script, pyMode], {
      stdin: "pipe",
      stdout: "pipe",
      stderr: "pipe",
    })
    
    if (args.data) {
      proc.stdin.write(args.data)
    }
    proc.stdin.end()
    
    const stdout = await new Response(proc.stdout).text()
    const stderr = await new Response(proc.stderr).text()
    await proc.exited
    
    if (stderr) {
      return `错误: ${stderr}`
    }
    
    return stdout.trim()
  },
})
