import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"

export default tool({
  description: `快速验证单个测试的覆盖率效果，返回 before/after/delta 对比。

⚠️ 警告: 此工具会删除 .gcda 文件，运行后需重新执行完整测试恢复覆盖率数据。

用法示例:
  mcu_quick_coverage(suite="dds_participant", test="lookup_with_actual_domain_id", file="dds_participant.c")

参数说明:
  suite: Suite 名称（如 "dds_participant"，不是 "dds_participant_coverage"）
  test:  Test 名称（如 "lookup_with_actual_domain_id"）
  file:  目标源文件名（如 "dds_participant.c"）

返回 JSON:
  { "before": {"line_coverage": 88.8}, "after": {"line_coverage": 93.8}, "delta": {"line_coverage": 5.0} }`,
  args: {
    suite: tool.schema.string().describe("Suite 名称，如 'dds_participant'"),
    test: tool.schema.string().describe("Test 名称，如 'lookup_with_actual_domain_id'"),
    file: tool.schema.string().describe("目标源文件名，如 'dds_participant.c'"),
  },
  async execute(args, context) {
    const toolsDir = path.join(os.homedir(), ".config/opencode/tools")
    const script = path.join(toolsDir, "mcu_quick_coverage.py")
    const projectRoot = "/home/sanmu/MyProject/mcu_ctest/autosar-mcu"
    
    const cmdArgs = [
      "python3", script,
      "--suite", args.suite,
      "--test", args.test,
      "--file", args.file
    ]
    
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
