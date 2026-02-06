import { z } from "zod";
import { spawn } from "child_process";
import path from "path";

const TOOL_PATH = path.join(__dirname, "mcu_coverage_report.py");

export const description =
  "解析 MCU 项目的覆盖率报告，返回未覆盖行/分支的结构化数据";

export const parameters = z.object({
  file: z
    .string()
    .describe(
      "源文件名或路径，如 ddsi_ownip.c 或 src/CDD/.../ddsi_ownip.c"
    ),
});

export async function execute(args: z.infer<typeof parameters>) {
  return new Promise((resolve) => {
    const proc = spawn("python3", [TOOL_PATH, args.file], {
      cwd: "/home/sanmu/MyProject/mcu_ctest/autosar-mcu",
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("close", (code) => {
      if (code !== 0 || stderr) {
        resolve({ error: stderr || `Exit code: ${code}` });
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch {
        resolve({ error: "Failed to parse output", raw: stdout });
      }
    });
  });
}
