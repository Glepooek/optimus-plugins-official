# 修订跟踪指南

## 概述

OpenXML 中的修订跟踪使用修订标记元素记录插入、删除和格式更改。每条修订都有唯一的 ID、作者和时间戳。

---

## 插入：`<w:ins>`

包裹在跟踪过程中插入的 run：

```xml
<w:ins w:id="1" w:author="张三" w:date="2026-03-21T10:30:00Z">
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" />
      <w:sz w:val="22" />
    </w:rPr>
    <w:t>这段文字是插入的。</w:t>
  </w:r>
</w:ins>
```

- `w:id` — 唯一修订 ID（整数，在整个文档中必须唯一）
- `w:author` — 标识作者的自由文本字符串
- `w:date` — ISO 8601 格式，含时区：`YYYY-MM-DDTHH:MM:SSZ`
- 内部内容为带可选格式的普通 run（`w:r`）

---

## 删除：`<w:del>`

包裹在跟踪过程中删除的 run：

```xml
<w:del w:id="2" w:author="张三" w:date="2026-03-21T10:31:00Z">
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" />
      <w:sz w:val="22" />
    </w:rPr>
    <w:delText xml:space="preserve">这段文字是删除的。</w:delText>
  </w:r>
</w:del>
```

**关键**：在 `<w:del>` 内部，文字**必须**使用 `<w:delText>`，**不能**使用 `<w:t>`。在删除标记内使用 `<w:t>` 是无效的，会导致文档损坏或意外行为。Word 可能会静默修复，但其他解析器会失败。

---

## 格式更改：`<w:rPrChange>`

记录某个 run 的格式被修改。放置于 `w:rPr` 内，存储**修改前**的格式：

```xml
<w:r>
  <w:rPr>
    <w:b />  <!-- 当前：粗体 -->
    <w:rPrChange w:id="3" w:author="李四" w:date="2026-03-21T11:00:00Z">
      <w:rPr>
        <!-- 之前：无粗体（空 rPr 表示无格式） -->
      </w:rPr>
    </w:rPrChange>
  </w:rPr>
  <w:t>这段文字被设为了粗体。</w:t>
</w:r>
```

外层 `w:rPr` 保存**新**（当前）格式，`w:rPrChange` 子元素保存**旧**（之前）格式。

---

## 段落属性更改：`<w:pPrChange>`

记录段落级格式更改（对齐、间距、样式）：

```xml
<w:pPr>
  <w:jc w:val="center" />  <!-- 当前：居中 -->
  <w:pPrChange w:id="4" w:author="李四" w:date="2026-03-21T11:05:00Z">
    <w:pPr>
      <w:jc w:val="left" />  <!-- 之前：左对齐 -->
    </w:pPr>
  </w:pPrChange>
</w:pPr>
```

---

## 修订 ID 管理

- 每个修订元素（`w:ins`、`w:del`、`w:rPrChange`、`w:pPrChange`、`w:tblPrChange` 等）都需要 `w:id` 属性
- ID 必须是整个文档中**唯一的整数**
- ID 应**单调递增**（并非严格要求，但 Word 期望如此）
- 添加修订时，扫描当前最大 `w:id` 值，从该值递增

```
现有最大 ID：47
新插入：w:id="48"
新删除：w:id="49"
```

---

## 作者与日期

- **作者**：自由文本。使用一致的字符串（如所有自动编辑统一用 `"UAI"`）
- **日期**：ISO 8601 格式，带 UTC 时区标识：`2026-03-21T10:30:00Z`
  - 必须包含 `T` 分隔符和 `Z` 后缀（或 `+HH:MM` 偏移量）
  - 省略日期是允许的，但不推荐

---

## 操作方法

### 建议插入

在目标位置用 `<w:ins>` 包裹新内容：

```xml
<w:p>
  <w:r><w:t>现有文字。</w:t></w:r>
  <w:ins w:id="5" w:author="UAI" w:date="2026-03-21T12:00:00Z">
    <w:r><w:t>建议新增的文字。</w:t></w:r>
  </w:ins>
  <w:r><w:t>更多现有文字。</w:t></w:r>
</w:p>
```

### 建议删除

将现有内容用 `<w:del>` 包裹，并将 `<w:t>` 改为 `<w:delText>`：

```xml
<w:p>
  <w:r><w:t>保留此处。</w:t></w:r>
  <w:del w:id="6" w:author="UAI" w:date="2026-03-21T12:01:00Z">
    <w:r>
      <w:rPr><w:b /></w:rPr>
      <w:delText>删除此处。</w:delText>
    </w:r>
  </w:del>
  <w:r><w:t>此处也保留。</w:t></w:r>
</w:p>
```

### 接受修订

- **接受插入**：删除 `<w:ins>` 包装，将内部 run 保留为普通内容
- **接受删除**：删除整个 `<w:del>` 元素及其内容

### 拒绝修订

- **拒绝插入**：删除整个 `<w:ins>` 元素及其内容
- **拒绝删除**：删除 `<w:del>` 包装，将 `<w:delText>` 改回 `<w:t>`

---

## 跨段落操作

### 删除段落分隔符（合并段落）

当跟踪删除跨越段落边界时，在合并后的段落上使用 `<w:pPrChange>`：

```xml
<w:p>
  <w:pPr>
    <w:pPrChange w:id="7" w:author="UAI" w:date="2026-03-21T12:05:00Z">
      <w:pPr>
        <w:pStyle w:val="Normal" />
      </w:pPr>
    </w:pPrChange>
  </w:pPr>
  <w:r><w:t>第一段文字。</w:t></w:r>
  <w:del w:id="8" w:author="UAI" w:date="2026-03-21T12:05:00Z">
    <w:r><w:delText> </w:delText></w:r>
  </w:del>
  <w:r><w:t>第二段文字（已合并）。</w:t></w:r>
</w:p>
```

### 插入新段落

整个新段落用 `<w:ins>` 包裹：

```xml
<w:p>
  <w:pPr>
    <w:rPr>
      <w:ins w:id="9" w:author="UAI" w:date="2026-03-21T12:10:00Z" />
    </w:rPr>
  </w:pPr>
  <w:ins w:id="10" w:author="UAI" w:date="2026-03-21T12:10:00Z">
    <w:r><w:t>全新的段落。</w:t></w:r>
  </w:ins>
</w:p>
```

段落标记本身通过 `w:pPr > w:rPr` 内的 `w:ins` 标记为已插入。
