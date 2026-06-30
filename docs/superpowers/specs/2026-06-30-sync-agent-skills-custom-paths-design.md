# sync-agent-skills 自定义 source/target 参数扩展设计

**日期：** 2026-06-30  
**Skill：** `unipus-devops-plugin:sync-agent-skills`  
**版本目标：** v1.2.0

---

## 背景

当前 skill 的 source 和 target 目录硬编码为默认值：
- source：`~/.agents/skills/`
- targets：`~/.claude/skills/`、`~/.kiro/skills/`

用户无法将其他目录的 skill 同步到自定义工具目录（如 `~/.cursor/skills/`）。

---

## 目标

1. 默认行为不变：不指定参数时使用原有默认值
2. 支持通过参数语法自定义 source 和 target
3. 支持 target 多目标（逗号分隔）
4. 自定义参数时展示参数语法说明

---

## 方案

**方案 A（采用）— 参数前置解析，注入现有 Step 变量**

在现有 Step 0（权限检测）之前新增 **Step 0 — 参数解析**，将原权限检测顺移为 Step 1，其余 Step 编号依次 +1。

参数解析结果以 `$source`/`$targets` 变量注入后续所有步骤，后续步骤无需感知"是否使用自定义参数"。

---

## 详细设计

### Step 0 — 参数解析（新增）

**触发语法：**

```
source=<绝对路径>           指定 skill 源目录
target=<路径1,路径2,...>    指定一个或多个目标目录（逗号分隔）
```

**逻辑：**

1. 从用户指令中提取 `source=` 和 `target=` 参数
2. 未提供则使用默认值
3. `target` 按逗号分隔解析为数组，去除每项首尾空格
4. 解析完成后打印确认行：
   ```
   📂 source: /path/to/source
   🎯 targets: ~/.claude/skills/ | ~/.kiro/skills/
   ```
5. 若使用了自定义参数，额外打印参数语法说明（默认模式不打印）：
   ```
   ℹ️  参数用法：
       source=<绝对路径>         指定 skill 源目录
       target=<路径1,路径2,...>  指定一个或多个目标目录（逗号分隔）
   ```

**变量赋值（Windows）：**

```powershell
$source  = "$env:USERPROFILE\.agents\skills"
$targets = @("$env:USERPROFILE\.claude\skills", "$env:USERPROFILE\.kiro\skills")
$useCustom = $false

# 从用户指令解析 source= 和 target=
# 若找到 source= → 覆盖 $source，设 $useCustom = $true
# 若找到 target= → 按逗号分割并 Trim()，覆盖 $targets，设 $useCustom = $true
```

**变量赋值（Bash）：**

```bash
source_dir="$HOME/.agents/skills"
targets=("$HOME/.claude/skills" "$HOME/.kiro/skills")
use_custom=false

# 从用户指令解析 source= 和 target=
# 若找到 source= → 覆盖 source_dir，use_custom=true
# 若找到 target= → IFS=',' read -ra targets，use_custom=true
```

---

### 自定义路径的边界处理

仅在 `$useCustom = $true` 时触发，插入参数解析后、源目录扫描前：

| 场景 | 行为 |
|------|------|
| source 路径不存在 | 与默认模式一致：打印错误并终止 |
| target 父目录不存在（自定义） | 询问 `❓ 目标目录 X 的父目录不存在，是否自动创建？(y/n)`；y → mkdir -p；n → 跳过该 target |
| target 路径是文件（非目录） | 打印 `❌ X 已存在且是文件，跳过`，跳过该 target |

> 注：默认路径的父目录不存在（如 `~/.kiro/` 未安装）保持原有静默跳过逻辑。

---

### 后续步骤（无变化）

Step 2（扫描源目录）、Step 3（创建链接）、Step 4（检测失效链接）、Step 5（汇总 & CHECKPOINT）只消费 `$source`/`$targets` 变量，无需任何修改。`$targets` 本为数组并被 foreach/for 迭代，多 target 天然支持。

---

## 步骤编号映射

| 原编号 | 新编号 | 内容 |
|--------|--------|------|
| —      | Step 0 | 参数解析（新增） |
| Step 0 | Step 1 | 权限检测（Windows 专用） |
| Step 1 | Step 2 | 扫描源目录 |
| Step 2 | Step 3 | 检测目标目录 & 创建链接 |
| Step 3 | Step 4 | 检测失效链接 |
| Step 4 | Step 5 | 汇总输出 & CHECKPOINT |

---

## 版本规划

| 变更 | 类型 |
|------|------|
| 新增 `source=` / `target=` 参数支持 | Minor |
| 步骤编号重排 | Patch |

目标版本：`v1.2.0`
