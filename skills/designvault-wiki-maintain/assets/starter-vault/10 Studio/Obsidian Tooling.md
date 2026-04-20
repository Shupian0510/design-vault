# Obsidian Tooling

这页只讲 vault 内的实际触发流。

## QuickAdd

QuickAdd 是带提示的新建入口。

建议至少保留这些命令：

- `QuickAdd: 新建 Wiki 页面`
- `QuickAdd: 新建设计长稿`
- `QuickAdd: 新建 Execution Plan`
- `QuickAdd: 新建 Execution Log`
- `QuickAdd: 新建 Change Review`

职责：

- 询问页面名称
- 把页面放到正确目录
- 套用正确模板
- 自动打开新页面
- 遇到重名时停止创建，而不是自动递增平行页

## Templater

Templater 是手动创建空白文件时的兜底模板系统。

建议的目录映射：

- `00 Wiki/Concepts/` -> `Concept Template`
- `00 Wiki/Rules/` -> `Rule Template`
- `00 Wiki/Surfaces/` -> `Surface Template`
- `10 Studio/Todo - Design/Longform/` -> `Longform Design Draft Template`
- `10 Studio/Execution Plans/` -> `Plan Template`
- `10 Studio/Execution Logs/` -> `Execution Log Template`
- `10 Studio/Todo - Personal/` -> `Personal Todo Template`
- `10 Studio/Change Review/` -> `Change Review Template`

## Dataview

Dataview 负责 dashboard 和索引视图。

建议让它只做：

- 列出执行记录
- 列出最近回写
- 列出待试玩项
- 列出待决策项

不要把长日志和原始执行输出直接塞进 dashboard。

## 公共版说明

这个 starter vault 已带一份公开版 `.obsidian/` 配置：

- 开启核心插件
- 声明社区插件列表
- 预填 QuickAdd 与 Templater 配置
- 附带一个安全的默认 workspace

但它**不包含社区插件二进制本体**。首次使用时仍需要你在 Obsidian 里安装：

- `QuickAdd`
- `Templater`
- `Dataview`

## 相关页面

- [[Workflow]]
- [[使用手册]]
- [[完整使用手册]]
