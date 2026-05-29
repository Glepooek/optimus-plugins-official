# Hypothetical Commit Plan — Without Skill

## 1. Version Bump Decision

**Decision: No version bump (no changes to marketplace.json)**

Reasoning: Only two existing files are modified — `SKILL.md` and `evals/evals.json`. No new plugin or skill was added; this is purely an improvement to existing content. The public-facing plugin interface hasn't changed, so bumping a version number isn't necessary.

## 2. Git Add Commands

```bash
git add plugins/unipus-frontend-plugin/skills/wpf-xaml-performance/SKILL.md
git add plugins/unipus-frontend-plugin/skills/wpf-xaml-performance/evals/evals.json
```

## 3. Commit Message

```
docs(wpf-xaml-performance): add three new performance checkpoints and evals

Added Checkpoint 9 (event handler memory leaks), Checkpoint 10 (data binding
performance), and Checkpoint 11 (UI thread / Dispatcher optimization) to
SKILL.md.

Also added three corresponding test cases to evals/evals.json covering
WeakEventManager, OneTime binding, and async/await patterns.
```

## 4. Push Command

```bash
git push origin master
```
