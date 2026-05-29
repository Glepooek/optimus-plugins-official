# Eval 1 — With Skill: New QA Automation Skill Added

## Step 1 — Inspect changes

From the provided git status:
- `modified: .claude-plugin/marketplace.json` (version already bumped to 1.1.0 in the diff)
- `untracked: plugins/unipus-qa-plugin/skills/unipus-qa-automation/SKILL.md` (new skill file)

## Step 2 — Version bump decision

**Decision: Minor bump (x.X.x) → 1.0.8 → 1.1.0**

Reasoning: A **new skill** (`unipus-qa-automation`) is being added under an existing plugin directory. Per the skill's version bump table:

> New plugin directory OR new skill added → **Minor** `x.X.x`

The diff already shows the version changed from `1.0.8` to `1.1.0` in `marketplace.json`, which is correct. No further edit needed.

## Step 3 — Selective staging

```bash
git add .claude-plugin/marketplace.json
git add plugins/unipus-qa-plugin/skills/unipus-qa-automation/SKILL.md

# Verify
git diff --staged --stat
```

Expected staged output:
```
 .claude-plugin/marketplace.json                                 | 5 +++++-
 plugins/unipus-qa-plugin/skills/unipus-qa-automation/SKILL.md | XX ++++++
 2 files changed, XX insertions(+), 1 deletion(-)
```

## Step 4 — Commit message

```bash
git commit -m "$(cat <<'EOF'
feat(qa-plugin): add unipus-qa-automation skill

- 新增 unipus-qa-plugin 下的 unipus-qa-automation skill
- 更新 marketplace.json 版本号 1.0.8 → 1.1.0（Minor 升级）

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

## Step 5 — Push

```bash
git push origin master
```
