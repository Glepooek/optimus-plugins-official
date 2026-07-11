# 数据读取与分析指南

> READ 路径参考文档。使用 `xlsx_reader.py` 进行结构发现和数据质量审计，然后用 pandas 进行自定义分析。**永远不要修改源文件。**

---

## 适用场景

用户要求读取、分析、查看、汇总、提取或回答关于 Excel/CSV 文件内容的问题，不需要修改文件。如果需要修改，转交给 `edit.md` 处理。

---

## 工作流

### 第一步 — 结构发现

首先运行 `xlsx_reader.py`。它处理格式检测、编码回退、结构探索和数据质量审计：

```bash
python3 SKILL_DIR/scripts/xlsx_reader.py input.xlsx                 # 完整报告
python3 SKILL_DIR/scripts/xlsx_reader.py input.xlsx --sheet Sales   # 单个工作表
python3 SKILL_DIR/scripts/xlsx_reader.py input.xlsx --quality       # 仅质量审计
python3 SKILL_DIR/scripts/xlsx_reader.py input.xlsx --json          # 机器可读输出
```

支持格式：`.xlsx`、`.xlsm`、`.csv`、`.tsv`。脚本会对 CSV 尝试多种编码（utf-8-sig、gbk、utf-8、latin-1）。

### 第二步 — 用 pandas 进行自定义分析

加载数据并执行用户请求的分析：

```python
import pandas as pd
df = pd.read_excel("input.xlsx", sheet_name=None)  # 获取所有工作表的字典
# CSV 文件：pd.read_csv("input.csv")
```

**表头处理**（当默认 `header=0` 不起作用时）：

| 情况 | 代码 |
|-----------|------|
| 表头在第 3 行 | `pd.read_excel(path, header=2)` |
| 多级合并表头 | `pd.read_excel(path, header=[0, 1])` |
| 无表头 | `pd.read_excel(path, header=None)` |

**分析快速参考：**

| 场景 | 模式 |
|----------|---------|
| 描述性统计 | `df.describe()` 或 `df['列'].agg(['sum', 'mean', 'min', 'max'])` |
| 分组聚合 | `df.groupby('Region')['Revenue'].agg(Total='sum', Avg='mean')` |
| 前 N 名 | `df.groupby('Region')['Revenue'].sum().sort_values(ascending=False).head(5)` |
| 数据透视表 | `df.pivot_table(values='Revenue', index='Region', columns='Quarter', aggfunc='sum', margins=True)` |
| 时间序列 | `df.set_index(pd.to_datetime(df['Date'])).resample('ME')['Revenue'].sum()` |
| 跨表合并 | `pd.merge(sales, customers, on='CustomerID', how='left', validate='m:1')` |
| 堆叠工作表 | `pd.concat([df.assign(Source=name) for name, df in sheets.items()], ignore_index=True)` |
| 大文件（>50MB） | `pd.read_excel(path, usecols=['Date', 'Revenue'])` 或 `pd.read_csv(path, chunksize=10000)` |

### 第三步 — 输出

如果用户指定了输出文件路径，写入该文件（最高优先级）。报告格式为：

```
## 分析报告：{文件名}
### 文件概览     — 格式、工作表、行数
### 数据质量     — 空值、重复值、混合类型（或"无问题"）
### 关键发现     — 对用户问题的直接回答
### 附加说明     — 公式 NaN、编码问题、注意事项
```

**数字显示**：金额 `1,234,567.89`，百分比 `12.3%`，倍数 `8.5x`，计数为整数。

---

## 常见陷阱

| 陷阱 | 原因 | 修复方法 |
|---------|-------|-----|
| 公式单元格读取为 NaN | 新生成文件中 `<v>` 缓存为空 | 告知用户；建议在 Excel 中打开并重新保存；或使用 `libreoffice_recalc.py` |
| CSV 编码错误 | Windows 中文版导出使用 GBK | `xlsx_reader.py` 自动尝试多种编码；全部失败时手动指定 |
| 列中类型混合 | 列中同时有数字和文字（如"N/A"） | `pd.to_numeric(df['列'], errors='coerce')` — 报告无法转换的行 |
| 年份显示为 2,024 | 年份列应用了千分位格式 | `df['Year'].astype(int).astype(str)` |
| 多级表头 | 两行表头已合并 | `pd.read_excel(path, header=[0, 1])`，然后用 `' - '.join()` 展平 |
| 行号不匹配 | pandas 从 0 开始，Excel 从 1 开始 | `excel行号 = pandas索引 + 2`（+1 转为 1 起始，+1 跳过表头） |

**关键**：永远不要用 `data_only=True` 打开再 `save()` — 这会永久销毁所有公式。

---

## 禁止操作

- 绝不修改源文件（不 `save()`，不编辑 XML）
- 绝不将公式 NaN 报告为"数据为零"——解释这是公式缓存问题
- 绝不将 pandas 索引作为 Excel 行号报告
- 绝不做数据不支持的推测性结论
