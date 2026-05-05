---
name: unipus:feishu:upload-doc
description: 按部门规范上传文档到飞书统一云空间，自动管理目录结构和文件命名，触发词：上传文档到飞书、飞书规范上传、upload to feishu drive、飞书云空间上传
---

# unipus:feishu:upload-doc

按公司规范上传文档到飞书统一云空间，自动管理子目录创建和文件命名规范。

**主目录：** `https://es3eflgtuw.feishu.cn/drive/folder/RX2gfGuXjlTyiMdouqwcAvwpnX8`
**主目录 Token：** `RX2gfGuXjlTyiMdouqwcAvwpnX8`

---

## HARD-GATE（必须通过，否则停止）

```bash
lark-cli --version
```

若命令不存在 → **立即停止**，提示：`请先安装 lark-cli：npm install -g @larksuite/cli`，不继续任何后续步骤。

---

## 核心规范

- **主目录 Token**：`RX2gfGuXjlTyiMdouqwcAvwpnX8`
- **子目录格式**：`<部门缩写>_<项目名称>`（如 `GX_统一认证平台`）
- **文件命名格式**：`<版本>_<项目名称>_<文档类型>.<扩展名>`（如 `V2.0_统一认证平台_技术方案.md`）

部门缩写对照见 `references/dept-codes.md`。

---

## Workflow

1. **宣告**：告知用户将按规范上传文档到飞书统一云空间
2. **读取部门信息**：从 `references/dept-codes.md` 获取部门列表
3. **环境检查**（HARD-GATE）：确认 lark-cli 可用
4. **收集信息**（每次只问一个问题，按序进行）：
   - 问 1：「您属于哪个部门？」（展示部门列表供选择）
   - 问 2：「项目名称是什么？」（如：统一认证平台）
   - 问 3：「文档版本是什么？」（如：V2.0）
   - 问 4：「文档类型是什么？」（如：需求文档、技术方案、测试报告）
   - 问 5：「本地文件路径是什么？」
5. **构建规范名称**：
   - 子目录名：`<部门缩写>_<项目名称>`
   - 文件名：`<版本>_<项目名称>_<文档类型>.<原扩展名>`
6. **检查子目录是否存在**：
   ```bash
   lark-cli api GET /open-apis/drive/v1/files \
     --params '{"folder_token":"RX2gfGuXjlTyiMdouqwcAvwpnX8","page_size":200}'
   ```
7. **子目录不存在时**：
   - Dry-run 预览：显示「将在主目录下创建子目录：`GX_统一认证平台`」
   - 等待用户确认（输入 y/yes 继续）
   - 创建子目录：
     ```bash
     lark-cli api POST /open-apis/drive/v1/files/create_folder \
       --data '{"name":"GX_统一认证平台","folder_token":"RX2gfGuXjlTyiMdouqwcAvwpnX8"}'
     ```
8. **检查目标文件是否已存在**（防止重复上传）：
   - 若同名文件已存在 → 询问：「目标位置已存在同名文件，是否覆盖？」
   - 用户选择否 → 停止
9. **Dry-run 预览上传**：
   - 显示：「将上传 `本地路径` → 飞书子目录 `GX_统一认证平台` / `V2.0_统一认证平台_技术方案.md`」
   - 等待用户确认（输入 y/yes 继续）
10. **执行上传**：
    ```bash
    lark-cli drive +upload \
      --file "<本地路径>" \
      --name "V2.0_统一认证平台_技术方案.md" \
      --folder-token "<子目录 token>"
    ```
11. **输出结果**：返回飞书文档链接

---

## Red Flags

| 情况 | 处理方式 |
|---|---|
| lark-cli 未安装 | 立即停止，提示安装命令 |
| 部门不在对照表中 | 展示部门列表，请用户重新选择 |
| 用户输入非标准版本号 | 提示推荐格式：`V1.0`、`V2.3`，但不强制 |
| 主目录查询失败（403） | 提示确认 lark-cli 认证状态，运行 `lark-cli doctor` |
| 文件扩展名与文档类型不符 | 提示确认（如 `.docx` 命名为 `.md`），但以用户决定为准 |
| 用户在 dry-run 后拒绝 | 停止操作，不执行任何写入 |

---

参考文件：
- `references/dept-codes.md` — 部门缩写对照表
- `references/naming-convention.md` — 命名规范和示例
