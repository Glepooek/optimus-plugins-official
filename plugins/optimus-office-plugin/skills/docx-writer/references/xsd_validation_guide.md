# XSD 验证指南

## 运行验证

```bash
# 针对 WML 子集 schema 验证
dotnet run --project u-docx validate input.docx --xsd assets/xsd/wml-subset.xsd

# 针对业务规则验证（场景 C 硬性门控必须执行）
dotnet run --project u-docx validate input.docx --xsd assets/xsd/business-rules.xsd

# 同时验证两者
dotnet run --project u-docx validate input.docx --xsd assets/xsd/wml-subset.xsd --xsd assets/xsd/business-rules.xsd
```

---

## wml-subset.xsd 的验证范围

子集 schema 验证最常见的 WordprocessingML 元素：

| 区域 | 验证的元素 |
|------|-----------|
| 文档结构 | `w:document`、`w:body`、`w:sectPr` |
| 段落 | `w:p`、`w:pPr`、`w:r`、`w:rPr`、`w:t` |
| 表格 | `w:tbl`、`w:tblPr`、`w:tblGrid`、`w:tr`、`w:tc` |
| 样式 | `w:styles`、`w:style`、`w:docDefaults` |
| 列表 | `w:numbering`、`w:abstractNum`、`w:num` |
| 页眉/页脚 | `w:hdr`、`w:ftr` |
| 修订跟踪 | `w:ins`、`w:del`、`w:rPrChange`、`w:pPrChange` |
| 批注 | `w:comment`、`w:commentRangeStart`、`w:commentRangeEnd` |

### 不覆盖的内容

- DrawingML 元素（`a:`、`pic:`、`wp:`）——图片/形状内部
- VML 元素（`v:`、`o:`）——旧版形状
- 数学元素（`m:`）——公式
- 扩展命名空间（`w14`、`w15`、`w16*`）——厂商扩展
- 自定义 XML 数据部件
- 关系和内容类型验证（属于结构性验证，不基于 schema）

---

## 错误解读

### 元素顺序错误

```
ERROR: Element 'w:jc' is not expected at this position.
Expected: w:spacing, w:ind, w:contextualSpacing, ...
Location: /word/document.xml, line 45
```

**原因**：子元素顺序错误。参见 `references/openxml_element_order.md`。
**修复**：重新排列子元素，使其符合 schema 顺序。

### 缺少必需元素

```
ERROR: Element 'w:tbl' missing required child 'w:tblPr'.
Location: /word/document.xml, line 102
```

**原因**：缺少必要的子元素。
**修复**：添加缺失的元素。表格需要同时包含 `w:tblPr` 和 `w:tblGrid`。

### 属性值无效

```
ERROR: Attribute 'w:val' has invalid value 'middle'.
Expected: 'left', 'center', 'right', 'both', 'distribute'
Location: /word/document.xml, line 78
```

**原因**：属性值不在允许的枚举值范围内。
**修复**：使用错误信息中列出的有效值之一。

### 意外元素

```
ERROR: Element 'w:customTag' is not expected.
Location: /word/document.xml, line 200
```

**原因**：该元素未在子集 schema 中定义，可能是厂商扩展。
**修复**：检查是否为已知扩展（w14/w15/w16）。如果是，通常安全。如果未知，进行调查或删除。

---

## 业务规则 XSD

`business-rules.xsd` schema 在标准 OpenXML 有效性之外还强制执行项目特定约束：

| 规则 | 检查内容 |
|------|---------|
| 必需样式 | `styles.xml` 中必须存在 `Normal`、`Heading1`–`Heading3`、`TableGrid` |
| 字体一致性 | `w:docDefaults` 字体与预期值匹配 |
| 页边距范围 | 页边距在可接受范围内（720–2160 DXA） |
| 页面尺寸 | 必须是 A4 或 Letter |
| 标题层级 | 不得跳级（如 H1 → H3 中间跳过 H2） |
| 样式链 | `w:basedOn` 引用必须指向已存在的样式 |

### 扩展业务规则

要添加项目特定规则，添加 `xs:assert` 或 `xs:restriction` 元素：

```xml
<!-- 要求最小 1 英寸页边距 -->
<xs:element name="pgMar">
  <xs:complexType>
    <xs:attribute name="top" type="xs:integer">
      <xs:restriction>
        <xs:minInclusive value="1440" />
      </xs:restriction>
    </xs:attribute>
  </xs:complexType>
</xs:element>
```

---

## 门控检查：场景 C 硬性门控

在场景 C（应用模板）中，输出文档**必须**通过 `business-rules.xsd` 验证才能交付：

```
1. 应用模板  →  output.docx
2. 验证      →  dotnet run ... validate output.docx --xsd business-rules.xsd
3. 通过？    →  交付给用户
4. 失败？    →  修复问题，重新验证，重复直到通过
```

**这是硬性门控。** 业务规则验证失败的文档**不可交付**，即使它在 Word 中能正常打开。

---

## 误报

### 厂商扩展

来自扩展命名空间（`w14`、`w15`、`w16*`）的元素不在子集 schema 中，可能触发警告：

```
WARNING: Element '{http://schemas.microsoft.com/office/word/2010/wordml}shadow' is not expected.
```

通常可以安全忽略——这些是 Microsoft 针对较新功能（如高级文字效果、批注扩展）的扩展。

### 标记兼容性

文档可能包含带有备用内容的 `mc:AlternateContent` 块。子集 schema 可能无法识别 `mc:` 命名空间处理。如果文档在 Word 中能正常打开，这些通常是安全的。

### 推荐处理方式

1. 运行验证
2. 将**错误**视为必须修复的问题
3. 审查**警告**——忽略已知厂商扩展，调查未知元素
4. 修复错误后，重新验证以确认
