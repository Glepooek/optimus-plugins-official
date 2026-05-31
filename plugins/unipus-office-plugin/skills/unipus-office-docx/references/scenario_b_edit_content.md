# 场景 B：编辑/填写已有 DOCX 内容

## 核心原则

**"首先，不造成伤害。"** 编辑已有文档时，最小化更改范围。只修改需要更改的内容。保留所有与本次编辑无直接关系的格式、样式、关系和结构。

---

## 使用时机

- 替换占位文字（`{{name}}`、`$DATE$`、`[PLACEHOLDER]`）
- 更新特定段落或表格单元格
- 填写表单字段
- 在已知位置添加或删除段落
- 插入修订标记用于审核工作流

**不要在以下情况使用：** 用户需要更改整个文档的外观/样式（→ 场景 C），或从零创建文档（→ 场景 A）。

---

## 工作流

```
1. 预览   → CLI：analyze <input.docx>
2. 分析   → 理解结构：节、样式、标题、表格
3. 定位   → 找到确切的编辑目标（段落索引、表格索引、占位符文字）
4. 编辑   → 通过 CLI 或直接 XML 进行精确修改
5. 验证   → CLI：validate <output.docx>
6. 对比   → 比较前后变化，确认只有预期内容被修改
```

---

## 何时使用 API vs 直接 XML

### 使用 CLI 编辑命令的情况：
- 替换占位文字（如 `{{fieldName}}` → 实际值）
- 从 JSON 填充表格数据
- 更新文档属性（标题、作者）
- 简单的文字插入或删除

### 使用直接 XML 操作的情况：
- 文字跨越多个格式不同的 run（run 边界问题）
- 添加复杂结构（嵌套表格、多图片布局）
- 操作修订跟踪标记
- 修改页眉/页脚内容
- 调整节属性

---

## 占位符模式

CLI 原生支持 `{{fieldName}}` 占位符：

```bash
# 从 JSON 映射中替换所有 {{占位符}}
dotnet run ... edit input.docx --fill-placeholders data.json --output filled.docx
```

其中 `data.json`：
```json
{
  "companyName": "某某公司",
  "date": "2026年3月21日",
  "amount": "¥15,000.00",
  "recipientName": "张三"
}
```

其他占位符格式（`$FIELD$`、`[PLACEHOLDER]`）需要文字替换：
```bash
dotnet run ... edit input.docx --replace "$DATE$" "2026年3月21日" --output updated.docx
```

---

## 文字替换策略

### 简单替换

当完整搜索文字在单个 `w:r`（run）内时：

```xml
<!-- 替换前 -->
<w:r>
  <w:rPr><w:b /></w:rPr>
  <w:t>{{companyName}}</w:t>
</w:r>

<!-- 替换后——格式保留 -->
<w:r>
  <w:rPr><w:b /></w:rPr>
  <w:t>某某公司</w:t>
</w:r>
```

直接替换。run 的 `w:rPr` 保持不变。

### 复杂替换（分散 run）

当搜索文字被分散到多个 run 中时（Word 在文字中途应用拼写检查或格式时常见）：

```xml
<!-- "{{companyName}}" 被分成 3 个 run -->
<w:r><w:rPr><w:b /></w:rPr><w:t>{{company</w:t></w:r>
<w:r><w:rPr><w:b /><w:i /></w:rPr><w:t>Na</w:t></w:r>
<w:r><w:rPr><w:b /></w:rPr><w:t>me}}</w:t></w:r>
```

策略：
1. 跨 run 拼接文字以找到匹配项
2. 将替换文字放入**第一个** run（保留其 `w:rPr`）
3. 从后续 run 中删除文字（若为空则完全删除该 run）

```xml
<!-- 替换后 -->
<w:r><w:rPr><w:b /></w:rPr><w:t>某某公司</w:t></w:r>
```

**规则**：始终保留匹配中第一个 run 的格式。

---

## 表格编辑

### 按索引

表格按文档顺序从 0 开始编号：

```bash
dotnet run ... edit input.docx --table-index 0 --table-data data.json --output updated.docx
```

### 按表头匹配

通过表头行内容查找表格：

```bash
dotnet run ... edit input.docx --table-match "姓名,金额,日期" --table-data data.json
```

### 表格数据 JSON 格式

```json
{
  "rows": [
    ["张三", "¥5,000", "2026-03-15"],
    ["李四", "¥3,200", "2026-03-18"]
  ],
  "appendRows": true
}
```

- `appendRows: true` — 在现有数据后追加行
- `appendRows: false`（默认）— 替换所有数据行（保留表头行）

### 直接 XML 表格编辑

通过行/列索引定位特定单元格：

```xml
<!-- 第 2 行（0 开始），第 1 列 -->
<w:tr>  <!-- tr[2] -->
  <w:tc>...</w:tc>
  <w:tc>  <!-- tc[1]——目标单元格 -->
    <w:p>
      <w:r><w:t>旧值</w:t></w:r>
    </w:p>
  </w:tc>
</w:tr>
```

只替换 `w:t` 内容。**不要**修改 `w:tcPr`（单元格属性）或 `w:tblPr`（表格属性）。

---

## 修订跟踪指南

### 何时添加修订标记
- 用户明确要求修订跟踪
- 文档已启用跟踪（settings 中有 `w:trackChanges`）
- 协作审核工作流

### 何时不添加修订标记
- 填写表单/替换占位符（这是"完成"文档，而非"修订"）
- 用户想要干净结果的直接编辑
- 批量数据填充操作

### 添加修订跟踪

完整 XML 示例参见 `references/track_changes_guide.md`。

快速参考——带跟踪的文字插入：
```xml
<w:ins w:id="1" w:author="UAI" w:date="2026-03-21T10:00:00Z">
  <w:r>
    <w:t>新增文字</w:t>
  </w:r>
</w:ins>
```

带跟踪的文字删除：
```xml
<w:del w:id="2" w:author="UAI" w:date="2026-03-21T10:00:00Z">
  <w:r>
    <w:delText>被删除的文字</w:delText>  <!-- 必须用 delText，不能用 t -->
  </w:r>
</w:del>
```

---

## 常见陷阱

### 1. 破坏 run 边界

**问题**：通过简单修改单个 run 来替换跨越多个 run 的文字，会破坏行内格式。

**修复**：拼接 run 文字，找到匹配边界，合并到第一个 run，删除被消费的 run。

### 2. 超链接内容

**问题**：替换 `w:hyperlink` 元素内的文字时，若不保留超链接包装，链接会消失。

```xml
<w:hyperlink r:id="rId5">
  <w:r>
    <w:rPr><w:rStyle w:val="Hyperlink" /></w:rPr>
    <w:t>点击这里</w:t>  <!-- 只替换这段文字 -->
  </w:r>
</w:hyperlink>
```

**修复**：只修改超链接 run 内的 `w:t`，绝不删除或替换 `w:hyperlink` 元素本身。

### 3. 修订上下文

**问题**：替换 `w:ins` 或 `w:del` 元素内的文字时，若不理解修订上下文，会产生无效标记。

**修复**：如果目标文字在修订标记内，可以：
- 在修订上下文内替换（保留 `w:ins`/`w:del` 包装）
- 或删除旧修订并创建新修订

### 4. 样式保留

**问题**：添加新段落时不指定样式，导致段落继承 `Normal`，可能与周围上下文不匹配。

**修复**：插入段落时，从同类型的相邻段落复制 `w:pStyle`。

### 5. 编号连续性

**问题**：插入新列表项破坏编号序列。

**修复**：确保新段落与相邻列表项具有相同的 `w:numId` 和 `w:ilvl`。如果延续序列，设置 `w:numPr` 与之匹配。

### 6. XML 特殊字符

**问题**：用户内容包含 `&`、`<`、`>`、`"`、`'`——这些必须在 XML 中转义。

**修复**：将用户提供的文字插入 `w:t` 元素之前始终进行 XML 转义：
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&apos;`

### 7. 空白保留

**问题**：`w:t` 中开头/结尾的空格会被 XML 解析器剥除。

**修复**：添加 `xml:space="preserve"` 属性：
```xml
<w:t xml:space="preserve"> 开头有空格的文字</w:t>
```

---

## 对比验证

编辑后，始终比较前后状态：

```bash
# 结构对比——只显示变更的元素
dotnet run ... diff original.docx modified.docx

# 纯文字对比——显示内容变更
dotnet run ... diff original.docx modified.docx --text-only
```

验证：
- 只有预期的文字发生了改变
- 没有样式被修改
- 没有意外添加或删除关系
- 表格结构完整（除非有意更改，否则行列数相同）
- 图片和其他媒体未变更
