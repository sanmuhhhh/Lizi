import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"

export default tool({
  description: `估算源文件的最大可达覆盖率，识别无法通过单元测试覆盖的代码块。

用法示例:
  mcu_estimate_max_coverage(file="q_transmit.c")
  mcu_estimate_max_coverage(file="ddsi_ownip.c")

返回 JSON:
  {
    "file": "q_transmit.c",
    "current": {"line_coverage": 45.5, "branch_coverage": 31.6},
    "estimated_max": {"line_coverage": 55, "branch_coverage": 45},
    "blockers": [
      {"pattern": "new_*", "category": "multiproc_required", "reason": "..."}
    ]
  }

用途: 在开始覆盖率提升前，了解目标是否可达`,
  args: {
    file: tool.schema.string().describe("源文件名，如 'q_transmit.c' 或 'ddsi_ownip.c'"),
  },
  async execute(args, context) {
    const toolsDir = path.join(os.homedir(), ".config/opencode/tools")
    const script = path.join(toolsDir, "mcu_estimate_max_coverage.py")
    const projectRoot = "/home/sanmu/MyProject/mcu_ctest/autosar-mcu"
    
    const proc = Bun.spawn(["python3", script, args.file], {
      cwd: projectRoot,
      stdout: "pipe",
      stderr: "pipe",
    })
    
    let stdout = ""
    let stderr = ""
    
    if (proc.stdout) {
      stdout = await new Response(proc.stdout).text()
    }
    if (proc.stderr) {
      stderr = await new Response(proc.stderr).text()
    }
    
    await proc.exited
    
    if (proc.exitCode !== 0 || stderr) {
      return JSON.stringify({ error: stderr || `Exit code: ${proc.exitCode}` })
    }
    
    try {
      JSON.parse(stdout)
      return stdout
    } catch {
      return JSON.stringify({ error: "Failed to parse output", raw: stdout })
    }
  },
})
