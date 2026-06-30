---
name: jenkins-build
version: 1.1.0
description: Use when user wants to immediately execute a Jenkins CI build — 触发构建、跑 Jenkins、build [job]、帮我打包（CI场景）、构建 [项目]、ci 跑一下。Applies even when "Jenkins" is not mentioned — any intent to trigger CI and wait for result. Not for Jenkinsfile authoring, diagnosing past failures, API token management, or GitHub Actions.
---

# Jenkins 构建触发工具

## 功能概述

远程触发 Jenkins 构建并实时跟踪构建结果，支持：
- **默认模式**：触发 jenkins-config.yaml 中配置的第一个 job
- **指定 job**：通过名称触发特定 job
- **带参数构建**：支持传入 KEY=VALUE 格式的构建参数
- 自动等待构建启动并轮询最终结果

## 使用方法

### 前置条件

1. 已有 Jenkins 账号和访问权限
2. 已创建配置文件 `jenkins-config.yaml`（参考 `jenkins_build/jenkins-config.yaml.example`）

### 配置文件

配置文件名为 `jenkins-config.yaml`，查找优先级：

| 优先级 | 路径 | 适用场景 |
|---|---|---|
| 1（最高） | `<当前工作目录>/jenkins-config.yaml` | 项目级，建议加入 `.gitignore` |
| 2 | `~/.claude/jenkins-config.yaml` | 用户级全局默认 |

配置模板及示例详见：`jenkins_build/jenkins-config.yaml.example`

### 执行构建

> 🔴 **CHECKPOINT — 触发前确认**
> 触发构建是不可逆操作，请确认以下三项后再执行：
> 1. `jenkins-config.yaml` 已正确配置（url / api_token / job path）
> 2. 目标 job 名称与环境（开发/测试/生产）与预期一致
> 3. 该 job 当前无正在运行的构建（避免并发冲突）

优先使用 `scripts/run.sh` 脚本运行（自动管理 venv、安装依赖）：

```bash
# 触发默认 job（jenkins-config.yaml 第一个）
.claude/skills/jenkins-build/scripts/run.sh

# 触发指定 job
.claude/skills/jenkins-build/scripts/run.sh zk-api

# 触发带参数的 job
.claude/skills/jenkins-build/scripts/run.sh zk-api BRANCH=main
```

也可以直接调用 Python 脚本（需手动安装依赖 `pip install requests pyyaml`）：

```bash
python3 jenkins_build/main.py [job_name] [KEY=VALUE ...]
```

> 构建触发后自动轮询状态，默认每 10 秒查询一次；SUCCESS 时退出码为 0，其他结果退出码为 1。

## 代码位置

- 主程序入口：`jenkins_build/main.py`
- Jenkins 构建封装：`jenkins_build/jenkins_build.py`
- 配置示例：`jenkins_build/jenkins-config.yaml.example`
- venv 位置：`~/.claude/cache/jenkins-build/.venv`（固定，不随安装方式变化）

## 构建完成后通知

脚本执行完毕后，**必须**以如下格式输出构建摘要：

```
● 构建成功！       （SUCCESS 时）
● 构建失败！       （非 SUCCESS 时）

| 项目         | 值                                              |
|--------------|------------------------------------------------|
| Job          | <job_name>                                     |
| 构建号       | #<build_number>                                |
| 结果         | <build_result>                                 |
| 耗时         | <duration>s（约 X 分钟）                       |
| 构建地址     | <build_url>                                    |
| 配置来源     | <实际加载的 jenkins-config.yaml 路径> ✓        |
```

- 结果为 SUCCESS 时首行用 `●`，非 SUCCESS 时首行用 `●`（内容改为"构建失败！"）
- `build_url` 由 `jenkins_url` + `job_path` + `/` + `build_number` + `/` 拼接
- 耗时同时展示秒数和换算后的分钟数（不足 1 分钟只显示秒）

## 失败处理

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| `Connection refused` / 无法连接 Jenkins | 检查 `jenkins-config.yaml` 中 `url` 是否可访问（`curl <url>/api/json`） | 确认 VPN/网络，或联系 DevOps 确认 Jenkins 服务状态 |
| 401 Unauthorized | 检查 `api_token` 是否过期，在 Jenkins → 用户设置重新生成 | 回退到 `password` 字段临时使用 |
| 403 Forbidden | 确认账号对目标 job 有 Build 权限 | 联系 Jenkins 管理员授权 |
| 构建启动后无响应（超过 5 分钟未进入 RUNNING） | 检查 Jenkins executor 是否空闲，队列是否阻塞 | 手动在 Jenkins UI 取消排队，再次触发 |
| 构建结果 `FAILURE` | 打开构建日志（脚本输出构建 URL）排查失败原因 | 修复后重新触发，仍失败则上报给对应开发负责人 |
| 构建结果 `ABORTED` | 通常是手动取消或超时，确认是否需要重触发 | 检查 Jenkins job 的超时配置 |
| `job_name` 不存在 | 检查 `jenkins-config.yaml` 中 jobs 列表，确认拼写与路径一致 | 在 Jenkins UI 手动确认 job path |
| 未找到配置文件 | 按提示在 `~/.claude/jenkins-config.yaml` 创建配置 | 参考 `jenkins-config.yaml.example` |

## ⛔ 反例黑名单

| 禁止行为 | 原因 | 正确做法 |
|---|---|---|
| 将 `api_token` 或 `password` 明文写入代码或提交到 git | 凭证泄露风险 | 写入 `jenkins-config.yaml` 并加入 `.gitignore` |
| 未确认 job 名称就触发构建 | 可能误触发生产环境构建 | 先用 `jenkins-config.yaml` 中的 jobs 列表核对 |
| 同时并发触发同一个 job 多次 | 可能导致构建队列阻塞或资源竞争 | 等待当前构建完成后再触发 |
| 构建完成后不输出摘要表格 | 用户无法快速确认构建结果 | 无论 SUCCESS 还是 FAILURE 都必须输出摘要 |
| 使用 `password` 字段代替 `api_token` 作为长期方案 | 明文密码安全级别低 | 始终优先使用 Jenkins API Token |
| job `path` 填写错误或含未编码特殊字符 | 触发请求 404 / 参数丢失 | 与 Jenkins URL 路径严格一致，特殊字符需 URL 编码 |
| 跳过 `jenkins-config.yaml` 直接手动运行 `main.py` | 未经 venv 管理可能依赖缺失 | 始终通过 `scripts/run.sh` 执行，自动处理 venv 和依赖 |
