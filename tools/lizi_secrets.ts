import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"

export default tool({
  description: `栗子的加密隐私存储工具。存储极敏感信息（密码、银行卡等）。

注意：获取隐私信息前必须先通过身份验证（lizi_verify）！

模式：
- list - 列出所有已存储的隐私项（只显示 key 和描述，不显示值）
- get - 获取某个隐私值（需先验证身份）
- set - 存储隐私信息
- delete - 删除隐私项`,
  args: {
    mode: tool.schema.enum(["list", "get", "set", "delete"]).describe("模式"),
    data: tool.schema.string().optional().describe("JSON数据。set模式: {key, value, description}; get/delete模式: {key} 或直接传 key"),
  },
  async execute(args, context) {
    const liziDir = path.join(os.homedir(), ".config/lizi")
    const venvPython = path.join(context.directory, ".opencode/.venv/bin/python3")
    const script = path.join(liziDir, "tools/lizi_secrets.py")
    
    const cmdArgs = [venvPython, script, args.mode]
    if (args.mode === "get" || args.mode === "delete") {
      if (args.data && !args.data.startsWith("{")) {
        cmdArgs.push(args.data)
      }
    }
    
    const proc = Bun.spawn(cmdArgs, {
      stdin: "pipe",
      stdout: "pipe",
      stderr: "pipe",
    })
    
    if (args.data && args.data.startsWith("{")) {
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
