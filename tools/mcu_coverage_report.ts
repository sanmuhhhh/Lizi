import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"

export default tool({
  description: "解析 MCU 项目的覆盖率报告，返回未覆盖行/分支的结构化数据",
  args: {
    file: tool.schema.string().describe("源文件名或路径，如 ddsi_ownip.c 或 src/CDD/.../ddsi_ownip.c"),
  },
  async execute(args, context) {
    const liziDir = path.join(os.homedir(), ".config/lizi")
    const script = path.join(liziDir, "tools/mcu_coverage_report.py")
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
      // Validate JSON is parseable, then return as string
      // (OpenCode expects string return, not object)
      JSON.parse(stdout)
      return stdout
    } catch {
      return JSON.stringify({ error: "Failed to parse output", raw: stdout })
    }
  },
})
