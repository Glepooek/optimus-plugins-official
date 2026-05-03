# 仓库合约校验清单

## 1. 合约校验项

每项校验均为 HARD-GATE，失败立即停止并给出明确错误说明。

| 序号 | 检查项 | 检查方式 | 通过条件 | 失败处理 |
|------|--------|----------|----------|----------|
| 1 | Git 仓库存在 | `test -d .git` | 目录存在 | 提示：当前目录不是 Git 仓库，请切换到正确目录 |
| 2 | 存在 Git Remote | `git remote -v` | 有输出行 | 提示：请先执行 `git remote add origin <url>` |
| 3 | Remote 属于平台 | 解析 remote URL | URL 包含 `git.unipus.cn` | 提示：仓库需托管在 git.unipus.cn 平台 |
| 4 | 无 Dockerfile | `test ! -f Dockerfile` | 文件不存在 | 停止：已存在 Dockerfile，该仓库可能已完成初始化或使用自定义构建 |
| 5 | 无 k8s/ 目录 | `test ! -d k8s` | 目录不存在 | 停止：平台不支持自定义 Kubernetes manifest |
| 6 | 无 manifests/ 目录 | `test ! -d manifests` | 目录不存在 | 停止：同上 |
| 7 | 无 chart/ 目录 | `test ! -d chart` | 目录不存在 | 停止：同上 |
| 8 | service.yaml 冲突 | `test ! -f service.yaml` | 不存在，或用户确认覆盖 | 询问：service.yaml 已存在，是否覆盖？(y/N) |
| 9 | Jenkinsfile 冲突 | 检查文件内容 | 不存在，或内容为平台标准 2 行，或用户确认覆盖 | 若内容非标准则警告并询问是否覆盖 |

## 2. 平台标准 Jenkinsfile 内容

以下两行为唯一合法内容（逐字符匹配）：

```
@Library('jenkins-shared-library@main') _
platformPipeline()
```

## 3. 健康检查路径对照表

| 语言 | 框架 | livenessPath | readinessPath |
|------|------|--------------|----------------|
| java | Spring Boot | `/actuator/health/liveness` | `/actuator/health/readiness` |
| java | Spring Boot (旧版) | `/actuator/health` | `/actuator/health` |
| java | Quarkus | `/q/health/live` | `/q/health/ready` |
| go | Gin | `/health` | `/ready` |
| go | Echo | `/health` | `/ready` |
| go | Fiber | `/health` | `/ready` |
| python | FastAPI | `/health` | `/ready` |
| python | Flask | `/health` | `/health` |
| python | Django | `/health/` | `/health/` |
| node | Express | `/health` | `/ready` |
| node | NestJS | `/health` | `/health` |
| node | Koa | `/health` | `/health` |

## 4. 推断逻辑

### 服务名称推断
从 `git remote get-url origin` 提取最后一段路径（去掉 `.git`）。
例：`git@git.unipus.cn:backend/user-service.git` → 推断名称：`user-service`

### 团队推断
从 remote URL 提取 group 段。
例：`git@git.unipus.cn:backend/user-service.git` → 团队：`backend`

### 展示名称推断
将服务名用 `-` 分词后翻译为中文加上"服务"后缀。
例：`user-service` → 推断展示名：`用户服务`（供用户确认）
