#!/usr/bin/env bash
set -e

LIZI_DIR="$(cd "$(dirname "$0")" && pwd)"
OPENCODE_DIR="$HOME/.config/opencode"

echo "==> Installing lizi from $LIZI_DIR"

# Step 1: 复制 agent
echo "--> agent"
cp "$LIZI_DIR/agents/lizi.md" "$OPENCODE_DIR/agents/lizi.md"

# Step 2: 复制 skills
echo "--> skills"
for f in "$LIZI_DIR/skills/"*; do
  [ -f "$f" ] && cp -f "$f" "$OPENCODE_DIR/skills/$(basename "$f")"
done

# Step 3: 复制 tools
echo "--> tools"
for f in "$LIZI_DIR/tools/"*; do
  [ -f "$f" ] && cp -f "$f" "$OPENCODE_DIR/tools/$(basename "$f")"
done

# Step 4: 确保 venv 存在
echo "--> venv"
VENV_DIR="$OPENCODE_DIR/.opencode/.venv"
if [ ! -f "$VENV_DIR/bin/python3" ]; then
  echo "    creating venv..."
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install -q openai numpy
else
  echo "    venv already exists, skipping"
fi

# Step 5: 更新 opencode.json 黑名单
echo "--> opencode.json blacklist"
python3 - <<PYEOF
import json, os

config_path = os.path.expanduser("~/.config/opencode/opencode.json")
tools_dir = "$LIZI_DIR/tools"

tool_names = [f[:-3] for f in os.listdir(tools_dir) if f.endswith(".ts")]

with open(config_path) as f:
    config = json.load(f)

if "tools" not in config:
    config["tools"] = {}

for name in tool_names:
    config["tools"][name] = False

with open(config_path, "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"    blacklisted {len(tool_names)} tools")
PYEOF

echo "==> Done! Restart opencode to activate lizi."
