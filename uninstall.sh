#!/usr/bin/env bash
set -e

LIZI_DIR="$(cd "$(dirname "$0")" && pwd)"
OPENCODE_DIR="$HOME/.config/opencode"

echo "==> Uninstalling lizi"

# Step 1: 删除 agent
echo "--> agent"
rm -f "$OPENCODE_DIR/agents/lizi.md"

# Step 2: 删除 skills
echo "--> skills"
for f in "$LIZI_DIR/skills/"*; do
  [ -f "$f" ] && rm -f "$OPENCODE_DIR/skills/$(basename "$f")"
done

# Step 3: 删除 tools
echo "--> tools"
for f in "$LIZI_DIR/tools/"*; do
  [ -f "$f" ] && rm -f "$OPENCODE_DIR/tools/$(basename "$f")"
done

# Step 4: 从 opencode.json 清除黑名单
echo "--> opencode.json blacklist"
python3 - <<PYEOF
import json, os

config_path = os.path.expanduser("~/.config/opencode/opencode.json")
tools_dir = "$LIZI_DIR/tools"

tool_names = [f[:-3] for f in os.listdir(tools_dir) if f.endswith(".ts")]

with open(config_path) as f:
    config = json.load(f)

removed = []
for name in tool_names:
    if config.get("tools", {}).pop(name, None) is not None:
        removed.append(name)

with open(config_path, "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"    removed {len(removed)} keys from blacklist")
PYEOF

echo "==> Done! Memories preserved at $LIZI_DIR/memories/"
