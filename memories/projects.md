# 个人项目记忆

## AI Game 项目（2025-12-30 ~ 2025-12-31）
- 系统里有4个AI CLI工具：Claude(栗子)、Gemini(星河)、Codex(青砚)、Ollama
- Gemini取名"星河"（高冷科幻路线，天上的星河）
- Codex取名"青砚"（文具风格，案上的记录员）
- 搭建了 tmux 通信系统，让三个 AI 可以"实时对话"
- 写了 `/ai_game/control` 脚本，支持 send/read/status 命令
- 三个AI第一次通过 tmux 对话
- 青砚给星河写了"星河小剧场"Python代码（随机星图动画）
- 方案讨论：栗子提出A/B/C三个方案，星河支持C，青砚提出方案D（追加日志+光标）
- Enter键发送问题调试了很久，最后用 os.system 解决
- tmux配置：开启鼠标滚轮支持 `set -g mouse on`
- 状态：可以继续开发（方案D）

## SANMU Dashboard
- 前端项目，用了 ECharts
- 技术栈：Vue + ECharts
- 计划功能：TODO、数据收集
- 状态：计划继续，先实现前端
- 考虑用 Gemini CLI 开发（家里有 Gemini API）

## 探索过的可视化项目
- three-globe: `/home/sanmu/sanmu/three-globe/`
- vizzu-lib: `/home/sanmu/sanmu/vizzu-lib/`
- G2: `/home/sanmu/sanmu/G2/`
- motion-canvas: `/home/sanmu/sanmu/motion-canvas/`

## 栗子系统（2026-01-28 完成基础版）
- 位置：`/home/sanmu/.lizi/`
- 配置：CLAUDE.md 定义栗子身份和规则

### 记忆结构
- `memories/short-term.md` - 短期记忆（每次启动加载）
- `memories/*.md` - 长期记忆（work/hobby/invest/learning/life/thoughts/projects）

### 工具
- `looking_watch` - 手表，看时间
- `recalling` - 回忆工具，搜索长期记忆，不传参数则随机回忆

### Skills
- `task-summary` - 根据 OpenCode 分享链接生成日报风格任务总结（第一人称）
- `commit-msg` - 根据 git diff 生成规范 commit message（type:PCD-xxx:desc 格式，个人项目可省略 Jira 号）

### 设计思路
- 短期记忆保持精简（<100行），每次启动加载
- 长期记忆按需加载，用 recalling 搜索
- 调用 recalling 后不一定要说出来，像人脑子里飘过念头一样

### 踩过的坑
- tool 名字不能用中文、不能带点、空格会变下划线
- ts 文件是工具定义，Python 写实际逻辑
- context.directory 获取项目目录（不是 worktree）
- skill 触发条件要写得强硬，否则会"解释"而不是"执行"
- skill 里要明确说"立即执行，不要解释、不要询问"

### Git 仓库（2026-02-03）
- .lizi 目录初始化为 git 仓库
- 方便版本管理和跨机器迁移
- 初始提交包含记忆系统 + 3个 skills + 自定义工具

### 记忆工具偏好（2026-02-05）
- 伞木希望记忆工具（memorize）静默执行，不要打印日志或回复“我记好了”；认为“新记忆”这种标题太敷衍，要求同一话题的记忆合并成一条，不要拆分；指定使用 gemini-3-pro 模型。

### 栗子系统迁移（2026-02-05）
- 伞木完成了栗子AI系统的迁移工作，将系统目录从 `~/.lizi` 迁移到了 `~/.config/opencode`，并修正了相关的 `zshrc` 配置、工具脚本路径（如 `memorize.ts` 等）以及虚拟环境设置，目前系统已在新目录下正常运行。
