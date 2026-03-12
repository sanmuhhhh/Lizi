#!/usr/bin/env bash
# lizi 安装/卸载脚本
# 安装：bash install.sh
# 卸载：bash install.sh --uninstall
# 重新运行可更新文件，新增 skill/tool 后重跑即可

set -e

UNINSTALL=false
[[ "${1:-}" == "--uninstall" ]] && UNINSTALL=true

LIZI_DIR="$(cd "$(dirname "$0")" && pwd)"
OPENCODE_DIR="$HOME/.config/opencode"

# ─── 颜色输出 ──────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }

if [[ ! -d "$OPENCODE_DIR" ]]; then
  warn "未找到 opencode 配置目录：$OPENCODE_DIR，正在创建..."
  mkdir -p "$OPENCODE_DIR"
  ok "已创建 $OPENCODE_DIR"
fi

if [[ "$UNINSTALL" == true ]]; then
  # ─── 卸载 ────────────────────────────────────────────
  echo ""
  echo "🗑️  卸载 agent..."
  rm -f "$OPENCODE_DIR/agents/lizi.md" && ok "agent: lizi.md"

  echo ""
  echo "🗑️  卸载 skills..."
  for skill_dir in "$LIZI_DIR/skills"/*/; do
    [[ -d "$skill_dir" ]] || continue
    name="$(basename "$skill_dir")"
    rm -rf "$OPENCODE_DIR/skills/$name" && ok "skill: $name"
  done

  echo ""
  echo "🗑️  卸载 tools..."
  for tool_file in "$LIZI_DIR/tools"/*.ts "$LIZI_DIR/tools"/*.py; do
    [[ -f "$tool_file" ]] || continue
    name="$(basename "$tool_file")"
    rm -f "$OPENCODE_DIR/tools/$name" && ok "tool: $name"
  done

  echo ""
  echo "🗑️  清除 opencode.json 黑名单..."
  python3 - <<PYEOF
import json, os

config_path = os.path.expanduser("~/.config/opencode/opencode.json")
tools_dir = "$LIZI_DIR/tools"

tool_names = [f[:-3] for f in os.listdir(tools_dir) if f.endswith(".ts")]

with open(config_path) as f:
    config = json.load(f)

tools_cfg = config.get("tools", {})
removed = [name for name in tool_names if name in tools_cfg]
for name in removed:
    del tools_cfg[name]
if not tools_cfg:
    config.pop("tools", None)
else:
    config["tools"] = tools_cfg

with open(config_path, "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"    removed {len(removed)} tools from blacklist")
PYEOF

  echo ""
  echo "✅ 卸载完成。"

else
  # ─── 安装 ────────────────────────────────────────────
  echo "==> Installing lizi from $LIZI_DIR"

  echo ""
  echo "📦 安装 agent..."
  mkdir -p "$OPENCODE_DIR/agents"
  cp -f "$LIZI_DIR/agents/lizi.md" "$OPENCODE_DIR/agents/lizi.md"
  ok "agent: lizi.md"

  echo ""
  echo "📦 安装 skills..."
  mkdir -p "$OPENCODE_DIR/skills"
  for skill_dir in "$LIZI_DIR/skills"/*/; do
    [[ -d "$skill_dir" ]] || continue
    name="$(basename "$skill_dir")"
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    mkdir -p "$OPENCODE_DIR/skills/$name"
    cp -f "$skill_dir/SKILL.md" "$OPENCODE_DIR/skills/$name/SKILL.md"
    ok "skill: $name"
  done

  echo ""
  echo "📦 安装 tools..."
  mkdir -p "$OPENCODE_DIR/tools"
  for tool_file in "$LIZI_DIR/tools"/*.ts "$LIZI_DIR/tools"/*.py; do
    [[ -f "$tool_file" ]] || continue
    name="$(basename "$tool_file")"
    cp -f "$tool_file" "$OPENCODE_DIR/tools/$name"
    ok "tool: $name"
  done

  echo ""
  echo "📦 确保 venv 存在..."
  VENV_DIR="$OPENCODE_DIR/.opencode/.venv"
  if [ ! -f "$VENV_DIR/bin/python3" ]; then
    warn "creating venv..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -q openai numpy
    ok "venv created"
  else
    ok "venv already exists, skipping"
  fi

  echo ""
  echo "📦 更新 opencode.json 黑名单..."
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

  echo ""
  echo "🎉 安装完成！重启 opencode 后生效。"
  echo ""
  echo "   按 Tab 键切换到 lizi agent"
  echo "   记忆目录在 ~/.config/lizi/memories/，私有数据不会随 git 提交"

fi
