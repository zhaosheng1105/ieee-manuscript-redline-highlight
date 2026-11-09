# LaTeX 净稿与增删对照

适用于已有 LaTeX/Overleaf 稿件的修订。以下命令中的目录是示例，应替换成当前任务路径；编译引擎沿用项目原有设置。

## 基线与构建目录

将原始基线与修订版放在不同目录，保留原始 ZIP 成员清单和本轮 checkpoint。先编译净稿，再构建对照。保留主文件及其子文件、图片、参考文献的相对路径；从修订项目目录启动编译，避免工作目录变化导致找不到图表或 `.bib`。

例如，工作目录为修订项目根目录时：

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=/tmp/revision-build/clean main.tex
latexdiff --flatten --math-markup=0 --graphics-markup=0 --preamble=/tmp/revision-build/diff-preamble.tex /absolute/baseline/main.tex /absolute/revision/main.tex > /tmp/revision-build/main_changes.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=/tmp/revision-build/redline /tmp/revision-build/main_changes.tex
```

`--flatten` 展开被包含的章节。这里关闭数学和图片内部的增删标记，以减少复杂公式、浮动体的破坏；这不代表数学和图片未变化，必须另外比较源码并报告实际变化。若用户要求突出数学改动，单独设计可读的标注方式并验证。

## 黄色新增与红色删除线

可把以下内容保存为上述 `diff-preamble.tex`。`ulem` 的覆盖标记适合含 inline math、citation 的学术段落；`soul` 的 `\hl` 在复杂命令中可能失败，不能仅凭纯文本例子判断可用。

```tex
\RequirePackage{xcolor}
\RequirePackage[normalem]{ulem}
\definecolor{DiffHighlight}{RGB}{255,236,139}
\definecolor{DiffDelete}{RGB}{170,35,45}
\DeclareRobustCommand{\DIFadd}[1]{{\color{black}\bgroup
  \markoverwith{\textcolor{DiffHighlight}{\rule[-0.5ex]{2pt}{2.5ex}}}
  \ULon{#1}}}
\DeclareRobustCommand{\DIFdel}[1]{{\color{DiffDelete}\sout{#1}}}
\providecommand{\DIFaddbegin}{}
\providecommand{\DIFaddend}{}
\providecommand{\DIFdelbegin}{}
\providecommand{\DIFdelend}{}
\DeclareRobustCommand{\DIFaddFL}[1]{\DIFadd{#1}}
\DeclareRobustCommand{\DIFdelFL}[1]{\DIFdel{#1}}
\providecommand{\DIFaddbeginFL}{}
\providecommand{\DIFaddendFL}{}
\providecommand{\DIFdelbeginFL}{}
\providecommand{\DIFdelendFL}{}
\makeatletter
\AtBeginDocument{\@ifpackageloaded{hyperref}{%
  \pdfstringdefDisableCommands{\def\DIFadd#1{#1}\def\DIFdel#1{}}%
}{}}
\makeatother
```

检查生成的 preamble；启用 `hyperref` 时，`latexdiff` 可能把底层命令改名为 `\DIFaddtex`、`\DIFdeltex` 并添加包装器。若需修复样式，编辑实际生成的定义，避免修改一个未被调用的同名宏。

上述样式不是所有 TeX 命令的通用保证。若局部命令无法被 `ulem` 正确处理，可在派生对照文件中给短小的数学/引用单元加 `\mbox{...}`，或调整该局部的标记边界。不要把整段放进 `\mbox`，否则无法换行。

## 对照文件常见问题

- 删除的 `\eqref` 等命令可能出现在 `%DIFDELCMD < ... %%%` 注释中，导致 PDF 显示“Equation”却没有编号。核对旧文及 label 是否仍存在；在派生对照中恢复安全的局部表示，例如 `\DIFdel{Equation~\mbox{\eqref{eq:example}}}`。若重新编号，明确比较的是文字修改还是原始显示编号，不能误配编号。
- 增删边界有时吞掉词间空格，如 `memoryform`。检查删除线、黄色块与普通文本之间的空隙，仅修复派生对照中的排版，不反向修改准确的源码。
- 被删除的标题、交叉引用和浮动体可能影响编号与分页；查看渲染结果，确保读者能够识别删除内容与当前结构。
- 解析源码中的注释或恢复新旧文本时，注意 `\%` 是正文百分号，不能用简单的 `%.*` 规则删掉。复杂命令需要处理成对括号，不要依赖单个正则表达式剥离所有标记。

标记让段落变长或抑制断词时，可能出现净稿没有的 overfull。只在派生对照中处理：先调整局部标记边界；表头同时显示旧新词时可局部缩小列间距；少量难以断行的对照段可用 `\begingroup\raggedright ... \par\endgroup`，随后渲染检查。不要为了容纳红线修改净稿、全局缩小字号或全篇改成不符合模板的对齐方式。`\emergencystretch`可能消除溢出却留下很宽的词间距，仍须目视判断。

## 验证与发布

检查编译退出状态与日志中的错误、缺失引用/文件和新增 overfull box；对 underfull 等排版警告，结合渲染判断影响。用 `pdftoppm` 渲染改动页并查看，必要时查看相邻页。文本提取可以辅助发现漏文，但不能替代视觉检查。

将章节范围外的文件与基线逐项比较；检查数学表达、数值、单位、引用 key、label 和图表是否按预期保留。增删标记必须分别对应正确的旧版与新版，不能把构建错误当成作者删除。可恢复旧/新文本进行归一化比较，也可对复杂块做定点人工核对。

最后将验证过的净稿 PDF、对照 PDF 和对照 TeX 复制到正式交付位置。按原始 ZIP 成员清单重新打包修订源码；若新增编译必需文件，再有意加入并记录。不要递归打包整个修订目录，把 checkpoint、日志、临时 PDF 或对照源码意外带入 Overleaf。检查新 ZIP 可读取、成员正确、修改文件范围正确，确认正式交付文件对应本轮最新源码后再报告完成。
