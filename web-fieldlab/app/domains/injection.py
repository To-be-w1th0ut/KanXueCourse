from __future__ import annotations

import ast
import os
import re
import shlex
import subprocess
from pathlib import Path

import yaml
from flask import Blueprint, render_template, render_template_string, request
from markupsafe import escape

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


# =====================================================================
# 批次 4：injection L05-L10 共 6 个新关卡
# =====================================================================

# ---------- L05 render_template_string SSTI ----------
@bp.route('/labs/injection/jinja-render-string', methods=['GET'])
def jinja_render_string():
    user_input = request.args.get('q', '')
    rendered = None
    error = None
    if user_input:
        try:
            if current_mode() == 'vuln':
                # ❌ 把用户输入当模板源码渲染
                rendered = render_template_string(user_input, price=299, quantity=2)
            else:
                # ✅ 模板源固定，仅作为变量传入并 HTML 转义
                rendered = render_template_string(
                    '诊断面板回显：<code>{{ msg }}</code>',
                    msg=user_input,
                )
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    return render_lab('jinja_render_string.html', 'jinja-render-string',
                      user_input=user_input, rendered=rendered, error=error)


# ---------- L06 YAML 不安全加载 ----------
@bp.route('/labs/injection/yaml-load', methods=['GET', 'POST'])
def yaml_load():
    parsed_repr = None
    error = None
    raw = ''
    if request.method == 'POST':
        raw = request.form.get('yaml_text', '')
        try:
            if current_mode() == 'vuln':
                # ❌ 完整 Loader 会处理 !!python/object/apply 等危险标签
                data = yaml.load(raw, Loader=yaml.Loader)
            else:
                # ✅ safe_load 只接受基本数据类型
                data = yaml.safe_load(raw)
            parsed_repr = repr(data)
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    return render_lab('yaml_load.html', 'yaml-load',
                      raw=raw, parsed_repr=parsed_repr, error=error)


# ---------- L07 环境变量注入 ----------
@bp.route('/labs/injection/env-injection', methods=['GET'])
def env_injection():
    target = request.args.get('target', '')
    output = None
    error = None
    if target:
        try:
            env = os.environ.copy()
            env['LC_FIELDLAB_TARGET'] = target
            if current_mode() == 'vuln':
                # ❌ shell=True + 直接读取环境变量，shell 会展开 $(...) / ``
                output = subprocess.check_output(
                    'echo target=$LC_FIELDLAB_TARGET',
                    shell=True, text=True, env=env, stderr=subprocess.STDOUT,
                    timeout=5,
                )
            else:
                # ✅ shell=False，环境变量值原样输出
                output = subprocess.check_output(
                    ['printenv', 'LC_FIELDLAB_TARGET'],
                    text=True, env=env, stderr=subprocess.STDOUT,
                    timeout=5,
                )
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    return render_lab('env_injection.html', 'env-injection',
                      target=target, output=output, error=error)


# ---------- L08 shlex.split 后 join 回去 ----------
@bp.route('/labs/injection/shlex-shell-true', methods=['GET'])
def shlex_shell_true():
    keyword = request.args.get('keyword', '')
    output = None
    error = None
    if keyword:
        try:
            if current_mode() == 'vuln':
                # ❌ 经典假防御：shlex.split 之后又 join 回字符串 + shell=True
                tokens = shlex.split(f'echo {keyword}')
                rebuilt = ' '.join(tokens)
                output = subprocess.check_output(
                    rebuilt, shell=True, text=True, stderr=subprocess.STDOUT, timeout=5,
                )
            else:
                # ✅ 保持 list 形式 + shell=False
                output = subprocess.check_output(
                    ['echo', keyword], text=True, stderr=subprocess.STDOUT, timeout=5,
                )
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    return render_lab('shlex_shell_true.html', 'shlex-shell-true',
                      keyword=keyword, output=output, error=error)


# ---------- L09 grep -E 正则可控 ----------
@bp.route('/labs/injection/grep-extended-pattern', methods=['GET'])
def grep_extended_pattern():
    pattern = request.args.get('pattern', '')
    output = None
    error = None
    log_file = data_root() / 'cmd_audit.log'
    if not log_file.exists():
        log_file.write_text('login attempt user=alice ip=10.0.0.1\n'
                            'login attempt user=bob ip=10.0.0.2\n'
                            'job dispatch id=42 status=ok\n')
    if pattern:
        try:
            if current_mode() == 'vuln':
                # ❌ shell=True + 直接拼 pattern
                cmd = f'grep -E {pattern} {log_file}'
                output = subprocess.check_output(
                    cmd, shell=True, text=True, stderr=subprocess.STDOUT, timeout=5,
                )
            else:
                # ✅ 正则在应用层用 re，不再调 shell
                lines = log_file.read_text().splitlines()
                try:
                    compiled = re.compile(pattern)
                except re.error as rex:
                    raise ValueError(f'正则不合法：{rex}')
                hits = [ln for ln in lines if compiled.search(ln)]
                output = '\n'.join(hits) if hits else '(no match)'
        except subprocess.CalledProcessError as exc:
            output = exc.output
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    return render_lab('grep_extended_pattern.html', 'grep-extended-pattern',
                      pattern=pattern, output=output, error=error)


# ---------- L10 git ref 拼接 ----------
_SAFE_REF_RE = re.compile(r'^[A-Za-z0-9._/-]{1,64}$')


@bp.route('/labs/injection/git-ref-injection', methods=['GET'])
def git_ref_injection():
    ref = request.args.get('ref', 'HEAD')
    output = None
    error = None
    cmd_shown = None
    if ref:
        try:
            if current_mode() == 'vuln':
                # ❌ 拼字符串 + shell=True
                cmd = f'git --version && echo using-ref={ref}'
                cmd_shown = cmd
                output = subprocess.check_output(
                    cmd, shell=True, text=True, stderr=subprocess.STDOUT, timeout=5,
                )
            else:
                # ✅ 严格校验 ref 字符集 + 参数数组
                if not _SAFE_REF_RE.match(ref):
                    raise ValueError('safe：ref 仅允许 [A-Za-z0-9._/-]，长度 1..64')
                cmd_shown = ['git', '--version']
                ver = subprocess.check_output(['git', '--version'], text=True, timeout=5).strip()
                output = f'{ver}\nusing-ref={ref}'
        except subprocess.CalledProcessError as exc:
            output = exc.output
        except FileNotFoundError:
            error = 'git 未安装在容器中（这一关只演示拼接风险，不依赖真实 git）。'
            if current_mode() == 'vuln':
                # 用 sh 模拟一次拼接执行，让 PoC 仍可观测
                cmd = f'echo no-git && echo using-ref={ref}'
                cmd_shown = cmd
                output = subprocess.check_output(
                    cmd, shell=True, text=True, stderr=subprocess.STDOUT, timeout=5,
                )
                error = None
            else:
                output = f'safe 模式 ref 校验通过：{ref}'
                error = None
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    return render_lab('git_ref_injection.html', 'git-ref-injection',
                      ref=ref, output=output, cmd_shown=cmd_shown, error=error)


def domain_taxonomy():
    return build_taxonomy(), '主轴：解释器边界', '解释器边界', '执行媒介'
