# FIX — 修复已有 xlsx 中的损坏公式

这是一个 EDIT 任务。必须保留所有原始工作表和数据，绝不创建新工作簿。

## 工作流

```bash
# 第一步：识别错误
python3 SKILL_DIR/scripts/formula_check.py input.xlsx --json

# 第二步：解包
python3 SKILL_DIR/scripts/xlsx_unpack.py input.xlsx /tmp/xlsx_work/

# 第三步：使用 Edit 工具修复工作表 XML 中每个损坏的 <f> 元素
#   （参见下方"错误与修复"映射表）

# 第四步：打包并验证
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx
python3 SKILL_DIR/scripts/formula_check.py output.xlsx
```

## 错误与修复映射表

| 错误 | 修复策略 |
|-------|-------------|
| `#DIV/0!` | 包裹：`IFERROR(原始公式, "-")` |
| `#NAME?` | 修复拼写错误的函数名（如 `SUMM` → `SUM`） |
| `#REF!` | 重建损坏的引用 |
| `#VALUE!` | 修复类型不匹配 |

完整的 Excel 错误类型列表和高级诊断，见 `validate.md`。

## 关键规则

- 输出必须包含与输入相同的工作表。不得创建新工作簿。
- 只修改损坏的 `<f>` 元素——其他所有内容必须保持不变。
- 打包后始终运行 `formula_check.py` 确认所有错误已解决。
