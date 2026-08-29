# 知识库分领域版本化与结构优化 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把知识库从「一个全局版本号 + 一份根 CHANGELOG」改为「9 个领域各自独立版本号 + 各自 CHANGELOG」，同时完成领域改名、README 改名与 235 处图解回填。

**Architecture:** 四组改动按 A→B→D→C 顺序执行，每组独立提交、独立验证。A 组改领域标识符（`git mv` + 39 条 id），B 组改领域元数据文件名（含校验器白名单，走 TDD），D 组回填图片（一次性脚本 + 上游 1.3.0），C 组重构版本治理（拆 CHANGELOG + 新增一致性校验 + 改 skill）。顺序不可调换：B 改文件名、D 改正文，两者都产生须写入 CHANGELOG 的变更，故 C 必须最后。

**Tech Stack:** Python 3（`unittest`，无 pytest）、PowerShell 7（网络访问）、Git Bash（POSIX 脚本）、Git

**Spec:** `docs/superpowers/specs/2026-08-29-knowledge-base-per-domain-versioning-design.md`

## Global Constraints

- **提交一律走 `commit-cc-plugin` skill**，禁止手动 git 工作流（仓库 `AGENTS.md` 强制要求）。计划中的 `git commit` 步骤均表示"调用该 skill 完成提交"
- **不升级 marketplace 版本**：全部改动落在 `knowledge-base/` 与 `.claude/` 下，`.claude-plugin/marketplace.json` 与各 `.codex-plugin/plugin.json` 不动
- **本机无 `pytest`**，单元测试只能用 `python -m unittest`
- **网络访问只有 PowerShell 可达**：`raw.githubusercontent.com` 在本机对 curl 与 WebFetch 均超时，`Invoke-WebRequest` 可达但**首次请求常超时，须重试**
- **编辑 Markdown 禁止无关格式化**：不增删空行、不调缩进、不做表格对齐（`.claude/rules/skill-conventions.md` 铁律）
- **历史记录类文本不改写**：`knowledge-base/CHANGELOG.md`（C 组前）、`docs/`、`.remember/` 下的历史文本记录当时事实，A/B 组不同步改其中的旧路径名
- **领域标识符**：`algorithms` → `data-structures-algorithms`；中文展示名「数据结构与算法」
- **版本分叉点 7.2.0**：9 领域均以此为起点。本次落点 `data-structures-algorithms` = **8.0.0**，其余 8 个 = **7.2.1**
- **skill 版本**：`knowledge-base-maintain` 1.8.0 → **1.9.0**；`commit-cc-plugin` 3.4.2 → **3.4.3**

## 基线（实施前实测，每组完成后须回到此基线或更好）

| 检查 | 命令 | 基线 |
|---|---|---|
| 索引一致性 | `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"` | `OK: 共检查 483 条记录，未发现问题` |
| 章节引用 | `python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict` | `OK: 检查 140 个消费者文件，章节号引用全部有效` |
| 单元测试 | `python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"` | `Ran 133 tests` / `OK` |

## File Structure

| 文件 | 责任 | 触及组 |
|---|---|---|
| `knowledge-base/data-structures-algorithms/` | 改名后的领域目录（原 `algorithms/`） | A |
| `knowledge-base/*/README.md` | 领域元数据（原 `00-README.md`），C 组起顶部承载该领域版本号 | B, C |
| `knowledge-base/*/CHANGELOG.md` | 新建，每领域独立变更历史 | C |
| `knowledge-base/CHANGELOG.md` | 删除 | C |
| `knowledge-base/README.md` | 根说明；删除顶部版本行，改写版本治理段 | A, C |
| `knowledge-base/catalog.json` | 领域目录册；`domain`/`title` 改名 | A |
| `.../scripts/check_index.py` | 校验器：白名单改 `README.md`，新增版本一致性检查 | B, C |
| `.../scripts/test_check_index.py` | 校验器测试 | B, C |
| `.../scripts/check_refs.py` | 章节引用校验器（仅注释更新） | B |
| `.../scripts/test_check_refs.py` | 夹具文件名更新 | B |
| `.claude/skills/knowledge-base-maintain/SKILL.md` | Step 2/4/6 与失败处理表 | B, C |
| `.claude/skills/commit-cc-plugin/SKILL.md` | 一处 Markdown 链接目标 | B |
| `<repo>/tmp-backfill-figures.ps1` | **一次性**图片回填脚本，跑完删除，不提交 | D |

---

## A 组：algorithms 领域彻底改名

### Task 1: 领域目录与 39 条 id 前缀改名

**Files:**
- Move: `knowledge-base/algorithms/` → `knowledge-base/data-structures-algorithms/`
- Modify: `knowledge-base/data-structures-algorithms/index.jsonl`（39 行的 `id` 字段）
- Modify: `knowledge-base/catalog.json:94`（`domain` + `title`）
- Modify: `knowledge-base/README.md:5,31,147`
- Modify: `knowledge-base/data-structures-algorithms/00-README.md`（标题与领域名措辞）

**Interfaces:**
- Consumes: 无（首个任务）
- Produces: 领域标识符 `data-structures-algorithms`，id 前缀 `data-structures-algorithms.<两位编号或 ref>.<slug>`。后续 B/C/D 组全部用新路径 `knowledge-base/data-structures-algorithms/`

- [ ] **Step 1: 记录基线，确认三项检查全绿**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
```

Expected: `483 条` / `140 个消费者文件` / `Ran 133 tests ... OK`

- [ ] **Step 2: 用 git mv 移动目录**

```bash
git mv knowledge-base/algorithms knowledge-base/data-structures-algorithms
git status --short
```

Expected: 输出全部为 `R  knowledge-base/algorithms/... -> knowledge-base/data-structures-algorithms/...`（`R` = rename，证明历史可追溯）。若出现 `D` + `??` 组合说明 `git mv` 未生效，先 `git reset` 再重试。

- [ ] **Step 3: 确认此时校验器报错（证明 id 前缀校验确实在起作用）**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
```

Expected: **FAIL**，39 条形如 `[data-structures-algorithms] [algorithms.01.complexity-declaration] id 前缀与领域不一致` 的报错，外加 `catalog.json` 双向不一致报错。这一步是有意的失败——它证明 Step 4 的改动不是可选的。

- [ ] **Step 4: 批量替换 39 条 id 前缀**

```bash
python - <<'PY'
from pathlib import Path
p = Path("knowledge-base/data-structures-algorithms/index.jsonl")
text = p.read_text(encoding="utf-8")
before = text.count('"id": "algorithms.')
text = text.replace('"id": "algorithms.', '"id": "data-structures-algorithms.')
p.write_text(text, encoding="utf-8")
print(f"替换 {before} 处；残留 {text.count(chr(34)+'id'+chr(34)+': '+chr(34)+'algorithms.')} 处")
PY
```

Expected: `替换 39 处；残留 0 处`

只替换 `"id": "algorithms.` 这个完整前缀，不做宽泛的 `algorithms` → 新名替换——`source` 字段里有 `hello-algo.com/chapter_introduction/algorithms_are_everywhere/` 这类 URL，宽泛替换会破坏它们。

- [ ] **Step 5: 改 catalog.json 的 domain 与 title**

`knowledge-base/catalog.json` 中该条记录改两个字段：

```json
      "domain": "data-structures-algorithms",
      "title": "数据结构与算法",
```

（原为 `"domain": "algorithms"` / `"title": "算法与数据结构选型判据"`；`categories`/`owner`/`status`/`consumers`/`reviewed_at`/`notes` 全部不动）

- [ ] **Step 6: 改根 README.md 三处**

第 5 行领域列表，`` `design-patterns`、`algorithms` `` → `` `design-patterns`、`data-structures-algorithms` ``

第 31 行领域职责边界末句：

```
`algorithms` 负责算法与数据结构的选型判据与复杂度判断
```
改为
```
`data-structures-algorithms` 负责数据结构与算法的选型判据与复杂度判断
```

第 147 行许可证隔离条目开头：

```
- **外部作品的许可证隔离**：`algorithms/reference/` 提取自《Hello 算法》
```
改为
```
- **外部作品的许可证隔离**：`data-structures-algorithms/reference/` 提取自《Hello 算法》
```

- [ ] **Step 7: 改领域 00-README.md 的标题与措辞**

第 1 行：`# 算法与数据结构规范` → `# 数据结构与算法规范`

第 3 行（引言）：`> 面向团队的算法与数据结构选择判据。` → `> 面向团队的数据结构与算法选择判据。`

第 9 行（文档目的）：`本规范给出算法与数据结构决策的**判断依据**` → `本规范给出数据结构与算法决策的**判断依据**`

**只改这三处领域名措辞。** 正文其他位置的"算法"、"数据结构"是普通名词（如"它不是算法教程"、"数据结构选型"），不是领域名，不动。

- [ ] **Step 8: 确认无残留旧标识符**

```bash
grep -rn '"id": "algorithms\.' knowledge-base/*/index.jsonl; echo "id 残留检查完成（应无输出）"
grep -rn 'algorithms' knowledge-base/catalog.json; echo "catalog 检查完成（应无输出）"
grep -rn '`algorithms`\|algorithms/reference\|algorithms/rules' knowledge-base/README.md; echo "根 README 检查完成（应无输出）"
```

Expected: 三处均无匹配行输出。

`knowledge-base/CHANGELOG.md` 与 `docs/` 下的 `algorithms` 字样**保持不动**（历史事实），不要因为这一步的 grep 顺手改它们。

- [ ] **Step 9: 跑三项检查回到基线**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
```

Expected: `483 条` / `140 个消费者文件` / `Ran 133 tests ... OK`——与 Step 1 完全一致。条目数不变是正确的：改名不增删条目。

- [ ] **Step 10: 确认 git 历史可追溯**

```bash
git log --follow --oneline -- knowledge-base/data-structures-algorithms/rules/01-complexity.md | head -3
```

Expected: 能看到 `a974b5d`（algorithms 补入 rules 侧那次提交），证明 `git mv` 保留了历史。

- [ ] **Step 11: 提交**

调用 `commit-cc-plugin` skill 提交，message 要点：

```
refactor(knowledge-base)!: algorithms 领域改名为 data-structures-algorithms

- 目录 git mv，39 条索引 id 前缀同步改名，git 历史可追溯
- catalog.json domain/title、根 README 三处、领域 README 三处措辞同步
- 破坏性变更：id 前缀变更；该领域 consumers 为空、source 全为外部 URL，无消费者受影响
- CHANGELOG 与 docs/ 下的历史记录按约定不改写
```

不升级 marketplace 版本（改动在 `knowledge-base/` 下）。领域版本号在 C 组统一处理，本组不动。

---

## B 组：领域 00-README.md 改名为 README.md

### Task 2: 校验器白名单改名（TDD）

**Files:**
- Modify: `.claude/skills/knowledge-base-maintain/scripts/test_check_index.py:413`
- Modify: `.claude/skills/knowledge-base-maintain/scripts/check_index.py:39`

**Interfaces:**
- Consumes: Task 1 的领域标识符 `data-structures-algorithms`
- Produces: `DOMAIN_META_FILES = {"README.md"}` —— Task 3 的目录改名依赖此常量已改，否则 9 个领域 README 会被报为孤儿文件

- [ ] **Step 1: 改测试夹具用 README.md（先写失败的测试）**

`test_check_index.py` 第 409-414 行，把夹具文件名改掉：

```python
class TestCheckOrphanFiles(unittest.TestCase):
    def test_readme_is_not_orphan(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "README.md").write_text("# 领域说明\n", encoding="utf-8")
            self.assertEqual(check_orphan_files(domain_dir, []), [])
```

只改 `"00-README.md"` → `"README.md"` 这一个字符串。方法名 `test_readme_is_not_orphan` 已是通用命名，不用改。

- [ ] **Step 2: 跑该测试，确认失败**

```bash
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_check_index.py" -k readme_is_not_orphan -v
```

Expected: **FAIL** — `AssertionError: ['孤儿文件未被索引引用：README.md'] != []`

这个失败证明白名单确实在起作用。若它意外通过，说明白名单不是在这里生效的，停下来重读 `check_orphan_files` 再继续。

- [ ] **Step 3: 改 check_index.py 的白名单**

第 38-39 行：

```python
# 领域元数据文件，不参与孤儿文件判定（不属于 rules/reference 内容）
DOMAIN_META_FILES = {"README.md"}
```

原为 `{"00-README.md"}`。彻底替换，**不保留** `00-README.md` 作为兼容项——留兼容会让下次误建 `00-README.md` 时静默通过，而该白名单的作用正是划定"什么文件不算内容"。

- [ ] **Step 4: 跑该测试，确认通过**

```bash
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_check_index.py" -k readme_is_not_orphan -v
```

Expected: **PASS** — `Ran 1 test ... OK`

- [ ] **Step 5: 跑全量测试，确认无其他测试被打破**

```bash
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
```

Expected: `Ran 133 tests ... OK`

- [ ] **Step 6: 确认真实数据此时报错（9 个领域 README 尚未改名）**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
```

Expected: **FAIL**，9 条形如 `[csharp] 孤儿文件未被索引引用：00-README.md` 的报错。这是有意的中间状态，Task 3 改完文件名后恢复。

本 Task 不单独提交（会留下 red 状态），与 Task 3 合并为一次提交。

### Task 3: 9 个领域文件改名与全部引用同步

**Files:**
- Move: `knowledge-base/<domain>/00-README.md` → `README.md`（9 个领域）
- Modify: `.claude/skills/knowledge-base-maintain/scripts/check_refs.py:25,35`（仅注释）
- Modify: `.claude/skills/knowledge-base-maintain/scripts/test_check_refs.py`（约 20 处夹具字符串）
- Modify: `.claude/skills/knowledge-base-maintain/SKILL.md:37,77,193`
- Modify: `.claude/skills/commit-cc-plugin/SKILL.md:23`
- Modify: `knowledge-base/data-structures-algorithms/README.md`、`knowledge-base/architecture/README.md`（交叉引用与文件地图）

**Interfaces:**
- Consumes: Task 2 的 `DOMAIN_META_FILES = {"README.md"}`
- Produces: 9 个 `knowledge-base/<domain>/README.md`。C 组的版本号一致性校验以此路径为准

- [ ] **Step 1: 用 git mv 改名 9 个文件**

```bash
for d in knowledge-base/*/; do
  if [ -f "$d/00-README.md" ]; then git mv "$d/00-README.md" "$d/README.md"; fi
done
git status --short | grep README
```

Expected: 9 行 `R  knowledge-base/<domain>/00-README.md -> knowledge-base/<domain>/README.md`

- [ ] **Step 2: 确认真实数据校验恢复**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
```

Expected: `OK: 共检查 483 条记录，未发现问题` —— Task 2 造成的 9 个孤儿报错已消失。

- [ ] **Step 3: 改领域正文中的交叉引用与文件地图（2 个文件 4 处）**

`knowledge-base/data-structures-algorithms/README.md` 第 18 行，把 `knowledge-base/csharp/00-README.md` 改为 `knowledge-base/csharp/README.md`。

同文件第 74 行文件地图行，编号列由 `00` 改为破折号、文件名去掉前缀：

```markdown
| — | `README.md` | 总则、级别、许可证隔离、领域边界、索引 |
```

`knowledge-base/architecture/README.md` 第 18 行同样把 `csharp/00-README.md` 改为 `csharp/README.md`；第 63 行文件地图行改为：

```markdown
| — | `README.md` | 总则、级别、领域边界、执行、索引 |
```

编号列改破折号的理由：文件不再带编号前缀，保留 `00` 会让读者以为文件名仍是 `00-README.md`。

- [ ] **Step 4: grep 兜底，找出所有剩余的领域内引用**

```bash
grep -rn "00-README" knowledge-base/*/README.md
```

Expected: 无输出。若有，按 Step 3 同样方式处理。

- [ ] **Step 5: 改 check_refs.py 的两处注释**

第 25 行末尾的 `领域 00-README.md` 改为 `领域 README.md`。

第 35 行整行替换——原注释的理由（文件名含大写）改名后不再成立：

```python
# （领域元数据文件与根 README 同名，故领域提取与文件路径提取分开）
```

**只改注释文本，不动任何代码逻辑。** 该脚本靠 `CONSUMER_GLOBS` 的 glob 模式排除领域 README，不按文件名字符串判断。

- [ ] **Step 6: 改 test_check_refs.py 的夹具字符串**

```bash
python - <<'PY'
from pathlib import Path
p = Path(".claude/skills/knowledge-base-maintain/scripts/test_check_refs.py")
text = p.read_text(encoding="utf-8")
n = text.count("00-README.md")
p.write_text(text.replace("00-README.md", "README.md"), encoding="utf-8")
print(f"替换 {n} 处")
PY
```

Expected: `替换 20 处`（数量以实际输出为准，只要下一步复查为 0 即可）

这些夹具里的 `00-README.md` 只是"一个 knowledge-base 路径字样"，用于让 `DOMAIN_RE` 识别领域名，改成 `README.md` 语义等价。

- [ ] **Step 7: 跑测试与章节引用校验**

```bash
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict
```

Expected: `Ran 133 tests ... OK` / `OK: 检查 140 个消费者文件`

**特别注意 `test_check_refs.py` 里第 317-321 行那个测试**——它断言领域 README 不在被扫描的消费者文件列表里。改名后语义变为"领域 `README.md` 不被扫描"，这仍是正确期望（`CONSUMER_GLOBS` 只含 `rules/*.md` 与 `reference/*.md`）。若该测试失败，说明 glob 意外把领域 README 纳入扫描，需读 `CONSUMER_GLOBS` 排查。

- [ ] **Step 8: 改 knowledge-base-maintain SKILL.md 三处**

第 37 行（Step 2 新建领域流程）：`knowledge-base/<domain>/00-README.md` 与 `knowledge-base/csharp/00-README.md` 两处都去掉 `00-` 前缀。

第 77 行（Step 4 迁移五处清单）：`领域 `00-README.md` 的文件地图` → `领域 `README.md` 的文件地图`。

第 193 行（失败处理表）：`knowledge-base/csharp/00-README.md` → `knowledge-base/csharp/README.md`。

- [ ] **Step 9: 改 commit-cc-plugin SKILL.md 的链接目标**

第 23 行改为：

```markdown
- 完整规则入口：[`knowledge-base/git/README.md`](../../../knowledge-base/git/README.md)
```

反引号内的显示文本与括号内的链接目标**两处都要改**——只改一处会留下文本与链接不符。

- [ ] **Step 10: commit-cc-plugin 升版本并写 CHANGELOG**

`SKILL.md` frontmatter 第 5 行：`version: "3.4.2"` → `version: "3.4.3"`

`CHANGELOG.md` 在 `# Changelog` 之后追加：

```markdown
## [3.4.3] - 2026-08-29

### Changed
- Git 知识库入口链接随知识库领域元数据文件改名同步：`knowledge-base/git/00-README.md` → `README.md`
```

`knowledge-base-maintain` 的版本号与 CHANGELOG 在 C 组 Task 8 统一处理——该 skill 在 C 组还有 Step 6 重写等更大改动，避免升两次版本。

- [ ] **Step 11: 全库 grep 确认残留只在历史文本里**

```bash
grep -rn "00-README" --include="*.md" --include="*.py" --include="*.json" --include="*.jsonl" . 2>/dev/null | grep -v "^./docs/\|^./.remember/\|^./knowledge-base/CHANGELOG.md"
```

Expected: **无输出**。有输出说明漏改，逐条处理。

允许残留三处：`docs/`（历史决策记录）、`.remember/`（会话历史）、`knowledge-base/CHANGELOG.md`（C 组会删除它，此刻不动）。

- [ ] **Step 12: 跑三项检查回到基线，并确认零孤儿**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" --audit | grep -i "孤儿"
```

Expected: `483 条` / `140 个消费者文件` / `Ran 133 tests ... OK`；`--audit` 的孤儿相关输出显示为 0 或无该行。

- [ ] **Step 13: 提交**

调用 `commit-cc-plugin` skill，把 Task 2 与 Task 3 的改动作为一次提交，message 要点：

```
refactor(knowledge-base): 领域元数据文件 00-README.md 统一改名为 README.md

- 9 个领域 git mv；check_index.py 白名单 DOMAIN_META_FILES 改为 {"README.md"}，不留旧名兼容
- check_refs.py 注释、test_check_refs.py 夹具、两处领域交叉引用与文件地图同步
- knowledge-base-maintain SKILL.md 三处、commit-cc-plugin SKILL.md 链接目标同步
- commit-cc-plugin 3.4.2 → 3.4.3
```

---

## D 组：235 处图解回填

### Task 4: 抓取上游 alt → 图片路径映射

**Files:**
- Create: `tmp-fetch-altmap.ps1`（一次性脚本，Task 6 删除）
- Create: `tmp-altmap.json`（中间产物，Task 6 删除）

**Interfaces:**
- Consumes: Task 1 的新领域路径 `knowledge-base/data-structures-algorithms/`
- Produces: `tmp-altmap.json` —— 结构为 `{"<章节md路径>": [{"alt": "...", "path": "<相对该md的图片路径>"}, ...]}`，**每篇内保持文档出现顺序**。Task 5 依赖这个顺序做多图展开

- [ ] **Step 1: 写抓取脚本**

创建 `tmp-fetch-altmap.ps1`：

```powershell
$ErrorActionPreference = 'Continue'
$Tag = '1.3.0'
$RawBase = "https://raw.githubusercontent.com/krahets/hello-algo/$Tag/"

function Get-WithRetry($url, $tries = 4) {
    for ($i = 1; $i -le $tries; $i++) {
        try { return (Invoke-WebRequest -Uri $url -TimeoutSec 40 -UseBasicParsing).Content }
        catch { if ($i -eq $tries) { throw } ; Start-Sleep -Seconds 2 }
    }
}

# 列出 tag 下全部章节 md
$tree = Invoke-RestMethod -Uri "https://api.github.com/repos/krahets/hello-algo/git/trees/$Tag`?recursive=1" -TimeoutSec 60
$mds = $tree.tree | Where-Object { $_.path -like 'docs/chapter_*' -and $_.path -like '*.md' }
Write-Host "章节 md 数：$($mds.Count)"

$result = @{}
$n = 0
foreach ($m in $mds) {
    $content = Get-WithRetry ($RawBase + $m.path)
    $list = @()
    foreach ($x in [regex]::Matches($content, '!\[(?<alt>[^\]]*)\]\((?<p>[^)]+)\)')) {
        $list += @{ alt = $x.Groups['alt'].Value.Trim(); path = $x.Groups['p'].Value }
    }
    if ($list.Count -gt 0) { $result[$m.path] = $list; $n += $list.Count }
}
Write-Host "图片引用总数：$n"
$result | ConvertTo-Json -Depth 5 | Set-Content -Path 'tmp-altmap.json' -Encoding UTF8
Write-Host "已写入 tmp-altmap.json"
```

`Get-WithRetry` 的重试不可省略——实测 `raw.githubusercontent.com` 首次请求常超时，105 篇顺序抓取必然遇到。

- [ ] **Step 2: 运行并核对数量**

```powershell
pwsh -File tmp-fetch-altmap.ps1
```

Expected: `章节 md 数：105`、`图片引用总数` 约 500 上下、`已写入 tmp-altmap.json`

若 md 数不是 105，说明 tag 取错了（用了 `main`），检查脚本里的 `$Tag`。

- [ ] **Step 3: 验证映射能覆盖全部 235 处指针**

```bash
python - <<'PY'
import json, re, glob
raw = json.load(open('tmp-altmap.json', encoding='utf-8-sig'))
alts = {item['alt'] for lst in raw.values() for item in lst}
pat = re.compile(r'📊 原书图：(?P<body>.+?)（图解见')
tot = hit = 0
miss = []
for f in sorted(glob.glob('knowledge-base/data-structures-algorithms/reference/hello-algo-*.md')):
    for m in pat.finditer(open(f, encoding='utf-8').read()):
        body = m.group('body')
        mm = re.search(r'（(\d+) 张分步图：(.*)）\s*$', body)
        base = body[:mm.start()].strip() if mm else body.strip()
        tot += 1
        if base in alts: hit += 1
        else: miss.append((f, base))
print(f"指针 {tot}，命中 {hit}，未命中 {len(miss)}")
for x in miss: print("  未命中:", x)
PY
```

Expected: `指针 235，命中 235，未命中 0`

**剥离「（N 张分步图：…）」后缀是关键**——不剥离时匹配率只有 98.3%，剥离后是 100%。若出现未命中，不要改用模糊匹配，先确认剥离正则是否与实际文本一致。

### Task 5: 下载图片并改写 235 处正文

**Files:**
- Create: `tmp-backfill-figures.py`（一次性脚本，Task 6 删除）
- Create: `knowledge-base/data-structures-algorithms/reference/assets/`（约 480 张 png）
- Modify: `knowledge-base/data-structures-algorithms/reference/hello-algo-*.md`（15 篇）

**Interfaces:**
- Consumes: Task 4 的 `tmp-altmap.json`
- Produces: `assets/` 目录与改写后的 15 篇正文。单图形态 `![alt](assets/name.png)`，多图形态为连续 N 行 `![alt](assets/name.png)`

- [ ] **Step 1: 写回填脚本**

创建 `tmp-backfill-figures.py`：

```python
"""一次性脚本：把 15 篇 reference 的图指针替换为本地图片引用。

单图：`> 📊 原书图：<alt>（图解见 URL）` → `![<alt>](assets/<file>)`
多图：`> 📊 原书图：<alt>（N 张分步图：...）（图解见 URL）`
      → 首张 alt 命中后，按上游文档顺序连续取 N 张，逐行输出
"""
import json, re, glob
from pathlib import Path

REF_DIR = Path("knowledge-base/data-structures-algorithms/reference")
ASSETS = REF_DIR / "assets"
POINTER = re.compile(r'^> 📊 原书图：(?P<body>.+?)（图解见 (?P<url>[^）]+)）\s*$', re.MULTILINE)
MULTI = re.compile(r'（(?P<n>\d+) 张分步图：(?P<labels>.*)）\s*$')

raw = json.load(open("tmp-altmap.json", encoding="utf-8-sig"))

# alt → (章节md路径, 该 md 内的序号)；同名 alt 取首次出现
index = {}
for md_path, items in raw.items():
    for i, item in enumerate(items):
        index.setdefault(item["alt"], (md_path, i))

wanted = {}   # 图片文件名 → 上游完整 raw 路径
plan = []     # (文件, 原始整行, 替换文本)

for f in sorted(glob.glob(str(REF_DIR / "hello-algo-*.md"))):
    text = Path(f).read_text(encoding="utf-8")
    for m in POINTER.finditer(text):
        body = m.group("body")
        mm = MULTI.search(body)
        base_alt = body[:mm.start()].strip() if mm else body.strip()
        count = int(mm.group("n")) if mm else 1
        if base_alt not in index:
            raise SystemExit(f"未命中 alt：{base_alt}（{f}）")
        md_path, start = index[base_alt]
        items = raw[md_path][start:start + count]
        if len(items) != count:
            raise SystemExit(f"{base_alt} 需 {count} 张，上游只剩 {len(items)} 张")
        lines = []
        for item in items:
            name = item["path"].rsplit("/", 1)[-1]
            upstream = md_path.rsplit("/", 1)[0] + "/" + item["path"]
            if name in wanted and wanted[name] != upstream:
                raise SystemExit(f"文件名冲突：{name}")
            wanted[name] = upstream
            lines.append(f'![{item["alt"]}](assets/{name})')
        plan.append((f, m.group(0), "\n".join(lines)))

print(f"待替换指针 {len(plan)} 处，需下载唯一图片 {len(wanted)} 张")
ASSETS.mkdir(exist_ok=True)
json.dump(wanted, open("tmp-wanted.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump([[f, o, n] for f, o, n in plan], open("tmp-plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("已写出 tmp-wanted.json 与 tmp-plan.json")
```

脚本**只做计划、不写正文**，把下载清单与替换清单落成两个 JSON——这样下载失败时正文还没被动过，可以重跑。

- [ ] **Step 2: 生成计划并核对数量**

```bash
python tmp-backfill-figures.py
```

Expected: `待替换指针 235 处，需下载唯一图片 480 张左右`

若报 `未命中 alt` 或 `文件名冲突`，停下来处理——`文件名冲突` 意味着"485 张文件名全局唯一"这个前提被打破，需改为按章节建子目录。

- [ ] **Step 3: 下载图片**

创建并运行 `tmp-download-assets.ps1`：

```powershell
$ErrorActionPreference = 'Continue'
$RawBase = 'https://raw.githubusercontent.com/krahets/hello-algo/1.3.0/'
$dest = 'knowledge-base/data-structures-algorithms/reference/assets'
$wanted = Get-Content 'tmp-wanted.json' -Raw -Encoding UTF8 | ConvertFrom-Json
$ok = 0; $fail = @()
foreach ($p in $wanted.PSObject.Properties) {
    $out = Join-Path $dest $p.Name
    if (Test-Path $out) { $ok++; continue }
    $url = $RawBase + $p.Value
    $done = $false
    foreach ($i in 1..4) {
        try { Invoke-WebRequest -Uri $url -OutFile $out -TimeoutSec 40 -UseBasicParsing; $done = $true; break }
        catch { Start-Sleep -Seconds 2 }
    }
    if ($done) { $ok++ } else { $fail += $p.Name }
}
"下载成功 $ok 张；失败 $($fail.Count) 张"
$fail | ForEach-Object { "  FAIL: $_" }
```

Expected: `下载成功 480 张左右；失败 0 张`

脚本可重复运行——已存在的文件跳过，所以失败后直接重跑即可补齐。

- [ ] **Step 4: 确认下载完整**

```bash
python - <<'PY'
import json
from pathlib import Path
wanted = json.load(open('tmp-wanted.json', encoding='utf-8'))
d = Path('knowledge-base/data-structures-algorithms/reference/assets')
missing = [n for n in wanted if not (d / n).exists()]
empty = [p.name for p in d.glob('*') if p.stat().st_size == 0]
print(f"清单 {len(wanted)} 张，磁盘 {len(list(d.glob('*')))} 个文件")
print(f"缺失 {len(missing)}：{missing[:5]}")
print(f"零字节 {len(empty)}：{empty[:5]}")
PY
```

Expected: 缺失 0、零字节 0。有零字节文件说明下载被截断，删掉它们重跑 Step 3。

- [ ] **Step 5: 应用正文替换**

```bash
python - <<'PY'
import json
from pathlib import Path
plan = json.load(open('tmp-plan.json', encoding='utf-8'))
by_file = {}
for f, old, new in plan:
    by_file.setdefault(f, []).append((old, new))
for f, pairs in by_file.items():
    text = Path(f).read_text(encoding='utf-8')
    for old, new in pairs:
        if text.count(old) != 1:
            raise SystemExit(f"{f} 中 {text.count(old)} 次匹配：{old[:60]}")
        text = text.replace(old, new)
    Path(f).write_text(text, encoding='utf-8')
    print(f"{Path(f).name}: 替换 {len(pairs)} 处")
PY
```

Expected: 15 行输出，各篇替换数合计 235。

`text.count(old) != 1` 的守卫很重要——同一篇里若有两处完全相同的指针行，无条件 `replace` 会把两处都替换成同一组图，其中一处就错了。

- [ ] **Step 6: 改 15 篇头部的改动说明**

每篇第 16 行那句：

```
> 相对原书的改动：代码示例仅保留 C# 一种语言（原书含 12 种），图解未导出、原位置以指针指向原书。
```

改为：

```
> 相对原书的改动：代码示例仅保留 C# 一种语言（原书含 12 种），图解随书提取至本目录 `assets/`。
```

批量执行：

```bash
python - <<'PY'
import glob
from pathlib import Path
OLD = "图解未导出、原位置以指针指向原书。"
NEW = "图解随书提取至本目录 `assets/`。"
n = 0
for f in sorted(glob.glob('knowledge-base/data-structures-algorithms/reference/hello-algo-*.md')):
    p = Path(f); t = p.read_text(encoding='utf-8')
    if OLD in t:
        p.write_text(t.replace(OLD, NEW), encoding='utf-8'); n += 1
print(f"改动说明已更新 {n} 篇")
PY
```

Expected: `改动说明已更新 15 篇`

- [ ] **Step 7: 验证替换彻底、无断链**

```bash
grep -rc '📊 原书图' knowledge-base/data-structures-algorithms/reference/*.md | grep -v ':0' ; echo "指针残留检查完成（应无输出）"
grep -rc '图解未导出' knowledge-base/data-structures-algorithms/reference/*.md | grep -v ':0' ; echo "旧说明检查完成（应无输出）"
python - <<'PY'
import re, glob
from pathlib import Path
d = Path('knowledge-base/data-structures-algorithms/reference/assets')
refs = []
for f in glob.glob('knowledge-base/data-structures-algorithms/reference/hello-algo-*.md'):
    refs += re.findall(r'!\[[^\]]*\]\(assets/([^)]+)\)', Path(f).read_text(encoding='utf-8'))
broken = sorted({r for r in refs if not (d / r).exists()})
print(f"图片引用 {len(refs)} 处，唯一文件 {len(set(refs))}，断链 {len(broken)}")
for b in broken[:10]: print("  断链:", b)
PY
```

Expected: 前两个 grep 无输出；`图片引用 488 处`（196 单图 + 292 多图展开）、断链 0。

- [ ] **Step 8: 跑索引校验，确认图片不被报为孤儿**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" --audit | grep -i "孤儿"
```

Expected: `483 条 OK`；孤儿数 0。`check_index.py` 只扫 `.md`（7.1.0 已实测 `LICENSE` 不被报孤儿），`assets/*.png` 同理。

- [ ] **Step 9: 人工抽查预览渲染**

打开三篇确认图正常显示：

- `hello-algo-04-array-linkedlist.md`（单图为主）
- `hello-algo-05-stack-queue.md`（**含 6 处多图**，重点确认分步顺序为 step1→step2→step3，没有错位或重复）
- `hello-algo-07-tree.md`（含 11 张连续分步图的前序遍历）

Expected: 图片正常显示；多图组的顺序与正文叙述一致。

这一步无法自动化——断链检查只能证明文件存在，证明不了"配的是对的那张图"。

### Task 6: 清理一次性脚本并提交

**Files:**
- Delete: `tmp-fetch-altmap.ps1`、`tmp-download-assets.ps1`、`tmp-backfill-figures.py`、`tmp-altmap.json`、`tmp-wanted.json`、`tmp-plan.json`

**Interfaces:**
- Consumes: Task 5 的产物（已落地的 `assets/` 与改写后的正文）
- Produces: 干净的工作区，只剩需提交的内容变更

- [ ] **Step 1: 删除全部临时文件**

```bash
rm -f tmp-fetch-altmap.ps1 tmp-download-assets.ps1 tmp-backfill-figures.py tmp-altmap.json tmp-wanted.json tmp-plan.json
git status --short | grep '^??'
```

Expected: 只剩 `?? knowledge-base/data-structures-algorithms/reference/assets/`，没有任何 `tmp-*` 文件。

这些脚本不留仓库——它们不属于 `knowledge-base-maintain` 的常规能力，留下会变成无人维护的死代码（spec 5.4 已确认）。

- [ ] **Step 2: 确认新增体积在预期内**

```bash
du -sh knowledge-base/data-structures-algorithms/reference/assets/
```

Expected: 8-9 MB 量级。若显著超过（如 30 MB+），说明下载了非引用图，回到 Task 5 Step 2 核对清单数量。

- [ ] **Step 3: 跑三项检查回到基线**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
```

Expected: `483 条` / `140 个消费者文件` / `Ran 133 tests ... OK`

- [ ] **Step 4: 提交**

调用 `commit-cc-plugin` skill。**暂存时注意** `assets/` 是新目录含数百个文件，逐文件暂存不现实，用目录级暂存：`git add knowledge-base/data-structures-algorithms/reference/assets`（这不违反"禁止 `git add -A`"——禁的是全库通配，目录级精确暂存是允许的）。

message 要点：

```
feat(knowledge-base): data-structures-algorithms 图解随书提取至本地 assets/

- 235 处文本指针替换为标准 Markdown 图片引用（196 单图 + 39 多图展开为 292 张）
- 从上游 1.3.0 tag 下载约 480 张图至 reference/assets/，按 alt 文本精确匹配，100% 命中
- 15 篇头部改动说明由「图解未导出」改为「图解随书提取至本目录 assets/」
- 图片同属 CC BY-NC-SA 4.0 原作，现有三层隔离（LICENSE、署名块、目录级声明）不变
```

---

## C 组：CHANGELOG 拆分与领域独立版本号

### Task 7: 新增版本号一致性校验（TDD）

**Files:**
- Modify: `.claude/skills/knowledge-base-maintain/scripts/test_check_index.py`（新增测试类）
- Modify: `.claude/skills/knowledge-base-maintain/scripts/check_index.py`（新增 `check_domain_versions`，接入 `run_checks`）

**Interfaces:**
- Consumes: Task 3 产出的 `knowledge-base/<domain>/README.md`
- Produces: `check_domain_versions(base_dir)` → `list[str]`，问题描述列表（空表示通过）。校验每个领域 `README.md` 顶部 `> 版本：x.y.z` 与该领域 `CHANGELOG.md` 首个 `## [x.y.z]` 一致。在 `run_checks` 末尾与 `check_catalog` 并列调用

- [ ] **Step 1: 写失败的测试**

在 `test_check_index.py` 的 `TestCheckCatalog` 类之后插入新测试类。同时在文件顶部的 `from check_index import (...)` 列表中按字母序加入 `check_domain_versions`：

```python
class TestCheckDomainVersions(unittest.TestCase):
    def _domain(self, base, name="csharp", readme_ver="7.2.1", changelog_ver="7.2.1"):
        d = base / name
        d.mkdir(parents=True, exist_ok=True)
        d.joinpath("index.jsonl").write_text("", encoding="utf-8")
        if readme_ver is not None:
            d.joinpath("README.md").write_text(
                f"# {name}\n\n> 版本：{readme_ver}\n\n正文\n", encoding="utf-8")
        else:
            d.joinpath("README.md").write_text(f"# {name}\n\n正文\n", encoding="utf-8")
        if changelog_ver is not None:
            d.joinpath("CHANGELOG.md").write_text(
                f"# Changelog\n\n## [{changelog_ver}] - 2026-08-29\n\n### Changed\n- x\n",
                encoding="utf-8")

    def test_matching_versions_have_no_problems(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base)
            self.assertEqual(check_domain_versions(base), [])

    def test_mismatched_version_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base, readme_ver="7.2.1", changelog_ver="8.0.0")
            problems = check_domain_versions(base)
            self.assertTrue(any("版本号不一致" in p and "7.2.1" in p and "8.0.0" in p
                                for p in problems))

    def test_missing_version_line_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base, readme_ver=None)
            self.assertTrue(any("README.md 缺少版本行" in p for p in check_domain_versions(base)))

    def test_missing_changelog_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base, changelog_ver=None)
            self.assertTrue(any("CHANGELOG.md 不存在" in p for p in check_domain_versions(base)))

    def test_changelog_without_version_entry_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base)
            (base / "csharp" / "CHANGELOG.md").write_text(
                "# Changelog\n\n还没有任何版本条目\n", encoding="utf-8")
            self.assertTrue(any("CHANGELOG.md 无版本条目" in p
                                for p in check_domain_versions(base)))
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_check_index.py" -k DomainVersions -v
```

Expected: **FAIL** — `ImportError: cannot import name 'check_domain_versions' from 'check_index'`

- [ ] **Step 3: 实现 check_domain_versions**

在 `check_index.py` 中，紧接 `check_catalog` 函数之后插入。同时在文件顶部常量区（`DATE_RE` 附近）加入两个正则：

```python
# 领域版本号：README.md 顶部的 `> 版本：x.y.z` 与 CHANGELOG.md 首个 `## [x.y.z]`
VERSION_LINE_RE = re.compile(r'^>\s*版本：\s*(?P<ver>\d+\.\d+\.\d+)\s*$', re.MULTILINE)
CHANGELOG_VER_RE = re.compile(r'^##\s*\[(?P<ver>\d+\.\d+\.\d+)\]', re.MULTILINE)
```

```python
def check_domain_versions(base_dir):
    """校验每个领域 README.md 的版本行与其 CHANGELOG.md 最新条目一致。

    取消全局版本号后，版本号散落在 9 个领域，靠人看必然漂移——README 说 7.2.1、
    CHANGELOG 最新条目是 8.0.0 这类不一致不会被任何其他检查发现，
    而消费者读的是 README 顶部那一行。
    """
    problems = []
    for domain in collect_all_domains(base_dir):
        domain_dir = base_dir / domain
        readme = domain_dir / "README.md"
        changelog = domain_dir / "CHANGELOG.md"

        if not readme.exists():
            problems.append(f"[{domain}] README.md 不存在：{readme}")
            continue
        m = VERSION_LINE_RE.search(readme.read_text(encoding="utf-8"))
        if not m:
            problems.append(f"[{domain}] README.md 缺少版本行（应为 `> 版本：x.y.z`）")
            readme_ver = None
        else:
            readme_ver = m.group("ver")

        if not changelog.exists():
            problems.append(f"[{domain}] CHANGELOG.md 不存在：{changelog}")
            continue
        c = CHANGELOG_VER_RE.search(changelog.read_text(encoding="utf-8"))
        if not c:
            problems.append(f"[{domain}] CHANGELOG.md 无版本条目（应含 `## [x.y.z] - YYYY-MM-DD`）")
            continue

        if readme_ver and readme_ver != c.group("ver"):
            problems.append(
                f"[{domain}] 版本号不一致：README.md 为 {readme_ver}，"
                f"CHANGELOG.md 最新条目为 {c.group('ver')}")
    return problems
```

`CHANGELOG_VER_RE.search` 取的是**首个**匹配，因此 CHANGELOG 必须最新版本在最上方——这与仓库既有 CHANGELOG 格式一致（`.claude/rules/skill-conventions.md` 规定倒序）。

- [ ] **Step 4: 跑测试确认通过**

```bash
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_check_index.py" -k DomainVersions -v
```

Expected: **PASS** — `Ran 5 tests ... OK`

- [ ] **Step 5: 接入 run_checks**

在 `run_checks` 末尾，`check_catalog` 之后加一行：

```python
    problems.extend(check_duplicate_ids(global_entries))
    problems.extend(check_catalog(base_dir))
    problems.extend(check_domain_versions(base_dir))
    return problems
```

放在全局检查区、与 `check_catalog` 并列——版本一致性是领域级元数据校验，与单领域的 file/anchor 检查不同层，即使只传一个 domain 参数也应全库判定。

- [ ] **Step 6: 跑全量测试**

```bash
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
```

Expected: `Ran 138 tests ... OK`（133 + 5 新增）

**若 `TestRunChecks` 里的既有测试转红**，原因是它们的临时领域没有 README/CHANGELOG，被新校验报错了。修法：给 `write_domain` helper 加上写入 README 与 CHANGELOG 的能力，而不是把新校验从 `run_checks` 里摘出来——摘出来等于让这个刹车在真实调用路径上失效。参考改法：

```python
def write_domain(base, domain, entries, files=None, version="7.2.1"):
    """在临时 base 目录下造一个领域：写入 index.jsonl 与 files 指定的 Markdown。"""
    domain_dir = base / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    for rel, text in (files or {}).items():
        target = domain_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    domain_dir.joinpath("index.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries),
        encoding="utf-8",
    )
    if version is not None:
        domain_dir.joinpath("README.md").write_text(
            f"# {domain}\n\n> 版本：{version}\n", encoding="utf-8")
        domain_dir.joinpath("CHANGELOG.md").write_text(
            f"# Changelog\n\n## [{version}] - 2026-08-29\n\n### Changed\n- x\n",
            encoding="utf-8")
    return domain_dir
```

- [ ] **Step 7: 确认真实数据此时报错（领域尚无 CHANGELOG 与版本行）**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
```

Expected: **FAIL**，9 组形如 `[csharp] README.md 缺少版本行` + `[csharp] CHANGELOG.md 不存在` 的报错。这是有意的中间状态，Task 8 建完 CHANGELOG 与版本行后恢复。

本 Task 不单独提交，与 Task 8、Task 9 合并为一次提交。

### Task 8: 拆分 CHANGELOG 到 9 个领域，写入版本行

**Files:**
- Create: `knowledge-base/<domain>/CHANGELOG.md`（9 个）
- Modify: `knowledge-base/<domain>/README.md`（9 个，顶部插入版本行）
- Delete: `knowledge-base/CHANGELOG.md`
- Modify: `knowledge-base/README.md`（删顶部版本行、改写维护约定末条）

**Interfaces:**
- Consumes: Task 7 的 `check_domain_versions`（决定 README 版本行与 CHANGELOG 首条目的格式）
- Produces: 9 个领域 CHANGELOG 与版本行。`data-structures-algorithms` = `8.0.0`，其余 8 个 = `7.2.1`

- [ ] **Step 1: 备份根 CHANGELOG 以便拆分时对照**

```bash
cp knowledge-base/CHANGELOG.md /tmp/kb-changelog-backup.md
grep -c '^## \[' /tmp/kb-changelog-backup.md
```

Expected: `34`

拆分期间从这份备份读原文，不要边删边读。

- [ ] **Step 2: 逐条按下表归属，把 26 条历史写入各领域 CHANGELOG**

**删除的 8 条**（改的是知识库机制而非领域内容，不写入任何领域）：

| 版本 | 内容 |
|---|---|
| 1.0.0 | 知识库建立、`index.jsonl` 机制、`check_index.py` |
| 1.1.1 | 校验脚本迁至 skill 的 `scripts/` |
| 1.3.3 | 根 README 补"动态检索 vs 固定映射"、覆盖渐进式 |
| 2.0.0 | Phase 0 基线与保护网 |
| 3.0.0 | Phase 2 规则内容质量治理 |
| 4.0.0 | 全库跨领域查重 |
| 4.1.0 | 根 README 新增"status：废弃条目的过渡期" |
| 5.0.0 | `enforcement` 从 3.7% 推广到 100% |

**归入单一领域的 20 条**：

| 领域 | 版本条目 |
|---|---|
| csharp | 1.1.0、1.2.0、1.4.0 |
| skill-authoring | 1.3.0、1.3.1 |
| wpf | 1.3.2 |
| git | 1.6.0、1.7.0、1.8.0、4.0.1 |
| media | 1.9.0、1.9.1、1.10.0、1.10.1、1.10.2、1.10.3、1.10.4 |
| dotnet | 1.11.0 |
| data-structures-algorithms | 7.1.0、7.2.0 |

**切成两半的 6 条**（每侧只留与该领域相关的内容，标注衍生来源）：

| 版本 | 切法 |
|---|---|
| 1.2.1 | csharp 侧记「`README.md` 改名为 `00-README.md`」；wpf 侧同 |
| 1.5.0 | git 侧记「新建 git 领域，首批 11 条索引」；csharp 侧记「`16-collaboration.md` 五节迁出至 git，本篇仅保留语言相关 CHANGELOG 条款并重编号为 §1」 |
| 4.2.0 | csharp 侧记「索引覆盖率 81.8% → 96.2%，新增 19 条（124 → 143）」；wpf 与 git 侧**不记**——原文提到它们只是横向对比与顺带修正，非该领域变更（判定依据：读正文，不是 grep 领域名） |
| 5.1.0 | architecture 侧记「新建领域，10 篇 rules + 2 篇 reference，64 条索引」；csharp 侧记「本次未收窄重复条款，迁移改造预告在 6.0.0」 |
| 6.0.0 | csharp 侧记「五条架构条款正文收窄为『引用 + C# 特有增量』，`id`/`file`/`anchor` 不动，属不兼容语义变化」；architecture 侧记「接收 csharp 迁出的通用约束」 |
| 7.0.0 | design-patterns 侧记「新建领域，6 篇 rules + 2 篇 reference，35 条索引」；csharp 侧记「`csharp.03.design-pattern-moderation` 正文收窄，`id`/`file`/`anchor` 不动」 |

每个领域 `CHANGELOG.md` 的结构（以 csharp 为例）：

```markdown
# Changelog — C# 语言与通用工程实践

本领域自 7.2.1 起使用**独立版本号**。7.2.0 及之前为知识库统一全局版本号时代，相关条目见下方「全局版本时代」，其版本号为当时的全局版本。

## [7.2.1] - 2026-08-29

### Changed
- 领域元数据文件 `00-README.md` 改名为 `README.md`

---

## 全局版本时代（2026-08-22 .. 2026-08-29）

### 衍生自全局 7.0.0 - 2026-08-29

- `csharp.03.design-pattern-moderation` 正文范围与 `summary` 收窄，通用判断层归入 `design-patterns` 领域。`id`/`file`/`anchor` 全部不动，检索仍能命中；属不兼容语义变化。经 grep 确认该条目零消费者 skill 引用

### 衍生自全局 6.0.0 - 2026-08-29

（原文中与 csharp 相关的部分）

（……按版本号倒序继续）
```

标题里的领域中文名取 `catalog.json` 的 `title` 字段，保持一致。

**倒序排列**（新版本在上），与仓库既有 CHANGELOG 格式一致，也是 `CHANGELOG_VER_RE` 取首个匹配的前提。

- [ ] **Step 3: 给 9 个领域 README 顶部插入版本行**

在每个 `knowledge-base/<domain>/README.md` 的一级标题之后、原有引言之前插入版本行加空行。以 csharp 为例，改后前 4 行为：

```markdown
# C# 开发规范

> 版本：7.2.1

> 面向团队的全覆盖 C# 开发总纲。**版本中立**——不绑定特定 .NET 版本，适用于所有主流 .NET 版本；编码风格与工程实践并重。
```

各领域版本号：

| 领域 | 版本 |
|---|---|
| data-structures-algorithms | **8.0.0** |
| architecture、csharp、design-patterns、dotnet、git、media、skill-authoring、wpf | **7.2.1** |

`data-structures-algorithms` 是 8.0.0 而非 7.2.1，因为它本次有 A 组改名（Major）与 D 组图片回填（Minor）。

- [ ] **Step 4: 删除根 CHANGELOG**

```bash
git rm knowledge-base/CHANGELOG.md
```

- [ ] **Step 5: 改根 README.md 两处**

删除第 3 行的 `> 版本：7.2.0` 与其后的空行（按你的决定不放领域版本一览表）。

第 143 行维护约定末条：

```
- 版本号见本文件顶部，变更规则与 CHANGELOG 格式见 `CHANGELOG.md`；日常新增/修改建议通过 `/knowledge-base-maintain` skill 完成，会自动同步索引与版本号。
```

改为：

```
- **版本号按领域独立管理**：各领域版本号见该领域 `README.md` 顶部，变更历史见该领域 `CHANGELOG.md`；知识库不再有全局版本号（7.2.0 为分叉点，此前的全局版本历史已按领域归入各自 CHANGELOG）。一次变更涉及多个领域时，每个领域各自升版本、各自写 CHANGELOG。`check_index.py` 校验领域 README 版本行与其 CHANGELOG 最新条目一致。日常新增/修改建议通过 `/knowledge-base-maintain` skill 完成，会自动同步索引与版本号。
```

- [ ] **Step 6: 跑校验确认版本一致性通过**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
```

Expected: `OK: 共检查 483 条记录，未发现问题` —— Task 7 Step 7 的 18 条报错全部消失。

- [ ] **Step 7: 故意改错一处，确认新校验真的能拦**

```bash
python - <<'PY'
from pathlib import Path
p = Path("knowledge-base/csharp/README.md")
t = p.read_text(encoding="utf-8")
p.write_text(t.replace("> 版本：7.2.1", "> 版本：9.9.9", 1), encoding="utf-8")
print("已把 csharp README 版本改为 9.9.9")
PY
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
```

Expected: **FAIL** — `[csharp] 版本号不一致：README.md 为 9.9.9，CHANGELOG.md 最新条目为 7.2.1`

这一步验证的是"刹车真的在真实数据上生效"，不是重复 Task 7 的单元测试——单元测试跑的是临时目录夹具。

- [ ] **Step 8: 改回并确认恢复**

```bash
python - <<'PY'
from pathlib import Path
p = Path("knowledge-base/csharp/README.md")
t = p.read_text(encoding="utf-8")
p.write_text(t.replace("> 版本：9.9.9", "> 版本：7.2.1", 1), encoding="utf-8")
print("已改回 7.2.1")
PY
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
git diff --stat knowledge-base/csharp/README.md
```

Expected: 校验 `OK`；`git diff` 显示该文件只有插入版本行这一处改动（证明试错已完全复原，没留下 9.9.9 残迹）。

- [ ] **Step 9: 确认根 CHANGELOG 引用已无残留**

```bash
grep -rn "knowledge-base/CHANGELOG" --include="*.md" --include="*.py" . 2>/dev/null | grep -v "^./docs/\|^./.remember/"
```

Expected: **无输出**。

预期需处理的两处：`knowledge-base/dotnet/README.md:45`（"同步更新 `index.jsonl`、根知识库版本和 `knowledge-base/CHANGELOG.md`"，改为指向本领域 CHANGELOG）、`test_check_refs.py:319`（断言里的 `knowledge-base/CHANGELOG.md`，改为其他仍存在的路径或直接删该断言行——它验证的是"CHANGELOG 不被当作消费者扫描"，文件已删则该断言无意义）。

- [ ] **Step 10: 跑三项检查**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
```

Expected: `483 条` / `140 个消费者文件` / `Ran 138 tests ... OK`

本 Task 不单独提交，与 Task 7、Task 9 合并。

### Task 9: 改 knowledge-base-maintain skill 并提交

**Files:**
- Modify: `.claude/skills/knowledge-base-maintain/SKILL.md`（Step 6 重写、Step 2 新建领域、Step 5 问题表、frontmatter 版本）
- Modify: `.claude/skills/knowledge-base-maintain/CHANGELOG.md`

**Interfaces:**
- Consumes: Task 7 的 `check_domain_versions`、Task 8 的领域 CHANGELOG 结构
- Produces: skill 1.9.0，Step 6 指向领域级版本号与 CHANGELOG

- [ ] **Step 1: 重写 SKILL.md 的 Step 6（第 169-179 行整节）**

```markdown
## Step 6：同步版本号与 CHANGELOG（新增/修改/迁移/废弃场景，仅校验场景跳过）

**版本号按领域独立管理**，知识库无全局版本号（7.2.0 为分叉点）。判断本次变更对**每个受影响领域**的升级级别：

| 变更类型 | 版本升级 |
|---|---|
| 新增领域、新增规范条目、新增 reference 条目 | Minor `x.X.x` |
| 修改已有规范/reference 内容、修正索引、文档优化 | Patch `x.x.X` |
| 删除领域、删除规范条目、**废弃条目（`status` 改 `deprecated`）**、规范措辞产生不兼容语义变化（如 SHOULD 改 MUST）、领域改名或条目 `id` 变更 | Major `X.x.x` |

**一次变更涉及多个领域时，每个领域各自升版本、各自写 CHANGELOG**——这是本模型下最容易做错的地方。跨领域迁移（如把条款从 `csharp` 迁到 `architecture`）两侧都要写：迁出侧记「收窄为引用 + 特有增量」，迁入侧记「接收通用约束」，两侧各自按自己的级别升版本（迁出侧通常是 Major，迁入侧可能只是 Minor）。

改两处，二者版本号必须一致（`check_index.py` 会校验）：

1. `knowledge-base/<domain>/README.md` 顶部 `> 版本：x.y.z`
2. `knowledge-base/<domain>/CHANGELOG.md` 顶部追加 `## [版本号] - YYYY-MM-DD` + `### Added`/`Changed`/`Removed`/`Fixed`（只写实际发生的类别），**新条目放在最上方**——校验器取首个 `## [x.y.z]` 作为最新版本
```

- [ ] **Step 2: 改 SKILL.md 第 37 行的新建领域流程**

在该句的文件创建清单中补入 CHANGELOG。原文要求创建 `README.md` 与空 `index.jsonl`，改为要求创建三个文件：

```
新建领域时先创建 `knowledge-base/<domain>/README.md`（参照 `knowledge-base/csharp/README.md` 的章节结构：文档目的、适用范围与读者、规范级别、阅读路径、文件地图，**顶部须有 `> 版本：1.0.0` 版本行**）、`knowledge-base/<domain>/CHANGELOG.md`（首条目 `## [1.0.0] - <今天>`，版本号与 README 一致）与空的 `knowledge-base/<domain>/index.jsonl`，并在 `knowledge-base/catalog.json` 的 `domains` 数组追加一条记录
```

新领域起始 `1.0.0` 而非 7.2.x——分叉点只适用于分叉时已存在的 9 个领域。

- [ ] **Step 3: 给 SKILL.md 第 137-152 行的问题表补 5 行**

在表格末尾追加新校验对应的问题类型：

```markdown
| `README.md 缺少版本行` | 领域 README 顶部漏了 `> 版本：x.y.z`（须紧跟一级标题） |
| `CHANGELOG.md 不存在` | 新建领域时漏建该领域 CHANGELOG |
| `CHANGELOG.md 无版本条目` | CHANGELOG 只有标题、没有 `## [x.y.z] - YYYY-MM-DD` 条目 |
| `版本号不一致` | 改了 README 版本行忘了写 CHANGELOG 条目（或反之）——两处必须同步 |
| `README.md 不存在` | 领域目录有 `index.jsonl` 但缺元数据文件 |
```

- [ ] **Step 4: 给 SKILL.md 失败处理表补 1 行**

在第 187-194 行的表格末尾追加：

```markdown
| `check_index.py` 报版本号不一致 | 确认本次实际改了什么，据此定级别，再同步 README 版本行与 CHANGELOG 首条目 | 若是历史遗留不一致（非本次改动造成），以 CHANGELOG 最新条目为准修正 README——CHANGELOG 记录了变更事实，README 那一行只是展示 |
```

- [ ] **Step 5: 升 skill 版本并写 CHANGELOG**

`SKILL.md` frontmatter 第 5 行：`version: "1.8.0"` → `version: "1.9.0"`

`CHANGELOG.md` 在 `# Changelog` 之后追加：

```markdown
## [1.9.0] - 2026-08-29

### Added
- `check_index.py` 新增 `check_domain_versions`：校验每个领域 `README.md` 顶部 `> 版本：x.y.z` 与该领域 `CHANGELOG.md` 首个版本条目一致，接入 `run_checks` 的全局检查区。取消全局版本号后版本号散落 9 处，靠人看必然漂移——README 说 7.2.1 而 CHANGELOG 最新是 8.0.0 这类不一致不会被任何其他检查发现，而消费者读的正是 README 那一行
- Step 5 问题表新增 5 行、失败处理表新增 1 行，覆盖新校验的报错形态

### Changed
- **Step 6 整节重写**：版本号与 CHANGELOG 由「根 `README.md` + 根 `CHANGELOG.md`」改为「各领域 `README.md` + 各领域 `CHANGELOG.md`」。新增判断：一次变更涉及多个领域时，每个领域各自升版本、各自写 CHANGELOG，跨领域迁移两侧级别可以不同（迁出侧通常 Major，迁入侧可能只是 Minor）
- Step 6 版本级别表的 Major 行补入「领域改名或条目 `id` 变更」——本次 `algorithms` → `data-structures-algorithms` 属此类，旧表未覆盖
- Step 2 新建领域流程要求同时创建 `CHANGELOG.md`（首条目 `1.0.0`）与带版本行的 `README.md`；新领域起始 `1.0.0`，不套用 7.2.0 分叉点
- 领域元数据文件路径由 `00-README.md` 改为 `README.md`（Step 2、Step 4 迁移五处、失败处理表）
```

- [ ] **Step 6: 确认 skill 与实现一致**

```bash
grep -n "00-README" .claude/skills/knowledge-base-maintain/SKILL.md; echo "SKILL 旧文件名检查完成（应无输出）"
grep -n "根 CHANGELOG\|knowledge-base/CHANGELOG\|knowledge-base/README.md\` 顶部" .claude/skills/knowledge-base-maintain/SKILL.md; echo "全局版本表述检查完成（应无输出）"
grep -n 'version: "1.9.0"' .claude/skills/knowledge-base-maintain/SKILL.md
```

Expected: 前两个 grep 无输出；第三个匹配到版本行。

- [ ] **Step 7: 跑三项检查，确认全绿**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
```

Expected: `483 条` / `140 个消费者文件` / `Ran 138 tests ... OK`

- [ ] **Step 8: 全库最终核对**

```bash
ls knowledge-base/CHANGELOG.md 2>&1 | grep -q "No such" && echo "根 CHANGELOG 已删除 ✓"
for d in knowledge-base/*/; do
  n=$(basename "$d")
  r=$(grep -c '^> 版本：' "$d/README.md" 2>/dev/null || echo 0)
  c=$([ -f "$d/CHANGELOG.md" ] && echo yes || echo NO)
  printf "%-28s 版本行=%s CHANGELOG=%s\n" "$n" "$r" "$c"
done
grep -n '^> 版本：' knowledge-base/README.md; echo "根 README 版本行检查完成（应无输出）"
```

Expected: 根 CHANGELOG 已删除；9 个领域全部 `版本行=1 CHANGELOG=yes`；根 README 无版本行。

- [ ] **Step 9: 提交**

调用 `commit-cc-plugin` skill，把 Task 7/8/9 作为一次提交，message 要点：

```
refactor(knowledge-base)!: 版本号与 CHANGELOG 改为按领域独立管理

- 根 CHANGELOG 删除，34 条历史按领域拆分：20 条归单一领域、6 条跨领域切分（标注衍生来源）、8 条机制类记录不保留
- 9 个领域 README 顶部新增版本行，CHANGELOG 各自建立；7.2.0 为分叉点，data-structures-algorithms 落 8.0.0，其余 7.2.1
- 根 README 删除全局版本行，维护约定改写为领域独立版本模型
- check_index.py 新增 check_domain_versions 校验 README 版本行与 CHANGELOG 首条目一致，配 5 个单元测试（133 → 138）
- knowledge-base-maintain 1.8.0 → 1.9.0：Step 6 整节重写，Step 2/5 与失败处理表同步
```

---

## 自审记录

**Spec 覆盖核对**（spec 各节 → 实现任务）：

| spec 节 | 任务 |
|---|---|
| 3 A 组领域改名 | Task 1 |
| 4 B 组 README 改名 | Task 2（白名单 TDD）、Task 3（文件与引用） |
| 5 D 组图解回填 | Task 4（抓映射）、Task 5（下载与改写）、Task 6（清理提交） |
| 6.1 版本号位置 | Task 8 Step 3、Step 5 |
| 6.2 CHANGELOG 拆分规则 | Task 8 Step 2（含 34 条完整归属表） |
| 6.4 skill 同步改动 | Task 9 Step 1-4 |
| 6.5 新增版本一致性校验 | Task 7（TDD 5 个测试）、Task 8 Step 7-8（真实数据验证） |
| 7 基线数据 | 头部「基线」表，每组末尾回归 |
| 8 提交与版本 | 各 Task 末步 + Global Constraints |

**已知的计划内偏差**：spec 提到 A 组需改 `reference/hello-algo-01-intro.md`，实测该文件 3 处 `algorithms` 全在上游 URL 内，不是领域名——spec 已修正为"实测确认无需改"，Task 1 相应不含该步。

**类型一致性**：`check_domain_versions(base_dir) -> list[str]` 在 Task 7 定义、Task 8/9 引用，签名与 `check_catalog(base_dir)` 一致；`VERSION_LINE_RE` / `CHANGELOG_VER_RE` 只在 Task 7 引入并使用。`DOMAIN_META_FILES` 在 Task 2 改值，Task 3 依赖其新值。


