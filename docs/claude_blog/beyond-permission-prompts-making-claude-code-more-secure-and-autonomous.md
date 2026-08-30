# 超越权限提示：让 Claude Code 更安全、更自主

Claude Code 让 Claude 能够在你身边编写、测试和调试代码，但这也带来了提示注入攻击的风险。本文介绍两项基于原生沙箱构建的新能力，帮助 Claude Code 在减少权限确认打扰的同时保持安全。

> **来源：** [Claude Blog - Beyond permission prompts: Making Claude Code more secure and autonomous](https://claude.com/blog/beyond-permission-prompts-making-claude-code-more-secure-and-autonomous)
> **发布日期：** 2025 年 10 月 8 日
> **分类：** Claude Code | 产品：Claude Code | 阅读时长：5 分钟

---

Claude Code 让 Claude 能够在你身边编写、测试和调试代码，但这也带来了风险——提示注入攻击可能诱导 Claude 执行非预期的操作，例如删除你并不想删除的文件。

为应对这一风险，Anthropic 推出了两项基于**原生沙箱（native sandboxing）**构建的新能力。沙箱的核心思路是为 Claude 的行动设定预先定义好的边界，而不是单纯依赖逐次提示的人工审批。

## 一、当前的权限模型

Claude Code 默认以只读模式运行，在执行编辑或命令前会请求审批，仅对少数安全操作（如通过静态分析自动放行 `echo`、`cat` 等命令）设有例外。这一模型的副作用是"审批疲劳"——频繁的确认弹窗会让用户不再仔细审查自己批准的到底是什么。

## 二、沙箱方案

沙箱的做法是创建"预先定义的边界，让 Claude 在其中更自由地工作"。这套系统依赖两大支柱：

1. **文件系统隔离**：将 Claude 限制在特定目录内，阻止其修改敏感的系统文件
2. **网络隔离**：将出站连接限制在已批准的服务器范围内，防止数据泄露或恶意软件下载

两者缺一不可：没有网络隔离，被攻陷的智能体可能窃取 SSH key 等敏感文件；没有文件系统隔离，则存在沙箱"逃逸"的风险。

## 三、能力一：沙箱化的 Bash 工具

Anthropic 开源了一个新的沙箱运行时（研究预览版），让用户可以为任意智能体或 MCP server 定义允许访问的目录与网络主机。在 Claude Code 中，该运行时用于沙箱化 Bash 工具，使命令执行时的权限确认大幅减少，而越界尝试会立即触发通知。

该运行时基于操作系统级原语构建——Linux 上使用 [bubblewrap](https://github.com/containers/bubblewrap)，macOS 上使用 Seatbelt——不仅约束直接执行的命令，也约束其派生的子进程。网络访问通过 Unix domain socket 转发给一个外部代理，由代理执行域名规则校验，并可在遇到新域名时请求批准；该代理本身也可自定义，以实现更严格的限制。

启用方式：运行 `claude --sandbox`。

## 四、能力二：Claude Code on the Web

该能力让会话运行在一个隔离的云端沙箱中，敏感凭据（如 git 凭据或签名密钥）**永远不会进入沙箱环境**。一个自定义代理服务负责处理 git 操作——沙箱内的 git 客户端通过一个范围受限的凭据完成认证，代理在把请求转发给 GitHub 之前校验并附加正确的认证信息，同时把可执行的操作（如允许推送的目标分支）限制在预先配置的范围内。

## 五、开始使用

- 运行 `claude --sandbox`，并参阅[沙箱配置文档](https://docs.claude.com/en/docs/claude-code/sandboxing)
- 访问 [claude.com/code](http://claude.ai/code) 使用 Claude Code on the Web
- 查看已开源的沙箱代码，用于构建自定义智能体

---

## 致谢

本文由 Anthropic 团队撰写。
