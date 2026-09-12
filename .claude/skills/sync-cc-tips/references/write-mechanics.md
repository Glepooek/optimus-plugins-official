# 写入机制 — 回滚基线与批量写法

**何时加载**：第四步 CHECKPOINT 已确认、即将实际写入 tips.jsonl 时。🚦 零变更总闸触发（0 新增 + 0 修改 + 0 删除）时整个第四步跳过，本文件不必加载；只推进 `.last-synced-version` 不需要本文件。

## 回滚基线（写入前确认，不额外备份）

tips.jsonl 是已入库文件，**git 本身就是回滚基线**，无需另存副本：

```bash
git status --short plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl   # 应为空（干净）
```

- 输出为空 → 直接改，出错时 `git restore <path>` 即可回到本轮起点
- 输出非空**且与前置校验所见相同** → 用户已在前置校验的 CHECKPOINT 同意带脏基线继续，**据此直接放行，不要二次询问**——再问一次等于作废用户刚给出的同意
- 输出非空**且与前置校验所见不同** → 中途又被别的操作改过，前次同意不覆盖新出现的改动，回到前置校验那个 CHECKPOINT 重新确认
- 需要与改动前对比时用 `git show HEAD:plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl`

⚠️ 本探测在「执行前置校验」已做过一次，此处是**紧邻破坏性写入前的复检**，不是重复——两次之间隔着抓取、判定、生成三个阶段，其间工作区状态可能被别的操作改变。复检的作用是**比对与前次是否相同**，不是重新征求同意。

⚠️ **不要 `cp` 到 `/tmp` 做备份**——`cp` 会报成功而 Python 读不到，备份形同虚设且无任何警示（失效原理见 SKILL.md 文末黑名单）。凡需跨 Bash 与 Python 传递的临时文件，一律放仓库内相对路径。

## 写入方式

条目多于两三条时，不要逐条 `Edit` 字面匹配——JSONL 单行内含大量转义（`\n`、中文引号、`\"`），字面匹配极易失败。改为写一个一次性 Python 脚本按 `id` 增删改：

```
Write: .claude/skills/sync-cc-tips/scripts/_apply_sync.py   （下划线前缀标记临时脚本）
```

脚本要点：`json.loads` 逐行读入 → 按 `id` 匹配处理 → `json.dumps(ensure_ascii=False)` 写回，`io.open(..., newline="\n")` 固定换行符；结尾自校验「旧数 − 删除 + 新增 == 实得」并在不符时 `sys.exit` 报错。**用后必须删除该脚本**，不要留在 `scripts/` 里污染正式脚本目录。

```
Edit: plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl   （改动 ≤ 2 条时直接用）
```

- **新增**：追加到文件末尾，每条为一行合法 JSON 对象
- **修改**：原地替换对应条目所在行，保持位置不变
- **删除**：移除对应条目所在行

## 写入失败处理

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| Edit 工具报错（文件锁 / 权限不足） | 等待 2 秒后重试一次 | 停止流程，报告错误路径，不继续第五步 |
| Edit 报 `String to replace not found`，但内容肉眼看着一致 | JSONL 行内转义（`\n`、`\"`）导致字面匹配失效，改用上方「写入方式」的 Python 脚本按 `id` 操作 | 停止流程，报告哪几条无法定位 |
| 写入后读回内容与预期不符 | 重新执行 Edit | 停止流程，提示用户手动检查文件状态 |
| 删除条目后空行残留 | 再次定位并删除残留在行 | 在摘要中标注"空行可能残留，请人工确认" |
| Python 报 `FileNotFoundError` 读某个 Bash 刚创建的文件 | 该文件在 `/tmp` 等 Git Bash 专有路径下，Windows 原生 Python 看不到；改用仓库内相对路径重新生成 | 用 `git show HEAD:<path>` 取基线替代临时文件 |
