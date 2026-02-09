import { tool } from "@opencode-ai/plugin"
import path from "path"
import fs from "fs"
import os from "os"

export default tool({
  description: "栗子的记忆工具，从对话中提取值得记住的信息，进行分级存储：将简短动态更新到 short-term.md（短期记忆），并将详细过程、逻辑分析和丰富细节按类别追加到长期记忆对应文件（如 work.md, life.md 等）中。当用户说结束语（拜拜、再见、晚安）或主动要求（记一下、总结到长期记忆等）时调用。",
  args: {
    conversation: tool.schema.string().describe("当前对话的完整内容"),
  },
  async execute(args, context) {
    const liziDir = path.join(os.homedir(), ".config/lizi")
    const venvPython = path.join(context.directory, ".opencode/.venv/bin/python3")
    const script = path.join(liziDir, "tools/lizi_memorize.py")
    
    const tmpFile = path.join(os.tmpdir(), `memorize-${Date.now()}.txt`)
    fs.writeFileSync(tmpFile, args.conversation, "utf-8")
    
    try {
      const proc = Bun.spawn([venvPython, script, tmpFile], {
        env: { ...process.env },
        stdout: "pipe",
        stderr: "ignore",
      })
      await proc.exited
    } finally {
      fs.unlinkSync(tmpFile)
    }
    
    return ""
  },
})
