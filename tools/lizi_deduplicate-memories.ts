import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "检测记忆中的重复内容。使用语义相似度（默认阈值0.85）找出相似的记忆片段。返回JSON格式的重复列表供审阅。",
  args: {
    threshold: tool.schema.number().optional().default(0.85).describe("相似度阈值（0-1），默认0.85"),
    rebuildIndex: tool.schema.boolean().optional().default(false).describe("是否强制重建索引"),
  },
  async execute(args, context) {
    const venvPython = path.join(context.directory, ".opencode/.venv/bin/python3")
    const script = path.join(context.directory, "tools/lizi_deduplicate-memories.py")
    
    const cmd = [
      venvPython, script,
      "--threshold", String(args.threshold || 0.85),
      "--dry-run"
    ]
    
    if (args.rebuildIndex) {
      cmd.push("--rebuild-index")
    }
    
    const proc = Bun.spawn(cmd, {
      env: { ...process.env, HF_HUB_OFFLINE: "1" },
      stdout: "pipe",
      stderr: "ignore",
    })
    
    const stdout = await new Response(proc.stdout).text()
    await proc.exited
    
    try {
      const json = JSON.parse(stdout.trim())
      return JSON.stringify(json, null, 2)
    } catch {
      return stdout.trim()
    }
  },
})
