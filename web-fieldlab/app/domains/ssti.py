from __future__ import annotations

import ast
import html

from flask import Blueprint, render_template, render_template_string, request
from markupsafe import Markup

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


def domain_taxonomy():
    return build_taxonomy(), '主轴：模板拼装路径', '模板拼装路径', '执行方式'
