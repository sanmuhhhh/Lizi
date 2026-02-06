import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"

export default tool({
  description: `根据源文件查找已有的测试文件，并推荐应该追加测试的位置。

用法示例:
  mcu_find_test_file(source="rpcserver.c")
  mcu_find_test_file(source="ddsi_ownip.c")

返回 JSON:
  {
    "source_file": "rpcserver.c",
    "existing_tests": [
      {"file": "notify_rpc_coverage.c", "suites": ["notify_rpc_qos", "notify_rpc_init"], "relevance": 10}
    ],
    "recommendation": {
      "action": "append",
      "file": "notify_rpc_coverage.c",
      "reason": "已有相关测试文件，建议追加到现有 suite"
    }
  }`,
  args: {
    source: tool.schema.string().describe("源文件名，如 'rpcserver.c' 或 'ddsi_ownip.c'"),
  },
  async execute(args, context) {
    const toolsDir = path.join(os.homedir(), ".config/opencode/tools")
    const script = path.join(toolsDir, "mcu_find_test_file.py")
    const projectRoot = "/home/sanmu/MyProject/mcu_ctest/autosar-mcu"
    
    const proc = Bun.spawn(["python3", script, args.source], {
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
