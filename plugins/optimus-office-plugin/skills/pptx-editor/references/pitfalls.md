# QA 流程与常见陷阱

## QA 流程

**假设一定存在问题。你的工作是找出它们。**

第一次渲染几乎不会是正确的。以找 Bug 的态度来做 QA，而不是做确认性检查。如果第一轮检查没有发现任何问题，那说明你看得不够仔细。

### 内容 QA

```bash
python -m markitdown output.pptx
```

检查缺失内容、错别字、顺序错误。

**检查残留占位文字：**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|placeholder|this.*(page|slide).*layout"
```

如果 grep 有输出，在声明成功前先修复。

### 验证循环

1. 生成幻灯片 → 用 `python -m markitdown output.pptx` 提取文字 → 审查内容
2. **列出发现的问题**（若未发现任何问题，再批判性地检查一遍）
3. 修复问题
4. **重新验证受影响的幻灯片**——一处修复经常引入另一个问题
5. 重复直到完整检查一遍没有新问题

**在完成至少一次"修复-验证"循环之前，不得声明成功。**

### 逐张 QA（从零创建时）

```bash
python -m markitdown slide-XX-preview.pptx
```

检查缺失内容、占位文字、缺少页码徽标。

---

## 常见错误

- **不要重复相同布局**——在幻灯片间变换列数、卡片和强调框
- **不要居中对齐正文**——段落和列表左对齐，只有标题居中
- **不要忽视字号对比**——标题需 36pt+ 才能从 14-16pt 正文中突出
- **不要默认选蓝色**——选择能反映具体主题的颜色
- **不要随意混用间距**——选定 0.3" 或 0.5" 的间距后保持一致
- **不要只精心设计一张幻灯片而其余敷衍了事**——要么全力投入，要么整体保持简洁
- **不要创建纯文字幻灯片**——添加图片、图标、图表或视觉元素；避免纯标题+要点
- **不要忘记文本框内边距**——对齐文字边缘与形状边缘时，在文本框上设置 `margin: 0`，或偏移形状以补偿内边距
- **不要使用低对比度元素**——图标和文字都需要与背景形成强烈对比
- **绝不在标题下方使用强调线**——这是 AI 生成幻灯片的标志性特征；改用留白或背景色
- **绝不在十六进制颜色中使用 "#"**——在 PptxGenJS 中会导致文件损坏
- **绝不将透明度编码在十六进制字符串中**——使用 `opacity` 属性代替
- **绝不在 createSlide() 中使用 async/await**——compile.js 不会 await
- **绝不在多个 PptxGenJS 调用间复用选项对象**——PptxGenJS 会就地修改对象

---

## 关键陷阱 — PptxGenJS

### 绝不在 createSlide() 中使用 async/await

```javascript
// 错误 - compile.js 不会 await
async function createSlide(pres, theme) { ... }

// 正确
function createSlide(pres, theme) { ... }
```

### 绝不在十六进制颜色中使用 "#"

```javascript
color: "FF0000"      // 正确
color: "#FF0000"     // 文件损坏
```

### 绝不将透明度编码在十六进制字符串中

```javascript
shadow: { color: "00000020" }              // 文件损坏
shadow: { color: "000000", opacity: 0.12 } // 正确
```

### 防止标题文字换行

```javascript
// 长标题使用 fit:'shrink'
slide.addText("Long Title Here", {
  x: 0.5, y: 2, w: 9, h: 1,
  fontSize: 48, fit: "shrink"
});
```

### 绝不在多个调用间复用选项对象

```javascript
// 错误
const shadow = { type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 };
slide.addShape(pres.shapes.RECTANGLE, { shadow, ... });
slide.addShape(pres.shapes.RECTANGLE, { shadow, ... });

// 正确 - 使用工厂函数
const makeShadow = () => ({ type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 });
slide.addShape(pres.shapes.RECTANGLE, { shadow: makeShadow(), ... });
slide.addShape(pres.shapes.RECTANGLE, { shadow: makeShadow(), ... });
```
