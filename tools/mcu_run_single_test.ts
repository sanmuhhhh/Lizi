import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"

export default tool({
  description: `运行单个测试 suite 或 test，返回简洁的结果。

用法示例:
  mcu_run_single_test(suite="rpcserver_coverage")
  mcu_run_single_test(suite="notify_rpc_qos", test="rpc_server_qos_setup_null")

成功返回:
  {
    "status": "passed",
    "tests_ran": 1,
    "tests_passed": 1,
    "asserts_total": 3,
    "asserts_passed": 3,
    "elapsed": "0.001s"
  }

失败返回:
  {
    "status": "failed",
    "tests_failed": 1,
    "output_tail": "... last 30 lines of output ..."
  }`,
  args: {
    suite: tool.schema.string().optional().describe("Suite 名称，如 'rpcserver_coverage'"),
    test: tool.schema.string().optional().describe("Test 名称，如 'service_fini_delete_error'"),
  },
  async execute(args, context) {
    if (!args.suite && !args.test) {
      return JSON.stringify({ error: "必须指定 suite 或 test" })
    }
    
    const toolsDir = path.join(os.homedir(), ".config/opencode/tools")
    const script = path.join(toolsDir, "mcu_run_single_test.py")
    const projectRoot = "/home/sanmu/MyProject/mcu_ctest/autosar-mcu"
    
    const cmdArgs = ["python3", script]
    if (args.suite) {
      cmdArgs.push("--suite", args.suite)
    }
    if (args.test) {
      cmdArgs.push("--test", args.test)
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
