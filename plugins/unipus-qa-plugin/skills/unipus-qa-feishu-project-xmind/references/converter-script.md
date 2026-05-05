# 转换脚本参考

## Python 转换脚本

以下脚本实现六级 Markdown 测试用例到飞书兼容 .xmind 文件的完整转换。

### 依赖

无需第三方库，仅使用 Python 标准库：`zipfile`、`json`、`uuid`、`re`

### 完整脚本

```python
import zipfile
import json
import uuid
import re
import sys
import os


def gen_id():
    """生成 XMind 节点唯一 ID"""
    return uuid.uuid4().hex[:26]


def parse_markdown(filepath):
    """
    解析六级 Markdown 测试用例文档。

    返回:
        root_title: str - H1 文档标题
        cases: list[dict] - 用例列表，每条包含：
            - title: 用例标题 (H5)
            - module: 功能模块 (H2)
            - test_point: 功能测试点 (H3)
            - verify_point: 验证点 (H4)
            - req_id: 需求ID
            - priority: 优先级（如 P0、P1）
            - steps: list[str] - 测试步骤
            - expected: list[str] - 预期结果
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.strip().split('\n')

    root_title = ''
    cases = []
    current_module = ''
    current_test_point = ''
    current_verify_point = ''
    current_case_title = ''
    current_field = ''
    current_req_id = ''
    current_priority = ''
    current_steps = []
    current_expected = []

    def flush_case():
        nonlocal current_case_title, current_req_id, current_priority, current_steps, current_expected
        if current_case_title and (current_steps or current_expected):
            cases.append({
                'title': current_case_title,
                'module': current_module,
                'test_point': current_test_point,
                'verify_point': current_verify_point,
                'req_id': current_req_id,
                'priority': current_priority,
                'steps': current_steps[:],
                'expected': current_expected[:]
            })
        current_case_title = ''
        current_req_id = ''
        current_priority = ''
        current_steps = []
        current_expected = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith('# ') and not stripped.startswith('## '):
            root_title = stripped[2:].strip()
        elif stripped.startswith('## ') and not stripped.startswith('### '):
            flush_case()
            current_module = stripped[3:].strip()
        elif stripped.startswith('### ') and not stripped.startswith('#### '):
            flush_case()
            current_test_point = stripped[4:].strip()
        elif stripped.startswith('#### ') and not stripped.startswith('##### '):
            flush_case()
            current_verify_point = stripped[5:].strip()
        elif stripped.startswith('##### ') and not stripped.startswith('###### '):
            flush_case()
            current_case_title = stripped[6:].strip()
        elif stripped.startswith('###### '):
            current_field = stripped[7:].strip()
        elif stripped.startswith('- '):
            val = stripped[2:].strip()
            val_clean = re.sub(r'^\d+\.\s*', '', val)
            if current_field == '需求ID':
                current_req_id = val_clean
            elif current_field == '优先级':
                current_priority = val_clean
            elif current_field == '测试步骤':
                current_steps.append(val_clean)
            elif current_field == '预期结果':
                current_expected.append(val_clean)
        elif stripped == '---':
            flush_case()

    flush_case()
    return root_title, cases


def make_topic(title, children=None):
    """创建 XMind 节点"""
    topic = {
        'id': gen_id(),
        'title': title,
    }
    if children:
        topic['children'] = {'attached': children}
    else:
        topic['children'] = {}
    return topic


def build_xmind_tree(root_title, cases, project_name=None):
    """
    构建 XMind JSON 树结构。

    参数:
        root_title: 根节点标题
        cases: 用例列表
        project_name: 项目名称前缀（可选），如 "AI智课"
    """
    case_topics = []

    for case in cases:
        # L1: 用例标题（可带前缀和优先级）
        title = case['title']
        if project_name:
            title = f'【{project_name}】【{case["module"]}】{title}'
        if case.get('priority'):
            title = f'{title} [{case["priority"]}]'

        # L2: 前置条件（模块路径 + 需求ID）
        path_parts = [case['module'], case['test_point'], case['verify_point']]
        path = ' > '.join(filter(None, path_parts))
        if case['req_id']:
            precondition = f'{path} [需求ID: {case["req_id"]}]'
        else:
            precondition = path

        # L3-L4: 步骤与预期配对
        step_topics = []
        max_len = max(len(case['steps']), len(case['expected']))
        for i in range(max_len):
            step_text = case['steps'][i] if i < len(case['steps']) else '(验证)'
            step_children = None
            if i < len(case['expected']):
                expected_topic = make_topic(case['expected'][i])
                step_children = [expected_topic]
            step_topics.append(make_topic(step_text, step_children))

        precond_topic = make_topic(precondition, step_topics if step_topics else None)
        case_topic = make_topic(title, [precond_topic])
        case_topics.append(case_topic)

    # L0: 根节点
    root_topic = {
        'id': gen_id(),
        'structureClass': 'org.xmind.ui.map.unbalanced',
        'title': root_title or '测试用例集',
        'children': {'attached': case_topics},
        'extensions': [{
            'provider': 'org.xmind.ui.map.unbalanced',
            'content': [{'name': 'right-number', 'content': str(len(case_topics))}]
        }]
    }

    return root_topic


def write_xmind(root_topic, output_path, template_path=None):
    """
    写入 .xmind 文件。

    参数:
        root_topic: XMind 根节点
        output_path: 输出文件路径
        template_path: XMind 模板路径（可选，用于复用主题样式）
    """
    # 读取模板主题（如有）
    theme = {}
    if template_path and os.path.exists(template_path):
        with zipfile.ZipFile(template_path, 'r') as tz:
            tdata = json.loads(tz.read('content.json').decode('utf-8'))
            theme = tdata[0].get('theme', {})

    sheet = {
        'id': gen_id(),
        'class': 'sheet',
        'title': root_topic['title'],
        'rootTopic': root_topic,
        'theme': theme,
        'relationships': [],
        'topicPositioning': 'fixed'
    }

    xmind_content = [sheet]

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('content.json',
                     json.dumps(xmind_content, ensure_ascii=False, indent=2))
        zf.writestr('metadata.json',
                     json.dumps({'creator': {'name': 'QA-Skills', 'version': '1.0.0'}},
                                ensure_ascii=False))
        zf.writestr('manifest.json',
                     json.dumps({'file-entries': {'content.json': {}, 'metadata.json': {}}},
                                ensure_ascii=False))


def convert(input_md, output_xmind=None, project_name=None, template_path=None):
    """
    主入口：将 Markdown 测试用例转换为 .xmind 文件。

    参数:
        input_md: 输入 Markdown 文件路径
        output_xmind: 输出 .xmind 文件路径（默认同名替换扩展名）
        project_name: 项目名前缀（如 "AI智课"），为 None 则不添加
        template_path: XMind 模板路径（可选）

    返回:
        output_path: 生成的 .xmind 文件路径
        case_count: 用例数量
    """
    if output_xmind is None:
        output_xmind = re.sub(r'\.md$', '.xmind', input_md)

    root_title, cases = parse_markdown(input_md)
    root_topic = build_xmind_tree(root_title, cases, project_name)
    write_xmind(root_topic, output_xmind, template_path)

    return output_xmind, len(cases)


# CLI 用法
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python converter.py <input.md> [--project "项目名"] [--template path.xmind]')
        sys.exit(1)

    input_file = sys.argv[1]
    project = None
    template = None

    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == '--project' and i + 1 < len(args):
            project = args[i + 1]
        elif arg == '--template' and i + 1 < len(args):
            template = args[i + 1]

    out, count = convert(input_file, project_name=project, template_path=template)
    print(f'Done! {count} test cases → {out}')
```

### 使用方式

**在 Claude Code 中调用：**

执行转换时按以下流程操作：

1. 读取输入 Markdown 文件
2. 调用 `parse_markdown()` 解析六级结构
3. 询问用户是否添加项目名/模块名前缀
4. 调用 `build_xmind_tree()` 构建节点树
5. 调用 `write_xmind()` 输出 .xmind 文件

**命令行直接调用：**

```bash
# 基础转换
python converter.py testcases/测试用例-01.md

# 带项目名前缀
python converter.py testcases/测试用例-01.md --project "AI智课"

# 使用模板主题样式
python converter.py testcases/测试用例-01.md --project "AI智课" --template Test-skills/xmind_template.xmind
```
