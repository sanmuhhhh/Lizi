import { tool } from "@opencode-ai/plugin"
import path from "path"
import fs from "fs"
import os from "os"

export default tool({
  description: "栗子的记忆工具，从对话中提取值得记住的信息并写入记忆文件。当用户说结束语（拜拜、再见、晚安）或主动要求（记一下、记住这个）时调用。",
  args: {
    conversation: tool.schema.string().describe("当前对话的完整内容"),
  },
  async execute(args, context) {
    const venvPython = path.join(context.directory, ".opencode/.venv/bin/python3")
    const script = path.join(context.directory, "tools/lizi_memorize.py")
    
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
