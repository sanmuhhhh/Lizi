import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"

export default tool({
  description: `一键编译、测试、生成覆盖率报告。成功返回覆盖率数据，失败只返回最后 50 行错误日志。

quick 模式会自动推断对应的 suite（基于 mcu_find_test_file），避免运行全部测试超时。

reconfigure=true 会重新运行 cmake 配置，用于：
- 新增/删除测试文件后
- CMakeLists.txt 修改后
- 遇到 "undefined reference" 链接错误时

成功返回:
  { "build": "ok", "coverage_test": "ok", "coverage": { "line_coverage": 100.0, ... } }

失败返回:
  { "stage": "configure|build|test|coverage", "error": "...", "last_50_lines": "..." }`,
  args: {
    file: tool.schema.string().describe("目标源文件名，如 'rpcserver.c'"),
    suite: tool.schema.string().optional().describe("只运行指定 suite（可选）"),
    quick: tool.schema.boolean().optional().describe("快速模式：只编译运行测试，不生成覆盖率报告"),
    reconfigure: tool.schema.boolean().optional().describe("重新运行 cmake 配置（测试文件新增/删除后需要）"),
  },
  async execute(args, context) {
    const toolsDir = path.join(os.homedir(), ".config/opencode/tools")
    const script = path.join(toolsDir, "mcu_build_and_coverage.py")
    const projectRoot = "/home/sanmu/MyProject/mcu_ctest/autosar-mcu"
    
    const cmdArgs = ["python3", script, "--file", args.file]
    if (args.suite) {
      cmdArgs.push("--suite", args.suite)
    }
    if (args.quick) {
      cmdArgs.push("--quick")
    }
    if (args.reconfigure) {
      cmdArgs.push("--reconfigure")
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
    
    if (stderr && !stdout) {
      return JSON.stringify({ error: stderr })
    }
    
    try {
      JSON.parse(stdout)
      return stdout
    } catch {
      return JSON.stringify({ error: "Failed to parse output", raw: stdout, stderr })
    }
  },
})
