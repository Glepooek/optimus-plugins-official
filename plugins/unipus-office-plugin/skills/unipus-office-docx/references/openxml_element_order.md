# OpenXML 子元素排序规则

OpenXML 中的元素顺序由 XSD schema 定义。顺序错误会产生无效文档，Word 可能拒绝打开或静默修复（可能导致数据丢失）。

> **核心规则**：属性元素（`*Pr`）必须始终是其父元素的**第一个子元素**。

---

## w:document

```
子元素顺序：
1. w:background       [0..1]  — 页面背景颜色/填充
2. w:body              [0..1]  — 文档内容容器
```

---

## w:body

```
子元素顺序（重复组）：
1. w:p                 [0..*]  — 段落
2. w:tbl               [0..*]  — 表格
3. w:sdt               [0..*]  — 结构化文档标签（内容控件）
4. w:sectPr            [0..1]  — 最后一个子元素：最终节属性
```

注意：`w:p`、`w:tbl` 和 `w:sdt` 按文档顺序交错出现。唯一的严格规则是 `w:sectPr` 必须是 `w:body` 的**最后一个子元素**。

---

## w:p（段落）

```
子元素顺序：
1. w:pPr               [0..1]  — 段落属性（必须是第一个）

之后可任意混合（按文档顺序交错）：
- w:r                  [0..*]  — 文字 run
- w:hyperlink          [0..*]  — 超链接包装器
- w:ins                [0..*]  — 跟踪插入
- w:del                [0..*]  — 跟踪删除
- w:bookmarkStart      [0..*]  — 书签锚点起始
- w:bookmarkEnd        [0..*]  — 书签锚点结束
- w:commentRangeStart  [0..*]  — 批注范围起始
- w:commentRangeEnd    [0..*]  — 批注范围结束
- w:proofErr           [0..*]  — 校对错误标记
- w:fldSimple          [0..*]  — 简单域
- w:sdt                [0..*]  — 行内内容控件
- w:smartTag           [0..*]  — 智能标记
```

**实践说明**：`w:pPr` 之后的其余子元素按文档阅读顺序出现。run、超链接、书签和批注范围根据其在文本中的位置自由交错。

---

## w:pPr（段落属性）

```
子元素顺序：
1.  w:pStyle            [0..1]  — 段落样式引用
2.  w:keepNext          [0..1]  — 与下一段落保持同页
3.  w:keepLines         [0..1]  — 段落内各行保持同页
4.  w:pageBreakBefore   [0..1]  — 段前分页
5.  w:framePr           [0..1]  — 文本框属性
6.  w:widowControl      [0..1]  — 孤行/孀行控制
7.  w:numPr             [0..1]  — 编号属性
8.  w:suppressLineNumbers [0..1]
9.  w:pBdr              [0..1]  — 段落边框
10. w:shd               [0..1]  — 底纹
11. w:tabs              [0..1]  — 制表位
12. w:suppressAutoHyphens [0..1]
13. w:kinsoku           [0..1]  — CJK 禁则处理设置
14. w:wordWrap           [0..1]
15. w:overflowPunct     [0..1]
16. w:topLinePunct      [0..1]
17. w:autoSpaceDE       [0..1]
18. w:autoSpaceDN       [0..1]
19. w:bidi              [0..1]  — 从右到左段落
20. w:adjustRightInd    [0..1]
21. w:snapToGrid        [0..1]
22. w:spacing            [0..1]  — 行距和段落间距
23. w:ind               [0..1]  — 缩进
24. w:contextualSpacing [0..1]
25. w:mirrorIndents     [0..1]
26. w:suppressOverlap   [0..1]
27. w:jc                [0..1]  — 对齐方式（左/居中/右/两端）
28. w:textDirection     [0..1]
29. w:textAlignment     [0..1]
30. w:outlineLvl        [0..1]  — 大纲级别
31. w:divId             [0..1]
32. w:rPr               [0..1]  — 段落标记的字符属性
33. w:sectPr            [0..1]  — 分节符（节在该段落结束）
34. w:pPrChange         [0..1]  — 跟踪段落属性更改
```

---

## w:r（Run）

```
子元素顺序：
1. w:rPr               [0..1]  — 字符属性（必须是第一个）

之后可包含（每个 run 通常含一个）：
- w:t                  [0..*]  — 文本内容
- w:br                 [0..*]  — 换行（行、页、列）
- w:tab                [0..*]  — 制表符
- w:cr                 [0..*]  — 回车符
- w:sym               [0..*]  — 符号字符
- w:drawing            [0..*]  — DrawingML 对象（图片）
- w:pict               [0..*]  — VML 图片（旧版）
- w:fldChar            [0..*]  — 复杂域字符
- w:instrText          [0..*]  — 域指令文本
- w:delText            [0..*]  — 已删除文本（位于 w:del 内）
- w:footnoteReference  [0..*]
- w:endnoteReference   [0..*]
- w:commentReference   [0..*]
- w:lastRenderedPageBreak [0..*]
```

---

## w:rPr（字符属性）

```
子元素顺序：
1.  w:rStyle            [0..1]  — 字符样式引用
2.  w:rFonts            [0..1]  — 字体规格
3.  w:b                 [0..1]  — 粗体
4.  w:bCs               [0..1]  — 复杂文字粗体
5.  w:i                 [0..1]  — 斜体
6.  w:iCs               [0..1]  — 复杂文字斜体
7.  w:caps              [0..1]  — 全大写
8.  w:smallCaps         [0..1]  — 小型大写字母
9.  w:strike            [0..1]  — 删除线
10. w:dstrike           [0..1]  — 双删除线
11. w:outline           [0..1]
12. w:shadow            [0..1]
13. w:emboss            [0..1]
14. w:imprint           [0..1]
15. w:noProof           [0..1]  — 禁用校对
16. w:snapToGrid        [0..1]
17. w:vanish            [0..1]  — 隐藏文字
18. w:color             [0..1]  — 文字颜色
19. w:spacing            [0..1]  — 字符间距
20. w:w                 [0..1]  — 字符宽度缩放
21. w:kern              [0..1]  — 字体字距调整
22. w:position          [0..1]  — 垂直位置（上升/下降）
23. w:sz                [0..1]  — 字号（半磅）
24. w:szCs              [0..1]  — 复杂文字字号
25. w:highlight         [0..1]  — 文字高亮颜色
26. w:u                 [0..1]  — 下划线
27. w:effect            [0..1]  — 文字特效（动画）
28. w:bdr               [0..1]  — run 边框
29. w:shd               [0..1]  — run 底纹
30. w:vertAlign         [0..1]  — 上标/下标
31. w:rtl               [0..1]  — 从右到左
32. w:cs                [0..1]  — 复杂文字
33. w:lang              [0..1]  — 语言
34. w:rPrChange         [0..1]  — 跟踪字符属性更改
```

---

## w:tbl（表格）

```
子元素顺序：
1. w:tblPr              [1..1]  — 表格属性（必填，必须是第一个）
2. w:tblGrid            [1..1]  — 列宽定义（必填）
3. w:tr                 [1..*]  — 表格行
```

---

## w:tblPr（表格属性）

```
子元素顺序：
1.  w:tblStyle           [0..1]  — 表格样式引用
2.  w:tblpPr             [0..1]  — 表格定位
3.  w:tblOverlap         [0..1]
4.  w:bidiVisual         [0..1]  — 从右到左表格
5.  w:tblStyleRowBandSize [0..1]
6.  w:tblStyleColBandSize [0..1]
7.  w:tblW               [0..1]  — 首选表格宽度
8.  w:jc                 [0..1]  — 表格对齐
9.  w:tblCellSpacing     [0..1]
10. w:tblInd             [0..1]  — 表格相对边距的缩进
11. w:tblBorders         [0..1]  — 表格边框
12. w:shd                [0..1]  — 表格底纹
13. w:tblLayout          [0..1]  — 固定宽度或自适应
14. w:tblCellMar         [0..1]  — 默认单元格边距
15. w:tblLook            [0..1]  — 条件格式标志
16. w:tblCaption         [0..1]  — 无障碍标题
17. w:tblDescription     [0..1]  — 无障碍描述
18. w:tblPrChange        [0..1]  — 跟踪表格属性更改
```

---

## w:tr（表格行）

```
子元素顺序：
1. w:trPr               [0..1]  — 行属性（必须是第一个）
2. w:tc                  [1..*]  — 表格单元格
```

---

## w:trPr（表格行属性）

```
子元素顺序：
1.  w:cnfStyle           [0..1]  — 条件格式
2.  w:divId              [0..1]
3.  w:gridBefore         [0..1]  — 第一个单元格之前的网格列数
4.  w:gridAfter          [0..1]  — 最后一个单元格之后的网格列数
5.  w:wBefore            [0..1]
6.  w:wAfter             [0..1]
7.  w:cantSplit          [0..1]  — 禁止行跨页分割
8.  w:trHeight           [0..1]  — 行高
9.  w:tblHeader          [0..1]  — 作为表头行重复显示
10. w:tblCellSpacing     [0..1]
11. w:jc                 [0..1]  — 行对齐
12. w:hidden             [0..1]
13. w:ins                [0..1]  — 跟踪行插入
14. w:del                [0..1]  — 跟踪行删除
15. w:trPrChange         [0..1]  — 跟踪行属性更改
```

---

## w:tc（表格单元格）

```
子元素顺序：
1. w:tcPr               [0..1]  — 单元格属性（必须是第一个）
2. w:p                   [1..*]  — 段落（至少需要一个）
3. w:tbl                 [0..*]  — 嵌套表格
```

---

## w:tcPr（表格单元格属性）

```
子元素顺序：
1.  w:cnfStyle           [0..1]
2.  w:tcW                [0..1]  — 单元格宽度
3.  w:gridSpan           [0..1]  — 水平合并（列跨度）
4.  w:hMerge             [0..1]  — 旧式水平合并
5.  w:vMerge             [0..1]  — 垂直合并
6.  w:tcBorders          [0..1]  — 单元格边框
7.  w:shd                [0..1]  — 单元格底纹
8.  w:noWrap             [0..1]
9.  w:tcMar              [0..1]  — 单元格边距
10. w:textDirection      [0..1]
11. w:tcFitText          [0..1]
12. w:vAlign             [0..1]  — 垂直对齐
13. w:hideMark           [0..1]
14. w:tcPrChange         [0..1]  — 跟踪单元格属性更改
```

---

## w:sectPr（节属性）

```
子元素顺序：
1.  w:headerReference    [0..*]  — 页眉引用（类型：default/first/even）
2.  w:footerReference    [0..*]  — 页脚引用
3.  w:endnotePr          [0..1]
4.  w:footnotePr         [0..1]
5.  w:type               [0..1]  — 分节符类型（nextPage/continuous/evenPage/oddPage）
6.  w:pgSz               [0..1]  — 页面尺寸
7.  w:pgMar              [0..1]  — 页面边距
8.  w:paperSrc           [0..1]
9.  w:pgBorders          [0..1]  — 页面边框
10. w:lnNumType          [0..1]  — 行编号
11. w:pgNumType          [0..1]  — 页码编号
12. w:cols               [0..1]  — 栏目定义
13. w:formProt           [0..1]
14. w:vAlign             [0..1]  — 页面垂直对齐
15. w:noEndnote          [0..1]
16. w:titlePg            [0..1]  — 首页不同的页眉/页脚
17. w:textDirection      [0..1]
18. w:bidi               [0..1]
19. w:rtlGutter          [0..1]
20. w:docGrid            [0..1]  — 文档网格
21. w:sectPrChange       [0..1]  — 跟踪节属性更改
```

---

## w:hdr（页眉）/ w:ftr（页脚）

```
子元素（与 w:body 内容相同的结构）：
1. w:p                   [0..*]  — 段落
2. w:tbl                 [0..*]  — 表格
3. w:sdt                 [0..*]  — 内容控件
```

页眉和页脚本质上是迷你文档。它们遵循与 `w:body` 相同的内容模型，但没有最终的 `w:sectPr`。
