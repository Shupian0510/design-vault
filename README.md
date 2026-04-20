# DesignVault Skills

[中文](#中文) | [English](#english)

---

## 中文

### 这是什么

`designvault-skills` 是从 `AgentMarket` 工作流中提炼出的可复用公开骨架。

它的目标不是导出某个项目的私有设计文档，而是把一套稳定的方法论公开出来：

- 用 `LLM Wiki` 保存当前真相
- 用 `spec coding` 把设计和实现拆开
- 用 `/design`、`/execute`、`/bug` 三条 lane 管理 AI 开发
- 用 subagent、automation、skills、Unity MCP、Obsidian 降低单线程上下文成本

一句话原则：

> `Longform 负责设计推敲，Wiki 负责当前真相，Execution Plan 负责工程实施。`

### 核心思想：LLM Wiki + Spec Coding

#### 1. LLM Wiki

这里的 wiki 不是展示站，也不是人类笔记堆。

它是给人和 AI 共用的“真相层”：

- `00 Wiki/` 只放当前批准过的稳定定义
- 页面尽量短、聚焦、可检索
- AI 先读 wiki，再改代码
- 代码改完，如果真相变了，再回写 wiki

这能解决两个常见问题：

1. 聊天上下文会漂移
2. 代码、说明、设计稿很容易各写各的

#### 2. Spec Coding

这里的 spec 不是重模板文档主义，而是把“设计思考”和“工程执行”拆开。

标准分层是：

- `Longform`
  - 用来推敲设计、记录取舍、保留开放问题
- `Wiki Truth`
  - 用来保存当前稳定真相
- `Execution Plan`
  - 用来定义实现顺序、phase、验证方式、停机条件、回写目标
- `Execution Log`
  - 用来记录 `/execute` 的 preflight、phase handoff、acceptance 和后续 playtest 关注点

关键约束：

- `Execution Plan` 必须引用 wiki，而不是变成第二份 wiki
- `/design` 结束在 plan，不直接写代码
- `/execute` 默认线性按 phase 跑完
- `/bug` 从现象出发，优先窄修；如果根因是设计问题，再回 `/design`

### 工作流总览

默认主链路：

`/design -> /execute -> 人类试玩反馈需要时走 /bug`

三个入口分别处理：

- `/design`
  - 读最小必要 wiki
  - grill 问题
  - 收敛成长稿
  - 更新 wiki
  - 生成完整 implementation plan
- `/execute`
  - 读一个 implementation plan
  - preflight
  - phase 线性执行
  - acceptance
  - wiki writeback
  - execution log
- `/bug`
  - 从症状开始
  - 先读最小必要 wiki
  - 查实现并修复
  - 做最窄验证
  - 轻量更新 wiki / execution log

### 仓库包含什么

- `skills/designvault-design/`
  - `/design` lane
- `skills/designvault-execute/`
  - `/execute` lane
  - 包含执行编排脚本
  - 包含可选的 subagent 模板
- `skills/designvault-bug/`
  - `/bug` lane
- `skills/designvault-ui-handoff/`
  - UI 逻辑和样式边界约束
- `skills/designvault-wiki-maintain/`
  - starter vault
  - lint / search / trace / writeback 建议脚本

### 这个公开仓库不包含什么

- AgentMarket 当前项目自己的真相页
- AgentMarket 正在使用中的 execution plans / logs / dashboards
- 用户本机 Obsidian 工作区状态
- Unity 项目本身
- 某个具体 AI 工具私有的账号、密钥、插件状态

---

### 目录结构

```text
skills/
  designvault-design/
  designvault-execute/
  designvault-bug/
  designvault-ui-handoff/
  designvault-wiki-maintain/
```

其中最关键的两个公共资产是：

- `skills/designvault-wiki-maintain/assets/starter-vault/`
  - 可复制到项目里的 wiki 骨架
- `skills/designvault-execute/assets/optional-agents/`
  - 可复制到项目里的 subagent 模板

---

### 如何在 Codex 中配置

这是本仓库最直接支持的目标环境。

#### 1. 安装 skills

PowerShell 示例：

```powershell
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }
New-Item -ItemType Directory -Force (Join-Path $CodexHome "skills") | Out-Null

Copy-Item -Recurse -Force .\skills\designvault-design        (Join-Path $CodexHome "skills")
Copy-Item -Recurse -Force .\skills\designvault-execute       (Join-Path $CodexHome "skills")
Copy-Item -Recurse -Force .\skills\designvault-bug           (Join-Path $CodexHome "skills")
Copy-Item -Recurse -Force .\skills\designvault-ui-handoff    (Join-Path $CodexHome "skills")
Copy-Item -Recurse -Force .\skills\designvault-wiki-maintain (Join-Path $CodexHome "skills")
```

也可以不复制，直接在当前仓库里维护，然后按需同步到 `~/.codex/skills/`。

#### 2. 在项目中放入 starter vault

```powershell
Copy-Item -Recurse -Force `
  .\skills\designvault-wiki-maintain\assets\starter-vault `
  .\Docs\DesignVault
```

#### 3. 配置可选 subagent

```powershell
New-Item -ItemType Directory -Force .\.codex\agents | Out-Null

Copy-Item -Force `
  .\skills\designvault-execute\assets\optional-agents\phase-executor.toml `
  .\.codex\agents\

Copy-Item -Force `
  .\skills\designvault-execute\assets\optional-agents\acceptance-executor.toml `
  .\.codex\agents\
```

推荐再补一个项目级 `.codex/config.toml`：

```toml
[agents]
max_threads = 3
max_depth = 1
```

#### 4. 验证 starter vault

```powershell
pwsh -File `
  "$CodexHome\skills\designvault-wiki-maintain\scripts\wiki_lint.ps1" `
  -VaultRoot .\Docs\DesignVault
```

#### 5. 推荐最小使用口令

```text
/design 这个功能。先 grill 关键设计问题，再收敛成长稿和 implementation plan。
```

```text
/execute 这个 implementation plan。
```

```text
/bug 这个问题：<现象描述>
```

---

### 如何配置 Obsidian

starter vault 已包含一份**公开版、安全的** `.obsidian/` 配置。

要真正使用这套配置，仍然需要在 Obsidian 里安装这三类社区插件：

- `QuickAdd`
- `Templater`
- `Dataview`

#### 建议的 Obsidian 角色分工

- `QuickAdd`
  - 负责带提示的新建入口
- `Templater`
  - 负责手动创建空白文件时的兜底模板映射
- `Dataview`
  - 负责索引和 dashboard 视图

#### 推荐保留的 QuickAdd 命令

- 新建 Wiki 页面
- 新建设计长稿
- 新建 Execution Plan
- 新建 Execution Log
- 新建 Change Review

#### 推荐的 Templater 目录映射

- `00 Wiki/Concepts/` -> `Concept Template.md`
- `00 Wiki/Surfaces/` -> `Surface Template.md`
- `10 Studio/Todo - Design/Longform/` -> `Longform Design Draft Template.md`
- `10 Studio/Execution Plans/` -> `Plan Template.md`
- `10 Studio/Execution Logs/` -> `Execution Log Template.md`
- `10 Studio/Todo - Personal/` -> `Personal Todo Template.md`
- `10 Studio/Change Review/` -> `Change Review Template.md`

#### 当前 starter vault 已包含

- 社区插件列表
- QuickAdd 配置
- Templater 配置
- 一个安全的默认 workspace

#### 推荐做法

- 把 `Docs/DesignVault/` 作为 Obsidian vault root
- 把 `_Templates/` 设成模板目录
- 把插件私有状态保存在本地 `.obsidian/`
- 不要把 workspace 状态当成这个公开仓库的一部分

---

### 如何配置 Unity MCP

这个仓库不自带 Unity MCP，默认假设目标环境中已经安装并能连接 Unity Editor。

推荐执行方式：

- Unity 编辑器里的真实执行和验证，优先走 `Unity MCP`
- `/execute` 的 machine evidence，优先看：
  - compile
  - console
  - targeted tests
- 场景、prefab、运行态 UI 验证尽量通过 Unity MCP 做，不靠猜

换句话说，`DesignVault` 负责“流程和真相”，`Unity MCP` 负责“Unity 编辑器执行桥”。

---

### 如何在 Claude Code 中配置

根据 Anthropic 官方文档，Claude Code 目前支持：

- `CLAUDE.md`
- `.claude/settings.json`
- `.claude/skills/*/SKILL.md`
- `.claude/agents/*`

#### 推荐映射方式

1. 把本仓库的 skill 目录复制或软链接到：
   - `.claude/skills/`
2. 在仓库根目录写 `CLAUDE.md`
   - 说明 `Docs/DesignVault` 的角色
   - 规定先读 wiki 再动实现
3. 把 `phase_executor` / `acceptance_executor` 改写成 Claude Code 的 subagent 文件
   - Claude Code 的 subagent 是 Markdown + YAML frontmatter
   - 不能直接把这里的 `.toml` 原样塞进去
4. 如需共享权限、工具行为，再加 `.claude/settings.json`

#### 最小建议

- skills 用这个仓库里的 `skills/`
- instructions 用 `CLAUDE.md`
- subagents 用 `.claude/agents/phase-executor.md` 和 `.claude/agents/acceptance-executor.md`

---

### 如何在 OpenCode 中配置

根据 OpenCode 官方文档，OpenCode 原生支持：

- `opencode.json`
- `.opencode/agents/`
- `.opencode/skills/`
- 以及兼容发现：
  - `.claude/skills/`
  - `.agents/skills/`

#### 推荐映射方式

1. 直接把 skill 目录放到以下任一位置：
   - `.opencode/skills/`
   - `.agents/skills/`
   - `.claude/skills/`
2. 在 `opencode.json` 中配置：
   - `instructions`
   - `agent`
   - `command`
   - `mcp`
3. 把 `phase_executor` / `acceptance_executor` 改写成：
   - `.opencode/agents/*.md`
   - 或 `opencode.json` 里的 agent 配置

#### 一个最小 `opencode.json` 示例

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["README.md", "AGENTS.md"],
  "default_agent": "build",
  "agent": {
    "phase-executor": {
      "description": "Execute one DesignVault phase with bounded scope",
      "mode": "subagent",
      "model": "openai/gpt-5",
      "reasoningEffort": "high"
    },
    "acceptance-executor": {
      "description": "Run bounded acceptance for one DesignVault execution",
      "mode": "subagent",
      "model": "openai/gpt-5",
      "reasoningEffort": "high"
    }
  }
}
```

如果已经在使用 `.claude/skills/` 或 `.agents/skills/`，OpenCode 可以直接发现它们，不一定要复制两遍。

---

### 给 AI 助手看的安装提示词

下面这段提示词可直接交给 Codex、Claude Code、OpenCode 一类 agent，用于自动初始化 DesignVault 工作流。

```text
请把当前项目初始化为 DesignVault 工作流仓库。

目标：
1. 安装或接入 designvault-design、designvault-execute、designvault-bug、designvault-ui-handoff、designvault-wiki-maintain 五个 skills。
2. 在项目内创建或更新 Docs/DesignVault，使用 starter-vault 作为初始骨架。
3. 为当前工具配置两类 subagent：
   - phase executor：只负责单个 implementation phase
   - acceptance executor：只负责 acceptance
4. 如果当前工具支持 skills、agents、instructions、MCP，请使用它的原生目录和配置格式，不要生搬硬套别的工具格式。
5. 如果当前工具支持项目级说明文件，请写入以下约束：
   - 先读最小必要 wiki，再读实现
   - Wiki 是真相，Execution Plan 是执行合同，不是第二份 wiki
   - /design 结束在 plan，不直接写代码
   - /execute 线性按 phase 执行，结束后写 execution log
   - /bug 从现象出发，若根因是设计问题则停并回 /design
6. 如果项目包含 Unity，请把 Unity MCP 作为 Unity 编辑器执行和验证的首选桥接方式。
7. 如果项目使用 Obsidian，请说明还需要手动安装 QuickAdd、Templater、Dataview，并把 _Templates 配成模板来源。

交付要求：
1. 列出你创建或修改的所有配置文件。
2. 明确说明哪些文件已经自动配置，哪些仍需人工补齐。
3. 运行一次 starter vault 的 lint，并报告结果。
4. 不要修改业务代码；只做 workflow、skills、agents、wiki、automation 相关配置。
```

---

### 推荐使用环境

推荐环境组合：

- `Codex`
  - 负责主线程执行、automation、subagent orchestration、skills
- `Unity MCP`
  - 负责 Unity Editor 执行、检查和测试
- `Obsidian`
  - 负责人类工作区、wiki 浏览、模板和 dashboard

这三者的职责不要混：

- `Codex` 不是 wiki 本体
- `Obsidian` 不是执行引擎
- `Unity MCP` 不是设计真相层

---

## English

### What This Repo Is

`designvault-skills` is the reusable public shell extracted from the workflow used inside `AgentMarket`.

It is built around two ideas:

- `LLM Wiki`: keep stable truth in a retrieval-friendly wiki layer
- `Spec Coding`: separate design convergence from implementation execution

The public package exposes the workflow, not the private project truth.

### Core Model

The operating rule is:

> `Longform shapes the design, Wiki stores current truth, Execution Plan drives implementation.`

Artifact roles:

- `Longform`
  - design reasoning, tradeoffs, open questions
- `Wiki Truth`
  - current approved truth
- `Execution Plan`
  - implementation contract, phase order, validation, stop conditions, writeback targets
- `Execution Log`
  - preflight, handoff, acceptance, follow-up playtest focus

Default flow:

`/design -> /execute -> /bug when later human observation finds a narrow issue`

### What Is Included

- reusable skills for `/design`, `/execute`, `/bug`
- a UI handoff skill
- wiki maintenance scripts
- a starter vault
- deterministic `/execute` helper scripts
- optional subagent templates

### Codex Setup

1. Copy or sync the five skill folders into `~/.codex/skills/` or `$CODEX_HOME/skills/`.
2. Copy `skills/designvault-wiki-maintain/assets/starter-vault/` into your project as `Docs/DesignVault/`.
3. Copy optional subagent templates from:
   - `skills/designvault-execute/assets/optional-agents/phase-executor.toml`
   - `skills/designvault-execute/assets/optional-agents/acceptance-executor.toml`
4. Add a project `.codex/config.toml` if you want the same bounded subagent model:

```toml
[agents]
max_threads = 3
max_depth = 1
```

5. Run the starter-vault lint.

### Obsidian Setup

This repo now ships a public-safe starter `.obsidian/` config.

To actually use it, you still need to install and enable:

- `QuickAdd`
- `Templater`
- `Dataview`

Recommended vault root:

- `Docs/DesignVault/`

Recommended template root:

- `_Templates/`

### Unity MCP Setup

This repo assumes Unity MCP is installed in your actual toolchain.

Use Unity MCP as the execution bridge for:

- editor-side verification
- compile / console checks
- targeted tests
- scene / prefab / runtime inspection

### Claude Code Setup

According to Anthropic’s current docs, Claude Code supports:

- `CLAUDE.md`
- `.claude/settings.json`
- `.claude/skills/*/SKILL.md`
- `.claude/agents/*`

Recommended mapping:

1. Put the skills into `.claude/skills/`
2. Put your repo-level workflow instructions into `CLAUDE.md`
3. Rewrite the optional phase / acceptance agents into Claude Code subagent files
4. Use `.claude/settings.json` for shared tool and permission behavior

Important:

- Claude Code skills are compatible with the skills model
- Claude Code subagents are not TOML; they need Claude’s own agent format

### OpenCode Setup

According to OpenCode’s current docs, OpenCode supports:

- `opencode.json`
- `.opencode/agents/`
- `.opencode/skills/`
- and also discovers `.claude/skills/` and `.agents/skills/`

Recommended mapping:

1. Put the skills into `.opencode/skills/`, `.agents/skills/`, or `.claude/skills/`
2. Configure instructions, agents, commands, and MCP in `opencode.json`
3. Rewrite the optional phase / acceptance agents as OpenCode agents

### Generic AI Bootstrap Prompt

Use the Chinese prompt above as a bootstrap task for any coding agent.

Its job is to:

- install skills
- create `Docs/DesignVault`
- configure subagents in the tool’s native format
- wire the workflow constraints into the project instructions
- run starter-vault lint
- report what still requires manual setup

### Recommended Environment

Recommended environment:

- `Codex` for orchestration, skills, automation, and subagents
- `Unity MCP` for Unity execution and evidence
- `Obsidian` for the human-facing wiki workspace

They should stay separated:

- `Codex` is not the wiki itself
- `Obsidian` is not the execution engine
- `Unity MCP` is not the source of design truth

---

## License

MIT
