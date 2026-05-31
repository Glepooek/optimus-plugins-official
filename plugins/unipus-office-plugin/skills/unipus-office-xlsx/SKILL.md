---
name: unipus:office:xlsx
description: "打开、创建、读取、分析、编辑或验证 Excel/电子表格文件（.xlsx、.xlsm、.csv、.tsv）。当用户要求创建、构建、修改、分析、读取、验证或格式化任何 Excel 电子表格、财务模型、数据透视表或表格数据文件时使用。涵盖：从零创建新 xlsx、读取分析已有文件、零格式损失编辑已有 xlsx、公式计算与验证，以及应用专业财务格式标准。触发词：电子表格、Excel、.xlsx、.csv、数据透视表、财务模型、公式，或任何要求以 Excel 格式输出表格数据的请求。"
license: MIT
metadata:
  version: "1.0"
  category: productivity
  sources:
    - ECMA-376 Office Open XML File Formats
    - Microsoft Open XML SDK documentation
---

# unipus XLSX Skill

直接处理请求，不要派发子智能体。始终输出用户要求的文件。

## 任务路由

| 任务 | 方法 | 指南 |
|------|--------|-------|
| **READ（读取）** — 分析已有数据 | `xlsx_reader.py` + pandas | `references/read-analyze.md` |
| **CREATE（创建）** — 从零新建 xlsx | XML 模板 | `references/create.md` + `references/format.md` |
| **EDIT（编辑）** — 修改已有 xlsx | XML 解包→编辑→重打包 | `references/edit.md`（如需样式修改加 `format.md`） |
| **FIX（修复）** — 修复已有 xlsx 中的损坏公式 | XML 解包→修复 `<f>` 节点→重打包 | `references/fix.md` |
| **VALIDATE（验证）** — 检查公式 | `formula_check.py` | `references/validate.md` |

## READ — 分析数据（先阅读 `references/read-analyze.md`）

先用 `xlsx_reader.py` 发现结构，再用 pandas 进行自定义分析。不得修改源文件。

**格式规则**：当用户指定小数位数（如"保留 2 位小数"）时，对所有数字值应用该格式——每个数字都使用 `f'{v:.2f}'`。当需要 `12875.00` 时，绝不输出 `12875`。

**聚合规则**：始终直接从 DataFrame 列计算总和/均值/计数——例如 `df['Revenue'].sum()`。聚合前绝不重新推导列值。

## CREATE — XML 模板（先阅读 `references/create.md` + `references/format.md`）

复制 `templates/minimal_xlsx/` → 直接编辑 XML → 用 `xlsx_pack.py` 重打包。每个推导值必须是 Excel 公式（`<f>SUM(B2:B9)</f>`），绝不硬编码数字。按 `format.md` 应用字体颜色。

## EDIT — XML 直接编辑（先阅读 `references/edit.md`）

**关键——编辑完整性规则：**
1. **绝不为编辑任务创建新 `Workbook()`**。始终加载原始文件。
2. 输出文件必须包含与输入**相同的工作表**（相同名称、相同数据）。
3. 仅修改任务要求的特定单元格——其他内容必须保持不变。
4. **保存 output.xlsx 后，验证文件**：用 `xlsx_reader.py` 或 `pandas` 打开，确认原始工作表名称和部分原始数据存在。若验证失败，说明写入了错误文件——交付前修复。

不要对已有文件使用 openpyxl 往返读写（会损坏 VBA、数据透视表、迷你图）。改用：解包 → 辅助脚本 → 重打包。

**"填写单元格"/"向已有单元格添加公式" = EDIT 任务。** 如果输入文件已存在，且要求填写、更新或向特定单元格添加公式，必须使用 XML 编辑路径。绝不创建新 `Workbook()`。示例——在 B3 填写跨表 SUM 公式：
```bash
python3 SKILL_DIR/scripts/xlsx_unpack.py input.xlsx /tmp/xlsx_work/
# 通过 xl/workbook.xml → xl/_rels/workbook.xml.rels 找到目标工作表 XML
# 然后用 Edit 工具在目标 <c> 元素内添加 <f>：
#   <c r="B3"><f>SUM('Sales Data'!D2:D13)</f><v></v></c>
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx
```

**添加列**（公式、数字格式、样式自动从相邻列复制）：
```bash
python3 SKILL_DIR/scripts/xlsx_unpack.py input.xlsx /tmp/xlsx_work/
python3 SKILL_DIR/scripts/xlsx_add_column.py /tmp/xlsx_work/ --col G \
    --sheet "Sheet1" --header "占总量%" \
    --formula '=F{row}/$F$10' --formula-rows 2:9 \
    --total-row 10 --total-formula '=SUM(G2:G9)' --numfmt '0.0%' \
    --border-row 10 --border-style medium
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx
```
`--border-row` 标志对该行所有单元格应用顶部边框（不只是新列）。当任务要求在合计行添加会计风格边框时使用。

**插入行**（移动已有行、更新 SUM 公式、修复循环引用）：
```bash
python3 SKILL_DIR/scripts/xlsx_unpack.py input.xlsx /tmp/xlsx_work/
# 重要：通过在工作表 XML 中搜索标签文字来查找正确的 --at 行号，
# 不要使用提示中的行号。提示可能说"第 5 行（办公室租金）"，
# 但实际上办公室租金可能在第 4 行。始终先按文字标签定位行。
python3 SKILL_DIR/scripts/xlsx_insert_row.py /tmp/xlsx_work/ --at 5 \
    --sheet "Budget FY2025" --text A=水电费 \
    --values B=3000 C=3000 D=3500 E=3500 \
    --formula 'F=SUM(B{row}:E{row})' --copy-style-from 4
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx
```
**行查找规则**：当任务说"在第 N 行（标签）之后"，始终通过在工作表 XML 中搜索"标签"来找到该行（`grep -n "标签" /tmp/xlsx_work/xl/worksheets/sheet*.xml` 或检查 sharedStrings.xml）。将实际行号 + 1 用于 `--at`。不要单独调用 `xlsx_shift_rows.py`——`xlsx_insert_row.py` 内部已调用它。

**应用整行边框**（例如合计行的会计线）：
运行辅助脚本后，对目标行所有单元格应用边框，而不只是新添加的单元格。在 `xl/styles.xml` 中追加新的 `<border>`（所需样式），然后在 `<cellXfs>` 中追加新的 `<xf>`（克隆每个单元格现有 `<xf>` 但设置新 borderId）。通过 `s` 属性将新样式索引应用到该行每个 `<c>`：
```xml
<!-- 在 xl/styles.xml 的 <borders> 末尾追加： -->
<border>
  <left/><right/><top style="medium"/><bottom/><diagonal/>
</border>
<!-- 然后在 <cellXfs> 中为每种现有样式追加带新 borderId 的 xf 克隆 -->
```
**关键规则**：当任务说"在第 N 行添加边框"时，遍历从 A 到最后一列的所有单元格，而不只是新添加的单元格。

**手动 XML 编辑**（辅助脚本未覆盖的情况）：
```bash
python3 SKILL_DIR/scripts/xlsx_unpack.py input.xlsx /tmp/xlsx_work/
# ... 用 Edit 工具编辑 XML ...
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx
```

## FIX — 修复损坏公式（先阅读 `references/fix.md`）

这是 EDIT 任务。解包 → 修复损坏的 `<f>` 节点 → 重打包。保留所有原始工作表和数据。

## VALIDATE — 检查公式（先阅读 `references/validate.md`）

运行 `formula_check.py` 进行静态验证。有 LibreOffice 时用 `libreoffice_recalc.py` 进行动态重算。

## 财务颜色标准

| 单元格角色 | 字体颜色 | 十六进制代码 |
|-----------|-----------|----------|
| 硬编码输入/假设值 | 蓝色 | `0000FF` |
| 公式/计算结果 | 黑色 | `000000` |
| 跨表引用公式 | 绿色 | `00B050` |

## 关键规则

1. **公式优先**：每个计算单元格必须使用 Excel 公式，不得硬编码数字
2. **CREATE → XML 模板**：复制最小模板，直接编辑 XML，用 `xlsx_pack.py` 打包
3. **EDIT → XML**：绝不使用 openpyxl 往返读写。使用解包/编辑/打包脚本
4. **始终输出文件** — 这是第一优先级
5. **交付前验证**：`formula_check.py` 退出码 0 = 安全

## 实用脚本

```bash
python3 SKILL_DIR/scripts/xlsx_reader.py input.xlsx                 # 结构发现
python3 SKILL_DIR/scripts/formula_check.py file.xlsx --json         # 公式验证
python3 SKILL_DIR/scripts/formula_check.py file.xlsx --report      # 标准化报告
python3 SKILL_DIR/scripts/xlsx_unpack.py in.xlsx /tmp/work/         # 解包供 XML 编辑
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/work/ out.xlsx          # 编辑后重打包
python3 SKILL_DIR/scripts/xlsx_shift_rows.py /tmp/work/ insert 5 1  # 移动行（插入用）
python3 SKILL_DIR/scripts/xlsx_add_column.py /tmp/work/ --col G ... # 添加带公式的列
python3 SKILL_DIR/scripts/xlsx_insert_row.py /tmp/work/ --at 6 ...  # 插入带数据的行
```
