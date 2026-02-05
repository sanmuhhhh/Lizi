import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"

export default tool({
  description: "栗子的手表，用来看当前时间",
  args: {},
  async execute(args, context) {
    const liziDir = path.join(os.homedir(), ".config/lizi")
    const script = path.join(liziDir, "tools/watch.py")
    const result = await Bun.$`python3 ${script}`.text()
    return result.trim()
  },
})

