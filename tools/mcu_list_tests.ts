import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"

export default tool({
  description: `列出 CUnit 测试二进制中的所有 suite 和 test，支持按 suite 名称或测试文件过滤。

用法示例:
  mcu_list_tests()                                        # 列出所有测试
  mcu_list_tests(suite_filter="dds_participant")          # 按 suite 名称过滤
  mcu_list_tests(file_filter="notify_rpc_coverage.c")     # 按测试文件过滤

返回 JSON:
  { "total_suites": 100, "total_tests": 500, "suites": [{"name": "...", "tests": [...], "test_count": N}] }

用途: 确认测试是否正确注册、查找测试名称`,
  args: {
    suite_filter: tool.schema.string().optional().describe("按 suite 名称过滤，支持部分匹配"),
    file_filter: tool.schema.string().optional().describe("按测试文件名过滤，如 'notify_rpc_coverage.c'"),
  },
  async execute(args, context) {
    const toolsDir = path.join(os.homedir(), ".config/opencode/tools")
    const script = path.join(toolsDir, "mcu_list_tests.py")
    const projectRoot = "/home/sanmu/MyProject/mcu_ctest/autosar-mcu"
    
    const cmdArgs = ["python3", script]
    if (args.file_filter) {
      cmdArgs.push("--file", args.file_filter)
    } else if (args.suite_filter) {
      cmdArgs.push(args.suite_filter)
    }
    
    const proc = Bun.spawn(cmdArgs, {
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
