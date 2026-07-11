# 从零新建 xlsx 文件

使用 XML 方式创建生产级 xlsx 文件。绝不使用 openpyxl 写入。绝不硬编码 Python 计算值——每个派生数字必须是实时 Excel 公式。

---

## 适用场景

以下情况使用本文档：
- 用户需要一个尚不存在的全新 Excel 文件
- 需要生成报告、财务模型或数据表格
- 任何"创建/构建/生成/制作"类请求

如果用户提供了已有文件需要修改，改用 `edit.md`。

---

## 不可动摇的规则

动手操作任何文件前，先牢记这四条规则：

1. **公式优先**：每个计算值（`SUM`、增长率、比率、小计等）都必须写为 `<f>SUM(B2:B9)</f>`，而不是硬编码的 `<v>5000</v>`。硬编码数字在源数据变化后会过期。只有原始输入和假设参数才可以是硬编码值。

2. **不使用 openpyxl 写入**：整个文件通过直接编辑 XML 构建。Python 只允许用于读取/分析（`pandas.read_excel()`）和运行辅助脚本（`xlsx_pack.py`、`formula_check.py`）。

3. **样式编码含义**：蓝色字体 = 用户输入/假设。黑色字体 = 公式结果。绿色字体 = 跨表引用。完整配色系统和样式索引表见 `format.md`。

4. **交付前验证**：运行 `formula_check.py` 并修复所有错误后再交付给用户。

---

## 完整创建工作流

### 第一步 — 动手前先规划

在碰任何 XML 前，在纸上定义完整结构：

- **工作表**：名称、顺序、用途（如 Assumptions/Model/Summary）
- **每个工作表的布局**：哪些行是标题、输入、公式、合计
- **字符串清单**：收集 sharedStrings 中需要的所有文字标签
- **样式选择**：每列需要什么数字格式（货币、百分比、整数、年份）
- **跨表链接**：哪些工作表从其他工作表拉取数据

这个规划步骤可以避免中途向 sharedStrings 添加字符串、重新计算所有索引的高代价循环。

---

### 第二步 — 复制最小模板

```bash
cp -r SKILL_DIR/templates/minimal_xlsx/ /tmp/xlsx_work/
```

该模板提供一个完整有效的 7 文件 xlsx 骨架：

```
/tmp/xlsx_work/
├── [Content_Types].xml        ← MIME 类型注册表
├── _rels/
│   └── .rels                  ← 根关系（指向 workbook.xml）
└── xl/
    ├── workbook.xml            ← 工作表列表和计算设置
    ├── styles.xml              ← 13 个预建财务样式槽
    ├── sharedStrings.xml       ← 文字字符串表（初始为空）
    ├── _rels/
    │   └── workbook.xml.rels  ← 将 rId 映射到文件路径
    └── worksheets/
        └── sheet1.xml          ← 一个空工作表
```

复制后重命名工作表并添加内容。不要从头创建文件——始终从模板开始。

---

### 第三步 — 配置工作表结构

#### 单工作表文档

模板已有一个名为"Sheet1"的工作表。只需修改 `xl/workbook.xml` 中的 `name` 属性：

```xml
<sheets>
  <sheet name="Revenue Model" sheetId="1" r:id="rId1"/>
</sheets>
```

单工作表文档无需修改其他文件。

#### 多工作表文档

必须保持四个文件同步。按以下顺序操作：

**重要 — rId 冲突规则**：模板的 `workbook.xml.rels` 中，`rId1`、`rId2`、`rId3` 已被占用：
- `rId1` → `worksheets/sheet1.xml`
- `rId2` → `styles.xml`
- `rId3` → `sharedStrings.xml`

新工作表条目必须从 `rId4` 开始向上递增。

**文件 1/4 — `xl/workbook.xml`**（工作表列表）：

```xml
<sheets>
  <sheet name="Assumptions" sheetId="1" r:id="rId1"/>
  <sheet name="Model"       sheetId="2" r:id="rId4"/>
  <sheet name="Summary"     sheetId="3" r:id="rId5"/>
</sheets>
```

工作表名称中的特殊字符：
- `&` → XML 中用 `&amp;`：`<sheet name="P&amp;L" .../>`
- 最多 31 个字符
- 禁止使用：`/ \ ? * [ ] :`
- 名称含空格时，公式引用需加单引号：`'Q1 Data'!B5`

**文件 2/4 — `xl/_rels/workbook.xml.rels`**（ID → 文件路径映射）：

```xml
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
    Target="styles.xml"/>
  <Relationship Id="rId3"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings"
    Target="sharedStrings.xml"/>
  <Relationship Id="rId4"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId5"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet3.xml"/>
</Relationships>
```

**文件 3/4 — `[Content_Types].xml`**（MIME 类型声明）：

```xml
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/sharedStrings.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>
```

**文件 4/4 — 创建新工作表 XML 文件**

将 `sheet1.xml` 复制为 `sheet2.xml` 和 `sheet3.xml`，然后清空 `<sheetData>` 内容：

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet
  xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetViews>
    <sheetView workbookViewId="0"/>
  </sheetViews>
  <sheetFormatPr defaultRowHeight="15" x14ac:dyDescent="0.25"
    xmlns:x14ac="http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac"/>
  <sheetData>
    <!-- 数据行写在此处 -->
  </sheetData>
  <pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>
</worksheet>
```

**同步检查清单** — 每次添加工作表时，验证以下四项一致：

| 检查项 | 验证内容 |
|-------|---------------|
| `workbook.xml` | 存在新的 `<sheet name="..." sheetId="N" r:id="rIdX"/>` |
| `workbook.xml.rels` | 存在新的 `<Relationship Id="rIdX" ... Target="worksheets/sheetN.xml"/>` |
| `[Content_Types].xml` | 存在新的 `<Override PartName="/xl/worksheets/sheetN.xml" .../>` |
| 文件系统 | `xl/worksheets/sheetN.xml` 文件实际存在 |

---

### 第四步 — 填充 sharedStrings

所有文字值（列标题、行标签、分类名称、用户可见的任何字符串）必须存储在 `xl/sharedStrings.xml` 中。单元格通过 0 起始索引引用它们。

**推荐工作流**：先收集所有需要的文字，一次性写完完整表格，然后在编写工作表 XML 时填入索引。这样可以避免中途重新计数索引。

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
     count="10" uniqueCount="10">
  <si><t>Item</t></si>                  <!-- 索引 0 -->
  <si><t>FY2023A</t></si>               <!-- 索引 1 -->
  <si><t>FY2024E</t></si>               <!-- 索引 2 -->
  <si><t>FY2025E</t></si>               <!-- 索引 3 -->
  <si><t>YoY Growth</t></si>            <!-- 索引 4 -->
  <si><t>Revenue</t></si>               <!-- 索引 5 -->
  <si><t>Cost of Goods Sold</t></si>    <!-- 索引 6 -->
  <si><t>Gross Profit</t></si>          <!-- 索引 7 -->
  <si><t>EBITDA</t></si>                <!-- 索引 8 -->
  <si><t>Net Income</t></si>            <!-- 索引 9 -->
</sst>
```

**属性规则**：
- `uniqueCount` = `<si>` 元素数量（表中唯一字符串数）
- `count` = 整个工作簿中所有工作表对字符串引用的总次数（若"Revenue"在 3 个工作表中出现，count = uniqueCount + 2）
- 对于每个字符串只出现一次的新文件：`count == uniqueCount`
- 两个属性必须准确——错误值在某些 Excel 版本中会触发警告

**特殊字符转义**：

```xml
<si><t>R&amp;D Expenses</t></si>          <!-- & 必须写为 &amp; -->
<si><t>Revenue &lt; Target</t></si>        <!-- < 必须写为 &lt; -->
<si><t xml:space="preserve">  (备注)  </t></si>  <!-- 保留首尾空格 -->
```

**辅助脚本**：使用 `shared_strings_builder.py` 从字符串列表生成完整的 `sharedStrings.xml`：

```bash
python3 SKILL_DIR/scripts/shared_strings_builder.py \
  "Item" "FY2024" "FY2025" "Revenue" "Gross Profit" \
  > /tmp/xlsx_work/xl/sharedStrings.xml
```

或从每行一个字符串的文件读取：

```bash
python3 SKILL_DIR/scripts/shared_strings_builder.py --file strings.txt \
  > /tmp/xlsx_work/xl/sharedStrings.xml
```

---

### 第五步 — 写入工作表数据

编辑每个 `xl/worksheets/sheetN.xml`，用行和单元格替换空的 `<sheetData>`。

#### 单元格 XML 结构

```
<c r="B5" t="s" s="4">
      ↑     ↑    ↑
   地址   类型  样式索引（来自 styles.xml 中的 cellXfs）

  <v>3</v>
     ↑
  值（对于 t="s"：sharedStrings 索引；对于数字：数字本身）
```

#### 数据类型参考

| 数据 | `t` 属性 | XML 示例 | 说明 |
|------|---------|-------------|-------|
| 共享字符串（文字） | `s` | `<c r="A1" t="s" s="4"><v>0</v></c>` | `<v>` = sharedStrings 索引 |
| 数字 | 省略 | `<c r="B2" s="5"><v>1000000</v></c>` | 默认类型，省略 `t` |
| 百分比（存为小数） | 省略 | `<c r="C2" s="7"><v>0.125</v></c>` | 12.5% 存为 0.125 |
| 布尔值 | `b` | `<c r="D1" t="b"><v>1</v></c>` | 1=TRUE，0=FALSE |
| 公式 | 省略 | `<c r="B4" s="2"><f>SUM(B2:B3)</f><v></v></c>` | `<v>` 留空 |
| 跨表公式 | 省略 | `<c r="C1" s="3"><f>Assumptions!B2</f><v></v></c>` | 使用 s=3（绿色） |

#### 完整工作表数据示例

```xml
<cols>
  <col min="1" max="1" width="26" customWidth="1"/>   <!-- A：标签列 -->
  <col min="2" max="5" width="14" customWidth="1"/>   <!-- B-E：数据列 -->
</cols>
<sheetData>

  <!-- 第 1 行：表头（样式 4 = 粗体表头） -->
  <row r="1" ht="18" customHeight="1">
    <c r="A1" t="s" s="4"><v>0</v></c>   <!-- "Item" -->
    <c r="B1" t="s" s="4"><v>1</v></c>   <!-- "FY2023A" -->
    <c r="C1" t="s" s="4"><v>2</v></c>   <!-- "FY2024E" -->
    <c r="D1" t="s" s="4"><v>3</v></c>   <!-- "FY2025E" -->
    <c r="E1" t="s" s="4"><v>4</v></c>   <!-- "YoY Growth" -->
  </row>

  <!-- 第 2 行：收入——实际值（输入）+ 公式（计算） -->
  <row r="2">
    <c r="A2" t="s" s="1"><v>5</v></c>    <!-- "Revenue"，蓝色输入标签 -->
    <c r="B2" s="5"><v>85000000</v></c>   <!-- FY2023A 实际值：$85M，货币输入 -->
    <c r="C2" s="6"><f>B2*(1+Assumptions!C3)</f><v></v></c>   <!-- 公式，货币 -->
    <c r="D2" s="6"><f>C2*(1+Assumptions!D3)</f><v></v></c>
    <c r="E2" s="8"><f>D2/C2-1</f><v></v></c>   <!-- 同比增长，百分比公式 -->
  </row>

  <!-- 第 3 行：毛利润 -->
  <row r="3">
    <c r="A3" t="s" s="2"><v>7</v></c>    <!-- "Gross Profit"，黑色公式标签 -->
    <c r="B3" s="6"><f>B2*Assumptions!B4</f><v></v></c>
    <c r="C3" s="6"><f>C2*Assumptions!C4</f><v></v></c>
    <c r="D3" s="6"><f>D2*Assumptions!D4</f><v></v></c>
    <c r="E3" s="8"><f>D3/C3-1</f><v></v></c>
  </row>

  <!-- 第 5 行：SUM 合计行 -->
  <row r="5">
    <c r="A5" t="s" s="4"><v>8</v></c>    <!-- "EBITDA" -->
    <c r="B5" s="6"><f>SUM(B2:B4)</f><v></v></c>
    <c r="C5" s="6"><f>SUM(C2:C4)</f><v></v></c>
    <c r="D5" s="6"><f>SUM(D2:D4)</f><v></v></c>
    <c r="E5" s="8"><f>D5/C5-1</f><v></v></c>
  </row>

</sheetData>
```

#### 列宽和冻结窗格

列宽放在 `<sheetData>` **之前**，冻结窗格放在 `<sheetView>` 内：

```xml
<!-- 在 <sheetViews><sheetView ...> 内——冻结首行 -->
<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>

<!-- 在 <sheetData> 之前——设置列宽 -->
<cols>
  <col min="1" max="1" width="28" customWidth="1"/>
  <col min="2" max="8" width="14" customWidth="1"/>
</cols>
```

---

### 第六步 — 应用样式

模板的 `xl/styles.xml` 有 13 个预建语义样式槽（索引 0–12）。**完整样式索引表、配色系统和如何添加新样式，请阅读 `format.md`。**

最常用槽的快速参考：

| `s` | 角色 | 示例 |
|-----|------|---------|
| 4 | 表头（粗体） | 列/行标题 |
| 5 / 6 | 货币输入（蓝）/ 公式（黑） | `$#,##0` |
| 7 / 8 | 百分比输入 / 公式 | `0.0%` |
| 11 | 年份（无千分位） | 2024 而非 2,024 |

设计原则：蓝色 = 人工设置。黑色 = Excel 计算。绿色 = 跨表引用。

如需 13 个预建槽以外的样式，请按 `format.md` 第 3.2 节的追加方式操作。

---

### 第七步 — 公式手册

#### XML 公式语法提醒

XML 中的公式**不带前导 `=`**：

```xml
<!-- Excel 界面：=SUM(B2:B9)   →   XML 中： -->
<c r="B10" s="6"><f>SUM(B2:B9)</f><v></v></c>
```

#### 基本聚合

```xml
<c r="B10" s="6"><f>SUM(B2:B9)</f><v></v></c>
<c r="B11" s="6"><f>AVERAGE(B2:B9)</f><v></v></c>
<c r="B12" s="10"><f>COUNT(B2:B9)</f><v></v></c>
<c r="B13" s="10"><f>COUNTA(A2:A100)</f><v></v></c>
<c r="B14" s="6"><f>MAX(B2:B9)</f><v></v></c>
<c r="B15" s="6"><f>MIN(B2:B9)</f><v></v></c>
```

#### 财务计算

```xml
<!-- 同比增长率：当期 / 上期 - 1 -->
<c r="E5" s="8"><f>D5/C5-1</f><v></v></c>

<!-- 毛利润：收入 × 毛利率 -->
<c r="B6" s="6"><f>B4*B3</f><v></v></c>

<!-- EBITDA 利润率：EBITDA / 收入 -->
<c r="B9" s="8"><f>B8/B4</f><v></v></c>

<!-- 当分母可能为零时，屏蔽 #DIV/0! -->
<c r="E5" s="8"><f>IF(C5=0,0,D5/C5-1)</f><v></v></c>

<!-- NPV 和 IRR（现金流在 B2:B7，折现率在 B1） -->
<c r="C1" s="6"><f>NPV(B1,B3:B7)+B2</f><v></v></c>
<c r="C2" s="8"><f>IRR(B2:B7)</f><v></v></c>
```

#### 跨表引用

```xml
<!-- 名称无空格：无需引号 -->
<c r="B3" s="3"><f>Assumptions!B5</f><v></v></c>

<!-- 名称有空格：需要单引号 -->
<c r="B3" s="3"><f>'Q1 Data'!B5</f><v></v></c>

<!-- 名称有 & 符号（workbook.xml 中 XML 转义，但公式中用字面量 &） -->
<c r="B3" s="3"><f>'R&amp;D'!B5</f><v></v></c>

<!-- 跨表范围：对另一张表中的范围求和 -->
<c r="B10" s="6"><f>SUM(Data!C2:C1000)</f><v></v></c>

<!-- 3D 引用：对多张表中相同单元格求和 -->
<c r="B5" s="6"><f>SUM(Jan:Dec!B5)</f><v></v></c>
```

跨表公式单元格应使用 `s="3"`（绿色）以标明数据来源。

#### 共享公式（同一列中重复相同公式模式）

当许多连续单元格共享相同的公式结构（仅行号不同）时，使用共享公式保持 XML 紧凑：

```xml
<!-- D2：定义共享组（si="0"，ref="D2:D11"） -->
<c r="D2" s="8"><f t="shared" ref="D2:D11" si="0">C2/B2-1</f><v></v></c>

<!-- D3 到 D11：引用同一组，无需公式文本 -->
<c r="D3" s="8"><f t="shared" si="0"/><v></v></c>
<c r="D4" s="8"><f t="shared" si="0"/><v></v></c>
<!-- ...以此类推... -->
```

Excel 自动调整相对引用（D3 计算 `C3/B3-1` 等）。有多个共享公式组时，依次分配 `si` 值（0、1、2……）。

#### 绝对引用

```xml
<!-- $B$2 在公式复制时锁定到该单元格 -->
<c r="C5" s="8"><f>B5/$B$2</f><v></v></c>
```

`$` 字符无需 XML 转义，直接写字面量即可。

#### 查找公式

```xml
<!-- VLOOKUP：精确匹配（最后一个参数为 0） -->
<c r="C5" s="6"><f>VLOOKUP(A5,Assumptions!A:C,2,0)</f><v></v></c>

<!-- INDEX/MATCH：更灵活 -->
<c r="C5" s="6"><f>INDEX(B:B,MATCH(A5,A:A,0))</f><v></v></c>

<!-- XLOOKUP（Excel 2019+） -->
<c r="C5" s="6"><f>XLOOKUP(A5,A:A,B:B)</f><v></v></c>
```

---

### 第八步 — 打包与验证

**打包**：

```bash
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ /path/to/output.xlsx
```

`xlsx_pack.py` 会：
1. 检查根目录是否存在 `[Content_Types].xml`
2. 解析每个 `.xml` 和 `.rels` 文件的格式正确性——如有失败则中止
3. 以正确压缩方式创建 ZIP 压缩包

**验证**：

```bash
python3 SKILL_DIR/scripts/formula_check.py /path/to/output.xlsx
```

`formula_check.py` 会：
1. 扫描每个单元格中的 `<c t="e">` 条目（缓存的错误值）——覆盖全部 7 种错误类型
2. 从每个 `<f>` 公式中提取工作表名称引用
3. 验证每个被引用的工作表是否存在于 `workbook.xml` 中

修复每个报告的错误后再交付。退出代码 0 = 可以安全交付。

---

## 交付前检查清单

交付给用户前逐项检查：

- [ ] `formula_check.py` 报告 0 个错误
- [ ] 每个计算单元格都有 `<f>` — 而不只是带数字的 `<v>`
- [ ] `sharedStrings.xml` 的 `count` 和 `uniqueCount` 与实际 `<si>` 数量匹配
- [ ] 每个单元格的 `s` 属性值在 `0` 到 `cellXfs count - 1` 范围内
- [ ] `workbook.xml` 中的每个工作表在 `workbook.xml.rels` 中都有对应条目
- [ ] 每个 `worksheets/sheetN.xml` 文件在 `[Content_Types].xml` 中都有对应的 `<Override>`
- [ ] 年份列使用 `s="11"`（格式 `0`，无千分位分隔符）
- [ ] 跨表引用公式使用 `s="3"`（绿色字体）
- [ ] 假设输入使用 `s="1"` 或 `s="5"` 或 `s="7"`（蓝色字体）

---

## 常见错误与修复

| 错误 | 症状 | 修复方法 |
|---------|---------|-----|
| 公式有前导 `=` | 单元格显示 `=SUM(...)` 文本 | 从 `<f>` 内容中删除 `=` |
| sharedStrings `count` 未更新 | Excel 警告或空白单元格 | 计数 `<si>` 元素，同时更新 `count` 和 `uniqueCount` |
| 样式索引越界 | 文件损坏 / Excel 修复 | 确保 `s` < `cellXfs count`；如需新样式则追加 `<xf>` |
| 新工作表 rId 与 styles/sharedStrings 的 rId 冲突 | 工作表丢失或样式丢失 | 新工作表使用 rId4、rId5……（rId1-3 为模板保留） |
| 工作表名称中的 `&` 在 XML 中未转义 | XML 解析错误 | 在 `workbook.xml` 的 name 属性中使用 `&amp;` |
| 跨表引用含空格的工作表名称时未加引号 | `#REF!` 错误 | 将工作表名称用单引号括起来：`'Sheet Name'!B5` |
| 跨表引用不存在的工作表 | `#REF!` 错误 | 核对 `workbook.xml` 中的工作表列表与公式 |
| 数字以文字形式存储（`t="s"`） | 左对齐，无法求和 | 从数字单元格移除 `t` 属性 |
| 年份显示为 `2,024` | 可读性问题 | 使用 `s="11"`（numFmtId=1，格式 `0`） |
| 硬编码 Python 结果而非公式 | "死表格"——不会更新 | 用 `<f>公式</f><v></v>` 替换 `<v>N</v>` |

---

## 列字母参考

| 列号 | 字母 | 列号 | 字母 | 列号 | 字母 |
|-------|--------|-------|--------|-------|--------|
| 1 | A | 26 | Z | 27 | AA |
| 28 | AB | 52 | AZ | 53 | BA |
| 54 | BB | 78 | BZ | 79 | CA |

Python 转换（编程构建公式时使用）：

```python
def col_letter(n: int) -> str:
    """将 1 起始的列号转换为 Excel 字母（A、B、...、Z、AA、AB……）"""
    result = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result

def col_number(s: str) -> int:
    """将 Excel 列字母转换为 1 起始的数字"""
    n = 0
    for c in s.upper():
        n = n * 26 + (ord(c) - 64)
    return n
```

---

## 典型场景演练

### 场景 A — 三年财务模型（单工作表）

布局：第 1-12 行 = 假设区（蓝色输入）/ 第 14-30 行 = 模型区（黑色公式）。

```xml
<!-- sharedStrings.xml（节选） -->
<sst count="8" uniqueCount="8">
  <si><t>Metric</t></si>           <!-- 0 -->
  <si><t>FY2023A</t></si>          <!-- 1 -->
  <si><t>FY2024E</t></si>          <!-- 2 -->
  <si><t>FY2025E</t></si>          <!-- 3 -->
  <si><t>Revenue Growth</t></si>   <!-- 4 -->
  <si><t>Gross Margin</t></si>     <!-- 5 -->
  <si><t>Revenue</t></si>          <!-- 6 -->
  <si><t>Gross Profit</t></si>     <!-- 7 -->
</sst>

<!-- sheet1.xml（节选） -->
<sheetData>
  <!-- 表头 -->
  <row r="1">
    <c r="A1" t="s" s="4"><v>0</v></c>
    <c r="B1" t="s" s="4"><v>1</v></c>
    <c r="C1" t="s" s="4"><v>2</v></c>
    <c r="D1" t="s" s="4"><v>3</v></c>
  </row>
  <!-- 假设区（第 2-3 行） -->
  <row r="2">
    <c r="A2" t="s" s="1"><v>4</v></c>    <!-- "Revenue Growth"，蓝色 -->
    <c r="B2" s="7"><v>0</v></c>          <!-- FY2023A：n/a，0% 占位 -->
    <c r="C2" s="7"><v>0.12</v></c>       <!-- FY2024E：12.0% 输入 -->
    <c r="D2" s="7"><v>0.15</v></c>       <!-- FY2025E：15.0% 输入 -->
  </row>
  <row r="3">
    <c r="A3" t="s" s="1"><v>5</v></c>    <!-- "Gross Margin"，蓝色 -->
    <c r="B3" s="7"><v>0.45</v></c>
    <c r="C3" s="7"><v>0.46</v></c>
    <c r="D3" s="7"><v>0.47</v></c>
  </row>
  <!-- 模型区（第 14-15 行） -->
  <row r="14">
    <c r="A14" t="s" s="2"><v>6</v></c>      <!-- "Revenue"，黑色 -->
    <c r="B14" s="5"><v>85000000</v></c>     <!-- 实际值，货币输入 -->
    <c r="C14" s="6"><f>B14*(1+C2)</f><v></v></c>
    <c r="D14" s="6"><f>C14*(1+D2)</f><v></v></c>
  </row>
  <row r="15">
    <c r="A15" t="s" s="2"><v>7</v></c>      <!-- "Gross Profit"，黑色 -->
    <c r="B15" s="6"><f>B14*B3</f><v></v></c>
    <c r="C15" s="6"><f>C14*C3</f><v></v></c>
    <c r="D15" s="6"><f>D14*D3</f><v></v></c>
  </row>
</sheetData>
```

### 场景 B — 数据+汇总（两张工作表）

`Summary` 工作表使用跨表公式（绿色，`s="3"`）从 `Data` 拉取数据：

```xml
<!-- Summary/sheet2.xml sheetData 节选 -->
<sheetData>
  <row r="1">
    <c r="A1" t="s" s="4"><v>0</v></c>   <!-- "Metric" -->
    <c r="B1" t="s" s="4"><v>1</v></c>   <!-- "Value" -->
  </row>
  <row r="2">
    <c r="A2" t="s" s="0"><v>2</v></c>   <!-- "Total Revenue" -->
    <c r="B2" s="3"><f>SUM(Data!C2:C10000)</f><v></v></c>
  </row>
  <row r="3">
    <c r="A3" t="s" s="0"><v>3</v></c>   <!-- "Deal Count" -->
    <c r="B3" s="3"><f>COUNTA(Data!A2:A10000)</f><v></v></c>
  </row>
  <row r="4">
    <c r="A4" t="s" s="0"><v>4</v></c>   <!-- "Avg Deal Size" -->
    <c r="B4" s="3"><f>IF(B3=0,0,B2/B3)</f><v></v></c>
  </row>
</sheetData>
```

---

## 绝对禁止

- 不得使用 openpyxl 或任何 Python 库写入最终 xlsx 文件
- 不得硬编码任何计算值——每个派生数字都使用 `<f>` 公式
- 不得未运行 `formula_check.py` 就交付
- 不得将单元格的 `s` 属性设置为 >= `cellXfs count` 的值
- 不得修改 `styles.xml` 中已有的 `<xf>` 条目——只能追加新条目
- 不得在未更新全部四个同步点的情况下添加新工作表（workbook.xml、workbook.xml.rels、[Content_Types].xml、实际 .xml 文件）
- 不得为新工作表分配与 rId1、rId2、rId3 重叠的 rId（模板中这三个 ID 已被 sheet1、styles、sharedStrings 保留）
