---
name: jenkins-build
description: 触发 Jenkins 构建并等待结果的自动化工具，支持指定 job 名称和构建参数
globs:
  - "jenkins_build/**"
disable-model-invocation: true
---

# Jenkins 构建触发工具

## 功能概述

远程触发 Jenkins 构建并实时跟踪构建结果，支持：
- **默认模式**：触发 config.yaml 中配置的第一个 job
- **指定 job**：通过名称触发特定 job
- **带参数构建**：支持传入 KEY=VALUE 格式的构建参数
- 自动等待构建启动并轮询最终结果

## 使用方法

### 前置条件

1. 已有 Jenkins 账号和访问权限
2. 已配置 `jenkins_build/config.yaml`（参考 `config.yaml.example`）

### 配置文件

在 `.claude/skills/jenkins-build/jenkins_build/config.yaml` 中配置：

```yaml
jenkins:
  url: "http://jenkins.example.com:8080"
  username: "your_username"
  api_token: "your_api_token"   # 优先使用，在 Jenkins → 用户设置 → API Token 中生成
  # password: "your_password"   # 无 api_token 时使用密码

jobs:
  lms-api-test:
    path: "view/mid/job/lms-api-test"
  # 添加更多job
  # 参数化构建示例（default_params 会在触发时自动传入，命令行参数可覆盖）：
  # uni-stu-pc:
  #   path: "job/k12-test-cloud/job/uni-stu-pc"
  #   default_params:
  #     BRANCH_OR_TAG: "master"
  #     Build_Type: "Release"
  #     VERSION_PREFIX: "1.2.1"
```

### 执行构建

优先使用 `scripts/run.sh` 脚本运行（自动检查配置、安装依赖）：

```bash
# 触发默认 job（config.yaml 第一个）
.claude/skills/jenkins-build/scripts/run.sh

# 触发指定 job
.claude/skills/jenkins-build/scripts/run.sh zk-api

# 触发带参数的 job
.claude/skills/jenkins-build/scripts/run.sh zk-api BRANCH=main
```

也可以直接调用 Python 脚本（需手动安装依赖 `pip3 install requests pyyaml`）：

```bash
python3 jenkins_build/main.py [job_name] [KEY=VALUE ...]
```

## 代码位置

- 主程序入口: `.claude/skills/jenkins-build/jenkins_build/main.py`
- Jenkins 构建封装: `.claude/skills/jenkins-build/jenkins_build/jenkins_build.py`
- 配置示例: `.claude/skills/jenkins-build/jenkins_build/config.yaml.example`

## 构建完成后：API 变动通知

`skill.run()` 返回 `(result, commits)`，其中 `commits` 是本次构建的 commit message 列表（从 Jenkins changeSet 提取）。

构建结果出来后，**必须**调用 `notify-api-change` skill，并将以下信息传入：
- `job_name`：job 名称
- `build_number`：构建号
- `build_result`：构建结果（SUCCESS / FAILURE 等）
- `jenkins_url` + `job_path`：用于拼接构建地址
- `commits`：本次 changeSet 的 commit message 列表

## 失败处理

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| `Connection refused` / 无法连接 Jenkins | 检查 `config.yaml` 中 `url` 是否可访问（`curl <url>/api/json`） | 确认 VPN/网络，或联系 DevOps 确认 Jenkins 服务状态 |
| 401 Unauthorized | 检查 `api_token` 是否过期，在 Jenkins → 用户设置重新生成 | 回退到 `password` 字段临时使用 |
| 403 Forbidden | 确认账号对目标 job 有 Build 权限 | 联系 Jenkins 管理员授权 |
| 构建启动后无响应（超过 5 分钟未进入 RUNNING） | 检查 Jenkins executor 是否空闲，队列是否阻塞 | 手动在 Jenkins UI 取消排队，再次触发 |
| 构建结果 `FAILURE` | 打开构建日志（脚本输出构建 URL）排查失败原因 | 修复后重新触发，仍失败则上报给对应开发负责人 |
| 构建结果 `ABORTED` | 通常是手动取消或超时，确认是否需要重触发 | 检查 Jenkins job 的超时配置 |
| `job_name` 不存在 | 检查 `config.yaml` 中 jobs 列表，确认拼写与路径一致 | 在 Jenkins UI 手动确认 job path |

## 注意事项

- `api_token` 字段优先于 `password`，建议在 Jenkins 用户设置中生成 API Token 使用
- job `path` 需与 Jenkins URL 中的路径一致，特殊字符需 URL 编码
- 构建触发后会自动轮询状态，默认每 10 秒查询一次
- 返回值：SUCCESS 时退出码为 0，其他结果退出码为 1
