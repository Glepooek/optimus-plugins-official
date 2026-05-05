import zipfile
import json
import uuid
import re
import sys
import os


def gen_id():
    return uuid.uuid4().hex[:26]


def parse_markdown(filepath):
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
        nonlocal current_case_title, current_req_id, current_priority
        nonlocal current_steps, current_expected
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
            raw = stripped[6:].strip()
            req_match = re.match(r'^\[([^\]]+)\]\s*', raw)
            if req_match:
                current_req_id = req_match.group(1).strip()
                raw = raw[req_match.end():]
            pri_match = re.search(r'\[(P[012])\]\s*$', raw)
            if pri_match:
                current_priority = pri_match.group(1)
                raw = raw[:pri_match.start()].strip()
            current_case_title = raw
        elif stripped.startswith('###### '):
            current_field = stripped[7:].strip()
        elif stripped.startswith('- '):
            val = stripped[2:].strip()
            val_clean = re.sub(r'^\d+[\.\)]\s*', '', val)
            if current_field == '测试步骤':
                current_steps.append(val_clean)
            elif current_field == '预期结果':
                current_expected.append(val_clean)
        elif stripped == '---':
            flush_case()
    flush_case()
    return root_title, cases


def make_topic(title, children=None):
    topic = {'id': gen_id(), 'title': title}
    if children:
        topic['children'] = {'attached': children}
    else:
        topic['children'] = {}
    return topic


def build_xmind_tree(root_title, cases, project_name=None):
    case_topics = []
    for case in cases:
        # L1: 需求ID + 用例标题 + 优先级
        title = case['title']
        if project_name:
            title = f'\u3010{project_name}\u3011\u3010{case["module"]}\u3011{title}'
        if case.get('req_id'):
            title = f'[{case["req_id"]}] {title}'
        if case.get('priority'):
            title = f'{title}[{case["priority"]}]'

        # L2: 前置条件（仅模块路径，不含需求ID）
        path_parts = [case['module'], case['test_point'], case['verify_point']]
        precondition = ' > '.join(filter(None, path_parts))

        # L3-L4: 步骤与预期配对
        step_topics = []
        max_len = max(len(case['steps']), len(case['expected']), 1)
        for i in range(max_len):
            step_text = case['steps'][i] if i < len(case['steps']) else '(\u9a8c\u8bc1)'
            step_children = None
            if i < len(case['expected']):
                step_children = [make_topic(case['expected'][i])]
            step_topics.append(make_topic(step_text, step_children))

        precond_topic = make_topic(precondition, step_topics if step_topics else None)
        case_topic = make_topic(title, [precond_topic])
        case_topics.append(case_topic)

    root_topic = {
        'id': gen_id(),
        'structureClass': 'org.xmind.ui.map.unbalanced',
        'title': root_title or '\u6d4b\u8bd5\u7528\u4f8b\u96c6',
        'children': {'attached': case_topics},
        'extensions': [{
            'provider': 'org.xmind.ui.map.unbalanced',
            'content': [{'name': 'right-number', 'content': str(len(case_topics))}]
        }]
    }
    return root_topic


def write_xmind(root_topic, output_path):
    sheet = {
        'id': gen_id(),
        'class': 'sheet',
        'title': root_topic['title'],
        'rootTopic': root_topic,
        'theme': {},
        'relationships': [],
        'topicPositioning': 'fixed'
    }
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('content.json',
                     json.dumps([sheet], ensure_ascii=False, indent=2))
        zf.writestr('metadata.json',
                     json.dumps({'creator': {'name': 'QA-Skills', 'version': '1.0.0'}},
                                ensure_ascii=False))
        zf.writestr('manifest.json',
                     json.dumps({'file-entries': {'content.json': {}, 'metadata.json': {}}},
                                ensure_ascii=False))


def convert(input_md, output_xmind=None, project_name=None):
    if output_xmind is None:
        output_xmind = re.sub(r'\.md$', '.xmind', input_md)
    root_title, cases = parse_markdown(input_md)
    root_topic = build_xmind_tree(root_title, cases, project_name)
    write_xmind(root_topic, output_xmind)
    return output_xmind, len(cases)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python converter.py <input.md> [--project name]')
        sys.exit(1)
    input_file = sys.argv[1]
    project = None
    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == '--project' and i + 1 < len(args):
            project = args[i + 1]
    out, count = convert(input_file, project_name=project)
    print(f'Done! {count} test cases -> {out}')
