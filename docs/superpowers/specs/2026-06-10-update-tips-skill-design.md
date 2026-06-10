# update-tips skill 设计文档

**日期：** 2026-06-10
**状态：** 已批准

---

## 背景

`tips.txt` 是 SessionStart Hook 的技巧内容文件（当前 201 条），每当 Claude Code 发布新版本，需要人工：

1. 查看 changelog
2. 识别新增/修改/废弃的功能
3. 手动更新 tips.txt 条目
4. 同步 3 处文档中的条目数字
5. 提交推送

这套流程全部为手动操作，且多处文档数字历史上出现不一致（158/175/334 三个不同数字并存）。`update-tips` skill 将整个流程自动化。

---

## 目标

- 用户执行 `/update-tips` 后，无需任何中间干预，全自动完成 tips.txt 的增删改和文档同步
- 执行完毕展示摘要，随后进入 `unipus-commit` 提交流程

---

## 文件位置

```
.claude/skills/update-tips/SKILL.md
```

`.claude/skills/` 下的 skill 仅服务于本仓库工作流，不发布到 marketplace，不触发版本号升级。

---

## 执行流程（6 步全自动）

```
① 抓取 changelog
   WebFetch https://github.com/anthropics/claude-code/releases
   默认抓取最近 10 个版本；用户可指定：/update-tips 5

② 读取现有 tips.txt
   建立已覆盖功能的语义索引（201 条）

③ 三类差异识别
   ├─ 新增：changelog 有，tips.txt 没有 → 生成新条目
   ├─ 修改：已有条目与 changelog 矛盾/过时 → 原地更新
   └─ 删除：changelog 标注 Removed/Deprecated → 直接删除

④ 写入 tips.txt
   新增追加末尾 · 修改原地替换 · 删除直接移除

⑤ 同步文档数字
   统计新总数，批量更新：
   - .claude-plugin/marketplace.json（2处）
   - README.md（2处）
   - plugins/unipus-devops-plugin/hooks/README.md（1处）

⑥ 展示摘要 → 调用 unipus-commit skill
```

---

## 差异识别规则

### 新增
- changelog 出现的新 flag、新命令、新 hook 事件、新设置项，tips.txt 无对应条目
- 按现有格式生成，从 11 个分类中选最匹配的
- 例子中命令必须完整可执行（`claude --xxx`，不是 `--xxx`）

### 修改
- 命令语法与 changelog 不符 → 更正
- 描述的行为已被新版本改变 → 更新
- 例子中用了不存在的 flag → 修正
- **不修改**：仅措辞差异、风格调整

### 删除
- changelog 明确标注 `Removed` / `Deprecated` / `no longer available` → 直接删除
- **不删除**：changelog 只是新增了替代功能，旧功能仍可用

### 条目格式校验（写入时自动执行）
- 必须包含功能/效果/例子三个字段
- 例子中命令必须是完整可执行形式
- 每条末尾必须有 `---` 分隔符

---

## 执行摘要格式

```
✅ update-tips 完成 · v2.1.160 → v2.1.170

📥 新增  8 条
  · [CLI] --safe-mode 安全模式
  · [CLI] /cd 切换工作目录
  · ...

✏️  修改  3 条
  · [CLI] claude agents → 补充 done/total 进度字段
  · ...

🗑️  删除  1 条
  · [CLI] claude doctor（已移除）

📊 条目总数：201 → 209
📄 已同步：marketplace.json · README.md · hooks/README.md
🔖 版本：2.0.1 → 2.0.2（Patch）

---
进入提交流程...
```

---

## 触发方式

| 输入 | 行为 |
|---|---|
| `/update-tips` | 抓取最近 10 个版本 |
| `/update-tips 5` | 抓取最近 5 个版本 |
| "更新tips" / "同步tips" | 语义等价触发 |

---

## 不在范围内

- 不修改 `show-tip.sh` 逻辑
- 不处理 tips.txt 以外的文件内容
- 不新增 Hook 或其他自动化机制
- 不对 `.claude/` 下的改动升级版本号（遵循 CLAUDE.md 规范）
