# 自包含脚本示例

> 讲解性内容，无规范语气。支撑 `rules/04-script-usage.md`（自包含脚本）。给出各语言"内联依赖声明 + 一条命令运行"的完整示例——不依赖外部 manifest 或安装步骤。

## 为什么自包含

agent 运行脚本时不应被迫先装依赖、读 manifest、找 node_modules。脚本自带依赖声明，一条命令即可跑，降低 agent 的认知负担和失败点。

## Python（PEP 723）

在脚本头部用 `# ///` 标记块声明依赖，`uv run` 创建隔离环境自动安装：

```python
# /// script
# dependencies = [
#   "beautifulsoup4",
# ]
# ///

from bs4 import BeautifulSoup

html = '<html><body><h1>Welcome</h1><p class="info">This is a test.</p></body></html>'
print(BeautifulSoup(html, "html.parser").select_one("p.info").get_text())
```

运行：

```bash
uv run scripts/extract.py
```

进阶：
- 锁版本区间：`"beautifulsoup4>=4.12,<5"`（PEP 508 specifier）
- 约束 Python 版本：`requires-python = ">=3.11"`
- 完全可复现：`uv lock --script` 生成 lockfile

## Deno

`npm:` / `jsr:` import specifier 让每个脚本默认自包含：

```typescript
#!/usr/bin/env -S deno run

import * as cheerio from "npm:cheerio@1.0.0";

const html = `<html><body><h1>Welcome</h1><p class="info">This is a test.</p></body></html>`;
const $ = cheerio.load(html);
console.log($("p.info").text());
```

运行：

```bash
deno run scripts/extract.ts
```

- `npm:` 用 npm 包，`jsr:` 用 Deno 原生包
- 版本 specifier 遵循 semver：`@1.0.0`（精确）、`@^1.0.0`（兼容）
- 依赖全局缓存；`--reload` 强制重取
- 原生扩展（node-gyp）包可能不工作——预编译二进制包最稳

## Bun

找不到 `node_modules` 时 Bun 自动装缺的包，版本直接锁在 import 路径：

```typescript
#!/usr/bin/env bun

import * as cheerio from "cheerio@1.0.0";

const html = `<html><body><h1>Welcome</h1><p class="info">This is a test.</p></body></html>`;
const $ = cheerio.load(html);
console.log($("p.info").text());
```

运行：

```bash
bun run scripts/extract.ts
```

- 无需 `package.json` / `node_modules`；TypeScript 原生支持
- 包全局缓存，首跑下载、后续近瞬时
- 若目录树某处存在 `node_modules`，自动安装被禁用，回退标准 Node 解析

## Ruby

Bundler 随 Ruby 2.6+ 自带，用 `bundler/inline` 在脚本内声明 gem：

```ruby
require 'bundler/inline'

gemfile do
  source 'https://rubygems.org'
  gem 'nokogiri'
end

html = '<html><body><h1>Welcome</h1><p class="info">This is a test.</p></body></html>'
doc = Nokogiri::HTML(html)
puts doc.at_css('p.info').text
```

运行：

```bash
ruby scripts/extract.rb
```

- 显式锁版本（`gem 'nokogiri', '~> 1.16'`）——无 lockfile
- 工作目录存在的 `Gemfile` 或 `BUNDLE_GEMFILE` 环境变量会干扰——注意隔离

## 语言选择建议

| 场景 | 首选 | 备选 |
|---|---|---|
| 通用逻辑、生态最全 | Python（PEP 723 + uv） | — |
| 单文件、无构建、TypeScript | Deno / Bun | — |
| 团队既有 Ruby 环境 | Ruby（bundler/inline） | — |
| 只调现成工具 | 用 one-off 命令（`uvx`/`npx`/`go run`） | 不写脚本 |

选择时考虑 **agent 环境已有什么**——SKILL.md 的 `compatibility` 声明前置条件，脚本用 `uv run` / `deno run` 等自包含方式降低依赖。

## 权威参考

- [在 skill 中使用脚本 — 完整版](https://agentskills.io/skill-creation/using-scripts)
