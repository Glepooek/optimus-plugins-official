---
name: unipus-commit
description: Use when the user wants to commit and push completed changes to this unipus-plugins-official plugin repository — trigger phrases include "commit", "push", "提交", "推上去", "推到 master", or when done editing any plugin, skill file, hook script, or marketplace.json. Always invoke this skill instead of a bare git workflow when a commit-push is requested in this repo.
---

# /unipus-commit

Project-specific commit workflow. Handles version bumping, selective staging, and push to master in one pass.

## Step 1 — Inspect changes

```bash
git status
git diff HEAD --stat
git log --oneline -5
```

## Step 2 — Decide version bump

Check whether `.claude-plugin/marketplace.json` needs a version bump:

| What changed | Bump type |
|---|---|
| New plugin directory OR new skill added | **Minor** `x.X.x` |
| Improved existing skill, fixed hook, updated docs | **Patch** `x.x.X` |
| Architecture change, breaking API, renamed skill | **Major** `X.x.x` |
| Config tweak, comment fix, internal refactor only | **No bump** |

If a bump is needed, edit `.claude-plugin/marketplace.json` → increment `"version"` field, then stage it alongside other files.

## Step 3 — Stage files selectively

**Never use `git add -A`** — it risks staging `.env`, lock files, or binaries.

```bash
# Stage each changed file by name
git add .claude-plugin/marketplace.json
git add plugins/<plugin-name>/skills/<skill-name>/SKILL.md
# ... add only what belongs in this commit

# Verify before committing
git diff --staged --stat
```

## Step 4 — Generate commit message

Analyze `git diff --staged` to write a conventional commit. Infer scope from the plugin/skill name.

**Format:**
```
<type>(<scope>): <concise summary in Chinese or English>

- <specific change detail>
- <specific change detail>

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
```

**Type reference:**
- `feat` — new skill, new plugin, new hook
- `fix` — bug fix in hook script, broken config
- `docs` — README, CLAUDE.md, tips.txt updates
- `chore` — version bump only, dependency update
- `refactor` — restructured skill without behavior change
- `perf` — skill token optimization

**Scope examples:** `wpf-skill`, `devops-hooks`, `marketplace`, `office-plugin`

Pass multi-line messages via heredoc to avoid quoting issues:
```bash
git commit -m "$(cat <<'EOF'
feat(wpf-skill): add event leak and async patterns

- 新增检查点 9: 事件处理器内存泄漏（WeakEventManager）
- 新增检查点 10: 数据绑定性能优化（OneTime/OneWay）
- 新增检查点 11: UI线程与Dispatcher优化

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

## Step 5 — Push to master

```bash
git push origin master
```

If push fails due to proxy/network reset, retry once. If it fails again, report the error to the user — do **not** force push or `--no-verify`.

## Common mistakes

- Staging with `git add -A` — can include sensitive files
- Forgetting version bump when a new skill is added (should be minor)
- Using generic commit messages like "update files" — always describe the specific change
- Bumping major for a skill content change — major is only for breaking/architectural changes
