# Commit Plan: Hook Bug Fix (Windows GBK Encoding)

## Step 1 — Inspect changes

```bash
git status
git diff HEAD --stat
git log --oneline -5
```

**Observed state:**
- 1 modified file: `plugins/unipus-devops-plugin/hooks/sessionstart/show-tip.sh`
- No new files, no deleted files
- Change: added `PYTHONIOENCODING=utf-8` to fix GBK codec error on Windows

---

## Step 2 — Version bump decision

**Change type:** Fixed hook script bug → matches "Improved existing skill, fixed hook, updated docs"

**Decision: Patch bump (x.x.X)**

Reasoning: This is a bug fix in an existing hook script (`show-tip.sh`). It doesn't add a new plugin or skill, and it's not a config tweak—it's a real behavioral fix affecting Windows users.

Action: Edit `.claude-plugin/marketplace.json`, increment patch version (e.g., `1.0.8` → `1.0.9`).

---

## Step 3 — Stage files selectively

```bash
git add plugins/unipus-devops-plugin/hooks/sessionstart/show-tip.sh
git add .claude-plugin/marketplace.json

# Verify
git diff --staged --stat
```

**Why not `git add -A`:** Could accidentally stage lock files, `.env`, or other unrelated files.

---

## Step 4 — Commit message

```bash
git commit -m "$(cat <<'EOF'
fix(devops-hooks): 修复 Windows 上 show-tip.sh 的 GBK 编码错误

- 添加 PYTHONIOENCODING=utf-8 环境变量，解决 Windows 默认 GBK 编码
  导致的 'gbk' codec can't encode character 错误
- 影响范围：所有在 Windows 上使用 SessionStart hook 的用户

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

**Type:** `fix` — bug fix in hook script ✓  
**Scope:** `devops-hooks` — matches the plugin path ✓

---

## Step 5 — Push

```bash
git push origin master
```

If push fails due to proxy/network reset, retry once. Do not force push.
