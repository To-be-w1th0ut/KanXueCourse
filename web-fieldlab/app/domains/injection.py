from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from flask import Blueprint, render_template, request

from content_store import data_root, execute, query_all, query_one
from injection_labs import LABS, build_taxonomy, get_lab
from shared import current_mode

bp = Blueprint('injection', __name__)
SAFE_CONTEXT = {'price': 299, 'quantity': 2}


def render_lab(template_name: str, slug: str, **context):
    return render_template(f'injection/labs/{template_name}', lab=get_lab(slug), mode=current_mode(), show_event_dock=False, **context)


def domain_info() -> dict:
    return {
        'code': 'INJ',
        'title': '代码 / 命令注入轨道',
        'description': '覆盖 eval、exec、shell=True 和运维命令拼接。',
        'summary': '把“解释器边界失守”从 Python 代码和 shell 命令两侧一起讲。',
        'level': '高级',
        'count': len(LABS),
        'href': '/domains/injection',
        'teaching_points': [
            '代码注入和命令注入本质都在于：不可信输入进入了解释器。',
            '先讲 eval/exec，再迁移到 shell=True。',
            '强调白名单 DSL 与参数数组是两种不同的防御思路。',
        ],
    }


def safe_arithmetic(expr: str) -> str:
    tree = ast.parse(expr, mode='eval')
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.Constant, ast.Load, ast.USub, ast.UAdd, ast.Name)
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError('safe mode only allows arithmetic names and operators')
        if isinstance(node, ast.Name) and node.id not in SAFE_CONTEXT:
            raise ValueError('safe mode only allows predefined names')
    return str(eval(compile(tree, '<safe>', 'eval'), {'__builtins__': {}}, SAFE_CONTEXT))


@bp.route('/labs/injection/python-eval')
def python_eval_lab():
    expr = request.args.get('expr', '')
    result = None
    error = None
    if expr:
        try:
            if current_mode() == 'vuln':
                result = repr(eval(expr, {'__builtins__': __builtins__}, SAFE_CONTEXT.copy()))
            else:
                result = safe_arithmetic(expr)
        except Exception as exc:
            error = str(exc)
    return render_lab('python_eval.html', 'python-eval', expr=expr, result=result, error=error, context=SAFE_CONTEXT)


@bp.route('/labs/injection/stored-exec', methods=['GET', 'POST'])
def stored_exec():
    preview = None
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save':
            execute('INSERT INTO injection_snippets (title, body, created_at) VALUES (?, ?, datetime(\'now\'))', (request.form.get('title', 'Untitled')[:80], request.form.get('body', '')))
        elif action == 'preview':
            row = query_one('SELECT * FROM injection_snippets ORDER BY snippet_id DESC LIMIT 1')
            if row:
                try:
                    if current_mode() == 'vuln':
                        scope = {'price': 299, 'quantity': 2}
                        exec(row['body'], {'__builtins__': __builtins__}, scope)
                        preview = scope.get('summary', repr(scope))
                    else:
                        preview = '安全模式：仅展示脚本源码，不执行用户片段。'
                except Exception as exc:
                    error = str(exc)
    snippets = query_all('SELECT * FROM injection_snippets ORDER BY snippet_id DESC LIMIT 5')
    return render_lab('stored_exec.html', 'stored-exec', snippets=snippets, preview=preview, error=error)


@bp.route('/labs/injection/command-diagnose')
def command_diagnose():
    target = request.args.get('target', '')
    output = None
    error = None
    if target:
        try:
            if current_mode() == 'vuln':
                cmd = f"printf 'diagnose target='; echo {target}"
                output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
            else:
                output = subprocess.check_output(['echo', target], text=True, stderr=subprocess.STDOUT)
        except Exception as exc:
            error = str(exc)
    return render_lab('command_diagnose.html', 'command-diagnose', target=target, output=output, error=error)


@bp.route('/labs/injection/command-grep')
def command_grep():
    keyword = request.args.get('keyword', '')
    output = None
    error = None
    log_file = data_root() / 'cmd_audit.log'
    if keyword:
        try:
            if current_mode() == 'vuln':
                cmd = f'grep -n {keyword} {log_file}'
                output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
            else:
                completed = subprocess.run(['grep', '-n', keyword, str(log_file)], capture_output=True, text=True)
                output = completed.stdout or completed.stderr or '(no match)'
        except Exception as exc:
            error = str(exc)
    return render_lab('command_grep.html', 'command-grep', keyword=keyword, output=output, error=error)


def domain_taxonomy():
    return build_taxonomy(), '主轴：解释器边界', '解释器边界', '执行媒介'
