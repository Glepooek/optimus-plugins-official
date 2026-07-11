---
name: optimus-feishu-read-write
description: 飞书文档读写通用工具，支持读取文档/表格、上传文件、导出文档，触发词：飞书读取、飞书上传、飞书导出、fetch feishu、read feishu doc
metadata:
  author: desktop client team
compatibility: 硬性依赖 @larksuite/cli（通过 npx 调用，需 Node.js/npm 环境）且需登录认证。
allowed-tools: Bash
---

# optimus-feishu-read-write

飞书文档读写通用工具，整合 lark-cli 能力，支持读取、上传、导出飞书云文档。

---

## HARD-GATE（必须通过，否则停止）

执行任何操作前，依次检查：

```bash
npx @larksuite/cli --version   # 确认已安装
npx @larksuite/cli doctor      # 确认已认证
```

任一失败 → 停止，提示用户安装或重新认证，不继续执行。

---

## Workflow

1. **宣告**：告知用户将使用 lark-cli 进行飞书文档操作
2. **环境检查**（HARD-GATE）：运行上方两条命令，确认通过
3. **判断意图**：
   - 提供了飞书 URL → 读取操作
   - 提供了本地文件路径 → 上传/导入操作
   - 提供了 doc token + 目标目录 → 导出操作
   - 意图不明 → 询问用户（每次只问一个问题）
4. **补全必要输入**（缺少时逐一询问）：
   - 读取：需要 URL（doc/sheet/wiki）
   - 上传：需要本地文件路径和文件名
   - 导出：需要 doc token 和输出目录
5. **解析 URL 类型**（参见 `references/url-patterns.md`）
6. **执行命令**（参见 `references/commands.md`）
7. **输出结果**：
   - 读取：返回 Markdown 内容
   - 上传：返回飞书链接或 token
   - 导出：返回本地文件路径

---

## 意图判断规则

| 用户输入特征 | 判断意图 |
|---|---|
| 包含 `feishu.cn/docx/` 或 `feishu.cn/doc/` | 读取文档 |
| 包含 `feishu.cn/sheets/` | 读取表格 |
| 包含 `feishu.cn/wiki/` | 读取 wiki |
| 本地文件路径 + "上传" / "import" | 导入为飞书文档 |
| 本地文件路径 + "上传" / "upload" | 上传到云空间 |
| doc token + "导出" / "export" | 导出到本地 |

---

## Red Flags

| 情况 | 处理方式 |
|---|---|
| `doctor` 报 401/未认证 | 停止，提示运行 `npx @larksuite/cli login` |
| lark-cli 未安装 | 停止，提示 `npm install -g @larksuite/cli` |
| URL 无法解析类型 | 对照 `references/url-patterns.md`，仍无法判断则询问用户 |
| 表格读取范围过大 | 提示用户缩小 range，默认最多 A1:Z1000 |
| 上传失败（403） | 提示检查目标文件夹权限 |

---

参考文件：
- `references/url-patterns.md` — URL 解析规则
- `references/commands.md` — lark-cli 命令速查
- `references/error-guide.md` — 常见错误及解决方案
