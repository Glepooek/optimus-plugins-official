---
name: 10-trigger
description: 正例——应触发 jenkins-build
max_turns: 3
runs: 1
allowed_tools:
  - Skill
---

构建一下测试环境，job 叫 staging-api-test，带参数 ENV=staging
