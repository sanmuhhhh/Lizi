import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"

export default tool({
  description: "栗子的回忆工具，搜索长期记忆（work/hobby/invest/learning/life/thoughts/projects）。支持关键词搜索和语义搜索。不传关键词则随机回忆。",
  args: {
    keyword: tool.schema.string().optional().describe("要搜索的关键词，不传则随机回忆"),
    mode: tool.schema.enum(["keyword", "semantic", "auto"]).optional().default("auto").describe("搜索模式：keyword=关键词匹配，semantic=语义搜索，auto=智能模式（关键词优先，不足时补充语义结果）"),
  },
  async execute(args, context) {
    const liziDir = path.join(os.homedir(), ".config/lizi")
    const venvPython = path.join(context.directory, ".opencode/.venv/bin/python3")
    const script = path.join(liziDir, "tools/lizi_recalling.py")
    
    const cmd = args.keyword 
      ? [venvPython, script, args.keyword, "--mode", args.mode || "auto"]
      : [venvPython, script]
    
    const proc = Bun.spawn(cmd, {
      env: { ...process.env, HF_HUB_OFFLINE: "1" },
      stdout: "pipe",
      stderr: "ignore",
    })
    
    const stdout = await new Response(proc.stdout).text()
    await proc.exited
    
    return stdout.trim()
  },
})
