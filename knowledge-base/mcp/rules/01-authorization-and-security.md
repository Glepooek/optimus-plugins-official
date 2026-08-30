# 1. 授权与安全

MCP 的无状态设计、代理架构与本地进程执行能力，带来了一组区别于一般 Web 应用的特有攻击面。本篇提炼官方 Security Best Practices 中可用于合规判断的强制/推荐条款；攻击原理与完整场景描述见本领域 `reference/` 与官方文档，不在此重复。

## 1. Token 直通（Token Passthrough）禁令

Token passthrough 是指 MCP server 未校验 token 是否确实为自己签发，就直接接受 client 传来的 token 并原样转发给下游 API 的反模式。它会绕过下游的限流/审计等安全控制，并造成"混淆代理人"（confused deputy）问题。

- **必须**：MCP server 不得接受任何未明确为该 server 签发的 token
- **必须**：MCP server 校验 token 的 audience（受众）声明，拒绝为其他服务签发的 token

## 2. 服务端请求伪造（SSRF）防护

恶意 server 可能在 OAuth 元数据发现过程中返回指向内部资源（如云元数据端点 `169.254.169.254`、内网 IP、localhost 服务）的 URL，诱导 client 发起非预期请求。

- **必须**：部署为服务的 MCP client 必须考虑 SSRF 风险并针对性实现缓解措施；具体采用哪些防护取决于网络环境
- **应该**：生产环境下所有 OAuth 相关 URL 强制要求 HTTPS，拒绝 `http://`（本地开发的 loopback 地址除外）
- **应该**：阻断对私有/保留 IP 段的请求（私有 IPv4 段、loopback、link-local 含云元数据端点、私有 IPv6 段）
- **应该**：对重定向目标应用与初始请求相同的 URL 校验，不无条件跟随重定向到内部资源
- **应该**：服务端部署的 client 考虑使用出口代理（egress proxy）强制执行网络策略，阻断对内部目标的访问
- 不建议手工实现 IP 校验逻辑——攻击者常利用编码技巧（八进制、十六进制、IPv4 映射 IPv6）绕过自制解析器；上述 SSRF 缓解措施同样适用于支持 Client ID Metadata Documents 的授权服务器（它们也会按输入 URL 发起请求）

## 3. 状态句柄劫持（State Handle Hijacking）防护

MCP 是无状态协议，没有协议层 session；server 需要跨请求维持状态时，会生成一个显式句柄（如购物车 ID）作为普通工具参数传回。若攻击者获取或猜中该句柄，且 server 未校验其归属，即可冒用他人状态。

- **必须**：实现了授权的 MCP server 必须校验所有入站请求
- **禁止**：不得把"持有某个状态句柄"当作身份认证的等价物
- **应该**：使用安全的非确定性随机数生成器生成句柄，避免可预测或连续的标识符；为句柄设置过期时间
- **应该**：将句柄在服务端与已认证用户绑定（如以 `<user_id>:<handle>` 为键存储状态，`user_id` 取自已验证的 token 而非客户端提供的值），拒绝其他主体提交的同一句柄

## 4. 本地 Server 一键配置的用户同意要求

本地 MCP server 是下载后在用户机器上执行的二进制/脚本，若缺乏适当的沙箱与同意机制，恶意的启动命令可执行任意代码、窃取数据或造成不可恢复的数据丢失。

- **必须**：支持一键式本地 server 配置的 MCP client，必须在执行命令前实现恰当的同意机制
- **必须**：配置前的同意对话框必须完整（不截断）展示将要执行的确切命令（含全部参数）、明确标注这是可能在用户系统上执行代码的危险操作、要求用户明确批准、并允许用户取消
- **应该**：对危险命令模式（含 `sudo`、`rm -rf`、网络操作、越出预期目录的文件系统访问）高亮提示；对访问敏感位置（home 目录、SSH key、系统目录）的命令显示警告；提示用户 MCP server 与 client 拥有相同权限；将 server 进程运行在沙箱环境中并限制其默认权限
- **应该**：意图被本地运行的 MCP server 作者，应实现防止未授权进程滥用的措施——使用 stdio 传输将访问范围限制在当前 client；若使用 HTTP 传输，应要求鉴权 token 或使用带访问限制的 IPC 机制（如 Unix domain socket）

## 5. OAuth 授权 URL 校验

恶意 server 提供的授权 URL 若未经严格校验就交给浏览器打开或用 shell 命令处理，可导致 XSS（`javascript:` URL 注入）或命令注入 RCE。

- **必须**：MCP client 只允许 `http://` 与 `https://` scheme 作为授权 URL；`http://` 仅在本地开发的 loopback 地址（`localhost`/`127.0.0.1`/`::1`）下可接受，生产环境的授权服务器必须使用 `https://`
- **必须**：拒绝 `javascript:`、`data:`、`file:`、`vbscript:` 等危险 scheme
- **应该**：采用允许列表（allowlist）而非阻止列表（blocklist）方式做 scheme 校验
- **必须**：打开 URL 时避免使用 shell 执行——不得用 `cmd.exe`、`sh`、PowerShell 等 shell 命令打开 URL，应使用平台原生的非 shell URL 打开机制
- **必须**：对从 MCP server 收到的所有 URL 进行清理和校验，拒绝含有可能被 shell 解释的特殊字符的 URL

## 6. Scope 最小化

发布过宽的 scope（`files:*`、`admin:*` 等通配符/大而全 scope）会扩大 token 泄露后的影响半径，提高撤销成本，并使审计线索模糊。

- **禁止**：发布通配符或大而全的 scope（`*`、`all`、`full-access`）
- **禁止**：把不相关的权限打包在一起以规避未来的多次确认提示
- **应该**：实现渐进式、最小权限的 scope 模型——初始只授予低风险的发现/只读操作，需要执行高权限操作时再通过 `WWW-Authenticate` 的 `scope` 挑战逐步升级权限
- **应该**：Server 侧发出精确的 scope 挑战，避免每次都返回完整的 scope 目录
- **应该**：Client 侧从基线 scope 开始请求，逐次升级时计算"已授予 scope ∪ 新挑战 scope"的并集，避免丢失此前已获得的权限

## 7. 混淆代理人（Confused Deputy）防护——MCP 代理服务器场景

当 MCP 代理服务器以静态 client ID 对接第三方授权服务器，同时允许 MCP client 动态注册各自的 client ID 时，攻击者可利用第三方授权服务器的同意 cookie 跳过用户同意screen，窃取授权码。

- **必须**：MCP 代理服务器实现按客户端的同意存储，在发起第三方授权流程**之前**检查该注册表
- **必须**：MCP 层的同意页面清晰标注请求方 client 名称、所请求的具体第三方 API scope、注册的 `redirect_uri`，并实现 CSRF 防护与防点击劫持（`frame-ancestors` CSP 或 `X-Frame-Options: DENY`）
- **必须**：若用同意 cookie 跟踪决策，cookie 须使用 `__Host-` 前缀、设置 `Secure`/`HttpOnly`/`SameSite=Lax`、经加密签名或使用服务端 session，并绑定到具体的 `client_id`
- **必须**：精确字符串匹配校验 `redirect_uri` 与注册值完全一致，不使用模式匹配或通配符；若 `redirect_uri` 变化而未重新注册，拒绝请求
- **必须**：OAuth `state` 参数为每次授权请求生成密码学安全的随机值，仅在用户明确批准同意后才在服务端存储；在跳转到第三方身份提供商**之前**立即设置 `state` 追踪 cookie/session；在回调端点严格校验 `state` 参数与存储值完全匹配；`state` 值单次有效（校验后即删除）且设置较短过期时间

## 权威参考

- MCP 官方文档 [Security Best Practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)
- MCP 官方规范 [MCP Authorization](https://modelcontextprotocol.io/specification/latest/basic/authorization)
