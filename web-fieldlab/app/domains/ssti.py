from __future__ import annotations

import ast
import html
import json
import os
import re
import string
import subprocess

from flask import Blueprint, render_template, render_template_string, request
from jinja2 import Environment
from jinja2.sandbox import SandboxedEnvironment
from markupsafe import Markup, escape

from content_store import execute, query_all, query_one
from shared import current_mode
from ssti_labs import LABS, build_taxonomy, get_lab

bp = Blueprint('ssti', __name__)

CONTEXT = {'student_name': 'Li Jia', 'course': 'WebSec', 'score': 94, 'title': 'Preview Banner', 'note': 'This banner is assembled at runtime.'}


def render_lab(template_name: str, slug: str, **context):
    return render_template(f'ssti/labs/{template_name}', lab=get_lab(slug), mode=current_mode(), show_event_dock=False, **context)


def domain_info() -> dict:
    return {
        'code': 'SSTI',
        'title': 'SSTI 轨道',
        'description': '围绕模板源码、表达式包装、存储后二次渲染与受信片段拼接。',
        'summary': '聚焦 Jinja2：模板就是代码，不可信字符串不能直接交给引擎。',
        'level': '高级',
        'count': len(LABS),
        'href': '/domains/ssti',
        'teaching_points': [
            '先讲模板源码和变量值的区别。',
            '再讲“用户没写 {{ }}，后端也可能帮他补上”。',
            '最后讲数据库中保存的模板为什么仍然危险。',
        ],
    }


def safe_eval_arithmetic(expr: str) -> str:
    if not expr.strip():
        return ''
    tree = ast.parse(expr, mode='eval')
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.Constant, ast.USub, ast.UAdd, ast.Load, ast.FloorDiv)
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError('only arithmetic is allowed in safe mode')
    return str(eval(compile(tree, '<safe-arith>', 'eval'), {'__builtins__': {}}, {}))


def manual_placeholder_render(body: str) -> str:
    rendered = body
    for key, value in CONTEXT.items():
        rendered = rendered.replace('{{ ' + key + ' }}', str(value))
        rendered = rendered.replace('{{' + key + '}}', str(value))
    return rendered


@bp.route('/labs/ssti/reflected-template')
def reflected_template():
    source = request.args.get('source', '')
    rendered = None
    error = None
    if source:
        try:
            rendered = render_template_string(source, **CONTEXT) if current_mode() == 'vuln' else source
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '模板已被拒绝。'
    return render_lab('reflected_template.html', 'reflected-template', source=source, rendered=rendered, error=error, context=CONTEXT)


@bp.route('/labs/ssti/expression-wrapper')
def expression_wrapper():
    expr = request.args.get('expr', '')
    template_source = '{{ ' + expr + ' }}' if expr else ''
    rendered = None
    error = None
    if expr:
        try:
            if current_mode() == 'vuln':
                rendered = render_template_string(template_source, **CONTEXT)
            else:
                rendered = safe_eval_arithmetic(expr)
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '安全模式仅允许基础算术表达式。'
    return render_lab('expression_wrapper.html', 'expression-wrapper', expr=expr, template_source=template_source, rendered=rendered, error=error)


@bp.route('/labs/ssti/stored-mail', methods=['GET', 'POST'])
def stored_mail():
    preview = None
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save':
            execute('INSERT INTO ssti_templates (title, body, created_at) VALUES (?, ?, datetime(\'now\'))', (request.form.get('title', 'Untitled')[:80], request.form.get('body', '')))
        elif action == 'preview':
            row = query_one('SELECT title, body, created_at FROM ssti_templates ORDER BY template_id DESC LIMIT 1')
            if row:
                try:
                    if current_mode() == 'vuln':
                        preview = Markup(render_template_string(row['body'], **CONTEXT))
                    else:
                        preview = Markup(html.escape(manual_placeholder_render(row['body'])))
                except Exception as exc:
                    error = str(exc) if current_mode() == 'vuln' else '模板预览被拒绝。'
    templates = query_all('SELECT template_id, title, body, created_at FROM ssti_templates ORDER BY template_id DESC LIMIT 6')
    return render_lab('stored_mail.html', 'stored-mail', templates=templates, preview=preview, error=error, context=CONTEXT)


@bp.route('/labs/ssti/theme-fragment', methods=['GET', 'POST'])
def theme_fragment():
    fragment = request.form.get('fragment', '') if request.method == 'POST' else request.args.get('fragment', '')
    rendered = None
    source = None
    error = None
    if fragment:
        source = '<section class="preview-banner">' + fragment + '</section>'
        try:
            if current_mode() == 'vuln':
                rendered = Markup(render_template_string(source, **CONTEXT))
            else:
                rendered = Markup('<section class="preview-banner">' + html.escape(fragment) + '</section>')
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '主题片段被安全模式拒绝。'
    themes = query_all('SELECT theme_id, name, body, created_at FROM ssti_themes ORDER BY theme_id DESC LIMIT 5')
    return render_lab('theme_fragment.html', 'theme-fragment', fragment=fragment, rendered=rendered, source=source, error=error, themes=themes, context=CONTEXT)


# =====================================================================
# 批次 2：SSTI L05-L12 共 8 个新关卡
# =====================================================================

# L08/L09 的演示用资源路径
_SSTI_SECRET_FILE = '/tmp/lab/ssti_secret.txt'
_SSTI_INCLUDE_DIR = '/tmp/lab/ssti_includes'
_SSTI_INCLUDE_SECRET = os.path.join(_SSTI_INCLUDE_DIR, 'admin_secret.html')


def _ensure_ssti_assets() -> None:
    """演示文件不存在时即时创建（容器重建后也能自愈）。"""
    try:
        os.makedirs(os.path.dirname(_SSTI_SECRET_FILE), exist_ok=True)
        if not os.path.exists(_SSTI_SECRET_FILE):
            with open(_SSTI_SECRET_FILE, 'w', encoding='utf-8') as fp:
                fp.write('FLAG{ssti_reads_local_file}\n')
        os.makedirs(_SSTI_INCLUDE_DIR, exist_ok=True)
        if not os.path.exists(_SSTI_INCLUDE_SECRET):
            with open(_SSTI_INCLUDE_SECRET, 'w', encoding='utf-8') as fp:
                fp.write('FLAG{ssti_include_local_template}\n')
    except OSError:
        # 只读环境也不阻断主流程
        pass


# ---------- L05 沙箱逃逸 ----------
_BLACKLIST_KEYWORDS = ('import', 'eval', 'exec', '__import__', 'os.', 'subprocess')


@bp.route('/labs/ssti/sandbox-escape')
def sandbox_escape():
    source = request.args.get('source', '')
    rendered = None
    error = None
    if source:
        if current_mode() == 'vuln':
            # ❌ 关键字黑名单 + 普通 Environment：mro 链能直接绕过
            if any(kw in source for kw in _BLACKLIST_KEYWORDS):
                error = '检测到危险关键字，已拒绝。'
            else:
                try:
                    rendered = Environment().from_string(source).render(**CONTEXT)
                except Exception as exc:
                    error = str(exc)
        else:
            # ✅ 真正的 SandboxedEnvironment + 不暴露任何对象
            try:
                rendered = SandboxedEnvironment().from_string(source).render()
            except Exception as exc:
                error = '安全模式拦截：' + str(exc)
    return render_lab(
        'sandbox_escape.html', 'sandbox-escape',
        source=source, rendered=rendered, error=error,
    )


# ---------- L06 Tornado / 其他方言 ----------
def _tornado_like_render(source: str, ctx: dict) -> str:
    """用 string.Template 模拟"另一种方言"的简化渲染：

    - {% if NAME %}…{% end %}：当 ctx[NAME] 为真时保留，否则移除整段
    - $name：作变量替换（与 Jinja 不同的方言！）
    """
    def _if_replace(match: re.Match) -> str:
        name, body = match.group(1), match.group(2)
        return body if ctx.get(name) else ''

    out = re.sub(r'{%\s*if\s+(\w+)\s*%}(.*?){%\s*end\s*%}', _if_replace, source, flags=re.DOTALL)
    return string.Template(out).safe_substitute(ctx)


@bp.route('/labs/ssti/tornado-dialect')
def tornado_dialect():
    source = request.args.get('source', '')
    rendered = None
    error = None
    if source:
        try:
            if current_mode() == 'vuln':
                rendered = _tornado_like_render(source, {**CONTEXT, 'admin': True})
            else:
                # ✅ 安全模式：完全不解析方言，只展示原文
                rendered = source
        except Exception as exc:
            error = str(exc)
    return render_lab(
        'tornado_dialect.html', 'tornado-dialect',
        source=source, rendered=rendered, error=error,
    )


# ---------- L07 客户端模板（AngularJS 风格） ----------
@bp.route('/labs/ssti/client-angular')
def client_angular():
    """前端模板演示，所有 SSTI 行为都在浏览器执行。"""
    return render_lab('client_angular.html', 'client-angular')


# ---------- L08 SSTI 读本地文件 ----------
@bp.route('/labs/ssti/file-read')
def file_read():
    _ensure_ssti_assets()
    source = request.args.get('source', '')
    rendered = None
    error = None
    if source:
        if current_mode() == 'vuln':
            try:
                # ❌ 给模板上下文里塞入文件读取能力
                env = Environment()
                env.globals['read'] = lambda path: open(path, 'r', encoding='utf-8').read()
                rendered = env.from_string(source).render(secret_path=_SSTI_SECRET_FILE, **CONTEXT)
            except Exception as exc:
                error = str(exc)
        else:
            error = '安全模式禁止任意文件读取，请使用预置的 watermark API。'
    return render_lab(
        'file_read.html', 'file-read',
        source=source, rendered=rendered, error=error,
        secret_path=_SSTI_SECRET_FILE,
    )


# ---------- L09 SSTI 执行系统命令 ----------
class _MockSubprocess:
    """白名单命令执行器：仅允许 id / whoami / pwd / ls 之类的只读命令。

    教学用，避免在容器里真的暴露任意 RCE。
    """

    _ALLOWED = {'id', 'whoami', 'pwd', 'ls', 'date', 'uname', 'hostname'}

    def check_output(self, args):
        if isinstance(args, str):
            args = args.split()
        if not args or args[0] not in self._ALLOWED:
            return f'mock: {args[0] if args else "?"} not in allowed list {sorted(self._ALLOWED)}'.encode()
        try:
            return subprocess.check_output(args, timeout=2)
        except Exception as exc:  # noqa: BLE001
            return f'mock error: {exc}'.encode()


@bp.route('/labs/ssti/command-exec')
def command_exec():
    source = request.args.get('source', '')
    rendered = None
    error = None
    if source:
        if current_mode() == 'vuln':
            try:
                env = Environment()
                env.globals['cmd'] = _MockSubprocess()
                rendered = env.from_string(source).render(**CONTEXT)
            except Exception as exc:
                error = str(exc)
        else:
            error = '安全模式：模板上下文不再注入 cmd 对象。'
    return render_lab(
        'command_exec.html', 'command-exec',
        source=source, rendered=rendered, error=error,
    )


# ---------- L10 双字段二次渲染 ----------
@bp.route('/labs/ssti/double-render', methods=['GET', 'POST'])
def double_render():
    rendered_title = None
    rendered_body = None
    error = None
    title = ''
    body = ''
    if request.method == 'POST':
        title = (request.form.get('title') or '')[:120]
        body = request.form.get('body') or ''
        try:
            if current_mode() == 'vuln':
                # ❌ 补丁只过滤了 body 中的 {{ }}，title 完全没过
                safe_body = body.replace('{{', '').replace('}}', '')
                rendered_title = Markup(render_template_string(title, **CONTEXT))
                rendered_body = Markup(render_template_string(safe_body, **CONTEXT))
            else:
                rendered_title = Markup(escape(title))
                rendered_body = Markup(escape(body))
        except Exception as exc:
            error = str(exc)
    return render_lab(
        'double_render.html', 'double-render',
        title=title, body=body,
        rendered_title=rendered_title, rendered_body=rendered_body,
        error=error,
    )


# ---------- L11 JSON key 进入模板 ----------
@bp.route('/labs/ssti/json-key', methods=['GET', 'POST'])
def json_key():
    raw = request.form.get('config_json', '') if request.method == 'POST' else request.args.get('config_json', '')
    rendered_pairs = None
    error = None
    if raw:
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError('配置必须是 JSON 对象')
            pairs = []
            for key, value in data.items():
                if current_mode() == 'vuln':
                    # ❌ key 和 value 都进引擎
                    rk = render_template_string(str(key), **CONTEXT)
                    rv = render_template_string(str(value), **CONTEXT)
                else:
                    rk = escape(str(key))
                    rv = escape(str(value))
                pairs.append((Markup(rk), Markup(rv)))
            rendered_pairs = pairs
        except Exception as exc:
            error = str(exc)
    return render_lab(
        'json_key.html', 'json-key',
        config_json=raw, rendered_pairs=rendered_pairs, error=error,
    )


# ---------- L12 include 路径可控 ----------
_SAFE_FRAGMENT_MAP = {
    'welcome': 'ssti/labs/_fragment_welcome.html',
    'footer': 'ssti/labs/_fragment_footer.html',
}


@bp.route('/labs/ssti/include-path')
def include_path():
    _ensure_ssti_assets()
    fragment = request.args.get('fragment', '')
    rendered = None
    error = None
    if fragment:
        if current_mode() == 'vuln':
            try:
                # ❌ 直接拼字符串再让 Jinja 自己解析 include 路径
                # 真实 include 受 loader 限制；这里改用绝对路径 open 模拟"任意 include"
                if os.path.isfile(fragment):
                    with open(fragment, 'r', encoding='utf-8', errors='replace') as fp:
                        body = fp.read()
                    rendered = Markup(render_template_string(body, **CONTEXT))
                else:
                    error = f'文件不存在：{fragment}（试试 {_SSTI_INCLUDE_SECRET}）'
            except Exception as exc:
                error = str(exc)
        else:
            target = _SAFE_FRAGMENT_MAP.get(fragment)
            if not target:
                error = f'非白名单片段：{fragment}（仅允许 {list(_SAFE_FRAGMENT_MAP)}）'
            else:
                try:
                    rendered = Markup(render_template(target, **CONTEXT))
                except Exception as exc:
                    error = str(exc)
    return render_lab(
        'include_path.html', 'include-path',
        fragment=fragment, rendered=rendered, error=error,
        secret_include=_SSTI_INCLUDE_SECRET,
        whitelist=list(_SAFE_FRAGMENT_MAP),
    )


def domain_taxonomy():
    return build_taxonomy(), '主轴：模板拼装路径', '模板拼装路径', '执行方式'
