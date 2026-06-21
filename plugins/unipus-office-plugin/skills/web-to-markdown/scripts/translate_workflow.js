/**
 * 长文档分段翻译 Workflow 模板
 *
 * 用法：Workflow({ scriptPath: "...translate_workflow.js", args: CONFIG })
 *
 * args：
 *   raw        {string}  原文临时文件绝对路径（docs/.raw-xxx.md）
 *   out        {string}  目标文件绝对路径
 *   tmp        {string}  临时段文件前缀（如 /path/docs/.tmp-seg）
 *   source     {string}  原始 URL，写入 frontmatter
 *   totalLines {number}  原文行数（调用方已知时传入可省去 count-lines agent）
 *   segSize    {number}  每段行数，默认 90
 *   terms      {string}  追加术语对照，如 "foo→bar, baz→qux"
 */

export const meta = {
  name: 'translate-long-doc',
  description: '长文档分段翻译：Read 文件 → 翻译 → Write 临时文件，Bash 合并',
  phases: [
    { title: 'Translate', detail: '各段并行翻译，写临时文件' },
    { title: 'Merge',     detail: 'Bash 合并，清理临时文件' },
  ],
}

// ── 参数校验 ──────────────────────────────────────────────
if (!args || !args.raw || !args.out || !args.tmp || !args.source) {
  throw new Error('缺少必要参数：raw / out / tmp / source')
}
const { raw, out, tmp, source, segSize = 90, terms = '' } = args

// ── 统计行数（优先使用调用方传入的 totalLines，避免多消耗一次 agent）──
let totalLines = args.totalLines ? parseInt(args.totalLines, 10) : 0
if (!totalLines || totalLines < 1) {
  const r = await agent(
    `运行 Bash（单次）：python -c "print(sum(1 for _ in open(r'${raw}')))"，只输出整数结果。`,
    { label: 'count-lines', phase: 'Translate' }
  )
  totalLines = parseInt(r.trim().split(/\D+/).find(s => s.length > 0) || '0', 10)
  if (!totalLines || totalLines < 1) throw new Error(`行数解析失败：${r}`)
}

// ── 生成分段 ──────────────────────────────────────────────
const segments = []
for (let offset = 1, id = 1; offset <= totalLines; offset += segSize, id++) {
  segments.push({ id, offset, limit: Math.min(segSize, totalLines - offset + 1) })
}
log(`共 ${totalLines} 行，分为 ${segments.length} 段（每段 ${segSize} 行）`)

// ── 翻译规则（压缩为单行，减少每段 prompt token）─────────
const RULES =
  `翻译规则：` +
  `①代码/URL/路径/专有名词/产品名/API名 原文不变；` +
  `②术语：agent→智能体,subagent→子智能体,background session→后台会话,` +
  `supervisor→主进程,worktree→工作树,context window→上下文窗口,` +
  `prompt→提示词,skill/hook/plugin/MCP server保留原文` +
  (terms ? `,${terms}` : '') + `；` +
  `③HTML组件：<Note>→"> **注意：**"引用块,<Step title="X">→"**步骤N：X**"加粗标题,` +
  `</Steps>忽略,<img>→标准MD图片；` +
  `④段落一一对应不增删；⑤直接输出MD不加说明`

// ── 并行翻译 ──────────────────────────────────────────────
phase('Translate')
const results = await parallel(segments.map(seg => () =>
  agent(
    `技术文档翻译。` +
    `Read "${raw}" offset:${seg.offset} limit:${seg.limit}，` +
    `翻译为中文（${RULES}），` +
    `Write 到 "${tmp}-${seg.id}.md"，` +
    `完成后只输出"seg-${seg.id} done"。`,
    { label: `seg-${seg.id}`, phase: 'Translate' }
  )
))

// ── 失败检测 ──────────────────────────────────────────────
const failedSegs = segments.filter((_, i) => results[i] === null)
if (failedSegs.length > 0) {
  const ids = failedSegs.map(s => s.id).join(', ')
  return `翻译未完成：段 [${ids}] 失败。用 resumeFromRunId 重试，已完成段将从缓存取回。`
}

// ── 合并（子 shell + set -e，任一 cat 失败立即终止）───────
phase('Merge')
const segIds = segments.map(s => s.id).join(' ')
// 使用 Python 统计行数，避免 wc -l 输出格式因平台而异（Windows 无 tr）
const bashCmd = [
  `set -e`,
  `mkdir -p "$(dirname '${out}')"`,
  `(`,
  `  printf -- '---\\nsource: ${source}\\n---\\n\\n'`,
  `  for i in ${segIds}; do cat "${tmp}-$i.md"; printf '\\n'; done`,
  `) > "${out}"`,
  `rm -f "${tmp}"-*.md "${raw}"`,
  `python -c "print('合并完成，共', sum(1 for _ in open(r'${out}')), '行')"`,
].join('\n')

const mergeResult = await agent(
  `运行 Bash（单次调用，原样输出结果）：\n\`\`\`bash\n${bashCmd}\n\`\`\``,
  { label: 'merge-bash', phase: 'Merge' }
)

return mergeResult
