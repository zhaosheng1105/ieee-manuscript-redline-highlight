# ieee-manuscript-redline-highlight

IEEE 论文修订 skill：保留作者表达与科学证据，强化贡献叙事，并交付经过视觉核验的净稿与完整增删对照稿。

## 功能

- 以明确版本、章节范围和比较基线开展修订，修改前保存 checkpoint。
- 围绕证据支持的贡献组织叙事，减少自我削弱和项目汇报式表述。
- 保留数值、单位、比较口径、重要不利结果及结论成立条件。
- 生成净稿与完整增删对照：新增黄色高亮，删除红色删除线。
- 编译、渲染并查看修改页，核对最终交付文件。

## 在另一台电脑安装

在 Codex 中发送：

```text
使用 $skill-installer 从 GitHub 仓库 zhaosheng1105/ieee-manuscript-redline-highlight 安装 skills/ieee-manuscript-redline-highlight。
```

也可以克隆仓库，再将 `skills/ieee-manuscript-redline-highlight` 整个目录复制到本机 Codex 的用户 skill 目录。当前官方文档使用 `~/.agents/skills/`；已有配置使用 `~/.codex/skills/` 的环境，请采用该环境实际发现的目录。只安装一份，避免重复同名条目。

安装后若未显示，重启 Codex 或新建会话。GitHub 用于保存版本及分发，各设备需要安装；登录相同账号不会自动拉取仓库更新。

## 使用

```text
$ieee-manuscript-redline-highlight
请润色指定稿件的第 III–VI 节，保留技术事实、数值与作者表达，并交付净稿和完整增删对照 PDF。
```

请在任务中说明稿件位置、章节范围，以及需要采用的比较基线。

## 文件

- `skills/ieee-manuscript-redline-highlight/SKILL.md`：修订工作流。
- `skills/ieee-manuscript-redline-highlight/agents/openai.yaml`：界面名称与调用提示。
- `skills/ieee-manuscript-redline-highlight/references/latex-redline.md`：LaTeX 编译、增删标记和视觉核验指引。

Skill 本身不包含 TeX 或 PDF 工具。生成并核验 PDF 的执行环境需要可用的 LaTeX 工具链、`latexdiff`、PDF 渲染工具（如 `pdftoppm`）及图像查看能力。

## 更新

修改 skill 后提交并推送到本仓库，再在其他设备更新本地安装的副本。更新前保留尚未提交的本地修改。
