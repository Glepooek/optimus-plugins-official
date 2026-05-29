# Eval 3 — With Skill Response: Improved Existing Skill Content

## Step 1 — Inspect Changes

From the provided git status:
- `plugins/unipus-frontend-plugin/skills/wpf-xaml-performance/SKILL.md` — modified
- `plugins/unipus-frontend-plugin/skills/wpf-xaml-performance/evals/evals.json` — modified

No new files, no new plugins, no new skill directories.

## Step 2 — Version Bump Decision

**Decision: Patch bump (`x.x.X`)**

Reasoning using the skill's decision table:

| Scenario | Match? |
|---|---|
| New plugin directory OR new skill added | ❌ No — this modifies an existing skill |
| Improved existing skill, fixed hook, updated docs | ✅ Yes — SKILL.md content significantly improved, evals updated |
| Architecture change, breaking API, renamed skill | ❌ No |
| Config tweak, comment fix, internal refactor only | ❌ No — adding 3 new checkpoints is a meaningful improvement |

→ **Patch bump** applies. I would edit `.claude-plugin/marketplace.json` to increment the patch version (e.g., `1.0.8` → `1.0.9`).

## Step 3 — Staging Commands

```bash
git add plugins/unipus-frontend-plugin/skills/wpf-xaml-performance/SKILL.md
git add plugins/unipus-frontend-plugin/skills/wpf-xaml-performance/evals/evals.json
git add .claude-plugin/marketplace.json

# Verify staged files
git diff --staged --stat
```

Files staged: 3 files (the two modified skill files + marketplace.json for the patch bump).
**Not used**: `git add -A` or `git add .`

## Step 4 — Commit Message

```bash
git commit -m "$(cat <<'EOF'
feat(wpf-skill): 新增事件泄漏、数据绑定、Dispatcher 优化检查点

- 新增 Checkpoint 9: 事件处理器内存泄漏（WeakEventManager、Unloaded 取消订阅）
- 新增 Checkpoint 10: 数据绑定性能（OneTime/OneWay 绑定、深层链避免、转换器缓存）
- 新增 Checkpoint 11: UI 线程与 Dispatcher 优化（async/await + Task.Run、InvokeAsync）
- 同步新增 evals/evals.json 中 eval-4/5/6 测试用例

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

- **Type**: `feat` — adding substantial new content (3 new checkpoints)
- **Scope**: `wpf-skill` — matches the affected plugin/skill
- **Summary**: Chinese, concise, describes the change

## Step 5 — Push

```bash
git push origin master
```
