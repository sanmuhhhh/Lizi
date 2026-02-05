import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "栗子的手表，用来看当前时间",
  args: {},
  async execute(args, context) {
    const script = path.join(context.directory, "tools/watch.py")
    const result = await Bun.$`python3 ${script}`.text()
    return result.trim()
  },
})

