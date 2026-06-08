---
name: unipus-infra-init-app
description: 触发词：初始化项目, init app, 新建服务, 创建应用, 项目脚手架, 服务声明
---

# unipus-infra-init-app

初始化 Git 仓库为平台标准服务，生成 service.yaml 与 Jenkinsfile。

**宣告**：正在执行 `unipus-infra-init-app` — 平台服务初始化。

---

## HARD-GATE：仓库合约校验

以下任一检查失败立即停止，不进入后续流程：

| 检查项 | 命令 | 通过条件 |
|--------|------|----------|
| Git 仓库 | `test -d .git` | .git/ 目录存在 |
| Git Remote | `git remote -v` | 有输出 |
| Remote 属于平台 | 解析 remote URL | 包含 git.unipus.cn |
| 无 Dockerfile | `test ! -f Dockerfile` | 文件不存在 |
| 无 k8s/ manifests/ chart/ | `ls` | 目录不存在 |
| service.yaml 冲突 | `test -f service.yaml` | 不存在；已存在则询问是否覆盖 |
| Jenkinsfile 冲突 | `test -f Jenkinsfile` | 不存在；已存在则检查是否为平台标准内容 |

---

## Workflow

1. **宣告**：输出宣告语
2. **读取规范**：读取 `references/service-yaml-template.yaml` 和 `references/init-checklist.md`
3. **HARD-GATE**：执行仓库合约校验（见上表），失败即停止
4. **收集信息**（逐一提问，每次只问一个）：
   - 服务名称（从 git 仓库名推断，确认）
   - 展示名称（中文，从服务名推断）
   - 团队（从 remote URL group 路径段推断）
   - 负责人（从 `git config user.name` 推断）
   - 语言（java/go/python/node，默认 java）
   - 语言版本（按语言给出默认值：java→17, go→1.22, python→3.11, node→20）
   - 框架（按语言推断：java→Spring Boot, go→Gin, python→FastAPI, node→Express）
   - 服务端口（默认 8080）
   - 健康检查路径（按框架对照 init-checklist.md 推断）
   - 是否需要 MySQL（y/n）
   - 是否需要 Redis（y/n）
   - 是否需要域名（y/n，是则询问子域名前缀）
   - 其他服务依赖（可选，回车跳过）
5. **展示确认**：打印所有收集到的信息，等待用户确认（y 继续，n 重新收集）
6. **生成 service.yaml**：按 `references/service-yaml-template.yaml` 填充所有字段
7. **生成 Jenkinsfile**：固定内容两行（见下方）
8. **确保分支存在**：检查 dev/test 分支，不存在则创建并推送
9. **切换 dev 分支**：`git checkout dev`，提交 service.yaml 和 Jenkinsfile，推送
10. **输出摘要**：列出创建的文件、分支状态、下一步操作提示

---

## Jenkinsfile 内容（固定不变）

```groovy
@Library('jenkins-shared-library@main') _
platformPipeline()
```

---

## Red Flags

| 现象 | 处理 |
|------|------|
| remote URL 不含 git.unipus.cn | 停止，提示用户在平台仓库中操作 |
| 已存在 Dockerfile | 停止，该仓库可能已完成初始化或使用自定义构建 |
| 已存在 k8s/ 等目录 | 停止，平台不支持自定义 manifest |
| Jenkinsfile 内容不是平台标准 | 警告并询问是否覆盖 |
| service.yaml 已存在 | 询问是否覆盖，否则停止 |
| git remote -v 无输出 | 停止，提示先设置 remote |

---

详细字段说明见 `references/service-yaml-template.yaml`，校验清单见 `references/init-checklist.md`，命名规则见 `references/naming-rules.md`。
