---
name: negative-control-probe
description: 临时阴性对照 skill，用于验证 new-skill-eval-case 门禁会拦住缺 eval case 的新增 skill。验证完即删除，不要基于它开发任何功能。
metadata:
  version: "0.0.0"
---

# negative-control-probe

阴性对照用的空 skill。**本文件预期在同一个 PR 内被删除**，不会合入 master。

判据见 `docs/superpowers/specs/2026-09-13-pr-flow-and-free-ci-design.md` § 9 第 5 项。
