# ShengZhao Research Skills

个人科研与工程协作技能集，覆盖从研究构思、milestone 逐级验证、实验组织，到仿真接口调用和 IEEE 论文修订。各技能独立安装、按需使用，并随后续项目持续积累经验。

## 技能目录

| Skill | 当前版本 | 用途 | 入口 |
|---|---|---|---|
| `ai-research-project` | 0.3.0 | 从研究定位到可复现交付；重点复用 milestone 设计与最终实验案例 | [SKILL.md](skills/ai-research-project/SKILL.md) |
| `autoverse-skill` | 0.1.0 | 通过原生 avrs CLI / HTTP 查询和控制 Autoverse，并核对实际结果 | [SKILL.md](skills/autoverse-skill/SKILL.md) |
| `ieee-manuscript-redline-highlight` | 以技能文件为准 | 保留作者表达与科学证据，强化贡献叙事，交付净稿及完整增删对照稿 | [SKILL.md](skills/ieee-manuscript-redline-highlight/SKILL.md) |

## 安装与跨设备使用

在 GitHub 打开需要的 `skills/<skill-name>` 目录，将目录链接发给 Codex：

```text
使用 $skill-installer 安装这个 GitHub 技能目录：[粘贴目录链接]。
```

也可以克隆或下载本仓库，将需要的技能**整个目录**复制到当前环境实际使用的用户 skills 目录。保留 `references/`、`assets/`、`scripts/` 和 `agents/` 等配套文件；只复制 SKILL.md 会丢失参考和工具。避免在多个发现目录重复安装同名技能。

GitHub 用于保存版本和分发；在其他设备使用时，需要安装或更新对应副本。更新前保留尚未合并的本地修改。

## ai-research-project

将用户的方向、关键判断和资源转换成持续推进的科研工程过程，维护项目记忆、阶段证据和可验证交付。

- 按关键不确定性拆解 milestone，定义进入条件、最小验证、验收证据和下一决策。
- 分别记录实现完成、检验完成和研究假设是否获得支持。
- 收录 `thermal_tire_ggv` 的 M0–M5b 设计过程，解释预测排序、局部反馈、执行接口、整圈闭环和预算比较之间的关系。
- 将用户最终选定的实验作为实验设计与组织参考；阶段史与最终论证分别维护。
- 提供项目记忆、阶段案例和实验案例模板，支持逐项目积累个人经验。

```text
使用 $ai-research-project，读取当前项目资料，按我的习惯设计 milestone，并推进第一个可验证阶段。
```

也可只说：

```text
使用 $ai-research-project，按项目记录继续。
```

## autoverse-skill

复用项目中的实际接口经验，以及已安装官方 CLI 的源码核查结果。参考基线为 Autoverse 仿真包 0.36.2、autoverse-cli 0.28.2；新环境应核对实际版本、连接目标及对象名称。

- 轮胎物理摩擦读取、全部/单轮设置、临时基线恢复及读回。
- 回到赛道、移动到地标、按 NED/LLA 坐标传送及位姿核验。
- 对象、环境、输入模式等原生 CLI 与 HTTP 请求对照。
- 区分原生物理接口、项目 ROS 参数、CAN 遥测与持续控制者。
- 附带标准库 HTTP 工具、请求模板及离线测试，无原项目代码依赖。

```text
使用 $autoverse-skill，把 ego 四轮物理摩擦设为 0.9，并读回确认。
```

原生调用需要可连接的 Autoverse 实例。HTTP 工具使用 Python 3；ROS/CAN 联调仅在相应运行环境和当前任务需要时使用。

## ieee-manuscript-redline-highlight

IEEE 论文修订工作流：保留作者表达与科学证据，强化贡献叙事，并交付经过视觉核验的净稿与完整增删对照稿。

- 以明确版本、章节范围和比较基线开展修订，修改前保存 checkpoint。
- 围绕证据支持的贡献组织叙事，减少自我削弱和项目汇报式表述。
- 保留数值、单位、比较口径、重要不利结果及结论成立条件。
- 生成净稿与完整增删对照：新增黄色高亮，删除红色删除线。
- 编译、渲染并查看修改页，核对最终交付文件。

```text
使用 $ieee-manuscript-redline-highlight，润色指定稿件的第 III–VI 节，保留技术事实、数值与作者表达，并交付净稿和完整增删对照 PDF。
```

任务中说明稿件位置、章节范围及比较基线。技能包含 [LaTeX 增删与视觉核验说明](skills/ieee-manuscript-redline-highlight/references/latex-redline.md)；生成和核验 PDF 的环境需要 LaTeX 工具链、`latexdiff`、PDF 渲染工具（如 `pdftoppm`）和图像查看能力。

## 维护

每个技能维护在 `skills/<skill-name>/`，保留自己的版本与配套文件。将已确认的方法、案例和偏好合并到相应技能，再提交至仓库；项目专属参数与临时操作状态保留适用范围。

新增项目时，`ai-research-project` 可以继续追加阶段设计和最终实验案例，合并已有规则；新增技能则加入技能目录并提供独立入口。
