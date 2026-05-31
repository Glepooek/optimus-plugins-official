# 故障排查指南——按症状索引

## 使用指南

按您**观察到的症状**搜索，而不是技术概念。每条条目包含：
- **症状** — 您看到或用户反映的问题
- **诊断** — 如何确认根本原因
- **修复** — 精确的步骤、命令或代码
- **预防** — 下次如何避免

**快速搜索关键词：** 标题错误、正文文字、修复、损坏、字体、表格丢失、图片丢失、目录损坏、更新目录、分页符、分节符、超链接、编号列表、项目符号、页边距、页面尺寸、中文方块、封面、修订跟踪、修订标记

---

## 1. "所有标题看起来像正文"（标题样式未应用）

**症状：** 应用模板后，标题没有格式——看起来像普通段落，字号、粗体、间距全部错误。

**诊断：** `document.xml` 中的 `pStyle` 值与 `styles.xml` 中的 `styleId` 值不匹配。

常见不匹配：
- 源文档使用 `Heading1`，但模板将样式定义为 `1`（中国模板常使用数字 styleId）
- 源文档使用 `heading1`（小写），但模板是 `Heading1`（区分大小写！）
- `pStyle` 引用的样式在输出文档的 `styles.xml` 中根本不存在

诊断命令：
```bash
# 列出文档中使用的所有 pStyle 值
$CLI analyze --input output.docx | grep -i "pStyle"

# 列出 styles.xml 中定义的所有 styleId
$CLI analyze --input template.docx --part styles | grep "styleId"
```

**修复：** 应用模板之前先建立 styleId 映射表，更新文档内容中的所有 `pStyle` 值。

```csharp
// 构建映射：源 styleId → 模板 styleId
var mapping = new Dictionary<string, string>();
// 按样式名称（w:name）比较，而不是 styleId
foreach (var srcStyle in sourceStyles)
{
    var templateStyle = templateStyles.FirstOrDefault(
        s => s.StyleName?.Val?.Value == srcStyle.StyleName?.Val?.Value);
    if (templateStyle != null)
        mapping[srcStyle.StyleId!] = templateStyle.StyleId!;
}

// 将映射应用于所有段落
foreach (var para in body.Descendants<Paragraph>())
{
    var pStyle = para.ParagraphProperties?.ParagraphStyleId;
    if (pStyle != null && mapping.TryGetValue(pStyle.Val!, out var newId))
        pStyle.Val = newId;
}
```

**预防：** 应用模板之前**始终**从源文档和模板中提取并比较 styleId。绝不假设 styleId 在不同文档间相同。

---

## 2. "文档打开时出现修复警告"（XML 损坏）

**症状：** Word 打开时提示"发现内容存在问题"或"发现无法读取的内容"。

**诊断：** 元素顺序错误。OpenXML 对子元素顺序有严格要求。

常见违规：
- `pPr` 必须在 `w:p` 中的 run 之前
- `tblPr` 必须在 `w:tbl` 中的 `tblGrid` 之前
- `rPr` 必须在 `w:r` 中的 `t`/`br`/`tab` 之前
- `trPr` 必须在 `w:tr` 中的 `tc` 之前
- `tcPr` 必须在 `w:tc` 中的内容之前

```bash
# 验证以查找顺序问题
$CLI validate --input doc.docx --xsd assets/xsd/wml-subset.xsd

# 自动修复元素顺序
$CLI fix-order --input doc.docx

# 重新验证
$CLI validate --input doc.docx --xsd assets/xsd/wml-subset.xsd
```

**修复：**
```bash
$CLI fix-order --input doc.docx
```

如果自动修复无效，手动解压检查：
```bash
$CLI unpack --input doc.docx --output unpacked/
# 检查 word/document.xml 的顺序问题
# 修复后重新打包：
$CLI pack --input unpacked/ --output fixed.docx
```

**预防：** 编写任何 XML 操作代码之前先阅读 `references/openxml_element_order.md`。始终先追加属性元素，再追加内容元素。

---

## 3. "所有文字使用了错误的字体"（字体污染）

**症状：** 模板指定了宋体/Times New Roman，但文档显示的是 Google Sans、Arial、Calibri 或源文档使用的任意字体。

**诊断：** 源文档的 `rPr` 包含内联的 `rFonts` 声明，覆盖了模板样式。在 OpenXML 中，直接格式化始终优先于样式格式化。

```bash
# 检查字体污染
$CLI analyze --input output.docx | grep -i "font"
# 查找内容中的 rFonts——如果存在，它们正在覆盖样式
```

**修复：** 复制内容时去除 `rPr` 中的 `rFonts`，但**保留** CJK 文字的 `w:eastAsia`：

```csharp
foreach (var rPr in body.Descendants<RunProperties>())
{
    var rFonts = rPr.GetFirstChild<RunFonts>();
    if (rFonts != null)
    {
        // 为 CJK 保留 EastAsia 字体——删除它会导致方块（□□□）
        var eastAsia = rFonts.EastAsia?.Value;
        rFonts.Remove();

        // 仅当 eastAsia 已设置时重新添加
        if (!string.IsNullOrEmpty(eastAsia))
        {
            rPr.Append(new RunFonts { EastAsia = eastAsia });
        }
    }
}
```

同时去除这些常见的直接格式覆盖：
- `w:sz` / `w:szCs`（字号）
- `w:color`（文字颜色）
- 与样式矛盾的 `w:b` / `w:i`

**预防：** 在文档间复制内容时始终清理直接格式。只保留 `pStyle`/`rStyle` 引用和 `w:t` 文字。

---

## 4. "表格丢失"（复制时表格消失）

**症状：** 源文档有 5 张表格，但输出只有 2 张（或 0 张）。

**诊断：** 代码使用了顶层的 `body.findall('w:p')` 或 `body.Descendants<Paragraph>()`，跳过了 `w:tbl` 元素。

```bash
# 验证表格数量
$CLI analyze --input source.docx | grep -i "table"
$CLI analyze --input output.docx | grep -i "table"
```

**修复：** 使用 `list(body)` 或 `body.ChildElements` 获取**所有**顶层子元素，包括表格：

```csharp
// 错误——跳过了表格、节属性和其他非段落元素
var paragraphs = body.Elements<Paragraph>();

// 正确——获取所有内容：段落、表格、SDT 块等
var allElements = body.ChildElements.ToList();
```

使用 lxml（Python）时：
```python
# 错误
elements = body.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')

# 正确
elements = list(body)  # 所有直接子元素
```

**预防：** 复制内容时始终使用 `list(body)` 或 `body.ChildElements` 进行遍历，不要单独按元素类型过滤。

---

## 5. "图片丢失或显示损坏图标"

**症状：** 图片占位符出现但图片不渲染，或图片完全缺失。

**诊断：** `w:drawing` 中的 `r:embed` rId 与 `document.xml.rels` 中没有对应的关系，或媒体文件没有复制到输出 ZIP。

```bash
# 检查关系
$CLI analyze --input output.docx --part rels | grep -i "image"

# 检查媒体文件是否存在
$CLI unpack --input output.docx --output unpacked/
ls unpacked/word/media/
```

**修复：**
1. 检查源文档 rels 中的图片文件路径
2. 将媒体文件从源文档复制到输出
3. 在输出 rels 中添加/更新关系
4. 更新绘图元素中的 `r:embed` 值

```csharp
// 在文档间复制含图片的内容时：
foreach (var drawing in body.Descendants<Drawing>())
{
    var blip = drawing.Descendants<DocumentFormat.OpenXml.Drawing.Blip>().FirstOrDefault();
    if (blip?.Embed?.Value != null)
    {
        var sourceRel = sourcePart.GetReferenceRelationship(blip.Embed.Value);
        // 将图片部件复制到目标文档
        var imagePart = targetPart.AddImagePart(ImagePartType.Png);
        using var stream = sourcePart.GetPartById(blip.Embed.Value).GetStream();
        imagePart.FeedData(stream);
        // 更新 rId 引用
        blip.Embed = targetPart.GetIdOfPart(imagePart);
    }
}
```

**预防：** 在文档间移动内容时始终进行 rId 重新映射 + 媒体文件复制。绝不假设 rId 可以在文档间移植。

---

## 6. "目录显示陈旧/错误条目"或"更新目录无效"

**症状：** 目录显示模板的示例条目（如"第1章 绪论...1"），而不是实际标题。或在 Word 中点击"更新目录"没有反应。

**诊断：**
- **陈旧条目（正常现象）：** 目录条目是缓存在域中的静态文字，不会自动更新，需要用户在 Word 中显式更新。
- **更新目录失败：** SDT 包装或域代码结构损坏。真实模板中的目录是混合结构：SDT 块 + 域代码 + 静态条目。

```bash
# 检查目录 SDT 是否存在
$CLI analyze --input output.docx | grep -i "sdt\|toc"
```

**修复：**
- **如果只是条目陈旧：** 这是预期行为。用户需要在 Word 中右键目录，选择"更新域"。或启用自动更新：
  ```csharp
  // 参见 FieldAndTocSamples.EnableUpdateFieldsOnOpen()
  FieldAndTocSamples.EnableUpdateFieldsOnOpen(settingsPart);
  ```
- **如果 SDT 损坏：** 保持模板的整个 SDT 块完整，不要修改它。
- **如果域代码缺失：** 确保目录包含：`fldChar begin` + `instrText` + `fldChar separate` + 静态条目 + `fldChar end`。参见 `FieldAndTocSamples.CreateMixedTocStructure()` 了解完整模式。
- **如果从头重建了目录（常见错误）：** 很可能破坏了 SDT 包装。改用模板原始的 SDT 块。参见 `Samples/FieldAndTocSamples.cs` 中的 `CreateMixedTocStructure` 方法了解真实目录结构。

**预防：** 执行 Base-Replace（C-2）时，保持模板的目录区完全不变。不要剥离、重建或修改 SDT 块。用户在 Word 中打开时目录会自动更新。

---

## 7. "章节不从新页开始"（缺少分节符）

**症状：** 内容连续流动，章节之间没有分页。第2章紧接在第1章最后一段之后在同一页开始。

**诊断：** 章节之间没有 `sectPr` 元素或分页段落。

**修复：** 在每个章节标题之前插入带 `sectPr` 的段落，或插入分页符：

```csharp
// 选项1：分节符（保留每节的设置，如页眉/页边距）
var breakPara = new Paragraph(
    new ParagraphProperties(
        new SectionProperties(
            new SectionType { Val = SectionMarkValues.NextPage })));

// 选项2：简单分页符（更轻量）
var breakPara = new Paragraph(
    new Run(new Break { Type = BreakValues.Page }));

// 在每个 Heading1 之前插入
body.InsertBefore(breakPara, heading1Paragraph);
```

**预防：** 复制内容时，根据需要在 Heading1 段落之前插入分页符/分节符。复制之前先检查源文档的节结构。

---

## 8. "超链接不起作用"（链接损坏）

**症状：** 点击输出文档中的超链接没有反应，或导航到错误的 URL。

**诊断：** `w:hyperlink r:id` 指向的关系在 `document.xml.rels` 中不存在。

```bash
# 检查超链接关系
$CLI analyze --input output.docx --part rels | grep -i "hyperlink"
```

**修复：** 将源文档的超链接关系合并到输出 rels 文件中，更新 rId 引用。

```csharp
foreach (var hyperlink in body.Descendants<Hyperlink>())
{
    if (hyperlink.Id?.Value != null)
    {
        var sourceRel = sourcePart.HyperlinkRelationships
            .FirstOrDefault(r => r.Id == hyperlink.Id.Value);
        if (sourceRel != null)
        {
            targetPart.AddHyperlinkRelationship(sourceRel.Uri, sourceRel.IsExternal);
            var newRel = targetPart.HyperlinkRelationships.Last();
            hyperlink.Id = newRel.Id;
        }
    }
}
```

**预防：** 合并文档时始终合并**所有**关系类型（图片、超链接、页眉、页脚）。绝不假设源 rId 在目标中有效。

---

## 9. "编号列表显示错误序号"或"项目符号消失"

**症状：** 原本编号为 1、2、3 的列表现在显示 1、1、1，或完全没有编号/项目符号。

**诊断：** `pPr` 中的 `numId` 引用的编号定义在 `numbering.xml` 中不存在，或 `abstractNumId` 映射损坏。

```bash
# 检查编号定义
$CLI analyze --input output.docx --part numbering
```

**修复：** 将源 numId 映射到模板 numId，或合并编号定义：

```csharp
// 1. 将 abstractNum 定义从源文档复制到目标 numbering.xml
// 2. 创建指向复制的 abstractNum 的新 num 条目
// 3. 更新文档内容中的所有 numId 引用

var sourceNumbering = sourceNumberingPart.Numbering;
var targetNumbering = targetNumberingPart.Numbering;

// 获取现有 ID 最大值以避免冲突
int maxAbstractNumId = targetNumbering.Elements<AbstractNum>()
    .Max(a => a.AbstractNumberId?.Value ?? 0) + 1;
int maxNumId = targetNumbering.Elements<NumberingInstance>()
    .Max(n => n.NumberID?.Value ?? 0) + 1;
```

**预防：** 在模板应用流程中包含 `numbering.xml` 协调步骤。参见 `Samples/ListAndNumberingSamples.cs` 了解正确的编号设置。

---

## 10. "页边距/页面尺寸不正确"

**症状：** 输出的页边距、页面尺寸或方向与模板不同。

**诊断：** 源文档的 `sectPr` 覆盖了模板的 `sectPr`。最终的 `sectPr`（`body` 的子元素）控制最后一节的版式。

```bash
# 比较节属性
$CLI analyze --input template.docx | grep -i "sectPr\|margin\|pgSz"
$CLI analyze --input output.docx | grep -i "sectPr\|margin\|pgSz"
```

**修复：** 使用模板的最终 `sectPr`。对于中间的 `sectPr`（多节文档），谨慎合并。

```csharp
// 用模板的 sectPr 替换输出的最终 sectPr
var templateSectPr = templateBody.Elements<SectionProperties>().LastOrDefault();
var outputSectPr = outputBody.Elements<SectionProperties>().LastOrDefault();

if (templateSectPr != null)
{
    var cloned = templateSectPr.CloneNode(true) as SectionProperties;
    if (outputSectPr != null)
        outputBody.ReplaceChild(cloned!, outputSectPr);
    else
        outputBody.Append(cloned!);
}
```

**预防：** 始终以模板的 `sectPr` 为页面版式的权威。复制内容之前去除源文档的 `sectPr`。

---

## 11. "中文显示为方块/豆腐"

**症状：** 中文字符显示为方块（□□□）或缺失字形。

**诊断：** `rFonts w:eastAsia` 设置的字体在系统上不存在，或完全缺失。没有东亚字体声明时，渲染引擎可能回退到没有 CJK 字形的字体。

**修复：** 确保所有 CJK 文字的 `w:eastAsia` 设置为可用字体：

```csharp
foreach (var run in body.Descendants<Run>())
{
    var text = run.InnerText;
    if (ContainsCjk(text))
    {
        var rPr = run.RunProperties ?? new RunProperties();
        var rFonts = rPr.GetFirstChild<RunFonts>();
        if (rFonts == null)
        {
            rFonts = new RunFonts();
            rPr.Append(rFonts);
        }
        // 设置为通用可用的 CJK 字体
        rFonts.EastAsia = "SimSun"; // 宋体——最安全的默认值
        if (run.RunProperties == null) run.PrependChild(rPr);
    }
}

static bool ContainsCjk(string text)
{
    return text.Any(c => c >= 0x4E00 && c <= 0x9FFF);
}
```

常见安全 CJK 字体：宋体 (SimSun)、黑体 (SimHei)、仿宋 (FangSong)、楷体 (KaiTi)。

**预防：** 清理 `rPr` 格式时**始终**保留 `w:eastAsia` 字体声明。另见 `references/cjk_typography.md`。

---

## 12. "模板的封面/声明页丢失"

**症状：** 输出文档直接从正文内容开始——没有封面、没有声明、没有摘要、没有目录。模板的结构性前置部分被丢弃了。

**诊断：** 使用了叠加（C-1）策略，但实际需要基底替换（C-2）。叠加策略将样式应用到源文档，但丢弃了模板的结构内容（封面、声明、摘要、目录）。

```bash
# 检查模板结构
$CLI analyze --input template.docx
# 如果模板有超过50个包含封面/目录/声明的段落，需要 C-2
```

**修复：** 使用基底替换（C-2）策略——以模板为基底，只用用户内容替换示例正文区域：

1. 识别模板的"正文区"（目录和最终 sectPr 之间的所有内容）
2. 删除模板的示例正文内容
3. 将用户内容插入正文区
4. 保留模板的其他所有内容（封面、声明、摘要、目录、sectPr）

```bash
$CLI apply-template --input source.docx --template template.docx --output out.docx --strategy base-replace
```

**预防：** 先分析模板结构。如果模板有结构性内容（封面、目录、声明节），始终使用 C-2（基底替换）。详细决策标准参见 `references/scenario_c_apply_template.md`。

---

## 13. "意外出现修订标记"

**症状：** 输出显示红色/绿色修订标记（插入、删除），但源文档中没有。

**诊断：** 模板启用了修订跟踪，或内容以修订形式插入而非普通文字。

```bash
# 检查修订标记
$CLI analyze --input output.docx | grep -i "revision\|ins\|del\|track"
```

**修复：** 通过展平 `w:ins` 和 `w:del` 元素接受所有修订：

```csharp
// 接受插入：解包 w:ins，保留内容
foreach (var ins in body.Descendants<InsertedRun>().ToList())
{
    var parent = ins.Parent!;
    foreach (var child in ins.ChildElements.ToList())
    {
        parent.InsertBefore(child.CloneNode(true), ins);
    }
    ins.Remove();
}

// 接受删除：完全删除 w:del 及其内容
foreach (var del in body.Descendants<DeletedRun>().ToList())
{
    del.Remove();
}
```

或在设置中禁用跟踪：
```csharp
var settings = settingsPart.Settings;
var trackChanges = settings.GetFirstChild<TrackChanges>();
trackChanges?.Remove();
```

**预防：** 开始前检查模板的 `settings.xml` 中是否有 `trackChanges`。如果有，先在模板中接受所有修订。

---

## 恢复策略——当存在多个问题时

当文档存在多个问题时，按以下优先顺序修复：

```
1. [Content_Types].xml  — 没有它，什么都打不开
2. _rels/.rels          — 包关系
3. word/_rels/document.xml.rels — 部件关系（图片、超链接）
4. word/document.xml    — 元素顺序（fix-order）
5. word/styles.xml      — 样式定义和 styleId 映射
6. word/numbering.xml   — 列表/编号定义
7. 其他所有内容          — 页眉、页脚、批注、设置
```

```bash
# 完整恢复流程
$CLI unpack --input broken.docx --output unpacked/
$CLI validate --input broken.docx --xsd assets/xsd/wml-subset.xsd  # 找到所有错误
$CLI fix-order --input broken.docx                                   # 修复元素顺序
$CLI validate --input broken.docx --business                         # 检查业务规则
scripts/docx_preview.sh broken.docx                                  # 视觉检查
```
