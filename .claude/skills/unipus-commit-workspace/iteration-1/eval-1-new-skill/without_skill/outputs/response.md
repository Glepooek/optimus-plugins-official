# Baseline Commit Plan (No Skill)

## 1. Version Bump Decision

The `marketplace.json` already shows the version bumped from `1.0.8` → `1.1.0` in the diff. Since a brand-new skill is being added (new plugin entry in the marketplace), this is a **minor** version bump — new feature added, no breaking changes. The diff already reflects this correctly, so no further change to the version is needed.

## 2. Git Add Commands

```bash
git add .claude-plugin/marketplace.json
git add plugins/unipus-qa-plugin/skills/unipus-qa-automation/SKILL.md
```

## 3. Commit Message

```
feat(qa-plugin): add unipus-qa-automation skill

- 新增 unipus-qa-plugin 下的 unipus-qa-automation skill
- 更新 marketplace.json，版本升级至 1.1.0
```

## 4. Push Command

```bash
git push origin master
```
