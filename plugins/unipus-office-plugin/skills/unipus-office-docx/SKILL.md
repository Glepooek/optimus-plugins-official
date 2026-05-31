---
name: unipus:office:docx
license: MIT
metadata:
  version: "1.0.0"
  category: document-processing
  author: UAI
  sources:
    - "ECMA-376 Office Open XML File Formats"
    - "GB/T 9704-2012 Layout Standard for Official Documents"
    - "IEEE / ACM / APA / MLA / Chicago / Turabian Style Guides"
    - "Springer LNCS / Nature / HBR Document Templates"
description: >
  使用 OpenXML SDK（.NET）进行专业的 DOCX 文档创建、编辑和排版。
  三条流水线：(A) 从零创建新文档，(B) 填写/编辑已有文档内容，(C) 应用模板排版并通过 XSD 验证门控。
  只要用户希望生成、修改或排版 Word 文档，就必须使用此 Skill——
  包括"写报告"、"起草提案"、"制作合同"、"填写表单"、"按模板重排版"，
  或任何最终输出为 .docx 文件的任务。即使用户未明确提及"docx"，
  如果任务隐含需要可打印的正式文档，也应使用此 Skill。
triggers:
  - Word
  - docx
  - document
  - 文档
  - Word文档
  - 报告
  - 合同
  - 公文
  - 排版
  - 套模板
---

# unipus-office-docx

通过 CLI 工具或基于 OpenXML SDK（.NET）构建的 C# 脚本来创建、编辑和排版 DOCX 文档。

## 环境准备

**首次使用：** `bash scripts/setup.sh`（Windows 上使用 `powershell scripts/setup.ps1`，加 `--minimal` 跳过可选依赖）。

**每次会话首次操作：** 运行 `scripts/env_check.sh` — 若提示 `NOT READY` 则不得继续。（同一会话内后续操作可跳过）

## 快速上手：直接编写 C#

当任务需要结构性文档操作（自定义样式、复杂表格、多节布局、页眉/页脚、目录、图片），直接编写 C# 比使用 CLI 更高效。使用以下脚手架：

```csharp
// File: scripts/dotnet/task.csx  (or a new .cs in a Console project)
// dotnet run --project scripts/dotnet/UAIDocx.Cli -- run-script task.csx
#r "nuget: DocumentFormat.OpenXml, 3.2.0"

using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

using var doc = WordprocessingDocument.Create("output.docx", WordprocessingDocumentType.Document);
var mainPart = doc.AddMainDocumentPart();
mainPart.Document = new Document(new Body());

// --- 在此编写逻辑 ---
// 编写任何 C# 前，请先读对应的 Samples/*.cs 文件，其中包含已验证的模式。
// 参见下方"参考文件"节中的 Samples 对照表。
```

**编写 C# 前，请先阅读对应的 `Samples/*.cs` 文件** — 其中包含可编译、经 SDK 版本验证的模式。下方"参考文件"节的 Samples 对照表列出了主题与文件的对应关系。

## CLI 简写

以下所有 CLI 命令均以 `$CLI` 代指：
```bash
dotnet run --project scripts/dotnet/UAIDocx.Cli --
```

## 流水线路由

检查：用户是否提供了输入 .docx 文件？

```
用户任务
├─ 无输入文件 → 流水线 A：CREATE（创建）
│   信号词："写"、"创建"、"起草"、"生成"、"新建"、"做一份报告/提案/备忘录"
│   → 阅读 references/scenario_a_create.md
│
└─ 有输入 .docx
    ├─ 替换/填写/修改内容 → 流水线 B：FILL-EDIT（填写编辑）
    │   信号词："填写"、"替换"、"更新"、"修改文字"、"添加章节"、"编辑"
    │   → 阅读 references/scenario_b_edit_content.md
    │
    └─ 重排版/应用样式/套模板 → 流水线 C：FORMAT-APPLY（格式应用）
        信号词："重排版"、"套模板"、"重新设计"、"按此格式"、"套模板"、"排版"
        ├─ 模板为纯样式（无内容）→ C-1：OVERLAY（样式叠加）
        └─ 模板有结构（封面/目录/示例章节）→ C-2：BASE-REPLACE
            （以模板为基础，用用户内容替换示例内容）
        → 阅读 references/scenario_c_apply_template.md
```

若请求跨多条流水线，按顺序依次执行（如先 Create 再 Format-Apply）。

## 预处理

如需将 `.doc` 转换为 `.docx`：`scripts/doc_to_docx.sh input.doc output_dir/`

编辑前预览（避免直接读 XML）：`scripts/docx_preview.sh document.docx`

分析编辑场景的结构：`$CLI analyze --input document.docx`

## 方案 A：创建

先阅读 `references/scenario_a_create.md`、`references/typography_guide.md` 和 `references/design_principles.md`。从 `Samples/AestheticRecipeSamples.cs` 中选择与文档类型匹配的美学配方——不要自行发明格式参数值。CJK 内容还需阅读 `references/cjk_typography.md`。

**选择路径：**
- **简单**（纯文字、最少格式）：使用 CLI — `$CLI create --type report --output out.docx --config content.json`
- **结构性**（自定义样式、多节、目录、图片、复杂表格）：直接编写 C#，先阅读对应的 `Samples/*.cs`。

CLI 选项：`--type`（report|letter|memo|academic）、`--title`、`--author`、`--page-size`（letter|a4|legal|a3）、`--margins`（standard|narrow|wide）、`--header`、`--footer`、`--page-numbers`、`--toc`、`--content-json`。

完成后运行**验证流水线**（见下方）。

## 方案 B：编辑/填写

先阅读 `references/scenario_b_edit_content.md`。预览 → 分析 → 编辑 → 验证。

**选择路径：**
- **简单**（文本替换、占位符填写）：使用 CLI 子命令。
- **结构性**（添加/重组章节、修改样式、操作表格、插入图片）：直接编写 C#，先阅读 `references/openxml_element_order.md` 和对应的 `Samples/*.cs`。

可用的 CLI 编辑子命令：
- `replace-text --find "X" --replace "Y"`
- `fill-placeholders --data '{"key":"value"}'`
- `fill-table --data table.json`
- `insert-section`、`remove-section`、`update-header-footer`

```bash
$CLI edit replace-text --input in.docx --output out.docx --find "OLD" --replace "NEW"
$CLI edit fill-placeholders --input in.docx --output out.docx --data '{"name":"John"}'
```

完成后运行**验证流水线**。还需运行 diff 验证改动最小化：
```bash
$CLI diff --before in.docx --after out.docx
```

## 方案 C：套用模板

先阅读 `references/scenario_c_apply_template.md`。预览并分析源文档和模板。

```bash
$CLI apply-template --input source.docx --template template.docx --output out.docx
```

复杂模板操作（多模板合并、分节页眉/页脚、样式合并）请直接编写 C# — 参见下方"关键规则"中的必要模式。

运行**验证流水线**，再运行**硬性门控检查**：
```bash
$CLI validate --input out.docx --gate-check assets/xsd/business-rules.xsd
```
门控检查是**硬性要求**。通过前不得交付成果。若失败：诊断、修复、重新运行。

还需运行 diff 验证内容保留：`$CLI diff --before source.docx --after out.docx`

## 验证流水线

每次写操作后运行。方案 C 是**必须**执行；方案 A/B 为**建议**执行（仅在操作极简单时可跳过）。

```bash
$CLI merge-runs --input doc.docx                                    # 1. 合并 run
$CLI validate --input doc.docx --xsd assets/xsd/wml-subset.xsd     # 2. XSD 结构验证
$CLI validate --input doc.docx --business                           # 3. 业务规则验证
```

若 XSD 失败，自动修复后重试：
```bash
$CLI fix-order --input doc.docx
$CLI validate --input doc.docx --xsd assets/xsd/wml-subset.xsd
```

若 XSD 仍失败，回退到业务规则验证 + 预览：
```bash
$CLI validate --input doc.docx --business
scripts/docx_preview.sh doc.docx
# 验证：字体污染=0、表格数量正确、图形数量正确、sectPr 数量正确
```

最终预览：`scripts/docx_preview.sh doc.docx`

## 关键规则

这些规则防止文件损坏——OpenXML 对元素排序有严格要求。

**元素顺序**（属性必须在前）：

| 父元素 | 顺序 |
|--------|-------|
| `w:p`  | `pPr` → runs |
| `w:r`  | `rPr` → `t`/`br`/`tab` |
| `w:tbl`| `tblPr` → `tblGrid` → `tr` |
| `w:tr` | `trPr` → `tc` |
| `w:tc` | `tcPr` → `p`（至少 1 个 `<w:p/>`） |
| `w:body` | 块级内容 → `sectPr`（必须是最后一个子元素） |

**直接格式污染：** 从源文档复制内容时，内联 `rPr`（字体、颜色）和 `pPr`（边框、底纹、间距）会覆盖模板样式。始终清除直接格式——仅保留 `pStyle` 引用和 `t` 文本。表格内容同样需要清理（包括单元格内的 `pPr/rPr`）。

**修订标记：** `<w:del>` 使用 `<w:delText>`，绝不使用 `<w:t>`。`<w:ins>` 使用 `<w:t>`，绝不使用 `<w:delText>`。

**字体大小：** `w:sz` = 磅数 × 2（12pt → `sz="24"`）。页边距/间距单位为 DXA（1 英寸 = 1440，1cm ≈ 567）。

**标题样式必须包含 OutlineLevel：** 定义标题样式（Heading1、ThesisH1 等）时，`StyleParagraphProperties` 中必须包含 `new OutlineLevel { Val = N }`（H1→0、H2→1、H3→2）。否则 Word 视其为普通带样式文字——目录和导航窗格将无法正常工作。

**多模板合并：** 给定多个模板文件（字体、标题、分节）时，**务必先阅读** `references/scenario_c_apply_template.md` 中的"多模板合并"章节。关键规则：
- 将所有模板的样式合并到一个 styles.xml 中。结构（节/分节符）来自分节符模板。
- 每个内容段落必须出现且仅出现一次——插入分节符时绝不重复。
- 绝不插入空白段落作为填充或节分隔符。输出段落数必须等于输入段落数。使用分节符属性（`w:pPr` 内的 `w:sectPr`）和样式间距（`w:spacing` before/after）实现视觉间隔。
- 在每个章节标题前插入奇数页分节符，而不只是第一个。即使章节包含双栏内容，也必须以奇数页分节符开始；在标题后用第二个连续分节符切换为双栏。
- 双栏章节需要三个分节符：(1) 前一段 pPr 中的奇数页分节符；(2) 章节标题 pPr 中的连续分节符 + cols=2；(3) 正文最后一段 pPr 中的连续分节符 + cols=1（恢复单栏）。
- 为每个节复制分节符模板中的 `titlePg` 设置。摘要节和目录节通常需要 `titlePg=true`。

**多节页眉/页脚：** 含 10 个以上节的模板（如中文学位论文）每节有不同的页眉/页脚（罗马数字 vs 阿拉伯数字页码、不同区域不同页眉文字）。规则：
- 使用 C-2 Base-Replace：将模板复制为输出基础，然后替换正文内容。这样可自动保留所有节、页眉、页脚和 titlePg 设置。
- 绝不从头重新创建页眉/页脚——逐字节复制模板的页眉/页脚 XML。
- 绝不添加模板页眉 XML 中不存在的格式（边框、对齐、字号）。
- 非封面节必须有页眉/页脚 XML 文件（至少空页眉 + 页码页脚）。
- 参见 `references/scenario_c_apply_template.md` 中的"多节页眉/页脚转移"章节。

## 参考文件

按需加载——不要一次性全部加载。选择与当前任务最相关的文件。

**以下 C# 示例和设计参考是本项目的知识库（"百科全书"）。** 编写 OpenXML 代码时，必须先阅读对应的示例文件——其中包含可编译、经 SDK 版本验证的模式，可预防常见错误。做出美学决策时，阅读设计原则和配方文件——它们编码了来自权威来源（IEEE、ACM、APA、Nature 等）的经过验证的和谐参数组合，而非凭空猜测。

### 场景指南（每条流水线开始前必读）

| 文件 | 适用场景 |
|------|------|
| `references/scenario_a_create.md` | 流水线 A：从零创建 |
| `references/scenario_b_edit_content.md` | 流水线 B：编辑已有内容 |
| `references/scenario_c_apply_template.md` | 流水线 C：套用模板格式 |

### C# 代码示例（可编译、详细注释——编写代码前先阅读）

| 文件 | 主题 |
|------|-------|
| `Samples/DocumentCreationSamples.cs` | 文档生命周期：创建、打开、保存、流、文档默认值、设置、属性、页面设置、多节 |
| `Samples/StyleSystemSamples.cs` | 样式：Normal/Heading 链、字符/表格/列表样式、DocDefaults、latentStyles、CJK 公文、APA 7th、导入、解析继承 |
| `Samples/CharacterFormattingSamples.cs` | 字符属性（RunProperties）：字体、大小、粗体/斜体、各类下划线、颜色、高亮、删除线、上下标、大写、间距、底纹、边框、着重号 |
| `Samples/ParagraphFormattingSamples.cs` | 段落属性（ParagraphProperties）：对齐、缩进、行距/段距、孤行控制、大纲级别、边框、制表位、编号、双向文字、框架 |
| `Samples/TableSamples.cs` | 表格：边框、网格、单元格属性、边距、行高、标题行重复、合并（横向/纵向）、嵌套表格、浮动表格、三线表、斑马条纹 |
| `Samples/HeaderFooterSamples.cs` | 页眉/页脚：页码、"第 X 页/共 Y 页"、首页/偶数页/奇数页、Logo 图片、表格布局、公文"-X-"格式、分节设置 |
| `Samples/ImageSamples.cs` | 图片：内嵌、浮动、文字环绕、边框、替代文字、在页眉/表格中、替换、SVG 备用、尺寸计算 |
| `Samples/ListAndNumberingSamples.cs` | 编号：项目符号、多级十进制、自定义符号、大纲→标题、法律编号、中文 一/（一）/1./(1)、重启/续接 |
| `Samples/FieldAndTocSamples.cs` | 域代码：目录、SimpleField vs 复杂域、DATE/PAGE/REF/SEQ/MERGEFIELD/IF/STYLEREF、目录样式 |
| `Samples/FootnoteAndCommentSamples.cs` | 脚注、尾注、批注（4 文件系统）、书签、超链接（内部 + 外部） |
| `Samples/TrackChangesSamples.cs` | 修订标记：插入（w:t）、删除（w:delText!）、格式变更、接受/拒绝全部、移动跟踪 |
| `Samples/AestheticRecipeSamples.cs` | 13 种来自权威来源的美学配方：ModernCorporate、AcademicThesis、ExecutiveBrief、ChineseGovernment（GB/T 9704）、MinimalModern、IEEE Conference、ACM sigconf、APA 7th、MLA 9th、Chicago/Turabian、Springer LNCS、Nature、HBR——每种均包含来自官方样式指南的精确参数值 |

注：`Samples/` 路径相对于 `scripts/dotnet/UAIDocx.Core/`。

### Markdown 参考文件（需要规范或设计规则时阅读）

| 文件 | 适用场景 |
|------|------|
| `references/openxml_element_order.md` | XML 元素排序规则（防止文件损坏） |
| `references/openxml_units.md` | 单位换算：DXA、EMU、half-points、eighth-points |
| `references/openxml_encyclopedia_part1.md` | 详细 C# 百科全书：文档创建、样式、字符与段落格式 |
| `references/openxml_encyclopedia_part2.md` | 详细 C# 百科全书：页面设置、表格、页眉/页脚、节、文档属性 |
| `references/openxml_encyclopedia_part3.md` | 详细 C# 百科全书：目录、脚注、域代码、修订标记、批注、图片、数学公式、编号、保护 |
| `references/typography_guide.md` | 字体搭配、字号、间距、页面布局、表格设计、配色方案 |
| `references/cjk_typography.md` | CJK 字体、字号、RunFonts 映射、GB/T 9704 公文规范 |
| `references/cjk_university_template_guide.md` | 中国高校论文模板：数字样式 ID（1/2/3 vs Heading1）、文档区域结构（封面→摘要→目录→正文→参考文献）、字体预期、常见错误 |
| `references/design_principles.md` | **美学基础**：6 大设计原则（留白、对比/比例、接近、对齐、重复、层次）——解释"为什么"，而非"怎么做" |
| `references/design_good_bad_examples.md` | **好坏对比**：10 类排版错误，附 OpenXML 参数值、ASCII 示意图和修复方案 |
| `references/track_changes_guide.md` | 修订标记深度解析 |
| `references/troubleshooting.md` | **按症状索引的修复方案**：13 类常见问题，按所见现象（标题异常、图片缺失、目录损坏等）检索——找症状，得修复方案 |
